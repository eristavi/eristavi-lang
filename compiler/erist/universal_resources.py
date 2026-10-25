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
from .ir_text import IRProcessCall, IRFileAcquire, IRUnicodeCall, IRFileExists, IRFileRemove, IRTextView, IRTextViewCount, IRTextViewIndex
from .universal_checked import CheckedUniversalLowerer
from .universal_ir import BOOL, I64, TEXT, UBranch, UField, UProgram, UReturn, UType


class ResourceUniversalLowerer(CheckedUniversalLowerer):
    """Universal lowering for deterministic resources and linked contracts.

    External module-object contracts and type layouts can be injected directly,
    so source modules compile against serialized implementations without fake
    source bodies. Cleanup is explicit and walks the active ownership stack in
    reverse order on normal exit, return, or checked-failure propagation.
    """

    def __init__(self, external_functions=None, external_types=()):
        super().__init__()
        self.cleanup_stack = []
        self.external_functions = dict(external_functions or {})
        self.external_types = list(external_types)

    def lower(self, program):
        from .collection_codegen import require_collection_codegen
        require_collection_codegen(program, "Universal IR")
        source_types = [
            UType(
                item.name,
                tuple(UField(field.name, self._map_type(field.type_name), field.fixed) for field in item.fields),
                item.is_error,
            )
            for item in program.structs
        ]
        self.types = []
        known = {}
        for item in [*self.external_types, *source_types]:
            existing = known.get(item.name)
            if existing is not None and existing != item:
                raise ValueError(f"conflicting Universal-IR type layout for {item.name!r}")
            if existing is None:
                known[item.name] = item
                self.types.append(item)
        if STD_FILE_ERROR not in known:
            file_error = UType(
                STD_FILE_ERROR,
                (UField("message", TEXT, False), UField("path", TEXT, False)),
                True,
            )
            known[file_error.name] = file_error
            self.types.append(file_error)
        self.type_by_name = dict(known)

        self.known_functions = dict(self.external_functions)
        for fn in program.functions:
            params = [self._map_type(p.type_name) for p in fn.parameters]
            result = "void" if fn.return_type is None else self._map_type(fn.return_type)
            contract = (params, result, tuple(fn.fails))
            existing = self.known_functions.get(fn.name)
            if existing is not None and existing != contract:
                raise ValueError(f"conflicting Universal-IR function contract for {fn.name!r}")
            self.known_functions[fn.name] = contract

        functions = [self._lower_function(fn) for fn in program.functions]
        functions.append(self._lower_entry(program.entry))
        return UProgram(functions, "__entry", list(self.types))

    def _map_type(self, source_type: str) -> str:
        if source_type == STD_FILE:
            return f"resource<{STD_FILE}>"
        if source_type == STD_FILE_ERROR:
            return f"nominal<{STD_FILE_ERROR}>"
        if source_type.startswith("Text ") and source_type.endswith(" view"):
            kind = source_type[5:-5]
            if kind not in ("bytes", "scalars", "characters"):
                raise ValueError(f"unknown Text view kind {kind!r}")
            return f"textview<{kind}>"
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
            # Outside a `with` scope, ordinary/checked return lowering must remain
            # identical to the checked layer. In particular, do not manufacture
            # cleanup error-state checks for functions that own no resources.
            if not self.cleanup_stack:
                return super()._stmt(stmt)
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
                source.terminator = UBranch(pending, fail_block.name, return_block.name)
                self.current = fail_block
                # Active cleanup already ran once above; use checked propagation
                # directly to avoid closing the same resources twice.
                CheckedUniversalLowerer._terminate_propagation(self)
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
            assert source is not None
            source.terminator = UBranch(pending, fail_block.name, return_block.name)
            self.current = fail_block
            CheckedUniversalLowerer._terminate_propagation(self)
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
                self._propagate_if_pending()
            return

        super()._stmt(stmt)

    def _expr(self, expr):
        if isinstance(expr, IRTextView):
            base = self._expr(expr.base)
            if base is None or base.type_name != TEXT:
                raise ValueError("Text view requires Text")
            result = self._emit(
                "text_view",
                f"textview<{expr.kind}>",
                (base,),
                immediate=expr.kind,
            )
            assert result is not None
            return result

        if isinstance(expr, IRTextViewCount):
            view = self._expr(expr.view)
            if view is None or not view.type_name.startswith("textview<"):
                raise ValueError("Text view count requires a Text view")
            result = self._emit("text_view_count", I64, (view,), immediate=view.type_name[9:-1])
            assert result is not None
            return result

        if isinstance(expr, IRTextViewIndex):
            view = self._expr(expr.view)
            index = self._expr(expr.index)
            if view is None or not view.type_name.startswith("textview<") or index is None or index.type_name != I64:
                raise ValueError("Text view index is malformed")
            kind = view.type_name[9:-1]
            result_type = I64 if kind == "bytes" else TEXT
            result = self._emit("text_view_index", result_type, (view, index), immediate=kind)
            assert result is not None
            return result

        if isinstance(expr, (IRProcessCall, IRFileAcquire)):
            raise ValueError("this bootstrap standard-library operation requires the reference or generated-C backend; use 'erist build'")

        if isinstance(expr, IRUnicodeCall):
            raise ValueError("std.unicode currently requires the reference runtime or generated-C backend; use 'erist build'")

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
