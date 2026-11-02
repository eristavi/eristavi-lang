# Eristavi compiler — current handover

**Verified: 2 November 2026, Asia/Nicosia.** This file contains current recovery
instructions and accepted boundaries. Superseded checkpoints are in the
[historical snapshot](docs/history/2026-11-02/HANDOVER_BEFORE_CLEANUP.md).

**Current authorization: U2 development resumed by explicit user instruction.**
Continue bounded U2 work under the governing philosophy, frozen semantics and
proportional testing rules. Optimization #51 remains OPEN / PAUSED.
No full CI or completed-batch qualification has been initiated.

## Current verified status

| Area | Current state |
| --- | --- |
| Repository | https://github.com/eristavi/eristavi-lang |
| Main implementation baseline | `59d30c18c28fa59e9793100f72b9ffd88cc603ee`; subsequent handover cleanup is Markdown-only |
| Latest qualified production merge | [PR #110](https://github.com/eristavi/eristavi-lang/pull/110), merge `6b5fccecb8e79f7c9bcc8261faa9203f4c94262a`; subsequent main changes are documentation/evidence/opt-in probes |
| U1a | Complete within its adopted scalar/SSA/call/Float/provenance/physical boundary; [#77](https://github.com/eristavi/eristavi-lang/issues/77) CLOSED |
| U1b | Bounded reference immutable aggregates/linked execution accepted through [merged #106](https://github.com/eristavi/eristavi-lang/pull/106); [#73](https://github.com/eristavi/eristavi-lang/issues/73) CLOSED |
| U2 | Foundation focused-tested; new typed-context reference and focused regression committed, NOT YET TESTED; [#74](https://github.com/eristavi/eristavi-lang/issues/74) OPEN; not complete, fully qualified or merged |
| U2 branch / PR | `compiler/u2-cleanup-foundation-20261102`; [#111](https://github.com/eristavi/eristavi-lang/pull/111) OPEN / DRAFT |
| U3 / U4 | [#75](https://github.com/eristavi/eristavi-lang/issues/75) / [#102](https://github.com/eristavi/eristavi-lang/issues/102) OPEN; redesigned production integration/machine migration unimplemented |
| Optimization | [#51](https://github.com/eristavi/eristavi-lang/issues/51) OPEN / PAUSED; no whole-compiler speedup or optimization completion claimed |
| Production | Existing frontend/default compiler, frozen source behavior and 32-byte ABI retained; no new-UIR backend promotion |
| Full owned compiler self-build | Explicitly excluded from ordinary work; NOT CERTIFIED |

## Current U2 development checkpoint — 2 November 2026

The user explicitly resumed implementation. Commit `2b39463e4be6fdb84ec119cddee3fc7b8e2eb165`
adds `src/compiler/u2_failure_order.eri`, a **private, untested** bounded
owner-scoped ordered checked-failure token ledger. It retains an existing primary,
promotes the first cleanup failure when none exists, and appends subsequent
failure tokens in cleanup order. Tokens are **not rooted typed error objects**;
this is not complete managed FailureContext, canonical resource lowering,
Text/List/identity support or U2 acceptance. The implementation has not been
compiled or run through focused tests; its API and allocation-failure behavior
require review before adoption. PR #111 remains draft; #74 remains open.
Follow-up commit `61fa433aa8c21ddd011b18b935759655cd2946c6` fixes an
identified constructor refusal path: the charged control allocation is released
if word-store creation fails. This is a code review correction, **not tested**.
New test fixtures in commits `c1724255540af024cde32e86d044203734a736ac`
and `4ecfb79606e9754d2adf81e53c243db0222a2563` exercise initial
primary/secondary order, already-active body failure, and charged owner
reclamation through a focused native Python unittest. **Not executed:**
this environment cannot access the repository via git/network, and the
connected GitHub actions do not provide a workflow dispatch or remote shell.
Do not claim these tests passed. The ledger is not a rooted FailureContext.
Next: compile and independently test the ledger, prove refusal/cleanup behavior,
then connect verified plans to canonical resource operations and managed roots.
Do not merge or run full qualification until coherent acceptance gates pass.

## 92. Current U2 checkpoint

**New 2 November continuation (unqualified):** On branch `compiler/u2-cleanup-foundation-20261102`, added `src/compiler/u2_failure_context.eri`, `tests/fixtures/u2_typed_failure_context.eri`, and `tests/test_u2_typed_failure_context.py` (commits `bf330fba3897f0d00e52868b6de4b9acda5b9aee`, `43d3493835dbbc9ecfbf1b938061f12300c5a323`, `c2d8bf3bd588304af257a971418eb35087da4b3c`). These are an **opt-in, typed and identity-linked semantic reference**, not a canonical managed FailureContext or root map. Primary typed failure and ordered secondary failure records carry type ID, Text payload and source location. Existing token-based order ledger remains unchanged. This change has **not been compiled or tested** because the local environment cannot resolve github.com for repository checkout; hosted smoke has not yet been inspected. No passing result, ABI integration, native adapter, allocation-failure/GC evidence, merge or closure is claimed. The newly added test is awaiting execution. Do not promote this implementation until actual compilation and tests confirm it.



This replaces the accumulated development instructions in former §§88–92.
The implementation is in the U2 draft branch, not `main`.

| Implemented and tested foundation | Source / boundary |
| --- | --- |
| Bounded reverse cleanup planning | `src/compiler/u2_cleanup_plan.eri`; private planning data, not executable IR |
| Fresh all-row cleanup verification | `u2_cleanup_verify.eri`; includes dead rows, mutations and checked refusal cleanup |
| Typed destinations and cleanup links | `u2_continuation_bind.eri`, `u2_cleanup_link.eri`; exact owners, revisions, signatures and source origins |
| Canonical fallible calls | `u2_invoke_build.eri`, `u2_invoke_contract.eri`, `u1_verify.eri`, `u1_successors.eri`; real FunctionIds, private opcode 46 and the existing canonical pools |
| Multiple checked contracts | Version-one metadata-owned table; exact normal signature snapshots, one aggregate failure payload, fresh checks of every entry including unused contracts |
| Typed outcome transport | `u2_invoke_transfer.eri`; version-two private descriptors, up to 128 carried values, predecessor availability and exact destination types |
| Bounded reference execution | `u2_invoke_reference.eri`; exact closed structural test adapter, outcome-only results and simultaneous source capture before destination writes |
| Initial scoped-owner verification | `u2_scoped_owners.eri`; explicit lexical owner signatures, success-only acquisition, LIFO consumption before both close outcomes, exact surviving edge prefixes and source origins |

The scoped profile currently admits **one explicit resource contract** with an
opaque aggregate handle interpretation. It checks every block, including dead
blocks; rejects resource construction/copy/escape, return without cleanup,
non-LIFO or consumed-owner use, bad edges and stale/foreign profiles; permits a
nonterminating loop to retain owners when its backedge signature matches.
It uses O(N+V+T+S) local verification and reusable
`2(V+1)+(T+1)+256`-word scratch under existing quotas, not path enumeration,
per-block register masks or an ownership fixed point.

**Do not broaden this result:** the resource fixture is hand-built canonical
UIR, not output of completed Eristavi cleanup-plan lowering or a real file
runtime. A structural aggregate payload is not the complete managed
primary/secondary FailureContext. Owned execution of the verifier is not native
execution of resource adapters. Text/List/identity, managed-local promotion,
root maps and complete runtime/context integration remain unfinished.

### Exact revisions and validation

| Evidence | Verified result |
| --- | --- |
| Latest implementation/evidence commit | `3dbc6add049c70fe6adb34bd954270f08a5ba6e7` |
| Exact implementation/evidence tree | `268d79d646293fb3acded1473ad52bceeae31c63` |
| Hosted-smoke head / tree | `4fea1f66fb6ea63621be419c67b8993b6f6bce07` / `982b4c149fd60ac72738a9677d6defabe1d3fdc8`; changes from the implementation commit are handover-only |
| Hosted smoke | [41492512950](https://github.com/eristavi/eristavi-lang/actions/runs/41492512950) SUCCESS; 69 collected, 66 passed, 3 opt-in skips; 145.442 s; job `125438983489` |
| Opt-in owned execution | All three skipped probes passed locally: invoke outcomes, carried outcomes and execution of the scoped-owner verifier |
| Focused U2 / ownership checks | 13/13 in 80.777 s; strengthened bootstrap owner checks 5/5 in 24.998 s; owned owner-verifier probe 1/1 in 24.458 s |
| Broad local smoke | 68 collected, 66 passed, 2 opt-in skips; 273.396 s; the later added owner-native test was run separately and adds the third hosted skip |
| Prior stop checkpoint | `867252d494d9dee6a7b40284b8ed4dffee88db8f`; handover-only successor of the hosted-smoke head |
| Qualification / merge | No new full four-platform CI, completed-batch qualification, U2 closure or merge selected; PR remains DRAFT |

Supporting coverage includes 150 independent legacy resource baseline cases,
30 cleanup plans / 1,602 semantic paths, frozen/dead-row mutations, typed
same-revision pool mutations, multiple fallible targets, unused contract
corruption, duplicate/foreign/version rejection, exact fuel/LocIds, constructor
work/traffic refusal, cancellation and released backing. Earlier intermediate
fixture failures are historical, not current blockers.

Current-source U1 forced-collision regression: **7,830,976 B actual phase peak /
21,974,768 B actual allocator traffic**, within the unchanged **8,388,608 /
67,108,864 B** gates; all tagged backing reclaimed. This is existing U1 physical
scope, not U2 scratch attribution or process RSS. The independent U1b type/value
backing test also reclaimed all observed metadata and function objects.

Evidence: [summary](https://github.com/eristavi/eristavi-lang/blob/3dbc6add049c70fe6adb34bd954270f08a5ba6e7/docs/evidence/2026-11-02/u2-canonical-summary.json),
[local smoke](https://github.com/eristavi/eristavi-lang/blob/3dbc6add049c70fe6adb34bd954270f08a5ba6e7/docs/evidence/2026-11-02/u2-canonical-smoke.json), and
[lossless archive](https://github.com/eristavi/eristavi-lang/blob/3dbc6add049c70fe6adb34bd954270f08a5ba6e7/docs/evidence/2026-11-02/u2-canonical-evidence.zip).
The archive retains raw logs, three owned result/hash records and 18 input
snapshots. CRC and every input SHA-256 were verified; current inputs still match.
Archive SHA-256: `4bea42f5648c0b2c8a3c69627fd1f612beb440405190e009d15eb673b2c6cda6`.

### Remaining U2 gates — actively authorized to resume

1. Connect semantic cleanup plans to canonical resource operations and prove
   exit origins, pending returns and exact cleanup across the complete profile.
2. Implement complete managed Text/List/identity typing and value-copy/alias
   semantics, pinned Unicode17 and managed-local promotion.
3. Implement rooted primary/ordered-secondary FailureContext, root/safe-point
   contracts and real resource/runtime adapters under the existing ABI.
4. Complete independent depth/exit/loop/identity-cycle/malformed cases,
   sanitizer/allocation-failure/cancellation and actual U2 physical/latency
   evidence under preselected policies. Existing small probes do not close this.
5. Once the coherent implementation meets acceptance, run one final exact-head
   four-platform CI and required full qualification, compare tested/merged trees,
   and only then decide merge/closure. Keep #74 open until its gates pass.

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
