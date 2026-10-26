from __future__ import annotations

from .diagnostics import SemanticError
from .semantic import Analyzer
from .syntax import IndexExpr, ListExpr, LiteralExpr, UnaryExpr
from .typesys import BYTES, MapType, NamedType, resolve


def _stable_map_key(value) -> bool:
    actual = resolve(value)
    return isinstance(actual, NamedType) and actual.name in ("Int", "Bool", "Text")


def install_collection_validation() -> None:
    if getattr(Analyzer, "_eristavi_collection_validation_installed", False):
        return

    base_expr = Analyzer._expr
    base_target_type = Analyzer._target_type

    def expr(self, expression, value_required=True, allow_checked=False):
        if isinstance(expression, ListExpr):
            expected = getattr(self, "_collection_expected_type", None)
            if expected is not None and resolve(expected) == BYTES:
                for element in expression.elements:
                    value = None
                    if isinstance(element, LiteralExpr) and element.type_name == "Int":
                        value = int(element.value)
                    elif (
                        isinstance(element, UnaryExpr)
                        and element.operator == "-"
                        and isinstance(element.operand, LiteralExpr)
                        and element.operand.type_name == "Int"
                    ):
                        value = -int(element.operand.value)
                    if value is not None and not 0 <= value <= 255:
                        raise SemanticError(
                            "Bytes literal elements must be between 0 and 255",
                            element.location,
                        )

        result = base_expr(self, expression, value_required, allow_checked)

        # Empty Maps begin with unresolved key/value relationships. Indexed use
        # can resolve the key later, so re-apply the stable-key contract after
        # that unification instead of validating only non-empty Map literals.
        if isinstance(expression, IndexExpr):
            base_type = self.expr_types.get(id(expression.base))
            if base_type is not None:
                actual = resolve(base_type)
                if isinstance(actual, MapType) and not _stable_map_key(actual.key):
                    raise SemanticError(
                        "Map keys currently support only Int, Bool, and Text",
                        expression.index.location,
                    )
        return result

    def target_type(self, target, for_write=False):
        result = base_target_type(self, target, for_write)
        if isinstance(target, IndexExpr):
            base_type = self.expr_types.get(id(target.base))
            if base_type is not None:
                actual = resolve(base_type)
                if isinstance(actual, MapType) and not _stable_map_key(actual.key):
                    raise SemanticError(
                        "Map keys currently support only Int, Bool, and Text",
                        target.index.location,
                    )
        return result

    Analyzer._expr = expr
    Analyzer._target_type = target_type
    Analyzer._eristavi_collection_validation_installed = True
