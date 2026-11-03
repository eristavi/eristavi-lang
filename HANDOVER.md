# Eristavi compiler — current handover

**Current review: 3 November 2026, Asia/Nicosia.** This file contains current recovery
instructions and accepted boundaries. Superseded checkpoints are in the
[historical snapshot](docs/history/2026-11-02/HANDOVER_BEFORE_CLEANUP.md).

**Current authorization: user granted standing permission for GitHub development, review, tests, documentation and qualified merges.**
Continue bounded U2 work under the governing philosophy, frozen semantics and
proportional testing rules. Optimization #51 remains OPEN / PAUSED.
No full U2 CI or completed-batch qualification has been initiated; unverified new changes must not be reported as passing.

## Current verified status

| Area | Current state |
| --- | --- |
| Repository | https://github.com/eristavi/eristavi-lang |
| Main implementation baseline | `59d30c18c28fa59e9793100f72b9ffd88cc603ee`; subsequent handover cleanup is Markdown-only |
| Latest qualified production merge | [PR #110](https://github.com/eristavi/eristavi-lang/pull/110), merge `6b5fccecb8e79f7c9bcc8261faa9203f4c94262a`; subsequent main changes are documentation/evidence/opt-in probes |
| U1a | Complete within its adopted scalar/SSA/call/Float/provenance/physical boundary; [#77](https://github.com/eristavi/eristavi-lang/issues/77) CLOSED |
| U1b | Bounded reference immutable aggregates/linked execution accepted through [merged #106](https://github.com/eristavi/eristavi-lang/pull/106); [#73](https://github.com/eristavi/eristavi-lang/issues/73) CLOSED |
| U2 | Canonical cleanup/failure and scoped roots, bounded SSA liveness, and opt-in Text/List/identity descriptor and operation contracts focused-tested; Stage-0/C/owned reference parity and a bounded single-block canonical List-i64 native execution slice passed focused checks; general managed operations/roots and full qualification OPEN; [#74](https://github.com/eristavi/eristavi-lang/issues/74) OPEN; draft/unmerged |
| U2 branch / PR | `compiler/u2-cleanup-foundation-20261102`; [#111](https://github.com/eristavi/eristavi-lang/pull/111) OPEN / DRAFT |
| U3 / U4 | [#75](https://github.com/eristavi/eristavi-lang/issues/75) / [#102](https://github.com/eristavi/eristavi-lang/issues/102) OPEN; redesigned production integration/machine migration unimplemented |
| Optimization | [#51](https://github.com/eristavi/eristavi-lang/issues/51) OPEN / PAUSED; no whole-compiler speedup or optimization completion claimed |
| Production | Existing frontend/default compiler, frozen source behavior and 32-byte ABI retained; no new-UIR backend promotion |
| Full owned compiler self-build | Explicitly excluded from ordinary work; NOT CERTIFIED |

## Current U2 checkpoint — canonical List-i64 native execution

Prior operation-shape hosted CI #41691861564 PASSED on exact head
`4ebf6f153bd0f8f21349d25846528fe31bdbb1f3`.

New `src/compiler/u2_list_i64.eri` verifies and emits a closed optional canonical
single-block List-i64 profile through the actual owned x86-64 graph runtime.
It supports empty/copy/append/replacement/count/get and explicit collection,
with automatic class-1 frame-root stores and straight-line last-use clearing.
Its carrier is explicitly opaque in this legal profile; this is not general
canonical managed type encoding or frontend routing. The compiler checks the
exact versioned seven-import signatures, symbols and effects, and rejects
aggregate materialization. Existing production main remains unchanged.

Focused native tests PASSED: 3 tests in 23.313 seconds, covering five snapshot
observations after GC and final reclamation, negative bounds, first graph OOM,
and three malformed ingress cases with no native assembly emitted.
Broader local smoke PASSED: 89 run, 86 passed, zero failures, three
intentional skips, 218.088 seconds. Source hashes, raw log and outcomes
are in `docs/evidence/2026-11-03/u2-list-i64-native-smoke.*`.
Hosted exact-head CI is pending; no full qualification or merge.
See `docs/architecture/UIR_U2_LIST_I64_NATIVE.md` for exact scope/algorithm,
closed runtime descriptor boundary and remaining requirements.

Next: independently validate target descriptor/root contracts and source-fault
mapping; extend the bounded legal profile to typed managed CFG/loops, integrate
managed registry and local promotion, then Text/identity and checked cleanup.
Do not treat this single-block executable slice as full U2 acceptance.

## Active U2 follow-up — managed SSA operation shapes

Current work extends `u2_managed_operation_contract.eri` with exact typed operand
and internal-result shapes and fresh stored-contract verification. List append
and indexed replacement retain zero SOURCE results while requiring one internal
replacement List SSA result, preserving earlier snapshots. Equality returns pred;
Text views use an explicit distinct semantic domain, not a fabricated canonical
Text/List TypeId. Complete native managed execution remains unfinished.

The standalone managed fixture passed locally (one unittest, 1.011 seconds),
including nine same-revision semantic/effect field corruptions. Broad local
smoke PASSED: 86 run, 83 passed, zero failures, three intentional opt-in skips
in 201.782 seconds. Source-hashed raw outcome/timing report:
`docs/evidence/2026-11-03/u2-managed-ssa-shapes-smoke.json`.
Hosted exact-head smoke is pending; local evidence is not full qualification.
No four-platform qualification, full owned self-build, merge or U2 closure.
Resume canonical managed type/value/instruction construction from this shape
boundary, then actual owned adapters and automatic live-root publication.

## U2 Phase 1 managed runtime — current in-progress checkpoint

**Workstream:** managed Text/List/identity type relationships. Source branch
`compiler/u2-cleanup-foundation-20261102`, draft PR #111; production `main`
remains unchanged. Added opt-in `src/compiler/u2_managed_types.eri` as a
separate, versioned owner-scoped descriptor registry (one canonical Text,
ordered growable homogeneous List relationship and explicit shared identity
handle relationship). Descriptors distinguish ordinary value-copy policy
(1) from shared identity alias policy (2), intern duplicate relationships,
reject foreign/forward/cyclic type references and unsupported identity nesting,
and expose deep-fixability for explicitly represented managed nesting.
The independent verifier checks frozen metadata backing, every canonical
record including unused records, copy/alias policy, duplicate descriptors,
and independently revalidates the unchanged structural aggregate graph.
Existing public 32-byte value ABI, canonical U1b aggregate graph, frontend,
owned collector and source syntax remain unchanged.

`tests/fixtures/u2_managed_types.eri` and
`tests/test_u2_managed_types.py` cover Text/List/identity descriptors,
nested type relationships, identity-induced non-fixability, forged policy,
forward element IDs, wrong version and owned-backing reclamation.
The test is included in the focused smoke test list.

**Verified managed-type foundation (2026-11-03):**
[Focused CI #41629331699](https://github.com/eristavi/eristavi-lang/actions/runs/41629331699)
SUCCESS on exact implementation head
`b57c5dfc88a1e618069a2c002f01f06e88821d26`:
85 tests run / **82 passed / zero failed / 3 intentionally skipped**.
The standalone managed-type descriptor regression and preceding SSA/native
collector regressions passed. The original #41625310530 failed because
the standalone fixture did not instantiate the already-accepted
`u1_meta.sequenceHash` concrete TypeId-list specialization. The correction
uses the established U1b fixture pattern, without modifying compiler
semantics or source/runtime ABI.

**Managed operation contract focused verification (2026-11-03):**
[CI #41631072215](https://github.com/eristavi/eristavi-lang/actions/runs/41631072215)
SUCCESS at exact implementation head
`0f7d8f8724addb1a952a0d3dc0d4a584cd39050b`:
85 run / **82 passed / 0 failed / 3 intentionally skipped**.
The `test_u2_managed_types` fixture exercised the closed version-one
copy/alias/List/Text Unicode17 operation selector and negative operation
refusals. The prior #41630206523 failed only because the new module
used unsupported `else if` syntax; the corrected disjoint `if` branches
compiled and passed. Text copy is conservatively classified as
potentially allocating, requiring safe-point root preservation until
a target proves otherwise.

**Exact-head managed operation + three-runtime parity verification — PASSED:**
[Focused CI #41631707129](https://github.com/eristavi/eristavi-lang/actions/runs/41631707129)
SUCCESS on implementation source
`d080c6fc50c72e7f86aba8cca4078437e913ae06`.
86 tests run / **83 passed / zero failed / 3 intentionally skipped**
(173.084 seconds); scope/patch check succeeded, full four-platform
CI intentionally skipped. In particular, the tests
`test_versioned_text_list_identity_descriptors_and_corruption` and
`test_u2_managed_unicode17_list_value_and_identity_alias_parity`
both reported `ok`. The latter executed the **existing** Stage-0,
C-native and Linux x86-64 owned runtimes on the same composite source
and checked Unicode17 grapheme/scalar/byte views, non-normalizing Text
equality, List value-copy isolation, identity alias/distinct equality
and final graph/Text reclamation. This freezes reference behavior
for the future redesigned-UIR backend: **it does NOT prove that new UIR
executes those managed operations or publishes their native GC roots**.

The new private `u2_managed_operation_contract.eri` independently
checks semantic kind/copy-policy consistency, enforces explicit
operation/type/view families and conservative allocator/root
obligations; no new surface keyword, 32-byte ABI change, moving
collector or production-backend routing was added. All three
opt-in skips remain visible and cannot count toward final U2 release.

**Phase 1 remaining:** Author versioned canonical UIR managed operation
and value representation with independent verification; connect to real
owned Text/List/identity native runtime adapters, automatic SSA native
root-class placement and publication, deep List copy/alias/Unicode17
behavioral parity, forced-GC and OOM tests. U2 #74 and draft PR #111
remain open; no full four-platform CI or production merge.

## Earlier U2 native-root checkpoint — 3 November 2026 (superseded by Phase 1 above)

**Current development:** single draft [PR #111](https://github.com/eristavi/eristavi-lang/pull/111), branch compiler/u2-cleanup-foundation-20261102. Support PRs #112–#118 are closed unmerged after reconciliation. U2 [issue #74](https://github.com/eristavi/eristavi-lang/issues/74) remains OPEN; U3/U4 open; optimization #51 remains PAUSED. Existing production main, compiler, locked source semantics, 32-byte ABI and owned runtime defaults unchanged.

**Verified tests:** [focused CI #41602009013](https://github.com/eristavi/eristavi-lang/actions/runs/41602009013) at exact implementation head a07478c1e84d8f8e9cc31d72ba9dde25297cf87e completed SUCCESS, 81 tests run, **78 passed, 0 failed, 3 opt-in skipped**, 267.157 seconds. [Preceding #41601414665](https://github.com/eristavi/eristavi-lang/actions/runs/41601414665) also passed 81/78/0/3 at f6db7ad146bc5fe783869ba5120fd98f6ba762d2, 175.821 seconds; no general compiler performance improvement is claimed. Both have scope check successful and the full four-platform CI intentionally skipped.

**Implemented and verified:** canonical opcode-46 checked invokes, scoped cleanup and 16-case ordered typed primary/secondary matrix; independent bounded versioned root-map metadata over all checked instructions including dead blocks; direct owned-runtime primary/secondary Text survival through explicit GC. New opt-in src/compiler/u2_native_root_x86_64.eri verifies the canonical root map before emitting concrete Linux/System-V x86-64 helpers for a scope-bound class-5 root-word table. Bind zero-initializes 8-byte caller stack words before publishing; each verified invoke gets unique publish/release helpers. Test tests/test_u2_native_root_publish.py constructs a real five-invoke canonical UIR fixture, compiles and assembles those emitted helpers, then uses the real owned collector to test single-root retention/reclamation and **two independently published saved-failure roots**, including survival of the second record after release/collection of the first. The two-slot case passed in #41602009013. See [native publisher contract](docs/architecture/UIR_U2_X86_NATIVE_ROOT_PUBLICATION.md).

**What is NOT yet proven:** the emitted native helper paths are exercised from a controlled handwritten checked-failure body, not an automatically lowered complete canonical UIR program. The bounded opt-in CFG live-set and declared publication-set verification is now focused-tested, but general live-in/liveness over all managed SSA values and its automatic native publication across allocating safe points, loops, nested unwinds and recursion remain unimplemented. So do new-UIR managed Text/List/identity with full Unicode17, real checked file/resource adapters and complete FailureContext secondary-order execution, arbitrary multi-exit cleanup/cancellation, allocator fault/physical/RSS evidence, Stage-0 vs new native execution oracle, and final completed-batch four-platform qualification. Three opt-in probes were skipped. **Do not close #74, mark U2 complete, run full owned compiler self-build or merge PR #111 into main.**

### In-progress U2 native placement check — not yet CI-verified

A private one-root-word-per-invoke x86-64 slot plan now binds the fresh canonical
root-map object, owner, type and exact revision. Independent validation checks
closed, foreign, forged, wrong-class, misaligned, overlapping or absent slots,
including unreachable checked calls, before native helper assembly is printed.
The native emitter consumes the verified displacements and the focused test
adds both adversarial slot mutations and a separate assembly-offset oracle.
The verified scope is limited to checked-failure pointer roots; it is **not**
whole-program managed SSA liveness. The completed bounded slot-plan implementation, including its checked-error
propagation fixes, passed exact-source [focused CI #41620686122](https://github.com/eristavi/eristavi-lang/actions/runs/41620686122)
at commit `8eb2bd1f2710ca377ab0a643bcb31edb63f3b48d`.
That same source also carries the new SSA-liveness and root-obligation tests;
the complete focused smoke ran 84 tests, 81 passed, 0 failed and 3 intentionally
skipped. The complete four-platform matrix was intentionally skipped.
Keep #111 DRAFT and #74 OPEN.

### New canonical SSA-liveness analysis — focused smoke verified, native rooting still open

The opt-in `src/compiler/u2_ssa_liveness.eri` now tracks an explicit list of
structural-aggregate TypeIds through the *existing canonical* SSA value table.
The analysis independently invokes the U2 fallible-registry/canonical verifier,
uses a bounded backward CFG fixpoint with predecessor-specific block-parameter
substitution, handles negative checked-invoke edge-created results as new values,
and exposes live entry/exit and instruction-before/after queries. The latter
walk each block's real instruction chain (global InstIds need not be in
execution order). Version, owner, type graph, contract identity, function
revision, storage lengths and independently recomputed live sets are verified;
malformed/missing/forged data must fail closed. Explicit limits are 64 blocks,
512 instructions/values/edges, 32 selected values, and 8 selected TypeIds.
A new test suite covers nested checked cleanup, SSA self-loop/backedges,
dead blocks and recursive calls; see
`tests/test_u2_ssa_liveness.py`, `tests/test_u2_ssa_loops.py` and
`tests/test_u2_ssa_recursion.py`. These tests are added to Linux smoke.

**Exact-head focused evidence:** [CI #41620686122](https://github.com/eristavi/eristavi-lang/actions/runs/41620686122)
passed on source commit `8eb2bd1f2710ca377ab0a643bcb31edb63f3b48d`:
84 run, 81 passed, 0 failed, 3 intentionally skipped. The dedicated
checked-cleanup, loop/backedge, recursive-call, and native two-failure
root-publishing tests all passed. Scope/patch check passed. No full matrix
or final U2 qualification was run. The test suite explicitly verifies
`requirePublished` at call/cleanup safe points, rejecting missing, duplicate,
foreign, or prematurely released declared SSA roots. The root obligations are
compiler-level proofs, **not yet automatically lowered native root words**.

The structural TypeIds in these probes
are immutable U1b aggregates; they do NOT yet have independently proven
managed pointer classes, automatic heap root publication at each allocating
safe point, or complete new-UIR Text/List/identity semantics. The 32-slot
profile is intentionally bounded and must not be advertised as universal
liveness/rooting. Full machine lowering, native GC live-set publication,
per-recursive-frame runtime allocation, allocator refusal and physical
measurements remain OPEN. Keep PR #111 draft, U2 #74 open, and main unchanged.

## Next U2 steps

1. Independently verify actual target slot allocation and liveness for every canonical checked edge and all live managed values across allocations, returns, loops, dead blocks, recursion and cleanup failure paths. Refuse stale, foreign, overlapping, misaligned, absent or prematurely cleared roots. Keep bounded complexity and owner/work accounting.
2. Emit full canonical checked invoke and real file/resource close operations into the existing owned runtime with typed primary and ordered secondary FailureContext; integrate Text/List/identity value/alias/Unicode17 behavior.
3. Complete native forced-GC and allocator refusal evidence, per-owner physical backing, traffic and RSS, independent Stage-0/owned oracle parity, and then one exact final full four-platform CI/qualification before any merge.

Detailed earlier U2 checkpoints were moved verbatim to [archived U2 history](docs/history/2026-11-03/U2_DRAFT_CHECKPOINTS_BEFORE_NATIVE_ROOTS.md). Archived pending notes are not current blockers unless restated above.

## Qualified baselines and paused performance debt

- **Production #110:** tested head `1fbb5115dccc2c6b6160d511366d31d06601849d`
  and merged tree `3e3ab90714a9a608c9dafabf4740dae60049ff1d` match.
  [Full CI 41336208716](https://github.com/eristavi/eristavi-lang/actions/runs/41336208716)
  and [qualification 41336171885](https://github.com/eristavi/eristavi-lang/actions/runs/41336171885)
  PASS. Scoped lookup boxes/allocations/finds decreased; no meaningful
  end-to-end wall-time gain was proved.
- **Reference U1b #106:** tested head `bd0a159975d73239f87300debce89c453a59ebb1`,
  tested/merged tree `e81f594294f4c0700a0a572ec4434742199d4573`, merge
  `b86d54f2f6268d12831bb0b09f3016b1dd3c1f67`.
  [Full CI 41313784760](https://github.com/eristavi/eristavi-lang/actions/runs/41313784760)
  and [qualification 41313784884](https://github.com/eristavi/eristavi-lang/actions/runs/41313784884)
  PASS. Accepted as bounded reference functionality, not a promoted production
  pipeline. Its 11.0158% improvement applies to one Linux GCC fixture only.
- **U1a #105:** merge `8c625b1ece6a229844def93e2bf9563c14e9e273`;
  [full CI 41222506854](https://github.com/eristavi/eristavi-lang/actions/runs/41222506854)
  and [qualification 41222506873](https://github.com/eristavi/eristavi-lang/actions/runs/41222506873)
  PASS. #77 closed within its adopted ownership/provenance boundary.
- Earlier #108/#99 runtime and profiler evidence is preserved in dated reports
  and the archive; those already-merged batches are not active tasks.

#51 remains paused. The large production `ir_verify.eri` diagnostic is still
censored at the unchanged 90-second cap. Six private round-three candidates
were not adopted. Actual verifier-storage measurements are complete; they do
not prove a new optimization. Do not repeat rejected pilots or capped workloads
for a favorable timing, loosen limits or infer total duration from a timeout.
Relevant preserved records:
[round-three report](docs/performance/ISSUE51_ROUND3_EXPERIMENTS_2026-11-01.md),
[storage report](docs/performance/ISSUE51_VERIFIER_STORAGE_2026-11-01.md), and
[storage summary](docs/evidence/2026-11-01/issue51-verifier-storage-summary.json).
Scalar unboxing and shared type-validation reuse still require their recorded
ownership/escape/liveness/root/exhaustion/immutability proofs before adoption.

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

## Recovery and governing documents

Dated records retain their original status wording. Their contracts remain
governing; the current implementation and task state is recorded above.

Read this complete current handover and [DESIGN_PHILOSOPHY.md](DESIGN_PHILOSOPHY.md),
[LANGUAGE_SEMANTICS.md](LANGUAGE_SEMANTICS.md), applicable locked semantics, the
relevant [architecture records](docs/README.md), and
[CI_QUALIFICATION.md](CI_QUALIFICATION.md) before a material decision. For U2,
include [remaining acceptance](docs/architecture/REMAINING_UIR_ACCEPTANCE_PLAN_2026-10-31.md),
[continuations](https://github.com/eristavi/eristavi-lang/blob/3dbc6add049c70fe6adb34bd954270f08a5ba6e7/docs/architecture/UIR_U2_CONTINUATION_CONTRACT.md),
[fallible registry](https://github.com/eristavi/eristavi-lang/blob/3dbc6add049c70fe6adb34bd954270f08a5ba6e7/docs/architecture/UIR_U2_FALLIBLE_REGISTRY.md),
[scoped ownership](https://github.com/eristavi/eristavi-lang/blob/3dbc6add049c70fe6adb34bd954270f08a5ba6e7/docs/architecture/UIR_U2_SCOPED_OWNER_SLICE.md),
[initial policy](https://github.com/eristavi/eristavi-lang/blob/3dbc6add049c70fe6adb34bd954270f08a5ba6e7/docs/architecture/UIR_U2_INITIAL_POLICY.json),
[cleanup semantics](RESOURCE_CLEANUP.md) and
[owned resource runtime](OWNED_RESOURCE_RUNTIME.md).

Fetch and inspect current GitHub refs; do not trust an old scratch checkout,
branch name or report title. Current recovery branch is
`compiler/u2-cleanup-foundation-20261102`; the latest implementation and tested
revisions are recorded above. Later documentation commits do not change those
inputs. Full U2 qualification remains outstanding. No development should start
merely because this handover lists future gates.

The earlier documentation-only stop is superseded by the latest user instruction. For the preceding documentation cleanup, the pre-cleanup file is preserved in full from
`867252d494d9dee6a7b40284b8ed4dffee88db8f`. The cleaned handover/history are published on both `main` and the U2 branch
without merging U2 implementation. Only Markdown changes are authorized and made; compiler/tests/ABI/evidence archives are unchanged. Use a patch/link/
archive-integrity check, reusing valid evidence; do not launch compilation or
full qualification. The user's former development stop was superseded by the explicit instruction to resume U2 implementation.

## Historical section references

Former §§1–92 and every original measurement/revision are retained in the
[pre-cleanup snapshot](docs/history/2026-11-02/HANDOVER_BEFORE_CLEANUP.md).
**Archived commands, pending statuses and next actions are historical evidence,
not active instructions.** Read history only when needed for a specific decision.

| Former reference | Historical subject |
| --- | --- |
| §§25, 28–29 | CI cost policy and earlier U1a execution acceptance |
| §44 | Accepted U1a #105/#77 boundary and physical evidence |
| §77 | Accepted reference U1b #106, exact-tree merge and closure |
| §§78, 84 | Qualified #108/#110 production optimizations |
| §§86–87 | Rejected optimization candidates and completed storage measurements |
| §§88–90 | Initial U2 planner, independent verification and destination binding |
| §§91–92 | Canonical invokes/transport/owner foundation and completed hosted smoke |

Future handovers should replace outdated current statements and archive history,
not recreate the old chronological accumulation. This current file supersedes
all archived recovery instructions while retaining the governing mandates.
