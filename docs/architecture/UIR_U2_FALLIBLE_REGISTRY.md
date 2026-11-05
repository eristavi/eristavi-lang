# U2 fallible contract table — version one

This optional, private metadata extension binds checked failure signatures to
canonical FunctionIds. It is not another executable IR or public artifact.
The existing declarations remain authoritative for normal parameters/results,
import versions and effects. A signature returning zero values defines no value.

Before implementation, select a dense two-word record per existing declaration:
the exact normal SignatureId and a failure SignatureId, or zero for no checked
failure. The unchanged declaration ceiling is 65,536, so at most 131,072 words
are admitted under existing shared/request capacity, traffic and work budgets.
Construction is O(declarations + selected contracts); fresh validation is
O(declarations + failure signature entries). Per-call lookup is O(1). No cache
or per-block mask is introduced. These are admission policies, not measurements.

The extension has exact metadata/type-graph ownership and version one. All
records are independently reread on every verification, including unused
contracts. Normal signature snapshots must match current declarations. Every
selected failure signature has zero inputs and exactly one declared aggregate
payload. The structural payload is not the completed managed FailureContext.
Duplicate, foreign, unknown-version and malformed records refuse. Failed
construction closes all table backing; consumed traffic/work is retained.

Canonical invoke.direct.v1 keeps opcode 46 and two consecutive outcome edges.
Its payload names the actual FunctionId, not a helper symbol. Negative edge
argument markers denote fresh edge-produced result ordinals; they cannot be
ordinary SSA values. Destination block parameters carry the exact normal or
failure tuple. SSA dominance applies at their destination block entries.
An ordinary call cannot name a function declared fallible in this table.
Legacy profiles reject invokes. Existing single-contract verification remains
an explicitly bounded compatibility entry, not a production default.

Acceptance requires several targets in one canonical function, mixed normal and
fallible declarations, zero/multiple results, dead malformed invokes and unused
contract mutations, restored-table verification, scope/owner/version mismatch,
work/cancellation/refusal cleanup and independent outcomes. Whole-function
resource ownership, managed values/contexts/roots and production adapters remain
separate U2 gates. No merge or full U2 completion follows from this extension.

## Continuation transport prerequisite for scoped owners

Before adding ownership instructions, permit ordinary, already-defined SSA
values to follow the fresh outcome tuple on either edge. Up to 128 transferred
values per edge use the unchanged edge-argument pool and its original quotas.
An outcome's first N entries remain exact negative result ordinals; all suffix
entries are positive existing ValueIds, type-checked against destination block
parameters and checked for predecessor availability. This makes retained outer
values explicit without fabricating call results or relying on a hidden stack.

Version-two private destination descriptors allow those typed suffixes; version
one remains the original exact-tuple binding. The builder initially forwards
the same value sequence on both mutually exclusive outcomes. No resource owner
meaning is inferred from ordinary transfers: a later scoped-owner gate must
prove acquisition, LIFO consumption and exact owner signatures independently.
