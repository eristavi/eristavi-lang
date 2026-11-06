# Eristavi compiler — current handover

Updated 6 November 2026 (Asia/Nicosia). U2 verifier word-read performance candidate; exact-source acceptance pending.
Branch: `compiler/u2-cleanup-foundation-20261102`; [PR #111](https://github.com/eristavi/eristavi-lang/pull/111) remains DRAFT; #74 remains OPEN.
Original checked-return checkpoint: `3100dc8e82f8e496d61fd38d0cdab5311416bd36`.
Prior publication implementation: `e40a64b3c8b7774dc68d3220f6b208ee38854ca6`. Earlier exact diagnostic: `a51182e663e645777186e9f6551bdc7081f36916`.
Current checked-only deferred-middle-proof implementation is in this containing commit (unqualified).
Current development is not qualified or merged. Optimization #51 remains PAUSED.

## Current blocker and next action

**First fast-read test (compile-only failure):**
[run #42272459327](https://github.com/eristavi/eristavi-lang/actions/runs/42272459327)
failed immediately while compiling the `u1_words` candidate:
`semantic error at 101:13: initializer expected identity Node, got
maybe identity Node`. No native execution or work accounting was
reached. The next small correction uses the existing
`needNode` / `needPage` checked unwrap helpers inside branches
whose inputs are already required to be non-none. This is a
source-type correction only; no change to budget/owner/fast-path
selection or fallback. Qualify this corrected revision separately.

**Current production implementation candidate (containing commit):**
`src/compiler/u1_words.eri` now has a bounded, *valid-read-only* fast
path. All seven original work units are charged on a successful read with
an unchanged six-child radix traversal, using one budget call **only if**
the current path/page is complete and the phase, owner and parent limits
can pay the entire charge. No cached path, owner trust flag, ownership
change, extra allocation or ABI change. A bad/missing radix child/page,
a closed/cancelled state or a low remaining work budget takes the
**original exact per-level slow path** and error order. Source-level
safety tests `test_u1_words_path` cover every corrupted radix depth,
frozen current backing, owner traffic and budget limits 0..6, and must
PASS on both C-bootstrap and owned runtimes. This change targets the
**measured U2 canonical-verifier/liveness read overhead**; independent
canonical/root verification is unchanged, and separate optimization
#51 stays PAUSED. No speedup is claimed until exact-head tests.

**Latest clean baseline:** [managed #42271055504](https://github.com/eristavi/eristavi-lang/actions/runs/42271055504)
at `dc0ce3f` ran **18 methods / 17 pass / 1 uninstrumented
120-second owned-generator timeout**; it emitted no output before deadline.
[Text/List integration #42270143006](https://github.com/eristavi/eristavi-lang/actions/runs/42270143006)
on same production compiler (prior test-only commit) **12/12 PASS**.
The prior checked-only deferred middle verifier improvement remains
implemented but not qualified. **New word-read fast path is untested**;
first run exact depth/failure-accounting test and hosted owned/C generator
comparison; do not mark U2 accepted, PR #111 merged, or issue #74 closed.

**Source state:** current development candidate is the containing commit after
`a51182e`. The checked-profile-only producer now **defers** the middle
`ssa.verify` reconstruction, rather than deleting the mandatory proof.
`roots.create` still freshly verifies the ENTIRE original frozen canonical
Function and builds the local Plan; `ssa.verifyPublications` still freshly
rederives the complete original Plan and independently checks ALL
entry/before/after bits, including dead blocks, **before the first assembly
output**. The untouched standalone `ssa.verify` and `requirePublished`
APIs remain strict. Unchecked `emit` and `emitRecursive` still perform
their original middle verification. No trusted stamp, new ABI, source syntax,
collector or work-limit change. Exact source `7b17207` passed
[Text/List #42270143006](https://github.com/eristavi/eristavi-lang/actions/runs/42270143006)
**12/12** and [managed focused #42270142869](https://github.com/eristavi/eristavi-lang/actions/runs/42270142869)
**17/18**. The sole failed method was the **instrumented** owned-generator
comparison, still timing out at 120 s; the second full proof was reached,
at ~58 s, and its canonical verification completed at ~102 s. It was
still calculating SSA flow when the 120-second watchdog expired.
This confirms that both full proof boundaries executed; it does
**not** qualify the generator or establish uninstrumented performance.

**Measured blocker, exact earlier source:**
[focused #42268931408](https://github.com/eristavi/eristavi-lang/actions/runs/42268931408)
on `a51182e`: 18 methods, **17 pass, 1 owned-generator 120-second
timeout**. In a temporary instrumented source copy, canonical root-plan
verification starts at 12.141 s and finishes 54.962 s, with checked
liveness construction ending at 77.873 s. The next *identical* independent
verification starts at 77.900 s and has still not completed by the 120-second
deadline. Detailed substage evidence is in
[publication/verification evidence](docs/evidence/2026-11-06/u2-publication-producer-batching.md).
Earlier [#42267466631](https://github.com/eristavi/eristavi-lang/actions/runs/42267466631)
measured canonical verification twice at 31.1/33.8 s, plan construction
twice at 16.6/17.8 s, and comparison ~4.2 s on an earlier trace. These
measurements support the redundant middle pass as a serious performance
cost, but **do not yet establish a speedup**.

**Why this is safe to test:** all three private compile entrypoints obtain
their Plan via `roots.create` immediately before `compile`. Only the
checked path skips the middle redundant proof; it does not emit any bytes,
expose a verified token, or execute owned code until the *later*
`ssa.verifyPublications` independently rejects or approves the original
canonical Function, Plan and the complete root publication bitmaps.
That checker still reconstructs from the original source, not the
emitter's table snapshots. Failures must still produce no native assembly.
The immutable input and private Plan do not leave this call; preserve
negative/owner/physical refusal tests, and treat every remaining limitation
as open until verified on the exact head.

**Next action:** run the corrected **uninstrumented** owned-versus-C
generator comparison against the exact new head. In the standard test, the
compiler source is an unchanged symlink to `src/compiler` and the fixture
source is original. The same C/owned assembly-byte equality, static
ELF/no-loader/undefined-symbol/non-executable-stack checks, exact
120-second watchdog and forced-GC depth-32 output oracle remain.
Host-side phase capture and isolated source-copy comments are still
available **only** with `ERISTAVI_U2_OWNED_GENERATOR_TRACE=1` for
future diagnostics. Instrumenting canonical verification changes runtime
work/allocations and can distort the qualification cutoff; no such
instrumentation belongs in the normal performance gate.
If the uninstrumented generator passes, verify independent checks,
negative matrix and ASan/UBSan within documented scope, then continue
the uncompleted U2 semantics and physical/CI gates. If not, measure the
remaining performance bottleneck without weakening verification,
native-output gating or exact failed-work accounting.
In particular `tests/test_u1_words_path.py` requires exact work charges on
failed radix paths; do not replace the word-store budget calls with a
single up-front charge. Preserve default ABI and avoid full owned
self-build. Keep #111 DRAFT and #74 OPEN.

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
