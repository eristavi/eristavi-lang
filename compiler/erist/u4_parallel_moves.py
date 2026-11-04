"""Private U4 reference planner for simultaneous SSA block-parameter moves.

This is a target-independent oracle for scalar machine-location scheduling,
not the production x86-64 emitter. A spare scratch location is mandatory for
cycles; allocation and root-aware liveness are future integration gates.
"""
from __future__ import annotations

MAX_MOVES = 65536

def plan_parallel_moves(assignments: tuple[tuple[str, str], ...], scratch: str) -> tuple[tuple[str, str], ...]:
    """Return sequential (destination, source) copies preserving simultaneous semantics."""
    if not isinstance(scratch, str) or not scratch:
        raise ValueError("missing scratch location")
    if len(assignments) > MAX_MOVES:
        raise ValueError("parallel move budget")
    pending = {}
    destinations = set()
    sources = set()
    for destination, source in assignments:
        if not isinstance(destination, str) or not isinstance(source, str) or not destination or not source:
            raise ValueError("invalid machine location")
        if destination in destinations:
            raise ValueError("duplicate destination")
        destinations.add(destination)
        sources.add(source)
        if destination != source:
            pending[destination] = source
    if scratch in destinations or scratch in sources:
        raise ValueError("scratch aliases live machine location")
    result = []
    while pending:
        # A destination not read by any pending assignment is safe to overwrite.
        reads = set(pending.values())
        ready = next((dst for dst in pending if dst not in reads), None)
        if ready is not None:
            result.append((ready, pending.pop(ready)))
            continue
        # All remaining destinations are read: save one destination's old value.
        destination = next(iter(pending))
        result.append((scratch, destination))
        # Replace reads of saved old destination; this breaks its dependency cycle.
        for dst, src in tuple(pending.items()):
            if src == destination:
                pending[dst] = scratch
    return tuple(result)
