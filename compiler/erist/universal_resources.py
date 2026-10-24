from __future__ import annotations

from .ir import (
    IRFileOpen,
    IRFileRead,
    IRFileWrite,
    IRReturn,
    IRWith,
    STD_FILE,
    STD_FILE_ERROR,
)
from .ir_text import IRFileExists, IRFileRemove
from .universal_checked import CheckedUniversalLowerer
from .universal_ir import BOOL, TEXT, UField, UReturn, UType


class ResourceUniversalLowerer(CheckedUniversalLowerer):
    """Universal lowering for deterministic `with` resources and std.files.

    Cleanup is made explicit as Universal-IR operations. The lowering stack is
    consulted by return and failure propagation, guaranteeing reverse-order
    cleanup without CPU-specific unwinding semantics.
    """

    def __init__(self):
        super().__init__()
        self.cleanup_stack = []

    def lower(self, program):
        result = super().lower(program)
        if not any(item.name == STD_FILE_ERROR for item in result.types):
            result.types.append(
                UType(
                    STD_FILE_ERROR,
                    (
                        UField("message", TEXT, False),
                        UField("path", TEXT, False),
                    ),
                    True,
                )
            )
        self.types = result.types
        self.type_by_name = {item.name: item for item in result.types}
        return result

    def _map_type(self, source_type: str) -> str:
        if source_type == STD_FILE:
            return f"resource<{STD_FILE}>"
        if source_type == STD_FILE_ERROR:
            return f"nominal<{STD_FILE_ERROR}>"
        return super()._map_type(source_type)

    def _emit_active_cleanups(self) -> None:
        for local in reversed(self.cleanup_stack):
            resource = self._load_local_value(local)
            self._emit("resource_cleanup", args=(resource,), immediate=local.type_name)

    def _terminate_propagation(self) -> None:
        self._emit_active_cleanups()
        super()._terminate_propagation()

    def _stmt(self, stmt) -> None:
        if isinstance(stmt, IRReturn):
            if stmt.value is None:
                if self.current_return != "void":
                    raise ValueError("value-returning universal function cannot use bare return")
                self._emit_active_cleanups()
                pending = self._emit("error_pending", BOOL)
                assert pending is not None
                source = self.current
                fail_block = self._new_block("cleanup.propagate")
                return_block = self._new_block("cleanup.return")
                assert source is not None
                from .universal_ir import UBranch
                source.terminator = UBranch(pending, fail_block.name, return_block.name)
                self.current = fail_block
                super()._terminate_propagation()
                self.current = return_block
                self.current.terminator = UReturn()
                return
            value = self._expr(stmt.value)
            if value is None or value.type_name != self.current_return:
                raise ValueError("universal IR return type mismatch")
            value = self._clone(value)
            self._emit_active_cleanups()
            pending = self._emit("error_pending", BOOL)
            assert pending is not None
            source = self.current
            fail_block = self._new_block("cleanup.propagate")
            return_block = self._new_block("cleanup.return")
            from .universal_ir import UBranch
            assert source is not None
            source.terminator = UBranch(pending, fail_block.name, return_block.name)
            self.current = fail_block
            super()._terminate_propagation()
            self.current = return_block
            self.current.terminator = UReturn(value)
            return

        if isinstance(stmt, IRWith):
            resource_type = self._map_type(stmt.resource_type)
            resource = self._expr(stmt.resource)
            if resource is None or resource.type_name != resource_type:
                raise ValueError("with resource type mismatch in Universal IR")
            local = self._declare(stmt.name, resource_type)
            self._emit("store_local", args=(resource,), local=local.id)
            self.scopes.append({stmt.name: local})
            self.cleanup_stack.append(local)
            try:
                self._lower_statements(stmt.body, new_scope=False)
            finally:
                self.cleanup_stack.pop()
                self.scopes.pop()
            if self.current is not None and self.current.terminator is None:
                active = self._load_local_value(local)
                self._emit("resource_cleanup", args=(active,), immediate=resource_type)
                # Cleanup on an otherwise normal path becomes a checked failure.
                self._propagate_if_pending()
            return

        super()._stmt(stmt)

    def _expr(self, expr):
        if isinstance(expr, IRFileOpen):
            path = self._expr(expr.path)
            if path is None or path.type_name != TEXT:
                raise ValueError("files.open requires Text path")
            result = self._emit("file_open", f"resource<{STD_FILE}>", (path,), immediate=STD_FILE_ERROR)
            assert result is not None
            if self.capture_checked_depth == 0:
                self._propagate_if_pending()
            return result

        if isinstance(expr, IRFileRead):
            resource = self._expr(expr.resource)
            if resource is None or resource.type_name != f"resource<{STD_FILE}>":
                raise ValueError("File.readText requires File resource")
            result = self._emit("file_read_text", TEXT, (resource,), immediate=STD_FILE_ERROR)
            assert result is not None
            if self.capture_checked_depth == 0:
                self._propagate_if_pending()
            return result

        if isinstance(expr, IRFileWrite):
            resource = self._expr(expr.resource)
            text = self._expr(expr.text)
            if resource is None or text is None or text.type_name != TEXT:
                raise ValueError("File.writeText arguments are invalid")
            self._emit("file_write_text", args=(resource, text), immediate=STD_FILE_ERROR)
            if self.capture_checked_depth == 0:
                self._propagate_if_pending()
            return None

        if isinstance(expr, IRFileExists):
            path = self._expr(expr.path)
            if path is None or path.type_name != TEXT:
                raise ValueError("files.exists requires Text path")
            result = self._emit("file_exists", BOOL, (path,), immediate=STD_FILE_ERROR)
            assert result is not None
            if self.capture_checked_depth == 0:
                self._propagate_if_pending()
            return result

        if isinstance(expr, IRFileRemove):
            path = self._expr(expr.path)
            if path is None or path.type_name != TEXT:
                raise ValueError("files.remove requires Text path")
            self._emit("file_remove", args=(path,), immediate=STD_FILE_ERROR)
            if self.capture_checked_depth == 0:
                self._propagate_if_pending()
            return None

        return super()._expr(expr)
