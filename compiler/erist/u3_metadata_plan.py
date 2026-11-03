"""Private U3 scalar metadata plan, not canonical publication.

Maps validated semantic node facts to deterministic source anchors and
signatures for the owned Eristavi U1 metadata builder. No public schema.
"""
from __future__ import annotations
from dataclasses import dataclass
from compiler.erist.u3_shadow_gate import SourceRevision, ScalarSignature
from compiler.erist.u3_semantic_bridge import ScalarPlan

@dataclass(frozen=True)
class Anchor:
    node_id: int
    source_index: int
    start: int
    end: int
    line: int
    column: int

@dataclass(frozen=True)
class FunctionDeclaration:
    function_id: int
    symbol: str
    signature: ScalarSignature
    declaration_anchor: int

@dataclass(frozen=True)
class MetadataPlan:
    revisions: tuple[SourceRevision, ...]
    anchors: tuple[Anchor, ...]
    declarations: tuple[FunctionDeclaration, ...]

def plan_metadata(revisions: tuple[SourceRevision, ...], plan: ScalarPlan) -> MetadataPlan:
    if not revisions or len({rev.logical_name for rev in revisions}) != len(revisions):
        raise ValueError("invalid source revision registry")
    source_index = {rev.logical_name: i + 1 for i, rev in enumerate(revisions)}
    anchors = []
    anchor_index = {}
    for node_id, fact in sorted(plan.facts.items()):
        index = source_index.get(fact.source_name)
        if index is None or fact.end > revisions[index - 1].size:
            raise ValueError("semantic fact has no matching source revision")
        anchor_index[node_id] = len(anchors) + 1
        anchors.append(Anchor(node_id, index, fact.start, fact.end, fact.line, fact.column))
    declarations = tuple(
        FunctionDeclaration(i + 1, fn.symbol, fn.signature, anchor_index[fn.node_id])
        for i, fn in enumerate(plan.functions)
    )
    return MetadataPlan(revisions, tuple(anchors), declarations)
