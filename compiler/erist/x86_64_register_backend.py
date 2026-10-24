from __future__ import annotations

from dataclasses import dataclass

from .universal_analysis import cfg_liveness, interference_graph, register_candidates
from .universal_ir import BOOL, F64, I64, UFunction, UInstruction, UValue
from .x86_64_backend import X86_64LinuxBackend
from .x86_64_lowering_contracts import x86_lowering_contract


# Keep the first production pool intentionally small and separate from the
# scratch/ABI registers used by current lowering code. Per-lowering clobber
# contracts decide whether a value may cross a particular instruction.
ALLOCATABLE_GP_REGISTERS = ("%r10", "%r11")
ALLOCATABLE_XMM_REGISTERS = ("%xmm8", "%xmm9")


@dataclass(frozen=True)
class X86RegisterPlan:
    """Physical-register assignment for one Universal-IR function."""

    registers: dict[int, str]


def _value_types(fn: UFunction) -> dict[int, str]:
    result: dict[int, str] = {}
    for block in fn.blocks:
        for ins in block.instructions:
            if ins.result is not None:
                result[ins.result.id] = ins.result.type_name
    return result


def _forbidden_registers(fn: UFunction, value_types: dict[int, str]) -> dict[int, frozenset[str]]:
    """Return physical registers each virtual value may not occupy.

    A value that is live beyond an instruction must avoid every physical
    register clobbered by that lowering. If a lowering can clobber registers
    before consuming its source operands, those operands receive the same
    restriction even when they die at the instruction.

    Results are intentionally excluded from the instruction's own clobbers:
    an operation whose contract marks a scalar result register-safe produces
    that result after its final clobber.
    """

    liveness = cfg_liveness(fn)
    forbidden: dict[int, set[str]] = {value_id: set() for value_id in value_types}

    def add_clobbers(value_id: int, gp: frozenset[str], xmm: frozenset[str]) -> None:
        type_name = value_types.get(value_id)
        if type_name == F64:
            forbidden.setdefault(value_id, set()).update(xmm)
        elif type_name in {I64, BOOL}:
            forbidden.setdefault(value_id, set()).update(gp)

    for block in fn.blocks:
        for index, ins in enumerate(block.instructions):
            contract = x86_lowering_contract(ins.op)
            live_after = set(liveness.live_after_instruction[(block.name, index)])
            if ins.result is not None:
                live_after.discard(ins.result.id)

            for value_id in live_after:
                add_clobbers(value_id, contract.gp_clobbers, contract.xmm_clobbers)

            if not contract.operands_before_clobber:
                for arg in ins.args:
                    add_clobbers(arg.id, contract.gp_clobbers, contract.xmm_clobbers)

    return {
        value_id: frozenset(registers)
        for value_id, registers in forbidden.items()
    }


def _validate_register_pool(registers: tuple[str, ...], allowed: tuple[str, ...], register_class: str) -> None:
    invalid = [register for register in registers if register not in allowed]
    if invalid:
        raise ValueError(
            f"x86 allocator {register_class} pool contains unaudited register(s): "
            + ", ".join(invalid)
        )


def allocate_x86_registers(
    fn: UFunction,
    gp_registers: tuple[str, ...] = ALLOCATABLE_GP_REGISTERS,
    xmm_registers: tuple[str, ...] = ALLOCATABLE_XMM_REGISTERS,
) -> X86RegisterPlan:
    """Color short-lived scalar values onto audited physical registers.

    Allocation combines three independent correctness constraints:

    1. Universal-IR CFG interference prevents simultaneously live virtual
       values from sharing a physical register.
    2. x86 lowering contracts forbid registers clobbered while a value is live
       and protect operands of lowerings that clobber before consuming them.
    3. only scalar results whose defining lowering explicitly permits register
       residency are eligible.

    Stack slots remain allocated as a fallback representation in this phase.
    Dead spill-slot/frame compaction is intentionally deferred until the
    machine-lowering contracts and broader register pool are fully established.
    """

    _validate_register_pool(gp_registers, ALLOCATABLE_GP_REGISTERS, "GP")
    _validate_register_pool(xmm_registers, ALLOCATABLE_XMM_REGISTERS, "XMM")

    graph = interference_graph(fn)
    candidates = set(register_candidates(fn))
    value_types = _value_types(fn)
    forbidden_by_value = _forbidden_registers(fn, value_types)

    defining_ops: dict[int, str] = {}
    for block in fn.blocks:
        for ins in block.instructions:
            if ins.result is not None:
                defining_ops[ins.result.id] = ins.op

    eligible = [
        value_id
        for value_id in candidates
        if value_types.get(value_id) in {I64, BOOL, F64}
        and x86_lowering_contract(defining_ops.get(value_id, "")).scalar_result_register_safe
    ]
    eligible.sort(key=lambda value_id: (-len(graph.get(value_id, ())), value_id))

    assigned: dict[int, str] = {}
    for value_id in eligible:
        register_pool = xmm_registers if value_types[value_id] == F64 else gp_registers
        forbidden = set(forbidden_by_value.get(value_id, ()))
        forbidden.update(
            assigned[neighbor]
            for neighbor in graph.get(value_id, ())
            if neighbor in assigned
        )
        register = next((item for item in register_pool if item not in forbidden), None)
        if register is not None:
            assigned[value_id] = register

    return X86RegisterPlan(dict(sorted(assigned.items())))


class X86_64RegisterLinuxBackend(X86_64LinuxBackend):
    """x86-64 backend layer with conservative physical register allocation.

    Register-resident scalar Universal-IR values bypass their spill-slot loads
    and stores. The allocator uses CFG interference plus explicit machine
    lowering clobber contracts, while the existing stack slots remain a safe
    fallback. This preserves the System-V ABI, precise-GC root model and
    composed runtime helpers while allowing a growing register-resident path.
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
