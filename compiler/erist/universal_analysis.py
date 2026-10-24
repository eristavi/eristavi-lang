from __future__ import annotations

from dataclasses import dataclass

from .universal_ir import UBranch, UFunction, UReturn


@dataclass(frozen=True)
class LiveRange:
    value_id: int
    type_name: str
    start: int
    end: int


@dataclass(frozen=True)
class StackSlotPlan:
    slots: dict[int, int]
    slot_count: int


@dataclass(frozen=True)
class EscapeInfo:
    escaping_values: frozenset[int]
    reasons: dict[int, tuple[str, ...]]


def _instruction_positions(fn: UFunction):
    position = 0
    for block in fn.blocks:
        for ins in block.instructions:
            yield position, ins
            position += 1
        yield position, block.terminator
        position += 1


def live_ranges(fn: UFunction) -> list[LiveRange]:
    definitions: dict[int, tuple[str, int]] = {}
    last_use: dict[int, int] = {}
    for position, item in _instruction_positions(fn):
        if hasattr(item, "result") and item.result is not None:
            definitions[item.result.id] = (item.result.type_name, position)
        args = getattr(item, "args", ())
        for arg in args:
            last_use[arg.id] = max(last_use.get(arg.id, position), position)
        if isinstance(item, UBranch):
            last_use[item.condition.id] = max(last_use.get(item.condition.id, position), position)
        if isinstance(item, UReturn) and item.value is not None:
            last_use[item.value.id] = max(last_use.get(item.value.id, position), position)
    return [
        LiveRange(value_id, type_name, start, max(start, last_use.get(value_id, start)))
        for value_id, (type_name, start) in sorted(definitions.items())
    ]


def coalesce_stack_slots(fn: UFunction) -> StackSlotPlan:
    """First-fit interval coloring for stack-spilled Universal-IR values.

    The current lower IR is stack-friendly and does not yet contain phi nodes.
    This conservative flattened ordering therefore provides a safe bootstrap
    slot allocator while keeping locals separate from temporary spill storage.
    """
    ranges = sorted(live_ranges(fn), key=lambda item: (item.start, item.end, item.value_id))
    active: list[tuple[int, int]] = []  # (end, slot)
    free: list[int] = []
    slots: dict[int, int] = {}
    next_slot = 0
    for item in ranges:
        still_active = []
        for end, slot in active:
            if end < item.start:
                free.append(slot)
            else:
                still_active.append((end, slot))
        active = still_active
        if free:
            slot = min(free)
            free.remove(slot)
        else:
            slot = next_slot
            next_slot += 1
        slots[item.value_id] = slot
        active.append((item.end, slot))
    return StackSlotPlan(slots, next_slot)


def escape_analysis(fn: UFunction) -> EscapeInfo:
    reasons: dict[int, set[str]] = {}
    heap_producers = {}
    for _, item in _instruction_positions(fn):
        result = getattr(item, "result", None)
        if result is not None:
            heap_producers[result.id] = result.type_name
        op = getattr(item, "op", None)
        args = getattr(item, "args", ())
        if op == "call":
            for arg in args:
                reasons.setdefault(arg.id, set()).add("passed-to-call")
        elif op in ("set_error", "list_add", "list_set", "set_field"):
            for arg in args[1:] if op in ("list_add", "list_set", "set_field") else args:
                reasons.setdefault(arg.id, set()).add("stored-into-runtime-object")
        elif op == "make_identity":
            for arg in args:
                reasons.setdefault(arg.id, set()).add("captured-by-identity")
        if isinstance(item, UReturn) and item.value is not None:
            reasons.setdefault(item.value.id, set()).add("returned")
    return EscapeInfo(
        frozenset(reasons),
        {value_id: tuple(sorted(values)) for value_id, values in reasons.items()},
    )


def register_candidates(fn: UFunction) -> tuple[int, ...]:
    """Return short-lived scalar values suitable for a future register allocator.

    This is deliberately a target-neutral candidate set. Actual register names,
    call-clobber constraints, and spilling remain backend-specific.
    """
    scalar = {"i64", "bool", "f64"}
    return tuple(
        item.value_id
        for item in live_ranges(fn)
        if item.type_name in scalar and item.end - item.start <= 3
    )
