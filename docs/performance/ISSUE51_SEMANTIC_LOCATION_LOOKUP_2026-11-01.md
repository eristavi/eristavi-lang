# Issue #51 — semantic source-location lookup: bounded measured optimization (1 Nov 2026)

Status: **FOCUSED CORRECTNESS AND ALLOCATION COUNTS PASS; FULL FINAL QUALIFICATION PENDING**. This report records the branch-only revision of [PR #110](https://github.com/eristavi/eristavi-lang/pull/110). Issue #51 remains **OPEN**; the larger source compiler still hits the original 90 s cap. Nothing below establishes an end-to-end compiler latency win.

## Frozen scope and source

- Governing order: `DESIGN_PHILOSOPHY.md` → `LANGUAGE_SEMANTICS.md` → architecture and `CI_QUALIFICATION.md` → implementation. Existing production frontend, frozen 32-byte value ABI, owned GC/fault/cleanup, validation, resource limits and both pre/post Universal IR verifier passes remain intact. No B→C/D owned full compiler self-build.
- Baseline production semantic source: unchanged `main` `src/compiler/semantic_model.eri` (main at start `cdea2387621d7c1b44dd65b3ef9fb88cf556ba74`); baseline private scoped diagnostic [run 41334612747](https://github.com/eristavi/eristavi-lang/actions/runs/41334612747), code head `3bf923e464e560a4fdc404417a300803594c37de`, artifact **13094602792**.
- First reversible experiment: hoist `node.ordinal` into `let ordinal` in `semantic_model.at`, instrumented [run 41335305818](https://github.com/eristavi/eristavi-lang/actions/runs/41335305818), artifact **13094344996**. It reduced graph finds but increased boxing/allocations and was **rejected** as a clean allocation optimization.
- Selected single source modification: left-first traversal `if token < node.ordinal { cursor=node.left; } else { if token == node.ordinal {return node;} cursor=node.right; }` (initial code commit `b5ab3cd43e136b043c0e69f49ccb5656e7cdcccb`). This is logically equivalent to equality-first traversal for each fixed ordinal and does not create a local boxed ordinal, a cache, arithmetic overflow or new root. It reads the ordinal only once on a left branch and twice on a right/match branch. This is a local evaluation-order change with no observable side effects in the key read.
- Completed left-first counter profile: [run 41335724590](https://github.com/eristavi/eristavi-lang/actions/runs/41335724590), diagnostic artifact **13094774597** (same fixed source, Linux x86-64 Clang `-O2`, independent bootstrap compiler B emitted by C). Counter instrumentation only in disposable output assembly; counts are operation entries, not CPU samples.

## Direct nonrecursive `semantic_model.at` cost

Identical input and corresponding **tag 6** typed-IR-verifier entry (after semantic analysis and typed-IR construction) of the larger `ir_verify.eri` source:

| Exact observed metric | Original | Left-first | Delta |
| --- | ---: | ---: | ---: |
| Boxed creations inside completed `at` calls | 5,102,527 | 4,598,389 | **−504,138 (−9.88%)** |
| Allocator entries inside `at` | 5,133,033 | 4,628,895 | **−504,138 (−9.82%)** |
| Graph-find entries inside `at` | 2,291,695 | 2,039,615 | **−252,080 (−11.00%)** |
| Cumulative allocation-capacity traffic inside `at` | 424,671,856 B | 382,637,696 B | **−42,034,160 B (−9.90%)** |

Unlike recursive `semantic.expression` inclusive counters, `semantic_model.at` does not recurse or call another instrumented source helper in its normal lookup path. Its inclusive call deltas are therefore meaningful as a scoped source hotspot. These figures describe **allocation traffic**, not retained heap or RSS.

## Whole source phase boundaries

Unmodified stage thresholds and source names; the large compiler still **censored at 90 seconds** within old Universal optimizer. The **tag 6** boundary is completed before that censoring. Do not extrapolate to full-run compilation or infer total-output equality for the censored workload.

| Larger `ir_verify.eri` through tag 6 | Baseline | Left-first | Delta |
| --- | ---: | ---: | ---: |
| New boxed values | 45,057,757 | 44,578,330 | **−479,427 (−1.06%)** |
| Allocator entries | 48,593,908 | 48,116,417 | **−477,491 (−0.98%)** |
| Graph finds | 32,218,728 | 31,940,703 | **−278,025 (−0.86%)** |
| Cumulative allocator-capacity traffic | 4,069,965,168 B | 4,027,616,320 B | **−42,348,848 B** |
| Garbage collection entries | 1,315 | 1,315 | unchanged |

On small `typed_ir.eri` the same tag 6 direct `at` counts changed 466,398 → 428,068 boxes (**−38,330**) and 207,814 → 188,638 graph finds (**−19,176**). Whole short-source tag 6 new boxes changed 7,125,094 → 7,111,475 (**−13,619**), while full stage counters and GC can shift because newly generated B includes the modified compiler module.

## Independent oracle, source-fact identity safety and wall-clock

- [Five paired trials and full public verifier oracle run 41335724547](https://github.com/eristavi/eristavi-lang/actions/runs/41335724547), retained artifact **13094683009**, **SUCCESS**. The exact same public Universal verifier malformed/CFG/bit-boundary corpus on baseline/C, baseline/owned, candidate/C, candidate/owned passed identical stdout/stderr/exit.
- An unchanged neutral [`examples/hello.eri`](../../examples/hello.eri) compiled with the SAME physical source path/root through both C reference and both owned B frontend compilers yielded identical assembly SHA-256 `e951211986feef49153eaff736610bf8c1f17c46f02bdb0949cdbeee25e05f26` across **all four**. Each compiler version's `typed_ir.eri` output also exactly matched its own independent C-bootstrap reference; cross-version assembly differs because `typed_ir.eri` itself imports the changed `semantic_model.eri` implementation. The changed module's assembly is not required to be byte-identical across source revisions.
- Five Linux Clang same-host *uninstrumented* alternating pairs of current owned B compiling `typed_ir.eri`: baseline median **1.678615 s**, left-first **1.679816 s** (0.0715% slower, candidate faster 1/5), byte parity against each revision's own independent bootstrap. Five repeated owned verifier pairs: **0.181307 s → 0.181237 s** (0.0387% lower, candidate faster 4/5). Both differences are runner-noise-sized, **not evidence of a speedup**.
- [Focused smoke run 41335724526](https://github.com/eristavi/eristavi-lang/actions/runs/41335724526) **SUCCESS**, with `test_source_fact_index.SourceFactIndexTests.test_identity_collisions_reanalysis_and_synthetic_nodes` added to smoke for duplicate token identity/newest fact, synthetic negative-token fallback and reanalysis.
- Diagnostic instrumentation includes per-method inclusive counter deltas through completed normal returns; parent/child semantic recursion overlaps so the huge `semantic.expression`/`statement` inclusive totals must **never be summed**. Source snapshot unchanged checks passed in each probe.

## Qualification, restrictions and outcome

The left-first change is accepted **for bounded allocation and graph-lookup improvement at matched phase boundaries**, not for demonstrable compiler wall-clock reduction. It preserves error paths, mutations outside a lookup call, missing/fallback locations and read-only key comparisons; no new cache or unbounded memory.

**Prior to merge:** select one exact-final-head 4-platform full CI matrix and full bootstrap/owned offline qualification per `CI_QUALIFICATION.md`, and verify source/tree identity and final job outcomes. The experimental owned full B→C/D compiler self-build stays excluded. Do not rerun heavy gates for documentation-only changes after exact qualified code inputs. Keep issue #51 OPEN for the still-censored larger production source; further upstream allocation, GC/boxing and typed-value representation optimizations need independent proofs.
