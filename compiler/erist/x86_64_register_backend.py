from __future__ import annotations

from dataclasses import dataclass

from .universal_analysis import cfg_liveness, interference_graph, register_candidates
from .universal_ir import BOOL, F64, I64, UFunction, UInstruction, UValue
from .x86_64_backend import X86_64LinuxBackend


@dataclass(frozen=True)
class X86RegisterPlan:
    """Physical-register assignment for one Universal-IR function."""

    registers: dict[int, str]


# These operations are guaranteed by the current composed x86 backend not to
# call a helper/PLT routine after consuming their inputs. Any other instruction
# is treated conservatively as a caller-saved-register clobber boundary.
_REGISTER_SAFE_OPS = frozenset({
    "const_i64",
    "const_bool",
    "const_f64",
    "load_local",
    "neg_checked",
    "add_checked",
    "sub_checked",
    "mul_checked",
    "div_checked",
    "rem_checked",
    "bool_not",
    "cmp_eq",
    "cmp_ne",
    "cmp_lt",
    "cmp_le",
    "cmp_gt",
    "cmp_ge",
    "f64_neg",
    "f64_add",
    "f64_sub",
    "f64_mul",
    "f64_div",
    "f64_cmp_eq",
    "f64_cmp_ne",
    "f64_cmp_lt",
    "f64_cmp_le",
    "f64_cmp_gt",
    "f64_cmp_ge",
})


def _caller_saved_survivors(fn: UFunction) -> frozenset[int]:
    """Return values that may not live solely in caller-saved registers."""

    liveness = cfg_liveness(fn)
    blocked: set[int] = set()
    for block in fn.blocks:
        for index, ins in enumerate(block.instructions):
            if ins.op in _REGISTER_SAFE_OPS:
                continue
            live_after = set(liveness.live_after_instruction[(block.name, index)])
            if ins.result is not None:
                live_after.discard(ins.result.id)
            blocked.update(live_after)
    return frozenset(blocked)


def allocate_x86_registers(
    fn: UFunction,
    gp_registers: tuple[str, ...] = ("%r10",),
    xmm_registers: tuple[str, ...] = ("%xmm8",),
) -> X86RegisterPlan:
    """Greedily color short-lived scalar values onto physical registers.

    This is deliberately a conservative first allocator:

    - only the existing short-lived scalar register candidates participate;
    - values that survive any possible helper/PLT/GC clobber remain spilled;
    - Int/Bool and Float use independent register classes;
    - the existing CFG interference graph prevents overlapping values from
      sharing the same physical register.

    Stack slots remain allocated as a fallback representation in this phase.
    Removing unused spill slots is a later frame-compaction step.
    """

    graph = interference_graph(fn)
    candidates = set(register_candidates(fn))
    blocked = _caller_saved_survivors(fn)

    value_types: dict[int, str] = {}
    for block in fn.blocks:
        for ins in block.instructions:
            if ins.result is not None:
                value_types[ins.result.id] = ins.result.type_name

    eligible = [
        value_id
        for value_id in candidates
        if value_id not in blocked and value_types.get(value_id) in {I64, BOOL, F64}
    ]
    eligible.sort(key=lambda value_id: (-len(graph.get(value_id, ())), value_id))

    assigned: dict[int, str] = {}
    for value_id in eligible:
        register_pool = xmm_registers if value_types[value_id] == F64 else gp_registers
        forbidden = {
            assigned[neighbor]
            for neighbor in graph.get(value_id, ())
            if neighbor in assigned
        }
        register = next((item for item in register_pool if item not in forbidden), None)
        if register is not None:
            assigned[value_id] = register

    return X86RegisterPlan(dict(sorted(assigned.items())))


class X86_64RegisterLinuxBackend(X86_64LinuxBackend):
    """x86-64 backend layer with conservative physical register allocation.

    Register-resident scalar Universal-IR values bypass their spill-slot loads
    and stores. The allocator currently uses caller-saved registers only for
    values proven not to survive a possible call/GC clobber boundary. This
    keeps the existing System-V ABI, precise-GC root model and composed runtime
    helpers unchanged while establishing a real physical-register path.
    """

    def __init__(self):
        super().__init__()
        self._register_plan_fn: UFunction | None = None
        self._register_plan = X86RegisterPlan({})

    def _ensure_register_plan(self) -> None:
        if self.fn is None:
            return
        if self._register_plan_fn is self.fn:
            return
        self._register_plan = allocate_x86_registers(self.fn)
        self._register_plan_fn = self.fn

    def _assigned_register(self, value: UValue) -> str | None:
        self._ensure_register_plan()
        return self._register_plan.registers.get(value.id)

    def _load(self, value: UValue, register: str = "%rax") -> None:
        assigned = self._assigned_register(value)
        if assigned is None:
            super()._load(value, register)
            return
        if assigned != register:
            self.lines.append(f"    movq {assigned}, {register}")

    def _load_f64(self, value: UValue, register: str = "%xmm0") -> None:
        assigned = self._assigned_register(value)
        if assigned is None:
            super()._load_f64(value, register)
            return
        if assigned != register:
            self.lines.append(f"    movsd {assigned}, {register}")

    def _store_result(self, instruction: UInstruction, register: str = "%rax") -> None:
        if instruction.result is None:
            raise ValueError(f"x86-64 instruction {instruction.op} unexpectedly has no result")
        assigned = self._assigned_register(instruction.result)
        if assigned is None:
            super()._store_result(instruction, register)
            return
        if assigned != register:
            self.lines.append(f"    movq {register}, {assigned}")

    def _store_result_f64(self, instruction: UInstruction, register: str = "%xmm0") -> None:
        if instruction.result is None:
            raise ValueError(f"x86-64 instruction {instruction.op} unexpectedly has no result")
        assigned = self._assigned_register(instruction.result)
        if assigned is None:
            super()._store_result_f64(instruction, register)
            return
        if assigned != register:
            self.lines.append(f"    movsd {register}, {assigned}")
