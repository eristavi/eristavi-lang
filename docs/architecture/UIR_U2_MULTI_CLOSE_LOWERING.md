# U2 multi-owner checked-close lowering: bounded canonical stage contract

Status: selected 2 November 2026 for an incremental, **unqualified** development
slice; not a completed multi-resource or managed FailureContext implementation.
Governing rules: DESIGN_PHILOSOPHY.md, LANGUAGE_SEMANTICS.md,
RESOURCE_CLEANUP.md, UIR_U2_CONTINUATION_CONTRACT.md and HANDOVER.md.

## Semantics first

Exiting nested `with` scopes consumes handles in **reverse acquisition order**,
including on checked failures. Each handle is consumed before both checked
outcomes of its close operation. A pending return remains available only
while cleanup succeeds. If cleanup fails, that exit is checked failure, not
success. An already-active primary failure must persist, and subsequent close
failures become ordered secondary diagnostics. Terminal defects are separate.

Do not treat a tuple of two ordinary aggregate errors as the completed
`FailureContext`. Until canonical managed contexts and safe-point roots exist,
the optional reference profile can prove owner/edge transport and retention of
one pending typed primary, **not** correct secondary composition.

## Architecture, budgets and selected scope

Use the existing canonical Function instruction, operand, edge, and parameter
pools and `invoke.direct.v1` (opcode 46); no second executable IR or new ABI.
The existing independently verified private Plan has two records for each
exiting lexical owner: mode 0 (not yet failing) and mode 1 (failure propagating).
Position 0 consumes the innermost exited owner, and position `depth-1` consumes
the outermost exited owner. Rows are `(mode * depth + position) * 8`; the
whole plan must be verified afresh at every consuming stage, even when frozen.
The plan stores the original SSA owner ValueIds at the exit boundary; later
canonical block parameters may be different SSA IDs for the **same lexical
owner scope**. Requiring identical SSA IDs at subsequent stages would be wrong.

The proposed `emitAt` construction adapter:
- Verifies owner, graph, version, complete plan, exact original obligations,
  checked close contract, current lexical owner signature, handle type/source
  definition and LocId before writing canonical pools.
- Requires the current source signature to contain exactly the still-live
  lexical prefix. Every transferred handle matches that current prefix
  **in order**; no consumed resource is copied or reintroduced.
- Requires an existing failure-mode stage to carry its typed structural
  primary on both outcomes. This does not yet append an additional failure.
- Uses the already checked `u2_invoke_transfer.emit` constructor and retains
  its poisoned-on-partial-write refusal protocol. Only a newly verified
  complete Function and scoped-owner Profile can be consumed subsequently.

Bounded depth <=128, the existing unchanged Plan record cap 2048 words and
Function budget 8 MiB owner peak / 64 MiB traffic qualification policy remain
unchanged. A fresh full-plan check per step costs O(depth^2) for a whole
depth-sized emitted chain (<=16,384 row visits at depth 128 before metadata
work); this is an **explicit prototype cost** to measure before admission into
general production lowering, never a claimed optimization. No unbounded cache
or hidden global mutable state is introduced.

## Incremental acceptance and exclusions

Exercise a two-owner canonical close chain from existing scoped-owner fixture:
inner normal or failure must both reach an outer close, retaining precisely one
outer handle. Emitting the outer close uses the **same verified original plan**,
but an edge-produced new block-parameter ValueId. Test another stage with an
already-active typed primary; check source LocIds, scope/argument prefixes,
invalid stage indices/modes, swapped handles, dropped primaries and mutated
plan/registry negative cases. Independent canonical and scoped-owner verification
must continue to reject malformed reachable and dead instructions. Focused smoke
only for this incremental batch.

Still open: actually construct **all** failure-mode rows from a single managed
FailureContext, merge new checked close failures into its ordered secondary
chain, validate complete route topology and every exit, execute real file
resource adapters, GC roots, Unicode17 managed Text/List/identity, deep
fault/physical tests and final four-platform completed-batch qualification.
Do not close U2 issue #74 or merge its draft PR based on this slice.
