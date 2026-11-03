# U2 canonical checked-failure root boundary — opt-in reference

Selected 3 November 2026. This bounded step binds the *full typed*
`u2_failure_context.Context` to the canonical failure edge's first checked
payload parameter. This is not an independent executable IR or a new source
construct; it uses the existing `u2_continuation_bind.Pair`, `Function` and
aggregate signature tables. `u2_failure_root_bind.eri` independently rechecks
the destination, SSA block parameter, aggregate payload type, owners, source
revision and live typed primary. The reference pin holds the identity-linked
context and is charged to the existing function owner. It must be released.

The native owned runtime already maintains saved failure records with 80/88
secondary links, a protected-failure root, and source-level root-map/handler
safe-point handling (see `OWNED_RESOURCE_RUNTIME.md` and
`src/runtime/graph_failure_x86_64.eri`). **This opt-in binding is NOT that
native collector root map.** No change to the 32-byte ABI, physical runtime,
GC safe-point scheduler or production compiler is claimed here.

Before U2 acceptance, canonical lowering must publish the pin into an actual
target-specific safe-point root slot before any allocating call, preserve the
primary and all secondary/managed Text/List/identity payloads through both
checked edges, and invalidate roots only after propagation/handler cleanup.
The native root tracer must verify that failure snapshots and secondary links
remain live under forced GC, including nested close failures, allocator
refusal, cancellation, abandoned handlers and stale stack maps. Independent
cross-target validation and physical allocation evidence remain mandatory.

This PR's focused regression validates only the exact canonical binding and
charged reference-pin lifecycle against a hand-built scoped-owner Function.
It is not final U2 resource/runtime/GC qualification.
