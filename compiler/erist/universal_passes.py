from __future__ import annotations

from dataclasses import replace
import math

from .universal_ir import (
    BOOL,
    F64,
    I64,
    UBranch,
    UInstruction,
    UJump,
    UProgram,
    UReturn,
    UValue,
)

INT64_MIN = -(1 << 63)
INT64_MAX = (1 << 63) - 1


class UniversalIRVerificationError(ValueError):
    """Raised when target-neutral IR violates its structural/type contract."""


def _fits_i64(value: int) -> bool:
    return INT64_MIN <= value <= INT64_MAX


def verify_program(program: UProgram) -> UProgram:
    fn_names = [fn.name for fn in program.functions]
    if len(fn_names) != len(set(fn_names)):
        raise UniversalIRVerificationError("duplicate Universal-IR function symbol")
    if program.entry not in set(fn_names):
        raise UniversalIRVerificationError("Universal-IR entry function is missing")

    type_names = [item.name for item in program.types]
    if len(type_names) != len(set(type_names)):
        raise UniversalIRVerificationError("duplicate Universal-IR type definition")

    fn_map = {fn.name: fn for fn in program.functions}
    for fn in program.functions:
        block_names = [block.name for block in fn.blocks]
        if not block_names:
            raise UniversalIRVerificationError(f"function {fn.name!r} has no blocks")
        if len(block_names) != len(set(block_names)):
            raise UniversalIRVerificationError(f"function {fn.name!r} has duplicate block names")
        blocks = set(block_names)
        local_ids = {local.id for local in fn.locals}
        if local_ids != set(range(len(fn.locals))):
            raise UniversalIRVerificationError(f"function {fn.name!r} local ids are not dense")
        if any(param.id not in local_ids for param in fn.parameters):
            raise UniversalIRVerificationError(f"function {fn.name!r} parameter is not a local")

        produced: dict[int, str] = {}
        for block in fn.blocks:
            if block.terminator is None:
                raise UniversalIRVerificationError(
                    f"function {fn.name!r} block {block.name!r} has no terminator"
                )
            for ins in block.instructions:
                for arg in ins.args:
                    if arg.id < 0 or arg.id >= fn.value_count:
                        raise UniversalIRVerificationError(
                            f"function {fn.name!r} uses invalid value %{arg.id}"
                        )
                if ins.local is not None and ins.local not in local_ids:
                    raise UniversalIRVerificationError(
                        f"function {fn.name!r} uses invalid local {ins.local}"
                    )
                if ins.result is not None:
                    if ins.result.id in produced:
                        raise UniversalIRVerificationError(
                            f"function {fn.name!r} produces value %{ins.result.id} more than once"
                        )
                    if ins.result.id < 0 or ins.result.id >= fn.value_count:
                        raise UniversalIRVerificationError(
                            f"function {fn.name!r} produces invalid value %{ins.result.id}"
                        )
                    produced[ins.result.id] = ins.result.type_name
                if ins.op == "call":
                    target = str(ins.immediate)
                    callee = fn_map.get(target)
                    if callee is None:
                        raise UniversalIRVerificationError(
                            f"function {fn.name!r} calls missing function {target!r}"
                        )
                    if len(ins.args) != len(callee.parameters):
                        raise UniversalIRVerificationError(
                            f"call to {target!r} has wrong argument count"
                        )
                    for arg, param in zip(ins.args, callee.parameters):
                        if arg.type_name != param.type_name:
                            raise UniversalIRVerificationError(
                                f"call to {target!r} has argument type mismatch"
                            )
                    if callee.return_type == "void":
                        if ins.result is not None:
                            raise UniversalIRVerificationError(
                                f"no-value call to {target!r} unexpectedly produces a value"
                            )
                    elif ins.result is None or ins.result.type_name != callee.return_type:
                        raise UniversalIRVerificationError(
                            f"call to {target!r} has result type mismatch"
                        )

            term = block.terminator
            if isinstance(term, UJump):
                if term.target not in blocks:
                    raise UniversalIRVerificationError(
                        f"function {fn.name!r} jumps to missing block {term.target!r}"
                    )
            elif isinstance(term, UBranch):
                if term.condition.type_name != BOOL:
                    raise UniversalIRVerificationError(
                        f"function {fn.name!r} branch condition is not Bool"
                    )
                if term.true_target not in blocks or term.false_target not in blocks:
                    raise UniversalIRVerificationError(
                        f"function {fn.name!r} branches to a missing block"
                    )
            elif isinstance(term, UReturn):
                if fn.return_type == "void":
                    if term.value is not None:
                        raise UniversalIRVerificationError(
                            f"no-value function {fn.name!r} returns a value"
                        )
                elif term.value is None or term.value.type_name != fn.return_type:
                    raise UniversalIRVerificationError(
                        f"function {fn.name!r} return type mismatch"
                    )
            else:
                raise UniversalIRVerificationError(
                    f"function {fn.name!r} has unknown terminator"
                )
    return program


def eliminate_unreachable_blocks(program: UProgram) -> bool:
    changed = False
    for fn in program.functions:
        by_name = {block.name: block for block in fn.blocks}
        reachable: set[str] = set()
        work = [fn.blocks[0].name] if fn.blocks else []
        while work:
            name = work.pop()
            if name in reachable:
                continue
            reachable.add(name)
            term = by_name[name].terminator
            if isinstance(term, UJump):
                work.append(term.target)
            elif isinstance(term, UBranch):
                work.extend((term.true_target, term.false_target))
        if len(reachable) != len(fn.blocks):
            fn.blocks[:] = [block for block in fn.blocks if block.name in reachable]
            changed = True
    return changed


def _int_div(a: int, b: int) -> int:
    # Eristavi integer division truncates toward zero without using Float.
    q = abs(a) // abs(b)
    return -q if (a < 0) ^ (b < 0) else q


def fold_constants(program: UProgram) -> bool:
    changed = False
    for fn in program.functions:
        constants: dict[int, tuple[str, object]] = {}
        for block in fn.blocks:
            out: list[UInstruction] = []
            for ins in block.instructions:
                replacement = ins
                if ins.result is not None:
                    value = None
                    if ins.op == "const_i64":
                        value = (I64, int(ins.immediate))
                    elif ins.op == "const_bool":
                        value = (BOOL, bool(ins.immediate))
                    elif ins.op == "const_f64":
                        value = (F64, float(ins.immediate))
                    elif ins.op == "bool_not" and ins.args and ins.args[0].id in constants:
                        t, a = constants[ins.args[0].id]
                        if t == BOOL:
                            value = (BOOL, not bool(a))
                    elif len(ins.args) == 2 and all(arg.id in constants for arg in ins.args):
                        left = constants[ins.args[0].id]
                        right = constants[ins.args[1].id]
                        if left[0] == right[0] == I64:
                            a, b = int(left[1]), int(right[1])
                            try:
                                if ins.op == "add_checked": r = a + b
                                elif ins.op == "sub_checked": r = a - b
                                elif ins.op == "mul_checked": r = a * b
                                elif ins.op == "div_checked" and b != 0 and not (a == INT64_MIN and b == -1): r = _int_div(a, b)
                                elif ins.op == "rem_checked" and b != 0 and not (a == INT64_MIN and b == -1): r = a - _int_div(a, b) * b
                                elif ins.op == "cmp_eq": value = (BOOL, a == b); r = None
                                elif ins.op == "cmp_ne": value = (BOOL, a != b); r = None
                                elif ins.op == "cmp_lt": value = (BOOL, a < b); r = None
                                elif ins.op == "cmp_le": value = (BOOL, a <= b); r = None
                                elif ins.op == "cmp_gt": value = (BOOL, a > b); r = None
                                elif ins.op == "cmp_ge": value = (BOOL, a >= b); r = None
                                else: r = None
                                if r is not None and _fits_i64(r):
                                    value = (I64, r)
                            except (ArithmeticError, OverflowError):
                                pass
                        elif left[0] == right[0] == F64:
                            a, b = float(left[1]), float(right[1])
                            if ins.op == "f64_add": value = (F64, a + b)
                            elif ins.op == "f64_sub": value = (F64, a - b)
                            elif ins.op == "f64_mul": value = (F64, a * b)
                            elif ins.op == "f64_div" and b != 0.0: value = (F64, a / b)
                            elif ins.op == "f64_cmp_eq": value = (BOOL, a == b)
                            elif ins.op == "f64_cmp_ne": value = (BOOL, a != b)
                            elif ins.op == "f64_cmp_lt": value = (BOOL, a < b)
                            elif ins.op == "f64_cmp_le": value = (BOOL, a <= b)
                            elif ins.op == "f64_cmp_gt": value = (BOOL, a > b)
                            elif ins.op == "f64_cmp_ge": value = (BOOL, a >= b)
                    if value is not None:
                        t, literal = value
                        op = {I64: "const_i64", BOOL: "const_bool", F64: "const_f64"}[t]
                        replacement = UInstruction(op, ins.result, (), None, literal)
                        constants[ins.result.id] = (t, literal)
                        if replacement != ins:
                            changed = True
                    else:
                        constants.pop(ins.result.id, None)
                out.append(replacement)
            block.instructions[:] = out
    return changed


def optimize_program(program: UProgram) -> UProgram:
    """Run semantics-preserving bootstrap optimizations and verify the result."""
    verify_program(program)
    fold_constants(program)
    eliminate_unreachable_blocks(program)
    verify_program(program)
    return program
