# Eristavi UIR U0 — initial baseline and implementation gates

Date: 2026-10-29
Status: Initial U0 observations and archived evidence remain unchanged. PR #58/#59/#60 are merged; final PR CI and completed-batch bootstrap repeatability/owned-integration qualification passed. Direct-IR modeled-capacity results remain distinct from original U0 source-pipeline measurements, complete physical-memory accounting and larger owned-runtime performance qualification.

## Outcome

Measured the unchanged pinned compiler on 12 source workloads, five fresh-process samples each, and executed all 12 generated Linux x86-64 applications against independent expected output. All matched. UIR/assembly hashes were stable over all five samples of each workload.

Separately measured the existing native Eristavi Universal verifier on one identical emitted assembly program linked with two runtimes, three widths, five paired samples per width. Every run completed and printed the expected eight completed verifications. This is a baseline, not a new-UIR speedup or proof of a particular bottleneck.

## Provenance and protocol

- Repository: eristavi/eristavi-lang at 8af0ffe3350c737550c3ab0e6c3fa89f60f6f091. All 342 files rehashed against GitHub Git-blob identities: zero mismatches; 2,771,268 source bytes.
- Host: Linux-6.18.55-x86_64-with-glibc2.39; CPU: INTEL(R) XEON(R) PLATINUM 8573C; 9 reported logical CPUs. Shared execution environment, not an isolated benchmark machine.
- Python: 3.12.14 (main, Aug 25 2026, 14:00:49) [Clang 22.1.3 ]; pinned regex 2026.9.29 and unicodedata2 17.0.0 installed into an isolated measurement directory. Unicode data reports 17.0.0.
- Toolchain: GCC 13.3.0; GNU assembler/linker 2.42. C-bootstrap seed built from the unchanged frontend with -std=c11 -O1; verifier assembly emitted by that seed.
- Source pipeline: Python bootstrap direct x86-64 backend; same fresh process loads the compiler, lowers the fixture, then emits assembly. The reported pipeline timer starts after imports and ends before report formatting. Stage wrappers call original functions unchanged; nested times use exclusive accounting.
- Native verifier: same assembly in both profiles. Bootstrap C runtime built with -std=c11 -O2 -DERIST_NATIVE_RUNTIME -DERIST_HEAP_GC_INTERVAL=65536. Owned runtime emitted from unchanged src/owned_runtime.eri using the Python reference interpreter, assembled and linked as static ELF.
- Owned executable audit: no INTERP or DYNAMIC segment; no undefined symbols; non-executable GNU_STACK.
- Fresh process for every sample, PYTHONHASHSEED=0, warm filesystem/page cache, no artifact cache and no cache flushing. Workload order reverses between pipeline rounds; bootstrap/owned order alternates between paired native rounds. No simultaneous benchmark jobs were run.
- These are five-sample descriptive measurements. Medians and min/max ranges are not confidence intervals. A new candidate must be measured against the same pinned baseline again in paired runs; comparison with a historical median alone is insufficient.

## Bootstrap source-to-assembly baseline

| Fixture | Median pipeline ms | Min–max ms | Median backend ms | Blocks | Instructions | Values |
|---|---:|---:|---:|---:|---:|---:|
| diamond_8 | 8.130 | 6.912–14.664 | 2.609 | 5 | 102 | 76 |
| diamond_32 | 23.661 | 19.752–37.172 | 7.349 | 5 | 390 | 292 |
| diamond_128 | 76.488 | 62.106–78.225 | 24.156 | 5 | 1542 | 1156 |
| loop_8 | 6.055 | 5.874–6.700 | 2.279 | 5 | 74 | 55 |
| loop_32 | 16.696 | 13.897–21.445 | 5.381 | 5 | 266 | 199 |
| loop_128 | 57.231 | 48.098–75.258 | 21.920 | 5 | 1034 | 775 |
| calls_8 | 5.016 | 4.586–7.110 | 1.711 | 2 | 31 | 21 |
| calls_32 | 9.097 | 7.467–10.419 | 2.429 | 2 | 103 | 69 |
| calls_128 | 25.626 | 19.738–31.985 | 5.917 | 2 | 391 | 261 |
| cfg_8 | 9.267 | 6.903–10.246 | 3.362 | 26 | 81 | 62 |
| cfg_32 | 23.384 | 17.792–30.265 | 9.521 | 98 | 297 | 230 |
| cfg_128 | 77.754 | 63.963–220.999 | 34.745 | 386 | 1161 | 902 |

Diamond and loop workloads vary live mutable-local width at 8/32/128 with a small CFG. Call workloads vary a sequence of direct calls at the same sizes. CFG workloads instead hold one updated local and vary sequential diamonds at 8/32/128, yielding 26/98/386 blocks. This separates local width from CFG size; it is not coverage of every graph family.

Instructions count nonterminator Universal operations; values are the existing model's declared value_count totals; edges retain duplicate-target edges. These are legacy representation counts, not new SSA instruction counts. Source, UIR, and assembly digests and operation histograms are in the evidence archive.

Fresh-process bootstrap peak RSS was approximately 101 MiB across these small fixtures and is dominated by compiler/import overhead. It does not measure bytes per UIR node or prove that the new representation saves memory. Per-function buffers/scratch need explicit allocation counters in U1a.

## Native verifier baseline: construction plus eight verifications

| Runtime | Width | Median CPU ms | CPU min–max ms | Median peak RSS MiB |
|---|---:|---:|---:|---:|
| bootstrap | 128 | 160.523 | 77.091–202.569 | 9.051 |
| bootstrap | 512 | 334.069 | 305.296–712.583 | 10.301 |
| bootstrap | 2000 | 1437.309 | 1200.123–1955.823 | 24.590 |
| owned | 128 | 938.546 | 800.456–986.455 | 1.277 |
| owned | 512 | 3052.569 | 2747.375–4093.969 | 2.402 |
| owned | 2000 | 16558.523 | 14227.516–19119.960 | 7.027 |

At width 2,000 the owned-runtime median CPU time was 11.52 times the bootstrap-runtime result, while peak resident memory was lower. The runtime choice and fixed configuration are the changed inputs in this comparison; both execute the same emitted assembly. This finding is specific to this workload and is not a statement about general Eristavi performance.

The probe uses the existing wide() fixture with 16 following chain blocks and eight verification rounds. Its elapsed CPU includes program/graph construction, argument handling, verification, reporting, and runtime overhead. Do not divide by eight and label the result isolated verifier time, attribute the difference to SSA, or blame a particular allocator/collector function without an additional phase/counter experiment.

The compiler seed is a C-bootstrap executable; the owned executable here is the verifier application, not an owned-runtime compiler performing a self-build. No B→C attempt, 900-second run, full qualification, or CI dispatch occurred.

## Memory measurement correction

Initial child wait4/ru_maxrss measurements could include resident memory inherited from the Python launching process. A control using /bin/true reported 8,448 KiB with a small parent and 106,880 KiB after the parent allocated 96 MiB. Those raw measurements must not become compiler memory budgets.

The authoritative native batch uses a small native launcher that execs, then forks/execs the target and records that target's wait4 usage. The same control reports 384 KiB in both parent-memory conditions. The launcher passes through stdout/stderr and the target result; it does not alter the measured program or runtime. Five complete paired samples were collected with this corrected method.

Linux /proc executable links are restricted in this environment, so attempted post-exec sampling was not used as authoritative native memory evidence. native-corrected-summary.json and native-corrected-samples.json are authoritative. Earlier native-summary.json and initial-launch-rss-pass observations are retained only for audit. Bootstrap workers also record their own post-exec /proc/self/status high-water mark; small native application RSS is intentionally left unavailable when sampling missed it.

## U1a structural acceptance gates

These gates apply to these fixed fixtures at canonical publication immediately after mandatory promotion and trivial-parameter cleanup, before optional CFG/constant transformations. They are expectations derived from the fixture semantics, not measured new-IR results or new limits on user programs.

| Fixture family | Sizes N | Remaining cells | Required inserted merge parameters | Required inserted merge-edge arguments |
|---|---|---:|---:|---:|
| Diamond locals | 8, 32, 128 | 0 | N at the join | 2N |
| Loop locals plus index | 8, 32, 128 | 0 | N+1 at the loop header | 2(N+1) |
| Sequential calls | 8, 32, 128 | 0 | 0 | 0 |
| Sequential CFG diamonds | 8, 32, 128 | 0 | N total, one per join | 2N |

Function entry parameters and ordinary call arguments are not counted as inserted merge parameters/edge arguments. Dominating immutable values need no redundant pass-through parameters. Evaluation order, checked arithmetic, simultaneous arguments, and runtime fault origins remain mandatory correctness gates.

For each function, record B blocks, E edges, C candidate cells, N scanned instruction/operand/result entries, frontier work F, inserted parameters P, and inserted arguments G. Reject duplicate liveness/placement processing of the same marked state; at most C*B distinct live-in states and C*B placement pairs exist, with at most C*E liveness predecessor visits under the specified worklist. Frontier construction is separately budgeted; these bounds do not justify repeatedly rescanning the whole function per state. Track actual allocated capacities as well as logical counts.

Proposed initial workload ceiling for qualification fixtures: include all 386-block/128-local source cases above and the width-2,000/16-chain native verifier shape in the comparison set. This is a minimum stress envelope to support, not a production maximum or a claim the frontend compiler itself fits it.

## Timing/capacity limitations and subsequent decision

The observed CPU spread is too large to support a narrow 5% regression verdict. For example, the corrected bootstrap width-128 native samples span about 77–203 ms, and owned width-2,000 about 14.23–19.12 s. Repeated measurements cannot turn that into an isolated, low-noise host result. Report this limitation rather than picking a convenient median.

The initial recommendation was to select exact structural/work gates and define matched candidate fixtures and allocation accounting before the rewrite. That selection is now specified in U1 contract section 15 and the machine-readable budget policy: 8 MiB peak/64 MiB allocation traffic per fixed qualification function lifecycle; 64 MiB/256 MiB development ceilings per function; 512 MiB peak for all UIR-owned request state; explicit visit/count gates; and qualification watchdogs of 60 CPU/120 wall seconds. These are deliberately selected engineering policies. They are not derived from the old process RSS or evidence that a new candidate meets them. Comparative timing remains informational for U1a because matched adapters and a low-noise timing result do not yet exist.

The legacy verifier accepts a mutable-register representation and performs weaker/different checks than the new contract, so its milliseconds are not automatically a fair hard cap for independent SSA verification. In particular, the historical wide() probe observes selected initialized values, while the new initialized-diamond/checksum stress recipe initializes and observes every local. A future timing pair must use the same new recipe on both adapters and fresh measurements.

Do not set a numeric wall-time or memory limit merely to make the new candidate pass. The U1a policies were selected before candidate implementation and close budget selection, not validation. The isolated PR #58 foundation was added after this baseline; it changes none of these observations. U0 is complete for this initial scalar/control-flow evidence batch, not for the entire later UIR architecture.

Still unmeasured: f64 boundary/FP-environment behavior in this batch; native sparse switches (legacy UIR has no equivalent switch); new SSA dominance/frontier/promotion costs; malformed-IR/source-location preservation after new passes; managed/resource cleanup expansion and repeated cleanup failures; generic artifact/cache migration; RevaSM argument threading; end-to-end owned compiler build behavior. These remain explicit U1/U2/U4 integration gates. Existing historical qualification is not rerun or relabeled as new evidence.

## Decisions recorded and next work

The agreed U1 sequence is scalar pred/i64/strict-f64 plus CFG/calls/guards/locations/verification/promotion first (U1a), then other integer widths and immutable aggregates (U1b). Standalone runtime defects terminate without cleanup; normal returns and checked failures retain required cleanup. This creates no promise of file flushing, durable writes, or persistent-lock release.

Foundation PR #58 remains merged as 6fb8b7bcd49418f398810ef9166acc888a35c4f5. [PR #59](https://github.com/eristavi/eristavi-lang/pull/59) merged as 8a2af1c95c0878a65aebbabb464ad1bf6c66db5e, including the C-bootstrap recovery fix. [PR #60](https://github.com/eristavi/eristavi-lang/pull/60) merged as cd421d859e3372796e59ddf236944efc1b6aaddb. Main's implementation tree equals tested tree c6a554e04c12d26c93650956709c5d57f1812ddf (promotion head 22b36c1de42a6bb1b6d54d03a9c69b7c49062082). Scalar-cell promotion, independent construction/canonical checks and transactional cleanup are implemented; production frontend/native integration remains separate. The full handover is [HANDOVER.md on GitHub](https://github.com/eristavi/eristavi-lang/blob/63297369fb7c41e9f13915f6102490f41ee9626a/HANDOVER.md), published in open documentation PR #61.

On 2026-10-30 the ten-test U1 focused batch passed, including both native runtime profiles and the 91-graph dominance oracle. Promotion independently compares 18 before/after IR pairs over 88 inputs, including complete guard/fault/location traces. Final GCC and Clang 18 -O2 differential/transactional checks pass, including eight negative cases and late-output failure/cancellation. Diamond, bounded-loop and sequential-diamond fixtures at N=8/32/128 meet their exact inserted-parameter/argument counts with eight additional verifications and unchanged modeled 8 MiB/64 MiB limits. The largest sequential case records 8,206,560 peak modeled bytes, 19,524,768 successful-allocation traffic bytes and 3,367,442 promotion-work units. These direct-IR fixtures are not the original source U0 workloads or a speedup benchmark. Per-case/source evidence lives in the repository's UIR_U1A_PROMOTION_EVIDENCE.json; original baseline measurements/archive are untouched. Both PR heads passed all four CI configurations. [Completed-batch qualification 41018345033](https://github.com/eristavi/eristavi-lang/actions/runs/41018345033) passed three bootstrap repeatability gates (C/D completed, offline audit successful, unchanged sources) and owned integration (repeatable=false, no C/D self-build, successful offline audit, unchanged sources). The separate full owned-self-build profile was intentionally skipped. Post-merge main CI was automatically triggered; this is separate from the completed pre-merge checks.

Mandatory scalar-cell promotion is implemented for the existing pred/i64/f64 construction profile; full U1a is not complete. Next are remaining scalar operations, calls/switches and strict Float execution, followed by source maps/origin chains, effects/import contracts, publication/revision capabilities and frontend/native integration. Scratch lifetime/claim-array reductions and phase-disjoint dominator storage reuse allow the selected direct-IR fixtures to pass modeled gates. Complete physical heap/GC accounting, packed native storage/physical ID layout, matched wider stress and owned-runtime performance qualification remain pending. The earlier combined owned graph/deep-chain run timed out at 120 seconds; that result remains unqualified. No limit was enlarged. One completed-batch full qualification was selected for the user-authorized merges. No separate 900-second full owned-self-build attempt was started.

U2 algorithms and machine/runtime interfaces remain separate reviews. PR #57 is unchanged and unmerged. PR #59/#60 were explicitly authorized and merged after normal CI; the final combined batch passed full qualification before #60's merge. The C-bootstrap recovery regression and its fix are recorded in #59. The production frontend/driver has not been replaced by the new scalar UIR.

## Evidence

The accompanying archive contains fixtures and expected results, raw samples and logs, hashes/provenance, measurement scripts, the native memory launcher/control records, and generated baseline assembly/runtime products. requirements.txt pins the two Unicode dependencies. Reproduction instructions distinguish unchanged compiler code from measurement infrastructure.

The original evidence archive remains unchanged and contains the original baseline report before this follow-up policy selection. New limits live in the separate budget JSON and current U1 contract; they do not rewrite the measurements or alter archived raw samples.

[Pinned repository baseline](https://github.com/eristavi/eristavi-lang/tree/8af0ffe3350c737550c3ab0e6c3fa89f60f6f091)
[Agreed U1 contract](Eristavi-UIR-U1-Contract-2026-10-29.md)
[UIR architecture](Eristavi-Typed-Universal-IR-Proposal-2026-10-29.md)
