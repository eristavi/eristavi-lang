# Eristavi compiler — current handover

Updated 6 November 2026 (Asia/Nicosia). Active incremental U2 performance/verification work.
Branch: `compiler/u2-cleanup-foundation-20261102`; [PR #111](https://github.com/eristavi/eristavi-lang/pull/111) remains DRAFT; #74 remains OPEN.
Original checked-return checkpoint: `3100dc8e82f8e496d61fd38d0cdab5311416bd36`.
Latest prior implementation: `e40a64b3c8b7774dc68d3220f6b208ee38854ca6`; diagnostic fix `ac475bb71e0a78808eb08c450895edaaa0442ca9`.
The current independent-verifier batching candidate is in this containing commit (not yet qualified).
Current development is not qualified or merged. Optimization #51 remains PAUSED.

## Current blocker and next action

The owned-versus-C source-generator comparison exceeds its **120-second**
watchdog. Hosted diagnostic [#42259784644](https://github.com/eristavi/eristavi-lang/actions/runs/42259784644)
passed **17/18 tests**; the remaining test timed out after markers `begin`,
`metadata`, `function`, `native-phase`, `native-emit`. The stall is inside
`native.emitChecked`, after metadata/Function construction.

The second hosted test-only diagnostic
[#42260926729](https://github.com/eristavi/eristavi-lang/actions/runs/42260926729)
also passed **17/18 tests** and stopped after `U2_NATIVE_TRACE:publication-build`
but before `U2_NATIVE_TRACE:publication-verify`. SSA verification, metadata,
exact canonical snapshots and checked admission completed: root-publication
construction is the first observed hang. Identical GAS-comment instrumentation
runs in isolated compiler copies for C and owned generators.

**Exact `e40a64b` hosted check:** [Text/List integration #42262075150](https://github.com/eristavi/eristavi-lang/actions/runs/42262075150)
**12/12 PASS**. [Managed focused #42262075162](https://github.com/eristavi/eristavi-lang/actions/runs/42262075162)
**18 run, 17 pass, 1 test-harness failure**: the isolated trace fixture
looked for a source comment removed by the optimized producer and asserted
`count == 1` before compiling/executing the owned/C generator. Therefore
**the owned-generator watchdog was NOT exercised on `e40a64b`**; this failure
is not a compiler liveness mismatch. The next test-only change updates the
trace anchor to the new producer comment, with unchanged watchdog and oracle.
The active candidate remains unqualified.

**Latest exact diagnostic:** [focused #42262947027](https://github.com/eristavi/eristavi-lang/actions/runs/42262947027)
on `ac475bb` executed 18 methods (17 passed, 1 timeout); all
generator source construction and publication-table production completed.
The last output marker is `U2_NATIVE_TRACE:publication-verify`: the
**independent per-instruction publication verifier** is now the first
measured 120-second bottleneck. Earlier diagnostic fixture failure is fixed.

The next narrow source candidate updates only
`ssa.verifyPublications`: it still freshly calls `verify` to independently
reconstruct the original whole Function/Plan, checks ordered tracked ValueIds,
then checks ALL canonical entry, before, and after root bits (including
unreachable blocks) by last-use and SSA definition ordinal from the ORIGINAL
owned Function tables. It does not trust emitter-generated table data,
change public point APIs, skip a validation row, weaken cleanup/root
requirements or alter public ABI. The verifier is structurally independent
of the emitter's reverse suffix-use producer. Synthetic randomized
reference-model parity: **3,093,668 cases, zero mismatches** (not a native
qualification). **First attempted verifier-build result:** [#42263997707](https://github.com/eristavi/eristavi-lang/actions/runs/42263997707)
FAILED at frontend semantic analysis, before source execution: the candidate
redeclared existing local `i` in a nested lexical block
(`name 'i' is already visible` at `u2_ssa_liveness.eri:516`).
This is a candidate-source scoping error, not a root liveness failure.
The next corrected revision reuses the existing mutable binding (`i=0`);
no language semantics or check is relaxed. The initial red builds do not
provide execution, sanitizer or speedup evidence.
**Hosted exact-source owned-generator tests are pending**;
no speedup or completion is claimed. `U2` and #74 remain unaccepted/open.

**Latest hosted check of corrected last-use verifier `c63f2a6`:**
[SSA/List #42264207607](https://github.com/eristavi/eristavi-lang/actions/runs/42264207607)
**8/8 PASS**; [identity roots #42264207644](https://github.com/eristavi/eristavi-lang/actions/runs/42264207644)
**15/15 PASS**. [Managed whole-Function #42264207710](https://github.com/eristavi/eristavi-lang/actions/runs/42264207710)
executed **18 methods: 17 pass, 1 owned generator timeout at 120 seconds**;
the last observed marker was again `publication-build`. No
exact-head passing generator result, performance speedup, or full U2
qualification has been established.

**Next diagnostic (test-only):** measure monotonic elapsed seconds when
each owned generator phase marker actually arrives on stdout, preserving
the exact 120-second watchdog, ELF checks and byte-exact comparison.
Additional markers expose buffer allocation, block-entry production,
per-block instruction chains, first suffix calculation and completed
blocks; all are injected into an isolated compiler copy, never production
source. This resolves whether repeated expensive allocations or a specific
block/value phase dominates before choosing another production edit.

The newest development revision replaces repeated emitter tail rescans with
bounded reverse suffix-use and forward definition sweeps, preserving frozen
linked instruction order and global SSA IDs. Every produced root bit still
passes through the **unchanged independent `ssa.verifyPublications` oracle**,
including dead instructions and foreign/stale/missing-root refusal. No trusted
flag, output ABI or resource semantics changes. This revision is **UNQUALIFIED**;
inspect its owned-generator, focused negative and independent-bit-comparison
results first. If the verifier becomes the next bottleneck, diagnose it
separately without weakening checks. Do not repeat superseded diagnostics.

Targeted reproduction:

```sh
PYTHONPATH=tests:. python -u -m unittest -v test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_owned_and_c_bootstrap_generators_emit_identical_checked_function
```

This builds an individual source generator with the owned resource runtime,
requires byte-identical assembly to the C generator, then executes the generated
checked Function at depth 32. Retain static ELF, no undefined symbols/loader and
non-executable-stack checks. Keep the test and its gate; do not skip it or silently
increase the timeout. Local `ptrace` was denied (EPERM). No measured speedup is
established. This probe is not a full owned-compiler self-build.

After resolving it, validate the coherent current checked class (11 methods),
existing managed class (7) and Text/List integration (12), relevant SSA/checked/
owner/registry negatives and changed-input ASan/UBSan; then focused hosted smoke.
Reuse unchanged physical evidence only within its documented scope. Reserve full
four-platform CI and completed-batch qualification for the completed final batch.

## Implemented scope — reuse rather than repeat

| Component | Current boundary |
| --- | --- |
| Canonical scalar CFG | Original Function reverified including dead blocks, simultaneous block arguments, i64/pred, branch/switch/backedges/return; bounded private x86-64 backend. |
| Managed roots and calls | Exact per-ValueId entry/before/after liveness; class-1 Text/List/identity roots, loops, nonfallible self calls and up to two caller-rooted results. Checked `emitChecked` adds opcode-46 self-invoke normal/failure CFG, exact negative outcome ordinals/carried SSA and class-5 saved-failure roots. Child publishes into registered caller roots before retiring its scope. No arbitrary/mutual targets or full File-call integration. |
| Checked return contract | `u2_function_contract.eri` binds exact frozen FunctionId/signatures; optional opcode 47 `return.failure`. Fresh verifier checks binding/type/arity/attributes/origin, including dead blocks; legacy profiles refuse it. Scoped owners must be empty on both return kinds. Zero, one and two normal results supported; no fake Void SSA. |
| Text / Unicode17 | Established 12 imports: scalar construction, immutable concat/copy/equality, views/counts/indexes, NFC and collection; mixed Text/List loops. Unicode17 remains frozen. |
| List<i64> | Empty/copy/append/count/get/replace/collect with rooted snapshots/boxes and original source/LocId bounds faults, including negative/end bounds. Nested/non-i64 producers remain open. |
| File cleanup / failures | Checked typed edges, owner prefixes, reverse exactly-once closes, primary/ordered-secondary failure roots; bounded two-stage native chain and recursive runtime probes. File paths remain separate adapters. Whole-Function checked recursion propagates existing saved contexts; general context construction and complete handler/resource integration remain open. |
| Private physical schema | Function gained `definedTarget` (default zero): **18** owned graph cells, previously 17. Physical observer and independent pin updated; capacity/traffic budgets unchanged. |
| Publication verification change (before newest producer revision) | `ssa.verifyPublications` freshly verifies the full plan once, then all ordered IDs and entry/before/after bits, including dead code; replaces repeated full per-instruction verification. Public `requirePublished` unchanged. `ssa.verify` closes its derived plan on comparison-work refusal. This change is not fully requalified and did not resolve the observed timeout. |

Contracts: [checked Function returns](docs/architecture/UIR_U2_CHECKED_FUNCTION_RETURNS.md),
[managed recursion](docs/architecture/UIR_U2_FUNCTION_MANAGED_RECURSION.md).

## Evidence and limits

[Raw logs and source hashes](docs/evidence/2026-11-06/u2-checked-function-stop-checkpoint.md)
retain detailed measurements and earlier failed attempts. Never treat older passes
as validation of later implementation changes.

| Evidence | Result and scope |
| --- | --- |
| Checked + existing managed tests, before publication batching | **16/16 pass**, 193.818 s: checked recursion depths 0/1/5/32/64, handler recovery, zero/scalar/two-managed returns, primary + two ordered secondary failures, malformed/dead returns/ordinals, legacy and missing-payload/handoff refusal; narrow Stage-0/old-C/new-native comparison. |
| Bootstrap C ASan/UBSan, before batching | **9/9 pass**, 298.642 s, `-O0`, `halt_on_error=1`, `detect_leaks=0`. LSan unavailable due to thread-inspection restrictions. Does not sanitize emitted owned assembly. |
| Owner physical/foundation/cleanup guards | **5/5 pass**, 52.557 s; actual backing/traffic/reclamation, 18-field schema and cleanup bypass refusal. Relevant builder/observer source unchanged since that run. |
| Publication corruption/refusal matrix after batching/fix | **1/1 pass**, 10.573 s: duplicate/foreign IDs, missing/dead/nonbinary flags, dead-entry corruption, forged backing, stale revision, extra rows and budget-refusal reclamation. Existing public SSA liveness negative also passed. |
| Owned/C comparison | Still failing 120-second watchdog; later hosted diagnostic **17/18 pass**, as above. No matching owned-generator assembly observed. |
| Last green implementation baseline | `50113f7`, Linux smoke [#42245608877](https://github.com/eristavi/eristavi-lang/actions/runs/42245608877): **147 run / 144 pass / 0 fail / 3 skips**. Does not qualify current WIP. |
| Final acceptance | Four-platform full CI and completed-batch qualification **not performed** for current implementation. No merge, production promotion or public 32-byte ABI change. |

## Remaining before #74 can close

1. Qualify current checked self-invoke, then integrate arbitrary/mutually recursive
   targets, File acquisition/consumption, owner proof, reverse cleanup, pending
   returns and all handler exits in original whole-Function lowering.
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
| U2 | Unaccepted, active diagnostic blocker above; #74 open, #111 draft. |
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
