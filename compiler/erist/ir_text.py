from __future__ import annotations

from dataclasses import dataclass

from .diagnostics import SemanticError
from .ir import IRExpr, IRIndex, Lowerer as BaseLowerer, STD_FILE, STD_FILE_ERROR
from .syntax import IndexExpr, MemberExpr, NameExpr
from .typesys import (
    AnyErrorType,
    BOOL,
    FLOAT,
    INT,
    NO_VALUE,
    TEXT,
    IdentityType,
    ListType,
    MaybeType,
    NamedType,
    ResourceType,
    TextViewType,
    resolve,
)


@dataclass(frozen=True)
class IRTextView(IRExpr):
    base: IRExpr
    kind: str


@dataclass(frozen=True)
class IRTextViewCount(IRExpr):
    view: IRExpr


@dataclass(frozen=True)
class IRTextViewIndex(IRExpr):
    view: IRExpr
    index: IRExpr


class Lowerer(BaseLowerer):
    """Typed-IR extension for explicit Unicode Text views.

    The IR can represent all three frozen view kinds.  The active C bootstrap
    backend currently executes byte/scalar views and deliberately rejects
    grapheme-cluster views until it has pinned Unicode 17 segmentation tables.
    """

    @staticmethod
    def _supported_type(t, loc):
        if t.startswith("Text ") and t.endswith(" view"):
            return
        return BaseLowerer._supported_type(t, loc)

    @staticmethod
    def _type_from_name(t):
        if t == "Text characters view":
            return TextViewType("characters")
        if t == "Text scalars view":
            return TextViewType("scalars")
        if t == "Text bytes view":
            return TextViewType("bytes")
        if t == "checked error":
            return AnyErrorType()
        if t == STD_FILE:
            return ResourceType(STD_FILE, (STD_FILE_ERROR,))
        if t.startswith("maybe "):
            return MaybeType(Lowerer._type_from_name(t[6:]))
        if t.startswith("identity "):
            return IdentityType(Lowerer._type_from_name(t[9:]))
        if t.startswith("List of "):
            return ListType(Lowerer._type_from_name(t[8:]))
        if t == "Int":
            return INT
        if t == "Float":
            return FLOAT
        if t == "Bool":
            return BOOL
        if t == "Text":
            return TEXT
        if t == "no-value":
            return NO_VALUE
        return NamedType(t)

    def _expr_type(self, e):
        if isinstance(e, IndexExpr):
            bt = resolve(self._expr_type(e.base))
            if isinstance(bt, TextViewType):
                return INT if bt.kind == "bytes" else TEXT
        if isinstance(e, MemberExpr):
            bt = resolve(self._expr_type(e.base))
            if bt == TEXT and e.name in ("characters", "scalars", "bytes"):
                return TextViewType(e.name)
            if isinstance(bt, TextViewType) and e.name == "count":
                return INT
        return super()._expr_type(e)

    def _ast_type(self, e):
        if isinstance(e, MemberExpr):
            bt = resolve(self._expr_type(e.base))
            if bt == TEXT and e.name in ("characters", "scalars", "bytes"):
                return TextViewType(e.name)
            if isinstance(bt, TextViewType) and e.name == "count":
                return INT
        if isinstance(e, IndexExpr):
            bt = resolve(self._expr_type(e.base))
            if isinstance(bt, TextViewType):
                return INT if bt.kind == "bytes" else TEXT
        return super()._ast_type(e)

    def _expr(self, e):
        if isinstance(e, MemberExpr):
            bt = resolve(self._expr_type(e.base))
            if bt == TEXT and e.name in ("characters", "scalars", "bytes"):
                semantic_t = f"Text {e.name} view"
                self._supported_type(semantic_t, e.location)
                return IRTextView(semantic_t, e.location, self._expr(e.base), e.name)
            if isinstance(bt, TextViewType) and e.name == "count":
                return IRTextViewCount("Int", e.location, self._expr(e.base))
        if isinstance(e, IndexExpr):
            bt = resolve(self._expr_type(e.base))
            if isinstance(bt, TextViewType):
                result = "Int" if bt.kind == "bytes" else "Text"
                return IRTextViewIndex(result, e.location, self._expr(e.base), self._expr(e.index))
        return super()._expr(e)
