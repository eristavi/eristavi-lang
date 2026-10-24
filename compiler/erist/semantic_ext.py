from __future__ import annotations

from .diagnostics import SemanticError
from .semantic import Analyzer as BaseAnalyzer
from .syntax import IndexExpr, MemberExpr
from .typesys import (
    INT,
    TEXT,
    TEXT_BYTES,
    TEXT_CHARACTERS,
    TEXT_SCALARS,
    TextViewType,
    resolve,
)


class Analyzer(BaseAnalyzer):
    """Frontend analyzer extensions for the frozen Unicode Text-view model.

    The public language still exposes only Text and Int.  The three view types
    below are compiler-internal semantic markers used to make
    text.characters/scalars/bytes explicit without inventing new source-level
    Character, Scalar, or Byte type names.
    """

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
            bt = resolve(self._expr(target.base, True, False))
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
        if isinstance(target, MemberExpr):
            bt = resolve(self._expr(target.base, True, False))
            if isinstance(bt, TextViewType):
                raise SemanticError("Text views are read-only", target.location)
        return super()._target_type(target, for_write)

    def _deep_fixable(self, t, seen):
        if isinstance(resolve(t), TextViewType):
            return True
        return super()._deep_fixable(t, seen)
