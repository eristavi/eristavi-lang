# Eristavi compiler — current handover

Updated 7 November 2026 (Asia/Nicosia). Active branch:
`compiler/u2-whole-function-file-roots-20261107`, draft PR #121 targeting
`compiler/u2-cleanup-foundation-20261102` (draft #111). Issue #74 remains OPEN.
Tested implementation commit: `2f5065cb32755e8560da4340852c25dc3610224f`.
This documentation successor changes no implementation or test input.
Baseline head: `0263208d7168b9a2a2365f7f105749df6a980ea7`.
**Latest implementation: explicit primary cleanup binding extracted.**
`u2_checked_chain_verify.verifyPrimary` independently verifies one original
already-failing File.close with exact primary/owner/pending block parameters,
failed-entry cleanup Plan, primary transport on both outcomes, separate new
failure and its class-5 root. Existing full chain verification delegates to it;
no SSA-liveness inference or alternate executable IR is introduced.
Native prefix/dispatch tests **2/2 PASS**, 9.153 s, including normal-mode Plan
refusal, restored binding and existing malformed-primary/native failure-order,
forced-GC and consumption scenarios. Raw `primary-binding.log` is committed.

**Remaining:** this is a reusable verified admission boundary, not completed
general whole-Function primary composition. Next connect its exact report to
`u2_function_managed_x86_64` File emission, preserving the distinct new close
outcome and carried original primary; then admit nested surviving prefixes.
Do not remove current general-emitter refusal until native integration passes.
Source base: `6926f825d8873ec55bd4ef88ea4173ee1249ade2` (timeout fix).

**Current checkpoint: owned File generator timeout RESOLVED locally.**
The initial managed Plan was discarded before constructing the File-extended
Plan. Diagnostic trace measured **17.711 s** in that redundant first Plan;
mandatory publication verification took **36.109 s** and remains intact.
Descriptor admission now returns selected types separately; File emission
constructs one SSA Plan. Legacy create still performs the same admission and
Plan creation. Full independent publication and lexical owner proofs remain.

Uninstrumented owned generator: **105.651 s**, unchanged 120-second watchdog;
byte-identical owned/C assembly, static-link audits and generated File success/
close-failure execution PASS. Full File class **5/5 PASS**, 164.210 s; shared
managed/checked-recursive regressions **2/2 PASS**, 14.333 s.
Baseline traced run timed out at 120 s. These are targeted measurements,
not five paired timings, RSS/GC-pause or whole-compiler performance evidence.
See `owned-baseline-trace.log`, `owned-fixed.log` and `plan-regressions.log`
in the batch evidence folder. No timeout or assertion was weakened.

Next resume explicit checked-chain primary binding and failure composition,
then nested surviving prefixes; full File integration remains incomplete.
Implementation base is `71436a23c0dd315d765ee8d5e4837b4d97d5d8c5`;
this successor contains the measured fix. Prior evidence below is historical.
**Final focused validation: 8/8 PASS, 0 failed, 0 skipped, 69.823 seconds.**
The command, source hashes and raw log are recorded in
[the batch evidence](docs/evidence/2026-11-07/u2-file-function/README.md).
No merge, production promotion, final four-platform qualification, #51 work,
or experimental owned full-compiler self-build is authorized by this checkpoint.

## Current File implementation and recovery

The general whole-Function emitter now has an opt-in `emitFileChecked` entry.
Actual original opcode-46 File.openRead/close calls select original typed edges;
acquisition is immediately rooted, checked close consumes the original SSA and
lexical root on both outcomes, and pending scalar success is cancelled on close
failure. Handler recovery, class-1/class-5 forced-GC roots and final reclamation
are exercised by compiler-generated execution. Existing independent owners,
SSA publication, native resource adapters and the 32-byte public ABI are reused.

**Bounded, not full integration:** one lexical owner only. Nested owners,
surviving prefixes, active-primary/ordered-secondary composition and File-owning
recursive/group calls remain refused. General all-exit acceptance, deeper
foreign/stale root and physical/sanitizer evidence, main reconciliation and final
four-platform/completed-batch qualification remain open. Do not repeat completed
checked-group work or the single-owner open/close slice.

**Exact next implementation step:** extend File close emission to consume the
original active FailureContext through the existing verified suffix-cleanup
infrastructure, proving primary preservation and ordered secondary failures;
then admit nested owners/surviving prefixes. Retain current refusal gates until
each combination has native positive/negative evidence.

Previous smoke [#42360813812](https://github.com/eristavi/eristavi-lang/actions/runs/42360813812)
on `8104d8e8b1819765addab4fde3854fd37ccd81b2` is now confirmed SUCCESS:
**171 run / 168 passed / 0 failed / 3 intentional skips**, 1611.120 seconds.
Scope/patch passed; the four-platform matrix was skipped. No newer branch run
was present at initial inspection. This verifies the prior foundation, not the
new integration. Earlier failed attempts and exact focused fix evidence remain
in [the historical checkpoint](docs/history/2026-11-07/file-roots-before-function-integration.md).

The current batch's broader Linux smoke, owned/C generator parity and final
qualification are deliberately not initiated locally to protect the usage
budget. Any automatically triggered hosted smoke must be reported separately
and must not be assumed successful. All standing instructions below continue.

## Latest verified development checkpoint — 7 November 2026

**Checked calls between different defined Functions and mutual recursion are
implemented and focused-tested within the existing bounded native profile.**
`emitCheckedGroup` resolves original opcode-46 FunctionIds to exact bound bodies;
different normal signatures and caller-rooted managed/failure results reuse the
existing canonical CFG, SSA and owned runtime. This does not complete all U2.

[Focused run #42349932276](https://github.com/eristavi/eristavi-lang/actions/runs/42349932276)
**29/29 PASS**, 651.252 s, on exact checkpoint `43d56f2`, plus word-path
prerequisite **1/1 PASS**. The 11 new group methods cover mutual depths
0/1/5/32/64 under forced GC, cross-member recovery, swapped normal result layouts,
two managed results, List snapshot independence, complete ordered saved failure
context, missing sibling roots, 14 target/type/count/dead-origin refusals, later-
member budget-refusal cleanup and actual stack measurements. Independent frozen
mutual source compares Stage-0/current C-native/new native outcomes.

Uninstrumented owned/C generators emit **byte-identical assembly**; static ELF,
no loader/undefined symbols/non-executable stack and native normal/failure
execution all pass. Existing self-recursive generator: **103.728 s**; new direct
group generator: **101.624 s**, both within unchanged **120 s** watchdog. The direct
fixture retains the established scalar edge specialization needed by bootstrap C;
its C build runs first to fail fast. No test was removed or timeout raised.

[Linux smoke #42349932257](https://github.com/eristavi/eristavi-lang/actions/runs/42349932257)
**170 run / 167 passed / 0 failed / 3 intentional opt-in skips**, 850.922 s,
on exact checkpoint `43d56f2`; scope/patch SUCCESS. Full four-platform matrix
SKIPPED, not qualified. Both generators also passed within the unchanged watchdog
in this smoke (legacy 78.363 s, group 74.805 s). No full completed-batch release
qualification, production promotion or merge is claimed.

Bootstrap C ASan/UBSan: **4/4 selected methods PASS**, 84.670 s, plus corrected
C direct-generator probe PASS; `-O0`, halt-on-error, `detect_leaks=0`. This does
not sanitize emitted assembly or qualify LSan. Actual mutual-fixture Function
stack: **592 bytes/frame**, 38,480 bytes at depth 64; excludes runtime/collector
helper stack and RSS. Native post-scope reclamation and existing charged-owner
work/capacity refusal checks pass. Local owned generator watchdogs also fail on
unchanged prior `6fe0024`; retained diagnostic failures are not green evidence.
Hosted exact-source runs above are the recorded development gate.

The group is capped at **16 members / 1024 total SSA values / 2048 instructions**;
existing per-body 8-input/2-result/64-root/64-block/256-value/512-instruction limits
remain. Initial checked groups use the caller's one exact saved-context failure
carrier. Other call combinations, new failure construction, nested producers and
full File owner/cleanup integration remain open. Plans are privately retained
only for this bounded transaction, remain charged to their owners and are freshly
rederived/compared by full `ssa.verifyPublications` before each body's output.
All retained Plans/phases close on completion and any later-member refusal.
No cached verified flag, new IR layer, public ABI or production default change.

**Next step — do not repeat the completed call-group work:** integrate original
whole-Function File acquisition/consumption, owner proof, reverse exactly-once
cleanup, pending returns and every normal/checked/handler exit. Complete the
remaining call combinations and managed/failure constructors, combined roots,
independent/physical/fault evidence; reconcile main and perform final exact-source
four-platform/completed-batch qualification only for the coherent finished U2.
Keep #111 DRAFT and #74 OPEN until all eight DoD gates pass. No justified U2 %.

[Contract](docs/architecture/UIR_U2_CHECKED_CALL_GROUPS.md) ·
[Raw evidence, input hashes and limits](docs/evidence/2026-11-07/u2-checked-groups/README.md) ·
[Superseded development checkpoints](docs/history/2026-11-07/u2-checked-group-development.md).
The user required this batch to stay within a five-hour session budget. Do not
run experimental full owned-compiler self-builds; separate #51 remains paused.

## Implemented scope — reuse rather than repeat

| Component | Current boundary |
| --- | --- |
| Canonical scalar CFG | Original Function reverified including dead blocks, simultaneous block arguments, i64/pred, branch/switch/backedges/return; bounded private x86-64 backend. |
| Managed roots and calls | Exact per-ValueId entry/before/after liveness; class-1 Text/List/identity, loops, nonfallible self calls and up to two caller-rooted results. Checked `emitCheckedGroup` adds exact different/mutually recursive defined targets, original normal/failure edges, negative outcome ordinals/carried SSA and class-5 saved contexts. Child publishes into registered caller roots before scope retirement. Other call combinations/full File integration remain open. |
| Checked return contract | `u2_function_contract.eri` binds exact frozen FunctionId/signatures; optional opcode 47 `return.failure`. Fresh verifier checks binding/type/arity/attributes/origin, including dead blocks; legacy profiles refuse it. Scoped owners must be empty on both return kinds. Zero, one and two normal results supported; no fake Void SSA. |
| Text / Unicode17 | Established 12 imports: scalar construction, immutable concat/copy/equality, views/counts/indexes, NFC and collection; mixed Text/List loops. Unicode17 remains frozen. |
| List<i64> | Empty/copy/append/count/get/replace/collect with rooted snapshots/boxes and original source/LocId bounds faults, including negative/end bounds. Nested/non-i64 producers remain open. |
| File cleanup / failures | Checked typed edges, owner prefixes, reverse exactly-once closes, primary/ordered-secondary failure roots; bounded two-stage native chain and recursive runtime probes. Single-owner File.openRead/close now runs in whole-Function CFG through emitFileChecked; nested composition and owned recursive/group integration remain open. Whole-Function checked recursion propagates existing saved contexts. |
| Private physical schema | Function gained `definedTarget` (default zero): **18** owned graph cells, previously 17. Physical observer and independent pin updated; capacity/traffic budgets unchanged. |
| Publication proof | `ssa.verifyPublications` freshly verifies the full plan and all ordered IDs/entry/before/after bits, including dead code, before each body's output. Checked groups reuse private immutable Plans within one bounded transaction, never a verified flag. Derived plans close on comparison-work refusal; all group Plans/phases close on any failure. |

Contracts: [checked Function returns](docs/architecture/UIR_U2_CHECKED_FUNCTION_RETURNS.md),
[managed recursion](docs/architecture/UIR_U2_FUNCTION_MANAGED_RECURSION.md).

## Evidence and limits

The current 7 November gate is recorded above and in the linked checked-group
report. The scoped 6 November records below are historical inputs, not automatic
qualification of later changes.

[Raw logs and source hashes](docs/evidence/2026-11-06/u2-checked-function-stop-checkpoint.md)
retain detailed measurements and earlier failed attempts. Never treat older passes
as validation of later implementation changes.

| Evidence | Result and scope |
| --- | --- |
| Checked + existing managed tests, before publication batching | **16/16 pass**, 193.818 s: checked recursion depths 0/1/5/32/64, handler recovery, zero/scalar/two-managed returns, primary + two ordered secondary failures, malformed/dead returns/ordinals, legacy and missing-payload/handoff refusal; narrow Stage-0/old-C/new-native comparison. |
| Bootstrap C ASan/UBSan, before batching | **9/9 pass**, 298.642 s, `-O0`, `halt_on_error=1`, `detect_leaks=0`. LSan unavailable due to thread-inspection restrictions. Does not sanitize emitted owned assembly. |
| Owner physical/foundation/cleanup guards | **5/5 pass**, 52.557 s; actual backing/traffic/reclamation, 18-field schema and cleanup bypass refusal. Relevant builder/observer source unchanged since that run. |
| Publication corruption/refusal matrix after batching/fix | **1/1 pass**, 10.573 s: duplicate/foreign IDs, missing/dead/nonbinary flags, dead-entry corruption, forged backing, stale revision, extra rows and budget-refusal reclamation. Existing public SSA liveness negative also passed. |
| Owned/C comparison | **PASS on `4b71966`**: full focused **18/18**, 98.399 s generator (120 s limit), byte-identical C/owned assembly, static ELF checks and depth-32 checked recursion/GC, [#42272620378](https://github.com/eristavi/eristavi-lang/actions/runs/42272620378). |
| 6 November Linux smoke | **`4b71966` 159 run / 156 pass / 0 fail / 3 skips**, [#42272620164](https://github.com/eristavi/eristavi-lang/actions/runs/42272620164); full cross-platform matrix intentionally skipped. |
| Final acceptance | Four-platform full CI and completed-batch qualification **not performed** for current implementation. No merge, production promotion or public 32-byte ABI change. |

## Remaining before #74 can close

1. Reuse the tested checked-group implementation; extend remaining call
   combinations outside this profile (including nonfallible helper targets and
   mixed failure carriers as required), and integrate File acquisition/consumption,
   owner proof, reverse cleanup, pending returns and all handler exits in original
   whole-Function lowering.
2. Generalize typed managed constructors, nested List elements and aggregate
   make/get/set/copy, preserving ordinary snapshots versus explicit shared identity;
   construct new typed FailureContexts. Boxed ingress alone is insufficient.
3. Complete combined class-1/class-5 root publication/retirement with missing,
   early-retired, stale, foreign, dead-published and invalid-owner refusal.
4. Complete broad independent Stage-0/current-native/new-native outcomes and
   source-origin comparisons; deep allocator-fault, owner backing/traffic, RSS,
   GC pause and sanitizer evidence under preselected budgets.
5. Reconcile current main, then qualify one coherent final revision on all four
   platforms plus required completed-batch gates. Earlier merge inspection at
   `50113f7` found conflicts in `HANDOVER.md` and
   `docs/architecture/UIR_U2_CHECKED_CHAIN_AND_RECURSIVE_FAILURE.md`; recheck current
   heads. Verify tested/merged tree equality. Keep #111 DRAFT and #74 OPEN until
   every acceptance gate passes; all eight top-level DoD boxes remain unchecked
   in the latest recorded issue audit.

## Project status

| Area | Disposition |
| --- | --- |
| U1a | Accepted within documented scalar/SSA/call/Float/provenance/physical scope; #77 closed, PR #105 merged. |
| U1b | Bounded immutable aggregates/reference linked execution accepted; #73 closed, PR #106 merged. |
| U2 | Checked defined-call groups/mutual recursion focused and Linux smoke green. Remaining resource/managed semantics, deep proof and final qualification unaccepted; #74 open, #111 draft. |
| U3 | Isolated Python shadow/planning foundation merged in #119; #75 open; production AST-to-owned-UIR integration unfinished. |
| U4 | Initial parallel-move foundation in draft #120; #102 open; machine migration unfinished. |
| Production | Existing frontend/default compiler and 32-byte ABI retained; latest recorded qualified optimization #110. |
| Optimization #51 / full owned self-build | #51 paused. Full owned-compiler self-build not certified and excluded without explicit authorization. |

## Governing documents and historical recovery

Read this handover, the complete [design philosophy](DESIGN_PHILOSOPHY.md),
[language semantics](LANGUAGE_SEMANTICS.md), applicable locked rules and
[CI qualification policy](CI_QUALIFICATION.md). Use the [records index](docs/README.md)
and current [architecture contracts](docs/architecture), including UIR acceptance,
continuations, fallible registry, scoped owners/multi-close, managed types, canonical
root map, failure roots/native publication and budgets. Also read
[cleanup semantics](RESOURCE_CLEANUP.md) and [owned runtime](OWNED_RESOURCE_RUNTIME.md).
Dated contracts retain governing decisions; superseded status is not active work.

The [full pre-cleanup handover](https://github.com/eristavi/eristavi-lang/blob/e40a64b3c8b7774dc68d3220f6b208ee38854ca6/HANDOVER.md)
and `3100dc8` preserve all removed chronology. Earlier snapshots remain in
[6 November history](docs/history/2026-11-06) and [3 November history](docs/history/2026-11-03).
Consult history for specific decisions/evidence, not old stops or next-step lists.

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

## Publication patch-check correction

Automatic [CI #42397322506](https://github.com/eristavi/eristavi-lang/actions/runs/42397322506)
on documentation head `5329f323952e0ed62cff8af2d5f3482eb104a800` failed the
scope/patch job on an extra blank line at EOF in the newly archived historical
handover. Smoke and matrix were skipped, not failed compiler tests. The archive
newline is corrected in this documentation-only successor; source/test hashes
and the 8/8 local result are unchanged. The full staged patch is checked against
the parent PR branch, including added files. Hosted rerun remains unqualified.
