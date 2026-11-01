# U1b full-fixture owned-runtime hotspot investigation — 2026-11-01

**Status:** U1b full-fixture phase profiling **PASS**. Four initial private generated-runtime micro-candidates **rejected** (the final 64-entry graph cache was **2.65% slower** across five paired native trials). A **fifth distinct, source-level** narrowly scoped `u1_words.context` optimization eliminating a duplicate pure `budget.poll` for an identical owner **PASSED** one pilot and **five alternating matched owned-native pairs (5/5 lower runtime, 6.24% lower median)** with strict independent C-bootstrap parity. The exact source change was committed to draft PR #106 at `dc756a4ef09166b7faf29a49ce8526cd4933659e` with a focused same/different-owner cancellation/work-credit regression; smoke [41303300082](https://github.com/eristavi/eristavi-lang/actions/runs/41303300082) **PASS**. **Final full four-platform CI/completed-batch qualification PASSED at `0a2ba59472a9571b9f352255c62957594ebacc68`**. Later test/workflow changes at `c2423d5` have a new diagnostic failure; see the current-review addendum below. No claim that this incremental improvement resolved the earlier ~830× C/owned reference disparity or made the reference runtime ready for production. See the follow-up section at the end, which supersedes early four-candidate-only conclusions.

## Governing constraints and architecture

Follow [DESIGN_PHILOSOPHY.md](../../DESIGN_PHILOSOPHY.md) → [LANGUAGE_SEMANTICS.md](../../LANGUAGE_SEMANTICS.md) → [U1 contract](../architecture/Eristavi-UIR-U1-Contract-2026-10-29.md) → implementation. Preserve machine-independent semantics, independently checked canonical SSA and *same-revision malformed/unreachable input rejection*, checked cancellation/resource faults, exactly-once cleanup and **original** modeled owner limits (8 MiB peak / 64 MiB traffic for fixed qualification). The reference execution workload is a complete U1b linked-aggregate fixture, **not** the promoted U3 production compiler, and 32-byte public value ABI stays frozen.

## Independent profile: verified data, not a synthetic extrapolation

**Exact profile run:** [41299296330](https://github.com/eristavi/eristavi-lang/actions/runs/41299296330). Tests: `tests/test_u1b_runtime_hotspot.py` on Linux x86-64 Clang -O2. A private temporary copy of U1b's source puts marker boundaries around canonical seal, repeated ingress revalidation, aggregate engine validation, recursive aggregate execution and engine close. Native Linux CLOCK_MONOTONIC snapshots plus counters instrument the **real** generated owned-runtime assembly, including graph GC, exact graph owner/hash lookups, allocation entries, safe points, slot collections and graph index preparations. The full normal + refusal/cancellation fixture had exact stdout/stderr/exit parity with an independently compiled C bootstrap. Production files unchanged.

| Stage of *instrumented* full fixture | Elapsed wall seconds | Runtime allocator calls | Graph-table finds | GC collections |
| --- | ---: | ---: | ---: | ---: |
| Canonical seal verification | 8.7328 | 179,340,858 | 63,373,654 | 170 |
| Per-run ingress reverification (all attempts) | 21.8376 | 497,492,849 | 175,863,916 | 481 |
| Aggregate engine creation / graph validation | 1.7184 | 48,182,528 | 17,040,075 | 39 |
| Linked recursive aggregate execution | 1.6492 | 22,200,134 | 7,990,198 | 28 |
| Engine close | 0.0010 | 9,985 | 6,825 | 0 |
| Other setup, expected refusals and teardown | 9.4284 | 202,028,351 | 71,665,771 | 313 |
| **All event counters (whole instrumented program)** | **43.9961 observed process wall** | **964,789,930** | **341,449,724** | **1,057** |

Additional totals: **932,256,371** safe-point entries, **232,148** graph allocator creations, **442,049** slot collections, **3,467** graph interior-owner lookup calls, **1,057** index preparations. Measured **GC inclusive time 0.393759852 s**. This GC time overlaps stages; it is **not** additive to stage wall seconds. Stage sums omit startup, observer transitions and final recording. Do not compare the instrumented 43.996 seconds against the independent uninstrumented ~72-second owned time as a candidate speedup: this profiler changes generated code layout and adds hooks.

**Finding:** the largest measured work concentration is repeated ingress verification (~21.84/43.996 instrumented seconds) and canonical verification (~8.73 seconds), accompanied by nearly **one billion** allocator and safe-point entries. Collector execution, at only ~0.394 seconds inclusive on this fixture, does **not** justify weakening safepoint/GC frequency to chase the main slowdown. Direct graph-owner lookup and index preparation counts are also too small to justify changing their algorithms as the first remedy. The measured 341M graph-table finds are genuine but isolating their call overhead is insufficient, as the pilots below show.

## Matched original-owned versus modified-owned micro-optimization pilots and five-pair acceptance

All four used the **same unmodified U1b fixture** and identical generated application assembly (SHA-256 `b91f772f7ac730d8a6e2cb145940d3395fab8e653ee2c44cb6bd4a8a6fb2902a`), the *same owned-runtime generator*, static x86-64 native link, same Clang -O2 CI profile and an independent native C output oracle. Each private generated-assembly rewrite made **one** limited change; original-owned baseline and private modified-owned candidate ran once, in that order, on the **same** runner. The fourth candidate was additionally compared in **five alternating fresh-process baseline/candidate pairs**. All tests had exact stdout/stderr/exit parity. **No production implementation was changed.**

| Isolated private candidate | Run | Original owned | Candidate owned | Candidate / baseline | Result |
| --- | --- | ---: | ---: | ---: | --- |
| Replace pure live-slot accessor call in safe-point with exact readonly counter load | [41299581706](https://github.com/eristavi/eristavi-lang/actions/runs/41299581706) | 73.638889 s | 75.368882 s | 1.02349 | No observed benefit |
| Inline unchanged bucket-hash calculation into graph-find (no change to identity/collisions) | [41299890268](https://github.com/eristavi/eristavi-lang/actions/runs/41299890268) | 74.400055 s | 75.334596 s | 1.01256 | No observed benefit |
| Cache one **positive** exact graph-find pointer; invalidate before graph sweep; all misses use unchanged lookup | [41300216836](https://github.com/eristavi/eristavi-lang/actions/runs/41300216836) | 62.017685 s | 61.946636 s | 0.99885 | Effect negligible |
| 64-entry direct-mapped **positive exact pointer** cache; invalidate entire table before sweep; preserve collision-safe miss fallback | [41300574222](https://github.com/eristavi/eristavi-lang/actions/runs/41300574222) | 75.799777 s | 73.980917 s | 0.97600 | Nominal 2.46% one-pair benefit; **not accepted until five-pair check** |

These are **one-pair exploratory pilots**, not performance qualification. The unmodified baseline ranged from about 62 to 76 seconds across different GitHub runs, illustrating cross-runner noise. The fourth pilot's nominal 2.46% improvement was too small to promote from one run, so it was independently rechecked with the exact requested paired protocol.

### Final five paired same-source native runtime comparison — PASS correctness, FAIL performance

**GitHub run:** [41300912191](https://github.com/eristavi/eristavi-lang/actions/runs/41300912191), job `124831431271`, head `5095de3ef115d13b213f121387f1575d5a321386`. Test `tests/test_u1b_owned_runtime_benchmark.py`; private `positive_table` candidate only. One unchanged fixture SHA-256 `b5a03a861efa494fbfd55e5a2440d34f6e522cf8f2f3b45f8a916cda56725993`, unchanged emitted application SHA-256 `b91f772f7ac730d8a6e2cb145940d3395fab8e653ee2c44cb6bd4a8a6fb2902a`, original generated runtime SHA-256 `dad392a24099e22d4d79090f34bbdaf5cd1ff08a50c5e93be493efafc40cad49`. Candidate generated runtime assembly SHA-256 `beb7c3da272d9ebc2508102aff39762f2103c2e6a249b09af7a862f6441b1cf3`. This is a within-owned-runtime comparison, not the old C/owned ~830x cross-runtime reference.

| Pair | Execution order | Original owned-native (seconds) | 64-line cache candidate (seconds) |
| ---: | --- | ---: | ---: |
| 1 | baseline → candidate | 62.335277 | 63.213191 |
| 2 | candidate → baseline | 60.891708 | 63.893320 |
| 3 | baseline → candidate | 62.051454 | 60.584959 |
| 4 | candidate → baseline | 63.894544 | 63.698386 |
| 5 | baseline → candidate | 61.368971 | 63.890124 |
| **Median** | **AB/BA/AB/BA/AB** | **62.051454** | **63.698386** |

**All 10 native executions passed the exact independent C-bootstrap stdout, stderr, and exit-status parity gate**, including the full normal/refusal/cancellation workload. The candidate-to-original ratio of medians was **1.02654139×** (candidate 2.654% **slower**, not a speedup). Raw samples, file hashes, workflow links, profile records and pilot results are persisted in [machine-readable evidence](../evidence/2026-11-01/u1b-owned-runtime-hotspot-pilots.json).

**Decision: REJECT and do not promote this fourth bounded cache.** Despite its GC-sweep invalidation, it is not independently qualified for forced-collision, allocation refusal, reclamation and stale-object stress; its measured performance also fails the optimization gate. No private assembly cache or other candidate has been added to the production runtime. No new full four-platform CI is justified for a non-production candidate rejected after focused parity and paired measurements.

## Initial micro-candidate decision (historical, superseded by later word-store follow-up)

1. **Stop low-benefit runtime graph lookup micro-optimizations**: three initial one-pair pilots and one **five-pair rejection** demonstrated no defensible latency gain. Keep the production runtime unchanged.
2. **Attribute boxed scalar value and word-store costs at the *actual verifier hotspots*** before designing the next candidate. In particular inspect high-frequency `erist_rt_value_new`, `erist_rt_alloc`/free-list handling and the U1 radix-16 `u1_words.get` accesses. Distinguish verifier structural visits from runtime slot allocations/GC work, and avoid blaming GC for general verifier churn.
3. A potential *bounded* architectural remedy is backend-private scalar intermediate unboxing or fused checked word access with the **same** location/error ordering, strict independent validation (including forged same-revision dead records), resource work/poll charges, ownership accounting and 32-byte ABI at public edges. **Proposal only**, no optimization code written or acceptance assumed. Do not attach a mutable cache to an untrusted canonical IR word store without mutation/invalidation proof.
4. Before any future production implementation, select a reproducible matched completed workload and an isolated, correctness-preserving prototype. Only a promising pilot justifies the required five paired native baseline/candidate repetitions (alternate order, raw samples, medians/spread) plus cancellation, allocator fault, GC, collision, malformed IR, memory-budget and independent-oracle regressions.
5. PR #106 remains a fully correctness/build-qualified **U1b reference** slice, but its extensive owned runtime cost remains an openly tracked integration/optimization risk. Do not call these rejected micro-pilots an improvement. Do not silently promote or merge on the assumption that the 830× cross-runtime disparity disappeared. Reuse previously successful final CI only while relevant code/toolchain inputs remain identical; experimental owned full self-build is still excluded.

**Disposition:** step 1 (phase/event profile) **COMPLETE**; step 2 (four bounded private optimization candidates) **TESTED AND REJECTED**; step 3 (four parity-checked one-pair pilots **PLUS full five-pair matched comparison** of fourth candidate) **COMPLETE**. The five-pair test passes correctness but finds the 64-entry candidate slower. No production optimization shipped, ABI/semantics/budgets unchanged. The remaining structural verifier and boxed-allocation performance debt is tracked in #51.


## Follow-up: verified same-owner word-store poll reduction — source promoted to PR, final matrix pending

The preceding four **generated-runtime cache/hash/safe-point** experiments were correctly rejected; that does not rule out an independent **source-level** cost removal in the actual verifier path. Source inspection found that `src/compiler/u1_words.eri`'s `context(words, phase, write)` performed `budget.poll(words.owner)` followed unconditionally by `budget.poll(phase.owner)` for every get/set/push. The actual budget API defines `poll(owner) { try active(owner); }`; `active` checks the current owner/root state, producing its existing checked cancellation/invalid-state failure without changing work, memory, traffic or ownership. Repeating this check immediately on the same owner is redundant in the current synchronous U1 reference execution. For *distinct* owner identities, both checks must remain in the original order so canceled cross-owner phases are detected before same-revision/foreign-store validation.

### Exact bounded source change

At committed source revision [`dc756a4`](https://github.com/eristavi/eristavi-lang/commit/dc756a4ef09166b7faf29a49ce8526cd4933659e), the only `u1_words.context` change was:

```eri
try budget.poll(words.owner);
if words.owner != phase.owner { try budget.poll(phase.owner); }
```

Previously the second poll was unconditional; no `budget.work`, modeled reserve/traffic, word path, immutable verification logic, traps/failure categories or ABI boundary was removed. In particular, unlike a mutable page cache, this change **never substitutes stale word data** for current canonical records. It does not bypass any fresh structural verification, including same-revision malformed dead code. No scalar public ABI or GC policy changed. This is an internal U1 adapter source optimization, not a new syntax or public configuration switch.

### Five paired owned-native original/candidate native runs

**Pilot** [41302328469](https://github.com/eristavi/eristavi-lang/actions/runs/41302328469) **PASS** C-bootstrap exact stdout/stderr/exit parity: original-owned **45.215022287s**, private source-overlay optimized-owned **43.296282773s**, nominal **4.24%** faster (one pair, not sufficient to claim speedup). Two test-harness-only failures before the pilot were an output filename collision with the temporary baseline directory; corrected without touching semantics or production sources. A malformed YAML job display title temporarily prevented a five-pair workflow from starting; it was corrected and the test ran. These harness failures were not compiler defects.

**Full same-runner five-pair** [41302564199](https://github.com/eristavi/eristavi-lang/actions/runs/41302564199), job `124836367268` **PASS all ten exact independent C-bootstrap stdout, stderr and exit comparisons**; pairs were alternated **AB/BA/AB/BA/AB**, with the **same original generated owned runtime** and one unmodified linked fixture on Linux x86-64 Clang -O2:

| Pair | Order | Original owned (s) | Same-owner poll optimized owned (s) | Pair runtime saved |
| ---: | --- | ---: | ---: | ---: |
| 1 | original → candidate | 43.954859 | 41.212584 | 6.24% |
| 2 | candidate → original | 44.134367 | 41.205843 | 6.64% |
| 3 | original → candidate | 44.815934 | 43.401338 | 3.16% |
| 4 | candidate → original | 41.820128 | 40.660818 | 2.77% |
| 5 | original → candidate | 43.392423 | 41.575663 | 4.19% |
| **Median** | **5 pairs** | **43.954859** | **41.212584** | **6.24% lower median** |

Candidate/baseline **ratio of medians = 0.937611572**; corresponding runtime-speed factor **1.06654×**. All five individual pairs favored the candidate. This is genuine *within-owned-runtime* before/after comparison; not the older ~830× *C bootstrap vs owned* cross-runtime observation. Single workload, one platform and hosted-runner timing noise still limit generality. Raw exact timings, candidate/original module and application assembly hashes, generator hash, model scope and negative verification are preserved in [`docs/evidence/2026-11-01/u1b-words-owner-poll-five-pair.json`](../evidence/2026-11-01/u1b-words-owner-poll-five-pair.json).

**Regression gates:** new no-extra-output `wordOwnerPollContracts()` in `tests/fixtures/u1_foundation.eri` verifies same-owner word reads consume **7** work units (unchanged), legal shared metadata reads from another function owner, denied function-store reads from a foreign phase, cancellation detection for both equal and different owners, exactly-once close and zero live/pending owner charges. Focused smoke [41303300082](https://github.com/eristavi/eristavi-lang/actions/runs/41303300082) passed on the production source patch + regression revision. The test-only original-versus-candidate benchmark was changed to reconstruct the **pre-optimization baseline** even when the checked-out current module is optimized, so future manual reproductions remain meaningful. Expensive five-pair benchmark workflow is now manual `workflow_dispatch` only.

**Next required gate:** because this changes `src/compiler/u1_words.eri`, the scoped fast smoke is **not a merge qualification**. Run once the final source + tests + evidence + handover are stable: full four-platform CI (GCC/Clang x86-64, ARM64 Clang and macOS Clang) **plus full completed-batch bootstrap repeatability/offline and owned integration**. Keep experimental owned compiler full self-build excluded. Validate the exact head, record any platform skips and final code SHA; do not claim PASS before workflows finish. If green, accept this **bounded improvement only**, while maintaining #51 for deeper boxed scalar allocation/verifier optimization; PR #106 remains draft until the remaining reference-only performance risk receives explicit disposition.

## Current review: qualified source, later profiler failure and next plan

On 1 November 2026 the exact source/test/workflow head `0a2ba59472a9571b9f352255c62957594ebacc68` was independently confirmed successful in [full CI 41303717634](https://github.com/eristavi/eristavi-lang/actions/runs/41303717634) and [qualification 41303717596](https://github.com/eristavi/eristavi-lang/actions/runs/41303717596). Earlier final-matrix-pending statements in this report are historical. All four platform tests and required bootstrap/offline/owned-integration jobs passed; experimental full owned compiler self-build remained skipped.

A later comparison to current PR head `c2423d5b6211c4999a116e541fb11c67dfa2357d` changes HANDOVER.md, the hotspot diagnostic test and ci.yml, not compiler/runtime source. [Run 41307434281](https://github.com/eristavi/eristavi-lang/actions/runs/41307434281) passed smoke but failed the new profiler reconciliation: decode() removes `gc_time_ns` while deriving seconds, then the assertion sums missing nanosecond keys as zero (`0 != 545628495`). This diagnostic requires raw-unit reconciliation repair; the assertion must remain meaningful. A later branch-specific automatic profiler selector also needs reconciliation with manual-only expensive profiling policy.

The [ordered optimization plan](U1B_OPTIMIZATION_PLAN_2026-11-01.md) starts with that measurement repair and one fresh current-source attribution run, then one bounded checked record-read pilot if supported; backend-private scalar unboxing needs a separate proof and batch. Keep fresh malformed/same-revision/dead/uncalled IR verification, fault/owner/work/cancellation semantics and unchanged budgets. Current compiler-source qualification is retained at its exact revision; later diagnostics are not described as green. No implementation, new benchmark or merge was performed during this plan review. HANDOVER §73 is the newest recovery checkpoint.
