from __future__ import annotations

from .diagnostics import SemanticError
from .semantic import Analyzer as BaseAnalyzer, STD_FILE_ERROR
from .syntax import CallExpr, IndexExpr, MemberExpr, NameExpr
from .typesys import (
    BOOL,
    INT,
    NO_VALUE,
    TEXT,
    TEXT_BYTES,
    TEXT_CHARACTERS,
    TEXT_SCALARS,
    ListType,
    TextViewType,
    TypeVar,
    resolve,
    unify,
)


class Analyzer(BaseAnalyzer):
    """Frontend extensions for pinned Unicode/Text and small stdlib additions."""

    def _member(self, expr, allow_checked):
        bt = resolve(self._expr(expr.base, True, allow_checked))
        fails = set(self.expr_failures.get(id(expr.base), set()))

        if bt == TEXT:
            if expr.name == "characters":
                return self._record(expr, TEXT_CHARACTERS, fails)
            if expr.name == "scalars":
                return self._record(expr, TEXT_SCALARS, fails)
            if expr.name == "bytes":
                return self._record(expr, TEXT_BYTES, fails)

        if isinstance(bt, TextViewType):
            if expr.name == "count":
                return self._record(expr, INT, fails)
            raise SemanticError(
                f"Text {bt.kind} view has no member {expr.name!r} in pre-0.1",
                expr.location,
            )

        return super()._member(expr, allow_checked)

    def _call(self, expr: CallExpr, value_required, allow_checked):
        if (
            isinstance(expr.callee, MemberExpr)
            and isinstance(expr.callee.base, NameExpr)
            and expr.callee.base.name in self.imports
            and self.imports[expr.callee.base.name] == ("std", "files")
            and expr.callee.name in ("exists", "remove")
        ):
            if len(expr.arguments) != 1:
                raise SemanticError(f"files.{expr.callee.name}(path) takes one Text argument", expr.location)
            path_type = self._expr(expr.arguments[0], True, allow_checked)
            self._require_type(path_type, TEXT, expr.arguments[0].location, f"files.{expr.callee.name}(path) requires Text")
            failures = {STD_FILE_ERROR}
            if not allow_checked:
                raise SemanticError(
                    f"files.{expr.callee.name}(path) may fail with std.files.FileError; handle it with 'else error' or propagate it with 'try'",
                    expr.location,
                )
            return self._record(expr, BOOL if expr.callee.name == "exists" else NO_VALUE, failures)
        return super()._call(expr, value_required, allow_checked)

    def _expr(self, expr, value_required=True, allow_checked=False):
        if isinstance(expr, IndexExpr):
            raw_bt = self._expr(expr.base, True, allow_checked)
            bt = resolve(raw_bt)
            if isinstance(bt, TextViewType):
                it = self._expr(expr.index, True, allow_checked)
                self._require_type(
                    it,
                    INT,
                    expr.index.location,
                    "Text view index must have static type Int",
                )
                fails = (
                    set(self.expr_failures.get(id(expr.base), set()))
                    | set(self.expr_failures.get(id(expr.index), set()))
                )
                result = INT if bt.kind == "bytes" else TEXT
                return self._record(expr, result, fails)
        return super()._expr(expr, value_required, allow_checked)

    def _target_type(self, target, for_write=False):
        if isinstance(target, IndexExpr):
            raw_bt = self._expr(target.base, True, False)
            bt = resolve(raw_bt)
            if isinstance(bt, TextViewType):
                self._require_type(
                    self._expr(target.index, True, False),
                    INT,
                    target.index.location,
                    "Text view index must have static type Int",
                )
                if for_write:
                    raise SemanticError("Text views are read-only", target.location)
                return INT if bt.kind == "bytes" else TEXT

            # Reading through a generic indexed expression already shapes an
            # unresolved parameter as List<T>.  Indexed assignment must impose
            # the same relationship so generic functions can express ordinary
            # List mutation without explicit generic syntax.  The List is still
            # passed by value; this only completes the inference relationship.
            if isinstance(bt, TypeVar):
                element = TypeVar("element")
                shaped = ListType(element)
                unify(raw_bt, shaped)
                self._require_type(
                    self._expr(target.index, True, False),
                    INT,
                    target.index.location,
                    "List index must have type Int",
                )
                return element

        if isinstance(target, MemberExpr):
            bt = resolve(self._expr(target.base, True, False))
            if isinstance(bt, TextViewType):
                raise SemanticError("Text views are read-only", target.location)
        return super()._target_type(target, for_write)

    def _deep_fixable(self, t, seen):
        if isinstance(resolve(t), TextViewType):
            return True
        return super()._deep_fixable(t, seen)
