# U1a opcode classification and CFG successor audit

Checkpoint: 2026-10-30. This document records an isolated, behavior-preserving hardening slice of the **closed** U1a foundation profile. It is not approval to add operations without the full U1 contract and the architecture decision documents.

## Current, executable profile

| Op ID | Description | Kind | Inline CFG edges |
| --- | --- | --- | --- |
| 1 | `const.i64` | canonical scalar | 0 |
| 2 | `const.pred` | canonical scalar | 0 |
| 3 | checked signed i64 add/overflow pair | canonical scalar | 0 |
| 4 | `pred.not` | canonical scalar | 0 |
| 5 | guard / terminal runtime fault | canonical effect | 0 |
| 6 | jump | canonical terminator | 1 |
| 7 | branch | canonical terminator | 2 |
| 8 | return | canonical terminator | 0 |
| 9 | `const.f64.bits` | canonical scalar | 0 |
| 10 | `cell.init` | private construction cell | 0 |
| 11 | `cell.read` | private construction cell | 0 |
| 12 | `cell.write` | private construction cell | 0 |

`known` continues to reject opcodes outside 1–12. Canonical verification rejects all construction cells; the SSA promoter produces a separately verified cell-free function.

## Safe classification boundary

Previously, some builder/verifier/promoter paths used `op >= 10` or `op < 10` as a proxy for cell membership, while CFG walkers each hard-coded jump and branch. Future opcode 13 could therefore have been mistaken for a cell or silently discarded by promotion.

This batch adds explicit `ops.isCell(op)`, `ops.inlineEdges(op)` and an enumerated `ops.terminal(op)`. The builder, independent verifier and promoter consume these classifications. No operation is added, removed or renumbered; instruction records, edge records, budgets, ABI, source semantics and production frontend/driver remain unchanged.

`inlineEdges` describes **only** the current two inline edge slots. A sparse multiway switch **cannot** be enabled by returning a count greater than two: it needs a separately reviewed case/edge side-table, discriminant semantics, duplicate-case and default policy, verification, SSA argument checking and a promoter copy/rebuild plan.

## Gates before adding op 13 or beyond

1. Read the authoritative Eristavi U1 contract and reconciled architecture decisions; do not recreate missing documents from names or summaries.
2. Define explicit instruction schema: operation category, operand/result types and arity, effects, locations, payload/attributes, and canonical availability. Avoid opcode ranges.
3. Define CFG successor iteration shared across verification, dominance, promotion, and reference execution, including sparse switches without allocation proportional to the largest case value.
4. Independently test zero/multiple results, direct calls and imported signatures/effects, switch transfers, checked i64 div/rem including MIN/-1, strict binary64 environment and bit observations, and malformed dead/reachable IR.
5. Preserve transactional promotion, modeled work/capacity quotas, and private cell-free publication; extend source-map/origin and full physical allocation evidence separately.
6. Obtain focused checks, four-platform CI, and the required completed-batch qualification on the exact final code revision before proposing merge. Do not launch the historical 900-second **owned** self-build automatically.

## Evidence and limits

The targeted source and classification regression is in `tests/test_u1_foundation.py`; existing `test_u1*.py` differential and malformed-IR suites remain unchanged. Local static replacement/count checks were performed before publication. Runtime and CI results must be recorded from the actual branch; do not infer success from unchanged op semantics alone.

The full operation/call/switch design is **not** implemented by this patch, nor is the new U1 architecture integrated into the production driver. It is the first safe prerequisite, not a completed U1a milestone.

References: `HANDOVER.md`, `UIR_U1A_FOUNDATION.md`, `UIR_U1A_VERIFIER.md`, `UIR_U1A_PROMOTION.md`, `CI_QUALIFICATION.md`.

## Follow-on isolated predicate extension (next branch, 2026-10-30)

The original closed foundation registry documented above is the pre-extension baseline. The later isolated predicate slice adds op 13 `pred.and` and op 14 `pred.or` without widening the private cell category (still **exactly** 10/11/12) or the inline CFG edge profile. See `UIR_U1A_PREDICATES.md`. This does not authorize switch/call/strict-Float schema changes.
## CI-detected missed opcode threshold (2026-10-30)

The initial U1a i64 candidate exposed a previously missed `instruction(state,cursor,0) >= 10` in `u1_promote.eri:prepare`. It misclassified new canonical op IDs as temporary cells when preparing cell instruction chains, and the i64 diamond fixture failed its exact SSA-promotion shape check. Fix: use `ops.isCell(...)` and extend the static test guard to reject direct opcode-read thresholds, not just local `op >= 10` comparisons. Preserve the strong one-parameter/two-edge merge shape assertion; do not weaken it to conceal the error. Initial ARM64 CI failed on pre-fix `8df153aa`; only fresh CI on the corrected head can qualify this change.
