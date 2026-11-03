"""Private U3 frozen-semantic-fact bridge, not an executable UIR builder.

A semantic analyzer must provide identity-checked node facts. This module
constructs a bounded, immutable scalar plan for subsequent Eristavi-owned
canonical U1 metadata/building. It never trusts inferred types from syntax.
"""
from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping
from compiler.erist.u3_shadow_gate import SCALAR_TYPES, ScalarSignature

MAX_NODES = 1_048_576
MAX_FUNCTIONS = 65_536

@dataclass(frozen=True)
class FrozenNodeFact:
    node_id: int
    token: int
    type_name: str
    effect_mask: int
    source_name: str
    start: int
    end: int
    line: int
    column: int

@dataclass(frozen=True)
class FrozenFunction:
    symbol: str
    node_id: int
    signature: ScalarSignature
    body_node_ids: tuple[int, ...]

@dataclass(frozen=True)
class ScalarPlan:
    functions: tuple[FrozenFunction, ...]
    facts: Mapping[int, FrozenNodeFact]

def freeze_scalar_facts(
    functions: tuple[FrozenFunction, ...],
    facts: tuple[FrozenNodeFact, ...],
    source_sizes: Mapping[str, int],
) -> ScalarPlan:
    """Reject stale/ambiguous facts before any U1 owner or builder allocation."""
    if not functions or len(functions) > MAX_FUNCTIONS or len(facts) > MAX_NODES:
        raise ValueError("invalid U3 fact cardinality")
    table = {}
    for fact in facts:
        if type(fact.node_id) is not int or fact.node_id < 1 or fact.node_id in table:
            raise ValueError("duplicate or invalid AST identity")
        if type(fact.token) is not int or fact.token < 0:
            raise ValueError("invalid token ordinal")
        if fact.type_name not in SCALAR_TYPES or type(fact.effect_mask) is not int or not 0 <= fact.effect_mask <= 63:
            raise ValueError("unsupported scalar semantic fact")
        length = source_sizes.get(fact.source_name)
        if type(length) is not int or not 0 <= fact.start <= fact.end <= length or fact.line < 1 or fact.column < 1:
            raise ValueError("invalid semantic source anchor")
        table[fact.node_id] = fact
    names = set()
    for function in functions:
        if not function.symbol or function.symbol in names or function.node_id not in table:
            raise ValueError("missing or duplicate function declaration")
        names.add(function.symbol)
        if any(t not in SCALAR_TYPES for t in function.signature.parameters + function.signature.results):
            raise ValueError("unsupported function signature")
        if not function.body_node_ids or len(set(function.body_node_ids)) != len(function.body_node_ids):
            raise ValueError("invalid function body identity list")
        if any(node not in table for node in function.body_node_ids):
            raise ValueError("unresolved AST semantic fact")
    return ScalarPlan(tuple(functions), MappingProxyType(table))
