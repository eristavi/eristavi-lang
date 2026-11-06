# Eristavi compiler — active U2 continuation

6 November 2026 (Asia/Nicosia). **Resumed at the user's explicit request** from
the saved five-hour-limit stop checkpoint `3100dc8`. Optimization #51 stays PAUSED.

### Current diagnostic — narrow, not qualification

The owned-versus-C source generator comparison remains the first blocker.
This continuation adds **test-only**, identical GAS-comment phase markers
to both generator inputs, plus partial-stdout phase extraction on the existing
120-second owned-generator timeout. It changes no compiler implementation,
source-language semantics, 32-byte public ABI, U2 gate, or watchdog threshold.
This is diagnostic evidence only; **do not mark the latest code green** until
the watchdog and exact-source validation pass. The previous unqualified
implementation stop checkpoint and detailed recovery instructions follow.

## Exact recovery point

Branch: `compiler/u2-cleanup-foundation-20261102`, draft
[PR #111](https://github.com/eristavi/eristavi-lang/pull/111).
The original unqualified stop checkpoint is `3100dc8e82f8e496d61fd38d0cdab5311416bd36`
(parent `2bb0c01b54b894f9de813078d0c4a70e150110c5`).
The active diagnostic continuation builds on it and is likewise **work in
progress, NOT qualified or merged**.
After the initial automatic approval rejection, Revaz explicitly requested
publication of the local code to GitHub for continuation from another session.
This checkpoint therefore includes the code, tests and evidence described below.
It is intentionally published with `[skip ci]` at the user's stop request,
so saving this work does not launch another expensive CI run. **This is not a
waiver: the new source has no passing hosted CI or final qualification.**

#74 stays OPEN; #111 stays DRAFT. No production promotion, public 32-byte ABI
change, full four-platform run, completed-batch qualification or merge occurred.

## What is implemented in this checkpoint

- New `src/compiler/u2_function_contract.eri`: bind a canonical defined fallible
  Function to its exact frozen FunctionId/signatures and construct private
  canonical opcode 47 `return.failure`. `Function.definedTarget` is zero by
  default; legacy verifiers reject the optional bound failure-return profile.
  The independent verifier checks payload type, binding, attributes, result
  arity, source origin and dead blocks; the owner verifier requires empty
  owner state on normal **and** failed returns.
- Existing `u2_function_managed_x86_64.eri` now has `emitChecked`, with genuine
  canonical opcode-46 **self** calls, normal/failure CFG routing, exact negative
  outcome ordinals and carried SSA. It reuses `u2_root_map.create/verify` and
  independently checked SSA liveness. Class-1 managed and class-5 saved-failure
  roots are automatic per frame. A child publishes normal results or the
  failure context into registered caller roots before its scope retires.
  Zero, one and two normal results are supported; no fake no-value SSA result.
- Tests cover parent-only Text through checked recursion at depths
  0/1/5/32/64, handler recovery, zero/scalar/two-managed results, original
  primary plus two ordered secondary failures at depth 64, malformed/dead
  returns/ordinals, legacy refusal, and terminal refusal of missing failure
  payload/handoff storage. A separate source corpus compares Stage-0,
  old C-native and generated native outcomes.
- The private Function gained one field (17 -> 18 owned graph cells). Its
  physical observer and independent schema pin were updated. Existing
  capacity/traffic budgets were NOT raised.
- **Latest, not yet fully requalified change:** the owned-runtime generator
  timed out, and the emitter was found to reconstruct full liveness twice
  per instruction. It now calls new `ssa.verifyPublications` once for a whole
  publication product. That API freshly verifies the complete plan, then checks
  every ordered ValueId and entry/before/after bit, including unreachable code.
  Public `requirePublished` remains unchanged. No trusted verification flag or
  alternate executable IR was introduced. `ssa.verify` also now closes its
  derived plan if comparison work refuses. This changed source AFTER the
  16-test and 9-test sanitizer runs below; do not call those exact-head passes.

Design: [checked Function returns](docs/architecture/UIR_U2_CHECKED_FUNCTION_RETURNS.md).
Recovery evidence: [raw logs and source hashes](docs/evidence/2026-11-06/u2-checked-function-stop-checkpoint.md).

## Tests actually observed — distinguish revisions/scopes

| Check | Observed result |
| --- | --- |
| Checked features + old managed Function tests, BEFORE whole-publication batching | **16/16 PASS**, 193.818 s. Includes 9 new checked methods and 7 existing managed methods. |
| Bootstrap C ASan/UBSan, BEFORE batching | **9/9 PASS**, 298.642 s, `-O0`, `halt_on_error=1`, `detect_leaks=0` because the earlier environment could not initialize LSan. This does NOT sanitize emitted owned assembly. |
| Targeted owner physical/foundation/cleanup guard tests | **5/5 PASS**, 52.557 s. Actual native owner backing/traffic/reclamation, 18-field observer, opcode categories and cleanup bypass refusal. Relevant builder/observer code is unchanged since this run. |
| Earlier checked/root/registry focused group | **12 run / 11 pass / 1 existing opt-in skip**, 101.174 s; before the later arity/publication additions. |
| New publication matrix AFTER batching and derived-plan cleanup fix | **1/1 PASS**, 10.573 s. Rejects duplicate/foreign IDs, missing/dead/non-binary flags, unreachable-entry corruption, forged plan backing, stale revision, extra rows; restored proof succeeds. Work refusal closes backing and returns owner live/pending accounting to baseline. |
| Existing public SSA liveness negative test after batching | PASSED in its focused run; the companion new matrix initially failed only from a test local named `dead` shadowing the fixture block, then was corrected and separately passed. |
| Owned-vs-C source code-generator comparison | **UNQUALIFIED / FAILING watchdog**. Initial small-probe 20 s timeout, then 120 s timeout; the first batched attempt also exceeded 120 s (test elapsed 152.077 s including setup). No matching generated assembly or passing owned-generator result has been observed. Keep this test; do not delete/skip it or silently increase the gate. |
| Diagnostic sample | At a 20 s diagnostic stop, stdout was still empty (emission not yet reached). Local `ptrace` sampling failed with EPERM; its child was killed in cleanup. No profiling success or hotspot timing is claimed. |
| New hosted CI / full platforms / completed-batch qualification | **NOT RUN** for this checkpoint. Saving at the user's requested stop uses `[skip ci]`; all acceptance gates remain open. |

The last published GREEN implementation remains `50113f7`, with Linux smoke
[#42245608877](https://github.com/eristavi/eristavi-lang/actions/runs/42245608877)
147 run / 144 pass / 0 fail / 3 skips. Its results **do not qualify this WIP**.

## Start here on the next continuation

1. Read this checkpoint and the checked-return contract. Do not repeat the
   already implemented Text/List imports, nonfallible recursion, typed return
   opcode or successful checked native cases.
2. Resolve the **owned source-generator execution** watchdog failure first:

   ```sh
   PYTHONPATH=tests:. python -u -m unittest -v test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_owned_and_c_bootstrap_generators_emit_identical_checked_function
   ```

   The test builds the individual Eristavi fixture/code generator through the
   existing frontend, links it to the owned resource runtime, and requires its
   output to equal the C-bootstrap generator byte-for-byte. It then executes
   that checked Function at depth 32. This is **not** an owned compiler
   self-build. The native generator gate is 120 seconds, with static ELF,
   no-undefined-symbol, no-loader and non-executable-stack checks retained.
   Instrument phase boundaries/counters in an isolated diagnostic copy to
   locate time spent before output. Repeated per-instruction full verification
   was removed, but that change alone did NOT produce an observed passing run.
   Do not assume the bottleneck is now solved; do not claim a speedup from
   censored runs. `ptrace` is unavailable in this environment. Do not restart
   unrelated paused #51 work or excluded full owned compiler self-builds.
3. Once that gate is resolved, run the coherent current checked class (now
   **11 methods**, including the added owned comparison and publication matrix)
   plus the old managed class (7), and the existing Text/List integration (12).
   Rerun relevant ASan/UBSan for changed bootstrap inputs, preserving the LSan
   limitation. Reuse unchanged physical evidence appropriately; never silently
   restore the old 17-field physical pin.
4. Run current SSA/checked/owner/registry negatives, then one focused hosted
   smoke for the coherent corrected revision. The smoke manifest and managed
   focused workflow already include the new class; an ordinary code push
   without `[skip ci]` triggers them. No prior green source qualifies this WIP.
5. Remaining full #74 work is still required: arbitrary nested managed
   representation/producers/copies; new typed FailureContext construction;
   arbitrary/mutually recursive targets and whole-Function File acquisition,
   reverse cleanup and all handler exits; comprehensive stale/foreign/dead/
   missing-root and allocator fault tests; owner/traffic/RSS/GC pause evidence;
   broad independent comparisons; main conflict reconciliation; then exact-head
   four-platform CI and completed-batch qualification. Keep #74 OPEN and #111
   DRAFT until those actual gates pass.

## Milestone status

| Area | Current disposition |
| --- | --- |
| U1a | Accepted within documented scalar/SSA/call/Float/provenance/physical boundary; #77 closed, qualified PR #105 merged. |
| U1b | Bounded immutable aggregates/reference linked execution accepted; #73 closed, qualified PR #106 merged. |
| U2 | OPEN / unaccepted. Draft PR #111; STOPPED unqualified checked Function-return/self-invoke WIP described above. Last published green source `50113f7`. All eight top-level #74 DoD boxes remain unchecked. |
| U3 | Initial isolated Python shadow/planning foundation merged in #119; #75 OPEN. Direct production AST-to-owned-UIR integration unfinished. |
| U4 | Initial parallel-move foundation in draft #120; #102 OPEN. Full machine migration unfinished. |
| Production | Existing frontend/default compiler and 32-byte ABI retained. Latest recorded qualified production optimization #110. No redesigned-UIR promotion. |
| Optimization #51 | OPEN / PAUSED; do not restart its benchmarks or rejected pilots. |
| Full owned-compiler self-build | NOT CERTIFIED; excluded without explicit authorization. |

## Already implemented — reuse, do not redo

| Component | Verified scope and boundary |
| --- | --- |
| Whole canonical Function scalar CFG | Original Function reverified including dead blocks, simultaneous block arguments, i64/pred operations, branch/switch/backedges/return. Bounded private x86-64 backend. |
| Whole-Function managed roots | Exact per-ValueId `liveEntry/liveBefore/liveAfter`, class-1 Text/List/identity publication/retirement, loops and up to two caller-rooted returns. Now includes nonfallible self calls plus the working checked self-invoke profile with class-5 contexts. Still no general constructors, arbitrary imported/resource checked calls or cross-function module lowering. |
| Text / Unicode17 | Reused 12 established imports: scalar construction, immutable concat/copy/equality, explicit views/counts/indexes, NFC and collection; mixed Text/List loops. Frozen Unicode17 remains unchanged. |
| List<i64> | Original empty/copy/append/count/get/replace/collect in whole-Function lowering with rooted intermediate snapshot/int boxes and exact original source/LocId bounds faults; GET/REPLACE negative and end bounds independently checked. Nested/non-i64 managed producers remain OPEN. |
| Checked SSA / File owners | Canonical opcode-46 normal/failure typed edges; exact carried SSA; owner prefixes; reverse exactly-once File closes; class-5 primary/ordered-secondary failures; bounded two-stage native chain at prior `be138658`, focused 8/8 and broad 141/144 pass (3 skips). The File cleanup path is still separate adapters. The new whole-Function checked dispatcher currently admits its own defined self target, not File imports. |
| Runtime failure recursion | Existing bounded recursive File runtime/cleanup probes and typed Unicode17 reference contexts. The active checked whole-Function profile now propagates saved primary/ordered-secondary contexts across real recursive frames. Arbitrary FailureContext producers and complete resource/handler integration remain OPEN. |
| Negative/physical checks | Descriptor/effects/revision/dead-block/root/GC/identity cycles and selected binding failures. Do not extrapolate these to every stale/foreign/dead machine-root or combined allocator/RSS/pause condition. |

## Remaining work before #74 can close

1. Finish qualification of the active canonical checked body/return and native
   self-invoke implementation. Then extend beyond that defined-self profile to
   arbitrary targets and existing File acquisition/consumption, owner proof,
   reverse cleanup, pending returns and all handlers/exits. The new self-recursive
   checked implementation does not by itself qualify complete U2 resource lowering.
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
