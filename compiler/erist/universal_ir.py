from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .ir import (
    IRAssign,
    IRBinary,
    IRCall,
    IRConst,
    IRExpr,
    IRExprStmt,
    IRIf,
    IRLet,
    IRProgram,
    IRStmt,
    IRUnary,
    IRVar,
    IRWhile,
)

I64 = "i64"
BOOL = "bool"
VOID = "void"


@dataclass(frozen=True)
class UValue:
    id: int
    type_name: str


@dataclass(frozen=True)
class ULocal:
    id: int
    name: str
    type_name: str


@dataclass(frozen=True)
class UInstruction:
    op: str
    result: UValue | None = None
    args: tuple[UValue, ...] = ()
    local: int | None = None
    immediate: int | bool | None = None


@dataclass(frozen=True)
class UJump:
    target: str


@dataclass(frozen=True)
class UBranch:
    condition: UValue
    true_target: str
    false_target: str


@dataclass(frozen=True)
class UReturn:
    value: UValue | None = None


UTerminator = UJump | UBranch | UReturn


@dataclass
class UBlock:
    name: str
    instructions: list[UInstruction] = field(default_factory=list)
    terminator: UTerminator | None = None


@dataclass
class UFunction:
    name: str
    return_type: str
    locals: list[ULocal]
    blocks: list[UBlock]
    value_count: int


@dataclass
class UProgram:
    functions: list[UFunction]
    entry: str = "__entry"

    def function(self, name: str) -> UFunction:
        for fn in self.functions:
            if fn.name == name:
                return fn
        raise KeyError(name)


class UniversalLowerer:
    """Lower source-close typed IR into a small target-neutral control-flow IR.

    This first layer deliberately covers the scalar/control slice used by the
    first direct CPU backend. Unsupported higher-level values fail explicitly;
    they remain fully supported by the existing typed IR/C portability backend.
    """

    _types = {"Int": I64, "Bool": BOOL}

    def __init__(self):
        self.blocks: list[UBlock] = []
        self.current: UBlock | None = None
        self.locals: list[ULocal] = []
        self.scopes: list[dict[str, ULocal]] = []
        self.next_value = 0
        self.next_block = 0

    def lower(self, program: IRProgram) -> UProgram:
        # Function calls are intentionally not hidden behind the entry lowering:
        # the first direct backend is a real but bounded bootstrap slice.
        self.blocks = []
        self.locals = []
        self.scopes = [{}]
        self.next_value = 0
        self.next_block = 0
        self.current = self._new_block("entry")
        self._lower_statements(program.entry, new_scope=False)
        if self.current is not None and self.current.terminator is None:
            self.current.terminator = UReturn()
        self._validate()
        fn = UFunction("__entry", VOID, list(self.locals), list(self.blocks), self.next_value)
        return UProgram([fn])

    def _new_block(self, stem: str) -> UBlock:
        name = stem if not self.blocks else f"{stem}.{self.next_block}"
        self.next_block += 1
        block = UBlock(name)
        self.blocks.append(block)
        return block

    def _new_value(self, type_name: str) -> UValue:
        value = UValue(self.next_value, type_name)
        self.next_value += 1
        return value

    def _emit(self, op: str, type_name: str | None = None, args: Iterable[UValue] = (), *, local: int | None = None, immediate=None) -> UValue | None:
        if self.current is None or self.current.terminator is not None:
            raise ValueError("cannot emit universal IR into a terminated block")
        result = self._new_value(type_name) if type_name is not None else None
        self.current.instructions.append(UInstruction(op, result, tuple(args), local, immediate))
        return result

    def _map_type(self, source_type: str) -> str:
        try:
            return self._types[source_type]
        except KeyError:
            raise ValueError(
                f"universal IR bootstrap currently supports Int and Bool values, got {source_type}"
            )

    def _declare(self, name: str, type_name: str) -> ULocal:
        local = ULocal(len(self.locals), name, type_name)
        self.locals.append(local)
        self.scopes[-1][name] = local
        return local

    def _lookup(self, name: str) -> ULocal:
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        raise ValueError(f"universal IR cannot resolve local {name!r}")

    def _lower_statements(self, statements: list[IRStmt], *, new_scope: bool) -> None:
        if new_scope:
            self.scopes.append({})
        try:
            for stmt in statements:
                if self.current is None or self.current.terminator is not None:
                    break
                self._stmt(stmt)
        finally:
            if new_scope:
                self.scopes.pop()

    def _stmt(self, stmt: IRStmt) -> None:
        if isinstance(stmt, IRLet):
            t = self._map_type(stmt.type_name)
            value = self._expr(stmt.value)
            if value is None or value.type_name != t:
                raise ValueError("universal IR let type mismatch")
            local = self._declare(stmt.name, t)
            self._emit("store_local", args=(value,), local=local.id)
            return
        if isinstance(stmt, IRAssign):
            local = self._lookup(stmt.name)
            value = self._expr(stmt.value)
            if value is None or value.type_name != local.type_name:
                raise ValueError("universal IR assignment type mismatch")
            self._emit("store_local", args=(value,), local=local.id)
            return
        if isinstance(stmt, IRExprStmt):
            self._expr(stmt.expression)
            return
        if isinstance(stmt, IRIf):
            condition = self._expr(stmt.condition)
            if condition is None or condition.type_name != BOOL:
                raise ValueError("universal IR branch requires Bool")
            then_block = self._new_block("if.then")
            else_block = self._new_block("if.else")
            merge_block = self._new_block("if.end")
            assert self.current is not None
            # _new_block appends but does not switch current, so the branch is
            # installed on the original block.
            source = next(block for block in self.blocks if block.terminator is None and block is self.current)
            source.terminator = UBranch(condition, then_block.name, else_block.name)

            self.current = then_block
            self._lower_statements(stmt.then_body, new_scope=True)
            if self.current.terminator is None:
                self.current.terminator = UJump(merge_block.name)

            self.current = else_block
            self._lower_statements(stmt.else_body, new_scope=True)
            if self.current.terminator is None:
                self.current.terminator = UJump(merge_block.name)

            self.current = merge_block
            return
        if isinstance(stmt, IRWhile):
            cond_block = self._new_block("while.cond")
            body_block = self._new_block("while.body")
            end_block = self._new_block("while.end")
            assert self.current is not None
            source = self.current
            source.terminator = UJump(cond_block.name)

            self.current = cond_block
            condition = self._expr(stmt.condition)
            if condition is None or condition.type_name != BOOL:
                raise ValueError("universal IR while requires Bool")
            self.current.terminator = UBranch(condition, body_block.name, end_block.name)

            self.current = body_block
            self._lower_statements(stmt.body, new_scope=True)
            if self.current.terminator is None:
                self.current.terminator = UJump(cond_block.name)

            self.current = end_block
            return
        raise ValueError(f"universal IR bootstrap does not yet lower {type(stmt).__name__}")

    def _expr(self, expr: IRExpr) -> UValue | None:
        if isinstance(expr, IRConst):
            if expr.type_name == "Int":
                return self._emit("const_i64", I64, immediate=int(expr.value))
            if expr.type_name == "Bool":
                return self._emit("const_bool", BOOL, immediate=bool(expr.value))
            raise ValueError(f"universal IR constant type {expr.type_name} is not yet supported")
        if isinstance(expr, IRVar):
            local = self._lookup(expr.name)
            return self._emit("load_local", local.type_name, local=local.id)
        if isinstance(expr, IRUnary):
            value = self._expr(expr.operand)
            if value is None:
                raise ValueError("unary operator requires a value")
            if expr.operator == "not":
                return self._emit("bool_not", BOOL, (value,))
            if expr.operator == "-" and value.type_name == I64:
                return self._emit("neg_checked", I64, (value,))
            raise ValueError(f"universal IR does not support unary {expr.operator!r} for {expr.type_name}")
        if isinstance(expr, IRBinary):
            if expr.operator in ("and", "or"):
                raise ValueError("universal IR short-circuit Boolean lowering is not in the first direct-backend slice")
            left = self._expr(expr.left)
            right = self._expr(expr.right)
            if left is None or right is None:
                raise ValueError("binary operator requires values")
            arithmetic = {
                "+": "add_checked",
                "-": "sub_checked",
                "*": "mul_checked",
                "/": "div_checked",
                "%": "rem_checked",
            }
            comparisons = {
                "==": "cmp_eq",
                "!=": "cmp_ne",
                "<": "cmp_lt",
                "<=": "cmp_le",
                ">": "cmp_gt",
                ">=": "cmp_ge",
            }
            if expr.operator in arithmetic and left.type_name == I64 and right.type_name == I64:
                return self._emit(arithmetic[expr.operator], I64, (left, right))
            if expr.operator in comparisons and left.type_name == right.type_name and left.type_name in (I64, BOOL):
                return self._emit(comparisons[expr.operator], BOOL, (left, right))
            raise ValueError(f"universal IR does not support binary {expr.operator!r} for {expr.left.type_name}")
        if isinstance(expr, IRCall) and expr.name == "output":
            if len(expr.arguments) != 1:
                raise ValueError("output requires one argument")
            value = self._expr(expr.arguments[0])
            if value is None:
                raise ValueError("output requires a value")
            if value.type_name == I64:
                self._emit("output_i64", args=(value,))
                return None
            if value.type_name == BOOL:
                self._emit("output_bool", args=(value,))
                return None
            raise ValueError("first direct backend output supports Int and Bool")
        if isinstance(expr, IRCall):
            raise ValueError(f"universal IR bootstrap does not yet lower function call {expr.name!r}")
        raise ValueError(f"universal IR bootstrap does not yet lower {type(expr).__name__}")

    def _validate(self) -> None:
        names = {block.name for block in self.blocks}
        if len(names) != len(self.blocks):
            raise ValueError("duplicate universal IR block name")
        for block in self.blocks:
            if block.terminator is None:
                raise ValueError(f"universal IR block {block.name!r} has no terminator")
            term = block.terminator
            if isinstance(term, UJump) and term.target not in names:
                raise ValueError(f"universal IR jump targets missing block {term.target!r}")
            if isinstance(term, UBranch):
                if term.condition.type_name != BOOL:
                    raise ValueError("universal IR branch condition must be Bool")
                if term.true_target not in names or term.false_target not in names:
                    raise ValueError("universal IR branch target is missing")


def format_program(program: UProgram) -> str:
    lines: list[str] = []
    for fn in program.functions:
        lines.append(f"function @{fn.name}() -> {fn.return_type} {{")
        for local in fn.locals:
            lines.append(f"  local ${local.id} {local.name}: {local.type_name}")
        for block in fn.blocks:
            lines.append(f"{block.name}:")
            for instruction in block.instructions:
                lhs = f"%{instruction.result.id}:{instruction.result.type_name} = " if instruction.result else ""
                operands = ", ".join(f"%{value.id}" for value in instruction.args)
                detail = ""
                if instruction.local is not None:
                    detail = f" ${instruction.local}" + (f", {operands}" if operands else "")
                elif instruction.immediate is not None:
                    detail = f" {str(instruction.immediate).lower()}"
                elif operands:
                    detail = f" {operands}"
                lines.append(f"  {lhs}{instruction.op}{detail}")
            term = block.terminator
            if isinstance(term, UJump):
                lines.append(f"  jump {term.target}")
            elif isinstance(term, UBranch):
                lines.append(f"  branch %{term.condition.id}, {term.true_target}, {term.false_target}")
            elif isinstance(term, UReturn):
                lines.append("  return" if term.value is None else f"  return %{term.value.id}")
        lines.append("}")
    return "\n".join(lines) + "\n"
