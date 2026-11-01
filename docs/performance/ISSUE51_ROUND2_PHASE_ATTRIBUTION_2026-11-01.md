# Issue #51 — second-round bounded compiler profile (1 November 2026)

**Observed, not yet optimized.** Exact completed [GitHub Actions run 41332022630](https://github.com/eristavi/eristavi-lang/actions/runs/41332022630), workflow artifact `13094081498` (`issue51-profile-1`), instrumented diagnostic head `fb74bcc13fee3092232eaa0ba7fa96893b12b817`. No Eristavi implementation, ABI, optimizer, checker, memory limit or original source was changed. Retain both mandated Universal verification passes. U2/U3/U4 statuses unchanged.

## Reconciled counter boundaries

A `tag=6` snapshot is emitted at entry to `universal_lower.lowerWithTracing`, **before** the typed-IR verifier; `tag=7` at the first `universal_lower.routine` entry, *after* typed verification; `tag=10` at Universal optimizer entry; `tag=30` immediately after the first Universal verifier returns. These are checkpoints, not separate complete-run wall-clock measurements.

| Large `ir_verify.eri` stage | New box objects | Allocator entries | Graph-find entries | GC entries |
| --- | ---: | ---: | ---: | ---: |
| Program start → typed-verifier entry | 45,057,757 | 48,593,916 | 32,217,975 | 1,315 |
| Typed verifier | 9,636,349 | 10,016,954 | 14,043,322 | 48 |
| Universal lowering, 182 routines | 5,819,502 | 6,275,795 | 23,463,408 | 89 |
| First Universal verifier | 24,294,026 | 25,498,793 | 67,148,582 | 198 |

Through the first verifier: **84,807,637 boxes; 90,385,458 allocator entries; 136,873,287 graph finds; 1,650 GC entries**. Instrumentation bears time overhead. The diagnostic was **censored at 90 s** both baseline and instrumented. Neither total latency nor assembly parity of this larger program is known.

The typed verifier entered **182** routines and evaluated **5,692** expression visits. Universal lowering processed **182** routines, **5,416** expression visits, **6,755** helper calls and created **12,591** IR instruction nodes and **10,857** register nodes. The first Universal verifier ran **7,433 transfers**, **5,358 intersections** and **3,486 `flowAt` lookups.** The short `typed_ir.eri` workload completed with independent byte-exact C-bootstrap assembly parity in both uninstrumented and instrumented variants. The existing cross-run observed times are not paired speedup evidence.

## Decision: further isolate the earliest 45M-box phase

The largest completed attribution is the **frontend/initial IR path before `universal_lower.lowerWithTracing`**, not the 3,486 verifier `flowAt` lookups or the 1,936 unreachable-pass `blockAt` lookups (both seen in the large observed workload). Do **not** spend a compiler implementation batch on those lookup indexes without deeper hotspot evidence. Likewise, the 12,591 Universal instructions cannot alone explain 45M prior boxes.

**Next minimal diagnostic:** add entry/exit counters or an event-stream reducer for lex/parse, module/source analysis, source-fact indexing, typed IR lowering and typed IR verification; include output byte parity and same 90s cap. Rank boxing/allocating caller families by emitted source-symbol entry (especially repeated source fact/location/index access and type lookup). Attribute GC and graph-find entry counts distinctly. Only then select a local hoist, proven lookup reduction, or bounded memoization with revision and source-mutation safety. No shared mutable cache, unchecked scalar unboxing, deleted verification, fault suppression, changed compiler ABI, or unbounded table.

**Acceptance:** full independent C-bootstrap and owned compiler output/parity; malformed and source-mutation regressions; five same-host alternating uninstrumented timing pairs against a fixed baseline; one completed-batch full 4-platform CI and required qualification when implementation code changes. Do not request owned B→C/D full self-build without separate permission.

See §79/§80 in `HANDOVER.md` and [PR #110](https://github.com/eristavi/eristavi-lang/pull/110). Issue #51 stays OPEN; this draft profiler alone does not qualify a production speedup.
