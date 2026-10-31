# Owned runtime optimization: production implementation and acceptance

Checkpoint: 2026-10-31. [PR #99](https://github.com/eristavi/eristavi-lang/pull/99) implements the three high-priority optimizations from [the owned-runtime investigation](OWNED_RUNTIME_INVESTIGATION_2026-10-31.md). Unlike the 5.42x *disposable diagnostic prototype*, this is an **actual source change** in the owned x86-64 runtime. It does **not** change Eristavi source syntax, the old production frontend, imported contracts, native C runtime, or the ABI.

## Design

1. **GC admission on new managed allocation pressure.** Successful graph, saved failure and Text record allocations increment saturated allocation count and estimated allocated byte counters. For graph-enabled profiles, safe-point GC is due when fresh allocation count reaches a retained-heap-scaled threshold with a 128 minimum and 4096 ceiling, allocated bytes reach 8 MiB, or a dirty heap has gone through 1,048,576 safe points. A collection resets counters and recalculates the count budget. Explicit forced GC and all original faults remain available. A dirty heap with nonzero Text allocation pressure is recognized without making the Text-only profile collect earlier than before. **The 8 MiB is a collection-pressure trigger, not a hard global live-heap byte cap.** A fixed 16x timing multiplier is not shipped.
2. **Exact-slot root deduplication.** Before graph marking, construct a *non-owning* exact-address hash for up to 4096 active value slots in a static 64 KiB table. Values are still traced through the original slot loop. Only class-1 roots **exactly matching** a slot address skip the redundant interior-object owner search. Genuine interior keys, foreign/nonsense pointers, saved failures and protected values keep the existing checked path. On larger active slot sets the original conservative path is used; no speculative dereference of arbitrary machine words.
3. **Reusable bounded slot-index scratch.** The slot-pruning and checked-unwind index share a static 64 KiB table, cleared on every checkout; a busy or oversized operation retains the original separate-reservation fallback, including the no-allocation linear search on reservation refusal. There is no unbounded workspace growth, root-map key reuse or public ABI impact. Two additional 64 KiB BSS ranges (exact roots + scratch) must be reported in total memory accounting; neither is a physical RSS speedup measurement.

## Correctness and regression coverage

- [Focused CI 41195818485](https://github.com/eristavi/eristavi-lang/actions/runs/41195818485) passed **27/27** selected tests on the integrated code revision `7d7719d84cb40a13d4e22692f3cc5d266f2a5138`. All original independent U1a integer/SSA/diagnostic tests, C- and owned-runtime parity, native-lifetime and strict Float cases were retained.
- New probes check 200,000 retained graph objects and byte/count/polling thresholds; true interior roots versus duplicate exact slots; a >4096-slot conservative fallback; reuse zeroing and ownership, nested dynamic scratch checkout, oversized fallback and deliberate reservation refusal; exact UTF-8 Text results and unchanged root cleanup; failure publication/OOM semantics.
- Intermediate [CI 41195636306](https://github.com/eristavi/eristavi-lang/actions/runs/41195636306) found one *incorrect new test expected count*: oversize fallback rechecks two duplicate roots **plus one genuine interior** (three owner calls). That test oracle was corrected without changing runtime code; the later integrated 27-test smoke passed.
- Native compiler output, ABI, fallback and independent oracle behavior remain subject to the unmodified **full suite**, not merely these smoke tests.

## Performance measurements: keep each scope honest

The baseline research appendix [owned-runtime-profile-evidence.md](../evidence/2026-10-31/owned-runtime-profile-evidence.md) showed 244.9 s → 57.3 s for eight workers, and five-pair worker0 37.617 s → 6.943 s, **on a disposable assembly prototype**, not on this patch. It is evidence of possible benefit, *not* a qualified speedup or a future CI duration guarantee. The checked-in policy eliminates repeated GC caused solely by scalar safe points; the exact-root and scratch tests check redundant work and correct storage ownership. Fresh same-host before/after **production-patch timing, CPU, collection count, allocator mapping activity and attributable physical RSS** must be measured before advertising a speedup. A target-specific CI timing report alone must not be divided against the baseline research host's timings.

## Full-CI acceptance adjustment

First full CI [41196060338](https://github.com/eristavi/eristavi-lang/actions/runs/41196060338)
on preliminary final head `5224cfbb464a399d0fb2c8881462d7ce2e1c6b3c` exposed
a stale instruction-level test expectation in the **original integer-owned
checked-unwind fallback fixture**. It asserted a direct
`call erist_rt_reserve` at `.Lunwind_index_allocate`, whereas the new
bounded scratch checkout intentionally provides `call .Lslots_scratch_acquire`.
The fixture was updated to force a failed checkout through that new
wrapper (zero pointer and size), retaining all original checked-unwind
success, failure, slot/lifetime and native C-versus-owned output oracles.
No runtime code or watchdog was changed to address this test failure.
The first full run **did not qualify** PR #99, despite other successful
jobs. The corrected head `fd4828e63826d0fc36f827a938b437f3dd863c3c` subsequently passed
[full four-platform CI 41196975098](https://github.com/eristavi/eristavi-lang/actions/runs/41196975098)
and [owned-integration qualification 41196975251](https://github.com/eristavi/eristavi-lang/actions/runs/41196975251),
with the experimental owned compiler self-build intentionally excluded.
[PR #99](https://github.com/eristavi/eristavi-lang/pull/99) was formally
**MERGED** at `388bfb6da42a6c0c1de307a0aa72ea987b63bbb0`, with identical tested/merged source
tree `aac54d7534168879e585e9c8045e1c762098dea0`.

The first Clang full run's owned integer test elapsed 59.879 s vs
257.767 s in the previous PR #98 CI job, while the verifier/oracle test
elapsed 38.588 s vs 133.107 s. These are comparable test names and
runner/compiler *classes* but **not** controlled, same-host paired executions.
They are *indicative regression signals*, not a peer-reviewed speedup claim.

## Final merged checkpoint and performance comparison

Commit `fd4828e63826d0fc36f827a938b437f3dd863c3c` is the exact **QUALIFIED** code version. Its
merge `388bfb6da42a6c0c1de307a0aa72ea987b63bbb0` contains identical source tree `aac54d7534168879e585e9c8045e1c762098dea0`.
The complete x86-64 Linux suites discovered 460 tests per compiler; Linux
ARM64 and macOS Clang also passed the full platform suites. No source language,
frontend, ABI or independent reference oracle was removed.

**CI timing cross-run observations, not controlled same-host trials:**
- Linux Clang full: qualified PR #98 759.939 seconds → PR #99 267.372 seconds;
  integer executor 257.767 → 40.839; verifier/oracle 133.107 → 26.638.
- Linux GCC full: qualified PR #98 824.042 seconds → PR #99 500.283 seconds;
  integer executor 266.345 → 75.874; verifier/oracle 139.684 → 41.181.

Because runners, load, caches and other conditions are not an identically
controlled AB/BA experiment, these timings establish an **encouraging CI
regression/efficiency signal**, not an exact speedup attributable solely
to the three optimizations. The five matched research pairs still used
a disposable prototype, not the production patch. Paired production
measurements, physical RSS/heap attribution (including the additional
128 KiB static BSS) and new GC counters remain highest priority.

## Known limits and follow-up gates

- The static exact-root cap forces conservative fallback with large live slot sets. Resource ceilings and cancellation remain unchanged.
- GC byte pressure is estimated from committed record/backing capacity and separately saturates; allocator metadata, full managed graph reachability, peaks and OS overhead are not represented. Live heap hard cap, true collector/GC physical root attribution and whole source→native comparison are separate policy decisions.
- Full forced tiny-memory/OOМ, recycled-address interior collisions, protected temporaries, Text/views/identity/List alias, nested cleanup and deterministic resource semantics must remain valid under the complete suite. No test or watchdog is deleted.
- **Release gate for x86-64 owned-runtime-only code:** **PASSED** exact-head four-platform full CI and owned integration qualification; the tested code Git tree matches the merge exactly. See [CI_QUALIFICATION.md](../../CI_QUALIFICATION.md). Experimental owned compiler full self-build and unnecessary repeated bootstrap self-builds were not selected.

Optimization-first development is a permanent direction in [HANDOVER.md](../../HANDOVER.md): prioritize measured runtime/compiler bottlenecks and bounded efficiency while keeping correctness, compatibility and safe failures non-negotiable.
