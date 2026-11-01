# Issue #51 — frontend and typed-IR source counters (1 Nov 2026)

**Profile completed; implementation not yet justified by function-level timing.** The original requested [Actions run 41333727380](https://github.com/eristavi/eristavi-lang/actions/runs/41333727380) was cancelled by the subsequent branch documentation commit and produced **no artifact**. Its replacement [run 41333745075](https://github.com/eristavi/eristavi-lang/actions/runs/41333745075) produced `issue51-profile-1` artifact `13093484598`, inspected directly, from exact source head `86ddc178498074a21e0540ab77f5466791041485`. The completed `typed_ir.eri` observer preserved independent bootstrap assembler byte parity. The large `ir_verify.eri` observer remained **censored at 90 seconds**, with seven boundary records including first Universal verification entry but not its exit.

## Source-stage allocation and graph lookup ranking

Each row subtracts two adjacent, complete monotonic counter snapshots. Counters are **entries**, not seconds or retained bytes. The first stage includes lex/parse/startup. Snapshots are from disposable assembly with observer overhead.

| Large `ir_verify.eri` stage | Box creations | Allocator calls | Graph finds | GC invocations |
| --- | ---: | ---: | ---: | ---: |
| Before project semantic analysis (start → tag 3) | 13,163,526 | 14,586,704 | 1,979,823 | 1,094 |
| Project semantic analysis (tag 3 → tag 5) | **20,105,621** | **21,776,194** | **19,223,122** | **176** |
| Typed-IR construction (tag 5 → tag 6) | **11,788,610** | **12,231,011** | **11,014,307** | **45** |
| Typed-IR verifier (tag 6 → tag 7) | 9,636,349 | 10,016,957 | 14,043,486 | 48 |
| Universal lowering (tag 7 → tag 10) | 5,819,502 | 6,275,796 | 23,463,486 | 89 |

The last completed boundary is entry of the first Universal verifier: **60,513,608 boxed creations**, **64,886,662 allocator calls**, **69,724,224 graph finds**, **1,452 GC invocations**. The large process subsequently timed out inside verification. No complete large-source time/output parity is claimed.

## Source-level entry counts

These are method **entry counts**, not cost-attribution by caller, allocation-per-call, or CPU samples. Their ranking does **not** establish which method itself allocates most.

| Large source function | Calls |
| --- | ---: |
| `semantic.expression` | 5,236 |
| `ir_lower.fact` | 5,190 |
| `ir_lower.expression` | 5,190 |
| `semantic.statement` | 1,277 |
| `ir_lower.sourceHash` / `sourceBucket` | 843 each |
| `ir_lower.sourceCached` / `instantiate` | 662 each |
| `semantic.resolveName` | 638 |
| `semantic.call` | 492 |
| `semantic_project.analyzeModule` | 10 |

The independent small `typed_ir.eri` workload shows the same stage ordering: project semantics adds 4,244,983 boxes; typed lowering 1,578,362; initial startup 1,301,749; typed verification 1,313,619. Both instrumented and plain small-source variants produced exact C-bootstrap byte parity.

## Decision and required next execution

This identifies **semantic analysis** as the largest complete *named frontend stage*, followed by typed-IR construction. Source-fact caching is **not yet selected**: only 5,190 `ir_lower.fact` calls and 843 source-hash calls were counted, and no per-method boxes, graph lookups or wall-clock expense has been attributed. A shared cache would require source revision and mutation invalidation proofs.

The next bounded experiment should instrument **each function's inclusive allocator/box/graph entry deltas**, with low sample rate to keep observer overhead bounded, or collect an uninstrumented phase baseline on a smaller deterministic workload. Prioritize `semantic.expression`, `semantic.evaluate`, `semantic.member`, `semantic.typeRef`, `ir_lower.expression`, `ir_lower.fact`, `ir_lower.concrete`, and type registry operations. Compare exact same-revision input, unaffected errors, GC/refusals and independent bootstrap assembly before and after one local change. Five alternating *uninstrumented* pairs plus required exact-head final CI/qualification remain mandatory for a production source change. No owned compiler full self-build. **No speculative production source edit is introduced by this evidence-only checkpoint.**

See [draft PR #110](https://github.com/eristavi/eristavi-lang/pull/110) and `HANDOVER.md` §82. Issue #51 remains OPEN.
