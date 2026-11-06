# Eristavi compiler — current handover

Reviewed 6 November 2026 (Asia/Nicosia). Historical checkpoints are evidence,
not instructions to restart completed work. Read the governing documents below
before design or implementation. Continue authorized U2 work without repeating
closed Text/List/cleanup primitives. Optimization #51 remains PAUSED.

## Resume here

**U2 #74 is OPEN; PR #111 is DRAFT/unmerged. The requested completion batch
is NOT finished.** Latest implementation/test checkpoint is
[`50113f7103a0790f83b59475ae3256736c43ebdd`](https://github.com/eristavi/eristavi-lang/commit/50113f7103a0790f83b59475ae3256736c43ebdd),
branch `compiler/u2-cleanup-foundation-20261102`, tree
`fecf6dc5c8b958954b1fa169e8ecbfe9d2728b55`. No production promotion or ABI change.

The new whole-original-Function `emitRecursive` supports **nonfallible self
calls**, using the SAME independently verified canonical SSA/liveness, managed
root vectors and Text/List runtime imports. Each actual recursive native frame
registers its own roots; parent-only values stay live through child collection.
The child publishes up to two managed results into the parent's already bound
temporary roots before retiring its scope; the parent stores canonical result
slots, publishes `liveAfter`, then clears the temporaries. There is no shared
global depth counter or root table. Exact FunctionId/SignatureId, defined kind,
version, effects and nonfallible contract are required before emission.

**Do not confuse this with checked recursion.** The new path still refuses
opcode 46. General nested managed producers/copies and all checked Function
return/handler/cleanup exits remain incomplete. The current canonical set has
an invoke terminator but no general typed function failure-return producer:
finish a coherent verified body/exit contract rather than introducing a hidden
status flag or treating a scalar as a typed failure. Reuse existing ownership,
cleanup plans and class-5 runtime adapters.

Contract, ABI, costs and limits:
[whole-Function managed recursion](docs/architecture/UIR_U2_FUNCTION_MANAGED_RECURSION.md).

## Current validation

| Check | Actual result |
| --- | --- |
| New whole-Function managed/recursive focused CI [#42245608757](https://github.com/eristavi/eristavi-lang/actions/runs/42245608757) | **SUCCESS 7/7**, 76.287 s, exact source `50113f7`. Parent-private Text at recursive depths 0/1/5/32/64, physical collector counts, identity cycle, scalar return, two managed returns at depth 32, post-return Text reclamation, final graph/Text/allocator audit and invalid defined/imported/effects/signature/zero/foreign bindings. Original four tests retained. |
| Existing whole-Function Text/List integration [#42245608781](https://github.com/eristavi/eristavi-lang/actions/runs/42245608781) | **SUCCESS 12/12**, 126.162 s, exact same source. Original Unicode17/List get/replace/copy/loop/bounds/refusal checks retained. |
| Broad Linux Clang smoke [#42245608877](https://github.com/eristavi/eristavi-lang/actions/runs/42245608877) | **SUCCESS 147 run / 144 passed / 0 failed / 3 intentional skips**, 637.800 s, exact same source. Scope/patch SUCCESS; final four-platform matrix SKIPPED. Three skips are not passes; timing is not a paired speedup measurement. |
| Local Linux GCC | Consolidated **7/7 PASS**, 55.714 s; final zero/foreign target cases separately **PASS**, 33.335 s. Stage-0, old C-native and new UIR native independently match the frozen nonfallible recursion corpus. |
| Bootstrap C generators with ASan+UBSan | **SUCCESS 7/7**, 188.653 s, `-O0`, `halt_on_error=1`; leak detection disabled only because LSan cannot inspect sandbox thread state. This does not instrument emitted owned machine code. |
| LeakSanitizer | **BLOCKED/FAILED to initialize**, zero tests executed: cannot open `/proc/11/task`; LSan reports unsupported process inspection. No passing leak-sanitizer evidence. Earlier `-O1` instrumented attempt ended with status 5 and no result/diagnostic; not a pass. |
| Final four-platform CI and completed-batch qualification | **NOT performed**; implementation is not complete. No final labels/ready-for-review/merge selected. |

These are narrow independent recursion/root results, not general U2 physical
RSS/GC-pause/allocator-fault/sanitizer acceptance. Exact source hashes, local raw
outcomes and sanitizer limitations are retained in the
[evidence record](docs/evidence/2026-11-06/u2-managed-function-recursion.md), with
[exact-source hosted test transcripts](docs/evidence/2026-11-06/u2-managed-function-recursion-hosted.md).
The subsequent documentation-only checkpoint leaves implementation/test inputs
byte-identical to `50113f7`; reuse those scoped results, not a new release claim.

## Milestone status

| Area | Current disposition |
| --- | --- |
| U1a | Accepted within documented scalar/SSA/call/Float/provenance/physical boundary; #77 closed, qualified PR #105 merged. |
| U1b | Bounded immutable aggregates/reference linked execution accepted; #73 closed, qualified PR #106 merged. |
| U2 | OPEN / unaccepted. Draft PR #111, latest source `50113f7`; only the bounded scopes below are verified. All eight top-level #74 DoD boxes remain unchecked. |
| U3 | Initial isolated Python shadow/planning foundation merged in #119; #75 OPEN. Direct production AST-to-owned-UIR integration unfinished. |
| U4 | Initial parallel-move foundation in draft #120; #102 OPEN. Full machine migration unfinished. |
| Production | Existing frontend/default compiler and 32-byte ABI retained. Latest recorded qualified production optimization #110. No redesigned-UIR promotion. |
| Optimization #51 | OPEN / PAUSED; do not restart its benchmarks or rejected pilots. |
| Full owned-compiler self-build | NOT CERTIFIED; excluded without explicit authorization. |

## Already implemented — reuse, do not redo

| Component | Verified scope and boundary |
| --- | --- |
| Whole canonical Function scalar CFG | Original Function reverified including dead blocks, simultaneous block arguments, i64/pred operations, branch/switch/backedges/return. Bounded private x86-64 backend. |
| Whole-Function managed roots | Exact per-ValueId `liveEntry/liveBefore/liveAfter`, class-1 Text/List/identity publication/retirement, loops and up to two caller-rooted returns. Now includes explicit nonfallible self calls with private live frames. Still no general constructors, checked calls or cross-function module lowering. |
| Text / Unicode17 | Reused 12 established imports: scalar construction, immutable concat/copy/equality, explicit views/counts/indexes, NFC and collection; mixed Text/List loops. Frozen Unicode17 remains unchanged. |
| List<i64> | Original empty/copy/append/count/get/replace/collect in whole-Function lowering with rooted intermediate snapshot/int boxes and exact original source/LocId bounds faults; GET/REPLACE negative and end bounds independently checked. Nested/non-i64 managed producers remain OPEN. |
| Checked SSA / File owners | Canonical opcode-46 normal/failure typed edges; exact carried SSA; owner prefixes; reverse exactly-once File closes; class-5 primary/ordered-secondary failures; bounded two-stage native chain at prior `be138658`, focused 8/8 and broad 141/144 pass (3 skips). This is still separate adapters, not general whole-Function opcode-46 dispatch. |
| Runtime failure recursion | Existing bounded recursive File runtime/cleanup probes and typed Unicode17 reference contexts. New nonfallible whole-Function recursion does not qualify recursive checked calls or complete FailureContext producers. |
| Negative/physical checks | Descriptor/effects/revision/dead-block/root/GC/identity cycles and selected binding failures. Do not extrapolate these to every stale/foreign/dead machine-root or combined allocator/RSS/pause condition. |

## Remaining work before #74 can close

1. Establish a coherent canonical defined-Function checked body/return contract
   and complete opcode-46 native normal/failure/handler dispatch. Integrate
   existing owner proof, reverse cleanup, pending returns and class-5 contexts
   on all exits, including genuine recursive checked calls. Nonfallible self
   recursion is now a verified root-frame building block, not this completion.
2. Generalize typed native managed representation/constructors, nested List
   elements and managed aggregate make/get/set/copy while preserving ordinary
   value snapshots versus explicit shared identity. The boxed ingress profile
   does not manufacture or prove arbitrary nested producers.
3. Finish automatic class-1/class-5 live-root publication/retirement across
   those combined checked, recursive and cleanup paths, with missing,
   prematurely retired, stale, foreign, dead-published and invalid-owner refusal.
4. Complete independent Stage-0/current-native/new-native outcome/source-origin
   comparisons and deep owner/allocator-fault/physical backing/traffic/RSS/
   collector pause/sanitizer evidence under preselected budgets. Bootstrap C
   sanitizer success alone does not cover owned assembly or close this gate.
5. Reconcile the draft with current main before selecting final acceptance.
   A read-only `git merge-tree --write-tree --name-only origin/main 50113f7`
   reports conflicts in `HANDOVER.md` and
   `docs/architecture/UIR_U2_CHECKED_CHAIN_AND_RECURSIVE_FAILURE.md` (main
   has an older copy of the latter). No merge or conflict resolution is claimed.
   Then run one coherent exact-head four-platform full CI and required
   completed-batch qualification; verify tested and merged trees before any
   merge/closure. Keep #111 DRAFT and #74 OPEN until all acceptance gates pass.

## Governing documents and recovery

Read this handover, the complete [design philosophy](DESIGN_PHILOSOPHY.md),
[language semantics](LANGUAGE_SEMANTICS.md), applicable locked rules and
[CI qualification policy](CI_QUALIFICATION.md). Follow **Philosophy → Semantics →
Architecture → Implementation**.

Read the typed UIR architecture/U1 contract through [the records index](docs/README.md).
For current U2 branch contracts, use the current [architecture directory](docs/architecture):
remaining UIR acceptance, continuations, fallible registry, scoped owners,
multi-close lowering, managed types, canonical root map, failure-root boundary,
native-root publication and initial budget policy. Also read
[cleanup semantics](RESOURCE_CLEANUP.md) and [owned resource runtime](OWNED_RESOURCE_RUNTIME.md).
Dated contracts retain governing decisions; outdated status paragraphs are
superseded by this handover, not permission to repeat completed work.

## Historical recovery records

The latest pre-consolidation status is archived in
[6 November recovery snapshot](docs/history/2026-11-06/HANDOVER_BEFORE_MANAGED_RECURSION_CHECKPOINT.md).
It is historical, including pending checks superseded by the checkpoint above.

Older pre-cleanup handover text is retained (terminal blank lines normalized):
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
