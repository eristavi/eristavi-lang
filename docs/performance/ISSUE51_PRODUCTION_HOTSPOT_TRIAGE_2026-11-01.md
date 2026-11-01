# Issue #51 — production Universal optimizer hotspot triage (2026-11-01)

Status: **analysis / candidate selected; no production code change, no new benchmark run**.

## Frozen basis

Follow `DESIGN_PHILOSOPHY.md`, `LANGUAGE_SEMANTICS.md`, `CI_QUALIFICATION.md` and latest `HANDOVER.md` §77. Keep the existing production frontend and ABI frozen; no experimental full owned B→C→D self-build without separate authorization.

## Reproduced from committed evidence (not a fresh measurement)

- `docs/evidence/2026-11-01/u1b-source-compiler-profile.json`: the old production compiler completed `src/compiler/typed_ir.eri` in **2.186212 s**, with exact output parity (SHA-256 `172769263e830e6bb555926612972f8b807b8a6f9261e0ca88087165f135cfb7`).
- The same prior diagnostic **censored `src/compiler/ir_verify.eri` at 90 s** inside `universal-optimize`, so there is **no completed parity result** or valid before/after time for that input.
- `src/compiler/universal_optimize.eri` calls `universal_verify.verify(program)` both **before and after** unreachable-block removal. These are correctness boundaries and must not be removed simply for speed.
- `src/compiler/universal_verify.eri` currently has a linked `Flow` list and `flowAt(flows,index)` linear search. The routine invokes `flowAt` during duplicate-block checks, entry discovery, and successor resolution. This is an identifiable potential repeated-lookup cost, **not yet a measured hotspot**.
- `src/runtime/graph_heap_x86_64.eri` already grows its graph registry beyond the old 16,384-live-object threshold and has a prepared non-owning interval index. Do **not** reapply superseded growth/caching suggestions.
- Previous U1b reference-only fixed-depth word-read speedup does not establish improved production compiler latency.

## Four measurement dimensions — required next diagnostic

| Dimension | Existing observable hook | Claim we can make now |
|---|---|---|
| Allocation | `erist_rt_alloc`, success/failure and capacity traffic counters in `tests/test_u1b_runtime_hotspot.py` | Hook available; production-compilation count **unmeasured** |
| Boxing | `erist_rt_value_new`, `erist_rt_scalar_value_new`, scalar copy/binary hooks | Hook available; compiler workload count **unmeasured** |
| Graph lookups | `erist_rt_graph_find`, `erist_rt_graph_owner`, `erist_rt_graph_prepare_index` | Hook available; compiler workload count **unmeasured** |
| Validation | Old `universal_verify.verify` before/after optimizer, traced `universal-optimize` phase | Two full passes confirmed; separate pass times **unmeasured** |

**Next bounded profile:** use a disposable diagnostic runtime/compiled frontend; instrument those existing entry labels and the two validator call boundaries, keeping generated output and normal production sources unchanged. Run identical `typed_ir.eri` and `ir_verify.eri` inputs with fixed 90-second per-run caps, record time and operation counters separately, and compare the *uninstrumented* output byte-for-byte against C-bootstrap reference. Instrumented clocks/counters are observer-bearing and are **not speedup evidence**. A timeout is censored and must retain last phase/counters, not be reported as a completed measurement. Do not run a full owned compiler self-build.

## Selected optimization candidate (conditional on measured attribution)

**Reduce repeated `flowAt` linear walks in the production Universal verifier by adding a bounded per-routine index for block lookup**. The existing linked list remains the source of truth. The index must reject duplicate/missing/negative block IDs exactly as today, preserve strict validation and resource refusal, and be local to one verification routine. A dense index must **not** allocate according to an attacker-controlled maximum block ID; size it by validated block count, or use a bounded sorted table with logarithmic lookup. If profiling shows boxing/allocation rather than block lookup dominates, reject this candidate and optimize the actual measured hotspot instead.

### Acceptance before code is merged

1. Collect baseline counts and phase times at the exact source/runtime revision; include both pre- and post-optimization verification counts. Record graph registry probes/owner lookups, new boxed values, allocator calls, allocator-capacity traffic, GC time and peak RSS distinctly (not interchangeable).
2. Add a focused regression for valid CFG, unreachable/duplicate/negative/missing block IDs, divergent control flow, and allocation pressure, with independent C-bootstrap oracle and exact output hashes.
3. Take five alternating **uninstrumented**, same-host baseline/candidate timing pairs on the same workload; require all correctness/refusal/limits to remain unchanged. Do not claim a speedup from instrumented timing.
4. Run a single completed-batch full 4-platform matrix and the appropriate final qualification before merging production changes. Keep issue #51 open until this evidence is complete.
