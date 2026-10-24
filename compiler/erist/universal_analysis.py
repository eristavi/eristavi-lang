from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from .universal_ir import BOOL, F64, I64, UBranch, UFunction, UJump, UReturn


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


@dataclass(frozen=True)
class BlockLiveness:
    live_in: dict[str, frozenset[int]]
    live_out: dict[str, frozenset[int]]
    live_after_instruction: dict[tuple[str, int], frozenset[int]]


def _instruction_positions(fn: UFunction):
    position = 0
    for block in fn.blocks:
        for ins in block.instructions:
            yield position, ins
            position += 1
        yield position, block.terminator
        position += 1


def _uses(item) -> set[int]:
    result = {arg.id for arg in getattr(item, "args", ())}
    if isinstance(item, UBranch):
        result.add(item.condition.id)
    elif isinstance(item, UReturn) and item.value is not None:
        result.add(item.value.id)
    return result


def _successors(block) -> tuple[str, ...]:
    term = block.terminator
    if isinstance(term, UJump):
        return (term.target,)
    if isinstance(term, UBranch):
        return (term.true_target, term.false_target)
    return ()


def value_types(fn: UFunction) -> dict[int, str]:
    result: dict[int, str] = {}
    for block in fn.blocks:
        for ins in block.instructions:
            if ins.result is not None:
                result[ins.result.id] = ins.result.type_name
    return result


def cfg_liveness(fn: UFunction) -> BlockLiveness:
    """Compute SSA-value liveness over the real Universal-IR CFG.

    Universal IR currently has no phi instructions. Values may nevertheless be
    consumed in successor blocks, loops, and branch terminators, so a flattened
    instruction order is not sufficient for GC/root or spill-slot decisions.
    This dataflow analysis intentionally operates on value ids only; locals have
    stable dedicated storage and are handled separately by direct backends.
    """

    names = {block.name for block in fn.blocks}
    use: dict[str, set[int]] = {}
    defs: dict[str, set[int]] = {}
    successors: dict[str, tuple[str, ...]] = {}

    for block in fn.blocks:
        block_use: set[int] = set()
        block_def: set[int] = set()
        for ins in block.instructions:
            for value_id in _uses(ins):
                if value_id not in block_def:
                    block_use.add(value_id)
            if ins.result is not None:
                block_def.add(ins.result.id)
        for value_id in _uses(block.terminator):
            if value_id not in block_def:
                block_use.add(value_id)
        succ = _successors(block)
        missing = [target for target in succ if target not in names]
        if missing:
            raise ValueError(f"Universal-IR liveness found missing successor(s): {', '.join(missing)}")
        use[block.name] = block_use
        defs[block.name] = block_def
        successors[block.name] = succ

    live_in = {block.name: set() for block in fn.blocks}
    live_out = {block.name: set() for block in fn.blocks}
    changed = True
    while changed:
        changed = False
        for block in reversed(fn.blocks):
            name = block.name
            new_out: set[int] = set()
            for target in successors[name]:
                new_out.update(live_in[target])
            new_in = use[name] | (new_out - defs[name])
            if new_out != live_out[name] or new_in != live_in[name]:
                live_out[name] = new_out
                live_in[name] = new_in
                changed = True

    live_after_instruction: dict[tuple[str, int], frozenset[int]] = {}
    for block in fn.blocks:
        live = set(live_out[block.name])
        live.update(_uses(block.terminator))
        for index in range(len(block.instructions) - 1, -1, -1):
            ins = block.instructions[index]
            live_after_instruction[(block.name, index)] = frozenset(live)
            if ins.result is not None:
                live.discard(ins.result.id)
            live.update(_uses(ins))

    return BlockLiveness(
        {name: frozenset(values) for name, values in live_in.items()},
        {name: frozenset(values) for name, values in live_out.items()},
        live_after_instruction,
    )


def live_ranges(fn: UFunction) -> list[LiveRange]:
    definitions: dict[int, tuple[str, int]] = {}
    last_use: dict[int, int] = {}
    for position, item in _instruction_positions(fn):
        if hasattr(item, "result") and item.result is not None:
            definitions[item.result.id] = (item.result.type_name, position)
        for value_id in _uses(item):
            last_use[value_id] = max(last_use.get(value_id, position), position)
    return [
        LiveRange(value_id, type_name, start, max(start, last_use.get(value_id, start)))
        for value_id, (type_name, start) in sorted(definitions.items())
    ]


def interference_graph(fn: UFunction) -> dict[int, frozenset[int]]:
    """Return a conservative CFG-aware interference graph for virtual values."""

    types = value_types(fn)
    graph: dict[int, set[int]] = {value_id: set() for value_id in types}
    liveness = cfg_liveness(fn)

    def connect(values) -> None:
        present = sorted(value for value in values if value in graph)
        for left, right in combinations(present, 2):
            graph[left].add(right)
            graph[right].add(left)

    for block in fn.blocks:
        connect(liveness.live_out[block.name])
        live_before_term = set(liveness.live_out[block.name]) | _uses(block.terminator)
        connect(live_before_term)
        for index, ins in enumerate(block.instructions):
            live_after = set(liveness.live_after_instruction[(block.name, index)])
            connect(live_after)
            if ins.result is not None:
                for other in live_after:
                    if other != ins.result.id and other in graph:
                        graph[ins.result.id].add(other)
                        graph[other].add(ins.result.id)

    return {value_id: frozenset(neighbors) for value_id, neighbors in graph.items()}


def coalesce_stack_slots(
    fn: UFunction,
    pinned_values: set[int] | frozenset[int] = frozenset(),
    excluded_values: set[int] | frozenset[int] = frozenset(),
) -> StackSlotPlan:
    """Color virtual-value spill slots using CFG liveness.

    Pinned values receive unique, never-reused slots. Direct GC backends pin
    heap-valued temporaries so a root frame can attach one stable type descriptor
    to each address.

    Excluded values receive no spill slot at all. Direct native backends use this
    for virtual values whose complete lifetime is represented by an allocated
    physical register. Pinned storage always wins over exclusion: a value needed
    as a stable compiler root can never be removed from the frame accidentally.

    Remaining values are greedily colored by interference.
    """

    graph = interference_graph(fn)
    pinned = sorted(value_id for value_id in pinned_values if value_id in graph)
    pinned_set = set(pinned)
    excluded = {
        value_id
        for value_id in excluded_values
        if value_id in graph and value_id not in pinned_set
    }

    slots: dict[int, int] = {value_id: index for index, value_id in enumerate(pinned)}
    first_reusable = len(pinned)

    unpinned = [
        value_id
        for value_id in graph
        if value_id not in slots and value_id not in excluded
    ]
    unpinned.sort(key=lambda value_id: (-len(graph[value_id]), value_id))
    for value_id in unpinned:
        forbidden = {slots[neighbor] for neighbor in graph[value_id] if neighbor in slots}
        slot = first_reusable
        while slot in forbidden:
            slot += 1
        slots[value_id] = slot

    slot_count = (max(slots.values()) + 1) if slots else 0
    return StackSlotPlan(dict(sorted(slots.items())), slot_count)


def heap_values_live_across_safepoints(fn: UFunction, safe_ops: tuple[str, ...] = ("store_local",)) -> frozenset[int]:
    """Return heap temporaries that must survive at least one GC safe point."""

    types = value_types(fn)
    heap = {
        value_id
        for value_id, type_name in types.items()
        if type_name not in {I64, F64, BOOL, "void"}
    }
    if not heap:
        return frozenset()
    liveness = cfg_liveness(fn)
    required: set[int] = set()
    for block in fn.blocks:
        for index, ins in enumerate(block.instructions):
            if ins.op in safe_ops:
                required.update(heap.intersection(liveness.live_after_instruction[(block.name, index)]))
    return frozenset(required)


def escape_analysis(fn: UFunction) -> EscapeInfo:
    reasons: dict[int, set[str]] = {}
    for _, item in _instruction_positions(fn):
        op = getattr(item, "op", None)
        args = getattr(item, "args", ())
        if op == "call":
            for arg in args:
                reasons.setdefault(arg.id, set()).add("passed-to-call")
        elif op in ("set_error", "list_add", "list_set", "set_field"):
            selected = args[1:] if op in ("list_add", "list_set", "set_field") else args
            for arg in selected:
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
    """Return scalar values suitable for backend register allocation.

    Candidates are restricted to values whose live range is short in the
    presentation order. Actual allocation must still honor the CFG interference
    graph and target call-clobber rules.
    """

    scalar = {I64, BOOL, F64}
    graph = interference_graph(fn)
    ranges = {item.value_id: item for item in live_ranges(fn)}
    result = [
        value_id
        for value_id, item in ranges.items()
        if item.type_name in scalar and item.end - item.start <= 3 and len(graph.get(value_id, ())) <= 6
    ]
    return tuple(sorted(result))
