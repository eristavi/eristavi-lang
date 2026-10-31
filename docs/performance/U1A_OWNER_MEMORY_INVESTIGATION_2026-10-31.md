# PR #105: physical U1 owner memory investigation

**31 October 2026. Active collision correction; NOT QUALIFIED.** Hosted smoke
[41220371417](https://github.com/eristavi/eristavi-lang/actions/runs/41220371417)
passed 34/35 but caught a direct-mapped-cache collision: 9,725,616 B peak,
515,478,752 B traffic and 1,035,287 stress allocations under hosted placement.
Initial local passes did not qualify the rejected direct-map candidate.
The corrected cache searches a sixteen-slot bounded window, including
invalidation through deletion holes, and rotates full-window victims. This
prevents hot identities repeatedly displacing each other in the initial slot.
The 256-entry table remains bounded; its victim cursor adds eight bytes, for
**4,112 B total shared cache state**. The full physical diagnostic now forces
ALL initial identity hashes to the same bucket. Seven focused regressions
passed, including the adversarial 65,536-word fixture: 7,853,712 B phase peak,
21,957,296 B traffic, 72,682 allocations; exact stress backing 6,653,840 B /
16,938 objects, all reclaimed. Eight and sixteen probes without rotating
victims failed the adversarial traffic gate; those prototypes were rejected.
Hosted smoke and final release gates remain pending. Full-window eviction,
stale-body checks and escaped-reference fallback retain conservative detachment.
Issue #77 remains open; nothing has been merged.
Local collision-stable implementation checkpoint: `9cf5b30`. The hosted submission/tested tree
is recorded in HANDOVER; raw source hashes bind these measurements independently
of commit metadata. No source-language, public value ABI,
production backend selection or U1 budget limit changed.

## What failed

The original diagnostic measured **24,400,832 B** stress-phase peak against
**8,388,608 B**, with **1,533,455,872 B** cumulative block traffic and
**3,215,578 graph allocations**. It correctly exposed substantial real overhead.
However, phase tags alone did not exactly partition semantic owners: function
publication copies were created in the metadata phase, and each phase also
included bookkeeping and temporary objects. Structural requested bytes were
not actual allocator capacity. The old PR description's no-oversized-reuse
experiment had already been superseded and could not justify the new counters.

Raw before/after data, exact backing observations, compiler/platform and source
hashes: [u1a-owner-physical-105.json](../evidence/2026-10-31/u1a-owner-physical-105.json).

## Changes and their contracts

1. **Aggregate word-store accounting.** Every successfully created node/page
   extends the store's existing allocation lease through `budget.commitInto`.
   Reservation admission, parent capacity, cumulative traffic, state validation,
   cancellation and work charges stay intact. Foreign, repeated or released
   capabilities reject before mutation. One store lease replaces thousands of
   independently managed bookkeeping records. Closing revokes access before
   releasing the aggregate charge; managed collection remains separate.
2. **Optional identity member writes.** The existing compiler reads the shared
   identity handle when updating its member, avoiding an unnecessary copy of
   the ordinary optional wrapper. Replacing an optional payload still uses its
   original mutable-place/COW path. Evaluation order is preserved.
3. **Bounded identity backing reuse.** On x86-64, first field mutation detaches
   an identity's ordinary payload. A nonowning 256-entry key/body cache permits
   subsequent writes to reuse that private body. Sixteen probes and rotating victims avoid repeated direct-map
   collision thrash; lookup/invalidation continue through deletion holes. Value snapshot reads invalidate
   the entry; graph mark and sweep clear keys before reclamation. Collisions
   re-clone; stale body matches are checked. Escaping a mutable identity payload
   reference permanently selects the original detach path for that runtime
   lifetime, since collection cannot revoke a reference. No new allocation is
   needed for this cache; static cost is **4,112 B**, explicitly shared overhead.
4. **Bounded allocator reuse.** Oversized free blocks split when their remainder
   can hold a block header plus a minimum 16-byte payload. The tail stays within
   the original verified region. A 64-class bitmap covers aligned sizes through
   1,024 B, including U1 node/page bodies; small free blocks do not clog the large
   first-fit chain. Class lookup is bounded/constant, metadata is checked, and
   release-all clears every head and bitmap bit. Added static state: **1,544 B**.
5. **Actual semantic-owner observations.** The private diagnostic intercepts
   acceptance-only self-equality events to identify each explicitly traversed
   identity wrapper/current body by allocator address. It deduplicates addresses,
   checks owner agreement, reports real retained block capacities and follows
   their GC reclamation. The independent radix/scratch oracle and source-schema
   pins validate shape separately. Construction-phase histories remain distinct
   conservative peak/traffic envelopes, including transient/bookkeeping overhead.
   Shared regions/slack and diagnostic maps are not assigned to arbitrary owners.

The original 65,536-word/4,096-page stress fixture and 8 MiB peak/64 MiB traffic
limits remain. Real selected production import, metadata, function, publication
and live dominance scratch are exercised. No test, oracle, timeout or limit was
removed or relaxed to produce the pass.

## Local results

| Measure | Original candidate | Corrected candidate |
| --- | ---: | ---: |
| Stress construction-phase physical peak | 24,400,832 B | 7,853,712 B (all initial hashes colliding) |
| Stress construction-phase cumulative traffic | 1,533,455,872 B | 21,957,296 B |
| Graph allocations in stress construction phase | 3,215,578 | 72,682 |
| Exact observed retained stress backing | Not independently partitioned | 6,653,840 B / 16,938 wrapper-body objects |
| Observed backing after final collection | Not independently partitioned | 0 B / all observed objects reclaimed |

Actual allocator reuse and address placement can vary small raw values. The
scope is this fixed acceptance workload, not a global allocator memory cap.
The phase envelope also includes temporary graph allocations not owned by the
retained UIR buffers. Every original ledger returns to zero independently.

Focused native regressions verify ordinary snapshots, shared aliases, nested
value detachment, optional rebinding, escaped-reference fallback, GC cache
invalidation, free-block tail reuse, high bitmap bit/multiple same-class heads,
release reset, malformed lease use and unchanged accounting. Six ownership/
allocator tests passed; the earlier broader local smoke passed 31/31; added
optional-identity tests also passed. Final hosted gates must inspect the final
exact head, including all later test/schema additions.

## Performance control and independent C evidence

**Final collision-stable implementation:** five AB/BA pairs independently pass
worker0 output/trace parity. Median **8.135968 → 8.254257 s (0.9857×)** is roughly
flat amid host variance, about 1.5% higher wall time. No speedup is claimed for
the final implementation. This fixed workload does not measure complete compiler
throughput. Program objects are reused only because their compiler/core inputs
remain unchanged; the final runtime was independently regenerated. Exact samples,
CPU/RSS caveats and source hashes:
[owned-whole-final-105.json](../evidence/2026-10-31/owned-whole-final-105.json).


**Historical development timing, before the collision correction:** five matched
AB/BA pairs of the unchanged integer worker0 oracle compare the
whole direct-map candidate compiler-core/lowering/runtime path with `a6472b1`: median
**8.857851 → 7.855453 seconds (1.1276×)**. Every output matches the independent
oracle. This is **one UIR workload, not full source-compiler throughput**. A
separate same-assembly runtime-only control is near-flat, about 1.05× amid host
variance; do not generalize that small difference or multiply either result by
the earlier PR #100 5.4414× result. Exact raw samples and hashes:
[whole candidate](../evidence/2026-10-31/owned-whole-candidate-105.json),
[runtime-only control](../evidence/2026-10-31/owned-runtime-only-105.json).

A refreshed independent current-C-path physical study passed **20/20** samples
(control/dense8/dense32/dense128). Whole C-managed heap peaks are
0 / 9,519,390 / 9,605,726 / 10,074,828 B. These include bootstrap/runtime storage,
are **not** individual UIR owner capacities, and must not be called a per-owner
improvement over the older PR #103 samples. Its C-relevant inputs stayed unchanged
during the subsequent owned-only allocator tuning. See
[u1a-c-heap-105.json](../evidence/2026-10-31/u1a-c-heap-105.json).

## Remaining release gates and optimization backlog

Run one final four-platform full CI plus completed-batch `qualification`, without
experimental owned compiler full self-build. Inspect every failure, exact head
and tested/merged tree equality before merging or closing #77. Keep handover,
issue disposition and PR description consistent with actual results.

Then implement U1b immutable aggregates, followed by U2 managed semantics,
U3 production frontend integration and U4 machine/toolchain migration. Profile
complete compiler phases separately (#51); the worker measurements do not
establish whole-compiler throughput. Preserve bounded work/allocation, independent
oracles and narrow incremental checks at every step.
