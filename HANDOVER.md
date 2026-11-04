# Eristavi compiler — current handover

Reviewed 3 November 2026 (Asia/Nicosia). This is the current recovery document.
Historical checkpoints are evidence, not instructions to restart old work.

## Resume here

### 4 November 2026 — Managed Text / Unicode17 focused checkpoint

- **Verified candidate:** `bce2e9c59b7c997d436f9b74980a31b6c4878aa2` on draft PR #111.
  [Dedicated native Text checks #41789413436](https://github.com/eristavi/eristavi-lang/actions/runs/41789413436)
  **PASSED**: 3 test methods, 0 failures, covering eight native
  expression/Unicode cases, invalid surrogate terminal fault, and malformed
  descriptor/import rejection. Includes immutable copy and explicit GC.
- **Current U2 full focused smoke:** [#41789413729](https://github.com/eristavi/eristavi-lang/actions/runs/41789413729)
  still in progress at this checkpoint. Do NOT mark full smoke green
  until that exact-head run completes. The four-platform U2 matrix and
  completed-batch qualification remain outstanding.
- **Descriptor/reference basis:** stronger frozen Text kind/copy/view/
  Unicode17 policy, negative corruption/foreign TypeId checks and the
  independent Stage-0/C/owned reference corpus of accents, ZWJ emoji,
  flags, ASCII wrappers, empty Text and value copying. These reference
  checks passed on prior focused execution; native Text is a distinct
  opt-in UIR adapter, not production frontend lowering.
- **Failure and repair history:** the initial native Text commit
  `aa675d83` failed on a no-shadowing diagnostic. Later revisions
  corrected the fixture's ValueId specialization, a numeric assembly
  oracle/linker issue, and an accidentally removed first descriptor
  guard during temporary instrumentation. Temporary fault tracing was
  removed before the passing exact-head dedicated native run.
- **Remaining Text scope:** general Text operations and views/indexing,
  multi-block CFG and recursive roots, complete checked failures/cleanup,
  malformed/fuzz and physical RSS/retention evidence, Stage-0
  differential execution on the new UIR adapter, and final platform
  qualification. **Do not merge U2 or close #74 on this evidence alone.**


- **Active work:** U2 on `compiler/u2-cleanup-foundation-20261102`, draft
  [PR #111](https://github.com/eristavi/eristavi-lang/pull/111). U2 is unmerged;
  issue #74 remains OPEN.
- **Current tested implementation:** native CFG List-i64 successor-edge root
  retirement, code commit `91f2703532a5b4644c25e0b0fc908d3106e7f769`;
  final test-only revision `d2a25a82d9d8216f494118b348878e25176903d1`.
- **Latest hosted evidence:** [CI #41718084522](https://github.com/eristavi/eristavi-lang/actions/runs/41718084522)
  on exact `d2a25a82`: patch check SUCCESS; focused Linux Clang smoke
  **92 run, 89 passed, 0 failed, 3 intentional skips, 382.990 seconds**.
  Four-platform matrix intentionally SKIPPED; no full qualification.
- **New implementation boundary:** when at most 32 List-carrier SSA values are
  selected, verified canonical CFG live-in facts clear dead List root slots
  after simultaneous successor edge transfers, including loops and cyclic
  moves, before the next possible allocation. More than 32 List values retain
  the existing conservative multi-block policy, up to 128 total native SSA
  values. Intra-block roots remain conservative; no general exact root map.
- **Next action:** add independent machine-root/dead-value rejection and
  physical GC retained-capacity evidence for edge pruning; then extend exact
  per-instruction liveness only after validating bounded work and semantics.
  Preserve the source-neutral UIR, previous runtime/profile, ABI and fault
  behavior. No speculative production promotion.
- **This session:** fixed the previous three EOF fixture patch-check errors,
  developed bounded native List edge-root retirement and observer tests, and
  reconciled its focused CI outcome. No U2 merge, closure, full four-platform
  qualification, owned full self-build or restart of paused #51.

Read the governing documents below before design or implementation. The user has
authorized continuing U2; historical stop instructions are superseded. A future
work list alone does not authorize unrelated development.

## Milestone status

| Area | Current disposition |
| --- | --- |
| U1a | Accepted within its documented scalar/SSA/call/Float/provenance/physical boundary; #77 closed, qualified PR #105 merged. |
| U1b | Bounded immutable aggregates/reference linked execution accepted; #73 closed, qualified PR #106 merged. |
| U2 | Implemented partial foundation plus bounded native List-i64 path; #74 OPEN, #111 DRAFT/unmerged; full acceptance outstanding. |
| U3 | Initial isolated Python shadow/planning foundation merged in #119; #75 OPEN. Direct production AST-to-owned-UIR integration remains unfinished. |
| U4 | Initial parallel-move foundation in draft #120; #102 OPEN. Full machine migration remains unfinished. |
| Production | Existing frontend/default compiler and 32-byte ABI retained. Latest recorded qualified production optimization is #110. No redesigned-UIR promotion. |
| Optimization #51 | OPEN / PAUSED. Do not restart its benchmarks or rejected pilots. |
| Full owned-compiler self-build | NOT CERTIFIED; excluded from routine work without explicit authorization. |

U2 code is on its draft branch, not main. Publishing this same recovery document
on main does not merge U2 implementation. Fetch current refs before continuing.

## What U2 currently implements

| Component | Implemented scope and boundary |
| --- | --- |
| Checked continuations | Canonical opcode-46 invokes, versioned FunctionId contracts, edge-only results and typed carried values. |
| Cleanup and owners | Independently verified reverse-cleanup plans, bounded canonical close construction, lexical owner signatures, success-only acquisition and consumption on both close outcomes. Complete resource adapters remain open. |
| Failure contexts | Typed primary/ordered-secondary reference models and semantic matrix; class-5 saved-failure root metadata and bounded native publisher probes. These do not establish complete canonical checked-runtime integration. |
| Liveness | Independently recomputed CFG/SSA plan and publication obligations; the native List-i64 profile now applies verified successor live-in facts to retire dead List roots after edge transfers for <=32 tracked List values. Per-instruction/all-managed-root coverage remains open. |
| Managed types | Owner-scoped Text/List/identity descriptors, copy-versus-alias contracts and typed operation shapes; existing Stage-0/C/owned runtime parity oracle. This is not general canonical managed execution. |
| Native List-i64 | Eristavi-written optional x86-64 adapter for empty/copy/append/replace/count/get/collection, branches/joins/backedges/cyclic transfers; verified successor-edge root retirement now focused-tested for <=32 selected List values. |
| Native boundaries | Managed-registry entry validation, Int/Bool/List runtime descriptor checks, List bounds source name/line/column, independent fixture frame-layout checks, GC/snapshot/reclamation and fault probes. |

The native List profile is capped at **64 blocks, 512 edges, 128 SSA values and
256 instructions**, with seven exact version-one runtime imports and an opaque
structural carrier interpreted only by that legal profile. It is not a general
managed-type encoding or frontend integration.

Single-block roots use last-use clearing. In the closed multi-block List-i64
profile, up to 32 selected List-carrier SSA values now receive independently
verified successor live-in-based dead-root clears **after** simultaneous edge
copies and before the next allocation. Other managed value families are not
classified by this adapter. More than 32 selected List values retain bounded
conservative all-block retention; other boxed values and deaths inside blocks
also remain conservatively rooted. This is not general exact machine root
publication/release. Managed-local promotion, arbitrary runtime/descriptor
compatibility and physical retention bounds are still outstanding.

## Validation and evidence

| Revision / run | Verified result |
| --- | --- |
| `d2a25a82d9d8216f494118b348878e25176903d1` — [hosted #41718084522](https://github.com/eristavi/eristavi-lang/actions/runs/41718084522) | **SUCCESS:** scope/patch check and Linux Clang focused smoke: 92 run, **89 passed, 0 failed, 3 intentional skips**; 382.990 s. Includes List snapshots, loop/backedge, cyclic swap, GC and added edge-clear assembly assertion. Full platform matrix SKIPPED. |
| `5bcaf8533bedc44f0b4689c3d0cbddc2c1fc9ac3` — [hosted #41711062178](https://github.com/eristavi/eristavi-lang/actions/runs/41711062178) | **SUCCESS:** earlier fixture-only EOF repair; scope and focused Linux smoke passed. |
| `c7149aee5102b67b2a68e888776406ea01a0035e` — local coherent smoke | 92 run, **89 passed, 0 failed, 3 intentional opt-in skips**, 255.341 s. Covers CFG List snapshots/cyclic swaps, registry/runtime rejection, bounds origins and existing regressions. |
| Same revision — hosted #41698723325 | **FAILED scope/patch check**; smoke and full matrix skipped. Local success does not override this failure. |
| `2619885a2ff7043dda4080e722ffe31c8806f495` — hosted #41696878635 | Scope and focused Linux smoke SUCCESS; full platform matrix skipped. Earlier single-block native slice only. |

Original implementation source hashes and raw outcomes/logs (unchanged by fixture-formatting repairs):
[JSON](https://github.com/eristavi/eristavi-lang/blob/c7149aee5102b67b2a68e888776406ea01a0035e/docs/evidence/2026-11-03/u2-list-cfg-smoke.json)
and [raw log](https://github.com/eristavi/eristavi-lang/blob/c7149aee5102b67b2a68e888776406ea01a0035e/docs/evidence/2026-11-03/u2-list-cfg-smoke.log).
Exact native scope, algorithms and exclusions:
[List-i64 contract](docs/architecture/UIR_U2_LIST_I64_NATIVE.md) (branch current); the earlier pinned file remains historical evidence.

Three skipped probes are not passes. No full U2 four-platform CI or
completed-batch qualification has passed. Earlier CI #41698723325 failed
only because three fixtures had surplus EOF blank lines; the corrected
fixture revision and subsequent edge-retirement revision both passed hosted
focused smoke. The final 382.990 s smoke is NOT a matched performance
comparison with the previous 255.341 s local run; no whole-compiler speedup
or measured physical retention improvement is claimed. Intermediate failed
candidate CI runs #41714642589/#41715592713/#41716173164/#41716892840
were corrected before final passing revision, and are historical failure
evidence only.

## Remaining U2 acceptance, in order

1. Extend independently verified List edge-root pruning with corruption
   rejection (missing, prematurely cleared, stale/foreign and dead-published
   roots), explicit collection at the destination, and actual retained-owner,
   collector/traffic/RSS evidence; avoid interpreting assembly pattern checks
   as full physical proof. Measure compile/emit overhead on matched inputs.
2. Move from bounded successor-only List root retirement to exact per-instruction
   managed-value publication/release on verified canonical CFG, preserving
   loop/recursion, checked-failure, terminal fault and cleanup boundaries.
   Resolve the current 32-tracked-List-value profile limit deliberately;
   keep conservative fallback until new proof is qualified.
3. Complete general canonical managed representation and eligible-local
   promotion; extend owned execution to Text/Unicode17, nested Lists and identity
   with value-copy/alias guarantees and identity-cycle coverage.
4. Connect complete checked FailureContext and real resource adapters to canonical
   lowering: pending returns, all exits, exactly-once reverse cleanup, stable
   primary and ordered secondary failures, roots through cleanup and recursion.
5. Complete independent behavior/source-origin comparisons, deep/malformed/dead
   CFG cases, cancellation, sanitizer/allocator-refusal and actual owner/traffic/
   RSS/latency evidence under preselected limits.
6. Once coherent acceptance is met, run one exact-head four-platform CI and
   required completed-batch qualification; compare tested/merged trees before
   any U2 merge/closure. Keep #74 OPEN and #111 DRAFT until then.

## Governing documents and recovery

Read this handover, the complete [design philosophy](DESIGN_PHILOSOPHY.md),
[language semantics](LANGUAGE_SEMANTICS.md), applicable locked rules and
[CI qualification policy](CI_QUALIFICATION.md). Follow **Philosophy → Semantics →
Architecture → Implementation**.

Read the typed UIR architecture/U1 contract through [the records index](docs/README.md).
For current U2 branch contracts, use this
[pinned architecture directory](https://github.com/eristavi/eristavi-lang/tree/c7149aee5102b67b2a68e888776406ea01a0035e/docs/architecture):
remaining UIR acceptance, continuations, fallible registry, scoped owners,
multi-close lowering, managed types, canonical root map, failure-root boundary,
native-root publication and initial budget policy. Also read
[cleanup semantics](RESOURCE_CLEANUP.md) and [owned resource runtime](OWNED_RESOURCE_RUNTIME.md).
Dated contracts retain governing decisions; outdated status paragraphs are
superseded by this handover, not permission to repeat completed work.

## Historical recovery records

The full pre-cleanup handover text is retained (terminal blank lines normalized):
[U2 branch snapshot](docs/history/2026-11-03/HANDOVER_BEFORE_CURRENT_ONLY_CLEANUP_U2.md)
and [main snapshot](docs/history/2026-11-03/HANDOVER_BEFORE_CURRENT_ONLY_CLEANUP_MAIN.md).
Exact original bytes remain at U2 revision `c7149aee5102b67b2a68e888776406ea01a0035e`
and main revision `0f7cd0af57777c73686f02b61b7991f68dcc8757`.
Older archives and raw evidence remain in Git. Consult them only for a specific
decision or measurement; old commands, stops, pending notes and “next” sections
are historical, not active instructions.

## Architecture and working boundaries

- Follow **Philosophy → Semantics → Architecture → Implementation**. Complexity
  belongs in the compiler/runtime; preserve a small, readable source language.
- Approved AST plus frozen semantic facts eventually build one source-neutral
  typed UIR directly. No extra mandatory source-close executable Typed IR.
  Preserve old paths and independent oracles until U2/U3/U4 gates pass.
- Independent owned metadata, immutable SSA, explicit effects, fresh all-block
  verification and mandatory eligible-cell promotion remain required. No fake
  Void value, stale verified flag or unchanged revision substitutes for proof.
- Checked signed Int64, strict binary64, value vs identity semantics and
  deterministic scoped resources stay frozen. Normal/checked exits require
  exactly-once reverse cleanup. Standalone terminal defects do not unwind;
  process termination promises no flush/durability or persistent-lock release.
- RevaSM is a peer target, not a compulsory intermediary. Preserve existing
  32-byte ABI boundaries, private-memory and generic compatibility adapters.
  Moving GC, a new address/provenance design, generic-template replacement,
  public UIR serialization/new artifact extensions and FS-001 remain separate
  decisions; do not introduce them as prerequisites or settled policy.
- Use `.eri` for source/implementation and `erist` for the toolchain; `.erist`
  remains reserved. C/Python are bootstrap tools, not intended permanent target
  dependencies. Major layer redesigns require the recorded technical review.
- Work autonomously within authorization, give concise progress updates and
  do not request repeated routine GitHub permission. Do not spawn sub-agents
  without an explicit applicable user/AGENTS.md/skill instruction.

## Standing GitHub authorization — explicit user instruction, 2026-11-01

The repository owner has **explicitly authorized ChatGPT to act on their behalf using the connected GitHub account**, without repeatedly asking permission for routine project work. Treat this as standing authorization for investigating repositories, reading files and issues, creating/editing commits and branches, updating PRs/issues/documentation, running available tests and workflows, and merging/closing completed milestones **when their documented acceptance gates actually pass**. Execute the requested work directly, provide results and evidence, and do not interrupt progress with redundant permission questions. This instruction applies to future Eristavi handovers and working sessions. Connected tool capabilities and service authorization remain binding; do not claim an action succeeded unless verified. Preserve philosophy, frozen semantics, CI/qualification rules, release safety and careful irreversible-action checks. **The standing authorization does not waive acceptance criteria or authorize previously excluded experimental full owned-compiler self-build tests.**

### Standing publication authorization — explicit user confirmation

The user explicitly approved publishing the updated full handover and raw evidence archive to the public `eristavi/eristavi-lang` GitHub repository and instructed: **“yes sure, you always have to do it.”** Treat routine publication of this project's handovers, performance reports, source patches, diagnostic logs, measurement summaries and evidence archives to that same repository as authorized project work. Keep these records current automatically, without repeatedly asking for routine publication permission. This does not authorize unrelated data disclosure, bypass service restrictions or waive correctness, qualification and merge gates.

## Mandatory philosophy-first engineering discipline — standing user instruction

**At the beginning of every new Eristavi chat, and before any material design, implementation, optimization or milestone decision, read and FOLLOW the actual governing project documents. Do not rely on the handover summary, old conversation memory or a milestone checklist as a substitute. This is a permanent user requirement; the user must not need to repeat it.**

1. **Read current sources first:** current `HANDOVER.md` (latest authoritative checkpoint and historical supersession), the **complete `DESIGN_PHILOSOPHY.md`**, `LANGUAGE_SEMANTICS.md`, applicable locked semantics and the relevant current architecture/IR contracts, then `CI_QUALIFICATION.md`. For a status-only request, verify current GitHub/CI/issue facts and describe the extent of the documents actually reviewed; never claim to have read something that was not inspected.
2. **Use the non-negotiable design order:** **Philosophy → Semantics → Architecture → Implementation**. Specify the intended meaning and review architectural consequences *before* choosing an implementation. Implementation convenience cannot weaken or silently redefine frozen semantics.
3. **Preserve the design constitution:** small stable language vocabulary; one obvious, readable, precise way to express fundamental concepts; strong static guarantees with sensible inference; rich libraries instead of unnecessary syntax; automatic safe memory and deterministic scoped cleanup for external resources; explicit low-level danger; excellent diagnostics; and universal portability. **Complexity belongs in the compiler/runtime, not in the programmer's code.** A feature must justify its permanent conceptual cost.
4. **Optimization-first, but never correctness-last:** correctness, safety and locked semantics are absolute gates. After them, execution and compilation speed, bounded physical memory, allocation/GC pressure, predictable work/cancellation and efficient CI are the **highest engineering priorities from initial design onward**. Define representation, algorithmic complexity, ownership/peak/traffic budgets and before/after measurements. Distinguish per-owner physical backing, total allocator traffic and process RSS. Never advertise a microbenchmark or rejected prototype as whole-compiler speedup.
5. **Keep the architecture and compatibility intact:** source-neutral typed Universal IR and independently verified publication; no extra mandatory source-close executable Typed IR; machine- and OS-independent semantics; C/Python as bootstrap tools rather than permanent target dependencies. Preserve the frozen Eristavi source behavior, the existing 32-byte public ABI, fault/source-location and exactly-once cleanup semantics, independent reference oracles, rollback and the default production compiler until the redesigned path passes its own U2/U3/U4 acceptance gates. Avoid speculative whole-compiler rewrites or unapproved new syntax/ABI/artifact formats.
6. **Qualify proportionately:** focused tests, independent positive/negative/oracle checks and resource/fault probes while developing; full four-platform CI and required completed-batch qualification **once per coherent final implementation batch**, never after every helper. Documentation-only changes require a lightweight patch check; never initiate experimental owned full compiler self-build without explicit user authorization. Report `planned`, `implemented`, `tested`, `qualified`, `merged` and `deferred` distinctly.
7. **Carry the rule into every future handover automatically:** each work session must reconcile current decisions and evidence in this document; keep opening instructions, current status and newest recovery checkpoint consistent, including philosophy, locked semantics, performance/CI rules and next actions. If a future handover is edited, **retain this section and propagate its requirements**. Do not make the user remind us to follow the project's philosophy.

## Mandatory handover maintenance — standing user instruction

**HANDOVER.md must stay current at all times. Updating it is part of every
project task, not a separate task that waits for the user to request it.**

- Read the current handover before continuing work. Update it immediately after
  each material implementation change, architectural decision, validation result,
  PR status change, merge, blocker or change to the next step.
- While work is in progress, record the active branch and what is pending.
  Distinguish implemented, tested, qualified and merged states. Never leave
  merged work labelled as a candidate or completed checks labelled pending.
- Keep the opening recovery instructions, current-status table and latest
  checkpoint consistent, with exact relevant commits, test evidence, limitations
  and next actions. Preserve older evidence as clearly superseded history.
- Include the handover update in the working batch and reconcile its final
  merge/qualification status promptly afterward. Before every final user reply
  about project work or session handoff, verify the checkpoint reflects the
  actual state; do not declare the task complete with a stale handover.
- Status-only documentation updates need a lightweight patch check. Reuse valid
  qualification evidence for unchanged implementation; do not rerun expensive
  compiler/runtime tests merely to keep this file current.

## Optimization-first engineering policy — standing user priority

**From this checkpoint onward, treat runtime and compiler performance,
memory/resource efficiency, and predictable compilation times as the
HIGHEST development priorities, after correctness, safety and frozen
language semantics.** Every newly designed or revised compiler/runtime
component must budget algorithmic cost, hot-path allocations, retained
memory, work/GC pressure, cancellation and determinism before adoption.
Do not accumulate avoidable temporary boxes, repeated full-heap passes,
redundant indexing, unbounded caches or unnecessarily expensive CI.

- Preserve the existing frontend, ABI, fault and cleanup order, independent
  acceptance oracles and observable language behavior. Never trade safety
  or correctness for benchmark gains; never skip/delete tests to look faster.
- Establish and retain **before/after** targeted wall/CPU,
  allocation/collection counts, modeled owner capacity/traffic and actual
  physical resource samples, stating attribution and platform limits.
- For incremental changes run the narrowest useful focused tests and
  differential/fault/forced-memory probes; run the complete four-platform
  CI plus required qualification **once per coherent final code batch**.
  Never enable experimental owned compiler full self-build without permission.
- Give priority to existing measured runtime bottlenecks before introducing
  competing optimizations. Prefer bounded, reversible production edits with
  explicit allocation-failure and no-allocation fallback. Resist public
  ABI churn, speculative whole-compiler rewrites and benchmark overclaiming.
- Maintain a ranked optimization backlog and update this handover after
  implementation, qualification, merge or a discovered performance regression.
  An unqualified prototype is not production-ready or a future CI time guarantee.
The separate optimization investigation #51 is currently **PAUSED** by the user.
The policy above continues to govern future design; it does not authorize
restarting paused benchmarks, rejected pilots or the capped compiler workload.

Keep this file current-only: replace superseded status rather than appending
contradictory recovery checkpoints. Move dated history to `docs/history/`,
retain raw evidence and link it. Preserve all standing instructions above.
