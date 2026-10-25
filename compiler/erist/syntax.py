from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from .diagnostics import SourceLocation

@dataclass(frozen=True)
class TypeRef:
    path: tuple[str, ...]
    maybe: bool = False
    identity: bool = False
    location: SourceLocation | None = None

@dataclass(frozen=True)
class Program:
    statements: list[Stmt]
class Stmt: pass
class Expr: pass

@dataclass(frozen=True)
class Block:
    statements: list[Stmt]
    location: SourceLocation
@dataclass(frozen=True)
class Parameter:
    name: str; type_annotation: TypeRef|None; location: SourceLocation
@dataclass(frozen=True)
class FieldDecl:
    name: str; type_ref: TypeRef; fixed: bool; location: SourceLocation
@dataclass(frozen=True)
class FunctionDecl(Stmt):
    name: str; parameters: list[Parameter]; return_type: TypeRef|None; fails: list[TypeRef]; body: Block; location: SourceLocation; public: bool=False
@dataclass(frozen=True)
class TypeDecl(Stmt):
    name: str; fields: list[FieldDecl]; location: SourceLocation; public: bool=False
@dataclass(frozen=True)
class ErrorDecl(Stmt):
    name: str; fields: list[FieldDecl]; location: SourceLocation; public: bool=False
@dataclass(frozen=True)
class ImportDecl(Stmt):
    path: tuple[str,...]; alias: str|None; location: SourceLocation
@dataclass(frozen=True)
class ReturnStmt(Stmt): value: Expr|None; location: SourceLocation
@dataclass(frozen=True)
class FailStmt(Stmt): value: Expr; location: SourceLocation
@dataclass(frozen=True)
class LetStmt(Stmt): name: str; fixed: bool; type_annotation: TypeRef|None; initializer: Expr; location: SourceLocation
@dataclass(frozen=True)
class AssignStmt(Stmt): target: Expr; value: Expr; location: SourceLocation
@dataclass(frozen=True)
class ExprStmt(Stmt): expression: Expr; location: SourceLocation
@dataclass(frozen=True)
class IfStmt(Stmt): condition: Expr; then_branch: Block; else_branch: Block|None; location: SourceLocation
@dataclass(frozen=True)
class WhileStmt(Stmt): condition: Expr; body: Block; location: SourceLocation
@dataclass(frozen=True)
class ForStmt(Stmt): name: str; iterable: Expr; body: Block; location: SourceLocation
@dataclass(frozen=True)
class WithStmt(Stmt): name: str; type_annotation: TypeRef|None; resource: Expr; body: Block; location: SourceLocation

@dataclass(frozen=True)
class LiteralExpr(Expr): value: Any; type_name: str; location: SourceLocation
@dataclass(frozen=True)
class NoneExpr(Expr): location: SourceLocation
@dataclass(frozen=True)
class ListExpr(Expr): elements: list[Expr]; location: SourceLocation
@dataclass(frozen=True)
class MapEntry:
    key: Expr; value: Expr; location: SourceLocation
@dataclass(frozen=True)
class MapExpr(Expr): entries: list[MapEntry]; location: SourceLocation
@dataclass(frozen=True)
class NameExpr(Expr): name: str; location: SourceLocation
@dataclass(frozen=True)
class UnaryExpr(Expr): operator: str; operand: Expr; location: SourceLocation
@dataclass(frozen=True)
class BinaryExpr(Expr): left: Expr; operator: str; right: Expr; location: SourceLocation
@dataclass(frozen=True)
class CallExpr(Expr): callee: Expr; arguments: list[Expr]; location: SourceLocation
@dataclass(frozen=True)
class MemberExpr(Expr): base: Expr; name: str; location: SourceLocation
@dataclass(frozen=True)
class IndexExpr(Expr): base: Expr; index: Expr; location: SourceLocation
@dataclass(frozen=True)
class FieldInit:
    name: str; value: Expr; location: SourceLocation
@dataclass(frozen=True)
class ConstructionExpr(Expr): type_path: tuple[str,...]; fields: list[FieldInit]; location: SourceLocation
@dataclass(frozen=True)
class IdentityExpr(Expr): value: Expr; location: SourceLocation
@dataclass(frozen=True)
class TryExpr(Expr): value: Expr; location: SourceLocation
@dataclass(frozen=True)
class ErrorHandler:
    type_ref: TypeRef|None; block: Block; location: SourceLocation
@dataclass(frozen=True)
class HandledExpr(Expr): value: Expr; handlers: list[ErrorHandler]; location: SourceLocation
