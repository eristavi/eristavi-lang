from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .ir import (
    IRAssign,
    IRBinary,
    IRCall,
    IRConst,
    IRConstruct,
    IRCount,
    IRExpr,
    IRExprStmt,
    IRFor,
    IRFunction,
    IRIdentity,
    IRIf,
    IRIndex,
    IRIndexAssign,
    IRLet,
    IRList,
    IRListAdd,
    IRMaybeGet,
    IRMaybeNone,
    IRMaybeSome,
    IRMember,
    IRMemberAssign,
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
class UField:
    name: str
    type_name: str
    fixed: bool = False


@dataclass(frozen=True)
class UType:
    name: str
    fields: tuple[UField, ...]
    is_error: bool = False


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
    fails: tuple[str, ...] = ()


@dataclass
class UProgram:
    functions: list[UFunction]
    entry: str = "__entry"
    types: list[UType] = field(default_factory=list)

    def function(self, name: str) -> UFunction:
        for fn in self.functions:
            if fn.name == name:
                return fn
        raise KeyError(name)

    def type(self, name: str) -> UType:
        for item in self.types:
            if item.name == name:
                return item
        raise KeyError(name)


def maybe_inner(type_name: str) -> str:
    if not type_name.startswith("maybe<") or not type_name.endswith(">"):
        raise ValueError(f"not a Universal-IR maybe type: {type_name}")
    return type_name[6:-1]


def identity_inner(type_name: str) -> str:
    if not type_name.startswith("identity<") or not type_name.endswith(">"):
        raise ValueError(f"not a Universal-IR identity type: {type_name}")
    return type_name[9:-1]


def list_inner(type_name: str) -> str:
    if not type_name.startswith("list<") or not type_name.endswith(">"):
        raise ValueError(f"not a Universal-IR list type: {type_name}")
    return type_name[5:-1]


def nominal_name(type_name: str) -> str:
    if not type_name.startswith("nominal<") or not type_name.endswith(">"):
        raise ValueError(f"not a Universal-IR nominal type: {type_name}")
    return type_name[8:-1]


def is_value_composite(type_name: str) -> bool:
    """Whether ordinary assignment/parameter transfer requires logical copying."""
    return (
        type_name.startswith("list<")
        or type_name.startswith("maybe<")
        or type_name.startswith("nominal<")
    )


class UniversalLowerer:
    """Lower source-close typed IR into target-neutral basic-block IR.

    The IR uses a uniform machine-word handle for heap-backed runtime values but
    keeps their semantic type explicit.  Ordinary composite values are cloned at
    Eristavi value-transfer boundaries; identity handles are deliberately not.
    This makes value/identity semantics part of target-neutral lowering rather
    than an accidental property of a CPU backend.
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
        self.current_fails: tuple[str, ...] = ()
        self.known_functions: dict[str, tuple[list[str], str, tuple[str, ...]]] = {}
        self.types: list[UType] = []
        self.type_by_name: dict[str, UType] = {}

    def lower(self, program: IRProgram) -> UProgram:
        from .collection_codegen import require_collection_codegen
        require_collection_codegen(program, "Universal IR")
        self.types = [
            UType(
                item.name,
                tuple(UField(field.name, self._map_type(field.type_name), field.fixed) for field in item.fields),
                item.is_error,
            )
            for item in program.structs
        ]
        self.type_by_name = {item.name: item for item in self.types}
        self.known_functions = {}
        for fn in program.functions:
            params = [self._map_type(p.type_name) for p in fn.parameters]
            result = VOID if fn.return_type is None else self._map_type(fn.return_type)
            self.known_functions[fn.name] = (params, result, tuple(fn.fails))

        functions = [self._lower_function(fn) for fn in program.functions]
        functions.append(self._lower_entry(program.entry))
        return UProgram(functions, "__entry", list(self.types))

    def _reset_function(self, return_type: str, fails: tuple[str, ...] = ()) -> None:
        self.blocks = []
        self.locals = []
        self.parameters = []
        self.scopes = [{}]
        self.next_value = 0
        self.next_block = 0
        self.current_return = return_type
        self.current_fails = fails
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
        self._reset_function(result, tuple(fn.fails))
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
            tuple(fn.fails),
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
        if source_type.startswith("maybe "):
            return f"maybe<{self._map_type(source_type[6:])}>"
        if source_type.startswith("identity "):
            return f"identity<{self._map_type(source_type[9:])}>"
        if source_type.startswith("List of "):
            return f"list<{self._map_type(source_type[8:])}>"
        if source_type.startswith("std.files.File"):
            return f"resource<{source_type}>"
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

    def _load_local_value(self, local: ULocal) -> UValue:
        value = self._emit("load_local", local.type_name, local=local.id)
        assert value is not None
        return value

    def _clone(self, value: UValue) -> UValue:
        if not is_value_composite(value.type_name):
            return value
        cloned = self._emit("clone_value", value.type_name, (value,), immediate=value.type_name)
        assert cloned is not None
        return cloned

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
            value = self._clone(value)
            local = self._declare(stmt.name, t)
            self._emit("store_local", args=(value,), local=local.id)
            return

        if isinstance(stmt, IRAssign):
            local = self._lookup(stmt.name)
            value = self._expr(stmt.value)
            if value is None or value.type_name != local.type_name:
                raise ValueError("universal IR assignment type mismatch")
            self._emit("store_local", args=(self._clone(value),), local=local.id)
            return

        if isinstance(stmt, IRIndexAssign):
            local = self._lookup(stmt.name)
            if not local.type_name.startswith("list<"):
                raise ValueError("indexed Universal-IR assignment requires List")
            base = self._load_local_value(local)
            index = self._expr(stmt.index)
            value = self._expr(stmt.value)
            if index is None or index.type_name != I64 or value is None:
                raise ValueError("malformed Universal-IR List assignment")
            element_type = list_inner(local.type_name)
            if value.type_name != element_type:
                raise ValueError("Universal-IR List assignment type mismatch")
            self._emit("list_set", args=(base, index, self._clone(value)), immediate=element_type)
            return

        if isinstance(stmt, IRMemberAssign):
            base, field_type, index = self._member_target(stmt.target)
            value = self._expr(stmt.value)
            if value is None or value.type_name != field_type:
                raise ValueError("Universal-IR member assignment type mismatch")
            self._emit(
                "set_field",
                args=(base, self._clone(value)),
                immediate={"index": index, "field": stmt.target.name},
            )
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
            value = self._clone(value)
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

        if isinstance(stmt, IRFor):
            self._lower_for(stmt)
            return

        raise ValueError(f"universal IR does not yet lower statement {type(stmt).__name__}")

    def _lower_for(self, stmt: IRFor) -> None:
        iterable = self._expr(stmt.iterable)
        if iterable is None or not iterable.type_name.startswith("list<"):
            raise ValueError("Universal-IR for currently requires List")
        snapshot = self._clone(iterable)
        snapshot_local = self._declare(f"#for_snapshot_{len(self.locals)}", iterable.type_name)
        self._emit("store_local", args=(snapshot,), local=snapshot_local.id)
        zero = self._emit("const_i64", I64, immediate=0)
        assert zero is not None
        index_local = self._declare(f"#for_index_{len(self.locals)}", I64)
        self._emit("store_local", args=(zero,), local=index_local.id)

        source = self.current
        cond_block = self._new_block("for.cond")
        body_block = self._new_block("for.body")
        end_block = self._new_block("for.end")
        assert source is not None
        source.terminator = UJump(cond_block.name)

        self.current = cond_block
        index = self._load_local_value(index_local)
        current_snapshot = self._load_local_value(snapshot_local)
        count = self._emit("list_count", I64, (current_snapshot,))
        assert count is not None
        condition = self._emit("cmp_lt", BOOL, (index, count))
        assert condition is not None
        self.current.terminator = UBranch(condition, body_block.name, end_block.name)

        self.current = body_block
        self.scopes.append({})
        try:
            index = self._load_local_value(index_local)
            current_snapshot = self._load_local_value(snapshot_local)
            element_type = list_inner(iterable.type_name)
            element = self._emit("list_get", element_type, (current_snapshot, index), immediate=element_type)
            assert element is not None
            loop_local = self._declare(stmt.name, element_type)
            self._emit("store_local", args=(self._clone(element),), local=loop_local.id)
            self._lower_statements(stmt.body, new_scope=False)
        finally:
            self.scopes.pop()

        if self.current.terminator is None:
            one = self._emit("const_i64", I64, immediate=1)
            index = self._load_local_value(index_local)
            assert one is not None
            next_index = self._emit("add_checked", I64, (index, one))
            assert next_index is not None
            self._emit("store_local", args=(next_index,), local=index_local.id)
            self.current.terminator = UJump(cond_block.name)

        self.current = end_block

    def _short_circuit(self, expr: IRBinary) -> UValue:
        left = self._expr(expr.left)
        if left is None or left.type_name != BOOL:
            raise ValueError("short-circuit Boolean operator requires Bool")
        temp = self._declare(f"#bool_{len(self.locals)}", BOOL)
        source = self.current
        rhs_block = self._new_block("bool.rhs")
        short_block = self._new_block("bool.short")
        end_block = self._new_block("bool.end")
        assert source is not None
        if expr.operator == "and":
            source.terminator = UBranch(left, rhs_block.name, short_block.name)
            short_value = False
        else:
            source.terminator = UBranch(left, short_block.name, rhs_block.name)
            short_value = True

        self.current = short_block
        constant = self._emit("const_bool", BOOL, immediate=short_value)
        assert constant is not None
        self._emit("store_local", args=(constant,), local=temp.id)
        self.current.terminator = UJump(end_block.name)

        self.current = rhs_block
        right = self._expr(expr.right)
        if right is None or right.type_name != BOOL:
            raise ValueError("short-circuit Boolean operator requires Bool")
        self._emit("store_local", args=(right,), local=temp.id)
        if self.current.terminator is None:
            self.current.terminator = UJump(end_block.name)

        self.current = end_block
        return self._load_local_value(temp)

    def _member_target(self, target: IRMember) -> tuple[UValue, str, int]:
        base = self._expr(target.base)
        if base is None:
            raise ValueError("member assignment base has no value")
        if base.type_name.startswith("identity<"):
            inner = identity_inner(base.type_name)
            unwrapped = self._emit("identity_get", inner, (base,))
            assert unwrapped is not None
            base = unwrapped
        if not base.type_name.startswith("nominal<"):
            raise ValueError(f"member access requires nominal value, got {base.type_name}")
        name = nominal_name(base.type_name)
        info = self.type_by_name.get(name)
        if info is None:
            raise ValueError(f"Universal IR has no layout for {name!r}")
        for index, field in enumerate(info.fields):
            if field.name == target.name:
                return base, field.type_name, index
        raise ValueError(f"Universal IR type {name!r} has no field {target.name!r}")

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
            return self._load_local_value(self._lookup(expr.name))

        if isinstance(expr, IRList):
            target_type = self._map_type(expr.type_name)
            if not target_type.startswith("list<"):
                raise ValueError("IRList did not carry a List type")
            values: list[UValue] = []
            element_type = list_inner(target_type)
            for item in expr.elements:
                value = self._expr(item)
                if value is None or value.type_name != element_type:
                    raise ValueError("Universal-IR List literal element mismatch")
                values.append(self._clone(value))
            result = self._emit("make_list", target_type, values, immediate=element_type)
            assert result is not None
            return result

        if isinstance(expr, IRIndex):
            base = self._expr(expr.base)
            index = self._expr(expr.index)
            if base is None or index is None or index.type_name != I64:
                raise ValueError("malformed Universal-IR index expression")
            if base.type_name.startswith("list<"):
                element_type = list_inner(base.type_name)
                result = self._emit("list_get", element_type, (base, index), immediate=element_type)
                assert result is not None
                return result
            raise ValueError(f"Universal IR indexing does not yet support {base.type_name}")

        if isinstance(expr, IRCount):
            base = self._expr(expr.base)
            if base is None:
                raise ValueError("count base has no value")
            if base.type_name.startswith("list<"):
                result = self._emit("list_count", I64, (base,))
                assert result is not None
                return result
            raise ValueError(f"Universal IR count does not yet support {base.type_name}")

        if isinstance(expr, IRListAdd):
            local = self._lookup(expr.base_name)
            if not local.type_name.startswith("list<"):
                raise ValueError("List.add base is not a List")
            base = self._load_local_value(local)
            value = self._expr(expr.value)
            element_type = list_inner(local.type_name)
            if value is None or value.type_name != element_type:
                raise ValueError("List.add value type mismatch")
            self._emit("list_add", args=(base, self._clone(value)), immediate=element_type)
            return None

        if isinstance(expr, IRConstruct):
            target_type = self._map_type(expr.type_name)
            if not target_type.startswith("nominal<"):
                raise ValueError("construction requires nominal Universal-IR type")
            info = self.type_by_name.get(nominal_name(target_type))
            if info is None:
                raise ValueError(f"missing Universal-IR layout for {expr.type_name!r}")
            provided = {field.name: field.value for field in expr.fields}
            values: list[UValue] = []
            for field in info.fields:
                if field.name not in provided:
                    raise ValueError(f"construction is missing field {field.name!r}")
                value = self._expr(provided[field.name])
                if value is None or value.type_name != field.type_name:
                    raise ValueError(f"construction field {field.name!r} type mismatch")
                values.append(self._clone(value))
            result = self._emit("make_struct", target_type, values, immediate=info.name)
            assert result is not None
            return result

        if isinstance(expr, IRMember):
            base, field_type, index = self._member_target(expr)
            result = self._emit(
                "get_field",
                field_type,
                (base,),
                immediate={"index": index, "field": expr.name},
            )
            assert result is not None
            return result

        if isinstance(expr, IRIdentity):
            value = self._expr(expr.value)
            if value is None:
                raise ValueError("identity requires a value")
            target_type = self._map_type(expr.type_name)
            if not target_type.startswith("identity<"):
                raise ValueError("identity expression has invalid type")
            result = self._emit("make_identity", target_type, (self._clone(value),), immediate=value.type_name)
            assert result is not None
            return result

        if isinstance(expr, IRMaybeNone):
            target_type = self._map_type(expr.type_name)
            result = self._emit("maybe_none", target_type, immediate=maybe_inner(target_type))
            assert result is not None
            return result

        if isinstance(expr, IRMaybeSome):
            target_type = self._map_type(expr.type_name)
            value = self._expr(expr.value)
            inner = maybe_inner(target_type)
            if value is None or value.type_name != inner:
                raise ValueError("maybe present value type mismatch")
            result = self._emit("maybe_some", target_type, (self._clone(value),), immediate=inner)
            assert result is not None
            return result

        if isinstance(expr, IRMaybeGet):
            base = self._expr(expr.value)
            if base is None or not base.type_name.startswith("maybe<"):
                raise ValueError("maybe_get requires maybe value")
            inner = maybe_inner(base.type_name)
            result = self._emit("maybe_get", inner, (base,), immediate=inner)
            assert result is not None
            return result

        if isinstance(expr, IRUnary):
            value = self._expr(expr.operand)
            if value is None:
                raise ValueError("unary operator requires a value")
            if expr.operator == "not" and value.type_name == BOOL:
                result = self._emit("bool_not", BOOL, (value,))
                assert result is not None
                return result
            if expr.operator == "-" and value.type_name == I64:
                result = self._emit("neg_checked", I64, (value,))
                assert result is not None
                return result
            if expr.operator == "-" and value.type_name == F64:
                result = self._emit("f64_neg", F64, (value,))
                assert result is not None
                return result
            raise ValueError(f"universal IR does not support unary {expr.operator!r} for {expr.type_name}")

        if isinstance(expr, IRBinary):
            if expr.operator in ("and", "or"):
                return self._short_circuit(expr)
            left = self._expr(expr.left)
            right = self._expr(expr.right)
            if left is None or right is None:
                raise ValueError("binary operator requires values")
            int_arithmetic = {
                "+": "add_checked", "-": "sub_checked", "*": "mul_checked",
                "/": "div_checked", "%": "rem_checked",
            }
            float_arithmetic = {"+": "f64_add", "-": "f64_sub", "*": "f64_mul", "/": "f64_div"}
            comparisons = {"==": "cmp_eq", "!=": "cmp_ne", "<": "cmp_lt", "<=": "cmp_le", ">": "cmp_gt", ">=": "cmp_ge"}
            if expr.operator in int_arithmetic and left.type_name == I64 and right.type_name == I64:
                result = self._emit(int_arithmetic[expr.operator], I64, (left, right)); assert result is not None; return result
            if expr.operator in float_arithmetic and left.type_name == F64 and right.type_name == F64:
                result = self._emit(float_arithmetic[expr.operator], F64, (left, right)); assert result is not None; return result
            if expr.operator == "+" and left.type_name == TEXT and right.type_name == TEXT:
                result = self._emit("text_concat", TEXT, (left, right)); assert result is not None; return result
            if expr.operator in comparisons and left.type_name == right.type_name:
                if left.type_name in (I64, BOOL):
                    result = self._emit(comparisons[expr.operator], BOOL, (left, right)); assert result is not None; return result
                if left.type_name == F64:
                    result = self._emit("f64_" + comparisons[expr.operator], BOOL, (left, right)); assert result is not None; return result
                if left.type_name == TEXT and expr.operator in ("==", "!="):
                    result = self._emit("text_eq" if expr.operator == "==" else "text_ne", BOOL, (left, right)); assert result is not None; return result
                if left.type_name.startswith("identity<") and expr.operator in ("==", "!="):
                    result = self._emit("identity_eq" if expr.operator == "==" else "identity_ne", BOOL, (left, right)); assert result is not None; return result
                if is_value_composite(left.type_name) and expr.operator in ("==", "!="):
                    result = self._emit("value_eq" if expr.operator == "==" else "value_ne", BOOL, (left, right), immediate=left.type_name); assert result is not None; return result
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
            parameter_types, result_type, fails = signature
            if fails:
                raise ValueError(
                    f"checked-error function {expr.name!r} requires the Universal-IR failure-edge lowering phase"
                )
            args = [self._expr(arg) for arg in expr.arguments]
            if any(arg is None for arg in args):
                raise ValueError("function arguments must produce values")
            concrete = [arg for arg in args if arg is not None]
            if [arg.type_name for arg in concrete] != parameter_types:
                raise ValueError(f"universal IR call contract mismatch for {expr.name!r}")
            transferred = [self._clone(arg) for arg in concrete]
            return self._emit("call", None if result_type == VOID else result_type, transferred, immediate=expr.name)

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
    for item in program.types:
        suffix = " error" if item.is_error else ""
        lines.append(f"type @{item.name}{suffix} {{")
        for index, field in enumerate(item.fields):
            fixed = " fixed" if field.fixed else ""
            lines.append(f"  field {index} {field.name}: {field.type_name}{fixed}")
        lines.append("}")
    for fn in program.functions:
        params = ", ".join(f"${p.id} {p.name}: {p.type_name}" for p in fn.parameters)
        fails = " fails " + ", ".join(fn.fails) if fn.fails else ""
        lines.append(f"function @{fn.name}({params}) -> {fn.return_type}{fails} {{")
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
