# U1b full-fixture owned-runtime hotspot investigation — 2026-11-01

**Status:** Diagnostic profiling **PASS**. Four isolated runtime micro-optimization pilots **PASS output parity**; the fourth, 64-entry exact positive-pointer lookup cache showed a small positive one-pair pilot, but its completed **five alternating matched pairs** were **ALL PARITY PASS** and **2.65% SLOWER** at the candidate median. All four private candidates **REJECTED / NOT PROMOTED**. No production compiler, runtime, UIR algorithm, GC policy, ABI, quota, test oracle or source semantics was changed during this investigation. PR [#106](https://github.com/eristavi/eristavi-lang/pull/106) remains draft pending explicit reference-runtime performance-risk disposition. [Issue #51](https://github.com/eristavi/eristavi-lang/issues/51) tracks deeper performance work.

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

## Next engineering decision

1. **Stop low-benefit runtime graph lookup micro-optimizations**: three initial one-pair pilots and one **five-pair rejection** demonstrated no defensible latency gain. Keep the production runtime unchanged.
2. **Attribute boxed scalar value and word-store costs at the *actual verifier hotspots*** before designing the next candidate. In particular inspect high-frequency `erist_rt_value_new`, `erist_rt_alloc`/free-list handling and the U1 radix-16 `u1_words.get` accesses. Distinguish verifier structural visits from runtime slot allocations/GC work, and avoid blaming GC for general verifier churn.
3. A potential *bounded* architectural remedy is backend-private scalar intermediate unboxing or fused checked word access with the **same** location/error ordering, strict independent validation (including forged same-revision dead records), resource work/poll charges, ownership accounting and 32-byte ABI at public edges. **Proposal only**, no optimization code written or acceptance assumed. Do not attach a mutable cache to an untrusted canonical IR word store without mutation/invalidation proof.
4. Before any future production implementation, select a reproducible matched completed workload and an isolated, correctness-preserving prototype. Only a promising pilot justifies the required five paired native baseline/candidate repetitions (alternate order, raw samples, medians/spread) plus cancellation, allocator fault, GC, collision, malformed IR, memory-budget and independent-oracle regressions.
5. PR #106 remains a fully correctness/build-qualified **U1b reference** slice, but its extensive owned runtime cost remains an openly tracked integration/optimization risk. Do not call these rejected micro-pilots an improvement. Do not silently promote or merge on the assumption that the 830× cross-runtime disparity disappeared. Reuse previously successful final CI only while relevant code/toolchain inputs remain identical; experimental owned full self-build is still excluded.

**Disposition:** step 1 (phase/event profile) **COMPLETE**; step 2 (four bounded private optimization candidates) **TESTED AND REJECTED**; step 3 (four parity-checked one-pair pilots **PLUS full five-pair matched comparison** of fourth candidate) **COMPLETE**. The five-pair test passes correctness but finds the 64-entry candidate slower. No production optimization shipped, ABI/semantics/budgets unchanged. The remaining structural verifier and boxed-allocation performance debt is tracked in #51.
