from __future__ import annotations

from .diagnostics import SemanticError
from .semantic import Analyzer
from .syntax import ListExpr, LiteralExpr, UnaryExpr
from .typesys import BYTES, resolve


def install_collection_validation() -> None:
    if getattr(Analyzer, "_eristavi_collection_validation_installed", False):
        return

    base_expr = Analyzer._expr

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
        return base_expr(self, expression, value_required, allow_checked)

    Analyzer._expr = expr
    Analyzer._eristavi_collection_validation_installed = True
