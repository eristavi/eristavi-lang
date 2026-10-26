from __future__ import annotations

from dataclasses import dataclass

from .diagnostics import SemanticError
from .ir import IRCount, IRExpr, IRIndex, IRStmt
from .ir_text import Lowerer as TextLowerer
from .syntax import AssignStmt, IndexExpr, ListExpr, MapExpr, MemberExpr, NameExpr
from .typesys import BYTES, INT, MapType, describe, resolve


@dataclass(frozen=True)
class IRMapEntry:
    key: IRExpr
    value: IRExpr


@dataclass(frozen=True)
class IRMap(IRExpr):
    entries: tuple[IRMapEntry, ...]


@dataclass(frozen=True)
class IRBytes(IRExpr):
    elements: tuple[IRExpr, ...]


@dataclass(frozen=True)
class IRCollectionIndexAssign(IRStmt):
    name: str
    base_type: str
    index: IRExpr
    value: IRExpr
    location: object


class Lowerer(TextLowerer):
    """Typed-IR collection layer for inferred Map and contextual Bytes values.

    Map and Bytes intentionally remain distinct IR nodes rather than being
    encoded as Lists. That keeps their runtime representation and operations
    free to differ while preserving one square-bracket source syntax family.
    """

    @staticmethod
    def _type_from_name(t):
        if t == "Bytes":
            return BYTES
        if t.startswith("Map from "):
            relationship = t[len("Map from "):]
            key, separator, value = relationship.partition(" to ")
            if not separator or key not in ("Int", "Bool", "Text"):
                raise ValueError(f"invalid inferred Map type description: {t}")
            return MapType(Lowerer._type_from_name(key), Lowerer._type_from_name(value))
        return TextLowerer._type_from_name(t)

    @staticmethod
    def _supported_type(t, loc):
        if t == "Bytes":
            return
        if t.startswith("Map from "):
            relationship = t[len("Map from "):]
            key, separator, value = relationship.partition(" to ")
            if not separator or key not in ("Int", "Bool", "Text"):
                raise SemanticError(f"unsupported compiled Map relationship: {t}", loc)
            Lowerer._supported_type(value, loc)
            return
        return TextLowerer._supported_type(t, loc)

    def _expr_type(self, e):
        known = self.a.expr_types.get(id(e))
        if known is not None:
            actual = resolve(known)
            if actual == BYTES or isinstance(actual, MapType):
                return actual

        if isinstance(e, MapExpr):
            if not e.entries:
                if known is not None:
                    return resolve(known)
                raise SemanticError("cannot lower an unresolved empty Map", e.location)
            return MapType(self._expr_type(e.entries[0].key), self._expr_type(e.entries[0].value))

        if isinstance(e, IndexExpr):
            base = resolve(self._expr_type(e.base))
            if base == BYTES:
                return INT
            if isinstance(base, MapType):
                return resolve(base.value)

        if isinstance(e, MemberExpr) and e.name == "count":
            base = resolve(self._expr_type(e.base))
            if base == BYTES or isinstance(base, MapType):
                return INT

        return super()._expr_type(e)

    def _ast_type(self, e):
        if isinstance(e, IndexExpr):
            base = resolve(self._expr_type(e.base))
            if base == BYTES:
                return INT
            if isinstance(base, MapType):
                return resolve(base.value)
        if isinstance(e, MemberExpr) and e.name == "count":
            base = resolve(self._expr_type(e.base))
            if base == BYTES or isinstance(base, MapType):
                return INT
        return super()._ast_type(e)

    def _stmt(self, s):
        if isinstance(s, AssignStmt) and isinstance(s.target, IndexExpr) and isinstance(s.target.base, NameExpr):
            base = resolve(self._expr_type(s.target.base))
            if base == BYTES or isinstance(base, MapType):
                target_name = describe(self._ast_type(s.target))
                value = self._coerce(self._expr(s.value), target_name, s.location)
                return IRCollectionIndexAssign(
                    s.target.base.name,
                    describe(base),
                    self._expr(s.target.index),
                    value,
                    s.location,
                )
        return super()._stmt(s)

    def _expr(self, e):
        semantic_type = self._expr_type(e)
        semantic_name = self._describe_collection_type(semantic_type)

        if isinstance(e, ListExpr) and resolve(semantic_type) == BYTES:
            self._supported_type("Bytes", e.location)
            return IRBytes("Bytes", e.location, tuple(self._expr(item) for item in e.elements))

        if isinstance(e, MapExpr):
            self._supported_type(semantic_name, e.location)
            return IRMap(
                semantic_name,
                e.location,
                tuple(IRMapEntry(self._expr(entry.key), self._expr(entry.value)) for entry in e.entries),
            )

        if isinstance(e, IndexExpr):
            base_type = resolve(self._expr_type(e.base))
            if base_type == BYTES or isinstance(base_type, MapType):
                return IRIndex(semantic_name, e.location, self._expr(e.base), self._expr(e.index))

        if isinstance(e, MemberExpr) and e.name == "count":
            base_type = resolve(self._expr_type(e.base))
            if base_type == BYTES or isinstance(base_type, MapType):
                return IRCount("Int", e.location, self._expr(e.base))

        return super()._expr(e)

    @staticmethod
    def _describe_collection_type(t):
        actual = resolve(t)
        if actual == BYTES:
            return "Bytes"
        return describe(actual)
