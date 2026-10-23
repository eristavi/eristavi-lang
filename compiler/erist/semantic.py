from __future__ import annotations

from dataclasses import dataclass

from .diagnostics import SemanticError
from .syntax import AssignStmt, BinaryExpr, CallExpr, Expr, ExprStmt, LetStmt, LiteralExpr, NameExpr, Program, UnaryExpr


@dataclass
class Symbol:
    type_name: str
    fixed: bool


class Analyzer:
    def __init__(self):
        self.symbols: dict[str, Symbol] = {}
        self.expr_types: dict[int, str] = {}

    def analyze(self, program: Program) -> dict[int, str]:
        for stmt in program.statements:
            if isinstance(stmt, LetStmt):
                if stmt.name in self.symbols:
                    raise SemanticError(f"name {stmt.name!r} is already declared in this scope", stmt.location)
                type_name = self._expr(stmt.initializer)
                self.symbols[stmt.name] = Symbol(type_name, stmt.fixed)
            elif isinstance(stmt, AssignStmt):
                symbol = self.symbols.get(stmt.name)
                if symbol is None:
                    raise SemanticError(f"unknown name {stmt.name!r}", stmt.location)
                if symbol.fixed:
                    raise SemanticError(f"cannot assign to fixed binding {stmt.name!r}", stmt.location)
                rhs = self._expr(stmt.value)
                if rhs != symbol.type_name:
                    raise SemanticError(f"cannot assign {rhs} to {stmt.name!r} of type {symbol.type_name}", stmt.location)
            elif isinstance(stmt, ExprStmt):
                self._expr(stmt.expression)
            else:
                raise SemanticError("statement is not implemented by the bootstrap analyzer")
        return self.expr_types

    def _record(self, expr: Expr, type_name: str) -> str:
        self.expr_types[id(expr)] = type_name
        return type_name

    def _expr(self, expr: Expr) -> str:
        if isinstance(expr, LiteralExpr):
            if expr.type_name == "Int" and not (-2**63 <= int(expr.value) <= 2**63 - 1):
                raise SemanticError("Int literal is outside the signed 64-bit range", expr.location)
            return self._record(expr, expr.type_name)

        if isinstance(expr, NameExpr):
            if expr.name == "output":
                return self._record(expr, "<function output>")
            symbol = self.symbols.get(expr.name)
            if symbol is None:
                raise SemanticError(f"unknown name {expr.name!r}", expr.location)
            return self._record(expr, symbol.type_name)

        if isinstance(expr, UnaryExpr):
            operand = self._expr(expr.operand)
            if expr.operator == "-" and operand in ("Int", "Float"):
                return self._record(expr, operand)
            if expr.operator == "not" and operand == "Bool":
                return self._record(expr, "Bool")
            raise SemanticError(f"operator {expr.operator!r} is not defined for {operand}", expr.location)

        if isinstance(expr, BinaryExpr):
            left = self._expr(expr.left)
            right = self._expr(expr.right)
            op = expr.operator

            if op in ("and", "or"):
                if left == right == "Bool":
                    return self._record(expr, "Bool")
                raise SemanticError(f"{op} requires Bool operands", expr.location)

            if op in ("==", "!=", "<", "<=", ">", ">="):
                if left != right:
                    raise SemanticError(f"cannot compare {left} with {right} without an explicit conversion", expr.location)
                if left in ("Int", "Float", "Bool", "Text"):
                    if op in ("<", "<=", ">", ">=") and left == "Bool":
                        raise SemanticError(f"ordered comparison {op} is not defined for Bool", expr.location)
                    return self._record(expr, "Bool")
                raise SemanticError(f"comparison is not implemented for {left} in the bootstrap subset", expr.location)

            if op in ("+", "-", "*", "/", "%"):
                if left != right:
                    raise SemanticError(f"operator {op} does not implicitly mix {left} and {right}", expr.location)
                if left == "Int":
                    return self._record(expr, "Int")
                if left == "Float" and op != "%":
                    return self._record(expr, "Float")
                if left == "Float" and op == "%":
                    raise SemanticError("% is Int-only in pre-0.1; Float remainder requires a named API", expr.location)
                raise SemanticError(f"operator {op} is not defined for {left}", expr.location)

        if isinstance(expr, CallExpr):
            if isinstance(expr.callee, NameExpr) and expr.callee.name == "output":
                if len(expr.arguments) != 1:
                    raise SemanticError("output(...) takes exactly one argument in pre-0.1", expr.location)
                arg_type = self._expr(expr.arguments[0])
                if arg_type not in ("Int", "Float", "Bool", "Text"):
                    raise SemanticError(f"bootstrap output does not yet support {arg_type}", expr.location)
                return self._record(expr, "<no-value>")
            raise SemanticError("only the predeclared output(...) call is implemented in the first bootstrap slice", expr.location)

        raise SemanticError("expression is not implemented by the bootstrap analyzer")
