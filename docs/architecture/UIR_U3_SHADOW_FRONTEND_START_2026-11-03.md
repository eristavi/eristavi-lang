# U3 shadow frontend — implementation boundary

Status: development plan, not implemented or qualified. Issue #75.

## Existing decisions

The approved AST and frozen semantic facts construct one owned source-neutral typed UIR directly. No mandatory source-close executable Typed IR. U1a/U1b canonical publication, fresh all-block verification, mandatory eligible-place promotion and independent oracles remain authoritative. U2 #74 is unfinished; production migration is prohibited until U2 passes.

## First independent implementation slice

1. Inventory existing AST, semantic-fact, UIR builder and source-location entrypoints before changing code.
2. Add an opt-in, non-default shadow construction path for source functions limited to supported U1 scalar types, function calls, basic blocks, branch edges and loop-carried SSA. Reject unsupported syntax explicitly; never silently fall back to different semantics inside the shadow artifact.
3. Reuse canonical owner-bound type/signature tables and registry. Preserve source digest and LocId/parent provenance, effect contracts, exact revision and fresh independent verifier. No public artifact serialization change.
4. Compare UIR reference execution with Stage-0 and existing production compiler on deterministic scalar/CFG fixtures, including malformed unreachable blocks, checked Int faults and strict f64.
5. Bound build/verifier work, temporary allocation, owner peak/traffic and cancellation; use focused tests, not full CI during development.

## Integration gate

Managed Text/List/identity, checked failures, resource cleanup and GC safe points must use U2's accepted contracts. Do not promote this shadow path to default, close #75 or merge a compiler implementation batch without exact-head full CI and qualification. Maintain rollback and old backend.
