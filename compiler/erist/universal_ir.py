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
    IRFunction,
    IRIf,
    IRLet,
    IRProgram,
    IRReturn,
    IRStmt,
    IRUnary,
    IRVar,
    IRWhile,
)

I64 = "i64"
F64 = "f64"
BOOL = "bool"
TEXT = "text"
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
    immediate: object | None = None


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
    parameters: list[ULocal]
    locals: list[ULocal]
    blocks: list[UBlock]
    value_count: int
    public: bool = False


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
    """Lower source-close typed IR into target-neutral basic-block IR.

    Universal IR is deliberately below Eristavi's source-close typed IR.  It
    owns function/call structure, explicit control-flow, checked primitive
    arithmetic and target-neutral value types.  Higher-level runtime values are
    added here only when their representation contract is explicit.
    """

    _types = {"Int": I64, "Float": F64, "Bool": BOOL, "Text": TEXT}

    def __init__(self):
        self.blocks: list[UBlock] = []
        self.current: UBlock | None = None
        self.locals: list[ULocal] = []
        self.parameters: list[ULocal] = []
        self.scopes: list[dict[str, ULocal]] = []
        self.next_value = 0
        self.next_block = 0
        self.current_return = VOID
        self.known_functions: dict[str, tuple[list[str], str]] = {}

    def lower(self, program: IRProgram) -> UProgram:
        self.known_functions = {}
        for fn in program.functions:
            params = [self._map_type(p.type_name) for p in fn.parameters]
            result = VOID if fn.return_type is None else self._map_type(fn.return_type)
            self.known_functions[fn.name] = (params, result)

        functions = [self._lower_function(fn) for fn in program.functions]
        entry = self._lower_entry(program.entry)
        functions.append(entry)
        return UProgram(functions)

    def _reset_function(self, return_type: str) -> None:
        self.blocks = []
        self.locals = []
        self.parameters = []
        self.scopes = [{}]
        self.next_value = 0
        self.next_block = 0
        self.current_return = return_type
        self.current = self._new_block("entry")

    def _lower_entry(self, statements: list[IRStmt]) -> UFunction:
        self._reset_function(VOID)
        self._lower_statements(statements, new_scope=False)
        if self.current is not None and self.current.terminator is None:
            self.current.terminator = UReturn()
        self._validate()
        return UFunction("__entry", VOID, [], list(self.locals), list(self.blocks), self.next_value)

    def _lower_function(self, fn: IRFunction) -> UFunction:
        result = VOID if fn.return_type is None else self._map_type(fn.return_type)
        self._reset_function(result)
        for param in fn.parameters:
            t = self._map_type(param.type_name)
            local = self._declare(param.name, t)
            self.parameters.append(local)
        self._lower_statements(fn.body, new_scope=False)
        if self.current is not None and self.current.terminator is None:
            if result != VOID:
                raise ValueError(f"universal IR function {fn.name!r} can fall through without a value")
            self.current.terminator = UReturn()
        self._validate()
        return UFunction(
            fn.name,
            result,
            list(self.parameters),
            list(self.locals),
            list(self.blocks),
            self.next_value,
            fn.public,
        )

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

    def _emit(
        self,
        op: str,
        type_name: str | None = None,
        args: Iterable[UValue] = (),
        *,
        local: int | None = None,
        immediate=None,
    ) -> UValue | None:
        if self.current is None or self.current.terminator is not None:
            raise ValueError("cannot emit universal IR into a terminated block")
        result = self._new_value(type_name) if type_name is not None else None
        self.current.instructions.append(UInstruction(op, result, tuple(args), local, immediate))
        return result

    def _map_type(self, source_type: str) -> str:
        if source_type in self._types:
            return self._types[source_type]
        if source_type == "no-value":
            return VOID
        # Reserve stable representation names now so subsequent parity work can
        # target Universal IR without reopening the source language.
        if source_type.startswith("maybe "):
            return f"maybe<{self._map_type(source_type[6:])}>"
        if source_type.startswith("identity "):
            return f"identity<{self._map_type(source_type[9:])}>"
        if source_type.startswith("List of "):
            return f"list<{self._map_type(source_type[8:])}>"
        if source_type.startswith("std.files."):
            return f"resource<{source_type}>"
        # User values/errors stay nominal at this layer.
        return f"nominal<{source_type}>"

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
        if isinstance(stmt, IRReturn):
            if stmt.value is None:
                if self.current_return != VOID:
                    raise ValueError("value-returning universal function cannot use bare return")
                assert self.current is not None
                self.current.terminator = UReturn()
                return
            value = self._expr(stmt.value)
            if value is None or value.type_name != self.current_return:
                raise ValueError("universal IR return type mismatch")
            assert self.current is not None
            self.current.terminator = UReturn(value)
            return
        if isinstance(stmt, IRIf):
            condition = self._expr(stmt.condition)
            if condition is None or condition.type_name != BOOL:
                raise ValueError("universal IR branch requires Bool")
            source = self.current
            then_block = self._new_block("if.then")
            else_block = self._new_block("if.else")
            merge_block = self._new_block("if.end")
            assert source is not None
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
            source = self.current
            cond_block = self._new_block("while.cond")
            body_block = self._new_block("while.body")
            end_block = self._new_block("while.end")
            assert source is not None
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
        raise ValueError(f"universal IR does not yet lower statement {type(stmt).__name__}")

    def _expr(self, expr: IRExpr) -> UValue | None:
        if isinstance(expr, IRConst):
            if expr.type_name == "Int":
                return self._emit("const_i64", I64, immediate=int(expr.value))
            if expr.type_name == "Bool":
                return self._emit("const_bool", BOOL, immediate=bool(expr.value))
            if expr.type_name == "Float":
                return self._emit("const_f64", F64, immediate=float(expr.value))
            if expr.type_name == "Text":
                return self._emit("const_text", TEXT, immediate=str(expr.value))
            raise ValueError(f"universal IR constant type {expr.type_name} is not yet supported")
        if isinstance(expr, IRVar):
            local = self._lookup(expr.name)
            return self._emit("load_local", local.type_name, local=local.id)
        if isinstance(expr, IRUnary):
            value = self._expr(expr.operand)
            if value is None:
                raise ValueError("unary operator requires a value")
            if expr.operator == "not" and value.type_name == BOOL:
                return self._emit("bool_not", BOOL, (value,))
            if expr.operator == "-" and value.type_name == I64:
                return self._emit("neg_checked", I64, (value,))
            if expr.operator == "-" and value.type_name == F64:
                return self._emit("f64_neg", F64, (value,))
            raise ValueError(f"universal IR does not support unary {expr.operator!r} for {expr.type_name}")
        if isinstance(expr, IRBinary):
            if expr.operator in ("and", "or"):
                raise ValueError("universal IR short-circuit Boolean lowering remains a dedicated control-flow operation")
            left = self._expr(expr.left)
            right = self._expr(expr.right)
            if left is None or right is None:
                raise ValueError("binary operator requires values")
            int_arithmetic = {
                "+": "add_checked",
                "-": "sub_checked",
                "*": "mul_checked",
                "/": "div_checked",
                "%": "rem_checked",
            }
            float_arithmetic = {"+": "f64_add", "-": "f64_sub", "*": "f64_mul", "/": "f64_div"}
            comparisons = {"==": "cmp_eq", "!=": "cmp_ne", "<": "cmp_lt", "<=": "cmp_le", ">": "cmp_gt", ">=": "cmp_ge"}
            if expr.operator in int_arithmetic and left.type_name == I64 and right.type_name == I64:
                return self._emit(int_arithmetic[expr.operator], I64, (left, right))
            if expr.operator in float_arithmetic and left.type_name == F64 and right.type_name == F64:
                return self._emit(float_arithmetic[expr.operator], F64, (left, right))
            if expr.operator == "+" and left.type_name == TEXT and right.type_name == TEXT:
                return self._emit("text_concat", TEXT, (left, right))
            if expr.operator in comparisons and left.type_name == right.type_name:
                if left.type_name in (I64, BOOL):
                    return self._emit(comparisons[expr.operator], BOOL, (left, right))
                if left.type_name == F64:
                    return self._emit("f64_" + comparisons[expr.operator], BOOL, (left, right))
                if left.type_name == TEXT and expr.operator in ("==", "!="):
                    return self._emit("text_eq" if expr.operator == "==" else "text_ne", BOOL, (left, right))
            raise ValueError(f"universal IR does not support binary {expr.operator!r} for {expr.left.type_name}")
        if isinstance(expr, IRCall) and expr.name == "output":
            if len(expr.arguments) != 1:
                raise ValueError("output requires one argument")
            value = self._expr(expr.arguments[0])
            if value is None:
                raise ValueError("output requires a value")
            op = {I64: "output_i64", BOOL: "output_bool", F64: "output_f64", TEXT: "output_text"}.get(value.type_name)
            if op is None:
                raise ValueError(f"direct output does not yet support {value.type_name}")
            self._emit(op, args=(value,))
            return None
        if isinstance(expr, IRCall):
            signature = self.known_functions.get(expr.name)
            if signature is None:
                raise ValueError(f"universal IR cannot resolve function call {expr.name!r}")
            parameter_types, result_type = signature
            args = [self._expr(arg) for arg in expr.arguments]
            if any(arg is None for arg in args):
                raise ValueError("function arguments must produce values")
            concrete = [arg for arg in args if arg is not None]
            if [arg.type_name for arg in concrete] != parameter_types:
                raise ValueError(f"universal IR call contract mismatch for {expr.name!r}")
            return self._emit("call", None if result_type == VOID else result_type, concrete, immediate=expr.name)
        raise ValueError(f"universal IR does not yet lower expression {type(expr).__name__}")

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
            if isinstance(term, UReturn):
                if self.current_return == VOID and term.value is not None:
                    raise ValueError("no-value universal function returned a value")
                if term.value is not None and term.value.type_name != self.current_return:
                    raise ValueError("universal IR return type mismatch")


def format_program(program: UProgram) -> str:
    lines: list[str] = []
    for fn in program.functions:
        params = ", ".join(f"${p.id} {p.name}: {p.type_name}" for p in fn.parameters)
        lines.append(f"function @{fn.name}({params}) -> {fn.return_type} {{")
        parameter_ids = {p.id for p in fn.parameters}
        for local in fn.locals:
            prefix = "param" if local.id in parameter_ids else "local"
            lines.append(f"  {prefix} ${local.id} {local.name}: {local.type_name}")
        for block in fn.blocks:
            lines.append(f"{block.name}:")
            for instruction in block.instructions:
                lhs = f"%{instruction.result.id}:{instruction.result.type_name} = " if instruction.result else ""
                operands = ", ".join(f"%{value.id}" for value in instruction.args)
                detail = ""
                if instruction.local is not None:
                    detail = f" ${instruction.local}" + (f", {operands}" if operands else "")
                elif instruction.immediate is not None:
                    detail = f" {instruction.immediate!r}"
                    if operands:
                        detail += f", {operands}"
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
