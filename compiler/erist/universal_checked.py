from __future__ import annotations

from .ir import (
    IRAssign,
    IRCall,
    IRExpr,
    IRFail,
    IRHandledAssign,
    IRHandledExprStmt,
    IRHandledLet,
    IRHandledReturn,
    IRIndex,
    IRMember,
    IRVar,
)
from .universal_ir import (
    BOOL,
    F64,
    I64,
    TEXT,
    VOID,
    UBranch,
    UJump,
    UReturn,
    UValue,
    UniversalLowerer,
)


class CheckedUniversalLowerer(UniversalLowerer):
    """Universal lowering layer for Eristavi checked failures.

    Checked failure state is explicit in Universal IR. A target provides a small
    error-state runtime, while control flow (capture, typed dispatch, propagation)
    is represented with ordinary IR blocks and branches. This avoids target-local
    exception semantics and keeps the source `fails` contract visible below the
    frontend.
    """

    def __init__(self):
        super().__init__()
        self.capture_checked_depth = 0

    def _map_type(self, source_type: str) -> str:
        if source_type == "checked error":
            return "error<any>"
        return super()._map_type(source_type)

    def _default_return(self) -> UValue | None:
        if self.current_return == VOID:
            return None
        if self.current_return == I64:
            value = self._emit("const_i64", I64, immediate=0)
        elif self.current_return == BOOL:
            value = self._emit("const_bool", BOOL, immediate=False)
        elif self.current_return == F64:
            value = self._emit("const_f64", F64, immediate=0.0)
        elif self.current_return == TEXT:
            value = self._emit("const_text", TEXT, immediate="")
        else:
            value = self._emit("zero_value", self.current_return, immediate=self.current_return)
        assert value is not None
        return value

    def _terminate_propagation(self) -> None:
        assert self.current is not None
        self.current.terminator = UReturn(self._default_return())

    def _propagate_if_pending(self) -> None:
        pending = self._emit("error_pending", BOOL)
        assert pending is not None
        source = self.current
        fail_block = self._new_block("error.propagate")
        success_block = self._new_block("error.continue")
        assert source is not None
        source.terminator = UBranch(pending, fail_block.name, success_block.name)
        self.current = fail_block
        self._terminate_propagation()
        self.current = success_block

    def _capture_expr(self, expr: IRExpr) -> UValue | None:
        self.capture_checked_depth += 1
        try:
            return self._expr(expr)
        finally:
            self.capture_checked_depth -= 1

    def _stmt(self, stmt) -> None:
        if isinstance(stmt, IRFail):
            value = self._expr(stmt.value)
            if value is None:
                raise ValueError("fail requires an error value")
            value = self._clone(value)
            self._emit("set_error", args=(value,), immediate=stmt.error_type)
            self._terminate_propagation()
            return
        if isinstance(stmt, IRHandledLet):
            target_type = self._map_type(stmt.type_name)
            local = self._declare(stmt.name, target_type)
            self._lower_handled(
                stmt.value,
                stmt.handlers,
                lambda value: self._store_checked_local(local.id, target_type, value),
            )
            return
        if isinstance(stmt, IRHandledAssign):
            self._lower_handled(
                stmt.value,
                stmt.handlers,
                lambda value: self._store_handled_target(stmt.target, self._map_type(stmt.target_type), value),
            )
            return
        if isinstance(stmt, IRHandledReturn):
            def success(value: UValue | None) -> None:
                if value is None or value.type_name != self.current_return:
                    raise ValueError("handled return type mismatch")
                assert self.current is not None
                self.current.terminator = UReturn(self._clone(value))
            self._lower_handled(stmt.value, stmt.handlers, success)
            return
        if isinstance(stmt, IRHandledExprStmt):
            self._lower_handled(stmt.value, stmt.handlers, lambda value: None)
            return
        super()._stmt(stmt)

    def _store_checked_local(self, local_id: int, target_type: str, value: UValue | None) -> None:
        if value is None or value.type_name != target_type:
            raise ValueError("handled let type mismatch")
        self._emit("store_local", args=(self._clone(value),), local=local_id)

    def _store_handled_target(self, target: IRExpr, target_type: str, value: UValue | None) -> None:
        if value is None or value.type_name != target_type:
            raise ValueError("handled assignment type mismatch")
        value = self._clone(value)
        if isinstance(target, IRVar):
            local = self._lookup(target.name)
            self._emit("store_local", args=(value,), local=local.id)
            return
        if isinstance(target, IRIndex):
            base = self._expr(target.base)
            index = self._expr(target.index)
            if base is None or index is None:
                raise ValueError("malformed handled indexed assignment")
            self._emit("list_set", args=(base, index, value), immediate=value.type_name)
            return
        if isinstance(target, IRMember):
            base, field_type, index = self._member_target(target)
            if field_type != target_type:
                raise ValueError("handled member assignment type mismatch")
            self._emit("set_field", args=(base, value), immediate={"index": index, "field": target.name})
            return
        raise ValueError("unsupported handled assignment target")

    def _lower_handled(self, expr: IRExpr, handlers, success_action) -> None:
        value = self._capture_expr(expr)
        pending = self._emit("error_pending", BOOL)
        assert pending is not None
        source = self.current
        success_block = self._new_block("error.success")
        dispatch_block = self._new_block("error.dispatch")
        merge_block = self._new_block("error.end")
        assert source is not None
        source.terminator = UBranch(pending, dispatch_block.name, success_block.name)

        self.current = success_block
        success_action(value)
        if self.current.terminator is None:
            self.current.terminator = UJump(merge_block.name)

        self.current = dispatch_block
        for index, handler in enumerate(handlers):
            handler_block = self._new_block(f"error.handler.{index}")
            if handler.error_type is None:
                self.current.terminator = UJump(handler_block.name)
                next_block = None
            else:
                match = self._emit("error_matches", BOOL, immediate=handler.error_type)
                assert match is not None
                next_block = self._new_block(f"error.next.{index}")
                self.current.terminator = UBranch(match, handler_block.name, next_block.name)

            self.current = handler_block
            self.scopes.append({})
            try:
                error_type = "error<any>" if handler.error_type is None else self._map_type(handler.error_type)
                error_value = self._emit("error_value", error_type, immediate=handler.error_type)
                assert error_value is not None
                error_local = self._declare("error", error_type)
                self._emit("store_local", args=(error_value,), local=error_local.id)
                self._emit("error_clear")
                self._lower_statements(handler.body, new_scope=False)
            finally:
                self.scopes.pop()
            if self.current.terminator is None:
                self.current.terminator = UJump(merge_block.name)

            if next_block is None:
                self.current = merge_block
                return
            self.current = next_block

        # Frontend exhaustiveness should make this unreachable. Keeping explicit
        # propagation here makes malformed/object IR safe rather than swallowing
        # a checked failure.
        self._terminate_propagation()
        self.current = merge_block

    def _expr(self, expr: IRExpr) -> UValue | None:
        if isinstance(expr, IRMember) and expr.base.type_name == "checked error":
            if expr.name != "message":
                raise ValueError("catch-all checked error exposes only message")
            base = self._expr(expr.base)
            if base is None or base.type_name != "error<any>":
                raise ValueError("malformed catch-all error value")
            result = self._emit("error_message", TEXT, (base,))
            assert result is not None
            return result

        if isinstance(expr, IRCall) and expr.name != "output":
            signature = self.known_functions.get(expr.name)
            if signature is None:
                return super()._expr(expr)
            parameter_types, result_type, fails = signature
            args = [self._expr(arg) for arg in expr.arguments]
            if any(arg is None for arg in args):
                raise ValueError("function arguments must produce values")
            concrete = [arg for arg in args if arg is not None]
            if [arg.type_name for arg in concrete] != parameter_types:
                raise ValueError(f"universal IR call contract mismatch for {expr.name!r}")
            transferred = [self._clone(arg) for arg in concrete]
            result = self._emit("call", None if result_type == VOID else result_type, transferred, immediate=expr.name)
            if fails and self.capture_checked_depth == 0:
                self._propagate_if_pending()
            return result

        return super()._expr(expr)
