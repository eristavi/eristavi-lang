"""U3 scalar direct-construction pilot.

Builds a strict source-neutral *plan* from already frozen AST semantic facts,
not from legacy Typed IR. The plan is not canonical owned UIR and must not be
executed, published or selected as the default compiler pipeline.
"""
from __future__ import annotations
from dataclasses import dataclass
from compiler.erist.u3_semantic_bridge import ScalarPlan
from compiler.erist.u3_metadata_plan import MetadataPlan

MAX_OPERATIONS = 1_048_576
SUPPORTED = frozenset({"const.i64", "const.pred", "return"})

@dataclass(frozen=True)
class ScalarOperation:
    node_id: int
    opcode: str
    result_type: str | None
    payload: int | None = None

@dataclass(frozen=True)
class FunctionPlan:
    function_id: int
    operations: tuple[ScalarOperation, ...]

def construct_scalar_plan(
    semantic: ScalarPlan, metadata: MetadataPlan,
    operations: dict[str, tuple[ScalarOperation, ...]],
) -> tuple[FunctionPlan, ...]:
    if set(operations) != {fn.symbol for fn in semantic.functions}:
        raise ValueError("function plan mismatch")
    results = []
    total = 0
    for function, declaration in zip(semantic.functions, metadata.declarations):
        sequence = operations[function.symbol]
        total += len(sequence)
        if not sequence or total > MAX_OPERATIONS or sequence[-1].opcode != "return":
            raise ValueError("unterminated or over-budget scalar function")
        if any(op.opcode == "return" for op in sequence[:-1]):
            raise ValueError("instructions after terminator")
        for op in sequence:
            if op.node_id not in function.body_node_ids or op.node_id not in semantic.facts:
                raise ValueError("operation lacks frozen AST fact")
            if op.opcode not in SUPPORTED:
                raise ValueError("unsupported scalar operation")
            if op.opcode == "const.i64":
                if op.result_type != "i64" or type(op.payload) is not int or not -(1<<63) <= op.payload < (1<<63):
                    raise ValueError("invalid i64 constant")
            elif op.opcode == "const.pred":
                if op.result_type != "pred" or type(op.payload) is not int or op.payload not in (0, 1):
                    raise ValueError("invalid predicate constant")
            elif op.result_type is not None or op.payload is not None:
                raise ValueError("invalid return marker")
        results.append(FunctionPlan(declaration.function_id, sequence))
    return tuple(results)
