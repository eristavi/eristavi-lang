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
class Block:
    statements: list[Stmt]
    location: SourceLocation


@dataclass(frozen=True)
class Parameter:
    name: str
    type_annotation: str | None
    location: SourceLocation


@dataclass(frozen=True)
class FunctionDecl(Stmt):
    name: str
    parameters: list[Parameter]
    return_type: str | None
    body: Block
    location: SourceLocation
    public: bool = False


@dataclass(frozen=True)
class ReturnStmt(Stmt):
    value: Expr | None
    location: SourceLocation


@dataclass(frozen=True)
class LetStmt(Stmt):
    name: str
    fixed: bool
    type_annotation: str | None
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
class IfStmt(Stmt):
    condition: Expr
    then_branch: Block
    else_branch: Block | None
    location: SourceLocation


@dataclass(frozen=True)
class WhileStmt(Stmt):
    condition: Expr
    body: Block
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
