from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

from .diagnostics import RuntimeFault
from .syntax import AssignStmt, BinaryExpr, CallExpr, Expr, ExprStmt, LetStmt, LiteralExpr, NameExpr, Program, UnaryExpr

INT_MIN = -(2**63)
INT_MAX = 2**63 - 1


@dataclass
class Cell:
    value: object
    fixed: bool


class Interpreter:
    def __init__(self, output: Callable[[str], None] = print):
        self.env: dict[str, Cell] = {}
        self.output_sink = output

    def run(self, program: Program) -> None:
        for stmt in program.statements:
            if isinstance(stmt, LetStmt):
                self.env[stmt.name] = Cell(self._expr(stmt.initializer), stmt.fixed)
            elif isinstance(stmt, AssignStmt):
                cell = self.env[stmt.name]
                if cell.fixed:
                    raise RuntimeFault(f"cannot assign to fixed binding {stmt.name!r}", stmt.location)
                cell.value = self._expr(stmt.value)
            elif isinstance(stmt, ExprStmt):
                self._expr(stmt.expression)
            else:
                raise RuntimeFault("statement is not implemented by the bootstrap runtime")

    def _expr(self, expr: Expr):
        if isinstance(expr, LiteralExpr):
            return expr.value

        if isinstance(expr, NameExpr):
            if expr.name in self.env:
                return self.env[expr.name].value
            if expr.name == "output":
                return "<builtin output>"
            raise RuntimeFault(f"unknown name {expr.name!r}", expr.location)

        if isinstance(expr, UnaryExpr):
            value = self._expr(expr.operand)
            if expr.operator == "not":
                return not value
            if expr.operator == "-":
                result = -value
                if isinstance(value, int) and not isinstance(value, bool):
                    return self._check_int(result, expr)
                return result

        if isinstance(expr, BinaryExpr):
            if expr.operator == "and":
                left = self._expr(expr.left)
                return bool(left) and bool(self._expr(expr.right))
            if expr.operator == "or":
                left = self._expr(expr.left)
                return bool(left) or bool(self._expr(expr.right))

            left = self._expr(expr.left)
            right = self._expr(expr.right)
            op = expr.operator

            if op == "+":
                result = left + right
                return self._checked_numeric(result, left, expr)
            if op == "-":
                result = left - right
                return self._checked_numeric(result, left, expr)
            if op == "*":
                result = left * right
                return self._checked_numeric(result, left, expr)
            if op == "/":
                if isinstance(left, int) and not isinstance(left, bool):
                    return self._int_div(left, right, expr)
                return self._float_div(float(left), float(right))
            if op == "%":
                return self._int_rem(int(left), int(right), expr)
            if op == "==":
                return left == right
            if op == "!=":
                return left != right
            if op == "<":
                return left < right
            if op == "<=":
                return left <= right
            if op == ">":
                return left > right
            if op == ">=":
                return left >= right

        if isinstance(expr, CallExpr):
            if isinstance(expr.callee, NameExpr) and expr.callee.name == "output":
                value = self._expr(expr.arguments[0])
                self.output_sink(self._format(value))
                return None

        raise RuntimeFault("expression is not implemented by the bootstrap runtime", getattr(expr, "location", None))

    def _checked_numeric(self, result, left, expr):
        if isinstance(left, int) and not isinstance(left, bool):
            return self._check_int(result, expr)
        return result

    def _check_int(self, value: int, expr):
        if value < INT_MIN or value > INT_MAX:
            raise RuntimeFault("signed 64-bit Int overflow", expr.location)
        return value

    def _int_div(self, a: int, b: int, expr) -> int:
        if b == 0:
            raise RuntimeFault("Int division by zero", expr.location)
        if a == INT_MIN and b == -1:
            raise RuntimeFault("signed 64-bit Int overflow", expr.location)
        q = abs(a) // abs(b)
        if (a < 0) != (b < 0):
            q = -q
        return q

    def _int_rem(self, a: int, b: int, expr) -> int:
        if b == 0:
            raise RuntimeFault("Int remainder by zero", expr.location)
        if a == INT_MIN and b == -1:
            raise RuntimeFault("signed 64-bit Int overflow", expr.location)
        q = self._int_div(a, b, expr)
        return a - q * b

    @staticmethod
    def _float_div(a: float, b: float) -> float:
        if b != 0.0:
            return a / b
        if math.isnan(a):
            return math.nan
        if a == 0.0:
            return math.nan
        sign = math.copysign(1.0, a) * math.copysign(1.0, b)
        return math.copysign(math.inf, sign)

    @staticmethod
    def _format(value: object) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        return str(value)
