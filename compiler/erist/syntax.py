from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .diagnostics import SourceLocation


@dataclass(frozen=True)
class Program:
    statements: list[Stmt]


class Stmt:
    pass


class Expr:
    pass


@dataclass(frozen=True)
class LetStmt(Stmt):
    name: str
    fixed: bool
    initializer: Expr
    location: SourceLocation


@dataclass(frozen=True)
class AssignStmt(Stmt):
    name: str
    value: Expr
    location: SourceLocation


@dataclass(frozen=True)
class ExprStmt(Stmt):
    expression: Expr
    location: SourceLocation


@dataclass(frozen=True)
class LiteralExpr(Expr):
    value: Any
    type_name: str
    location: SourceLocation


@dataclass(frozen=True)
class NameExpr(Expr):
    name: str
    location: SourceLocation


@dataclass(frozen=True)
class UnaryExpr(Expr):
    operator: str
    operand: Expr
    location: SourceLocation


@dataclass(frozen=True)
class BinaryExpr(Expr):
    left: Expr
    operator: str
    right: Expr
    location: SourceLocation


@dataclass(frozen=True)
class CallExpr(Expr):
    callee: Expr
    arguments: list[Expr]
    location: SourceLocation
