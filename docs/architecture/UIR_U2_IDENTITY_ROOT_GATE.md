# U2 — bounded identity descriptor and SSA-root admission

**Status: focused Linux-verified development slice, NOT native canonical
identity lowering, completed U2 acceptance or production promotion.**
Draft [PR #111](https://github.com/eristavi/eristavi-lang/pull/111);
issue [#74](https://github.com/eristavi/eristavi-lang/issues/74) remains open.

## Meaning and frozen contracts

Ordinary Eristavi values copy logically. Explicit `identity T` copies a
shared handle and preserves observable aliases. The collector may reclaim an
identity cycle only after every reachable, registered native root has been
removed. A checked primary error remains primary through cleanup; any
secondary cleanup failures remain ordered. GC must never act as deterministic
File/socket/resource closure. No source spelling, runtime public 32-byte ABI,
canonical executable opcode or production backend changes are introduced.

## Implemented source-neutral identity gate

`src/compiler/u2_identity_root_gate.eri` is an opt-in verifier combining
the **existing** immutable U1b structural carrier and the version-one
`u2_managed_types` registry:

- Requires the exact carrier to belong to the same frozen aggregate graph and
  be a declared nonprimitive aggregate, with owner-family agreement.
- Reruns the independent `managed.verify`, then checks the selected
  managed descriptor is **kind 3 / copyPolicy 2 / base domain 0** with the
  exact structural payload `carrier.index`.
- Rejects an ordinary Text copy descriptor, wrong payload carrier, foreign
  managed TypeId/registry and incompatible allocation/owner contexts without
  generating any native machine instructions.
- Calls the existing `ssa.create`, which performs full canonical
  fallible-registry/Function verification and bounded liveness construction;
  the caller can independently recompute the plan with `ssa.verify` and
  validate exact published live ValueIds with `ssa.requirePublished`.
- Inherits the existing **32 selected ValueId limit**, 64-block and 512-edge
  bounded proof, cancellation/budget behavior, and explicit plan close.
  It does **not** infer an identity machine root class from a bare U1b
  structural TypeId. A separate target-specific exact representation check
  remains mandatory before any native class-1 publication.

This is an *admission proof* for later identity lowering. It does not
turn a deterministic File owner into a sharable identity handle and does not
invent an executable second IR.

## Independent behavioral and physical probes

The focused `tests/test_u2_identity_root_gate.py` test dynamically
augments the existing canonical aggregate CFG/backedge fixture with a frozen
identity-of-structural-payload descriptor. It validates exact SSA entry,
exit, after-instruction and publication facts, rejects the wrong descriptor,
foreign identity handle, wrong carrier and missing required root, and closes
the allocated plan/registry.

The Linux x86-64 `tests/test_u2_identity_gc_cleanup.py` test uses the
pre-existing owned graph runtime. It constructs a three-node cyclic graph
and registers two class-1 alias roots, explicitly forces collection, verifies
all **three** nodes remain live, releases the first root, repeats collection
and verifies the same three nodes survive, then releases the last root and
requires **zero** surviving graph objects and clean teardown.

A further program deliberately keeps an identity cycle in an ordinary
checked `Problem` error payload while allocating 200 temporary cycles.
The original unchecked production source compiler's Stage-0 interpreter,
native C implementation and existing owned-runtime program are compared
against the same exact outputs, including the identity self-alias and the
retained typed error message/link. The owned graph allocator and failure
objects must be reclaimed on final teardown. **This is differential
reference/runtime behavior, not new canonical opcode-46 identity lowering.**

**Focused evidence:** implementation
[`1397628`](https://github.com/eristavi/eristavi-lang/commit/139762896ff8f71c0d5ab1e019cf76ac737967da),
[Linux CI #41993529224](https://github.com/eristavi/eristavi-lang/actions/runs/41993529224):
**4 tests run, 4 passed, 0 failed**. Earlier exploratory red runs were
caused by test-only local shadowing and an unbound test fixture helper;
both were corrected without changing language semantics or weakening
verification. Cross-suite smoke evidence is recorded separately in
`HANDOVER.md` when it is complete.

## Performance, limitations and next proof

The type/SSA admission gate is intentionally bounded and never in the
production compiler hot path. It performs independent metadata verification;
we have not measured compile-time overhead, allocator traffic, retained
owner memory, RSS or collector-pause latency. No overall performance claim
is justified from these four probes.

**Still required:** explicit canonical identity-producing instructions and
value representation, native class-1 root stores controlled by verified SSA
obligations across all instruction/edge/handler/recursion boundaries,
independent cyclic identity mutation semantics with nested lists,
automatic combined saved `FailureContext` + deterministic File cleanup
without loss of caller identity roots, forged/stale/dead root and
allocation-refusal tests, physical size/GC/pause measurements, Stage-0
behavior/source-origin A/B for the new canonical emitter, and the exact-head
four-platform CI/qualification gate. Keep #111 draft and #74 open.

## 5 November 2026 — native checked File cleanup with live identity aliases

The additional `tests/test_u2_identity_file_cleanup.py` test physically
combines the **existing, separately verified native three-File cleanup helper**
with two class-1 identity alias roots in a nested owned scope and one class-5
saved primary failure root. The test preserves the original File/FileError
runtime descriptors, adds private typed nodes to form a three-node cycle,
injects actual File-close failures, forces real GC after the resource
cleanup, and checks the identity cycle survives while one alias remains.
It then clears the second identity root, leaves the nested scope, releases the
saved failure and the outer resource scope, and requires the existing runtime
finish/leak audit to succeed. The original primary and reverse-close ordered
secondaries must match the test's independent expected output.

The [focused Linux run #41993529224](https://github.com/eristavi/eristavi-lang/actions/runs/41993529224)
passed **all four identity methods** after correcting a test-only generated
caller-prologue text anchor. This is a **bounded runtime composition**, NOT
automatic canonical identity/File cleanup Function lowering, nor full physical
RSS/GC-pause or four-platform qualification. General typed identity source
semantics and all original ABI contracts remain unchanged.
