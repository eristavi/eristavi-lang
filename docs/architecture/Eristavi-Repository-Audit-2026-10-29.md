# Eristavi — repository-wide engineering audit

29 October 2026 · Review of `eristavi/eristavi-lang`

## Assessment

The evidence does not justify discarding the language design or rebuilding the entire compiler architecture. It does show substantial implementation debt in shared runtime operations, data structures, and the self-hosted code-generation path. The slowdown is not adequately explained by one Universal optimizer lookup.

The strongest new result is a reproduced quadratic allocation path in the exact owned runtime emitted for the failed run. A second probe confirms severe internal fragmentation when a small request reuses a large free block. Separately, the module cache can reuse artifacts produced by an older compiler implementation. These are concrete findings, not a claim that every observed second has now been attributed.

The appropriate next step is a measured repair of the shared foundations, alongside independent correctness fixes. Keep the source semantics, mandatory verification, identity rules, and public 32-byte value ABI. Keep PR #57 open until its integration value is established.

## Scope, identity, and limits

- Tested/reviewed head: `8af0ffe3350c737550c3ab0e6c3fa89f60f6f091`, PR #57.
- Main at inspection: `17a39a508728e42465add23c497189684d6318a9`.
- Retrieved all **342 repository files**, totaling **2,771,268 bytes**. Recomputed Git blob SHA-1 identities for every local file: **zero mismatches**.
- Parsed all **145 Python files** with Python's AST parser: **zero syntax errors**. Inventoried **429 test methods**, **86 Eristavi source files**, and **29 runtime emitter files**.
- Reviewed the main frontend/semantic pipeline, typed and Universal IR, verification, both Eristavi native emitters, owned allocation/value/graph/root paths, reference backend analysis, object/cache boundaries, build/evidence scripts, test harnesses, and relevant architecture documents.
- Reused the existing four-platform CI and full qualification evidence. Did not rerun those suites or another compiler self-build.
- Executed two tiny allocator probes against the existing emitted owned runtime and one isolated cache-class probe. Details below.

This is a repository-wide source and evidence audit, with focused deep review of the paths relevant to performance and trust. It is not an exhaustive manual proof of every line, a complete new execution of every backend/corpus, or a guarantee that no further defects exist. Every file was retrieved and identity checked; that is not equivalent to independently proving every file correct. The root cause of the full 900-second runtime remains only partially attributed.

## Existing failure evidence

[Owned self-build run 40829491044](https://github.com/eristavi/eristavi-lang/actions/runs/40829491044)

Artifact: `pr57-owned-self-build`, ID `12878257815`.
Artifact ZIP SHA-256: `41bd29ba7a945c6e6008f2a4f2b6a5e8edbbd7a2828e0b14f939b4c32c17b8aa`.

`evidence/qualification.json` records a timeout during `native-B-to-C-assembly`, unchanged source, no completed C or D, and no repeatability qualification. Compiler-B SHA-256 is `31c4433fa599ce52c3ddd6814cd510d39b35c1d004793ec7b48ce5b99ab24eb1`, matching the owned integration artifact's B binary.

Times below are elapsed wall time from the start of the B emission command, derived from its recorded phase events. The Universal-lowering outer phase includes typed verification; the table subtracts that nested phase to avoid double counting.

| Work | Elapsed interval | Duration |
|---|---:|---:|
| Initial frontend work and semantic project analysis | 0–268.324 s | ~268.3 s |
| Typed IR lowering | 268.328–400.522 s | ~132.2 s |
| Typed IR verification | 400.525–698.588 s | ~298.1 s |
| Universal lowering after typed verification | 698.588–887.260 s | ~188.7 s |
| Universal optimization observed before termination | 887.261–900.040 s | ~12.8 s |

All 459 source functions finished typed lowering; all 460 routines, including the entry, finished typed verification and Universal lowering. There was no preceding compiler error diagnostic. The timeout handler killed the command group; exit `-9` here is expected termination behavior and does not establish a crash or OOM.

**Correction to the previous working model:** being inside `universal-optimize` when killed does not prove that optimizer work dominates. This sample spent approximately 98.6% of its budget before optimization. The earlier samples entered optimization at ~720.76 and ~844.09 seconds, on a smaller compiler workload. These are not controlled paired measurements of PR #57.

## Findings and repair priorities

P1 means important correctness/performance work before promotion; P2 means scalability, maintainability, or validation work that should be planned. No P0 memory-corruption defect was demonstrated in this review.

### A1 — P1: every allocation can rescan one mixed-size free list

**Status: source confirmed and reproduced on the existing emitted runtime. Full-build contribution not yet measured.**

Sources: [allocator emitter, freeListBody](https://github.com/eristavi/eristavi-lang/blob/8af0ffe3350c737550c3ab0e6c3fa89f60f6f091/src/runtime/allocator_x86_64.eri#L21) and [allocatorBody](https://github.com/eristavi/eristavi-lang/blob/8af0ffe3350c737550c3ab0e6c3fa89f60f6f091/src/runtime/allocator_x86_64.eri#L30).

`erist_rt_alloc` invokes `erist_rt_freelist_take` before attempting fresh bump storage. The latter starts at the head of one global free list and examines successive blocks until one is large enough. A run of undersized blocks remains available for the next request, so the next larger request repeats the same scan. Each examined entry also performs checked metadata loads.

Probe method: use `owned-runtime.s` from the failed run; add one counter increment at `.Lfreelist_scan`; allocate N blocks of 48 bytes, free them, then request N blocks of 128 bytes without freeing those new blocks. Count loop entries, including the final empty-list check. Assemble/link only the small probe with the existing runtime; no compiler rebuild. All probes exited 0, wrote exactly eight counter bytes, and emitted no stderr.

| Small free blocks | Larger requests | Free-list loop entries |
|---:|---:|---:|
| 64 | 64 | 4,160 |
| 128 | 128 | 16,512 |
| 256 | 256 | 65,792 |

The count is exactly N × (N + 1), demonstrating quadratic work for this allocation shape. This affects a shared service used by value slots and graph objects throughout the pipeline. The free-region/page cache improves `free`; it does not remove this allocation-side search.

**Repair direction:** checked size-segregated reusable blocks, or a comparably bounded-fit policy, with a fallback for large allocations. Preserve reservation provenance, metadata validation, allocation-failure semantics, and the public ABI. First obtain counts on a representative bounded compiler workload so the expected benefit is attributable.

### A2 — P1: large free blocks are consumed whole by tiny requests

**Status: source confirmed and reproduced. This is fragmentation, not demonstrated value corruption.**

The reuse branch takes the first sufficiently large block and marks its original capacity allocated. It does not split that block into a requested-size block and reusable remainder.

A separate probe allocated and freed a 65,536-byte block, requested 48 bytes, verified that the same block was returned, and inspected its validated capacity header:

| Requested payload | Capacity retained by the allocation |
|---:|---:|
| 48 bytes | 65,536 bytes |

That is over 1,365 times the requested payload capacity for this case. It does not imply the full compiler has that ratio. The allocator also retains reserved regions until `release_all`; this is a retention policy, not automatically a leak.

**Repair direction:** splitting when the remainder can hold a valid header and useful payload, or preventing small allocations from consuming arbitrarily large classes. Review together with A1 rather than adding independent patches that fight each other. Coalescing and page return are separate questions.

### C1 — P1: typed verification still performs repeated linear type/function lookup

**Status: source confirmed; contribution to the 298-second phase remains unmeasured.**

Sources: [typed_ir lookup helpers](https://github.com/eristavi/eristavi-lang/blob/8af0ffe3350c737550c3ab0e6c3fa89f60f6f091/src/compiler/typed_ir.eri#L23) and [ir_verify.expression](https://github.com/eristavi/eristavi-lang/blob/8af0ffe3350c737550c3ab0e6c3fa89f60f6f091/src/compiler/ir_verify.eri#L109).

`ir.kind`, `ir.inner`, and `ir.fieldAt` reach the linear `ir.typeAt` chain. The verifier queries kinds repeatedly per expression, and uses linear `ir.functionAt` for calls. The private type index added for lowering is not used in the independent verifier. Optimizing one phase's lookup does not improve every consumer of the canonical table.

A source-close expression visit can therefore cost O(T) in descriptor lookup, and each call can cost O(F) in target lookup, before runtime pointer/boxing costs. This does not establish that every lookup visits every entry.

**Repair direction:** build independently validated, verifier-private indexes once per program. Preserve canonical iteration order, sparse descriptor behavior where currently accepted, exact identity, diagnostics, and the validation boundary. Do not trust the lowerer's cache merely to save time.

### C2 — P1: Universal lowering still linearly searches routine locals

**Status: source confirmed; whole-build contribution not measured.**

Sources: [universal_model.local](https://github.com/eristavi/eristavi-lang/blob/8af0ffe3350c737550c3ab0e6c3fa89f60f6f091/src/compiler/universal_model.eri#L25) and [universal_lower.expression](https://github.com/eristavi/eristavi-lang/blob/8af0ffe3350c737550c3ab0e6c3fa89f60f6f091/src/compiler/universal_lower.eri#L32).

Every relevant lowered local use calls a helper that scans `builder.locals`. The list is prepended during routine setup. Repeated uses of locals far from its head can accumulate O(U × L) work. The measured post-verification Universal construction cost was ~188.7 seconds.

**Repair direction:** one private per-routine ID-to-register index, constructed from the already verified local table, while retaining the public representation and generated output. Measure lookup visits before selecting a representation.

### R1 — P1: the owned compiler uses boxed helper operations for ordinary scalar work

**Status: confirmed implementation property; runtime cost not individually attributed.**

Sources: `src/compiler/universal_lower.eri`, `src/compiler/ir_x86.eri`, `src/runtime/value_scalar_x86_64.eri`, and `src/runtime/graph_values_x86_64.eri`.

Local reads lower to `copy`; arithmetic generally lowers to `binary`; field reads lower to `member`; optional extraction lowers to `get`. The owned runtime creates temporary value slots for scalar and other copies. This is correct by construction but much more expensive than an unboxed register operation, especially when every allocation encounters A1/A2.

The existing compiler-B assembly contains **183,098 lines and 32,944 static call sites**. These include **8,896 `evn_copy`**, **2,919 `evn_binary`**, and **2,814 `evn_member`** call sites. These are static code counts, not dynamic execution counts or a speedup estimate.

**Repair direction:** reduce avoidable allocations/copies using proven private fast paths and, later, semantic-aware scalar lowering. The stable public 32-byte ABI does not require every private intermediate to be allocated on the heap. Any unboxing needs checked-arithmetic, aliasing, call, failure, resource, and safepoint proofs; it is not a quick deletion of helper calls.

### R2 — P1: dead temporaries remain in broad function root maps

**Status: source/assembly confirmed; heap-retention and tracing contribution not measured.**

Sources: [ir_x86.routine](https://github.com/eristavi/eristavi-lang/blob/8af0ffe3350c737550c3ab0e6c3fa89f60f6f091/src/compiler/ir_x86.eri#L47), `ir_arm64.routine`, and `runtime/value_roots_x86_64.eri`.

The Eristavi backend allocates stack slots/root descriptions from all Universal registers plus parameters. It does not use the Python direct backend's instruction-level liveness analysis. A class-1 value pointer can remain in its static register slot after its final use, keeping its temporary slot and graph reachable until overwrite or scope exit. This can make later collections revisit dead work within long-running functions.

The root descriptions for compiler functions `f161` and `f372` contain 2,308 and 1,426 register/parameter entries respectively, excluding their terminating zero byte. These are descriptor lengths, not counts of simultaneously live heap objects.

**Repair direction:** measure retained slot/root counts and collection work by phase. Introduce verified last-use clearing or liveness-aware root planning in a dedicated change with failure/unwind and interior-pointer coverage. Removing roots without those proofs would be a correctness bug.

### R3 — P2: every mutable field access takes the conservative object-detach path

**Status: source confirmed; optimization eligibility needs alias analysis.**

In `runtime/graph_values_x86_64.eri`, `evn_member_ref` calls `erist_rt_graph_detach`. Detach allocates a new backing object and copies all its initialized cells. Even identity-backed member updates pass through a shared-inner-value representation and this conservative copying path. The typed structural verifier sets and clears `Node.marked`, so those traversals also exercise member mutation.

This protects ordinary value semantics but creates allocation/copy work for very frequent compiler bookkeeping. Do not simply remove detach: ordinary values and snapshots must remain independent.

**Repair direction:** identify an exclusive or otherwise semantically proven mutation path; retain the conservative fallback. This is a shared runtime improvement candidate, not permission to change identity semantics.

### C3 — P2: further graph/type traversals lack general memoization or bounded depth

**Status: source confirmed; failure/performance thresholds not reproduced here.**

- `semantic_types.resolve` follows link chains without path compression. Repeated deep chains can remain costly; union links are not balanced by rank.
- `semantic.layout` recursively searches imported modules without a per-query visited set/cache. On the actual frontend import graph, a failed full traversal expands 30 distinct reachable modules to 401 recursive module visits. This count models a full miss from `frontend`; it is not a count measured during the failed compile. Real early hits can be cheaper.
- `ir_verify.layout` scans prior functions and prior local tails. It avoids the old per-local quadratic identity bug but retains O(F²) table checking.
- `ir_verify.tree` recursively traverses sibling `next` links as well as children. Long flat bodies therefore contribute to native recursion depth. No stack-exhaustion threshold was established in this audit.
- `universal_optimize.visit` recursively visits CFGs and retains linear `blockAt`. The previous flow-index change does not optimize that distinct path.

**Repair direction:** use explicit worklists where input depth is unbounded; privately index or memoize repeated queries while preserving error order. Avoid changing every list merely because it is a list: measure relevant multiplicities.

### B1 — P1 correctness: build-cache identity omits compiler implementation identity

**Status: source confirmed and reproduced in an isolated unit harness of the actual cache class. Unrelated to the owned self-build timeout.**

Source: [ArtifactBuilder fingerprint and hit path](https://github.com/eristavi/eristavi-lang/blob/8af0ffe3350c737550c3ab0e6c3fa89f60f6f091/compiler/erist/build_cache.py#L100).

The key contains source bytes, public dependency-interface digests, Unicode version, and schema/IR versions. It contains no compiler build identity or explicit semantic implementation version. A compiler bug fix that leaves those format constants unchanged can reuse artifacts emitted by the old compiler.

Probe method: execute the actual `ArtifactBuilder` class, isolating parser/compiler collaborators with deterministic test doubles. The first compiler returns artifact payload A; the next compiler returns payload B with source and schemas unchanged. A fresh builder reports a hit, produces the same key, and copies payload A. This isolates invalidation logic; it is not an end-to-end language compilation test.

**Repair direction:** add an explicit toolchain semantic/build fingerprint to the cache key, with a regression covering an implementation change. Do not indiscriminately invalidate importers for every private dependency edit: the existing public-interface rule is useful where artifacts do not embed changed implementation work.

### B2 — P2 correctness/resilience: a cache hit trusts file existence

**Status: source confirmed; interrupted/corrupted-cache behavior not dynamically reproduced here.**

The cache hit condition is just that both cached files exist. Cache files and adjacent output files are written/copied separately. There is no payload digest validation on the hit branch and no atomic publication of the pair. An interrupted write can leave a pair considered reusable on the next invocation; consumers may reject it later, but the cache itself reports a hit and publishes it.

**Repair direction:** validate schema/identity/digests before reuse, and publish a complete cache entry transactionally. This is independent of the compiler-throughput problem.

### V1 — P1 evidence: current timing capture is incomplete on timeout

**Status: observed failure in this session's diagnostic wrapper, not a defect attributed to the production compiler.**

`owned-emit-18.time.txt` is empty. The diagnostic wrapper placed `/usr/bin/time` in the group that the journal kills on timeout, so it did not finalize its measurements. Wall-time phase events survived, but no valid per-emission user/system CPU or maximum-RSS result is available. The exact interaction is inferred from the wrapper and group-kill code; the empty file itself is observed.

Production `BuildJournal` records wall durations and phases but not per-child CPU/RSS itself. It also groups optimizer pre-verification, reachability, and post-verification under one broad production phase.

**Repair direction:** retain CPU/RSS through timeout using a resource-accounting mechanism outside the killed workload group or direct child accounting. Separate optimizer subphases in diagnostics. Do not rerun a 900-second build solely to fill this missing file.

### V2 — P2: documentation and qualification can be read as one pipeline when there are two

**Status: source/documentation confirmed.**

The Python direct pipeline has richer typed Universal IR, CFG liveness, spill planning, physical-register allocation, and related tests. The Eristavi-written path used for this owned self-build has a different helper-oriented Universal representation and simpler all-register stack/root emission. Its Universal optimizer removes unreachable blocks; Python-side constant folding and register allocation do not automatically apply to it.

Some documents explicitly distinguish these implementations, but the repository overview and historical audit updates require careful reading. Green tests of Python/direct-backend features do not qualify equivalent owned self-hosted behavior. Existing tests are meaningful; the problem is how their scope is interpreted.

**Repair direction:** maintain one current capability/qualification matrix naming compiler implementation, backend, runtime profile, target, and gate. Mark historical audit sections clearly. Promote features only on evidence from the path that actually executes them.

## Architecture and coverage review

| Area | Assessment |
|---|---|
| Language semantics and philosophy | No demonstrated need to weaken typing, checked Int, explicit failures, identity/value separation, or deterministic resources. |
| Lexer/parser | Byte-cursor lexer avoids the older whole-file scalar-indexing pattern. Existing frontend corpus has 42 cases. No new lexical/parser correctness defect demonstrated. Recursive depth remains a hardening consideration. |
| Semantic analysis | Explicit phase/module boundaries exist. Linked symbol/type searches, uncompressed type resolution, and recursive import-layout lookup are scalability risks. Existing semantic corpus has 175 cases. |
| Typed IR | Useful independent verification boundary. Private indexes are inconsistently available across consumers; structural bookkeeping itself allocates/mutates many graph objects. |
| Universal IR and optimizer | Representation is coherent enough to verify/lower; remaining lookup, dataflow, and CFG work needs attribution. This timeout is not proof that optimization consumed most time. |
| x86-64/ARM64 emitters | Share the Eristavi helper-based IR; both are simpler than the Python direct backend. Broad root maps and boxed values matter for the executed path. |
| Owned allocator/value runtime | Shared scaling problems reproduced; automatic reclamation exists but does not guarantee low allocation cost or low retained memory. |
| Text/Unicode/Float/resources | Existing dedicated tests and pinned data provide evidence. Manual assembly emitters form part of the trusted implementation boundary; this review does not newly prove all numerical, Unicode, or syscall behavior. |
| Object/cache pipeline | Source-independent artifacts exist; compiler-identity invalidation and cache publication need correction. These paths are not the owned full-build timeout cause. |
| Build/offline qualification | Existing full gate genuinely checks repeated bootstrap builds and offline application behavior. Owned integration intentionally records non-repeatability; full owned repetition is still unqualified. |
| Test suite | 429 discovered methods; existing successful CI is reusable for the exact head. Platform skips and pipeline/runtime distinctions must remain visible. No full suite rerun during this audit. |
| Dependency removal/platform roadmap | Python/C bootstrap, GNU assembler/linker, shell/host dependencies and incomplete additional-platform ownership remain real boundaries, not explanations to bypass the current owned gate. |

## Recommended repair sequence

1. **Repair diagnostic accounting and collect cheap structural counters.** Count allocation request sizes, free-list visits, capacity/request ratios, slot creation/pruning, collections, roots visited, and graph objects traversed on a representative bounded workload. Avoid instrumenting every operation with expensive allocation. Require identical output.
2. **Address allocator A1/A2 together.** This is the strongest newly reproduced shared scaling defect. Use deterministic work counters, mixed-size reuse checks, allocation-failure checks, and correctness/ABI gates. Do not promise a full-build percentage before measuring.
3. **Index typed-verifier type/call lookup and Universal-lowering locals as separate attributable changes.** These correspond to large observed pre-optimizer phases. Build each private index from validated canonical inputs.
4. **Measure remaining boxing, mutation-copy, and root-retention costs.** Select a narrow proven fast path. Plan liveness-aware rooting as its own correctness-sensitive batch rather than an emergency shortcut.
5. **Fix cache correctness independently.** Include compiler identity and validated atomic entries; these fixes should not be presented as self-build performance improvements.
6. **Run normal CI and full qualification on the completed implementation batch.** Inspect logs/artifacts and guard exact source identity. Retain mandatory verifier passes.
7. **Only then run one justified 900-second owned repeatability gate.** If it times out, inspect phase/counter evidence before another attempt. Do not raise the boundary to manufacture success.

PR #57 should remain an open, isolated candidate during this work. Its focused owned-verifier benchmark is valid within its workload, but the existing full-run result does not establish end-to-end improvement. A small lookup improvement is neither proof of a healthy whole pipeline nor proof of a broken language architecture.

## What changed during this audit

No production code, branches, PR metadata, or repository tests were modified. No new CI workflow, qualification run, or compiler self-build was launched. Only the review snapshot, temporary local probes, and this report were created. The two allocator probes use the already emitted runtime and system assembler/linker; the cache probe isolates actual cache-class logic. Neither is a substitute for later completed-batch qualification.

The evidence supports a focused engineering repair program. It does not support declaring the whole project irreparable, or claiming that one newly found allocator defect explains the entire timeout without representative measurements.
