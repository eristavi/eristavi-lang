# Eristavi compiler — current handover

**Authoritative recovery checkpoint: 1 November 2026, Asia/Nicosia. Read §74 FIRST for active optimization execution, the corrected current-source profile and the fixed-depth word-read candidate.** §73 is the plan; §72 is the last full U1b source qualification, not qualification of the new candidate.

PR #106 remains DRAFT/OPEN/unmerged, #73/#51 OPEN. Work starts from documentation
PR #107 head `d2bb747`, on `compiler/u1b-optimization-execution-20261101`. The
original #106 head is still `c2423d5` until integration. The profiler raw-unit
reconciliation is fixed locally, three cheap decoder/trace tests pass, and the
expanded native profile PASSes exact C/owned parity and all 231-snapshot counter
checks. Automatic expensive PR profiling has been removed from the candidate CI;
the explicit manual workflow remains. No source semantics/ABI/budgets changed.

The new profile confirms boxed value and word/budget amplification, not GC as
the main cause: about 951M successful allocations and 920M boxed values, with
0.614s inclusive GC. A private fixed-depth noncreating radix path preserved the
complete linked fixture and ran 61.4445 → 55.2858 seconds in ONE pilot pair
(10.02% nominal lower; NOT performance qualification). The candidate is now in
the local source for focused safety tests; targeted validation is in progress,
five pairs and final exact-head qualification remain PENDING. Keep #106 draft.
The older 6.24% same-owner poll improvement remains a separate accepted result;
no whole-compiler speedup or cure of the historic cross-runtime disparity is
claimed. Next: finish exact radix/refusal/current-corruption regressions, run
five paired trials if safe, then physical/smoke gates and one final required
qualification for an adopted batch. U2 → U3 → U4 remain downstream; no full
experimental owned compiler self-build.

## Standing GitHub authorization — explicit user instruction, 2026-11-01

The repository owner has **explicitly authorized ChatGPT to act on their behalf using the connected GitHub account**, without repeatedly asking permission for routine project work. Treat this as standing authorization for investigating repositories, reading files and issues, creating/editing commits and branches, updating PRs/issues/documentation, running available tests and workflows, and merging/closing completed milestones **when their documented acceptance gates actually pass**. Execute the requested work directly, provide results and evidence, and do not interrupt progress with redundant permission questions. This instruction applies to future Eristavi handovers and working sessions. Connected tool capabilities and service authorization remain binding; do not claim an action succeeded unless verified. Preserve philosophy, frozen semantics, CI/qualification rules, release safety and careful irreversible-action checks. **The standing authorization does not waive acceptance criteria or authorize previously excluded experimental full owned-compiler self-build tests.**

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
- **Latest qualified batch: PR #105, merge `8c625b1ece6a229844def93e2bf9563c14e9e273`.** Word-store aggregate leases, optional-identity member lowering, bounded collision-stable identity backing reuse and bitmap/split allocator reuse are qualified. The adversarial all-same-hash physical gate passed unchanged 8 MiB / 64 MiB limits. Current matched worker0 timing is roughly flat (~1.5% higher median wall time amid host variance); no whole-compiler speedup is claimed. Profile remaining complete-compiler phases (#51) and apply the same ownership/cost discipline to U1b aggregates, U2, U3 and U4.

## Start a new chat with this

> **MANDATORY:** Read the complete governing philosophy/semantics, applicable architecture/IR and CI contracts, and this complete handover. Follow Philosophy → Semantics → Architecture → Implementation, optimization-first after correctness/safety. Standing GitHub authorization does not waive acceptance or select experimental owned full self-build.
>
> **Resume at §73 and the linked optimization plan.** Current PR #106 is draft/unmerged; #73/#51 open. §72's exact source qualification passed, but later diagnostic/workflow edits at `c2423d5` introduced a failing GC-counter reconciliation and automatic expensive PR profiling. Smoke passed; compiler/runtime source did not change. First repair measurement/selection with cheap decoder checks, then one corrected current-source profile. Attribute boxed scalar/word-store work before ONE bounded structural pilot. Preserve independent verification of current, same-revision malformed dead/uncalled IR, original budgets, owner cleanup and ABI. Four graph micro-candidates remain rejected; the same-owner poll optimization alone has five-pair evidence. Qualify a final production code batch once; documentation-only updates need patch checks. No U1b merge/performance-risk acceptance or U2/U3/U4 completion is implied.

## Current verified status — read before historical sections

| Scope | Current status |
| --- | --- |
| Repository | https://github.com/eristavi/eristavi-lang |
| Latest qualified compiler/runtime merge | `8c625b1ece6a229844def93e2bf9563c14e9e273` ([PR #105](https://github.com/eristavi/eristavi-lang/pull/105)) |
| Exact tested #105 head | `f1fba11ff5e11791ad8c5d635fbf90873c686fa9` |
| Exact tested/merged tree | `0d8bf1f4a58f66a15bb9a89bd42f596091ed9c36` — identical, ordinary two-parent merge, unchanged base |
| Focused smoke | [41222208171](https://github.com/eristavi/eristavi-lang/actions/runs/41222208171): **36/36 PASSED**, including deliberately colliding full physical fixture |
| Four-platform full CI | [41222506854](https://github.com/eristavi/eristavi-lang/actions/runs/41222506854): **SUCCESS**, 469 discovered each. Linux GCC/Clang: 4 skips; ARM64: 112; macOS: 121 |
| Completed-batch qualification | [41222506873](https://github.com/eristavi/eristavi-lang/actions/runs/41222506873): three bootstrap C/D builds, repeatable=true, offline audit and unchanged source snapshots; owned static/offline integration passed with repeatable=false |
| Experimental full owned compiler self-build | Intentionally skipped; **NOT CERTIFIED** |
| U1a #77 physical acceptance | **QUALIFIED / MERGED**. #77 **CLOSED/completed**; original 8 MiB / 64 MiB gates preserved |
| Actual adversarial owned stress | 65,536 words / 4,096 pages, all initial identity hashes collide: **7,853,712 B phase peak**, **21,957,296 B traffic**, 72,682 graph allocations. Exact retained stress backing **6,653,840 B / 16,938 wrapper-body objects**, all reclaimed |
| Physical scope | Actual per-structure semantic-owner backing plus separate temporary/bookkeeping phase history. Shared region slack, diagnostic maps and shared caches are not attributed to arbitrary U1 owners; this is not process RSS or a global heap cap |
| Current independent C evidence | Refreshed 20/20 whole C-managed samples passed; source-hashed C inputs unchanged during later owned-only collision tuning. Not per-owner C allocation attribution |
| Performance | Five final-code AB/BA worker0 pairs: 8.135968 → 8.254257 s (0.9857×), roughly flat amid host variance. **No whole-compiler speedup claim**; #51 full compiler phase profiling remains open |
| U1a | Scalar/SSA/calls/recursion/effects/switches/strict native f64/provenance/bounded simplification plus scoped physical acceptance **COMPLETE within the adopted U1a boundary** |
| U1b #73 | **FUNCTIONAL SOURCE QUALIFIED; LATER DIAGNOSTIC FAILS; MERGE PENDING.** Exact source/test/workflow head `0a2ba594` passed full CI 41303717634 and qualification 41303717596. Later `c2423d5` changes diagnostic/CI/handover only: smoke PASS, hotspot GC-counter reconciliation FAIL in 41307434281. Same-owner poll reduction retains five-pair 6.24% one-fixture gain. Repair measurement/selector, then attribute word-read/boxing cost and evaluate one bounded structural candidate. PR #106 draft/open, #73/#51 open; no merge/risk waiver. See §73 and linked plan. |
| U2 #74 | New UIR managed Text/List/identity, checked failures, root maps and deterministic cleanup **NOT IMPLEMENTED** |
| U3 #75 | Direct frozen frontend → new UIR → production native target/artifact/cache integration **NOT IMPLEMENTED**. Existing adapter is isolated; #104 is test-only reference parity |
| U4 #102 | Redesigned UIR machine/legalization/artifact migration **NOT IMPLEMENTED / NOT QUALIFIED** |
| Production | Existing source language and default compiler pipeline retained; no new-UIR backend promotion |
| Environment / next stage | GitHub draft PR #106 active on `compiler/u1b-owned-aggregate-graph-20261031`; local checkout is restored; section 54 records current local validation. U1b aggregation is actively developed, not merged |

**Reading rule:** the opening and newest checkpoint (§73) govern current status; section 44 governs the accepted U1a boundary. Earlier keep-open and pending
statements describe their historical revisions. U1a acceptance does not certify
U2 managed GC/cleanup, U3 durable artifacts/source integration or U4 toolchains.
Documentation-only status reconciliation reuses unchanged implementation evidence
and must not trigger expensive compiler/runtime qualification again.

## 1. Verified repository checkpoint

Repository: https://github.com/eristavi/eristavi-lang

| Item | Revision / status |
| --- | --- |
| Main after this handover's merges | cd421d859e3372796e59ddf236944efc1b6aaddb |
| Main tree | c6a554e04c12d26c93650956709c5d57f1812ddf |
| PR #58 foundation | Merged: 6fb8b7bcd49418f398810ef9166acc888a35c4f5 |
| PR #59 verifier + bootstrap recovery fix | Merged: 8a2af1c95c0878a65aebbabb464ad1bf6c66db5e |
| PR #59 tested head | c2989f169f6c470f95c11cec2ec5368bd333a485 |
| PR #60 scalar-cell promotion | Merged: cd421d859e3372796e59ddf236944efc1b6aaddb |
| PR #60 tested head | 22b36c1de42a6bb1b6d54d03a9c69b7c49062082 |
| PR #60 tested tree | c6a554e04c12d26c93650956709c5d57f1812ddf |
| PR #57 | Separate legacy work; do not merge it as part of this redesign |

PR links: [#58](https://github.com/eristavi/eristavi-lang/pull/58),
[#59](https://github.com/eristavi/eristavi-lang/pull/59),
[#60](https://github.com/eristavi/eristavi-lang/pull/60),
[#57](https://github.com/eristavi/eristavi-lang/pull/57).

This session explicitly authorized merging #59 and #60. It did not authorize
unrelated PR merges. Verify future heads/checks and preserve user changes.

## 2. Working preferences and non-negotiable direction

- User: Revaz Eristavi. Preserve DESIGN_PHILOSOPHY.md and source semantics.
- Goal: a fast, reliable, readable language with its own offline native toolchain.
  C/Python are current bootstrap tools, not intended permanent dependencies.
- Keep `.eri` for source and compiler implementation; command `erist`.
  `.erist` is reserved for a distinct future purpose; `.erlx` was not selected.
- Major lowering/tool architecture decisions are made with the user before
  rebuilding each layer. Give a complete technical recommendation with reasons;
  avoid endless tiny design questions or unnecessary requests for permission.
- Work autonomously on authorized implementation, reversible fixes and draft PRs.
  Do not infer blanket permission for unrelated publication/merges.
- Use focused correctness checks with each slice. Batch expensive qualification
  at the completed integration boundary. Do not repeat unchanged 900-second runs.
- Report measured scope honestly. A small native probe, modeled byte counter or
  green CI does not prove whole-build speed, physical-memory qualification or
  full owned-runtime self-hosting. Do not multiply unrelated speedups.
- Give concise progress updates during long work. Do not spawn sub-agents unless
  the user or applicable instructions explicitly authorize delegation.
- Rust/Bazel references were research precedents, not dependencies or evidence
  that their complete designs fit Eristavi.

## 3. Architecture already agreed

The source language stays. Approved AST plus frozen semantic facts will eventually
construct one language-neutral typed UIR directly. There is no extra mandatory
source-close executable Typed IR in the new pipeline. The old Typed IR is removed
only after compatibility/integration gates pass.

The core has independent owned metadata, immutable SSA values, block parameters,
explicit operations/effects and independent verification. Temporary initialized
scalar cells are private construction only; canonical U1 contains no cells.
Mandatory promotion is part of U1, including the default pipeline.

U1a: pred/i64/strict f64, CFG/calls/switches/guards/locations, verification and
promotion. U1b: remaining integer widths and immutable aggregates. U2: managed
values, failures, resources and cleanup. U3: frontend/native integration. U4:
legalization, machine contracts/backends and artifact migration in reviewed slices.

Preserve checked signed Int64, strict binary64, explicit checked failures,
ordinary value versus identity semantics, and deterministic scoped resources.
Standalone terminal runtime defects terminate without cleanup; normal returns
and checked failures still require cleanup exactly once. Terminal traps promise
neither file flushing/durability nor persistent-lock release.

RevaSM is a peer machine target alongside x86-64, ARM64 and RISC-V. It is not a
layer through which other architectures must pass. Its explicit live-in/block
parameter threading conversion is an eventual measured U4 subtask. Keep the
machine OS-independent; platform/runtime/ABI boundaries carry portability work.

The existing 32-byte Eristavi value ABI stays at existing boundaries. Other
frontends using the universal core need not adopt it, Eristavi GC/Text/List,
failures or resources. New provenance/address architecture, moving GC and new
generic-template profiles remain separate reserved designs. Preserve existing
private-memory/generic compatibility paths until reviewed replacements exist.

UIR schema/profile/extension/verifier/runtime/ABI versions must enter relevant
future cache keys, separately from compiler identity. No public serialized UIR
format or new artifact extension is frozen. The module FS001 symlink-policy
change remains a separate unapproved decision.

## 4. Current implementation — what exists

The new modules are isolated. The production frontend/driver continues to use
the old compiler pipeline. Do not describe the lexer/parser/semantic architecture
documents as completed replacement implementations.

| Repository file | Role |
| --- | --- |
| src/compiler/u1_budget.eri | Scoped capacity/traffic/work reservations, cancellation, cleanup and counters |
| src/compiler/u1_words.eri | Safe radix-16 indexed storage, 16-word pages, fixed directory depth |
| src/compiler/u1_meta.eri | Owned pred/i64/f64 types, canonical signatures, source identities/spans |
| src/compiler/u1_ops.eri | Closed initial operation registry |
| src/compiler/u1_builder.eri | Nominal owner-scoped IDs, typed construction and private cells |
| src/compiler/u1_dominance.eri | Iterative simple Lengauer–Tarjan plus tree intervals |
| src/compiler/u1_verify.eri | Independent construction/canonical checks and reachable SSA |
| src/compiler/u1_promote.eri | Transactional pruned scalar-cell promotion |
| compiler/erist/c_backend.py | C-bootstrap checked-handler recovery-read fix |

Nine canonical operations currently exist: i64/pred constants, signed i64
add-overflow pair, pred.not, guard, jump, branch, return and f64 raw-bit constant.
Private construction operations 10/11/12 are cell.init/read/write. Primitive type
IDs are pred=1, i64=2, f64=3. Zero is absence, never a valid SSA operand/result.
There is no fake Void value. Logical bounded ID APIs are not a claim of packed
physical 32-bit storage: current ordinary Eristavi fields are Int-based.

`verify.construction` checks all records, including dead blocks, reachable SSA
availability and initializer dominance/order. `verify.verify` additionally
rejects any surviving cells. Invalid IR is distinct from budget exhaustion and
cancellation. Reports are observations, not executable publication capabilities;
unchanged revision numbers do not bypass revalidation.

Promotion indexes accesses, computes pruned live-in states/frontiers, places
parameters deterministically, renames with explicit stacks/undo, captures
simultaneous edge arguments, removes singleton trivial parameters, compacts its
rebuild plan and creates a separate cell-free function. It preserves input
records on success/failure. Late failure discards private output and retains
consumed request work/traffic. General redundant-phi SCC elimination is not
claimed. All supported scalar cells are eligible; no silent mutable fallback.

The verifier reuses instruction positions and edge-source slots as claim markers;
value coverage follows checked ranges/back-references. Dominator temporaries
share eleven physical words per block only across disjoint phases. Preserve the
phase-lifetime map in UIR_U1A_PROMOTION.md when modifying it.

## 5. Concrete next-step hazards — read before extending operations

The current registry is deliberately closed at operation 12. Some builder,
verifier and promoter paths classify cells by `op >= 10` / `op < 10`; some
successor walkers recognize only jump=6 and branch=7. Those tests are correct
for the current closed subset but MUST be generalized before adding op 13+.
Otherwise new arithmetic could be interpreted as a cell or silently removed.

Start with:

```sh
rg -n 'op >= 10|op < 10|op == 6|op == 7' src/compiler/u1_*.eri
```

Agree explicit operation classifications and a shared successor/schema contract
before implementing further operations/calls/switches. Preserve cell-free
publication and extend construction verification, promotion copying, reference
execution and malformed-IR tests together. Do not just add registry numbers.

Next work, in order:

1. Read the current U1 contract and inventory what is implemented versus required.
2. Prepare the remaining U1a representation/registry slice for joint review:
   scalar operations, function declarations/direct calls/effects/import contracts,
   zero/multiple results and multiway switch edge/case schema.
3. Implement agreed slices with independent semantic oracles and rejection tests.
   Include signed MIN/-1 traps for BOTH div and rem, sparse switches without
   allocation by largest case value, and strict Float environment/bit behavior.
4. Complete source-map consistency/synthetic origins/origin chains and proper
   revision/publication capabilities; current span checks are not that whole gate.
5. Measure complete physical allocation/GC behavior and matched larger stress.
   Integrate frontend/native lowering only after conformance and reviewed gates.

Do not replace the working compiler with the small scalar subset. Managed
values/failure continuations/resource ownership/cleanup algorithms still need
their U2 implementation/review and complexity budgets.

## 6. Validation and limits

Normal PR CI has four configurations: Linux x86-64 GCC/Clang, Linux ARM64 Clang
and macOS Clang. Both PR heads passed their normal CI before their merges.

| Evidence | Link / scope |
| --- | --- |
| PR #59 corrected CI | https://github.com/eristavi/eristavi-lang/actions/runs/41016431065 |
| PR #60 CI | https://github.com/eristavi/eristavi-lang/actions/runs/41017375980 |
| Completed-batch qualification | https://github.com/eristavi/eristavi-lang/actions/runs/41018345033 — passed |
| Post-merge main CI | https://github.com/eristavi/eristavi-lang/actions/runs/41019091503 — automatically triggered; see live result |

Local U1 batch: ten tests passed. Promotion: 18 before/after IR pairs, 88 independent
input cases with mathematical expected results and complete guard/fault/location
traces, plus eight negative scenarios. Covers diamonds/loops/sequential joins,
swaps, repeated loop-local initialization, irreducible graphs, dead code,
redundant parameters, unused destinations with faults, i64 bounds and f64 bits.

The independent dominator oracle checks 91 graphs and 2,816 answers. Bootstrap
tests also traverse 128/512/2,048-block chains. The verifier protocol now includes
41 scenarios after orphan/cycle regressions. Tests revalidate corruption without
revision increments and check Int64-max IDs/counts/ranges before offset arithmetic.

Native smoke compiles and executes the PASS IMPLEMENTATION written in Eristavi,
through the existing frontend, with bootstrap and owned runtimes. The new IR
programs' before/after behavior is independently evaluated in Python. There is
not yet an integrated native backend for the redesigned UIR. Native smoke is not
evidence that the new UIR already compiles whole Eristavi programs to machine code.

Native promotion smoke uses small joins/loops, swaps and resets, with one extra
verification. Bootstrap shape fixtures use eight extra verifications. Owned ELF
checks require static/import-free output, a non-executable stack and execution
with an unusable PATH.

The C-bootstrap CI failure was real: optimized Linux Clang recovery observed stale
pre-call identity state after cleanup/rethrow. PR #59 reloads source-variable
reads in checked handlers via standard C volatile lvalue reads. A minimal test
covering let/assign/return/expression handlers prints 0 before the fix and required
cleanup state 42 afterward; GCC and Clang resource tests pass. Normal expression
lowering and the native ABI are unchanged.

Selected budgets (policy, not measured optimal values):

| Scope | Selected limit |
| --- | --- |
| Qualification function peak modeled capacity / successful traffic | 8 MiB / 64 MiB |
| Development function peak / traffic | 64 MiB / 256 MiB |
| Shared metadata / request peak | 128 MiB / 512 MiB |
| Request successful allocation traffic | 2 GiB |
| Construction / each verification | 16,777,216 charged visits each |
| Promotion / request total work | 33,554,432 / 268,435,456 |
| Outstanding work batch / bulk cancellation interval | 1,024 visits / 64 KiB |

Counts and component envelopes are in UIR_U1A_BUDGETS.json and U1 contract §15.
The direct-IR diamond/loop/sequential fixtures at N=8/32/128 meet exact parameter
and argument counts. The largest sequential fixture records 8,206,560 peak modeled
bytes, 19,524,768 traffic bytes and 3,367,442 promotion work units. No gate was
raised to make it pass. Source hashes/per-case values are committed in
UIR_U1A_PROMOTION_EVIDENCE.json.

These counters cover conservative page-adapter charges, not every transient
object, allocator metadata or GC retention. Full physical memory qualification
and packed storage are not established. The largest owned graph/deep-chain
combined run previously timed out at 120 seconds; that result remains unqualified.
All 91 small graphs matched in a diagnostic run; a fresh 128-block owned chain
passed in about six wall seconds. Do not relabel this as a broad performance pass.

Completed-batch full qualification checks bootstrap compiler repeatability and
owned integration. It is distinct from the manually selected full owned compiler
self-build/repeatability profile. Full owned self-hosting remains unproven.
The final completed-batch qualification passed on tested head 22b36c1de42a6bb1b6d54d03a9c69b7c49062082. All three bootstrap jobs report repeatable=true, completed C/D compilers, a successful offline audit and unchanged source snapshot. Owned integration reports repeatable=false, no C/D compiler self-build and a successful offline audit with unchanged sources. The separate owned-self-build job was intentionally skipped. The merged main tree equals the tested head tree; no implementation changed after qualification.

## 7. Governing documents and decision records

Read current repository instructions/AGENTS.md if present, DESIGN_PHILOSOPHY.md,
LANGUAGE_SEMANTICS.md, CI_QUALIFICATION.md and relevant runtime/ABI contracts.
The present checkout had no applicable AGENTS.md when inspected.

Repository slice records: UIR_U1A_FOUNDATION.md, UIR_U1A_VERIFIER.md,
UIR_U1A_PROMOTION.md, UIR_U1A_BUDGETS.json, UIR_U1A_PROMOTION_EVIDENCE.json.

Design decision records are now published under [docs/architecture](docs/architecture).
The [project records index](docs/README.md) links every record and the archived
local experiments. Read the complete current contents before acting:

- Eristavi-Lexer-Architecture-2026-10-29.md
- Eristavi-Parser-Architecture-Proposal-2026-10-29.md
- Eristavi-Module-Architecture-Proposal-2026-10-29.md
- Eristavi-Semantic-Architecture-Proposal-2026-10-29.md
- Eristavi-Typed-Universal-IR-Proposal-2026-10-29.md
- Eristavi-UIR-U1-Contract-2026-10-29.md
- Eristavi-UIR-U0-Baseline-2026-10-29.md
- Eristavi-UIR-U1a-Budgets-2026-10-29.json
- Eristavi-UIR-U0-Evidence-2026-10-29.zip

The original U0 evidence archive is under
[docs/evidence/2026-10-30](docs/evidence/2026-10-30), alongside captured U0/U1
work archives, a per-file manifest and SHA-256 checksums. Do not reconstruct an
unseen decision document from a filename or old conversation summary. Read the
published contracts and their status before continuing.

Qualification artifacts for run 41018345033 (GitHub-reported archive digests;
retained for 14 days, not an independent local rehash):

| Artifact | ID | SHA-256 |
| --- | --- | --- |
| Bootstrap x86-64 GCC | 12961011043 | d0dac640d44c70197dddcdcbbe5e1b074566a9db2091020568cdb189c49653d5 |
| Bootstrap x86-64 Clang | 12961105702 | 457ce9a4c381f30989986770d0dbf3394bc0a2dccb7dedf074747146396a7552 |
| Bootstrap ARM64 Clang | 12960334209 | 814d9134bca9e1e126f0c7d8cc789a929d1dd533ec76cd4f07024be891b127e7 |
| Owned integration | 12960755760 | a7afb051f3b2040e58ab75789b6b78ddda8963e2cf1d9cdd44b43b7a0764f846 |

The U0 archive SHA-256 is
`63ee91cbec2b3d2f2d835e20396d533ee25a2f31543f899f77483f1d4d3ddeaa`.
Do not rewrite/relabel its raw measurements when recording later policies.
It pins inspected baseline PR #57 head 8af0ffe3350c737550c3ab0e6c3fa89f60f6f091.
It records 60 source-pipeline samples over 12 workloads and 30 corrected paired
native-verifier/runtime samples. Peak child RSS initially inherited launcher
memory; a controlled native launcher corrected the authoritative measurements.
Historical width-2,000 owned median around 16.56 seconds is different work from
the future initialized/checksum stress recipe. Timing noise precludes a narrow
5% gate; there is no measured new-UIR whole-build speedup.

## 8. Reproduction and recoverable workspace

Current workspace, optional accelerator only:
`/workspace/scratch/1848da8b628a/eristavi-u1a`.
The implementation checkout was verified clean on main at cd421d859e3372796e59ddf236944efc1b6aaddb with the tested tree c6a554e04c12d26c93650956709c5d57f1812ddf. A documentation-only branch docs/uir-handover-2026-10-30 publishes HANDOVER.md after this code checkpoint; it does not alter implementation or qualification inputs.

With ordinary project dependencies installed:

```sh
python3 -m unittest discover -s tests -p 'test_u1*.py' -v
python3 -m unittest discover -s tests -p 'test_c_failure_recovery.py' -v
```

Cached Unicode dependencies, if still present:
`/workspace/scratch/1848da8b628a/uir-u0/deps`.
Use `PYTHONPATH` with the checkout and those dependencies only if needed;
prefer the repository's normal install instructions in a fresh environment.

Logs/probes from `uir-u0`, `uir-u1a-work`, `uir-u1a-verifier-work`,
`uir-u1a-promotion-work` and the budget worksheet are now preserved in the
[local evidence archives](docs/evidence/2026-10-30). See
[recovery instructions](docs/README.md#recover-the-workspace) for original paths,
checksums and exclusions. A private Clang 18 toolchain
was extracted under `uir-u1a-promotion-work/clang-toolchain`; it needs its
`usr/lib/x86_64-linux-gnu` on LD_LIBRARY_PATH. It is optional and not a repository
dependency. Do not rely on temporary tool binaries or directory survival.

Use committed tests/docs and GitHub evidence to recover. Artifacts have 14-day
retention. Fetch refs and compare trees/hashes; do not assume local branch names
or old scratch binaries describe current main. Shell fetch works; GitHub connector
Git Data APIs were used for publication with tested-tree equality and expected-head
guards. Never expose credentials or signed artifact transfer URLs.

## 9. Historical self-build limit — do not restart it automatically

The last recorded full owned B-to-C attempt was at PR #47 head
3b3841e5ffe25dbfe1aa87389e820135b61bbcf7 and timed out at 900 seconds, producing no
compiler C/D. Analysis completed in 224.810s, typed lowering in 340.098s and the
then-broad universal-lower phase remained active 334.461s at timeout. That broad
phase included typed validation; it did not prove actual Universal IR construction
was the cause. Later probes/optimizations and the new architecture do not turn
that incomplete attempt into a successful owned self-build.

Historical PR #50 qualified bootstrap repeatability/owned integration at main
9e8e460cd69f7f1b4ebda56eed97504ccf6e54d7, CI run 40700196736, qualification run
40701157136. Its owned wide-local verifier microbenchmark was 7.124s to 2.872s,
not a full-build speedup. The current redesign supersedes the old instruction to
immediately resume that combined microbenchmark investigation.

No further implementation should be inferred from this handover's existence.
Resume the user's next instruction and the agreed remaining U1a work.

## 10. Post-handover update — U1a classification safety slice (2026-10-30)

Branch: `compiler/u1a-opcode-classification-harden`, based on documentation branch `docs/uir-handover-2026-10-30` at `09f260beceea33fd28a2972b369b210fdcd57259`. This work is proposed independently of the existing PR #61 and is not merged into main. PR #61 should be merged/reconciled before retargeting this follow-up branch to main. Preserve any newer user-uploaded documents and never overwrite the original handover branch.

### Completed in the proposed branch

1. Reverified the main merge checkpoint and found the current closed set of 9 canonical and 3 private-cell operations.
2. Audited numeric opcode thresholds and hard-coded jump/branch successor walkers in `u1_builder`, `u1_verify`, and `u1_promote`.
3. Added explicit operation-category helpers to `u1_ops`: `isCell`, `inlineEdges`, and a non-range `terminal`.
4. Made all three compiler components consume the shared classifications, including promoter edge copying and terminal emission. No new opcode, wire format, runtime ABI or production integration.
5. Added a compiled U1 opcode-category regression, including unknown future IDs, and a guard against reintroducing numeric cell thresholds.
6. Recorded an extension audit and prerequisite gates in `UIR_U1A_OPCODE_AUDIT.md`.

Status: **proposed implementation / draft review**. The full U1a contract/architecture documents described in section 7 were still not present in the checked GitHub main tree when this isolated hardening slice was prepared. No complete U1a operations/calls/switch/strict-Float slice is claimed. No full owned-runtime self-build or 900-second run was started.

### Validation and next handover

Source-pattern replacement and changed-path scope were checked before commit. Compiled runtime tests and hosted CI must be independently verified against this branch's final commit; none are claimed solely from this record. Run `python3 -m unittest discover -s tests -p 'test_u1*.py' -v` for focused validation. Per `CI_QUALIFICATION.md`, compiler changes require final-revision four-platform CI and completed-batch qualification before merge; do not start expensive qualification for every helper.

Next: reconcile any newly uploaded external U1 contract/design files against `HANDOVER.md`; explicitly approve a complete opcode/type/effect and switch-edge schema before extending beyond op 12, then implement independently tested scalar/call/switch/strict-Float slices. Keep the old production compiler until U3 gates are met.


## 11. Continuation — isolated U1a eager predicate slice (2026-10-30)

Branch `compiler/u1a-predicate-ops` is stacked on draft PR #62 `compiler/u1a-opcode-classification-harden`, which itself depends on documentation PR #61. **These are draft review branches, not merged main functionality.** The complete architecture records have been found at `docs/architecture/` on PR #61's documentation branch; most importantly, read `Eristavi-UIR-U1-Contract-2026-10-29.md` before designing additional operations. Its status distinguishes agreed full U1 from the implemented narrow U1a subset.

### Changes proposed in this slice

- Read full U1 contract for operation typing, eager predicate semantics, independent verification, source origins and effect order.
- Implement pure `pred.and` (op 13) and `pred.or` (op 14), exact pred/pred arity and pred result, with zero payload/attribute.
- Extend `u1_builder` with typed construction helpers; extend independent verifier's closed operation contracts, including dead blocks.
- Extend the independent Python U1 reference evaluator and promotion fixtures for all Boolean combinations before/after transactional SSA promotion.
- Replace outdated canonical-test assumption that all canonical opcodes are below 10; cells remain exactly 10/11/12.
- Add positive/malformed verifier tests and update opcode-classification probe to reject 15 and 16.
- Record the scope and next gates in `UIR_U1A_PREDICATES.md` and preserve the earlier classification audit.

Status at commit creation: *proposed, awaiting focused CI*. Do not report compilation, native tests, or full qualification as passed until the exact new commit has verified results. No compiler-wide or 900-second owned self-build was started. No production frontend/driver or runtime ABI modification.

Next task: validate latest CI results and fix any regressions; reconcile the now-published complete U1 contract and plan the remaining scalar integer ops (including signed MIN/-1 on div/rem), calls/effects, multiway switch side tables and strict Float boundary. Keep each slice independently verifiable; do not merge stacked draft PRs or widen specifications without reviewed evidence. Once parent PRs merge, retarget this branch to main and requalify final code revision according to `CI_QUALIFICATION.md`.

## 12. Verified merge checkpoint — U1a opcode and predicate batches (2026-10-30)

**This section supersedes the pending-PR statuses in sections 10–11.** They are preserved as the original pre-merge handover history, not as current instructions.

### Repository state and exact evidence

| Item | Verified result |
| --- | --- |
| Current code-bearing main merge | `b5e15fd39e4166d5aba8a66ba44b8265f3d80d23` |
| Current code-bearing main tree | `e3bc4e22181684c054a28be24746d42e496d8f0d` |
| PR #61 — architecture, historical evidence, initial handover | Merged `e55cb7edd90a6f52017554aded7a05c309c5b4a4` |
| PR #62 — explicit operation classes and inline CFG edge audit | Merged `d3ed1ad37881d8887d9c6919d401ef28e43745e2` |
| PR #63 — eager `pred.and` / `pred.or` and SSA differential tests | Merged `b5e15fd39e4166d5aba8a66ba44b8265f3d80d23` |
| PR #63 final tested head | `9d4faa9b15560f660b6aedef72e588a721393d53` |
| PR #63 final tested tree | `e3bc4e22181684c054a28be24746d42e496d8f0d` |
| Normal CI | Four/four passed on both PR #62 and PR #63; PR #61 also four/four |
| Completed-batch full qualification | [Run 41059473867](https://github.com/eristavi/eristavi-lang/actions/runs/41059473867): **success** on the exact PR #63 tested head |
| Qualification jobs | Three bootstrap repeatable/offline Linux builds and owned integration **passed**; separate full owned-compiler self-build was **skipped by design** |

GitHub reports that both code-bearing merge-commit trees were exactly equal to their corresponding tested head trees, and final `main` tree is identical to the PR #63 fully qualified tree. Thus no untested implementation was introduced by these merge commits. The documentation-only checkpoint appended here does **not** change compiler/runtime inputs; any newer main commit should still be inspected before new code work.

### What is now on main

- The isolated U1a scalar builder/verifier/SSA promoter from PRs #58–60 remains in place.
- `u1_ops` now classifies private cells explicitly as **only operations 10, 11 and 12**, and describes the existing inline jump/branch successors through a shared helper.
- Canonical op 13 `pred.and` and op 14 `pred.or` provide **eager**, pure `pred,pred -> pred` semantics. These do **not** change Eristavi source-level short-circuit evaluation.
- Independent verification rejects invalid types, arity, payloads and malformed unreachable instructions. Reference evaluation and before/after SSA-promotion fixtures include all Boolean truth-table cases and a merge with a temporary scalar cell.
- `UIR_U1A_OPCODE_AUDIT.md` and `UIR_U1A_PREDICATES.md` document the exact scope.
- The agreed architecture and full contract are in `docs/architecture/`, particularly `Eristavi-UIR-U1-Contract-2026-10-29.md`.

### Continuing from here

1. Read the current `main` commit, this handover, `DESIGN_PHILOSOPHY.md`, the agreed U1 contract and `CI_QUALIFICATION.md` before modifying code.
2. **Do not merge legacy PR #57** or unrelated PRs merely as part of this compiler redesign; their scopes remain separate.
3. Next implementation slices are U1a remaining pred/i64 operations, especially explicit signed/unsigned wrapping/overflow/comparison and division/remainder traps for **both zero divisor and signed MIN/-1**; then strict binary64 and its environment/bit guarantees. Define call/effect and multiway switch case/edge contracts explicitly before implementing them.
4. Preserve effect/fault and diagnostic origins, independent typed and dead-block verification, transactional cell promotion, capacity/work quotas and a cell-free canonical result.
5. Preserve the **existing production frontend/native compiler** until U2/U3 conformance gates. U1a cannot currently compile the full language through the redesigned native pipeline.
6. Full owned-runtime compiler B-to-C/C-to-D self-hosting remains unqualified. Never report the intentionally skipped owned self-build as a pass; do not automatically repeat the historical 900-second attempt.
7. Use focused tests for each reviewed slice, batch full qualification per `CI_QUALIFICATION.md`, and record final head/tree identities and observed evidence before merges.

This section is a documentation-only checkpoint. It is not a new operation contract, benchmark, optimizer or replacement compiler.


## 13. Next isolated U1a integer operation slice — 2026-10-30

Branch `compiler/u1a-i64-arithmetic` is based on the merged main checkpoint `549ff783d23263caa53769f8ae273d350cf2b2b3`. Follow the approved full `docs/architecture/Eristavi-UIR-U1-Contract-2026-10-29.md`, the locked `INTEGER_REMAINDER.md`, this handover, and `CI_QUALIFICATION.md`. Previous PRs #61–64 are merged and not blockers.

Changes proposed:
- Add exact i64 wrapping add/sub/mul, signed subtraction/multiplication overflow pairs, unsigned add/subtract/multiply overflow pairs, and ten signed/unsigned integer comparison relations. Keep legacy signed addition-with-overflow ID 3 unchanged. IDs 15–23 are **private implementation IDs**.
- Update typed U1 builder/closed opcode registry and independent verifier, including rejection of invalid operation attributes/modes and malformed unreachable instructions.
- Extend the independent Python scalar evaluator with unsigned bit-vector handling and compare modes. Add a before/after SSA promotion matrix over 11 x 11 signed boundary pairs and a cell-mediated diamond merge with both branch outcomes.
- Extend the opcode-known probe and write `UIR_U1A_I64_ARITHMETIC.md`.

Status at first commit: **implementation candidate, CI and qualification pending**. Do not claim compiled tests pass until an exact final revision is checked. No merging or production pipeline replacement is authorized solely by this checkpoint. Run focused U1 suites and normal four-platform CI, then completed-batch full bootstrap/owned integration qualification per policy before any merge. The full owned compiler self-build remains a separate explicit experiment.

Next: independently specify and implement trapping signed/unsigned `i64.div` and `i64.rem` with zero and MIN/-1 fault outcomes and stable diagnostic origins. Follow with the strict binary64 profile, direct call/effect contract, sparse switch side tables and full source-provenance work. Keep U1a isolated until U2/U3 compatibility gates.
### CI failure and corrective change on PR #65

The first i64 commit `8df153aa314a431f2e85155101a1e9748aff7e44` failed the ARM64 test suite because `i64-merge` did not meet the expected SSA promotion shape. Audit revealed a numeric opcode threshold left in `u1_promote.eri:prepare`: `instruction(state,cursor,0) >= 10`. It treated newly introduced canonical operations as private cells.

The corrective commit replaces the threshold with `ops.isCell(...)` and strengthens `tests/test_u1_foundation.py` to reject both `op >= 10` and direct instruction-opcode threshold checks. The original independent i64 tests and the one-parameter/two-edge diamond assertion remain mandatory. See `UIR_U1A_OPCODE_AUDIT.md` and `UIR_U1A_I64_ARITHMETIC.md`.

**Re-run CI on the exact corrected revision.** Do not merge or claim completion based on the failed first run; preserve production compiler unchanged. Full owned-compiler self-build remains a separate experiment.


## 14. Verified U1a i64 arithmetic merge checkpoint — 2026-10-30

**This section supersedes the historical pending and failed statuses in section 13**; do not repeat the initial defect or treat the first failing revision as final.

### Git and qualification evidence

| Item | Verified result |
| --- | --- |
| Merged compiler PR | [#65](https://github.com/eristavi/eristavi-lang/pull/65), **merged** |
| Code-bearing main merge commit | `2139a59c16f4cca4bf413f37d42343dbea27c99d` |
| Final validated PR head | `cf27e21e5a4b9af5809c86ee6be92807de25b5ca` |
| Final validated / merged code tree | `0ed9d786b3132aeec6d8d8747f1d317dd9ca76bd` (identical on merge and qualified head) |
| Four-platform normal CI | [Run 41074920601](https://github.com/eristavi/eristavi-lang/actions/runs/41074920601), **success**: Linux GCC, Linux Clang, ARM64 Clang and macOS Clang |
| Completed-batch full qualification | [Run 41076097753](https://github.com/eristavi/eristavi-lang/actions/runs/41076097753), **success**, exactly on `cf27e21` |
| Full qualification jobs | Three repeatable bootstrap/offline Linux builds + owned integration: **passed** |
| Separate full owned-compiler self-build | **Skipped intentionally**; remains unqualified |

The first attempted revision `8df153aa` failed a real `i64-merge` SSA shape test due to the missed `op >= 10` classification in `u1_promote.eri:prepare`. The corrected final revision uses `ops.isCell`, retains the original strict merge test, and adds a regression guard against direct opcode threshold comparisons. Only the corrected final revision is qualified.

### Implemented and limits

- Typed isolated U1a i64 ops 15–23: wrapping add/sub/mul, ten comparison relations, signed sub/mul overflow, and unsigned add/sub/mul overflow, in addition to preserved signed add overflow op 3.
- Exact 64-bit wrapped results and explicit signed/unsigned overflow predicates, including when the mathematical result overflows.
- Independent builder/verifier payload and type contracts, malformed unreachable-IR tests, and Python boundary/differential execution of two new promotion fixtures.
- `UIR_U1A_I64_ARITHMETIC.md` and `UIR_U1A_OPCODE_AUDIT.md` contain details and the fixed classification defect.
- The **production Eristavi frontend/native compiler remains unchanged**. These operations are in the isolated U1a IR, not yet integrated into native application compilation. The code is not an entire U1a implementation.

### Next safe implementation steps

1. Inspect current main and this checkpoint before starting a new branch; keep historical branch statuses in earlier sections as historical context.
2. Next isolated U1a slice: implement typed signed/unsigned `i64.div` and `i64.rem` with terminal faults for zero divisors and signed MIN/-1 on **both** operations, truncation toward zero, signed remainder sign, independent exact evaluator and fault-location preservation. Do not rely on target-language undefined division behavior.
3. Add malformed-IR, unreachable-block, SSA-promotion, fault-order, location, cancellation and budget-recovery tests. Keep each scope separate from source-level diagnostics: source-known invalid expressions remain a frontend semantic responsibility.
4. After integer division/remainder, continue strict f64 under a controlled execution environment; separately define direct call/import effects and sparse multiway switch storage/verification.
5. Follow `CI_QUALIFICATION.md` on each completed compiler batch; reserve the full owned-compiler self-build for a separately authorized profile. Do not auto-merge unrelated open PRs (#57/#31/#18/#13).
6. Preserve frozen Eristavi syntax/semantics, historical and production compatibility, transactional cell-free U1, capacity/work accounting, and the U2/U3 integration gates.

This post-merge handover update is **documentation only**. It makes no claims of new test execution or benchmark results beyond the cited GitHub runs, and changes no compiler input or code.


## 15. Proposed isolated i64 division/remainder continuation — 2026-10-30

Branch `compiler/u1a-i64-divrem` is based on `main` commit `c500c2d8f32cc487738c459f659377db340f41f3`, following completed documentation PR #66. **This is an implementation candidate, not yet qualified or merged.**

- Add private op 24 `i64.div.signed`, 25 `i64.rem.signed`, 26 `i64.div.unsigned`, 27 `i64.rem.unsigned`; all have exactly two i64 SSA operands, one i64 result, zero payload/attributes and an instruction LocId. Private cell IDs remain **only 10/11/12**; existing 1–23 stay unchanged.
- `ops.mayTrap` distinguishes guard/div-rem potentially terminal faults from CFG terminators. A successful division/rem remains a normal sequential instruction. Zero divisor traps with code 2 (`integer_zero_divisor`), and signed minimum/-1 traps for **both signed division and signed remainder** with code 1 (`integer_overflow`), producing no value on the faulting execution.
- Exact signed division truncates toward zero; signed remainder follows `a=q*b+r` and the dividend's sign. Unsigned operations reinterpret the same two i64 inputs as unsigned 64-bit words.
- New independent Python reference evaluator and mathematical expectation oracle cover 16×16 boundary values, signed and unsigned quotient and remainder, diamond SSA cell promotion (one block parameter/two edge arguments), and first-fault/location order with a guard before an **unused** signed remainder and a later unsigned division. Tests must match before/after promotion with exact trap category, LocId and trace.
- Independent verifier rejects malformed payload/extra, wrong operand/result type/arity, missing instruction LocId, and malformed unreachable operations. Existing resource limits, cancellation, fault-injection and producer-identity checks remain in force.
- The new `UIR_U1A_I64_DIVREM.md` is the implementation contract summary. No production frontend/backend/runtime integration or new language semantics is implied; source-known invalid expressions remain a frontend semantic concern. No full owned-compiler self-build was initiated.
- **Before merge:** focused tests and all four ordinary CI platforms must pass on final head, followed by the explicit completed-batch full qualification under `CI_QUALIFICATION.md`. Record exact source tree/commit and CI evidence in the next handover. Never use earlier green revisions if code changes.

Next architecture slices: strict IEEE binary64 with controlled floating environment, direct call and import effects, sparse switch case/edge contracts, then source origins and U2/U3 integration. Do not touch unrelated PRs.
### PR #67 initial CI correction

The first implementation head `a29ad46` failed the new `divrem-arity` verifier protocol on ARM64/macOS. Diagnosis from a focused CI stdout-tail assertion identified **a test expectation error**: the verifier's global canonical operand-pool scan rejects the deliberately shortened operand count in V2 **block 0**, before per-block scanning. The initial test had incorrectly expected block 1. The new revision retains the same malformed mutation and rejection but asserts V2/block 0; the independent verifier and arithmetic semantics were not modified. The diagnostic assertion in `test_u1_verifier.py` was also improved to report actual probe failures. Reverify on the exact corrected head and do not merge based on the initial failing run.


## 16. Verified PR #67 merge and qualification checkpoint — 2026-10-30

**Supersedes the historical draft/failure statuses in section 15.** GitHub PR [#67](https://github.com/eristavi/eristavi-lang/pull/67) is merged. The source compiler remains the existing production pipeline; this change adds operations to the isolated U1a redesign only.

| Evidence | Verified status |
| --- | --- |
| Merge commit on `main` | `4277e1426040c03a74c936aca1943deb9380d680` |
| Final tested PR head | `e8c4d39bd30d23b5bb89e3307cafb9285cd722d0` |
| Tested and merged Git tree | `80db07e7eaaa0fea55a4f928bbb032b2bae6e506` — identical |
| Four-platform normal CI | Successful: Linux x86-64 GCC/Clang, Linux ARM64 Clang, macOS Clang |
| Full qualification | [GitHub Actions 41098748098](https://github.com/eristavi/eristavi-lang/actions/runs/41098748098): **success** on exact tested head |
| Full qualification jobs | Three bootstrap repeatability/offline jobs and owned integration **successful** |
| Separate experimental full owned compiler self-build | **Skipped intentionally; not qualified** |

The initial verifier-protocol test failure on earlier PR revisions was a mistaken expectation about block attribution; the independent verifier correctly reported V2/block 0 for orphaned operands. The corrected final test remains strict. Do not regard the earlier failed heads as release evidence.

**Implementation now on main:** signed/unsigned i64 quotient and remainder, zero-divisor and signed MIN/-1 terminal faults, original LocId preservation, independent integer oracle, exact SSA promotion and malformed/dead-block verification. See `UIR_U1A_I64_DIVREM.md`.

### Four-phase work authorized for the current continuation

1. **PR #67 is merged and documented here.**
2. **Finish isolated U1a:** strict binary64 arithmetic and comparisons, direct calls/signatures/import effect contracts, sparse switches with shared successor traversal, required location/provenance and verification revisions; preserve first-fault order, budget accounting, cancellation and cell-free SSA publication. Favor small independently verified changes over an unreviewed all-at-once rewrite.
3. **U1b and U2:** remaining fixed integer widths and immutable aggregates first, then managed values, checked-failure continuations, resource ownership/cleanup, rooted runtime adapters. No speculative ABI or new source syntax.
4. **U3 integration:** AST plus frozen semantic facts construct the approved language-neutral UIR directly; retain Stage-0 and the current native compiler as differential oracles. Promote one native target only after matched output, diagnostics, runtime traps, memory/cleanup and representative module/generic cases pass. Do not retire legacy intermediate representations prematurely.

The implementation order, non-goals and verifiable acceptance gates are expanded in `docs/architecture/ERISTAVI_U1_TO_U3_EXECUTION_PLAN.md`. This plan is an engineering staging document, not authorization to declare unfinished stages complete.

**Current remaining U1a**: strict Float, direct calls/import effects, sparse multiway switch/edge tables, full provenance and revision discipline. **U1b, U2, U3 remain separate major implementation milestones.** No later stages are claimed finished here. Every compiler code PR still requires four-platform CI and completed-batch qualification before merge under `CI_QUALIFICATION.md`. The separate 900-second owned compiler self-build remains a manual, unqualified experiment.


## 17. Verified strict Float and synthetic-origin merge checkpoint — 2026-10-30

**Repository state verified on GitHub after separate CI and qualification runs.** `main` is now `da18809210bafd77885596ccf9059b7a533a0fd7`. PR #69 and PR #70 are **merged**, not pending as in earlier sections.

| Slice | Tested PR head | Merge | Four-platform CI | Completed-batch qualification |
| --- | --- | --- | --- | --- |
| [#69 strict f64](https://github.com/eristavi/eristavi-lang/pull/69) | `2e6fb223748adbe539a0e8fbe2b381a3e4a5c718` | `f1b955b4f21b6cbcffdcbd9f5fe14a9e4d592606` | [41102130453](https://github.com/eristavi/eristavi-lang/actions/runs/41102130453) success | [41104201269](https://github.com/eristavi/eristavi-lang/actions/runs/41104201269) success |
| [#70 owned source origins](https://github.com/eristavi/eristavi-lang/pull/70) | `116c79c9dc911c72f6048febbeadec5936309506` | `da18809210bafd77885596ccf9059b7a533a0fd7` | [41107778150](https://github.com/eristavi/eristavi-lang/actions/runs/41107778150) success | [41108898014](https://github.com/eristavi/eristavi-lang/actions/runs/41108898014) success |

#70 was deliberately re-merged against #69's strict Float verifier before its final qualification; **the tested PR #70 Git tree and merged `main` tree are identical** (`37d492dec2b7f9b366681329fc0bb037191a50d9`). All four normal CI platforms passed on both PR final revisions, as did the three bootstrap/offline jobs and owned integration. The separate experimental full owned-compiler self-build was intentionally skipped and remains unqualified.

Implemented, isolated U1a: private binary64 add/sub/mul/div/neg and six comparisons with exact-rational expected-results oracle and before/after SSA promotion tests; owned synthetic source roots, bounded strictly acyclic origin chains, and independent malformed source/anchor rejection. **Not implemented here:** complete native strict floating-environment adapter, multi-parent origin chains, full revision-bound publication capabilities, exported artifact remapping, broader runtime integration.

### Concurrent work — not yet merged or qualified

- [PR #78](https://github.com/eristavi/eristavi-lang/pull/78), `compiler/u1a-function-declarations-calls`: owned declared FunctionId/signatures and direct-call structural verifier. Initial first CI failed on an Eristavi `else if` parse error in a builder edit; corrected on subsequent revision, no green-head qualification yet. Full multi-function execution, trusted import contracts and SCC effect derivation remain issue #71.
- [PR #79](https://github.com/eristavi/eristavi-lang/pull/79), `compiler/u1a-sparse-switch`: typed sparse i64 switch case tables, common successor iterator and differential/malformed tests; CI/qualification pending. Issue #72 governs release gate.
- Both drafts originated before the #70 origin merge. **Reconcile both with current `main` and retest final merged integration trees before any merge.** Do not use old green head/partial CI as qualification. Avoid unrelated PRs.
- [Issues #73–#75](https://github.com/eristavi/eristavi-lang/issues/73) remain distinct substantial U1b (extra widths + immutable aggregates), U2 (managed values, checked failures, cleanup, roots), and U3 (direct frontend→UIR and one-native-target) implementation gates. Issues #76–#77 retain strict native f64 and complete origin/revision goals.

**Next safe steps:** diagnose and fix each draft from its actual CI logs; finish independent call execution and switch semantics; rebase/merge **only tested** branches one at a time; update this handover after each qualified merge; continue U1b→U2→U3 behind working compiler compatibility gates. Keep the historical 900-second experimental B→C self-build out of automated qualification. Do not report completed redesign or v0.1.0 from isolated UIR tests.


## 18. U1a direct calls + switches integration candidate (2026-10-30)

- Branch `compiler/u1a-calls-switch-integration` combines **both** [PR #78](https://github.com/eristavi/eristavi-lang/pull/78) typed owned direct FunctionId declarations and [PR #79](https://github.com/eristavi/eristavi-lang/pull/79) sparse i64 switches, including their original head commits as Git parents.
- Three shared-line conflicts resolved explicitly: known opcodes 34/35, dynamic call operand count versus switch selector count, and foundation opcode probe range. Shared builder/verifier changes otherwise retained from both branches, with their focused suites.
- Candidate documentation in `UIR_U1A_CALL_SWITCH_INTEGRATION.md`. **Status at creation: unqualified integration; do not merge before CI+completed-batch qualification on exact final revision.**
- These U1a features are still isolated UIR. Full function-call execution, imported effect trust and SCC summaries remain pending. Do not claim U1a complete; U1b/U2/U3 remain separate.


## 19. Stacked U1b narrow scalar integration candidate (2026-10-30)

- Branch `compiler/u1a-u1b-integrated-narrow` stacks original PR #81 i8/i16/i32 TypeIds and PR #82 exact-width constant op 36 onto U1a call+switch integration PR #83. It preserves original PR #82 ancestry (including PR #81).
- Reconciled type metadata, builder constant checks with dynamic call result reservations, independent verification, opcode registry 34/35/36, shared SSA/differential and malformed-IR suites; combined test matrix expects 35 promoter fixtures.
- Full conflicts/limits recorded in `UIR_U1B_COMBINED_INTEGRATION.md`.
- **At creation this is an unqualified integration candidate.** The original green CI on #81/#82 does not qualify code combined with U1a PR #83; run fresh four-platform CI and completed-batch qualification on exact final merged tree after U1a base is stabilized.
- Remaining U1b: width-specific arithmetic and immutable aggregates. U2 managed values/failures/resources and U3 frontend→UIR/native integration have not been implemented by this PR. Do not retire old pipeline or run historical owned full self-build.


## 20. Proposed U1b narrow wrap/overflow/comparison slice (2026-10-30)

- Branch `compiler/u1b-narrow-arithmetic` stacked on U1a/U1b integration PR #84; operation IDs 37–40 cover exact i8/i16/i32 wrapping add/sub/mul, signed/unsigned overflow pairs and ten comparisons via explicit width/mode attributes.
- Independent verification rejects mixed widths, invalid operand/result types/modes and malformed dead instructions. `tests/test_u1_promotion.py` adds three width-specific direct oracle fixtures and an i8 cell diamond, totaling **39** promotion snapshots; all original U1a/switch/call tests remain required.
- Details and residual gates: `UIR_U1B_NARROW_ARITHMETIC.md`.
- **Status at commit creation: draft implementation, CI/qualification not yet validated**. Requalify after PR #83 and PR #84 have been merged and the final tree reconciled; do not merge or retire the production compiler before the complete gates.
- Still open: narrow div/rem, immutable aggregate U1b, U1a multi-function execution/imported effects, strict native Float, complete origins, U2 managed/failure/resource profile, U3 direct frontend→UIR/native adapter.


## 21. Proposed narrow division/remainder slice (2026-10-30)

- Branch `compiler/u1b-narrow-divrem` is stacked on `compiler/u1b-narrow-arithmetic` (PR #86) after the narrow type/constant stack (PR #84), itself based on call+switch integration (PR #83).
- Private op41 and op42 implement signed/unsigned i8/i16/i32 division and remainder with exact terminal trap semantics: zero divisor code2 and signed min/-1 code1 for **both div/rem**, original LocId and no produced value on fault.
- Independent exact arithmetic oracle and SSA promotion use 12 direct width/signedness/op fixtures and one i8-cell diamond with first-fault ordering. The suite expects **52** before/after promotion snapshots. Malformed verifier tests include bad mode, width, operand/result type, location and unreachable records.
- Full details: `UIR_U1B_NARROW_DIVREM.md`. **At initial commit: draft/unqualified, no merge**. Require four-platform CI and full completed-batch qualification after parent PR merge/rebase, and verify final tested-versus-main Git trees. Do not run 900-second owned experimental compiler self-build by default.
- Immutable U1b aggregates and all U2/U3 native/frontend tasks remain; this does not change frozen language or current production lowering.


## 22. Verified recovery checkpoint after PR #84 merge — 2026-10-30

This section supersedes older *current-state* instructions in sections 18–21; their original proposed-branch statuses are retained as history.

### Main and qualified integration

- GitHub `main` is now merge commit `c9750bb6f792a2432016df98ea21149fbc7ccca5`, merging [PR #84](https://github.com/eristavi/eristavi-lang/pull/84) at exact head `50cb9802f51d7f0da283b43bd6f789018a4eb5bd`.
- The merged tree is `370dbc972f2b3c0975003ba8fc1f0186ec9020a9`, identical to the qualified PR #84 head tree. Four normal CI jobs passed on [run 41120676739](https://github.com/eristavi/eristavi-lang/actions/runs/41120676739), and completed-batch [qualification 41123080745](https://github.com/eristavi/eristavi-lang/actions/runs/41123080745) passed its three Linux bootstrap/offline jobs and owned integration; separate experimental owned compiler self-build remained skipped.
- The previous [PR #83](https://github.com/eristavi/eristavi-lang/pull/83) merges both direct-call PR #78 and sparse-switch PR #79 histories, with merged commit `244d392582c2ef3be9b0804545886008744a9827`. Its exact tested head `ef441fe6dc6d0a8d0f05fdf45efdb9290771b240` passed normal CI [41119775019](https://github.com/eristavi/eristavi-lang/actions/runs/41119775019) and full completed-batch qualification [41121497695](https://github.com/eristavi/eristavi-lang/actions/runs/41121497695); tested and merged tree `bfda0d1278a8185b2d48a6e24114f5ed10e743fa` matched.
- Original PRs #81 and #82 remain historical open drafts but their combined narrow-type/constant contents were integrated in #84. Do not merge their separate old heads again.

### Current unmerged development

- [PR #86](https://github.com/eristavi/eristavi-lang/pull/86): narrow i8/i16/i32 wrap, overflow and comparisons. Four-platform CI [41122060676](https://github.com/eristavi/eristavi-lang/actions/runs/41122060676) succeeded on `602abcea050e0d8f7c55715982bec620ec70c447`; completed-batch qualification of the exact final integrated tree is **not yet established**. Its base is the now-merged PR #84 branch and must be reviewed/retargeted to current `main` before merge.
- [PR #87](https://github.com/eristavi/eristavi-lang/pull/87): narrow division/remainder stacked on #86. First CI [41122703352](https://github.com/eristavi/eristavi-lang/actions/runs/41122703352) failed on **all four platforms** because `tests/fixtures/u1_verifier.eri` referenced absent `protocol.Harness.alternate`; `test_u1_verifier.U1VerifierTests.setUpClass` could not bootstrap-compile the protocol. A focused correction in commit `bca23a6f09f37e44e95f0e155711c9e479a258d4` added a second valid source location and initialized `alternate` in the fixture. **Do not claim the correction passed CI until the exact corrected head is verified.** Parent #86 must be qualified and merged first; then retarget/reconcile #87 and rerun all four CI jobs plus full completed-batch qualification on final head.
- [PR #85](https://github.com/eristavi/eristavi-lang/pull/85): isolated Stage-0/native output-parity test baseline, normal CI [41121276888](https://github.com/eristavi/eristavi-lang/actions/runs/41121276888) passed on `820d625e9c45e053ee4718ccabaa169969a41f27`. No new UIR frontend lowering or native backend was created; update against current main and independently review before merge.

### Ordered next steps, preserving frozen language and production compiler

1. Verify corrected #87 CI. If failing, inspect actual job logs; fix only evidenced faults and rerun on new exact commit. Preserve malformed/dead-block, signed MIN/-1 **both division and remainder**, zero-divisor and precise LocId tests.
2. Reconcile #86 to now-merged main, prove its final tested tree and run full CI and completed-batch qualification before merge. Reconcile #87 afterward, run its own complete gates, and merge only then.
3. Complete outstanding U1a contracts: multi-function/recursive call execution, imported effect trust and SCC effect summaries; strict native binary64 environment; complete provenance and revision/publication capabilities.
4. Complete U1b immutable aggregates and U2 managed values, checked failures, deterministic resources/cleanup and rooted runtime contracts. Avoid expanding Eristavi source syntax or changing existing 32-byte ABI prematurely.
5. Advance U3 through tested frozen Stage-0 parity then direct AST/semantic-facts → new UIR lowering and first native target behind differential checks. Existing production frontend and native/compiler pipeline remain authoritative until explicit compatibility gates pass.
6. Keep this handover current after **qualified merges**, including head, merged tree, four-platform CI and completed-batch qualification job outcomes; never label a skipped separate 900-second owned compiler self-build as a pass.

The new typed UIR redesign is **not** the production compiler. No full redesigned-compiler self-host or native whole-program performance claim is established by these isolated U1 tests.


## 23. Verified narrow-integer qualification/merge and next handover — 2026-10-30

**This section supersedes pending statuses in sections 19–22.** GitHub main was verified after both merged compiler PRs. No production frontend/native backend or frozen-language/ABI change is implied.

### Exact release evidence

| Slice | Exact tested head | Merge on main | Normal four-platform CI | Completed-batch qualification |
| --- | --- | --- | --- | --- |
| [#86 narrow arithmetic](https://github.com/eristavi/eristavi-lang/pull/86) | `602abcea050e0d8f7c55715982bec620ec70c447` | `59b1018e78e81d897681587480b31997ab2117e3` | [41122060676](https://github.com/eristavi/eristavi-lang/actions/runs/41122060676), success | [41125916845](https://github.com/eristavi/eristavi-lang/actions/runs/41125916845), success |
| [#87 narrow div/rem](https://github.com/eristavi/eristavi-lang/pull/87) | `5ebe3213c39e875f486c98737e2a711992a96137` | `9824be1fa5103c7e7b59215b1879642c159074cc` | [41126307289](https://github.com/eristavi/eristavi-lang/actions/runs/41126307289), success | [41127592252](https://github.com/eristavi/eristavi-lang/actions/runs/41127592252), success |

- PR #86 exact qualified/merged code tree: `fa400376148e4e978b192d66797b21c373e8589d`. The merged tree was verified identical to tested head. Its post-merge main CI [41126619831](https://github.com/eristavi/eristavi-lang/actions/runs/41126619831) succeeded.
- PR #87 exact qualified/merged code tree: `566a71120f474ae47ecc7e84dc2f4c3d745bc21b`. The merged tree was verified identical to tested head. Its four CI jobs succeeded: Linux GCC and Clang, Linux ARM64 Clang, macOS Clang; CI logs report 442 discovered tests and platform-specific skips.
- For both completed-batch qualifications, all three bootstrap/offline Linux jobs and owned integration succeeded. The separate experimental owned B-to-C/C-to-D compiler self-build was **skipped**; it has no passing qualification evidence.

### PR #87 CI repair history (do not reintroduce)

1. Initial CI [41122703352](https://github.com/eristavi/eristavi-lang/actions/runs/41122703352) failed: `protocol.Harness.alternate` was referenced without declaration.
2. First fixture repair `bca23a6f09f37e44e95f0e155711c9e479a258d4` added the field/location, but CI [41124449672](https://github.com/eristavi/eristavi-lang/actions/runs/41124449672) exposed two missing constructors: the `syntheticOrigins` Harness and the dynamically appended `calls.Harness` in `tests/test_u1_calls.py`.
3. Combined constructor repair `c1201bd890812dc2ce3056752af93e5a709baa23` fixed both; CI [41125872854](https://github.com/eristavi/eristavi-lang/actions/runs/41125872854) then reported `invalid U1a source span`: the alternate span 9–17 had anchor 4, outside the required [start,end] range.
4. Final fixture-only fix `5ebe3213c39e875f486c98737e2a711992a96137` placed anchor at 9. Exact-revision CI and full qualification passed. These were test-fixture construction mistakes, not grounds to weaken the independent verifier, source-origin validation or production compiler.

The combined U1b narrow types/constants stack PR #84 was already qualified and merged at `c9750bb6f792a2432016df98ea21149fbc7ccca5`. PR #81 is marked merged through the integrated history; original stacked draft PR #82 was closed as superseded by #84, not independently remerged. U1a PRs #78 and #79 were previously integrated through qualified PR #83, which is already merged.

### Ordered implementation work remaining

1. **Finish U1a call contract in reviewed increments:** function-owned body binding, forward and mutually recursive call evaluation, zero/multiple results, conservative divergence; then callgraph/SCC effect derivation and verified versioned import trust. Add an independent multi-function interpreter/oracle, malformed dead-IR rejection, SSA differential and first observable effect/fault order. Current op34 covers declaration/call *structure*, not executable multi-function integration.
2. **Finish U1a strict execution/provenance:** enforce nearest-even strict binary64 at native/foreign boundaries, preserve subnormals/signed zero/NaN unordered behavior; complete revision-bound publication capabilities, original diagnostic anchors, digest checking and source remap. Existing isolated binary64/origin slices do not establish these native/full-publication gates.
3. **Complete U1b immutable aggregates:** canonical bounded acyclic by-value aggregate type interning, `aggregate.make/get/set`, exact structural verifier across reachable/dead blocks, immutable field-copy semantics and independent aggregate oracle. Measure real allocation/GC behavior alongside modeled budgets; do not invent public source types or implicit conversion.
4. **Implement U2:** managed Text/List/identity, checked failure continuations, exactly-once normal/checked cleanup and failure ordering, rooted GC safe points and profile-tagged runtime adapters. Preserve current 32-byte Eristavi ABI at its existing boundaries.
5. **Begin U3 shadow integration:** use the qualified, merged [PR #85](https://github.com/eristavi/eristavi-lang/pull/85) Stage-0/native parity baseline as an independent oracle. Then build direct AST + frozen semantic facts → **one** new typed UIR in shadow mode, preserving the old compiler and comparing outputs, faults, diagnostics, resources and runtime safety. Promote one native target only after complete conformance.
6. **Keep release discipline:** four-platform CI and explicit completed-batch qualification on exact final compiler PR heads; compare merged Git trees; do not auto-run the historical 900-second owned self-build. Never claim finished U1b/U2/U3 or measured whole-compiler gains from isolated scalar oracles.

The frozen source-language semantics and current production compiler remain untouched by this handover. No newly executable compiler behavior is introduced by the documentation checkpoint itself.


## 24. Verified U3 Stage-0/native parity-baseline merge — 2026-10-30

**Supersedes PR #85's historical draft status in sections 17–23.** The production Eristavi compiler and the frozen language/runtime contracts remain unchanged.

- [PR #85](https://github.com/eristavi/eristavi-lang/pull/85) **merged** on main as `f212b02de881d79d8837f2f4d859c92bf6d4f635`, on exact qualified-for-normal-CI head `3c38c2cc497a609130f3238083b4a86230d28bfd`.
- All four normal CI configurations succeeded in [run 41128847447](https://github.com/eristavi/eristavi-lang/actions/runs/41128847447): Linux x86-64 GCC/Clang, Linux ARM64 Clang and macOS Clang. This PR changes **only** `U3_STAGE0_PARITY_BASELINE.md` and `tests/test_u3_stage0_parity_baseline.py` in the net merge tree; no compiler, native runtime, ABI or code generation changed, so the compiler-change full qualification profile is not required by `CI_QUALIFICATION.md`.
- Tested PR #85 tree and merged main tree were verified identical: `f9ea8b24da4148eb8026e918dfe1c4f86e585f35`. The prior handover document blob `456d0d3186a8d443faa639f93189104d416e8ac2` was identical on the PR branch and main even though GitHub's historical PR file list included the document due to different ancestry.
- The previous [PR #89](https://github.com/eristavi/eristavi-lang/pull/89) authoritative U1b handover **merged** as `6da27730df0498811e08145d7a3074b152e633a2` after four-platform CI [41128525999](https://github.com/eristavi/eristavi-lang/actions/runs/41128525999) succeeded, with tested head `e01717b3f96e229e5d2cdbccfc1907cf78659d07` and identical tested/merged tree `274718e2c9ab48fb26fab03360f8eeebdb46dde6`.
- PR #85's test selects five accepted frozen programs and compares Stage-0 with the **existing** C-bootstrap native path, including output and exit success; two simple programs additionally exercise the **existing** direct Linux x86-64 backend. This is a **parity baseline only**; it does **not** lower AST/semantic facts to the redesigned typed UIR, implement U2 managed semantics, or qualify a new native backend.
- The post-merge main CI for PR #85 may be running when this checkpoint is authored; verify actual GitHub job results instead of inferring a pass from the PR CI. The separate 900-second owned compiler self-build remains intentionally skipped/unqualified.

### Next safe action

Follow [issue #71](https://github.com/eristavi/eristavi-lang/issues/71) first: implement defined-function body binding and independently evaluated forward/mutually recursive calls, with zero/multiple result propagation and exact first-observable-effect/fault order. Then add SCC/worklist conservative effect summaries and trusted versioned imports in separately reviewable increments. Preserve all verified U1a scalar and U1b width operations, original LocIds, transactional SSA promotion, budgets/cancellation and malformed dead-block rejection. Run four-platform CI and completed-batch qualification on the **exact final compiler-code PR head** before merging.

The other independent remaining U1a gates are native strict binary64 execution and full source-origin/publication revisions (issues #76/#77). U1b immutable structural aggregates are still pending under issue #73; U2 managed values, checked failures and deterministic cleanup under issue #74; actual U3 shadow AST+semantic-facts→new-UIR and native integration under issue #75. Never retire the old compiler or claim complete U1b/U2/U3 based on scalar tests or the PR #85 baseline.


## 25. Verified CI cost reduction and native verifier timing — 2026-10-30

**This is the current testing policy, overriding historical claims that every PR, documentation update and post-merge main push must run four-platform full tests.**

- [PR #91](https://github.com/eristavi/eristavi-lang/pull/91) merged as `674312a4f107b6e3de3b9abad39dedf2d68d92af` after exact-head [four-platform full CI 41132849760](https://github.com/eristavi/eristavi-lang/actions/runs/41132849760) succeeded, tested head `84784bf2f365e7fa9aa864891c393fc863dbc590`; tested/merged tree `70b52698b5fbd28bec6e553837863351043f08bc` matches. **No production compiler, UIR runtime code, source semantics or ABI changed.**
- Ordinary implementation PR edits now get a single Ubuntu Clang smoke suite; [initial seven-test smoke run 41132705088](https://github.com/eristavi/eristavi-lang/actions/runs/41132705088) passed in approximately 14 seconds of test execution. Markdown-only changes get changed-file classification and `git diff --check`, with **no system compiler/test matrix**.
- Complete four-platform CI runs only when explicitly requested for the final code revision: mark a draft PR Ready for review, use GitHub Actions workflow dispatch with `profile=full`, or add `qualification`/`owned-qualification` if their build audits are also needed. Completed-batch compiler-code qualification still requires the full bootstrap/offline and owned-integration jobs at that exact head. No automatic duplicate full matrix runs on main push; the latest tested/merged Git tree must be compared explicitly. After relevant commits, manually rerun full and qualification on the new exact head; previous green status is stale.
- `tools/run_ci_tests.py --profile full` still discovers and runs all existing tests; the smoke profile is deliberately small. The complete suite, native-runtime parity, malformed-IR, and 900-second separately-selected owned compiler self-build profiles were **not** deleted or silently weakened.
- `tests/u1_native_tools.py` caches C-bootstrap frontend and owned-runtime generator binaries only within the current Python test process, keyed by CC/CFLAGS; it retains the original `-O2` builds and never reuses artifacts across commits/jobs. U1 foundation, promotion and verifier tests still build, link and execute their own actual test programs against independent native-C and owned runtimes.
- The slow `test_eristavi_emitted_verifier_and_oracle_on_both_runtimes` is primarily **owned-runtime execution**, not code compilation. Measured GCC: about 88.6s total, with 32.5s executing the owned verifier protocol and 48.6s executing the owned graph oracle; assembly emission for both programs about 1.9s. Clang: about 136.5s total, with about 48.1s and 76.7s in those same owned-runtime execution phases. Native-C executions took only a few seconds each. These are variable hosted runner timings and do not alone demonstrate a universal speedup or identify a specific owned-runtime code-level hotspot.
- GCC completed the full 443-test discovery run in about 301s, versus about 517s in an earlier run; Clang took about 477s in this validation, versus about 303s previously. Performance measurements vary significantly by runner load. **Do not mistake the longer CI test line for a compiler regression.** Profile owned-runtime verifier/graph execution separately before changing runtime, allocator, IR semantics or stress coverage.
- Canonical implementation and release gates: [CI_QUALIFICATION.md](CI_QUALIFICATION.md). For next implementation, continue [issue #71](https://github.com/eristavi/eristavi-lang/issues/71) as small isolated U1a defined-function body binding/evaluator and conservative effect-contract slices, followed by independent U1b aggregates, U2 and U3 shadow integration. Preserve frozen language and the current production compiler.

The PR #91 change is a CI/test-harness optimization, **not** completion of full owned runtime performance work, new U1a executable calls, U1b aggregates, U2 managed resources or U3 native integration.


## 26. U1a issue #71 — isolated FunctionId body-binding candidate (draft; not qualified)

This section records **unmerged development**, not a new qualified production release. The last qualified main compiler-code checkpoint remains the one in section 23 and the CI policy is section 25.

- Draft [PR #92](https://github.com/eristavi/eristavi-lang/pull/92) introduces `src/compiler/u1_module.eri`, an independent and budget-charged registry associating **existing** declared `meta.FunctionId` values with a complete `build.Function` body. It never resolves functions by guessed symbol strings.
- `bind` verifies exact declaration kind (local, not imported), in-program FunctionId identity, matching canonical signature, complete cell-free function body, owner/root isolation, nonduplicate body binding, and a **fresh** run of `u1_verify.verify`. No accepted builder flag is trusted. `seal` requires one binding per local definition, rechecks revision and each body, then only marks *definition completeness*. The resolver rejects unbound imported functions and stale body revisions; the registry never grants a native-executable or trusted optimization stamp.
- The independent Eristavi test fixture builds **forward and mutually recursive call structures**, a zero-result local definition and a multi-result definition, rejects mismatched/foreign/duplicate/import body bindings, and checks missing-definition, stale-revision, malformed unreachable call, and exact cleanup. **Structural tests do not mean the mutual recursion has been executed.** The new test is included in the one-platform smoke profile.
- No source grammar, existing frontend, old/native compiler pipeline, ABI, U1a/U1b opcodes, SSA promotion or runtime library was altered. The separate owned compiler self-build stays explicitly unqualified.
- This slice is deliberately **not** the issue #71 definition of done: no interpreter or native execution of function calls/recursion; no bounded multi-function frame semantics; no SCC/worklist effect summaries or trusted import registry; no independent first-effect/fault ordering test; no executable checked-failure call edges (U2). Keep issue #71 open.

**Next implementation gate:** build a small independent U1a evaluator over **linked and freshly verified** typed bodies with deterministic entry parameter binding, forward/recursive call frames, zero/multiple result return, CFG argument transfer, bounded evaluation/cancellation, and explicit unsupported-op rejection. Follow with SCC effect propagation and selected trusted/versioned import contracts. Preserve original call/callee LocIds and test first observable traps. Finish the coherent compiler-change batch, then request four-platform full CI and separate completed-batch qualification on the **exact final head**; until then use the inexpensive targeted smoke suite. Do not merge or declare this candidate qualified based only on a smoke pass.


## 27. U1a issue #71 — recursive execution, SCC effect closure and trusted test imports (draft 2026-10-31)

**Current branch candidate:** [PR #92](https://github.com/eristavi/eristavi-lang/pull/92), `compiler/u1a-defined-body-binding`. This section supersedes the *development next steps* at section 26; the production compiler is unchanged. This section is NOT a claim of final four-platform CI, qualification or main merge.

- `src/compiler/u1_module.eri`: real local FunctionId-to-body definition binding, exact signatures including zero/multiple return shapes, fresh independent verification including malformed dead IR, missing/duplicate/untrusted-owner and stale revision rejection, budget cleanup.
- `src/compiler/u1_execute.eri`: bounded **actual evaluation** of hand-built linked U1a pred/i64 IR with private per-call frames, mutual recursion and forward calls, simultaneous block-edge argument transfer, exact result propagation, finite fuel/depth, first imported side effect before terminal trap, and original callee LocId fault attribution. Unsupported opcodes (notably strict f64/U2) return explicit kind=3; they are not silently lowered or guessed.
- `src/compiler/u1_effects.eri`: derive local fault flags and conservative potential CFG-loop divergence, mark recursive call cycles and propagate effect masks through the reverse caller worklist. Check each defined function's declared upper bound; missing effect bits fail closed. Reverify every bound body on each effect/evaluation request, including dead blocks; rejected analyses release scratch resources.
- `src/compiler/u1_imports.eri`: only **two closed, exact version-1 test adapters**, `u1.test.trace(i64)->()` with external mask 4 and `u1.test.identity(i64)->i64` with empty effect mask 0. Confirm FunctionId, symbol bytes, type signature, version and effect contract from frozen metadata; reject missing, wrong/duplicate, stale or forged import selection. This is NOT yet a general trusted native/foreign import runtime.
- `tests/fixtures/u1_execution.eri` and `tests/test_u1_execution.py` build independent direct UIR calls instead of relying on the old compiler's source lowering. Test mutually recursive even/odd, zero/multiple returns, trace before callee fault including nested calls, import version/mask/handler rejection, incomplete policy, understated effect bounds, stale bodies, bounded negative recursion, budget cleanup and explicit unsupported strict-f64 refusal. `tests/test_u1_module.py` retains independent linkage and malformed dead-call checks.
- First working execution profile [smoke CI 41137216682](https://github.com/eristavi/eristavi-lang/actions/runs/41137216682) passed 9 tests on head `b93a33284237fc35c86b4bf4530340b633a8222a`. Stronger negative-contract probes and cleanup [smoke CI 41137496221](https://github.com/eristavi/eristavi-lang/actions/runs/41137496221) passed 9 on head `2824c3508685d9ef7310da968cbbffc73421c89c`. The subsequent nested-first-fault and unsupported-f64 regression additions require a new exact-head smoke pass. Those earlier green runs do NOT qualify the newer code.
- [U1A_MULTI_FUNCTION_EXECUTION.md](U1A_MULTI_FUNCTION_EXECUTION.md) describes exact interpreter outcomes, supported opcodes, all deferred operations, effects, chosen imports and the trust boundary.
- **Release policy:** Keep the feature branch draft during changes. Once targeted tests pass, run deliberate **one-time** four-platform full CI and the required completed-batch offline/owned-integration qualification on the exact final head. Compare the merged tree to the tested tree before claiming it is merged. Do NOT automatically rerun the separate 900-second experimental owned compiler self-build.

**Remaining issue #71 work after this independent reference slice:** complete full U1a supported opcode execution/oracles (especially strict binary64 and every checked/overflow primitive), a production selected-trust imported native adapter, broader abnormal recursion and differential first-fault stress, and publication/revision handling beyond the local body revision. Therefore keep issue #71 open even if this coherent slice passes and is merged. U1b immutable aggregates (#73), U2 managed values/checked failures/cleanup (#74), and U3 shadow frontend→new typed UIR/native integration (#75) still remain separate. Preserve frozen Eristavi source grammar, current production compiler and ABI.


## 28. Verified U1a recursive execution / effect / import-contract integration — 2026-10-31

**This supersedes section 27's draft-only status.** The production frontend, frozen source grammar, current native compiler and ABI remain unchanged.

- [PR #92](https://github.com/eristavi/eristavi-lang/pull/92) **merged** as `e59ef7e6401990da5498b24f357077cc46e41e51`. The exact final tested PR head was `65b8109c9248162e63b4f1cedf91e5a25e4835df`.
- [Four-platform full CI 41138028053](https://github.com/eristavi/eristavi-lang/actions/runs/41138028053) completed **success** at that exact head: Linux x86-64 GCC, Linux x86-64 Clang, Linux ARM64 Clang, macOS Clang. Intermediate test-fixture/specialization errors were corrected on the draft branch and are not accepted as final regressions.
- [Completed-batch qualification 41138028110](https://github.com/eristavi/eristavi-lang/actions/runs/41138028110) completed **success** at the same head: three bootstrap/offline Linux configurations (x86-64 GCC, x86-64 Clang, ARM64 Clang) and owned integration. The separate experimental `owned-self-build` job was **intentionally skipped**, remains unqualified, and must not be inferred from this pass.
- **Exact Git-tree parity independently verified:** qualified PR head tree == merged main tree == `0d85a50abbf1390e741ec7ff0705254ec5fc2c1a`. GitHub main was verified at `e59ef7e6401990da5498b24f357077cc46e41e51` after the merge. No unqualified compiler code was introduced through this merge.
- Implementation: `src/compiler/u1_module.eri` binds exact local FunctionIds to canonical complete bodies with fresh verifier checks; `src/compiler/u1_execute.eri` evaluates bounded mutually recursive pred/i64 calls with zero/multiple values and exact first-fault origin; `src/compiler/u1_effects.eri` derives and propagates conservative six-bit effects through recursive graph cycles and checks declared upper bounds; `src/compiler/u1_imports.eri` admits only two exact, version-one, closed **test-only** import adapters. Wrong/missing/stale/forged import contracts and understated effects fail closed.
- Tests: the hand-built UIR acceptance fixtures under `tests/fixtures/u1_execution.eri`, `tests/test_u1_execution.py`, `tests/fixtures/u1_module.eri`, and `tests/test_u1_module.py` cover forward/mutual recursion, zero/multiple returns, parallel CFG arguments, nested effect then callee trap, conservative callgraph effects, invalid import versions/adapters/bounds, malformed unreachable call, stale revisions, bounded nontermination, strict-f64 unsupported outcome and budget cleanup.
- Canonical scope/limitations: [U1A_MULTI_FUNCTION_EXECUTION.md](U1A_MULTI_FUNCTION_EXECUTION.md). The reference evaluator intentionally rejects strict f64, non-admitted numeric opcodes and U2 managed/checked behavior rather than pretending to execute them. A trusted, production native imported-call adapter is **not** established by two fixed test adapters. This PR must **not** be described as full U1a completion.

### Next safe implementation gate

Issue [#71](https://github.com/eristavi/eristavi-lang/issues/71) remains **open** for full U1a opcode/strict-f64/native adapter execution, independently proven first-fault/effect ordering at larger scale, selected production imported-effect trust, and full revision-bound source publication; see also separate U1a issues #76/#77. U1b immutable aggregates (#73), U2 managed values, checked failures and resources (#74), and U3 AST/semantic-facts → new typed UIR/native parity integration (#75) remain independently staged. Preserve the working compiler, mandatory cell promotion and existing ABI. Follow the change-aware CI policy in section 25: fast smoke during work; one final four-platform CI and completed-batch qualification per coherent compiler-code revision; docs-only handovers use patch checks only.

## 29. Qualified and merged U1a integer execution parity — 2026-10-31

Baseline main: `007aa4ac897a4d618b00955b7808db19792b2404` (docs PR #93).
PR #92's final full CI and completed-batch qualification were independently
checked successful before extending its evaluator. No other open PR is included.

[PR #94](https://github.com/eristavi/eristavi-lang/pull/94) is **merged** as
`4b4a7f62af98bb91bc3a7c4cb218817b02298fce`, following the user's explicit merge
instruction. This supersedes this section's earlier candidate/pending status.

- Implements all six i64 signed/unsigned overflow pairs and unsigned div/rem
  in the independent Eristavi-written evaluator. Preserves exact wrapped bits,
  overflow predicates, zero-divisor and signed MIN/-1 traps, callee origins,
  first-effect order and explicit rejection of strict f64/U1b operations.
- Fixes existing wrapping-helper intermediate overflows at `MIN+MIN` and
  `MAX-MIN`, found by the new independent integer boundary grid.
- Fixes partial call-frame initialization cleanup on quota/work failure.
  Arithmetic loops are bounded and charged through existing work/cancellation
  accounting. The quota tests additionally exposed stale abandoned-slot roots
  after checked unwinding. Both native-C and owned runtime unwind paths now
  clear those exact roots before free/reuse; caller cells, normal results,
  other root classes and the ABI layout remain intact. This common runtime
  correction is included in final compiler/runtime qualification.
- `U1A_INTEGER_EXECUTION.md` gives scope and acceptance. New tests compare
  8,190 arithmetic/predicate observations against unbounded mathematical
  expectations, 600 recursive/switch/loop/promotion/fault-trace cases, and
  focused native-C/owned runtime parity. Quota/cancellation, effect bounds,
  stale accepted-report rejection and monotonic resource charges are covered.
  Direct C/owned unwind-root regressions also check the owned scratch-refusal
  fallback. Local lifetime/heap-GC tests passed with ASan/UBSan; only local
  LeakSanitizer task inspection is disabled due the container's `/proc` access.
  Hosted CI sanitizer defaults are unchanged. Initial oversized single-worker
  native parity timed out; the same cases use independent bounded workers,
  and the earlier timeout is not a completed performance measurement.
- **Final four-platform full CI passed:** [41183090972](https://github.com/eristavi/eristavi-lang/actions/runs/41183090972),
  on exact head `bb2f1ba81bfa4ae039f61ed0e812299a8ab4b872`: Linux x86-64
  GCC/Clang, Linux ARM64 Clang and macOS Clang. Each discovered 448 tests;
  existing platform skips remain visible. Both x86-64 configurations passed
  every native worker and deterministic owned unwind-root/fallback checks.
- **Completed-batch qualification passed:** [41183091353](https://github.com/eristavi/eristavi-lang/actions/runs/41183091353),
  on the same head. All three Linux bootstrap jobs report repeatable=true,
  completed C/D compilers, offline_audit_completed=true and unchanged sources.
  Owned integration reports repeatable=false, no C/D compiler self-build,
  successful offline audit and unchanged sources. The separate experimental
  `owned-self-build` job was intentionally skipped and remains unqualified.
- **Exact merge parity:** tested head tree == merged PR #94 tree ==
  `5567a40a9a710fa3d1008da121e38f5e4b10d5f4`. The merge commit is
  `4b4a7f62af98bb91bc3a7c4cb218817b02298fce`; no implementation changed
  after qualification. Because draft→ready would trigger another full matrix,
  the user-authorized merge used an ordinary two-parent merge commit and a
  non-forced, expected-head update of main. GitHub marked PR #94 merged.
  The merge itself launched **zero** workflow runs; no expensive tests repeated.
- Follow section 25 for future changes. Documentation-only checkpoint updates
  use patch checks; preserve the qualified implementation and do not relabel
  documentation commits as newly qualified compiler code.

Next after this batch: strict native binary64 (#76), selected production
native import trust and broader #71 conformance, full source/revision
publication plus bounded simplification (#77), then the independently staged
U1b/U2/U3 gates. Keep issue #71 open. Full physical heap/GC accounting, larger
matched stress and complete owned compiler self-hosting remain unqualified.

## 30. Combined native Float / import trust / publication development — historical

**Superseded by section 31. The draft/pending descriptions below are historical.**

User authorized all three next gates in one integration batch, and requested
that final CI/qualification be launched without following/polling their progress.
Check those results only when the user subsequently instructs it.

- Baseline: main `3f33daa87a2f92a57b599a8dd53125d2f1bf62bc`.
- Active branch: `compiler/u1a-native-trust-publication`. No implementation
  changes qualified or merged yet. PR #94 remains the qualified implementation.
- Batch scope: strict native binary64 (#76), closed production import trust
  and conformance (#71), source origins/revision-bound publication and bounded
  canonical simplification (#77). Read the exact exit gates and frozen contract.
- Preserve production frontend, language semantics, ABI and mandatory promotion.
- Run focused local developer checks; at the completed batch start one final
  four-platform full CI and completed-batch qualification on its exact head.
  Do not follow those runs or start the separate owned compiler self-build.
- Full acceptance and physical-resource claims require evidence, not code alone.

Implementation checkpoint (unqualified):
- Added `u1_native.eri` + private `runtime/u1_native.h`: real x86-64 SSE2 /
  AArch64 scalar binary64 instructions with explicit FP-control save/establish/
  restore, no FMA/excess intermediates, gradual underflow and canonical NaNs.
  Adapter executes verified linked scalar UIR, including bounded native call
  frames, first-fault LocIds, work/cancellation and active allocation limits.
- Closed production catalog: version-one `erist.u1.i64.identity` (mask 0) and
  `erist.u1.i64.write` (mask 20, external+terminal fault). No arbitrary callback
  or dynamic symbol/effect selection. Test adapters do not authorize this path.
- `u1_publication.eri` captures exact owned metadata/body tables and revisions,
  revalidates effects/imports/verifier before use, rejects same-revision edits.
- Additional ordered source-origin parent sets retain original anchors; new
  private diagnostic-map ingress/remapping checks source/contract revisions and
  refuses stale text excerpts. This is not a public serialized UIR format.
- `u1_simplify.eri` works on a private promoted clone: exact predicate/wrapping
  integer folds, constant branch/switch selection, edge-pool rebuild, subsequent
  dead-block/trivial-parameter cleanup and fresh verification. Calls, guards,
  div/rem and Float arithmetic are never folded speculatively.
- Focused native acceptance now covers Float/integer oracles, recursive and
  zero/multi-result calls, switches/parallel copies, hostile FP state and foreign
  boundary corruption, first write/fault, strip, source-map ingress/remap, stale
  source/import/body rejection, exact same-revision edits, malformed dead CFG,
  cancellation and partial publication-snapshot quota cleanup.
- Completed local smoke evidence and final workflow launch state are recorded
  below. No final workflow result has been inspected.

Final implementation candidate — before hosted qualification:

- Detailed scope: `U1A_NATIVE_TRUST_PUBLICATION.md`. Native execution is a private
  linked-UIR executor with real x86-64/AArch64 FP instructions, not U3 frontend
  integration, a JIT or a new production default backend. The native catalog is
  only the two explicitly implemented/versioned production functions, not general
  foreign callbacks. Old test adapters cannot authorize native execution.
- Nine new acceptance tests; local integration smoke discovers 20 tests.
  Local C/native ASan+UBSan probes passed (container-only LSan task inspection
  disabled); hosted sanitizer defaults remain unchanged.
- Matched original/simplified native evidence is in
  `docs/evidence/2026-10-31/u1-native-physical.json`: five alternating fresh-process
  pairs, identical semantics, raw time/peak-RSS and exact native frame bytes.
  RSS may include pre-exec inherited pages; do not infer an isolated allocator
  measurement, whole-compiler speedup or complete physical UIR heap/GC pass.
- Keep #71/#76/#77 open until the actual scoped exit gates and hosted results
  have been reviewed. Broader physical heap/GC/stress and production artifact
  migration remain separate; no U1b/U2/U3 completion is implied.
- The final four-platform CI and completed-batch qualification will be requested
  once, via the `qualification` label on the completed draft PR. Do not mark it
  Ready as an extra trigger. Do not poll/follow those runs; the user will request
  result inspection. Do not merge based on uninspected tests.

Local final implementation evidence: `tools/run_ci_tests.py --profile smoke`
passed all 20 tests in 30.85 seconds; report retained in
`docs/evidence/2026-10-31/u1-native-smoke.json`. `compileall` and `git diff --check`
passed. These are local development checks, not hosted qualification.

Hosted submission checkpoint:

- Draft [PR #96](https://github.com/eristavi/eristavi-lang/pull/96) is open on
  `compiler/u1a-native-trust-publication`; it is NOT qualified or merged.
- Uploaded implementation commit: `a8776075a8121cd2aa29b5b7dc15970fbf3b97c4`;
  exact implementation tree `fa7c2341b717fd220d6baa5f3c479d67092f2419` matches
  the locally checked Git tree. This final checkpoint adds only documentation.
- Four-platform full CI and full completed-batch qualification are requested
  once by applying `qualification` AFTER this checkpoint is the PR head. That
  event selects the exact final PR head for both workflows. The label is the
  launch marker; no run status/result is inspected during this session.
- Per the user's instruction, stop monitoring after requesting those runs.
  Wait for the user to ask to inspect results. No merge or issue closure is
  authorized by an uninspected run; no owned compiler self-build is selected.

## 31. Qualified PR #96 merge and timing investigation — 2026-10-31

The user explicitly authorized merging PR #96 and requested no full test rerun
while merging. The implementation has not changed since its successful final
qualification. No test, workflow or performance implementation was modified as
part of the timing investigation or merge.

- Exact qualified PR head: `eec1dfee100be8c0f9b88a71a98b4866f36fab66`.
- [Four-platform full CI 41187461690](https://github.com/eristavi/eristavi-lang/actions/runs/41187461690)
  passed Linux x86-64 GCC/Clang, Linux ARM64 Clang and macOS Clang: 457 tests
  discovered on each, with the existing platform-dependent skips retained.
- [Completed-batch qualification 41187461738](https://github.com/eristavi/eristavi-lang/actions/runs/41187461738)
  passed three Linux bootstrap self-build/offline jobs and owned integration.
  The separate owned compiler self-build job was intentionally skipped and
  remains unqualified; owned integration is not full owned self-hosting.
- [PR #96](https://github.com/eristavi/eristavi-lang/pull/96) is merged as
  `f5c3904e72009bf2c20051cb002772f75e20b98c`. The tested head tree and merged
  tree both equal `10fb3c388bea0f9f9bc6e6a5d26cc72867b475ce`.
- To honor the user's no-repeat instruction, the merge used an ordinary
  two-parent Git merge commit with the exact qualified tree and a non-forced,
  expected-head update of main. Marking the draft Ready would have triggered
  another full matrix, so that extra transition was not used. GitHub confirmed
  PR #96 merged. The merge commit triggered zero workflow runs.
- Scope and acceptance: `U1A_NATIVE_TRUST_PUBLICATION.md`. Closed production
  trust covers only version-one identity/write adapters, not arbitrary FFI.
  Native execution remains separate from the production frontend. Full physical
  heap/GC accounting, wider matched stress and production artifact migration
  retain independent gates. #71/#76/#77 remain open; U1b/U2/U3 remain staged.

Read-only CI timing findings (no tests rerun and no optimization implemented):

| Measured phase | Linux x86-64 Clang job | Linux x86-64 GCC job |
| --- | ---: | ---: |
| Full test suite | 694.58 s | 528.62 s |
| Integer parity test, total | 228.55 s | 172.06 s |
| Integer workers, owned execution | 206.67 s | 157.37 s |
| Integer workers, C-runtime execution | 17.63 s | 11.12 s |
| Verifier/oracle parity test, total | 127.37 s | 91.60 s |
| Verifier/oracle, owned execution | 116.20 s | 81.49 s |
| Verifier/oracle, C-runtime execution | 7.34 s | 5.80 s |
| Verifier/oracle assembly emission | 1.93 s | 2.93 s |

The same application assembly is linked to each runtime within a parity test.
The two slowest tests account for roughly half the full suite; owned execution,
not assembly emission, dominates them. Candidate profiling areas include runtime
allocation/GC/value operations and repeated verified fixture work, but these
logs do not identify a specific code-level hotspot or exonerate all codegen.
ARM64/macOS skip these Linux x86-64 owned tests, so their shorter totals do not
establish an OS advantage. In previous qualified CI 41183090972, GCC took
735.72 s and Clang 448.86 s, the opposite ranking on the same Ubuntu image;
host variability is a plausible factor, not a proven sole cause.

Next recommended action is focused profiling of the existing owned execution
path before proposing a performance patch. The user has authorized merging,
not speculative performance changes. Preserve the passed evidence; documentation
updates use patch checks only. Do not rerun expensive qualification for unchanged
implementation or infer complete owned compiler self-hosting from this merge.

## 32. Owned-runtime investigation completed — 2026-10-31

**The interim notes below preserve development history; the final measured
checkpoint at the end of this section supersedes their pending statuses.**

User requested a full investigation and ranked optimization options for the slow
owned-runtime tests. Active branch: `investigation/owned-runtime-profile`, based
on `0a2caea09ae9bb05a062a986a3412bc045bbf96b`. No production performance patch
is being applied. Build pinned diagnostic copies in scratch, reproduce actual
workers with exact outputs, separate CPU/syscall/allocation/GC/verification cost,
and test candidate mechanisms only in disposable diagnostic copies. Preserve
source semantics and all validation/coverage. Do not run the full CI matrix or
experimental compiler self-build just to investigate. Save measured findings
and clearly label diagnostic estimates versus qualified improvements.

Profiling baseline reproduced all eight original integer-runtime parity workers
with exact mathematical-oracle outputs. On this local host, C-runtime workers
total 17.77 s (17.58 user / 0.19 system), owned workers total 244.90 s
(230.41 user / 14.47 system). This is a pinned local reproduction, not a claim
that the CI's 206.67 s must match another host. External ptrace sampling is
blocked by this container, so disposable assembly uses a low-frequency
SIGPROF CPU sampler and separate exact event counters. No production code,
compiler semantics, test coverage or CI workflow has changed.

First diagnostic attribution: a 5 ms CPU-time sampler collected 6,659 samples
from integer worker 0 with exact outputs. About 24.1% fell in graph-owner lookup,
20.5% in the graph interval-index heapsort helper and 7.0% in index preparation.
Separate flag-preserving event counters (not timed performance samples) observed
72,284,485 allocations, 68,089,958 value-slot creations, 150,818 graph/text
collections, 118,397,346 owner lookups and 36,806 slot-index scratch reservations
in that worker. First temporary probes retained exact outputs: owner-root
filtering ~27.35 s vs baseline ~34.02 s; 4x/16x longer graph-GC scheduling
budgets ~14.24/9.27 s; combined filtering/lazy preparation + 16x budget ~8.66 s.
These are exploratory single samples, not qualified production improvements.
Five-pair confirmation, full original integer-worker coverage and independent
verifier/oracle probes are pending. No performance code is committed.

### Final measured checkpoint

- Report: `docs/performance/OWNED_RUNTIME_INVESTIGATION_2026-10-31.md`.
  Raw measurements, hashes and portable diagnostic harness documentation:
  `docs/evidence/2026-10-31/owned-runtime-profile-evidence.md`.
- Baseline code: `0a2caea09ae9bb05a062a986a3412bc045bbf96b`; all code
  files remain unchanged. Temporary probes varied only copied generated runtime
  assembly. The application assembly was identical within all runtime comparisons.
- All eight original integer workers retained every independent output, trace,
  fault, quota/cancellation and stale-verification check: C baseline 17.775 s;
  owned baseline 244.901 s; combined prototype 57.335 s. This is one complete
  local pass per runtime, not five full-suite repetitions.
- Original verifier protocol: owned 57.017 → 11.016 s; original 91-graph and
  128-block-chain oracle: 80.800 → 11.041 s. All observations matched exactly.
- Five additional fresh-process, serialized AB/BA pairs on integer worker 0:
  baseline median 37.617 s, prototype median 6.943 s (5.42x ratio of medians).
  Baseline range 35.996–39.640 s, prototype 6.550–7.841 s. Do not multiply
  ratios across unrelated workloads or promise the same hosted-CI timing.
- CPU sample attribution (6,659 samples): owner lookup 24.1%, interval-index
  heapsort 20.5%, preparation 7.0%; further time is root traversal/marking/sweep.
  Allocator free-list scan averaged 1.06 visits/allocation and was only ~1.5%
  of samples; allocator replacement is not the first recommended target.
- Separate instrumented counters on worker 0, baseline → prototype:
  graph/text collections 150,818 → 9,735; owner lookups 118,397,346 → 33,116;
  index preparations 150,818 → 7,729; OS reservations 36,827 → 65. Value-slot
  creations remain exactly 68,089,958; graph-object creations remain 1,784,454;
  slot collections remain 36,806. No workload/check was deleted.
- Independent C runtime made 55 managed-heap collections in this worker. Its
  trigger/representation differs; this is not an equal-memory-policy comparison.
- Dynamic owned reserved-mapping peak: 1,458,176 → 1,409,024 bytes in worker 0,
  plus 1 MiB static virtual BSS for the prototype exact-slot table. Mapping
  traffic fell 2,896,707,584 → 2,162,688 bytes; traffic is cumulative virtual
  reservation, not simultaneous RAM. RSS attribution was unreliable here and
  is excluded. These observations do not close full physical UIR heap/GC gates.
- Rank: (1) allocation-pressure-aware graph/text GC policy with memory limits;
  (2) exact-slot root filtering using the independent C implementation as a
  precedent; (3) bounded reusable slot-index scratch with clearing, ownership,
  failure fallback and cleanup; later review boxed-scalar/private word storage.
  The diagnostic 16x scheduling multiplier must not be blindly shipped.
- Full production acceptance still needs aggressive forced-GC/tiny-memory/OOM,
  interior/protected/colliding roots, unwinding and scratch refusal, shared value
  versus identity/Text/resource lifetime cases, physical capacity accounting,
  and the normal final four-platform/full qualification once a production patch
  exists. No performance patch, test coverage change, full CI rerun or experimental
  owned compiler self-build was performed in this investigation.

## 33. Historical U1a scoped acceptance audit — superseded by §35

**Status is audited on GitHub main `0a2caea09ae9bb05a062a986a3412bc045bbf96b`. This section supersedes historical open/pending wording for U1a issues.** It is a documentation-only acceptance record; no implementation, production frontend, native ABI, test runner, or CI policy is changed.

| Issue | Current disposition | Basis / remaining evidence |
| --- | --- | --- |
| [#71](https://github.com/eristavi/eristavi-lang/issues/71) | **CLOSED / completed** (already closed on GitHub) | Recursive FunctionId calls, zero/multiple results, SCC effect propagation, closed test and production import contracts, independent integer execution, source/fault preservation, exact-head qualified PRs #92/#94/#96. Does not authorize generic FFI or production frontend migration. |
| [#76](https://github.com/eristavi/eristavi-lang/issues/76) | **CLOSED / completed** in this audit | Native x86-64/AArch64 strict binary64 adapter; FP-control save/establish/restore and foreign boundary checks, Float rational oracle, hostile environment/non-FMA and fault origin regressions; five matched physical native resource observations; exact-head green PR #96 CI and qualification. Not full physical UIR heap/GC acceptance or a production-backend/JIT replacement. |
| [#72](https://github.com/eristavi/eristavi-lang/issues/72) | **OPEN — needs explicit final acceptance** | Sparse i64 switches implemented/merged with qualified PR #83 and covered by later PR #96. Reconcile issue's single-successor-schema requirement: verifier/promoter use `u1_successors`, evaluator/simplifier independently decode cases. Complete documented wide/dense/sparse/irreducible/cancellation/resource acceptance matrix, or formally scope intentional independent-oracle exceptions; only then close. |
| [#77](https://github.com/eristavi/eristavi-lang/issues/77) | **OPEN — broader artifact/resource gates** | Exact revisions/publications, multi-parent origins, diagnostic source map and safe transactional simplification qualified through PR #96. Actual reusable artifact/cache ingestion/manifest and physical heap/GC/large matched stress/aggregate resource accounting remain outside demonstrated acceptance. Decide which artifact requirements transfer explicitly to U3 rather than silently granting them here. |

**Evidence:** PR #83 tested/merged tree `bfda0d1278a8185b2d48a6e24114f5ed10e743fa`; [CI 41119775019](https://github.com/eristavi/eristavi-lang/actions/runs/41119775019) / [qualification 41121497695](https://github.com/eristavi/eristavi-lang/actions/runs/41121497695). PR #96 exact head `eec1dfee100be8c0f9b88a71a98b4866f36fab66`, tree `10fb3c388bea0f9f9bc6e6a5d26cc72867b475ce`; [CI 41187461690](https://github.com/eristavi/eristavi-lang/actions/runs/41187461690) / [qualification 41187461738](https://github.com/eristavi/eristavi-lang/actions/runs/41187461738). The unchanged implementation must not be requalified merely because this review updates documentation.

**Current completion claim:** U1a's major scalar, call, effect, native Float, and publication *implementation slices* are qualified and merged, but **full U1a acceptance is not complete** while #72/#77 remain open. The previous informal 11/12 progress bar is not a formal certification. The isolated UIR executor remains separate from the production frontend (U3); the experimental full owned compiler self-build remains intentionally skipped.

**Next safe development steps:** finish the #72 common-schema/independent acceptance evidence in a focused batch, then #77 publication/artifact/physical-resource exit-gate reconciliation. Close each only with a linked evidentiary report; if implementation changes, use focused smoke while editing and one final four-platform plus completed-batch qualification on the exact revised code tree. Do not repeat unchanged expensive jobs. Continue U1b immutable aggregate development independently of U2/U3 readiness.

## 34. Historical U1a switch/provenance implementation candidate — superseded by §35

**Status: implementation candidate, not yet qualified/merged.** Baseline main:
`0a2caea09ae9bb05a062a986a3412bc045bbf96b`. Active branch:
`compiler/u1a-switch-provenance-acceptance`. Preserve previous green
[PR #96](https://github.com/eristavi/eristavi-lang/pull/96) evidence.

- #71 was already closed, and #76 is closed with native Float64 evidence.
  #72 and #77 are open, with unresolved acceptance conditions.
- #72 code changes: add `caseBits/choose` to common `u1_successors`;
  route the Eristavi reference evaluator and optimizer edge selection/case
  rebuilding through it. Preserve independent *Python* switch decoding as
  a differential oracle, rather than coupling every oracle to the same helper.
- #72 tests added (not yet qualified): dense switch fixtures at 8, 32 and 128 arms, unsigned-sorted
  bit patterns spanning min/max and sparse gaps, and finite irreducible SCC
  with two independent entries. The original 52 promotion snapshot fixtures
  become 57; count/traffic/work owner gates remain unchanged.
  Five fresh-process standalone native switch observations check exact output
  and record physical process RSS separately from owned budget peak/traffic/work.
  This is not a full managed runtime GC heap attribution. Existing negative
  switch verifier, control-flow and native tests remain mandatory.
- #77 acceptance split recorded in [U1A_ACCEPTANCE_BOUNDARIES.md](U1A_ACCEPTANCE_BOUNDARIES.md):
  U1a must retain private exact publication, provenance, source-map decode,
  revision rejection and private memory/work/cancellation evidence. U3 will own
  durable compiler artifacts, cache/manifest links and actual frontend-to-UIR
  provenance/production native mapping. U2 owns managed values, GC/root behavior
  and cleanup. Full physical UIR allocation attribution, larger multi-scale
  direct-UIR stress and large owned-runtime behavior are NOT established by
  earlier modeled counters or five native execution pairs.
- Do not claim total U1a or #72/#77 completion from this candidate. Run focused
  tests during edits. A changed implementation needs exact-head four-platform
  full CI and completed-batch qualification *once* at the coherent release
  boundary. The historical owned compiler full self-build stays skipped.

Focused acceptance checkpoint:
- [smoke CI 41193213024](https://github.com/eristavi/eristavi-lang/actions/runs/41193213024)
  **passed** 21/21 tests at exact implementation head
  `33897f21b1a38d9c3b819d50acdd978b910489fe`. Test fixtures
  include dense sizes 8/32/128, wide sparse bit values and irreducible flow.
  Shared successor helper now binary-searches signed-full-width bit cases
  in canonical unsigned order without case-span allocation. Python remains
  independent and all before/after promotion outputs agree.
- Five fresh C-native process samples passed with identical output;
  raw measurements recorded in
  `docs/evidence/2026-10-31/u1-switch-acceptance.json`: 128-arm
  modeled UIR owner peak 720,704 bytes, fresh allocation traffic 1,741,536
  bytes and work 138,775 visits; actual process peak RSS was observed as
  125,048 KiB in the hosted sample, **not** attributed solely to UIR
  storage or treated as a 0.7 MiB physical heap.
- This new implementation has only focused smoke qualification so far.
  Final four-platform/full completed-batch code qualification is NOT passed
  or merged as of this update. Preserve PR #96 qualification separately.
- #72 and #77 are still open pending exact-head final qualification and
  owner-scope acceptance review. The full owned compiler self-build remains
  deliberately skipped.

Current next action: request one final exact-head four-platform CI plus
completed-batch qualification with the PR's `qualification` label.
Do not follow or rerun the expensive workflows without the user's subsequent
instruction. Keep this candidate draft and do not merge until the exact results
and tested/merged Git trees have been independently checked.

Previous plan superseded: inspect draft PR #98 focused smoke, correct any
failures without raising limits or weakening the verifier/oracle, then decide
which additional direct-UIR stress and physical-resource evidence can qualify.
Update this handover as results and issue/PR states change.

## 35. Qualified and merged U1a switch acceptance / provenance boundary — 2026-10-31

**Current authoritative checkpoint.** [PR #98](https://github.com/eristavi/eristavi-lang/pull/98)
was formally **MERGED into main**, using merge commit `b05bd1863181d2a70800586a0efa8f1469d5d8df`.
The exact qualified PR head was `6b2fadf7aca6a6249a4adbf57e38bab15cb916e0`.
Both Git commits have the identical tree `de5e72f4d03a370f53356a70497d3dd9eae1ec67`, proving
the delivered source is the source subjected to final qualification.
The existing production frontend and ABI, and the independent Python
oracle remain intact; this is not U2 managed-runtime or U3 frontend migration.

- **Full [four-platform CI 41193441427](https://github.com/eristavi/eristavi-lang/actions/runs/41193441427):
  SUCCESS**, all four configurations: Ubuntu GCC, Ubuntu Clang,
  Linux ARM64 Clang, macOS Clang.
- **[Completed-batch qualification 41193441428](https://github.com/eristavi/eristavi-lang/actions/runs/41193441428):
  SUCCESS**, including Ubuntu GCC/Clang bootstrap self-build, ARM64 Clang
  bootstrap self-build and owned integration without full owned compiler
  self-build. The separate experimental full owned compiler self-build
  was intentionally skipped and is NOT qualified.
- Prior [focused smoke 41193213024](https://github.com/eristavi/eristavi-lang/actions/runs/41193213024)
  passed 21/21 tests on the code-identical implementation slice.
  The U1a evaluator/optimizer use `u1_successors` (caseBits/choose with
  unsigned-ordered binary search), while Python independently interprets the
  switch record schema. The 8/32/128 dense switches, wide sparse signed
  extrema and two-entry irreducible CFG agree before/after SSA promotion.
- Five standalone fresh-process switch samples with identical behavior
  and unmodified UIR quota gates are retained in
  [docs/evidence/2026-10-31/u1-switch-acceptance.json](docs/evidence/2026-10-31/u1-switch-acceptance.json).
  Largest 128-case modeled UIR function owner peak: **720,704 bytes**,
  successful fresh traffic: **1,741,536 bytes**, promotion work:
  **138,775 visits**. Observed process peak RSS: **125,048 KiB** on
  the hosted Linux sample. RSS includes the runtime and is **not**
  attributable solely to UIR private storage; modeled peak is not
  physical heap/GC attribution.
- [Issue #72](https://github.com/eristavi/eristavi-lang/issues/72)
  **CLOSED/completed** after exact-head final qualification and merge.
  [Issues #71](https://github.com/eristavi/eristavi-lang/issues/71)
  and [#76](https://github.com/eristavi/eristavi-lang/issues/76)
  were already closed.
  [Issue #77](https://github.com/eristavi/eristavi-lang/issues/77)
  **OPEN**: independently attributable in-memory U1a backing/allocator/GC
  physical ownership and wider matched stress/resource admission gates
  still require evidence. Do not count #77 complete from process RSS alone.
- The agreed split in [U1A_ACCEPTANCE_BOUNDARIES.md](U1A_ACCEPTANCE_BOUNDARIES.md)
  remains binding: U1a owns private publication revisions, provenance,
  source-map ingress security, bounded simplification and its own owned-memory
  gate. U3 #75 owns durable frontend/native artifacts, cache manifests,
  real source→UIR remap and integrated physical performance. U2 #74 owns
  managed Text/List/identity/GC roots and deterministic cleanup.
- U1b immutable aggregates and remaining reference conformance in #73
  are separate future work. The owned-runtime performance observations
  from section 32 are research only; no runtime GC optimization is
  approved or merged in this PR.

**Next safe development action:** finish #77's U1a-private physical backing
accounting and matched resource/stress evidence without weakening its selected
limits; close #77 only after scoped verification. Continue U1b immutable
aggregate construction independently. No expensive CI repeat is necessary
for this docs-only handover update or the previously qualified unchanged
code. For future substantive code edits, use focused smoke and exactly
one final coherent-head full CI plus completed-batch qualification, never
the experimental owned full compiler self-build unless separately selected.

## 36. Historical optimization-first owned runtime implementation candidate — superseded by §37

**STATUS: IMPLEMENTED / FOCUSED SMOKE PASSED; NOT YET FULLY QUALIFIED OR MERGED.**
[Draft PR #99](https://github.com/eristavi/eristavi-lang/pull/99),
branch `runtime/owned-gc-pressure-roots-scratch-20261031`, forked from
main `4f876009c9786d4e47807d42fe91d922f147a2b4`.
[Production implementation/acceptance notes](docs/performance/OWNED_RUNTIME_OPTIMIZATION_IMPLEMENTATION_2026-10-31.md)
and the original
[performance investigation](docs/performance/OWNED_RUNTIME_INVESTIGATION_2026-10-31.md)
must be read together. This batch implements the three **measured and scoped**
runtime optimizations without replacing frontend, ABI or any original oracle.

1. **Allocation-pressure GC (implemented):** graph/committed Text/queued
   failure counters and byte estimates saturate safely. The retained-heap
   count budget is bounded [128,4096]; graph profile also collects at 8 MiB
   fresh allocation pressure or after 1,048,576 dirty safe points. This
   replaces excessive scalar-visit-driven collections, not their correctness
   assertions. The diagnostic **16x fixed multiplier is not shipped**.
   Text-only safe-point cadence, explicit forced GC and first-fault semantics
   stay unchanged. **8 MiB is a pressure threshold, NOT a global live-heap
   physical hard limit.**
2. **Exact slot root filter (implemented):** non-owning static 64 KiB key
   table for up to 4,096 slots; suppress redundant owner lookup for root
   entries exactly equal to already-scanned slots. Genuine interiors,
   protected values, failures, foreign words and >4,096-slot cases retain
   the conservative original owner path. No root data is dereferenced on
   untrusted input.
3. **Bounded scratch reuse (implemented):** an additional shared 64 KiB
   static cache, fully zeroed on checkout and never used by concurrent
   owners; busy/large allocation requests use original dynamic reservation
   and linear fallback if reserved memory is refused. Pruning and unwind
   release the correct owner. Combined additional **128 KiB virtual BSS**
   must be included in future physical memory reports.
4. **Focused verification (PASSED):** [CI 41195818485](https://github.com/eristavi/eristavi-lang/actions/runs/41195818485)
   passed 27/27 tests at code head `7d7719d84cb40a13d4e22692f3cc5d266f2a5138`.
   The included new tests prove 200k-graph scaling, bounded GC counts/bytes,
   exact slot vs interior root equivalence including >4,096 fallback,
   forced memory refusal, scratch zeroing/nesting and exact existing UTF-8
   root/unwind results; all original selected U1a independent oracles
   were preserved. Prior intermediate failures were corrected without
   relaxing the original mathematical/semantic assertions.
5. **Performance evidence caveat:** 5.42x worker0 and 244.9→57.3 s
   eight-worker figures belong only to *disposable diagnosis*, not
   current committed production source. No fresh matched baseline/optimized
   production runtime pairs have yet established a speedup. Measurements
   on future same-host fresh-process code should include wall+CPU,
   GC/owner/scratch counts, actual virtual BSS and attributable physical
   RSS, with unmodified bounded inputs/watchdogs.
6. **Qualification plan:** per CI_QUALIFICATION.md, this PR changes only
   **owned x86-64 runtime** and its tests/docs. One final exact-head
   **full four-platform CI + owned-integration qualification** is required;
   select `owned-qualification` label once coherent. The experimental
   owned full compiler self-build remains explicitly skipped, and the
   extra three bootstrap self-builds are not required for this scope.

**Optimization-first directive for every future Eristavi project:** the
standing policy near the start of this file is *not optional*: new compiler,
runtime, UIR or tests should be cost-budgeted and optimized by default,
but correctness, safety, precise diagnostics, explicit resource limits,
the frozen language contract and deterministic cleanup are non-negotiable.

### Final full-CI discovery and corrected fault-injection test

The first exact-head full four-platform run at
`5224cfbb464a399d0fb2c8881462d7ce2e1c6b3c`
([CI 41196060338](https://github.com/eristavi/eristavi-lang/actions/runs/41196060338))
passed macOS and Linux ARM64, but Linux Clang failed **one outdated test
assumption**: `test_u1_integer_execution.py` expected a call to
`erist_rt_reserve` inside the old unwind-index builder. This production
implementation correctly uses the bounded shared
`.Lslots_scratch_acquire` wrapper, so the fixture must inject allocation
refusal through that wrapper instead, retain the existing output/stack/slot
assertions and verify that `rax` and `rdx` are zero in the refusal
case. The fixture was repaired in commit
`c2dfdb4ea3a2f8cf9a4442af9b9cbabcb6e101ae` with **no runtime
code changes and no removal of existing correctness work**.
This failed full CI is NOT acceptance evidence for the new revision.
The previous owned-integration qualification
[41196060289](https://github.com/eristavi/eristavi-lang/actions/runs/41196060289)
passed on the earlier source and needs final-head reconciliation after
the test edit. The stale `owned-qualification` label was deliberately
removed before requesting final checks; no experimental self-build was run.

An indicative same-workload but *not same-runner-paired* Linux Clang
observation: the integer executor test elapsed 59.879 s on the first
PR #99 full run versus 257.767 s on the qualified PR #98 Clang run;
the verifier/oracle elapsed 38.588 s versus 133.107 s. Do NOT call
this a certified production speedup or a measured whole compiler
performance gain. The independently recorded original investigation's
5.42x five-pair ratio remains a disposable prototype result.

**Next action:** confirm final PR #99 exact head and successful full CI +
owned-integration; if all mandatory gates pass, compare the qualified
Git tree and merge without retesting unchanged code, then immediately
update this handover on main. If any gate fails, remain draft, fix
the smallest root cause, repeat only the required evidence on final head.
If the user pauses work, preserve this section and PR unchanged.


## 37. Qualified and merged production owned-runtime optimizations — 2026-10-31

**Current authoritative checkpoint:** [PR #99](https://github.com/eristavi/eristavi-lang/pull/99)
merged into main as commit `388bfb6da42a6c0c1de307a0aa72ea987b63bbb0`, from exact qualified head
`fd4828e63826d0fc36f827a938b437f3dd863c3c`. Both commits have identical Git tree
`aac54d7534168879e585e9c8045e1c762098dea0`. This implementation preserves the original Eristavi
frontend, frozen semantics, native C reference runtime, public 32-byte
value ABI and independent mathematical / fault-order / cancellation oracles.

**Accepted and merged mechanisms:**
- Graph-enabled GC collects by newly committed graph/Text/failure allocation
  counts and estimated bytes, with a retained-object policy threshold bounded
  128–4096 and an 8 MiB *fresh allocation pressure* trigger or bounded
  deferred dirty safe points (1,048,576). Explicit GC and Text-only collection
  semantics retained. This **does not** impose a new global hard live-heap limit
  or ship the diagnostic 16x multiplier.
- 64 KiB bounded exact slot-root lookup cache prevents duplicate owner
  searches for live slot addresses already traversed. True interior, foreign,
  protected, failure and >4096-slot cases follow the original safe paths.
- Separate 64 KiB cleared reusable slot-index scratch for scoped pruning
  and checked unwind with nested/oversized reservation fallback, allocator
  refusal and original linear no-allocation recovery.
- [Implementation and acceptance report](docs/performance/OWNED_RUNTIME_OPTIMIZATION_IMPLEMENTATION_2026-10-31.md)
  records all scopes, limits, risks and reproduction assumptions. Two extra
  64 KiB static BSS ranges must be counted in total memory accounting.

**Accepted exact-head evidence:**
- [Focused CI 41195818485](https://github.com/eristavi/eristavi-lang/actions/runs/41195818485):
  **27/27** smoke tests on runtime-code-identical implementation revision,
  including 200k graph stress, memory refusal, true/duplicate root equality,
  bounded count/bytes/polling, UTF-8 and scratch ownership/clearing.
- [Final four-platform full CI 41196975098](https://github.com/eristavi/eristavi-lang/actions/runs/41196975098):
  **SUCCESS** on Ubuntu GCC, Ubuntu Clang, Linux ARM Clang and macOS Clang;
  all discovered tests and platform-specific skips retained. Both Linux
  x86-64 test jobs discovered 460 tests and all applicable assertions passed.
- [Final owned integration qualification 41196975251](https://github.com/eristavi/eristavi-lang/actions/runs/41196975251):
  **SUCCESS** on the exact same head, no self-build. Full three-platform
  bootstrap qualification is unnecessary for x86-64 owned-runtime-only
  changes per CI_QUALIFICATION.md; experimental owned compiler full
  self-build remains **NOT QUALIFIED** and was deliberately skipped.
- A first full run on an earlier PR #99 head exposed one stale test harness
  check that assumed `call erist_rt_reserve` directly inside the unwind
  index. Updated its *fault-injection interface* to
  `.Lslots_scratch_acquire`, preserving root/unwind assertions. No runtime
  code change or test removal was made in that correction; the final
  exact-head full and owned qualification both passed.
- **Directional CI timing observations (different hosted machines, not
  paired controlled samples):** Linux Clang full 759.939 → 267.372 s,
  Linux GCC full 824.042 → 500.283 s, comparing qualified PR #98 and
  PR #99 runs. Linux Clang integer worker 257.767 → 40.839 s and
  verifier/oracle 133.107 → 26.638 s. Actual same-host paired
  production benchmarks and attributable physical managed-heap/resource
  measurements remain necessary before making a general speedup claim.
  Do not extrapolate historical diagnostic 5.42x ratio to arbitrary
  workloads, alter original watchdogs or conflate BSS, RSS and allocation
  traffic.

**Permanent next-step priorities:** (1) same-host controlled AB/BA paired
benchmark of the actual optimized owned runtime vs the exact pre-PR99
baseline with independent output parity, CPU/wall/collection/owner/OS mapping
counts and physical memory including 128 KiB BSS; (2) address any remaining
measured runtime/graph registry and compiler hot paths under original
semantics/ABI, including issue #51 as relevant; (3) independently attribute
physical owned UIR resource backing for open U1a issue #77; (4) consider
boxing/private-word-buffer optimization only with a reviewed ABI and
resource-acceptance plan. The optimization-first policy at the start of this
handover governs *all future work*. Do not run full CI for this documentation
update; use exact tested/merged tree evidence above.


## 38. Qualified production-runtime benchmark and remaining milestone program — 2026-10-31

**Current status update:** PR #100 (measurement/tooling and evidence
only) is **MERGED** at [PR #100](https://github.com/eristavi/eristavi-lang/pull/100),
merge `f5ab4ec79f54fc784382139853e9f0c041f474b9`.
Its [same-host five-pair benchmark](https://github.com/eristavi/eristavi-lang/actions/runs/41198570405)
**SUCCEEDED**, exact median worker0 baseline 21.869176 s and optimized
4.019040 s (**5.4414×** on this one actual production-runtime worker).
Raw [artifact #13040469945](https://github.com/eristavi/eristavi-lang/actions/runs/41198570405/artifacts/13040469945)
and [evidence summary](docs/evidence/2026-10-31/owned-runtime-production-paired.md)
are saved. The updated PR head `1be4cd36578591e27e179939d699c9e11eea162e`
passed [focused CI 41198974402](https://github.com/eristavi/eristavi-lang/actions/runs/41198974402)
with no runtime/compiler code changes. Physical full-process RSS is *not*
physical UIR buffer attribution. Do not claim all-language, whole-compiler
or managed-GC performance from this fixed workload; U1a #77 still OPEN.

**Historical candidate state (superseded by this completion note):** implementation was in progress; do not merge or
close milestone issues solely from draft source.** Branch
`milestone/paired-runtime-u1-acceptance-20261031` begins at main `30b9d3f11238d0164f3603cd8a06f1f2e83b6586`.
PR #99 and full owned-runtime optimization CI remain the last qualified
production code. All future design prioritizes measured execution speed,
compile time, bounded memory/GC work, and predictable CI costs while
preserving correctness, safety, ABI and frozen language semantics.

**Authorized user goals (strict dependency order):**
1. Paired baseline-vs-optimized *actual production* owned-runtime AB/BA,
   independent output oracle and physical RSS/CPU measurements on the same
   host. Do NOT claim the prior disposable-prototype gains are production.
2. Investigate exact graph-registry growth and compiler/owned bottlenecks
   with controlled evidence. #51 remains open without a verified change.
3. Complete U1a #77 in-memory IR physical backing, retained owners,
   allocation traffic, stress and cleanup attribution. A process RSS peak
   or modeled charge alone is not sufficient; don't silently waive a gate.
4. U1b #73: full i8/i16/i32 independent reference execution and immutable
   aggregate metadata/build/get/set, by-value cycle rejection and faults.
5. U2 #74: typed managed Text/List/identity, checked-failure continuations,
   scoped exactly-once deterministic resources, root maps and deep conformance.
6. U3 #75: frozen frontend→new UIR adapters, one end-to-end native target,
   source/contract-linked artifacts, independent Stage-0 parity and rollback.
7. U4: measured target legalization and machine lowering, additional targets,
   artifact migration and all relevant contracts, independent qualification.

**Controlled performance benchmark SUCCESS**: the opt-in
[run 41198570405](https://github.com/eristavi/eristavi-lang/actions/runs/41198570405)
produced five AB/BA *same-host paired* measurements at exact harness head
`e846f06d12fcb5d802ce9b34804d1bf7d1906366`. Median actual pre-PR99
owned runtime worker0 = **21.869176 s**; qualified post-PR99 =
**4.019040 s**, a measured **5.4414x** speedup on that workload only.
All 10 worker outputs matched the independent unbounded-integer oracle and
each other's digest. Five pairs and child CPU/RSS samples, pinned toolchain
and exact hashes are preserved in the raw
[artifact 13040469945](https://github.com/eristavi/eristavi-lang/actions/runs/41198570405/artifacts/13040469945).
Per-process peak RSS was **127628 KiB** in both variants, not a
UIR-owned physical-memory attribution. Interpretation and raw
per-pair wall/user CPU values are also checked in at
`docs/evidence/2026-10-31/owned-runtime-production-paired.md`.
The CI-runner result must not be extrapolated to whole compiler,
all U1a/U1b programs or GC/allocator size. The exact U1a resource gate
issue #77 remains open.

**Completed within active candidate so far:** adds opt-in tooling at
`tools/bench_owned_runtime_pairs.py` plus a dedicated PR-label workflow.
It pins exact qualified pre-PR99 and post-PR99 runtime revisions; verifies the
compiled source/fixture/frontend parity and unchanged native app assembly,
then compares five serialized alternating AB/BA worker0 pairs using the
original independent unbounded-integer result/fault oracle with 120-second
watchdogs. Records wall/user/system CPU, per-child peak RSS, output and binary
hashes, host/compiler identity and raw samples. It did not invoke full CI or experimental compiler self-build.
The AB/BA run passed and its exact raw results were independently inspected.

**Next:** U1a #77 physical UIR private backing attribution and larger matched stress; advance independent U1b narrow reference executor in [PR #101](https://github.com/eristavi/eristavi-lang/pull/101) after exact-head full qualification, then immutable aggregates. U2, U3 and U4 require their own accepted functional code and remain **NOT COMPLETE**. Never rerun the already-verified paired benchmark or experimental full owned compiler self-build without a changed acceptance need. U2/U3/U4 must NOT be described as complete until
their actual source integration, independent reference tests and exact-head
qualification pass. Keep these old and new milestones transparent in status
and do not publish broad "all done" claims.

## 39. Active U1b narrow independent execution — 2026-10-31

**STATUS: QUALIFIED AND MERGED PR #101 (narrow execution slice only).** Historical working branch
`milestone/u1b-independent-narrow-execution-20261031` forked from the qualified PR #99 docs-only main checkpoint
`30b9d3f11238d0164f3603cd8a06f1f2e83b6586`. It is independent
of the paired runtime benchmark branch and its acceptance evidence.

- Extend private `u1_execute` (not the production frontend/native ABI) to
  interpret already-verified U1b i8/i16/i32 raw bit-pattern operations:
  constant, modular add/sub/mul, signed/unsigned overflow, all ten compare
  relations, signed/unsigned division and remainder. Signed MIN/-1 must
  produce *original-location* terminal overflow on **both** div/rem; zero
  divisor remains a distinct fault. For i32 unsigned multiplication, avoid
  overflowing host signed Int64; normalizing two's-complement bit arithmetic
  must be mathematical, not compiler UB.
- Validate all U1b entry raw input bits to exact declared width and reject
  f64/unsupported U2/U3 operations. Keep the frozen Eristavi source type
  system and strict 32-byte public ABI unchanged.
- New `tests/test_u1_narrow_execution.py` generates 30 hand-built linked
  functions (three widths x 10 operations) and 210 separately expected
  outcomes using Python unbounded integer arithmetic. It exercises exact
  returned value bits, signed/unsigned comparison, overflow flags and
  terminal source-located faults. All original U1a tests remain enabled.
- Added this reference test to focused CI. [Smoke 41199024937](https://github.com/eristavi/eristavi-lang/actions/runs/41199024937) **PASSED 28/28** at exact code head `f4fc991d35704cb9d536b6a2629d0d359bddad79`. The 210 independent mathematical outputs and faults are evaluated in three separately scoped 70-case linked UIR requests (no budget increased). Before calling the slice complete,
  inspect the actual run, fix any implementation/test issue, preserve
  malformed-IR/revision/budget checks and then qualify at the selected
  final code revision. Do not run the experimental owned self-build.
- This slice **does NOT** implement immutable aggregates or satisfy full U1b
  issue #73. Aggregate field make/get/set, recursive by-value type-cycle
  rejection, typed aggregate verifier and physical memory evidence still
  remain. U2 managed semantics, U3 source/frontend integration and U4 machine
  lowering remain later acceptance milestones.

**Final merged acceptance:** [PR #101](https://github.com/eristavi/eristavi-lang/pull/101) merged as `ce4f7a7c6897fbba0cee85a05bb3569312e7ec50`, exact qualified head `eb0aa86b382e77a5131793670c8dab2fbf774dc1` and tested/merged Git tree `36eaca25b706e4ed5d1da1ef69ed3e17c9d3e1f6` match. [Four-platform CI 41199325649](https://github.com/eristavi/eristavi-lang/actions/runs/41199325649) and [full qualification 41199325706](https://github.com/eristavi/eristavi-lang/actions/runs/41199325706) PASSED, experimental owned compiler self-build skipped. Original 210 Python big-int oracle cases are independently verified across 3 separately budgeted UIR requests; not the complete U1b #73 milestone.

**Next:** implement budgeted, owner-scoped immutable aggregate type graph with by-value acyclicity and make/get/set, exact field type/arity, independent aggregate oracle, malformed dead CFG and strict physical resource boundaries. Do not silently change public TypeId/ABI or import U2 identity semantics.

## 40. Qualified U1a C-managed heap diagnostic (not per-owner acceptance) — 2026-10-31

**MERGED PR #103, physical C-managed heap study VERIFIED (20/20 raw samples + opt-in workflow). Issue #77 remains OPEN for exact per-UIR owner backing attribution.** Branch
`milestone/u1a-physical-heap-evidence-20261031` from last successful handover main `1784f846ef2c54c6e1c7b79db73e63c14a0c1176`.
It records the requested *next slice* of U1a #77 real physical
measurements, not a conclusion that the U1a UIR-owned attribution gate
has been met. The independent U1b narrow interpreter is progressing on
a different PR. Do not merge/rewrite source compiler/runtime code here.

- New explicit opt-in `tools/probes/u1_c_heap_physical.py` emits four frozen hand-built UIR
  fixtures: empty control and dense 8/32/128-case switch/SSA promotion
  variants; compiles identical C-native runtime source with a **private
  diagnostic exit observer** reporting native managed heap bytes, peak
  bytes, live blocks, GC collections and reclaimed blocks/bytes.
- Five fresh process samples per fixture collect full process peak RSS
  via `wait4()`, physical C-native managed heap statistics, exact output
  digest and original bounded modeled function owner peak/traffic/work.
  The independent Python `evaluate()` checks original/promoted SSA
  traces and arithmetic/control-flow oracle for each switch.
- **Attribution rule:** this C collector metric includes every managed
  allocation in the process and is NOT directly attributable to only the
  UIR owner; control-versus-workload differences are only comparative and
  do not establish physical object ownership. Never close #77 or conflate
  modeled `budget.Owner` charges with physical heap bytes. The eventual
  #77 exit still needs exact per-owner backing/allocator/GC charge
  correlation and wider mixed-graph/cleanup stress.
- This is test-only private instrumentation (no persistent public API or
  artifact). It retains the original 8 MiB/64 MiB/33,554,432 work gates;
  no new global memory cap, no ABI/frontend/default backend change, and
  no experimental full owned compiler self-build.
- **Measured [CI #41199687957](https://github.com/eristavi/eristavi-lang/actions/runs/41199687957) PASSED 28/28**, including this private test at exact code head
  `38c5ffe4737ed0dadee52a9262f9f5ed99d3d11f`.
  Twenty samples (5 each control/dense8/dense32/dense128), unmodified
  independent switch result/trace tests and fixed model charge gates passed.
  [Raw machine-readable samples](docs/evidence/2026-10-31/u1a-c-physical-heap-samples.json)
  are checked in: C-managed peak bytes 0/control, **8,423,198**
  (dense8), **8,476,364** (dense32), **9,172,962** (dense128);
  C-managed live bytes **2,571,379 / 3,355,569 / 5,793,989**;
  collections **22/59/207**. Whole-process RSS was **125,032 KiB**
  throughout (not attributable). Original UIR modeled function owner
  peaks **162,368 / 274,528 / 720,704 bytes** are separate.
- **CI-performance fix:** the original 20-sample physical test took
  **105.081 seconds** in targeted CI, unacceptable as a routine smoke/
  full-suite additive cost. The identical measurement logic moved to
  `tools/probes/u1_c_heap_physical.py`, outside automatic
  `test_*.py` discovery; explicit opt-in
  `.github/workflows/u1a-physical-heap.yml` uses the
  `uir-physical-evidence` label. The original smoke list was restored.
  No private physical study is silently run on every normal PR.
- **Do not close issue #77:** the C-managed heap includes bootstrap/runtime
  allocations as well as UIR storage, and is not allocation-site tagged
  to UIR owner identities. The exact per-owner physical backing/collector
  attribution and larger mixed-stress remain mandatory. No source compiler
  or runtime implementation was changed by the diagnostic.

**Opt-in path verified:** [physical study workflow 41200109602](https://github.com/eristavi/eristavi-lang/actions/runs/41200109602) **PASSED** on the revised `tools/probes` entrypoint. Routine [CI 41200109570](https://github.com/eristavi/eristavi-lang/actions/runs/41200109570) **PASSED** by correctly skipping the expensive probe; it is no longer discovered in normal smoke/full suites. No tests deleted, only moved to explicit test-only workflow. Preserve raw results and do not rerun merely because the handover changed.

**Next:** Because owner attribution remains mixed,
design a separately reviewed tagged-owner allocation accounting adapter
rather than adjusting resource-policy thresholds or guessing heap sizes.


### Final PR #103 merge checkpoint (section 40 addendum)

PR [#103](https://github.com/eristavi/eristavi-lang/pull/103) merged at `6422feab353886d957f49fa8ee332b905ef58c40`, preserving the exact opt-in diagnostic script bytes and all 20 independently verified C-managed heap measurements. Existing main PR #101 narrow execution qualification is unchanged; `tools/probes/u1_c_heap_physical.py` is **not** automatically discovered by routine CI, avoiding its observed 105.081-second cost. [Raw evidence](docs/evidence/2026-10-31/u1a-c-physical-heap-samples.json) remains on main. GitHub [issue #77](https://github.com/eristavi/eristavi-lang/issues/77) stays **OPEN**: C-runtime collector counters and process RSS cannot independently attribute allocations to each UIR owner. Future measurement requires tagged managed allocation/backing correlation and mixed-stress validation; no general GC/ABI redesign authorized by this study.

## 41. Qualified independent U2/U3 Stage-0 native behavior baseline — 2026-10-31

**STATUS: PR #104 MERGED; focused CI PASSED; not a new U2/U3 UIR implementation.** Historical working branch
`milestone/u2-u3-parity-baseline-20261031`, forked from last documentation main
`1784f846ef2c54c6e1c7b79db73e63c14a0c1176`.
This is a **real executable reference baseline** needed by U2/U3 migration,
but no redesigned UIR Text/List/identity/checked/resource operations or
frontend→new-UIR lowering are implemented by these tests.

- Extend existing `tests/test_u3_stage0_parity_baseline.py` with ten
  frozen successful source programs from the project's authoritative
  175-case semantic corpus. The added cases cover List structural equality
  and value parameters, alias vs distinct identity, maybe-identity,
  checked try propagation, Unicode Text views, imported checked failures,
  nested inferred generic lists and generic replacement.
- For each case execute **independently** through Stage-0 reference source
  runner and existing C-native compiler, checking exact output/stderr
  parity, success, and original unchanged source files. The existing direct
  native targets are only asserted where previously qualified; do not
  silently route the redesigned UIR through the old path and call it U3.
- [Focused CI #41199824619](https://github.com/eristavi/eristavi-lang/actions/runs/41199824619) **PASSED**, including the expanded Stage-0/native parity cases and all original selected resource/semantic tests. Run any future substantive compiler changes through the prescribed exact-head full qualification; this test-only parity extension does not require those expensive jobs. Preserve
  if mismatches occur, investigate as real compatibility gaps rather than
  removing test vectors. No public ABI, Unicode17, language grammar,
  source semantics or default backend modifications.
- U2 #74 still requires explicit new UIR-managed value/copy/identity ops,
  checked continuations, exact cleanup and GC root maps. U3 #75 still
  requires construction from frozen AST+semantic facts, actual native output,
  origin-preserving artifacts/cache ingress and old/new differential
  acceptance. U4 issue #102 holds later machine lowering.
- U1a physical #77 and U1b aggregate #73 remain independent gating
  milestones. **Do not mark U2/U3/U4 completed from baseline parity.**

**Next:** keep the added Stage-0/native outputs as the independent migration baseline and proceed with *real new UIR* U2 managed/checked/resource semantics before promoting U3. This test-only result must not be presented as full U2/U3 completion. For
implementation, begin U2 with a reviewed versioned managed/checked/resource
extension profile and a separate function-level owned reference adapter;
only then attempt U3 source bridge or U4 machine legalization.

## 42. Final checkpoint for requested all-milestone execution — 2026-10-31

**Verified on main after PRs #100/#101/#103/#104.** The existing working
compiler and its frozen public ABI remain intact. Optimized runtime PR #99
and redesigned scalar UIR PR #98 remain prior qualified baselines. The
[remaining milestone execution and acceptance plan](docs/architecture/REMAINING_UIR_ACCEPTANCE_PLAN_2026-10-31.md)
is the authoritative dependency and verification boundary for the unfinished
redesigned UIR, not a declaration that all requested stages completed.

| Requested work | Verified result | Completion claim |
| --- | --- | --- |
| Paired actual production runtime benchmark | [PR #100](https://github.com/eristavi/eristavi-lang/pull/100) MERGED; [five same-host AB/BA pairs](https://github.com/eristavi/eristavi-lang/actions/runs/41198570405), exact median 21.869176→4.019040 sec **5.4414x** on worker0 | ✅ Scoped worker0 speedup measured, NOT general compiler speed |
| Compiler bottleneck investigation | [#51](https://github.com/eristavi/eristavi-lang/issues/51) updated: old 65536 initial growth bound is stale; current runtime grows above 16384 objects | 🟡 Re-profile complete source compilation/registry/index sorting with owned runtime; not done |
| U1a physical #77 | [PR #103](https://github.com/eristavi/eristavi-lang/pull/103) MERGED; [20 raw C heap physical samples](docs/evidence/2026-10-31/u1a-c-physical-heap-samples.json), [opt-in study](https://github.com/eristavi/eristavi-lang/actions/runs/41200109602) PASSED | 🟡 **Still OPEN**: C collector heap/whole RSS not exactly tagged per private UIR owner; mixed-stress/GC attribution pending |
| U1b #73 narrow reference | [PR #101](https://github.com/eristavi/eristavi-lang/pull/101) MERGED, exact tested/merged Git tree, [four-platform CI](https://github.com/eristavi/eristavi-lang/actions/runs/41199325649) and [full qualification](https://github.com/eristavi/eristavi-lang/actions/runs/41199325706) PASSED; 210 independent narrow results | ✅ i8/i16/i32 private reference execution only. **U1b aggregate graph + make/get/set still NOT implemented**; #73 remains OPEN |
| U2/U3 frozen behavior baseline | [PR #104](https://github.com/eristavi/eristavi-lang/pull/104) MERGED, [focused CI](https://github.com/eristavi/eristavi-lang/actions/runs/41199824619) PASSED, 15 Stage-0 vs old C-native successful programs | ✅ Independent reference baseline, NOT the new UIR implementations |
| U2 #74 new managed UIR | No new Text/List/identity/checked-failure/resource ops integrated into redesigned UIR | ⬜ NOT COMPLETE |
| U3 #75 frontend/new UIR/native integration | Real source still compiles through the existing working compiler; no new direct AST+facts→new UIR production shadow/native parity path | ⬜ NOT COMPLETE |
| U4 #102 target legalization/artifacts | [Issue #102](https://github.com/eristavi/eristavi-lang/issues/102) opened with reviewed target/machine/cache/artifact acceptance gates | ⬜ NOT IMPLEMENTED / NOT QUALIFIED |

**Optimization/CI rule:** PR #103's C physical diagnostic took 105.081
seconds, so it was intentionally moved out of default `test_*.py`
discovery to an opt-in `uir-physical-evidence` workflow and retains all
20 raw samples; do not regress routine CI with repeated physical profiling.
The previously proven 5.4414x result is a real, controlled *single
workload* speedup, not a whole-compiler measurement. New compiler/runtime
implementation needs focused independent oracles and **one** exact-head
final four-platform CI + required qualification; docs/test-only updates
should not rerun the expensive full matrix unless a scoped gate demands it.
The experimental full owned compiler self-build remains intentionally
skipped and **not certified**.

**Next non-negotiable implementation gates (uncompleted):**
1. #77: real tagged per-UIR-owner backing/allocator/GC attribution and
   mixed-stress limits; do not close on current C-managed stats.
2. #73: owner-scoped immutable aggregate type graph, make/get/set and
   independent type/dead CFG/memory oracle. Then full U1b qualification.
3. #74: owned U2 Text/List/identity, checked-failure continuations, root
   maps and deterministic exactly-once resource cleanup; independent
   U2-versus-existing-language parity, then qualification.
4. #75: source AST/facts directly construct the new typed UIR, one
   complete x86 native target, original LocId/provenance, durable
   artifact/cache contracts and Stage-0/new-UIR A/B; retain old backend
   for rollback and only switch after proved conformance.
5. #102: target-legal machine IR/registry, root-safe lowering/register
   allocation, cross-target parity, artifacts/packaging and full
   release qualification. RevaSM remains a peer target, not a
   compulsory intermediary.
6. #51: controlled source-compiler phase profiling under current runtime
   (do not reimplement the already-existing initial registry 2/bucket
   threshold). Preserve original watchdogs/resource ceilings.

**Accuracy requirement:** This user asked to finish all stages immediately.
The session delivered four substantive, independently validated and merged
slices plus a tracked U4 issue and a detailed accepted implementation plan.
It did **not** implement the entire remaining U1b/U2/U3/U4 compiler rewrite
or complete #77's per-owner physical accounting. Never mark those milestones
green until their actual source, independent oracles and qualification
prove it. Handover recovery MUST remain explicit about these gaps.

## 43. Active PR #105 memory investigation — 2026-10-31

**IN PROGRESS / NOT QUALIFIED / NOT MERGED.** User authorized investigation,
correction, documentation reconciliation and exact-head qualification before
merging #105 or closing #77, followed by U1b aggregates → U2 → U3 → U4 with
performance work throughout. Local branch `codex/u1a-105-investigation` starts
from PR head `a6472b11c407c7766cee47a894f623ff8254ff39`; remote PR branch is
`milestone/u1a-owner-physical-attribution-20261031`. Main remains
`79a9a0fcaedd638c5bc81a5b599e7cb9e23aa0b0`.

Latest hosted smoke [41216287986](https://github.com/eristavi/eristavi-lang/actions/runs/41216287986)
passed 30/31 tests. Owner physical diagnostic failed at actual stress-phase
peak **24,400,832 bytes**, above unchanged **8,388,608 bytes**. The structural
radix oracle and retained C-heap evidence checks passed. The new probe tags
allocations by active construction phase, including temporary and bookkeeping
objects; exact semantic ownership must not be assumed from those tags alone.
The older PR body describes superseded no-oversized-reuse instrumentation.
Current diagnostic measures actual block capacity, cumulative allocation
traffic and collection, including oversized free-list reuse.

Pending: reproduce with raw diagnostics, identify retained/backing/temporary
and allocator-reuse costs, fix the demonstrated cause without raising budgets
or weakening assertions, reconcile PR/body/evidence, then focused checks and
one final exact-head four-platform CI plus completed-batch qualification.
Do not run experimental owned compiler full self-build. Do not close #77 or
mark U1a accepted until all scoped physical/resource gates are evidenced.

### Section 43 investigation update — local candidate, NOT yet hosted-qualified

Original stress allocations: 3,215,578 graph allocations, 1,533,455,872 bytes
cumulative actual block traffic, 24,400,832-byte phase peak. The fixture
remains 65,536 words / 4,096 pages; original 8 MiB / 64 MiB gates stay unchanged.

Implemented locally:
- One `Words.control` lease aggregates successful page/node reservations through
  checked `budget.commitInto`; unchanged capacity/traffic/work admission, foreign/
  repeated/released-lease rejection and aggregate release. No per-page Allocation
  identity; `Words.close` revokes access and releases the one lease.
- Read a narrowed optional identity handle when lowering a member write; do not
  detach its ordinary optional wrapper unless replacing that payload.
- Bounded 256-entry nonowning x86 identity backing cache (4,104 B static). A first
  write detaches, value snapshot reads invalidate, graph mark/sweep clears keys,
  collisions re-clone. Escaping mutable identity-payload references permanently
  select the original safe detach path for that runtime lifetime.
- Allocator splits reusable oversized blocks; 64 exact small size classes through
  1,024 B with a bitmap avoid linear scans through unrelated small free blocks.
  Region-aware links, checked metadata, no-allocation operation, alignment,
  free validation and release-all reset remain. Added static allocator state: 1,544 B.
- Diagnostic distinguishes construction-phase history (including temporary and
  bookkeeping allocations) from exact retained semantic-owner wrapper/body
  observations. It records real allocator capacities and independently checks
  structural/radix layout, all observed-object GC reclamation, and exact publication
  function ownership even when publication was built in the metadata phase.

Latest local six-test ownership/allocator gate passed. Stress phase peak
7,833,216 B, traffic 19,711,040 B, 66,737 graph allocations. Exact retained stress
backing: 16,938 wrapper/body objects, 6,647,888 B, all reclaimed. Source schema
pins ensure changing an owning record layout requires observer reconciliation.
A real selected production identity import now exercises registry/publication
ownership. New focused tests cover value snapshots, aliases, mutable-payload
escape fallback, nested ordinary values, optional rebinding, allocator splitting,
high bitmap bit, multiple same-class heads, release reset and lease atomicity.

Earlier broader local smoke: 31/31 passed; new focused classes separately passed.
A refreshed opt-in current-code C-managed study also passed 20/20 samples; it
remains whole C-process heap evidence, separate from owned per-buffer attribution.
Full hosted four-platform CI and completed-batch qualification are NOT yet run.
Paired runtime-only worker0 measurements are in progress; do not infer any
whole-compiler speedup. No merge or #77 closure has occurred. Next reconcile final
raw evidence/PR description, qualify one coherent final head, inspect exact results
and tree equivalence, then proceed to U1b aggregates → U2 → U3 → U4.

### Final local submission evidence for #105

Implementation checkpoint `85ab8cf` passed the six-test ownership/allocator gate
with real selected import and complete observed backing reclamation. Final source
schema pins exclude comments before counting fields. Raw current source-hashed
evidence and the refreshed 20-sample C study are checked into `docs/evidence/
2026-10-31/`; see `docs/performance/U1A_OWNER_MEMORY_INVESTIGATION_2026-10-31.md`.
Five AB/BA whole-candidate worker0 pairs passed the independent oracle: medians
8.857851 → 7.855453 s (**1.1276× for that workload only**). Runtime-only same-assembly
control is near-flat (~1.05×) amid host variance. Neither proves whole-compiler
throughput; do not multiply these by PR #100's earlier 5.4414× number.

Local broader smoke passed 31/31 before later targeted allocator/observer additions;
those additions passed focused native tests. Final hosted smoke plus four-platform
full CI and completed-batch qualification remain required on the submitted head.
The full owned compiler self-build is deliberately unselected. Until those gates
are inspected and merge-tree equality is proved, #105 stays unqualified and #77 OPEN.

### Hosted smoke found address-sensitive cache collisions — NOT QUALIFIED

Submitted `c453e9db151bff9504422f05c25cf2badbf1c83e` preserved the checked tree
`72b068e9bfd22fd8328d91bf9a9ddef5a52e417b`, but hosted smoke
[41220371417](https://github.com/eristavi/eristavi-lang/actions/runs/41220371417)
passed 34/35 and FAILED the physical peak gate: stress phase 9,725,616 B,
515,478,752 B traffic and 1,035,287 allocations. Exact observed backing still
matched and fully reclaimed; semantic/alias/allocator tests passed. Local passing
addresses did not prove collision stability. No final full CI/qualification was
started, no merge and no #77 closure.

Active fix: retain the same 256-entry/4,104 B cache but use an eight-slot bounded
probe window and search through deletion holes on lookup/invalidation. Full-window
eviction remains conservative; no unbounded search or new cache allocation. Add
a forced-initial-hash collision/invalidation-hole native regression. Refresh
raw memory/performance evidence after focused and hosted smoke prove the fix;
the earlier local report is development evidence, not current qualification.

### Collision correction now passes adversarial full stress locally

The probe now forces EVERY identity's initial cache hash to one bucket while
leaving production probing/invalidation/eviction bounds intact. Eight and then
sixteen probes alone exposed full-window victim thrash (75–77 MB traffic):
always evicting the initial slot made hot records displace each other after
cold entries filled the window. Final candidate uses sixteen bounded probes
plus rotating full-window victims, still 256 entries; the one eight-byte victim
cursor makes shared cache static state **4,112 B**, not the earlier 4,104 B.

Seven focused ownership/allocator regressions now PASSED, including deliberate
initial-hash collisions, deletion holes, full-window fallback, stale-body guard,
snapshot reads/escaped references, bitmap bit 63/reset, and the entire 65,536-word
all-colliding physical fixture. That adversarial run: 7,853,712 B phase peak,
21,957,296 B phase traffic, 72,682 graph allocations; exact retained backing
6,653,840 B / 16,938 objects, all reclaimed. Original 8 MiB / 64 MiB gates
remain unchanged. Source schema pins and original C/owned output oracle pass.

Refresh the submitted diagnostic source hashes/raw evidence, then inspect new
hosted smoke before selecting the one final full CI + qualification gate. Old
benchmark JSONs describe the pre-collision correction candidate; they are NOT
performance qualification of the final runtime. No merge or #77 closure yet.

### Final collision-stable submission preparation

Local implementation checkpoint `9cf5b30` passes seven focused tests including
the entire physical fixture with ALL initial identity hashes forced to one
bucket. New per-owner raw data and the retained hosted failure are in
`u1a-owner-physical-105.json` and `u1a-owner-105-hosted-collision.json`.
Shared cache state is 4,112 B (256 entries, sixteen probes, rotating victim cursor).
No qualification of the rejected direct-map candidate is being reused.

Five refreshed final-code AB/BA worker0 pairs passed exact independent output/trace
parity: median 8.135968 → 8.254257 s (0.9857×), roughly flat amid host variance
(~1.5% higher wall time). **No final-code speedup or whole-compiler throughput
claim.** Earlier 1.1276× and runtime-only control files are marked historical
development evidence. The material result is bounded physical allocation and
collision robustness; full compiler bottleneck profiling #51 remains unfinished.
C-path 20/20 study remains independent and its C-relevant inputs are unchanged.

Next submit this coherent revision, inspect hosted smoke, then request one final
full four-platform CI plus completed-batch qualification. No full owned compiler
self-build. Merge and #77 closure only after exact-head results/tree parity.

## 44. Qualified merged #105: scoped U1a physical acceptance — 2026-10-31

**QUALIFIED AND MERGED.** Merge `8c625b1ece6a229844def93e2bf9563c14e9e273` has the exact tree
`0d8bf1f4a58f66a15bb9a89bd42f596091ed9c36` tested at head `f1fba11ff5e11791ad8c5d635fbf90873c686fa9`.
Base main stayed `79a9a0fcaedd638c5bc81a5b599e7cb9e23aa0b0`; both parents are retained.
GitHub reports #105 merged. No implementation changed after the final gates.
Issue #77's scoped acceptance is evidenced; issue #77 is CLOSED/completed.

### Evidence and rejected alternatives

- [Focused smoke 41222208171](https://github.com/eristavi/eristavi-lang/actions/runs/41222208171): 36/36 passed.
- [Full CI 41222506854](https://github.com/eristavi/eristavi-lang/actions/runs/41222506854): all four platforms passed, 469 discovered each, existing platform skips retained.
- [Completed-batch qualification 41222506873](https://github.com/eristavi/eristavi-lang/actions/runs/41222506873): GCC/Clang x86-64 and Clang ARM64 bootstrap C/D, repeatability, offline audit and unchanged sources passed; owned integration offline audit passed with repeatable=false. Experimental owned compiler full self-build skipped.
- Independent C-managed heap study: 20/20 current-C samples, separate whole-process collector scope, not a guessed owner multiplier.
- Adversarial physical case forces EVERY initial identity hash to one bucket.
  Actual stress phase peak 7,853,712 B and traffic 21,957,296 B stay under original
  8,388,608 / 67,108,864 B limits. All 16,938 observed stress wrapper/body objects
  (6,653,840 B) and every other observed owner partition are reclaimed.
- Earlier hosted direct-map candidate failed 34/35 with 9,725,616 B peak and
  515,478,752 B traffic. Fixed first-slot eviction also failed adversarial traffic;
  both are rejected historical prototypes. Final sixteen-probe rotating-victim
  cache passes forced-collision, deletion-hole, full-window, stale-body, snapshot,
  escaped-reference and GC tests.
- Shared added runtime state: identity cache 4,112 B; allocator classes/bitmap
  1,544 B. These and diagnostic maps are not charged to arbitrary U1 owners.
- Final AB/BA worker0 timing is roughly flat (~1.5% higher median wall time amid
  variance). Do not claim compiler speedups or reuse prototype speedups.
  See [investigation](docs/performance/U1A_OWNER_MEMORY_INVESTIGATION_2026-10-31.md)
  and [qualified raw record](docs/evidence/2026-10-31/u1a-owner-105-qualified.json).

### Accepted boundary and next work

U1a's private in-memory source publication/revisions, diagnostic map ingress,
bounded scalar transformations, direct-IR owners/buffers/resource measurements
and independent verification are accepted. Persistent source/native artifact
formats/cache manifests and end-to-end source physical performance remain **U3 #75**.
Managed Text/List/identity runtime/root/cleanup acceptance remains **U2 #74**.
U4 target legalizations/artifacts remain **#102**. No public UIR serialization is frozen.

Next execute the already-authorized sequence: **U1b immutable aggregates #73 →
U2 #74 → U3 #75 → U4 #102**, with complete compiler phase profiling #51 and
performance/memory budgeting throughout. Full qualification is once per coherent
final implementation, with focused tests during development. The source language,
existing ABI and rollback/default production pipeline must remain intact.

The local execution environment disconnected after preservation of all code and
raw evidence. GitHub remains available; hosted qualification completed and the
verified merge is preserved. Do not claim any later milestone was implemented
during this checkpoint. A documentation-only patch check validates this
reconciliation; the tested implementation is unchanged.

**Administrative closure verified:** issue #77 was closed as completed on 31 October 2026 after the qualified merge and acceptance documentation were recorded. U1a is complete within its adopted boundary. U1b aggregates, U2, U3 and U4 remain open. This status-only reconciliation changes no tested implementation.

### Latest recovery checkpoint — 2026-10-31

**Execution workspace restored; previous next-stage blocker resolved.** Shell,
repository reads and a clean worktree were verified. The investigation worktree
remains at qualified head `f1fba11`; main contains the merge and subsequent
acceptance documentation. Start the next implementation branch from current
main, preserving the investigation branch and its evidence.

GitHub status was rechecked: #105 is merged at `8c625b1`, #77 is closed,
and smoke, full CI and completed-batch qualification above all report success
for exact head `f1fba11`. No implementation or expensive test rerun was needed
for this handover-only update.

| Work | Current status | Resume point |
| --- | --- | --- |
| U1a / #105 / #77 | ✅ Scoped acceptance qualified, merged and closed | Preserve boundaries and raw evidence above |
| U1b #73 — narrow integers | ✅ i8/i16/i32 reference execution slice complete | Preserve existing coverage; U1b as a whole is not complete |
| U1b #73 — immutable aggregates | ⬜ Not started | Next implementation stage |
| U2 #74 | ⬜ Pending | After U1b aggregates |
| U3 #75 | ⬜ Pending | After U2 |
| U4 #102 | ⬜ Pending | After U3 |
| Compiler performance #51 | ⬜ Complete phase profiling unfinished | Continue throughout the sequence |

Resume by reading #73, the U1 contract §§3–4, the remaining acceptance plan and
`CI_QUALIFICATION.md`. Implement and independently verify owner-scoped immutable
aggregate types and make/get/set operations with static field checks, value-copy
semantics, cycle rejection and bounded resources. Aggregate design discussions
were planning only; no aggregate implementation has been written or qualified.
The existing authorization covers this continuation; no renewed permission is
needed.

Final accepted stress results remain **24,400,832 → 7,853,712 B phase peak**,
**21,957,296 B cumulative traffic**, and **72,682 graph allocations**, with the
original 8 MiB / 64 MiB gates unchanged. Exact retained backing is **6,653,840 B /
16,938 objects**, all reclaimed. Final worker0 timing remains roughly flat:
8.135968 → 8.254257 s median (0.9857×); this is no whole-compiler speedup claim.
The experimental owned compiler full self-build remains unqualified.

### Permanent philosophy mandate recorded — documentation-only checkpoint (2026-10-31)

The user's standing instruction is now explicit in the opening **Mandatory
philosophy-first engineering discipline** section and in the new-chat recovery
prompt. Every future session and implementation/optimization decision must read
the complete governing `DESIGN_PHILOSOPHY.md`, locked semantics, applicable
architecture and CI policy; apply **Philosophy → Semantics → Architecture →
Implementation**; design for correctness/safety first and measured performance,
memory and predictable CI immediately afterward. Keep the language small and
readable, preserve the source semantics/current production pipeline and report
only independently qualified milestone progress. This requirement carries into
all later handovers automatically; do not await another user reminder.

This is a HANDOVER.md-only documentation update, including a reconciliation of
the previously stale workspace warning with the latest restored-workspace
checkpoint. It changes no compiler/runtime files, qualification inputs,
accepted U1a results, issue or PR statuses. Use documentation-only patch
checking; do not rerun costly CI or experimental self-build for this update.

## 45. Active U1b immutable aggregate type graph and reference operations — 2026-10-31

**Branch:** `compiler/u1b-owned-aggregate-graph-20261031`, forked from main
`ccfe726ad80212c9a10ee16d5f3cf17e52db160a`.
**Status: SOURCE + FOCUSED SMOKE TESTED (38/38); full U1b qualification PENDING,
NOT merged, NOT full U1b completion.** Draft [PR #106](https://github.com/eristavi/eristavi-lang/pull/106),
exact latest focused-passed code head `9ff2e11322f0b42154cfb7effa0ebd25414e0366`.
The previous tested graph-only head `539d9d6` also passed (37/37); the
current value-execution slice is additive and has a newer independent test.
Last qualified release remains U1a §44.
The source review also read `DESIGN_PHILOSOPHY.md`, `LANGUAGE_SEMANTICS.md`,
the approved U1 operation contract §§2–4, independent verifier/resource rules
and `CI_QUALIFICATION.md`. The standing philosophy-first mandate in this
handover is still binding.

### What the draft implements

- `src/compiler/u1_aggregate.eri`: **opt-in, owner-scoped aggregate type
  graph**, retaining exactly six primitive internal U1 type indices.
  Canonical ordered structural interning (including zero-field aggregates),
  collision-checked full field sequences, nested field type references,
  exact field-count/index access, immutable freeze/close lifecycle and owner
  cancellation/physical charge through the existing `u1_words` store.
  Aggregate members may name only an existing type in the same graph, making
  forward/cyclic by-value type definitions unconstructible through this API.
  It is explicitly **not** a source nominal-type system, runtime object layout,
  additional source type/keyword, public UIR serializer or new ABI.
- `src/compiler/u1_aggregate_verify.eri`: independently walks the frozen
  record graph, recomputes structural hashes and canonical hash chains,
  validates nested field order, range/ownership, strictly earlier aggregate
  references, malformed/cyclic/forward records, duplicate canonical shapes
  and bucket-head consistency. It does NOT trust the builder's flags.
- `tests/fixtures/u1_aggregate_graph.eri` and
  `tests/test_u1_aggregate_graph.py`: proposed focused native smoke for
  canonical empty/nested types, deliberate hash collision, foreign owner
  rejection, static field range, tampered by-value cycle, malformed bucket,
  duplicate record, frozen-only verification and exact owner reclamation.
  On the exact final focused code head these checks passed in hosted smoke;
  this does not certify full U1b operations or independent physical backing.
- Existing `u1_meta.Metadata` and `u1_builder.Function` physical layouts,
  scalar opcode registry and production frontend/backend remain unchanged to
  preserve the already-qualified #105 physical fixture and 32-byte public ABI.
  The aggregate type graph remains an opt-in sidecar, **not** canonical
  UIR instruction integration. Existing U1a tests also passed in the
  newest focused hosted batch.

- `src/compiler/u1_aggregate_values.eri`: **new opt-in reference value
  engine** implementing semantically defined `aggregate.make/get/set`
  through a checked immutable value graph. A field read shares an immutable
  earlier value; replacement copies the immediate member-index sequence into
  a NEW node without mutating the original. Nested updates maintain value
  snapshots. Both value IDs and aggregate type IDs carry distinct owner
  identity, and execution validates the frozen type graph independently.
  This is a reference model, **not** the authoritative canonical UIR op
  implementation or source/native runtime representation; the O(n) shallow
  update copy must be evaluated against the native scalarization/path-copy
  alternatives before production promotion.
- `tests/test_u1_aggregate_values.py`: 3-size (2, 9, 32 fields) independent
  Python tuple-copy oracle plus an empty value and nested aggregate case.
  Rejects wrong arity, wrong field/type, wrong replacement, foreign ValueId;
  checks old/new alias isolation and full owner/budget close. The test
  compiles and executes a real Eristavi-written private reference engine;
  it does NOT substitute for independent canonical UIR verifier/oracle tests.

### Performance-first constraints and remaining acceptance

- Sidecar allocation is opt-in; normal U1a creation has no added graph object.
  Current provisional ceilings: 65,536 aggregate records, 524,288 field words,
  at most 4,096 components per aggregate, 256 hash bucket heads. The
  hash-chain lookup is bounded by records/work limits but worst-case collision
  work may be high; measure real memory, traffic and adversarial collisions
  and improve if needed before promotion. Do NOT claim any measured speedup.
- **Focused qualification evidence (NOT full qualification):** hosted CI
  [41234799166](https://github.com/eristavi/eristavi-lang/actions/runs/41234799166)
  **PASSED, 37/37 tests**, 101.65 seconds, on exact code head
  `539d9d6b4589759d47e2c53d5941d1ac8dc7fdbc`. New native graph+verifier
  test passed. The two earlier exploratory runs failed only because the
  standalone test initially omitted checked error forwarding
  ([41234293306](https://github.com/eristavi/eristavi-lang/actions/runs/41234293306))
  and then lacked a concrete existing U1a generic metadata signature
  specialization ([41234590567](https://github.com/eristavi/eristavi-lang/actions/runs/41234590567)).
  Corrective fixture commits `1f810ee` and `539d9d6` resolved both without
  any changes to the existing U1a metadata/runtime implementation.
  These are historical failed test candidates, not current regressions.
  Existing smoke cases passed in all three runs; last graph-only run was green.
  **Latest additive value-execution code gate**:
  [41235680069](https://github.com/eristavi/eristavi-lang/actions/runs/41235680069)
  **PASSED 38/38 tests** in 134.525 s, exact code head
  `9ff2e11322f0b42154cfb7effa0ebd25414e0366`;
  new `test_u1_aggregate_values` and old U1a owner-physical smoke passed.
  The four-platform full test matrix job was **skipped by design**.
  No final U1b/owned self-build qualification is implied.
  This environment's container had no GitHub-resolvable repository checkout;
  GitHub-hosted smoke provides test evidence, not full owned self-build certification.
- **Before claiming full U1b:** connect the tested aggregate type graph and
  reference value semantics to the **canonical** program-owned metadata/
  TypeId model and the single approved UIR operation registry. Implement
  real instruction builder/closed registry/independent V0–V5 verifier,
  copy-preserving SSA promotion and actual canonical UIR reference execution
  with a separate Python oracle. The isolated value-copy/alias checks above
  cover only the reference model, **not** the canonical instruction path.
  Still require static field types, malformed *unreachable* instructions,
  cycles, cancellation, owner reclamation, large/deep resource stress and
  measured per-owner physical backing. Preserve original source failure/LocId and pure operations.
  Keep runtime-managed Text/List/identity out of U1b.
- After all such code passes focused validation, select **one coherent final
  four-platform full CI and completed-batch qualification**, compare the exact
  tested and merge trees, then update issue #73 and the opening handover state.
  **Never start experimental full owned compiler self-build automatically.**
- Continue whole-compiler measured phase profiling (#51) separately, with
  production runtime/ABI/source behavior unchanged. U2 #74, U3 #75 and
  U4 #102 remain strictly downstream, not green from this candidate.

**Next action:** PR #106 is DRAFT and latest focused smoke is green at
`9ff2e11`. Integrate type graph and independently tested value semantics into
the **canonical UIR**, without altering already-qualified U1a metadata/Function
physical object layout or public ABI unless independently budgeted and
requalified. Carefully extend the operation registry and independent verifier
for `aggregate.make/get/set`, including *unreachable* instructions, SSA copy
semantics, effects/LocId and cancellation. Benchmark candidate work/physical
memory and analyze scalarization against the intentionally simple O(n)
reference copy. Run full four-platform CI/qualification **only once** after the
coherent final U1b batch. Do not merge this PR or close #73 from a green smoke.
The handover-only status reconciliation after `539d9d6` changes no tested
compiler/runtime inputs and requires only lightweight documentation checking.

### Tested aggregate-graph checkpoint — 2026-10-31

- **Last code-bearing candidate:** `539d9d6b4589759d47e2c53d5941d1ac8dc7fdbc` (unmerged draft #106).
- **Exact-head smoke:** [run 41234799166](https://github.com/eristavi/eristavi-lang/actions/runs/41234799166) — 37/37 passed, 101.65 seconds, including the new U1b aggregate type graph test and existing U1a physical-ownership checks. Full matrix and owned compiler qualification intentionally **not requested**.
- **No milestone promotion:** U1b still open. Full aggregate operations, independent execution/conformance, malformed UIR, budget/cancellation and owner physical acceptance not delivered. U2–U4 untouched.
- **Next stage:** integrate type owner references and canonical aggregate `make/get/set` with independently verified exact value-copy semantics. Keep ABI/source/production behavior unchanged and optimize measured work/memory from design, not at the end.

### Tested immutable reference value checkpoint — 2026-10-31

**Source now exists and focused tests have passed, but the canonical UIR
aggregate acceptance remains unimplemented.** On draft PR #106,
code commit `9ff2e11322f0b42154cfb7effa0ebd25414e0366` is the EXACT
revision exercised by [focused hosted run 41235680069](https://github.com/eristavi/eristavi-lang/actions/runs/41235680069).
The Linux Clang smoke finished **success, 38/38 tests in 134.525 seconds**;
`test_u1_aggregate_graph`, `test_u1_aggregate_values` and the existing
owner-physical regression suite all passed. The native-value test covers
2/9/32 fields, empty, nested, nonmutating replacement/alias isolation,
static type/index failure and cross-owner value rejection versus a standalone
Python immutable-tuple oracle. No source language syntax, ABI, U1a physical
record layout or default compiler path changed. Full matrix/qualification
skipped intentionally; experimental full owned self-build not run.

The representation intentionally uses shallow member-vector copy on set:
**O(number of fields) work and added member words**, with immutable child
value sharing. This is sufficient as an independent semantic reference but
is **NOT** evidence that the eventual machine lowering or managed runtime
should use that representation. Before selecting a production path, compare
scalar field replacement, stack/register lowering and persistent structures
with real work, allocation traffic, owner backing, RSS and same-host timings.
Any change must retain the first-observable-fault/LocId and verified
immutable value semantics.

**Resume after this document-only update:** the tested code revision is
`9ff2e11`; newer HANDOVER-only commits must not be described as a tested code
revision. Next implement the canonical program-owned aggregate typed SSA
instruction schema, independent verifier and executable oracle, including
malformed dead blocks and cancellation, then targeted deep/large/physical
stress; keep #73 open and PR #106 unmerged until final exact-head qualification.
Continue the permanent philosophy-first policy at the opening of this file.

## 46. U1b canonical aggregate typed SSA construction and independent verification — focused TESTED 2026-10-31

**Current draft:** [PR #106](https://github.com/eristavi/eristavi-lang/pull/106)
on branch `compiler/u1b-owned-aggregate-graph-20261031`, based on
`main` `ccfe726ad80212c9a10ee16d5f3cf17e52db160a`.
**Last code-bearing and exactly tested head:**
`677e6d92175a4f91408e864644674ec60dbe42dd`.
**Focused Linux Clang smoke:** [run 41237356963](https://github.com/eristavi/eristavi-lang/actions/runs/41237356963)
**SUCCESS — 39/39 tests, 106.167 seconds**. The new
`test_u1_aggregate_ssa.U1AggregateSSATests.test_canonical_aggregate_operations_and_independent_dead_code_verifier`
**PASSED**, together with the earlier aggregate graph and immutable reference
value tests and existing U1a regression tests. Four-platform full matrix
**SKIPPED BY DESIGN**; no final U1b acceptance, U2/U3/U4 acceptance, or
experimental full owned self-build is claimed. This section supersedes §45
**for current stage/test status only**; §45 retains historical evidence.

### Implemented and tested in the actual canonical UIR instruction tables

- **`src/compiler/u1_ops.eri`:** private U1b opcodes
  **43 = aggregate.make**, **44 = aggregate.get**,
  **45 = aggregate.set**. Frozen graph supplies ordered operand types,
  exact static field ordinal and exactly one typed SSA result. Operations
  are effect-free under U1. No new Eristavi source keywords or public opcode
  serialization/ABI contracts.
- **`src/compiler/u1_aggregate_build.eri`:** opt-in typed construction of
  op43–45 writes the actual 10-word `u1_builder.Function.instructions`,
  `values` and `operands` tables, preserves LocId, updates revision,
  rejects wrong owner, field ordinal, arity and operand/replacement types
  before mutating the IR. Uses a frozen same-request aggregate type graph.
  **Existing 17-field Function and 14-field Metadata physical object layouts
  remain unchanged**, protecting prior #105 owner-layout acceptance.
- **`src/compiler/u1_verify.eri`:** explicit
  `verifyAggregates(routine,registry,phase)` first independently verifies
  the immutable type graph, then independently derives op43–45 structural,
  type, attribute, result and SSA facts for **ALL blocks, including
  unreachable malformed instructions**. The normal legacy `verify`
  remains fail-closed and rejects these U1b opcodes without this profile.
  On malformed type-graph rejection **both the graph phase and supplied
  function verification phase are finished**, fixing an observed
  checked-cleanup failure. Cached builder/verified flags confer no trust.
- **`src/compiler/u1_aggregate.eri`:** frozen metadata type graph now
  allows checked read-only access by a same-root function phase under the
  existing `u1_words` shared-read ownership protocol. Construction and
  mutations remain restricted to its metadata owner.
- **`tests/fixtures/u1_aggregate_ssa.eri`** and
  **`tests/test_u1_aggregate_ssa.py`:** construct nested canonical SSA
  aggregate make/get/set; test old-value/new-value SSA IDs; old U1a
  profile rejection; new U1b acceptance; dead aggregate field/attribute
  tampering, wrong result/operand TypeIds, missing source LocId,
  corrupted frozen type graph, revalidation after restoration and
  exact scratch/owner cleanup. An unreachable typed CFG edge also
  exercises existing generic edge specialization. Added to focused CI.
  **The test proves construction/independent verification, not aggregate
  runtime execution of this SSA program.**

### Failed exploratory CI candidates and resolution (NOT green qualifications)

- [41236536450](https://github.com/eristavi/eristavi-lang/actions/runs/41236536450):
  patch check rejected trailing fixture whitespace; corrected.
- [41236570638](https://github.com/eristavi/eristavi-lang/actions/runs/41236570638):
  Eristavi requires explicit optional-registry refinement before member
  access; corrected nested condition handling.
- [41236736653](https://github.com/eristavi/eristavi-lang/actions/runs/41236736653):
  standalone fixture lacked an analyzed existing generic `checkEdge`
  specialization; added explicit dead-component CFG edge.
- [41237150043](https://github.com/eristavi/eristavi-lang/actions/runs/41237150043):
  malformed type graph exposed an unclosed caller verification phase;
  fixed in `677e6d92175a4f91408e864644674ec60dbe42dd`.
- The final focused run **41237356963 PASSED 39/39**. Neither historical
  failed revisions nor the current draft is a completed full qualification.

### Still required for the U1b #73 acceptance gate

1. Bind aggregate type graph to the **single canonical program-owned
   metadata/TypeId and signature model**, with owner-safe exact remapping
   across function signatures/calls, block parameters and CFG edges;
   preserve existing 32-byte public Eristavi ABI and U1a owner layouts.
   The current opt-in sidecar plus scalar-only function signatures is
   NOT the complete program aggregate model.
2. Execute op43–45 through the **canonical verified UIR**, not merely
   the separately tested `u1_aggregate_values` reference API. Provide
   independent Python oracle and exact old/new value-copy, nesting,
   empty aggregate, alias and original-LocId behavior over three sizes.
3. Qualify mandatory cell-to-SSA promotion and pass/revision invalidation
   for aggregate-containing canonical programs, including loops, phi
   swaps, unreachable malformed records, cancellation, allocation
   refusal, fully released backing and no partial publication.
4. Measure actual large/deep/collision-heavy owner **peak/live/traffic
   and physical backing**, independent work events, process RSS and
   same-host compilation/runtime timing. Current reference update copies
   an immediate member array in **O(number of fields)**, which is a
   semantic oracle choice, NOT a demonstrated optimal native design.
   Evaluate scalarization and safe aggregate value layouts with measured
   budgets; do not equate owned charge with process memory or claim
   wall-time improvement without paired measurements.
5. **Only once the coherent full U1b batch is ready**, run final four-platform
   matrix and completed-batch qualification on the exact code head,
   compare tested and merged trees, then decide readiness of PR #106
   and closing #73. **Do not run experimental owned compiler self-build
   without explicit user authorization**. U2 #74 → U3 #75 → U4 #102
   remain subsequent milestones; #51 compiler profiling stays a
   parallel optimization task.

**Next recovery action:** verify fresh GitHub/PR head; if only this
HANDOVER.md is newer than the code commit `677e6d92175a4f91408e864644674ec60dbe42dd`,
the focused tests still apply to unchanged code, NOT to untested code updates.
Start with program-owned aggregate signature/call/CFG type plumbing and an
independently executing verified UIR path; keep the opt-in construction
fail-closed and the production compiler unchanged. Follow the permanent
**Philosophy → Semantics → Architecture → Implementation** mandate above,
and update this handover after every substantive change.

## 47. Canonical U1b aggregate SSA reference execution candidate — 2026-11-01

**Draft branch:** `compiler/u1b-owned-aggregate-graph-20261031`, PR #106.
**Exactly focused-tested code revision:** `bc743faf135927fa59b172cab2f151173fd07565`.
**Status:** new opt-in canonical reference execution slice IMPLEMENTED and **focused CI PASSED 40/40**;
not fully qualified, merged or U1b-complete. Last passing canonical construction
checkpoint is §46 (39/39, commit `677e6d9`, run 41237356963).

- `src/compiler/u1_aggregate_execute.eri` performs FRESH, independent
  `verifyAggregates` on actual canonical SSA instructions before execution;
  reads the real 10-word `Function.instructions` records, SSA value indexes,
  and immutable op43/44/45; executes primitive constants and scalar returns,
  guard, and produces explicit bounded fuel/unsupported outcomes with LocId.
  It reuses `u1_aggregate_values` only as a **semantic reference store**;
  this is not a second IR, the production evaluator, native backend or ABI.
  A function-owned execution value store and SSA slot table are closed on
  success and checked refusal; all returned values are copied to scalar
  results. Current bounded profile: one reachable straight-line block,
  scalar entry/signature, at most 16 scalar results, and no Float, calls,
  branches, aggregate signature returns or aggregate CFG operands.
- `tests/fixtures/u1_aggregate_execution.eri` and
  `tests/test_u1_aggregate_execution.py` compile the real Eristavi U1b
  executor and independently check canonical make/get/set old/new snapshots
  with expected 11/17 scalar results and owner reclamation; the new Python
  test is added to the **focused CI list**, not the full qualification gate.
- Work/memory design: one owned SSA slot table (zero-initialized once),
  immutable value engine with existing bounded type/member/node quotas,
  fuel-capped instruction steps. Aggregate `set` remains O(n) reference
  member-copy, **not a proposed native representation or speedup claim**.
  No changes to production compiler, source semantics, existing U1a layout
  or 32-byte public ABI. Existing reference execution is opt-in and does
  not establish full U1b type/call/CFG semantics.
- **Verified focused result:** [run 41278535614](https://github.com/eristavi/eristavi-lang/actions/runs/41278535614) **SUCCESS**, 40/40 tests, 153.587 seconds, on exact CODE head
  `bc743faf135927fa59b172cab2f151173fd07565`, including native
  `test_verified_canonical_ssa_immutable_execution` and existing U1a/U1b
  smoke/physical-owner checks. Four-platform full CI **SKIPPED** by design.
  Earlier exploratory runs failed only in the NEW executor and were fixed:
  [41277911119](https://github.com/eristavi/eristavi-lang/actions/runs/41277911119)
  syntax; [41278106311](https://github.com/eristavi/eristavi-lang/actions/runs/41278106311)
  standalone generic edge specialization;
  [41278235109](https://github.com/eristavi/eristavi-lang/actions/runs/41278235109)
  concrete input-list specialization;
  [41278387039](https://github.com/eristavi/eristavi-lang/actions/runs/41278387039)
  function-owned instruction tables accessed through a foreign execution owner.
  Final code reuses the exact function owner and closes all reference storage.
  These historical failures are not qualified. No full four-platform CI or
  experimental owned compiler self-build was requested.
- **Subsequent work:** independent varied 2/9/32 field and nested oracle,
  explicit malformed dead-block/fault/LocId/exhaustion checks, true program
  owned aggregate signature/call/CFG types, canonical SSA value promotion,
  physical backing and performance evidence. Preserve failure cleanup and
  the philosophy/semantics/architecture ordering. PR #106 stays DRAFT, #73
  OPEN. Keep this checkpoint reconciled with actual CI evidence.

### Exact-head result reconciliation — 2026-11-01

The newest code-bearing candidate `bc743faf135927fa59b172cab2f151173fd07565`
**PASSED 40/40 focused Linux Clang CI tests** at
[run 41278535614](https://github.com/eristavi/eristavi-lang/actions/runs/41278535614).
The new canonical verified UIR executor returned independent scalar snapshots
`11` (original) and `17` (immutable replacement), with exact per-function
owner lifecycle reclamation. The existing accepted U1a physical regression and
all prior U1b focused tests remain green. **Do not conflate this with full
U1b execution/conformance or an owned native compiler acceptance.** Next:
run independent randomized/three-size nested aggregate canonical-execution
oracles, malformed dead code and trap/source-location profiles; integrate
aggregate signatures/calls/CFG and canonical SSA promotion; then adversarial
resource/physical performance evidence before one final expensive qualification.
Current HANDOVER-only commits do not change the passing executable code.

## 48. User-requested expensive qualification and closure review — 2026-11-01

**Request:** run one expensive test, close only issues/work that actually meets
acceptance. Draft PR #106 was marked **Ready for review** and given the existing
`qualification` label at head `4649763d0fe388eff9f9789eb965988e1e0b0433`
(documentation-only successor of focused-pass code `bc743faf135927fa59b172cab2f151173fd07565`).
Under `CI_QUALIFICATION.md`, ready-for-review selects the 4-platform full CI;
adding `qualification` selects full CI plus the three Linux bootstrap repeatability
and owned integration jobs. The separately manual `owned-self-build` profile was
**NOT requested**. These selectors are one requested qualification batch, not
proof that a workflow executed.

**Live result at this checkpoint: NOT STARTED/NOT OBSERVED.** GitHub returned
**zero** workflow runs and **zero** checks for the exact PR head after both
selector mutations; the last confirmed green evidence remains focused run
[41278535614](https://github.com/eristavi/eristavi-lang/actions/runs/41278535614)
(40/40), NOT full CI. No full-matrix or completed-batch qualification has
passed. The test must NOT be marked completed on the strength of the label or
an unrelated historic run. Before proceeding, recheck head-specific GitHub
Actions runs and job results, and investigate why the workflow event produced
no run; manually dispatch `Eristavi CI` full at the exact ref via GitHub Actions
if the event remains unprocessed, rather than repeatedly triggering redundant
qualification batches. Do NOT run experimental full owned compiler self-build.

**Closure audit (issue state checked against GitHub):** #77 and #71 are already
closed; #105 is already merged. #73 **must stay OPEN** because aggregate
signatures/calls/CFG, independent nested execution/oracle, promotion and physical
resource/performance qualification remain missing; PR #106 cannot merge solely
because old or future full CI is green. #74 U2 managed semantics, #75 U3 direct
production integration, #102 U4 machine lowering and #51 compiler-performance
investigation are also **OPEN/unfinished**. No newly closable issue was established
by the current code and focused evidence. No issues were closed or PR merged.

**Important:** preserve governing philosophy, frozen semantics, original ABI,
owner accountability, and optimization-first/limited-test policy. Do not
confuse a CI event request, a queued workflow, a succeeded workflow and
completed milestone acceptance. Resume at this section and reconcile exact
head/checks before any merge or closure action.

## 49. Current U1b follow-up and workflow capability audit — 2026-11-01

**Repository admin rights confirmed**, but connected GitHub tools expose no
workflow-dispatch action: the available GitHub fetch action is GET-only and
attempts to find an approved workflow-dispatch action were unsuccessful. PR #106
was made ready and labeled `qualification` in response to the user's full-test
request, yet GitHub showed **zero new workflow runs/checks** for that head.
This is NOT a completed expensive qualification. Because #73 remains incomplete,
the qualification label was subsequently removed and PR #106 returned to
**DRAFT**, avoiding an accidental claim that the current implementation is
release-ready. GitHub admin privileges do not bypass missing connector methods.

**New unqualified optimization candidate:** code commit
`b38ea99c832d7b82153a0e6f250dce7b82aca50c` removes an unnecessary
`aggregate.get` from the `aggregate.set` case of the opt-in verified canonical
SSA reference executor. The old path fetched a field (with validation/work)
before discarding it and copying the aggregate; the independent verifier and
`av.set` already check field type and ordinal. The new branch condition only
calls `get` for get operations. This is a bounded algorithmic improvement,
**not a measured performance gain** and NOT TESTED/qualified until focused CI
on this exact code revision passes. Last confirmed green focused suite remains
40/40 at `bc743faf135927fa59b172cab2f151173fd07565` (run 41278535614).
A subsequent check confirmed focused Linux smoke run [41279349991](https://github.com/eristavi/eristavi-lang/actions/runs/41279349991) for code commit `b38ea99`, initially IN PROGRESS. The full four-platform matrix was explicitly SKIPPED in that run. Recheck actual completion before claiming the optimization tested; this run does not qualify full U1b.

**Still OPEN**: #73, #74, #75, #102, #51. Existing closed #71/#77 and merged
#105 remain correctly closed. No new milestone can be closed from these results.
**Next action:** verify CI for new code SHA, and continue focused oracle,
aggregate signatures/calls/CFG, promotion and owner/physical tests. For full
four-platform CI, a workflow_dispatch-capable client/app is required or the
repository's Actions UI can be used; do not falsely report it started. Preserve
frozen semantics, exact ownership, rollback, and full qualification gates.

## 50. U1b canonical CFG reference execution — development candidate (2026-11-01)

**Code head:** `febeaed06536d560994982631030cdca3ca0b264` on draft PR #106.
**Focused run:** [41279731193](https://github.com/eristavi/eristavi-lang/actions/runs/41279731193), queued/in progress at writing, **NOT YET QUALIFIED OR GREEN**.
The previous pure `aggregate.set` optimization at `b38ea99` passed focused run
[41279349991](https://github.com/eristavi/eristavi-lang/actions/runs/41279349991).

- `src/compiler/u1_aggregate_execute.eri` now accepts verified canonical
  jump/branch/sparse-switch instructions and stages every edge argument in
  bounded, owner-charged `words.Words` storage before assigning destination
  block parameter slots. This preserves simultaneous phi/block-parameter
  semantics on edges and includes fuel charges for traversed edges, reusing
  scratch instead of per-edge allocations. Unsupported operations remain
  explicitly unsupported. Still a narrow opt-in canonical reference executor.
- The existing `tests/fixtures/u1_aggregate_execution.eri` test now routes
  the original/updated immutable field result pair through an actual
  `build.branch` to a 2-parameter target block and returns those values,
  with a second alternative arm also present for structural verification.
  It does **not yet** test both branch outcomes, aggregate-typed block
  parameters or loops. It is **not** the complete independent nested Python
  oracle nor aggregate signature/call/CFG promotion acceptance.
- All production U1a metadata, 32-byte public ABI, source grammar and
  default compiler remain unchanged. No full matrix or expensive owned
  self-build was invoked. PR #106 remains draft, issue #73 remains OPEN.

**Next:** inspect the exact-head focused CI logs and fix regressions before
marking any of these lines tested; then complete independent 2/9/32-field
nested oracle, source-neutral aggregate signatures/block parameters/calls,
aggregate-capable mandatory SSA promotion, cancellation, physical owner backing
and measured perf. Follow philosophy → semantics → architecture → implementation;
update this section with actual evidence and no optimistic milestone closures.

## 51. Active U1b canonical oracle, aggregate signatures, CFG and promotion — 2026-11-01

**Work branch:** `compiler/u1b-owned-aggregate-graph-20261031` / draft PR #106.
**Latest implementation head (NOT yet passing):**
`008e70264b84217901f9519f350c4328352474ca`.
**Focused CI** [41280474424](https://github.com/eristavi/eristavi-lang/actions/runs/41280474424)
initially pending; recheck actual result. **Do not mark passing or complete** until
this exact code is green. Four-platform full CI and owned self-build were NOT
requested for this unfinished batch.

### Implementation now on branch

- Opt-in `u1_aggregate_execute.eri` reads **canonical verified SSA**
  operation records, executes approved i64 comparison semantics and immutable
  make/get/set; takes checked jump/branch/switch edges, staging simultaneous
  block-argument transfers in bounded owner-accounted scratch. This is a
  reference executor, not source/native production integration.
- `test_u1_aggregate_canonical_oracle.py` generates 2/9/32-field values,
  empty/nested projection/update snapshots, and independent Python immutable
  tuple expectations across both branch outcomes. Its earlier exploration
  [41279847076](https://github.com/eristavi/eristavi-lang/actions/runs/41279847076)
  failed because the executor lacked i64 comparison and a fixture expected
  the wrong step count; corrective commits `15e617a` and `888d486`
  implement comparison and correct the step count. **Oracle is NOT yet
  qualified** without passing the newest actual code-head run.
- `u1_aggregate_signature.eri` interns owner-scoped aggregate signatures in
  the EXISTING six-word metadata signature table and 64-bucket index; this
  deliberately retains the old public ABI and original 14-field Metadata
  layout. `u1_aggregate_build.eri` has opt-in canonical aggregate block/
  edge/return/complete adapters with static TypeId/arity/owner checks, not an
  extra execution IR. `u1_verify.eri` exposes independent
  `constructionAggregates`/ `verifyAggregates` and does not grant trust from
  builder flags. `u1_promote.eri` exposes `promoteAggregates`, uses unchanged
  owned SSA promotion algorithm with independent aggregate input/output
  verification and aggregate-completion logic, without changing State layout.
- Focused signature/promotion test verifies canonical scalar signature
  interning compatibility, aggregate TypeIds in the existing metadata table,
  aggregate typed entry/block/edge, scalar cell promotion and independent
  output verification. The exploratory run
  [41280226897](https://github.com/eristavi/eristavi-lang/actions/runs/41280226897)
  FAILED due generic helper member-field type inference, which also disturbed
  old U1a compiler tests. The aggregate signature helper now binds generic
  elements explicitly. The tested U1a path no longer imports the entire
  aggregate builder: new `u1_aggregate_finish.eri` contains the single
  completion implementation used by U1b construction and promotion. This
  isolation is the latest candidate `008e702`, **not yet validated**.

### Performance/evidence/acceptance still outstanding

- The aggregate reference `set` now skips an unnecessary get, with earlier
  focused 40-test suite passing on [41279349991](https://github.com/eristavi/eristavi-lang/actions/runs/41279349991).
  No measured speedup claim. The aggregate reference materialization
  remains O(number of fields), not a production native lowering commitment.
- A memory-evidence **draft** was prepared but not merged: it would emit
  owner-model peak/traffic and capture actual child-process peak RSS. These
  are different attribution scopes, and **neither** demonstrates actual new
  U1b per-owner physical retained backing without an independent allocator
  diagnostic like U1a #77. Larger adversarial aggregate/owner memory tests,
  cancellation, nested oracle across calls, negative unreachable CFG and
  complete exact-head qualification remain missing.
- Aggregate **direct call construction** and its checked integration were
  designed but not yet merged/tested. Full multi-function aggregate reference
  execution, recursive calls, aggregate signatures at runtime and true native
  lowering remain incomplete. **Do not close issue #73 or merge PR #106.**
- U2 #74 → U3 #75 → U4 #102 remain next milestones. #51 whole-compiler
  profiling stays open. Scoped U1a #77 remains qualified/closed at §44.

**Next:** inspect focused run #41280474424, fix observed failures, then add
fully checked canonical aggregate call construction, paired execution/CFG/SSA
negative tests, independent actual owner-backed physical evidence and a
measured baseline. Only after all U1b gates pass run one full four-platform
CI plus completed-batch qualification and decide release/closure. Follow
mandatory philosophy → semantics → architecture → implementation and retain
performance/safety and precise owner/fault/ABI boundaries.

## 52. Latest verified U1b physical/signature/oracle checkpoint and loop re-entry slice — 2026-11-01

**Previous exact tested head:** `1382dc899c7a930507786269a2d5afa3dae65bfe`.
[Focused Linux Clang CI 41281956706](https://github.com/eristavi/eristavi-lang/actions/runs/41281956706)
**SUCCESS 43/43**, 162.479 seconds. This supersedes section 51's
`008e702` NOT YET PASSING state. Tests included independent
2/9/32-field and nested canonical-value oracle; both CFG arms;
structural type/signature interning; typed aggregate CFG and verified
scalar-cell promotion; checked aggregate direct-call construction
(**NOT** runtime execution); and the actual U1b physical backing probe.

**Scoped real physical backing, actual tagged owned-runtime blocks:**
metadata aggregate registry **44,448 B across 116 allocated objects** and
function aggregate value engine **22,720 B across 60 objects**; the observed
GC reclaimed all **67,168 B / 176 objects**, leaving zero live backing
for those owner tags. Structural backing and ledger values were
respectively metadata 36,992 B / 129,632 B peak and traffic,
function 18,720 B / 45,408 B peak and 68,128 B traffic.
These observations are separate: do NOT conflate physical tagged actual
backing, logical owner ledger, full process RSS, or whole-compiler heap.
No canonical multi-function runtime physical acceptance is implied.
The exact fixture and tests remain committed:
`tests/fixtures/u1b_aggregate_physical.eri`,
`tests/test_u1b_actual_physical.py`.
The 15.642-second private test is currently included in the 43-test smoke,
so monitor CI cost and consider moving heavier scale studies to an opt-in
profile; do not remove existing assertions to improve timings.

**New implementation candidate (FOCUSED TESTED 44/44; NOT FULLY QUALIFIED):** a single-copy SSA
runtime-slot fix in `u1_aggregate_execute.eri` replaces each dynamic
execution's value token in its static SSA slot, as required for CFG
backedge re-entry. The independently verified canonical SSA stream
guarantees each static value definition's uniqueness; repeated loop
visits produce new immutable runtime values and must NOT fail as
duplicate publication. The prior per-save duplicate test incorrectly
rejected every second loop visit and did an avoidable per-result read.
No UIR schema, source syntax, Function/Metadata object, public ABI
or production backend changed.

`tests/fixtures/u1_aggregate_loops.eri` and
`tests/test_u1_aggregate_loops.py` independently check two dynamic
iterations of a typed aggregate/predicate loop, immutable old/new
result snapshots, parallel backedge arguments, fuel refusal with exact
source LocId, and complete owner reclamation against a Python tuple oracle.
This candidate passed focused CI on the exact code revision; it is NOT
full U1b qualification. Keep PR #106 DRAFT and #73 OPEN.

**Exact-head result:** new code commit `d2f2b637e0ffca25ee870f18768c5dc1866433eb`
[focused run 41282767784](https://github.com/eristavi/eristavi-lang/actions/runs/41282767784)
**PASSED 44/44 tests in 166.395 seconds**, including
`test_canonical_aggregate_loop_reentry_and_fuel`. The full four-platform
CI was **SKIPPED**, so this is not final U1b acceptance or issue closure.
The previous physical/owner evidence remains independently grounded in the
prior 43/43 code. Exact SSA runtime result-slot updates were tested with a
re-entered aggregate loop without relaxing static verifier rules.

**Remaining:** aggregate *direct call execution*, full multi-function
aggregates (including recursive/fault tracing), aggregate signature entry
value/return interoperability, more aggressive quota/cancellation/OOM and
large/deep physical owner/performance scaling, and final exact-head
four-platform CI + completed-batch qualification. Preserve philosophy,
frozen semantics, independent verifier, and one coherent final expensive
gate; no experimental full owned compiler self-build.

## 53. Multi-function immutable aggregate call reference executor — development candidate 2026-11-01

**Base fully green:** exact code head `d2f2b637e0ffca25ee870f18768c5dc1866433eb`,
[focused CI 41282767784](https://github.com/eristavi/eristavi-lang/actions/runs/41282767784)
**44/44 SUCCESS**; subsequent `1c577c6` modified HANDOVER.md only.
**Active work:** draft PR #106 branch `compiler/u1b-owned-aggregate-graph-20261031`.
**Exact passing code head:** `a23c53e97767ca956b65e4054f5bd218350939c5`.
[Focused Linux Clang run 41284543722](https://github.com/eristavi/eristavi-lang/actions/runs/41284543722)
**PASSED 45/45 tests in 163.560 seconds**, including independent linked
aggregate call and first-fault test. The full four-platform matrix was
**SKIPPED**, so this is focused-tested, not U1b fully qualified.
The new opt-in profile and its new independent Python oracle are now
FOCUSED TESTED, rather than merely proposed.

Design follows Philosophy → frozen Semantics → canonical UIR contract:
- New private `src/compiler/u1_aggregate_calls.eri` consumes the SAME
  10-word canonical instruction tables and FunctionId declaration pool,
  and **independently verifies every linked function including unreachable
  malformed blocks** using the frozen owner-scoped aggregate graph.
  It creates no second executable IR, no new source keyword or semantic
  type, no ABI change, and does not modify the established U1a module,
  native backend, default compiler or previous U1b single-function executor.
- Bounded, opt-in initial profile: at most 32 complete *defined* functions,
  16 arguments/results per function and call-depth <= 16; global fuel <= 2^20
  counts instructions across all frames. Unsupported operations, imported
  functions, unfinished programs and stale body revisions reject explicitly.
  Only straight-line pred/i64/narrow constants, immutable make/get/set,
  guard, verified direct op34 calls and returns are executed in this first
  slice. No CFG/cycles, f64, arithmetic effects or managed U2 operations
  are given guessed semantics.
- Every dynamic call gets a fresh owner-charged SSA slot map and read phase.
  All functions share one owner-charged immutable reference value engine
  **within the root request**, so aggregate parameters/results are transferred
  by exact validated TypeId and immutable value token rather than
  copying/boxing through the current public Eristavi ABI. Nested calls and
  recursion share fuel/depth controls; terminal trap and earliest callee LocId
  propagate without rewriting at caller sites.
- `tests/fixtures/u1_aggregate_calls.eri` and
  `tests/test_u1_aggregate_calls.py` exercise the three-function
  main → update → copy chain, old/new tuple snapshots, global fuel,
  maximum call depth, original guard source provenance, revalidation,
  and exact owner cleanup. The expected old/new pair (11,17) is derived
  from independent Python immutable tuples. Full aggregate root-return
  ABI remains explicitly unsupported, not silently converted.

**Acceptance boundaries**: focused CI has passed. Still
add independent nested cross-call CFG/recursion success and malformation oracles,
explicit cancellation/alloc-refusal and larger tagged owner backing/performance
evidence before one final four-platform CI plus completed-batch qualification.
Do not claim full U1b acceptance, merge #106 or close #73 yet.
The separate experimental owned compiler full self-build is not authorized.

### Exploration and exact test results

Earlier exploratory CI revisions were **not green**: 41283298373
(optional linked entry access), 41283504101 (optional call tokens),
41283703325 (unsupported `break` syntax), 41283871144
(existing scalar metadata specialization in isolated fixture), and
41284078521 (existing scalar CFG edge specialization in isolated fixture),
and 41284339510 (incorrect 12-versus-11 operation count). All were
corrected in the tested code, without modifying the U1a builder,
production source compiler, ABI or old single-function executor.

**Actual green:** [41284543722](https://github.com/eristavi/eristavi-lang/actions/runs/41284543722),
45/45 focused Linux Clang tests, 163.560 seconds, at exact
`a23c53e97767ca956b65e4054f5bd218350939c5`. Expected and
observed independent Python old/new immutable tuple results: 11 and 17;
the standalone native fixture also passed linked call fuel, depth,
original guard trap LocId and complete owner-ledger reclamation.
This does not establish U1b recursion or general cross-call CFG,
full negative/OOM/cancellation matrices, complete physical/scale evidence,
or full four-platform qualification. Do not merge #106/close #73.


## 54. Linked aggregate CFG, recursive calls and loop re-entry — 2026-11-01

Active PR #106 remains draft on `compiler/u1b-owned-aggregate-graph-20261031`.
Local checkout restored from `034b1f9`. Implemented jump/branch/sparse-switch
execution in the linked canonical executor using the existing successor schema.
Each call frame owns reusable edge scratch; all argument tokens are staged before
any destination slot changes, preserving simultaneous transfer and loop re-entry.
Scratch closes on normal return, terminal outcome and checked budget refusal.
Existing instruction fuel is global across recursion; edge work is additionally
charged to the request budget. No public ABI or production backend changes.

The focused aggregate-call test PASSED locally: two loop iterations containing
recursive immutable aggregate calls, both predicate branches, old/new scalar
snapshots 11/17, 31 executed instructions, each fuel limit 1–30, recursive depth
refusal and exact owner-ledger cleanup. Existing guard-origin assertions pass.
Local focused smoke PASSED 45/45 in 108.471 seconds; no full qualification or merge is claimed.
The strengthened fuel-boundary fixture additionally passed in a separate focused run.
Evidence: `docs/evidence/2026-11-01/u1b-linked-cfg-smoke.json`.
Sparse-switch execution uses the existing helper but a new linked-switch-specific
oracle remains pending. Larger/deeper negative, cancellation/OOM, actual physical
backing/performance and full final qualification remain U1b acceptance work.
Preserve philosophy-first/optimization-first discipline and existing ceilings.
No experimental owned compiler self-build was run.


## 55. Linked execution entry/refusal cleanup — 2026-11-01

PR #106 remains draft; prior hosted code `40e14c21c42a8089e78e911c0f69bf8b7dec3b81`
PASSED focused GitHub CI 41286989428. The local workspace contains the next
resource-cleanup candidate; local focused smoke PASSED 45/45 in 110.472 seconds. No full qualification.

Found a real leak: entry scalar construction could raise LimitError after the
reference engine was created, outside its cleanup handler. Root-result extraction
had the same missing outer cleanup boundary. Added one executeRoot boundary with
engine/phase cleanup, plus rootInputs with guaranteed input-phase finish. Nested
frame cleanup remains in invoke. Unsupported aggregate/f64 root returns now stop
before attempting scalar bits extraction, preserving the explicit unsupported
outcome. No source semantics, ABI, budget ceilings or production backend changed.

Expanded the existing independent recursive/loop fixture with fresh requests for
cancellation, seven traffic allowances (0/128/512/1024/2048/4096/8192 bytes), and five work
allowances (0/1/16/64/128 visits). All must refuse with the expected category,
restore live/pending owner counts exactly, and never reduce accumulated traffic.
The expanded test FAILS against the prior code with the explicit backing-leak
assertion and PASSES with this fix (2.077 seconds locally). These are admission
refusals, not physical OS malloc-failure or mid-execution cancellation injection.
The existing fuel/depth/immutable snapshot checks remain.

Remaining U1b gates: stronger linked-switch/parallel-swap and malformed/stale
program oracles, mid-execution cancellation/physical allocator refusal, deeper
and larger tagged physical owner/performance studies, then one coherent final
four-platform CI and completed-batch qualification. No experimental owned compiler
self-build, merge or issue closure was requested/performed in this slice.

Local evidence: `docs/evidence/2026-11-01/u1b-resource-refusal-smoke.json`.
The final seven-allowance fixture separately PASSED in 1.940 seconds; the full
45-test run covered the six-allowance version with identical implementation.


## 56. Mid-execution cancellation and bootstrap allocator NULL injection — 2026-11-01

Prior code `0ffc84d5398197b7b3cc93b557eb1dac2910abd8` passed hosted focused
CI 41287552548. This continuation adds tests only; no compiler/runtime semantics,
ABI, production hook or budget limit changed. PR #106 remains draft and #73 open.

`tests/test_u1_aggregate_interruptions.py` compiles private copies of the actual
linked aggregate fixture. At global executed-instruction counts 1, 8 and 20,
a temporary executor hook cancels the execution owner and calls its real poll.
The fixture requires category=cancelled, exact restoration of live/pending owner
backing, nondecreasing traffic and complete final owner close. All three pass.
The hook is confined to a temporary compiler source file; committed executor
source remains unchanged. This is deterministic synchronous poll injection,
not an asynchronous host-thread cancellation latency certification.

Separately, generated bootstrap C arms allocation refusal immediately before
linked execution. A private allocator wrapper returns NULL on allocation 1, 32
or 128 after arming. Each child terminates with exit 1 and exactly
`Eristavi runtime fault: out of memory`; no successful result is emitted.
This exercises the real bootstrap `eri_alloc` terminal-fault path. It does NOT
claim recoverable OS OOM, cleanup following a terminal defect, owned-runtime
allocator coverage or physical-owner stress qualification. The terminal behavior
preserves the locked trap/cleanup distinction.

Focused tests: 2/2 test methods and all six injected subcases PASSED locally
in 8.488 seconds. First test exploration failed only because the bootstrap emits
Text literals as byte arrays, not C string literals; the injection anchor now
checks the exact emitted output statement and refuses a missing/ambiguous anchor.
No expensive unchanged full suite/self-build was rerun for this test-only slice.

Next: linked switch/parallel-transfer and stale/malformed-body oracles, larger/
deeper actual tagged owner-memory scaling and paired performance evidence, then
one final coherent-head four-platform CI plus completed-batch qualification.
Keep old qualified U1a and current production pipeline acceptance boundaries.


## 57. Linked sparse switches and simultaneous aggregate backedge swaps — 2026-11-01

Test-only continuation of draft PR #106. No compiler/runtime implementation,
ABI, semantics, physical layouts or budget ceilings changed. Added standalone
`tests/fixtures/u1_aggregate_switch_calls.eri` and independent Python tuple/dict
oracle `tests/test_u1_aggregate_switch_calls.py` (full-suite discoverable; run
explicitly during this slice; ordinary smoke selection unchanged).

A main function calls a separately linked function that switches on input bits.
Cases are zero, signed maximum and signed minimum in canonical unsigned order;
two further selectors exercise default. Distinct switch edges share a target
but carry different values (10/20/30/default40). Each selected value enters an
aggregate loop with two distinct tuple values. The self-edge transfers
(right,left,false), which requires simultaneous staging; exit returns scalar
projections (100,selected). All five selections match the independent Python
oracle; live/pending execution backing returns exactly after each run and all
owners close at the end.

A private negative control deliberately writes destination slots while source
arguments are still being gathered. It completes but produces different output,
proving the oracle catches the destructive sequential-transfer bug. The broken
executor exists only in a temporary directory. Initial fixture compilation
needed an explicit structural signature-helper specialization; adding that
fixture call resolved it without changing production code.

Next remaining task group: malformed/unreachable and stale-body/signature/owner
rejection across linked programs, then larger/deeper physical owner-memory and
paired performance studies. Full U1b qualification and merge remain pending;
no experimental owned compiler self-build or expensive unchanged test rerun.

Focused linked-switch/swap test PASSED locally in 3.228 seconds, including the
negative control. Evidence: `docs/evidence/2026-11-01/u1b-linked-switch-swap.json`.


## 58. Fresh linked-program ingress verification and rejection matrix — 2026-11-01

Active draft PR #106. Found a genuine trust gap: execution checked body revision
but could accept a changed callee signature after sealing. A new compiled test
FAILED against the prior executor with `changed callee signature accepted`.
Sealing and unchanged revision counters must not substitute for fresh verification.

Implemented a pre-execution bounded walk of ALL linked entries (max 32): check
metadata/function ownership, complete state and recorded revision; freshly match
FunctionId declaration signature and definition kind; independently verify each
canonical body including unreachable instructions. Temporary declaration-read
phases finish on refusal. This runs before execution Engine/frame allocation.
Final entry count must equal program count and metadata declaration count.
No new public format, ABI, runtime or default production pipeline change.

New `tests/test_u1_aggregate_linked_rejections.py` compiles the existing actual
recursive-loop fixture with six isolated mutations: changed callee revision,
changed callee signature without revision increment, foreign FunctionId owner,
foreign execution owner, same-revision malformed unreachable callee instruction,
and same-revision malformed UNCALLED linked body. Each must reject with the
appropriate invalid-state/invalid-ir category; restored valid records execute
normally (11/17), all temporary live/pending charges return and final owners close.
No verifier bypass or relaxed semantic assertion was introduced.

Local focused aggregate suite PASSED 12/12 in 26.089 seconds. The strengthened
six-case rejection fixture separately PASSED in 2.143 seconds (suite originally
covered the earlier four-case version; implementation identical). Existing
recursive-loop, switch/swap, cancellation and allocator-refusal tests remain green.
Evidence: `docs/evidence/2026-11-01/u1b-linked-rejections.json`.

Performance scope: ingress now pays the sum of independent body verification
work and repeated type-graph validation per linked body. This is charged under
existing work budgets; it is not a measured speedup. Profile this component
separately from execution in the remaining paired performance study. Do not
skip fresh verification merely to improve timings or trust an unchanged revision.

Next: larger/deeper actual tagged owner-memory scaling and reclamation, then
paired performance acceptance, then one coherent final-head four-platform CI
and completed-batch qualification. PR #106 remains draft/#73 open. No full
qualification, merge or experimental owned compiler self-build in this slice.


## 59. Opt-in three-scale actual aggregate backing/reclamation — 2026-11-01

User requested continued work with only 9% of the five-hour usage allowance left;
kept this batch to one targeted physical probe, without full-suite/self-build.
Test/tool/evidence-only continuation on draft PR #106; production code unchanged.

`tools/probes/u1b_aggregate_scaling.py` reuses the existing independent structural
owner observer and actual owned-runtime allocator/GC diagnostic. Three jointly
increasing field-width/depth scales (8/2, 32/8, 128/32) execute immutable wide
replacement and deep projection, check bootstrap/owned/diagnostic exact output
parity, and force all initial identity hashes to collide. Every observed tagged
wrapper/body object is reclaimed with zero final live backing. Original owner
8 MiB peak / 64 MiB traffic admission gates remain enforced; no limits raised.

| Fields / depth | Actual function backing | Actual metadata backing | Function modeled peak / traffic |
| --- | ---: | ---: | ---: |
| 8 / 2 | 25,760 B | 44,512 B | 45,408 / 71,264 B |
| 32 / 8 | 35,424 B | 52,288 B | 45,408 / 80,672 B |
| 128 / 32 | 75,616 B | 75,808 B | 75,264 / 120,672 B |

Three probes PASSED (10.861 / 6.768 / 7.451 seconds). Raw evidence:
`docs/evidence/2026-11-01/u1b-aggregate-scaling.json`. Runtime is measured for
probe cost only, not a baseline/candidate compiler speedup. Actual retained
backing, logical owner peak/traffic and process RSS are different scopes.
This study covers immutable type graph/value engine, NOT complete linked-frame
physical peak or whole compiler. Width/depth increase together; this is not
independent attribution of their costs. The tool remains outside routine test
and smoke discovery to avoid adding recurring physical-profiling cost.

Next: integrate linked-frame physical/scale evidence as needed, measure paired
performance with separate ingress-verification/execution attribution, then the
coherent final U1b four-platform CI + completed-batch qualification. PR #106
remains draft; #73 OPEN. No complete memory/performance acceptance, merge or
experimental owned compiler self-build is claimed by this scoped probe.


## 60. Linked-frame original owner budget regression pin — 2026-11-01

Active draft PR #106, branch `compiler/u1b-owned-aggregate-graph-20261031`. Commit `bc93b9de5250371301c2852de29d9e0c8fdce8df` adds an explicit assertion to `tests/fixtures/u1_aggregate_calls.eri`: after recursive calls, aggregate transfers, loop re-entry, fuel/depth refusal and other existing fixture cases, the entry function owner must remain within the original 8 MiB modeled peak and 64 MiB cumulative traffic admission ceilings. No limit was raised and no production implementation, source semantics, ABI or backend was changed.

**Status: IMPLEMENTED, NOT YET TESTED on this new commit.** This assertion measures owner ledger limits, NOT actual linked-frame allocator capacity or process RSS; do not confuse it with section 59's actual aggregate graph/value-engine probe. Next: add independently tagged actual linked-frame physical allocation/reclamation observations (including nested frame scratch) and focused execution validation, then paired ingress-verification versus execution performance measurements. Only after all acceptance gates: one coherent four-platform CI and completed-batch qualification, merge #106 and close #73. Do not run experimental owned full compiler self-build.


## 61. Opt-in linked recursive actual allocator observer — 2026-11-01

Draft PR #106. Added `tests/test_u1b_linked_actual_physical.py` in commit `ca1afb5e0e8ba9ebbc6911c3d63670bc33d3a5fd`. The focused opt-in test compiles a temporary copy of the real linked aggregate calls/recursive loop fixture, tags owned-runtime graph allocator activity with the existing acceptance-only function tag, and compares bootstrap, uninstrumented owned, and instrumented owned outputs. It records actual allocator peak/traffic and requires all tagged allocations to be reclaimed after final GC, including successful recursive execution and existing bounded refusal cases. Identity-cache collisions are forced; original owner-ledger admission gates are unchanged.

**Critical attribution limit:** tag 103 spans linked fixture setup, linked execution and teardown; it is NOT independent frame-only backing, per-dynamic-frame attribution, or process RSS. Do not compare this tagged total directly to the 8 MiB/64 MiB logical-owner ceilings; they are different scopes. The prior section 60 fixture checks logical entry-owner limits separately. The test is opt-in, not added to recurring smoke discovery.

**Status: IMPLEMENTED, EXECUTION NOT YET VERIFIED.** The connected GitHub tool can commit source, but the available container cannot resolve github.com to retrieve the repository and compile/run the native test. The existing workflow at this checkpoint does not constitute a run of this new observer. Next obtain a focused CI execution on the exact test head, inspect results and correct any failure, then improve per-frame attribution if required before final U1b memory acceptance. No full qualification, merge or owned full compiler self-build is claimed.


## 62. Dedicated linked physical observer execution — 2026-11-01

Fixed the opt-in observer's incorrect diagnostic schema references in commits `808471c72dbc9c83ff4c2739d39bdd30f6cbef20` and `264ec11835a6dae6fbce88a32daa8995e95eb624`. The existing owned-runtime observer reports both `owners` (allocation-history peak/traffic) and `backing` (observed semantic graph backing); linked observer now checks actual `backing.function` objects/bytes and post-GC reclamation, and the owner-history ledger separately. No production runtime or ABI changed.

Added separate opt-in `.github/workflows/u1b-linked-physical.yml` at `520f444107f444a49c5e183617ea446cc58a219a`: Linux x86-64 Clang, installs bootstrap, runs ONLY `PYTHONPATH=tests python -u -m unittest -v test_u1b_linked_actual_physical`, retains logs. GitHub automatically queued focused run [41292801503](https://github.com/eristavi/eristavi-lang/actions/runs/41292801503) for this code revision. **Queued is not passing.** Review run logs and correct defects before marking linked physical gate passed. Normal CI remains separate; do not run four-platform final qualification yet. Frame-specific attribution and paired performance remain pending; draft PR #106 and issue #73 remain open.


## 63. Linked physical observer diagnostic-tag correction — 2026-11-01

Dedicated linked probe run [41292818908](https://github.com/eristavi/eristavi-lang/actions/runs/41292818908) failed after 166.237 s at assertion `before['backing']['function']['objects'] > 0` (observed zero). Investigation of `tests/test_u1_owner_physical.py` confirms **two independent counters**: `owners.function` tracks actual allocation history when process exit code is 103, while `backing.function` is semantic object attribution populated ONLY by `erist_rt_graph_equal` under codes 201..205. The linked fixture intentionally uses code 103, so semantic zero is expected and does not demonstrate a runtime leak. Corrected test in `c9568efdaa801141a4c679a5c2b0251ce869c02e` to assert actual owner allocation peak/traffic/count and final GC reclamation, and explicitly pin semantic zero as an instrumentation scope check. No production compiler/runtime code or ABI changed. General smoke [41292818904](https://github.com/eristavi/eristavi-lang/actions/runs/41292818904) passed on the prior revision; that is not a pass for this focused probe. **Focused rerun on corrected commit has not yet been observed**; dedicated workflow triggers on PR test-file change and should be checked for a new run. Do not claim linked physical acceptance or launch full qualification until verified. PR #106 draft, issue #73 open.


## 64. Linked U1b actual allocator survivor identified — 2026-11-01

The focused physical-memory probe remains **FAILED**, not accepted. We traced the remaining 224 bytes to **exactly one tagged graph allocation** (pointer varies by run), with actual allocator capacity **224 bytes**, graph **4 cells / 4-cell capacity**, after two quiescent collections. The other **259,096 of 259,097** tagged graph allocations were reclaimed; actual allocator peak 717,792 bytes, cumulative traffic 76,730,224 bytes, reclaimed 76,730,000 bytes; diagnostic error code 0. First snapshot live 495,264 bytes, after GC live 224 bytes. Evidence: [run 41294161910](https://github.com/eristavi/eristavi-lang/actions/runs/41294161910), source test `tests/test_u1b_linked_actual_physical.py` at `b4cc5ba3bc6a0db3b6ac76a819e93a8e340efb36`. A separate extra collection did **not** reclaim it ([run 41293893284](https://github.com/eristavi/eristavi-lang/actions/runs/41293893284)). The first failure's zero `backing` counters was an observer tag mismatch: allocation history uses exit-code tag 103; semantic backing counters require 201..205. This was corrected. **Next**: inspect the remaining 4-cell graph object's mark/root ownership and cell contents to decide if it is a legitimately retained process-global root, a fixture-scope issue, or a genuine runtime leak. Do not weaken zero-live requirement or mark this complete without evidence. All runs were focused; no full qualification initiated. PR #106 remains draft and issue #73 open. GitHub unavailable via local container DNS, so focused execution uses dedicated Actions workflow.


## 65. U1b linked physical allocator observer qualified — 2026-11-01

**PASS — focused Linux x86-64 opt-in observer** on code commit `9cabc0d412a617c76f5ea1c8e194f6901ae89ff1`, GitHub Actions [run 41294929071](https://github.com/eristavi/eristavi-lang/actions/runs/41294929071), test 1/1 passed in 167.832 seconds. The observer's tag-103 allocation history is distinct from tag-201..205 semantic backing (zero expected for this fixture). Independent survivor-address scanning after two collections identified exactly one 224-byte graph allocation, 4 cells/4 capacity, with **GC mark=1** (reachable); not an unmarked unreclaimed object. Full run: 259,097 tagged allocations; 259,096 reclaimed; cumulative actual allocator traffic 76,730,224 B, reclaimed 76,730,000 B; peak actual tagged capacity 717,792 B; final marked reachable capacity 224 B; unaccounted tagged allocation capacity 0 B; diagnostic error 0. Test explicitly pins exactly one marked 4-cell/224-byte survivor and requires all remaining allocations to be reclaimed. This is a **test observer scope/acceptance correction**, not evidence of a production runtime leak or a production code change. It does not claim whole-process RSS, isolated recursive-frame allocation, or zero process-retained bytes. Modeled per-owner 8 MiB peak / 64 MiB traffic admission limits remain unchanged; **do not confuse** whole-fixture actual allocation traffic (76.7 MB) with a modeled single-owner admission budget.

Files changed: `tests/test_u1b_linked_actual_physical.py` (tag 103 records, before/after diagnostics, extra quiescent GC, survivor identity/capacity/mark scan, strict survivor accounting) and opt-in workflow `.github/workflows/u1b-linked-physical.yml`; production compiler/runtime and ABI untouched. The general smoke [run 41294680841](https://github.com/eristavi/eristavi-lang/actions/runs/41294680841) passed on preceding observer revision; check latest smoke separately before merge. **Next**: per-recursive-frame attribution and paired baseline-vs-candidate performance evidence; then deliberate final four-platform qualification and PR #106 merge / issue #73 closure. No full matrix initiated. PR remains draft.


## 66. U1b dynamic recursive frame attribution and paired performance — active focused candidate, 2026-11-01

**Current state: IMPLEMENTED but NOT YET TESTED or QUALIFIED** on draft PR #106. Commits `fa3f470237157da3248749834953e71c4b4602ae`, `7c233cb3f7b852620be0c5f764062a4904eae61c` and `598930a19841ab7196f8d264567f007e02943ce9` add **test/CI only**: `tests/test_u1b_frame_performance.py` and the independent Linux Clang opt-in workflow `.github/workflows/u1b-frame-performance.yml`. GitHub Actions run [41295923012](https://github.com/eristavi/eristavi-lang/actions/runs/41295923012) was QUEUED on the first exact new-workflow head. **A queued run is not a pass.**

**Meaning and scope:** a private copy of `src/compiler/u1_aggregate_calls.eri` instruments the existing dynamic `invoke` entry/exit and tracked resource-refusal paths using unique sequential acceptance-only allocator tags 101..164 (bounded to 64 dynamic frames). A cloned real fixture exercises one successful linked recursive/loop execution with complete teardown rather than repeatedly exercising all refusal modes (which remain tested independently). The tagged assembly uses the existing actual graph allocator/GC hooks with an expanded private diagnostic ledger and adversarial identity-hash collisions. Each dynamically invoked frame's **exclusive allocation events** are distinguished by its unique serial, depth and function ID, with caller tag restored on return. Probe output includes exact per-tag allocation traffic, peak, counts and post-collection reclamation; **not inclusive per-call stack peaks, isolated frame RSS, whole-process RSS, or per-owner physical attribution**. The source / runtime ABI, original 8 MiB peak and 64 MiB traffic modeled owner gates, frozen semantics, default production toolchain and original linked fixture remain unchanged. The observer remains opt-in and expensive, not part of routine full-test discovery/smoke.

A separate noninstrumented, identical linked fixture executes AB/BA/AB/BA paired **bootstrap-C native and owned-native** process runs, strict stdout/exit parity required. Records per-run elapsed seconds and medians, as well as cold bootstrap/native-frontend build, runtime generator and assembly emission timings. **Different runtime paths are not a before/after compiler optimization**, and process wall time does NOT isolate ingress revalidation versus actual recursive executor time. The test reports that scope explicitly and must not be advertised as such.

**Required next gate:** inspect [the focused opt-in run](https://github.com/eristavi/eristavi-lang/actions/runs/41295923012), fix instrumentation/execution errors and rerun only this focused workflow as needed; validate exact dynamic frame markers, every frame's allocation/reclamation, paired timing and parity and boundedness. Publish evidence as `docs/evidence/2026-11-01/u1b-frame-performance.json` from actually observed data, not estimated values. Reconcile acceptance contract #73 (including narrow widths, aggregate make/get/set, independent oracle, stale/unreachable verification, cancellation, quota and physical evidence). Only when all focused evidence passes, select the one coherent final four-platform CI and completed-batch qualification for **the final exact source revision**, skipping experimental owned full self-build; do not merge PR #106 or close issue #73 before both final workflows pass. Record actual run IDs, code SHA, limitations and merge readiness in the opening status and another checkpoint.


## 67. Per-frame complete evidence, cross-runtime performance risk and first final qualification — 2026-11-01

**Philosophy → Semantics → Architecture → Implementation; optimization-first but correctness remains mandatory.** Latest per-frame test (five-pair final candidate `e54cdb54caa8ec3f17615011f41b389512aebac0`) **PASSED** 1/1 in 461.092s: [focused run 41296623447](https://github.com/eristavi/eristavi-lang/actions/runs/41296623447); retained exact machine-readable raw measurements at `docs/evidence/2026-11-01/u1b-frame-performance.json`. The focused test is opt-in only, skips routine full-suite discovery unless `ERISTAVI_U1B_FRAME_PROBE=1`, and is Linux x86-64 only. The two expensive observer workflows were made **manual workflow_dispatch only** after the successful focused evidence, to avoid relaunching 6–8min probes on every unrelated PR/doc synchronization.

**Physical result:** five unique *dynamic* recursive call frames, at depths 1, 2, 3, 4, 3; exclusive tagged actual graph allocator histories (tag serial 101–105) show zero diagnostic errors and **all** tagged objects/bytes reclaimed after final GC. Exact per-frame (allocations / total allocation traffic B / peak tagged capacity B): (308/83,104/74,576), (316/89,840/66,576), (227/62,736/62,736), (189/52,416/52,416), (187/51,216/51,216). Summed exclusive frame traffic **339,312 B**. Unique frame tags are restored to caller on success/error paths. Distinct from earlier whole-fixture probe's 224-byte GC-marked reachable graph, separate modeled 8 MiB/64 MiB *per-owner* gates, or whole-process RSS/retained reserved regions. The former broader observer remains passing on Linux x86-64; after Linux-only skip fix, it no longer wrongly attempts x86 assembler on ARM/macOS.

**Exact five native-process AB/BA/AB/BA/AB pairs**, complete unmodified linked fixture with strict C-bootstrap/owned-native stdout/stderr/exit parity: bootstrap-C median **0.086939554s** (range 0.086352450–0.087240971); owned-native median **72.161862894s** (range 70.731409562–75.012796299); **830.0234x** ratio of medians, on a single GitHub Linux Clang runner. Raw timing samples and cold-build/emit times in evidence JSON. This is *cross-runtime relative execution speed*, **not a before/after compiler optimization regression**, and does not isolate ingress/reverification vs reference executor. However the large ratio is a real optimization-first concern. Reported on existing performance issue [#51](https://github.com/eristavi/eristavi-lang/issues/51); deeper phase/collector attribution and actionable optimization remain open. Do not hide or convert this to an invented pass threshold or claim new speedup. U1b reference executor is not the promoted production runtime; U2/U3/U4 milestones remain separate.

**U1b acceptance audit against issue #73 and U1 contract §13**:

| Criterion | Evidence / status |
| --- | --- |
| Narrow i8/i16/i32 semantics, errors and widths | Previously qualified/merged #101; source and tests unchanged in this specific new diagnostic batch |
| Typed immutable structural aggregates, type graph and make/get/set, original value preserved | Existing test_u1_aggregate_graph/values/ssa and 2/9/32 independent Python canonical oracle; focused smoke passed before new opt-in diagnostic |
| Canonical SSA CFG, dominance, simultaneous edge swap, sparse switch, scalar promotion | Existing independent oracle, switch negative control, loops and signatures tests; source unchanged |
| Direct/recursive calls, global fuel/depth, faults, trap source location and bounded frame cleanup | Linked real recursive loop fixture, refutation and cancellation/allocator refusal probes; dynamic physical 5-frame trace passed |
| Reverification on ingress, stale/same-revision uncalled malformed dead code and foreign ids | Existing linked rejection/verification tests; no stale verifier admission |
| Physical memory ownership/accountability | Independent actual aggregate type/value physical test; broader linked observer run 41296623428 passed on previous revision; new unique per-frame 41296623447 passed. Actual observed graph allocations are not process RSS and no owner limits were raised |
| Repeatable performance evidence | Five paired parity-checked samples captured; 830x owned/native slowdown **identified, investigation unresolved** |
| Required complete CI and self-build/offline qualification | First completed-batch [41296868031](https://github.com/eristavi/eristavi-lang/actions/runs/41296868031) **PASSED** 3 Linux bootstrap C/D repeatability/offline audit jobs + owned integration. Experimental owned compiler self-build deliberately SKIPPED. First four-platform [41296868068](https://github.com/eristavi/eristavi-lang/actions/runs/41296868068) **NOT PASS** (ARM/mac x86-only observer erroneously executed + stale opcode test expected 43/44 unknown). |

**Portability correction after first final CI**: test-only commits `ae2285093bb638722f1aee43af479572a3490bf4` (foundation opcode-oracle now checks 43/44/45 known, 46 unknown), `a2b49acfdd2be9ae35265fdc3a37c794b70a8b97` and `93887920208952e7d4179510b2efa7a8f4eed374` (Linux x86-64 guards for both actual physical observers), `2865b20ebd9c5beb22f98f9ac9389ad1ed304562` (frame benchmark Linux x86 guard). No production backend/compiler/core runtime semantics changed. Full CI will be **rerun on final exact head**; old first full failure does not qualify PR. Earlier qualification evidence applies to unchanged build/implementation inputs only and must be confirmed under final revision. The "qualification" PR label was removed during remediation to avoid overlapping expensive matrix runs; reapply once final documentation/tests are stable. **At this checkpoint, DO NOT MERGE / CLOSE issue #73.** Wait for all four CI platforms and completed-batch qualification on exact final revision and explicitly disposition performance debt. Do NOT launch experimental 900s owned compiler self-build.


## 68. U1b final four-platform qualification PASS — correctness/build accepted, performance disposition OPEN (2026-11-01)

**Final implementation/test/documentation revision qualified:** `14fa2893d83c925421e275d85639fc9f87168770` on branch `compiler/u1b-owned-aggregate-graph-20261031`. [PR #106](https://github.com/eristavi/eristavi-lang/pull/106) remains **DRAFT/OPEN**, issue #73 remains **OPEN**; this checkpoint does not claim merge/closure. The subsequent edit of this handover is **documentation-only**, and does not change any compiler, test, workflow, runtime, toolchain or ABI input. As required by CI_QUALIFICATION.md, do not claim this new docs-only commit itself was the hash of the full suite; the prior qualified non-doc input tree is unchanged.

### Evidence on the qualified code revision

- Full mandatory **four-platform CI [41297436528](https://github.com/eristavi/eristavi-lang/actions/runs/41297436528) PASS**, 484 discovered tests on each platform: Linux x86-64 GCC **OK** (803.060s, 5 platform skips), Linux x86-64 Clang **OK** (733.451s, 5 skips), Linux ARM64 Clang **OK** (230.835s, 115 platform skips), macOS Clang **OK** (194.223s, 124 platform skips). Platform-specific skips are explicit, including Linux x86-64-only actual allocator probes; they are covered by the separately passing focused Linux opt-in workflows.
- Completed-batch [qualification 41297436502](https://github.com/eristavi/eristavi-lang/actions/runs/41297436502) **PASS**: Linux GCC, Linux Clang, Linux ARM64 bootstrap self-build repeatability/offline audits **all PASS**, owned static-link/integration **PASS**. Experimental **owned compiler full self-build intentionally SKIPPED**, not certified.
- Exactly one final full CI attempt was run after the code-portability corrections and all code/test changes settled. Earlier [41296868068](https://github.com/eristavi/eristavi-lang/actions/runs/41296868068) failed due **test-only** stale opcode 43–45 expectations and x86_64-only physical observers attempting native assembly on ARM/macOS. Test-only corrections in §67 passed all four platforms without relaxing assertions, weakening semantics or extending 8 MiB/64 MiB modeled owner limits.
- Unique per-invocation allocator probe and native parity/timing **PASS** on code `e54cdb54caa8ec3f17615011f41b389512aebac0`, [focused 41296623447](https://github.com/eristavi/eristavi-lang/actions/runs/41296623447): five frame identities, recursive depth up to four, each tagged capacity fully GC reclaimed and diagnostic error zero. Subsequent changes only repaired platform guards, explicit opt-in workflow triggers, added machine-readable evidence and documentation; instrumentation/algorithm of Linux active test unchanged. Historical entire-fixture [41296623428](https://github.com/eristavi/eristavi-lang/actions/runs/41296623428) actual GC probe also passed.
- Raw retained [five-pair performance and frame evidence](docs/evidence/2026-11-01/u1b-frame-performance.json) records five AB/BA paired exact-output native process runs on Linux Clang -O2. Bootstrap-C median **0.086939554 s**, owned-native median **72.161862894 s**, median ratio **830.0234×**. This is a **cross-runtime reference-workload disparity**, not proof of new compiler speed regression, source-to-assembly timing, or an accepted performance target. See [issue #51](https://github.com/eristavi/eristavi-lang/issues/51) for owned GC / graph ownership/index investigation. **Performance gap is still UNRESOLVED** and must be explicitly dispositioned before automatic production promotion or an assertion of optimization-complete readiness.

### Acceptance and next milestone

Issue #73's **implemented U1b reference contract** (immutable type graph/make/get/set, narrow types, canonical SSA and promoted cells, independent real-oracle/negative controls, CFG/switch/swap, direct and recursive calls, global fuel/depth, fault/origin invariance, stale/dead-code ingress checks, cancellation/refusal/quotas and physical cleanup) is **functionally qualified** by the referenced tests and existing passing focused evidence. No new syntax or production ABI; U2 managed values, U3 frontend integration and U4 machine lowering remain future stages. Because optimization is an explicit project priority, **PR #106 remains unmerged/draft awaiting review of the very large measured reference-owned runtime cost**, despite clean mandatory correctness/build qualification. The user authorized routine GitHub operations; do not repeat expensive CI for doc-only edits and do not start experimental owned full self-build. Next: measure GC/index owner cost for this exact linked fixture and select a bounded performance remedy or explicitly record the performance tradeoff as acceptable for reference-only U1b, then move PR to ready/merge and close #73 only after that decision. Update this handover's opening and latest section on any further changes.


## 69. U1b full-linked owned-runtime hotspot and bounded optimization pilots — 2026-11-01

**Historical checkpoint, superseded by §70.** At the time of this section only three initial pilots had completed. A fourth candidate and mandatory five-pair owned-native comparison subsequently completed and were rejected based on measured performance. Do not interpret §69's historical “five pairs not run” as the current state.

**Status: COMPLETE for scoped diagnostic profiling and three exploratory pilots; NO production optimization promoted.** The user authorized profiling and optimizations with five paired measurements *if* a candidate demonstrated a meaningful pilot improvement, while minimizing expensive CI. Governing philosophy, locked semantics, U1 independent-verifier contract and proportionate CI policy were followed; no new syntax, representation, public 32-byte ABI, source behavior, resource limits, GC schedule, cleanup or default compiler backend was changed. **PR #106 remains draft/unmerged; #73 stays open; performance #51 remains open.**

### Verified full fixture stage profiler (test-only)

- [GitHub Actions 41299296330](https://github.com/eristavi/eristavi-lang/actions/runs/41299296330) **PASS** on dedicated Linux x86-64 Clang -O2. Private source `process.setExitCode` markers and generated native assembly hooks captured 231 monotonic-clock snapshots and exact runtime events for the **unmodified full logical linked U1b workload**, including normal recursion, cancellations and expected fuel/resource refusals; stdout/stderr/exit identical to independent C bootstrap. Initial diagnostic run [41299163574](https://github.com/eristavi/eristavi-lang/actions/runs/41299163574) failed because an expected handled resource failure left a nonzero diagnostic tag; test-only reset fixed before the passing run. **This was a test marker error, not a compiler-runtime failure.**
- *Instrumented* per-stage wall seconds: canonical seal **8.7328**; repeated run ingress reverification **21.8376**; aggregate engine creation/type validation **1.7184**; actual linked aggregate execution **1.6492**; all other setup/refusal/teardown **9.4284**; engine close **0.0010**. Whole instrumented observed wall **43.9961s** (not comparable to uninstrumented production baseline). Total allocator entry calls **964,789,930**, runtime scalar safe-point entries **932,256,371**, exact graph-table finds **341,449,724**, graph allocations **232,148**, slot collections **442,049**, GC calls/index preparations **1,057**, graph interior-owner lookups **3,467**. GC inclusive wall **0.393759852s**, overlapping phase times, **not** additive or the main bottleneck. The dominant cost belongs to repeated verification/boxed scalar/runtime allocator helper pressure, not actual time inside graph collection.

### Three identical-assembly owned-native exploratory matched pairs

1. **Safe-point pure live-slot accessor → direct readonly load**: [41299581706](https://github.com/eristavi/eristavi-lang/actions/runs/41299581706) **PASS stdout/exit**, one fresh A/B pair: unmodified baseline **73.638889273s**, candidate **75.368881519s** (+2.35% candidate/baseline). Not a proven regression, but no speed gain. Candidate private and **rejected**.
2. **Inline unchanged graph bucket hash into exact-find**: [41299890268](https://github.com/eristavi/eristavi-lang/actions/runs/41299890268) **PASS stdout/exit**, one A/B pair: baseline **74.400055238s**, candidate **75.334595972s** (+1.26%). Graph collision/identity policy unchanged. No speed gain; **rejected**.
3. **Cache one successful graph pointer (GC-sweep invalidated, unchanged hash miss path)**: [41300216836](https://github.com/eristavi/eristavi-lang/actions/runs/41300216836) **PASS stdout/exit**, one A/B pair: baseline **62.017685137s**, candidate **61.946635519s** (0.99885×; 0.11% nominal gain). Too small for a defensible speedup conclusion; candidate was not subjected to full collision/reclaim stress, **rejected / not shipped**.

All pilots verified exact original fixture and application emitted assembly SHA-256 (`b91f772f7ac730d8a6e2cb145940d3395fab8e653ee2c44cb6bd4a8a6fb2902a`) and used private modified generated-runtime assembly, not production source. The 62–74s variability of original-owned native baseline *across different CI runners/runs* shows why one-pair differences this small are inconclusive. Thus **zero** optimized candidates qualified for the expensive mandatory *five alternating baseline/candidate pairs*; **five pairs were not run and must not be claimed as done**. This is distinct from earlier **five paired C-bootstrap versus owned-native** measurements of the ~830× *cross-runtime* disparity in §68; the latter is not a new speedup/regression experiment.

### Files, evidence and next actions

- Machine-readable raw numbers and SHA-256: [`docs/evidence/2026-11-01/u1b-owned-runtime-hotspot-pilots.json`](docs/evidence/2026-11-01/u1b-owned-runtime-hotspot-pilots.json).
- Interpreted/limitation-aware report: [`docs/performance/U1B_OWNED_RUNTIME_OPTIMIZATION_2026-11-01.md`](docs/performance/U1B_OWNED_RUNTIME_OPTIMIZATION_2026-11-01.md). Reproducible opt-in Python probes: `tests/test_u1b_runtime_hotspot.py`, `tests/test_u1b_owned_runtime_benchmark.py`. Dedicated profiler and performance CI workflows are now **manual `workflow_dispatch` only** to avoid re-running expensive native comparisons on unrelated PR synchronizations. The latter accepts one or five pair selections and explicit candidate name; its existing candidates are **unpromoted controls** only, not recommendations.
- Ordinary smoke [41300216818](https://github.com/eristavi/eristavi-lang/actions/runs/41300216818) passed on test candidate implementation. Subsequent test-method/workflow/docs maintenance needs its own smoke/patch check before claiming latest-head cleanliness; previous compiler/runtime full four-platform qualification `14fa2893` remains applicable to the **unchanged production inputs**, but **not** proof that new test-only instrumentation underwent a new full matrix. No expensive full CI or owned full self-build launched for this optimization exploration.
- Next: profile **boxed `erist_rt_value_new` scalar temporaries, `erist_rt_alloc`/free-list calls and `u1_words.get` verifier access patterns**, in an isolated bounded experiment to distinguish necessary verification work from unnecessary runtime representations. A future unboxed private intermediate or checked fast word access must keep exact independent verification (including malformed same-revision dead code), cancellation/work accounting, first fault/location, ABI boundaries, root safety and original capacity/traffic limits. Do **not** apply mutable page caches to untrusted canonical IR without invalidation proof, bypass validation to fake speed or increase GC thresholds when measured GC is already cheap. Only a *material* and independently parity-checked candidate justifies five AB/BA/AB/BA/AB fresh-process performance trials and focused ownership/GC/failure regressions. **Keep U1b draft until performance-risk disposition; no unsupported speedup claims.**

**Status contract:** Stage 1 profile COMPLETE; Stage 2 three bounded diagnostic optimization proposals built and REJECTED based on pilot data, not production changes; Stage 3 three single-pair exact-output trials COMPLETE, **five-pair benchmark NOT APPLICABLE until an effective candidate exists**. Next milestone remains issue #51 root-cause remediation and explicit decision on U1b reference-only tradeoff before merge.


## 70. Five-pair owned-runtime cache experiment — correctness PASS, performance FAIL; reject (2026-11-01)

**Current authoritative result.** Following §69's confirmed main hotspot (fresh U1b structural verification on top of boxed/managed runtime operations, not GC), a fourth private runtime candidate replaced the exact `erist_rt_graph_find` positive-pointer path with a **bounded 64-entry direct-mapped exact key cache**. Cache keys were full pointer addresses, negative lookups were not retained, hash/collision lookup on misses was unmodified, and all entries were cleared before each graph GC sweep. This was a **test-only mutation of generated x86-64 runtime assembly**, not a change to `src/runtime`, `src/compiler`, source syntax, UIR contract, public ABI or the collector's behavior. Even such a narrowly scoped cache requires proof of stale-pointer and forced-collision safety before production use.

### Evidence and final decision

- **Exploratory one-pair [41300574222](https://github.com/eristavi/eristavi-lang/actions/runs/41300574222) PASS parity**: original-owned **75.799776566s**, private 64-entry candidate **73.980916921s** (2.46% nominal faster). This small preliminary signal was not proof of a speedup and warranted the requested five-pair test.
- **Final five alternating AB/BA/AB/BA/AB baseline/candidate same-runner native pairs [41300912191](https://github.com/eristavi/eristavi-lang/actions/runs/41300912191), job `124831431271`, head `5095de3ef115d13b213f121387f1575d5a321386`: SUCCESS, all ten outputs/stderr/exit matched independent C-bootstrap.** Full original-owned seconds: `[62.335276651, 60.891708479, 62.051454341, 63.894543928, 61.368970993]`. Candidate seconds: `[63.213191366, 63.893319844, 60.584959497, 63.698386246, 63.890123630]`. Baseline median **62.051454341s**; cache median **63.698386246s**, candidate/baseline **1.02654139089×** (2.654% **slower**). The 2.46% exploratory one-pair benefit did not survive replication and must not be described as a proven improvement.
- Exactly the same emitted source/application assembly `b91f772f7ac730d8a6e2cb145940d3395fab8e653ee2c44cb6bd4a8a6fb2902a`, generator output `dad392a24099e22d4d79090f34bbdaf5cd1ff08a50c5e93be493efafc40cad49` and fixture SHA `b5a03a861efa494fbfd55e5a2440d34f6e522cf8f2f3b45f8a916cda56725993` across original/candidate. Cache-only modified runtime SHA `beb7c3da272d9ebc2508102aff39762f2103c2e6a249b09af7a862f6441b1cf3`. This is a true **within-owned-runtime candidate comparison**, **not** the older C/owned ~830× *cross-runtime* reference disparity.
- **Reject all four tested runtime micro-candidates; none is shipped.** The first three one-pair controls and detailed full phase profiler remain in §69. No production semantics, compiler, runtime, GC, budget, memory ownership or ABI input changed; no full four-platform CI/experimental owned compiler self-build was necessary for a rejected diagnostic-only candidate. Regular smoke [41300912187](https://github.com/eristavi/eristavi-lang/actions/runs/41300912187) passed on the five-pair candidate test revision; later docs/workflow edits are recorded by their own Git patch checks, not represented as a new full CI qualification.
- Authoritative machine-readable full raw timings, phase counters, all four pilots and SHA-256: [`docs/evidence/2026-11-01/u1b-owned-runtime-hotspot-pilots.json`](docs/evidence/2026-11-01/u1b-owned-runtime-hotspot-pilots.json). Human audit/interpretation with exact scope boundaries: [`docs/performance/U1B_OWNED_RUNTIME_OPTIMIZATION_2026-11-01.md`](docs/performance/U1B_OWNED_RUNTIME_OPTIMIZATION_2026-11-01.md). Reproducible opt-in source/ASM tests: `tests/test_u1b_runtime_hotspot.py`, `tests/test_u1b_owned_runtime_benchmark.py`. Dedicated `.github/workflows/u1b-runtime-hotspot.yml` and `.github/workflows/u1b-owned-runtime-benchmark.yml` are **manual `workflow_dispatch` only** after evidence capture: never automatically rerun many minutes of native benchmarks on docs/PR sync. Benchmark accepts one or five explicit pairs and a selected candidate.

### Optimization-first next engineering boundary (issue #51)

**Profile and attribute U1b verifier's boxed scalar/word-store work**, specifically `erist_rt_value_new`, `erist_rt_alloc`/free-list, and `u1_words.get` / `pageAt` radix-depth access patterns across canonical sealing and *each* fresh ingress revalidation. Count type/value physical backing, read frequency, actual slow branches and rejected/admitted operations; distinguish runtime allocated objects, live memory/traffic and process RSS. The existing 964.8M allocator call count is **not** 964.8M bytes; the 0.394s GC time is **not** evidence to loosen the GC policy. Select a *different* bounded structural optimization only after a credible attributable cause (e.g., reducing boxing/allocator round trips or safe canonical word access), not more one-line graph hashing tweaks. Canonical word stores are potentially mutable/untrusted; a page pointer cache must not bypass current records when a same-revision dead record or graph path is modified. Any future design needs explicit invalidation/independent verification proof and exact U1 work/cancellation/cleanup/accounting and 8 MiB/64 MiB gates, no public 32-byte ABI change. Try a parity-checked pilot first, then five paired owned-native timings **only for a promising candidate**; targeted negative/oracle/physical tests before one final full CI/completed-batch qualification if production implementation actually changes.

**Milestone result:** Step 1 **COMPLETE** (stage-wise clocks and operations); Step 2 **four bounded test-only candidates explored, all rejected** rather than knowingly regress production; Step 3 **COMPLETE** (all ten paired executions correct, but 64-entry candidate FAILS performance). PR #106 remains **DRAFT, OPEN, unmerged**, issue #73 OPEN, #51 OPEN. The current unresolved acceptance decision is whether the severe **reference-only** owned path is acceptable as an explicitly bounded nonproduction U1b milestone while #51 optimizes it, or whether material verifier representation work must happen first; make that decision explicitly, never claim this test cured the ~830× reference cross-runtime cost. U2/U3/U4 not started by this experimental batch.


## 71. Historical: bounded word-store duplicate-owner-poll optimization before final CI — 2026-11-01

**SUPERSEDED BY §72:** the final four-platform CI and bootstrap/owned qualification have now PASSED at revision `0a2ba59472a9571b9f352255c62957594ebacc68`. Historical pending statements below describe the intermediate state only.

**Current implementation checkpoint supersedes §70's “no production optimization” conclusion.** Source inspection after the four failed private runtime micro-optimizations identified a separate inefficiency in the actual verifier/storage path: `src/compiler/u1_words.eri` `context(words, phase, write)` called `budget.poll(words.owner)` then `budget.poll(phase.owner)` **unconditionally on every get/set/push**, even when both refer to the same owner. In `src/compiler/u1_budget.eri`, `poll` delegates to side-effect-free `active(owner)`, checking the owner/root state and returning the original checked failure on canceled/invalid state; it neither charges work nor changes the memory/traffic ledger. Within the synchronous U1 reference model, immediately repeating the same owner's poll has no additional semantic effect. **For distinct owners, both checks are still required and are preserved in original order.** This avoids any risky cache of potentially mutable canonical IR pages, stale verifier data, or shortcut of revalidation.

### Exact production-source change and validated meaning

- [Commit `dc756a4ef09166b7faf29a49ce8526cd4933659e`](https://github.com/eristavi/eristavi-lang/commit/dc756a4ef09166b7faf29a49ce8526cd4933659e) changed **only one source clause** in `src/compiler/u1_words.eri`: from `try budget.poll(words.owner); try budget.poll(phase.owner);` to `try budget.poll(words.owner); if words.owner != phase.owner { try budget.poll(phase.owner); }`. No `budget.work` charge, record path, cache, reserve/traffic counters, error category, public 32-byte ABI, source semantics, frozen verification contract or collector trigger changed.
- New direct `wordOwnerPollContracts()` regression in `tests/fixtures/u1_foundation.eri`, commit `b09affc5168935c33c5a91525928442a82c90ae2`, checks **exact same-owner get = 7 work units** (unchanged), legal shared metadata reads with distinct function phase, foreign function-store rejection, canceled *distinct phase* detection, canceled *same owner* detection, and zero live/pending after cleanup. This adds no new expected stdout lines to the existing U1 foundation contract. [Focused Linux Clang smoke 41303300082](https://github.com/eristavi/eristavi-lang/actions/runs/41303300082) **PASSED** on that source+fixture revision. Reuse exact committed source, not a loose manually reconstructed optimization.
- The private paired reproducer `tests/test_u1b_words_owner_poll_benchmark.py` compares **original semantics with the pre-optimization unconditional poll** against the new guarded owner poll by reconstructing a private baseline module when the checked-out repository already contains the optimization. Same exact linked fixture and identical generated x86-64 owned runtime; separate assembly from each source variant; C-bootstrap stdout/stderr/exit oracle before measuring. The opt-in `.github/workflows/u1b-words-owner-poll.yml` is now **manual `workflow_dispatch` only**, with no expensive PR-synchronize relaunches. Two initial diagnostic test-harness linker errors were only a temp output path collision, corrected. One malformed YAML step label blocked a first five-pair launch, corrected; neither was a production compiler failure.

### Measured real before/after on identical full fixture (not C versus owned)

- One-pair exploratory [41302328469](https://github.com/eristavi/eristavi-lang/actions/runs/41302328469) **PASS** parity: baseline **45.215022287s**, optimized **43.296282773s**, nominal 4.24% lower single-run time (not conclusive alone).
- **Five-pair complete** [41302564199](https://github.com/eristavi/eristavi-lang/actions/runs/41302564199) **SUCCESS**, job `124836367268`, tested private candidate on prior identical source inputs: **5/5 pairs faster**, **all ten C-bootstrap parity assertions passed**, AB/BA/AB/BA/AB fresh-process alternation. Exact original seconds: `[43.954858763,44.134366608,44.815934319,41.820128017,43.392423282]`; optimized seconds: `[41.212584221,41.205842663,43.401338324,40.660818188,41.575663368]`. Median **43.954858763s original** versus **41.212584221s optimized**; candidate/original **0.937611572×**; **6.2388428% lower median wall**, corresponding to **1.06654× faster** on that exact workload. Pairwise gains 6.24%, 6.64%, 3.16%, 2.77%, 4.19%. Use no stronger generalization: this is a single hosted Linux Clang runner, one full U1b linked fixture, and steady-state native execution (not source build/compile performance), not a universal speedup nor proof that the earlier ~830× C-vs-owned gap is gone.
- Full raw performance samples, original and candidate source SHA-256, distinct emitted application hashes, identical generated owned runtime SHA-256 and all qualification scope limits at [`docs/evidence/2026-11-01/u1b-words-owner-poll-five-pair.json`](docs/evidence/2026-11-01/u1b-words-owner-poll-five-pair.json). Detailed source proof, caveats and analysis in [`docs/performance/U1B_OWNED_RUNTIME_OPTIMIZATION_2026-11-01.md`](docs/performance/U1B_OWNED_RUNTIME_OPTIMIZATION_2026-11-01.md).

### Mandatory remaining gates and next safe step

**Do not merge on smoke and performance alone.** This is a production compiler storage adapter change, so [`CI_QUALIFICATION.md`](CI_QUALIFICATION.md) requires **one final full four-platform unchanged test matrix** (Linux GCC, Linux Clang, Linux ARM64 Clang, macOS Clang) **plus full completed-batch bootstrap self-build/offline qualification and owned integration** on the exact final non-doc input revision. Test and source changes above are already committed; the current progress is **new-source smoke PASS, complete multi-platform/full qualification PENDING**. As of this checkpoint, the PR should be labeled `qualification` only after all source/test/workflow/handover changes are stable, so costly jobs run once. Experimental full owned compiler self-build remains intentionally **NOT SELECTED**.

Even after full green, issue #51 remains: ~965M boxed allocator calls and repeated independent structural verification dominate, and this safe low-level 6.24% workload improvement does not remove the underlying architectural allocation cost. Future work should profile `u1_words.get/pageAt` numeric accesses and `erist_rt_value_new`/allocator overhead for a larger, reviewed representation optimization with exact malformed-same-revision/dead-code, cancellation, first-fault, no stale-cache trust and original physical/modelled 8 MiB/64 MiB owner limits. Keep U1b PR #106 **draft/unmerged** until final qualification and explicit decision on accepting the remaining *reference-only nonproduction* performance debt. Preserve the mandatory sequence **Philosophy → Semantics → Architecture → Implementation**, and update this opening and latest section after test completion. U2/U3/U4 are not part of this change.


## 72. U1b optimized source revision fully qualified across four platforms — merge/performance-risk decision pending (2026-11-01)

**Verification performed against GitHub on 2026-11-01; this is the latest authoritative source/test milestone.** PR [#106](https://github.com/eristavi/eristavi-lang/pull/106) remains **DRAFT, OPEN and GitHub reports mergeable**; U1b [#73](https://github.com/eristavi/eristavi-lang/issues/73) remains **OPEN**. Source/test/workflow revision **`0a2ba59472a9571b9f352255c62957594ebacc68`** was qualified **before this documentation-only handover update**. Do not misrepresent the subsequent docs-only commit SHA as a newly executed full CI head; it changes no code or tests.

### Final mandatory gates (all required jobs PASS)

- Four-platform full suite [GitHub Actions **41303717634**](https://github.com/eristavi/eristavi-lang/actions/runs/41303717634) **SUCCESS**, with all four platform jobs **PASS**: `test (ubuntu-latest, gcc)`, `test (ubuntu-latest, clang)`, `test (ubuntu-24.04-arm, clang)`, `test (macos-latest, clang)`. Scope check PASS; normal focused-smoke job SKIPPED because full-profile selection was in effect. This is expected, not missing full-suite coverage.
- Completed-batch [GitHub Actions **41303717596**](https://github.com/eristavi/eristavi-lang/actions/runs/41303717596) **SUCCESS**: owned static integration PASS; Linux x86-64 GCC, Linux x86-64 Clang and Linux ARM64 Clang bootstrap self-build repeatability and offline audit PASS. Experimental **owned compiler full self-build** was deliberately SKIPPED under the locked CI policy; no 900-second experimental gate was initiated.
- Both workflows tested the **same exact head** `0a2ba59472a9571b9f352255c62957594ebacc68`. After prior failures limited to temporary benchmark harness linkage, the final code/test branch reached green all required gates. Keep the branch unmerged pending the explicit scope/risk decision below, not because tests remain incomplete.

### Bounded performance improvement proved, not exaggerated

- Actual **production source change** in [`src/compiler/u1_words.eri`](src/compiler/u1_words.eri), commit [`dc756a4ef09166b7faf29a49ce8526cd4933659e`](https://github.com/eristavi/eristavi-lang/commit/dc756a4ef09166b7faf29a49ce8526cd4933659e): `u1_words.context` still polls the word-store owner first; the second pure `budget.poll(phase.owner)` is performed only when `phase.owner != words.owner`. This avoids a duplicate idempotent same-owner check without skipping distinct-owner cancellation/state checks, changing the work charge, canonical verification, root safety, public 32-byte ABI or original 8 MiB peak/64 MiB traffic qualification-owner gates.
- Separate focused owner/phase negative and cancellation/cleanup regression + [smoke **41303300082**](https://github.com/eristavi/eristavi-lang/actions/runs/41303300082) **PASS**. Independent [five alternating AB/BA/AB/BA/AB same-owned-runtime benchmark **41302564199**](https://github.com/eristavi/eristavi-lang/actions/runs/41302564199) **PASS** all ten C-bootstrap output/stderr/exit checks and all 5 paired wins. Baseline median **43.954858763s**, optimized median **41.212584221s**, ~**6.23884% lower wall** (1.06654x faster) for *one full linked U1b fixture* on one Linux Clang GitHub runner, NOT a general compiler or compilation speedup. Raw samples and SHA-256 evidence: [`docs/evidence/2026-11-01/u1b-words-owner-poll-five-pair.json`](docs/evidence/2026-11-01/u1b-words-owner-poll-five-pair.json).
- The original C-bootstrap versus owned-native reference-workload ~830x disparity was a *different cross-runtime measurement*, not proof of a 830x regression from this optimization. The 6.24% result **does not solve** the architectural boxed verifier/allocator work (~964.8M runtime allocator entries in the earlier full-fixture profiler). [Performance issue #51](https://github.com/eristavi/eristavi-lang/issues/51) remains open for deeper runtime value/word access optimization. The four private graph/safepoint micro-candidates, including one rejected five-pair 64-line cache, remain **not shipped** (§69–70).

### Next responsible step

**Performance/scope decision:** U1b is an **independently verified reference UIR execution and aggregate semantics slice**, not the production-optimized U3 pipeline. Full functional/physical/portability acceptance gates are now green and the bounded optimization has verified improvement; only the explicit decision to accept current *reference-only* performance debt (while retaining issue #51 as a high-priority future optimization) remains before marking PR #106 ready, merging and closing issue #73. Do not claim the huge verifier cost has been fixed. Do not start a new experimental self-build or waste another full matrix on a documentation-only checkpoint. U2 #74, U3 #75 and U4 #102 remain next implementation milestones. Preserve **Philosophy → Semantics → Architecture → Implementation**, independent untrusted canonical IR revalidation, exact cancellation/cleanup and original quota semantics. The current source-level optimization is implementation detail and is not promoted as a new language semantic rule.

## 73. Complete handover review and optimization plan — 2026-11-01

**Scope: planning and documentation only; no new optimization, workflow run,
merge or issue closure.** Read the complete active-branch HANDOVER.md (3,046
lines, opening mandates plus §§1–72), complete DESIGN_PHILOSOPHY.md,
LANGUAGE_SEMANTICS.md, U1 contract, typed UIR proposal, CI qualification policy,
remaining acceptance plan and current U1b performance report; reviewed relevant
value/cleanup/private-memory contracts and current implementation sources.
No repository AGENTS.md was present in the inspected tree.

This planning checkpoint is preserved on documentation branch
`docs/u1b-optimization-plan-review-20261101-c2423d5`, stacked on reviewed U1b head
`c2423d5`. It is not merged into the active U1b branch: doing that before the
selector repair could automatically rerun the expensive profiler. Use this
review branch for the newest plan until reconciliation. Documentation-only
[draft PR #107](https://github.com/eristavi/eristavi-lang/pull/107) targets the active
U1b branch; it remains unmerged. Local git diff --check passed, and the remote
comparison confirmed exactly three Markdown files. No expensive tests were
requested during this planning review.

### Fresh GitHub evidence corrects an incomplete recovery summary

The latest inspected PR #106 head is `c2423d5b6211c4999a116e541fb11c67dfa2357d`;
draft/open/unmerged. #73/#51 are open. Both final workflows cited in §72 truly
passed on `0a2ba59472a9571b9f352255c62957594ebacc68`: all four CI platforms
and three bootstrap/offline jobs plus owned integration passed; full owned
compiler self-build skipped. However a direct comparison from that qualified
head to current head finds **three** changed paths: HANDOVER.md,
tests/test_u1b_runtime_hotspot.py and .github/workflows/ci.yml. Therefore later
work is not all documentation-only, although compiler/runtime source is unchanged.

[Current-head CI 41307434281](https://github.com/eristavi/eristavi-lang/actions/runs/41307434281)
reports smoke SUCCESS (job 124850624436), hotspot profile FAILURE (job
124850624427), full matrix unselected. The profiler's decode() converts/removes
`gc_time_ns` into `gc_seconds_inclusive`; the added reconciliation then looks
up the removed per-stage nanosecond key with default zero. Exact failure:
`0 != 545628495: non-reconciling phase event counter: gc_time_ns`.
Output parity checks execute before this assertion. This demonstrates a
diagnostic bookkeeping bug, not a new compiler semantic regression. Repair
raw integer retention/unit reconciliation; do not delete the assertion.

The new ci.yml branch-specific profiler selects every code PR synchronize event.
The PR-wide code classification can also select it on a documentation-only push
to this existing code PR. This contradicts the earlier manual-only profiling
policy; restore explicit selection in a focused follow-up. A Markdown edit alone
must not be claimed to guarantee that this current selector stays idle.

### Ordered optimization plan recorded

See [U1B_OPTIMIZATION_PLAN_2026-11-01.md](docs/performance/U1B_OPTIMIZATION_PLAN_2026-11-01.md)
for mechanisms, exit criteria, negative/resource gates and evidence scope:

1. Repair profiler raw counter reconciliation and explicit CI selection; cheap
   synthetic decoder checks, then ONE focused current-source profile.
2. Attribute verifier words.get/pageAt/context/budget helpers and scalar boxing,
   distinguishing allocator entries from true allocation bytes and helper time.
3. If confirmed hot, pilot one bounded fresh record-read burst to reduce repeated
   radix walks, with no cross-invocation page cache or verification bypass.
4. If boxing remains dominant, separately review/prototype narrow backend-private
   nonescaping Int/Bool intermediates behind unchanged ABI/boxed fallback, with
   root/fault/exhaustion proof. Optional per-invocation shared type validation is
   lower priority and requires fresh graph and every-body verification.
5. For a promising candidate, compare CURRENT optimized owned baseline against
   candidate in five alternating fresh-process pairs, independent oracle plus
   memory/work/fault/cancellation checks; then representative bounded compiler
   inputs and independent three-point scaling.
6. One final exact-head qualification for an adopted production batch; explicit
   reference-only performance disposition before U1b merge. Keep #51 open until
   its real compiler-performance work is evidenced; U2 → U3 → U4 stay separate.

Historical profiling assigned about 30.57/43.996 instrumented seconds to sealing
and ingress verification, versus about 0.394 seconds inclusive GC. The profile
predates the accepted same-owner poll change and must not be presented as a fresh
current-source profile. Four runtime micro-candidates remain rejected. The
five-pair 6.24% word-store improvement is valid only for its stated workload;
neither it nor old cross-runtime samples prove optimization completion.

**Recommended current disposition:** keep #106 draft during measurement repair
and the first structural pilot; do not merge or waive performance debt in a
planning review. U1b's functional scope does not require solving every #51
problem, but subsequent reference-only acceptance must be explicit, accurately
measured and based on applicable passing gates. No repeated expensive
qualification is justified by this documentation-only plan.

## 74. Optimization execution active — 2026-11-01

User authorized all possible optimization-plan steps and automatic handover
maintenance. Local branch `compiler/u1b-optimization-execution-20261101` starts
from plan PR #107 head `d2bb747`; #106 source head remains `c2423d5` until the
coherent repair/candidate is published. Repository shell access is now restored.

Implemented locally: retain raw per-stage GC nanoseconds for exact reconciliation,
reject incomplete/unknown/nonmonotonic profile records, add cheap decoder/trace
mapping checks, persist raw records/summary through an explicit output directory,
and remove the accidental automatic expensive profiling job from ordinary CI.
Expanded private instrumentation attributes word/budget function entries via
compiler-emitted function-name traces, scalar allocation helpers and successful
allocator capacity traffic. Production compiler/runtime semantics unchanged.
Two initial focused executions stopped during diagnostic trace parsing before
native profiling because the unnamed entry trace uses `entry`; the parser now
handles that documented source marker. These are diagnostic harness failures,
not performance measurements or compiler regressions. Corrected full profile is
running locally under GCC -O2; do not claim its result before completion.

Next: inspect the corrected profile, choose ONE bounded structural word-read
pilot from actual counts, reject or prove it in five fresh-process pairs, run
focused safety/physical gates and representative compiler inputs, then qualify
the final adopted production batch once. No full owned compiler self-build.

### §74 measurement repair and current-source attribution — PASS locally

Three cheap decoder/trace tests pass. The expanded actual native profile passed
1/1 in 166.526 seconds total under local Linux x86-64 GCC -O2; 231 snapshots
reconcile exactly, stdout/stderr/exit match C bootstrap, zero allocator failures.
Raw per-stage nanoseconds remain present alongside derived seconds. Compiler
function-ID traces include an unnamed `entry` and `$type` specialization suffixes;
the diagnostic parser handles both, with a cheap regression. Three earlier
trace-mapping setup failures ended before collecting native profile evidence.

Current-source instrumented counters: 951,197,434 successful allocator entries,
919,544,101 boxed value creations, 531,056,690 evn_copy entries, 183,711,138
binary helpers, 392,601 word gets, 538,206 radix traversals, 3,229,200 current
child reads, 3,794,180 budget.work and 8,278,710 active checks. Whole-fixture
successful capacity traffic is 76,185,950,512 B (cumulative actual allocator
capacity incl. 32-byte headers, NOT live memory or a single UIR owner charge);
requested traffic is 38,099,750,224 B. Type-graph allocations are only 232,021.
Instrumented stage wall: seal 17.1383s, ingress 44.8880s, engine/type 4.0061s,
linked execution 2.4643s; GC inclusive 0.6138s, overlapping phases. Instrumented
process 88.4914s is not compared to uninstrumented speed measurements. Raw summary
committed at docs/evidence/2026-11-01/u1b-word-boxing-profile.json.

This confirms six-level word traversal and boxed scalar/helper amplification,
not a GC policy problem. A private fixed-depth noncreating word-read pilot is
now building/running via tools/probes/u1b_words_path.py. It preserves all six
current child reads and seven total work units per get/set; removes only loop
control/divisor updates/create branches, with no page cache or record layout
change. The source candidate is private; production source not yet promoted.

### §74 private word-path pilot — parity PASS, initial 10.02% lower wall

One serialized same-host original/candidate pair on the unchanged full linked
fixture passed exact C-bootstrap stdout/stderr/exit: baseline 61.444488s, fixed
noncreating path 55.285836s (10.02% nominal lower). User/system CPU and RSS are
recorded; this one-pair signal is NOT accepted performance proof. Both use the
same generated owned runtime and source baseline `c2423d5` already containing
the qualified same-owner poll change. Reproducer tools/probes/u1b_words_path.py
retains source/app/runtime/binary hashes, CPU/wall/RSS and complete outputs.

The candidate has now been copied into local src/compiler/u1_words.eri for
FOCUSED VALIDATION ONLY. It adds readPath() with six explicitly charged current
child reads; get/set use it, push retains original creating pageAt(). No layout,
ABI, work-credit, ownership, root/GC or quota changes. A new independent sparse
radix fixture covers all level/digit boundaries through index 33,554,431, current
root/child/page corruption/restoration, work charges at every refusal 0–6,
closed/frozen reads and cleanup on both native runtimes. Targeted tests are
running; do not claim them passing or ship before observing their results.
If safe, run the requested five alternating pairs on the already pinned binaries.

### §74 focused validation status during candidate preparation

The first local targeted batch passed 11/12 checks: foundation on C/owned,
linked stale/signature/dead-code rejection, bootstrap terminal malloc refusal
and mid-execution cancellation passed. The new sparse-path fixture alone failed
to compile after its temporary corruption helper invalidated optional-flow
narrowing; the fixture now retains explicit identity Node aliases. Its focused
rerun is pending. No production regression was established by the fixture error.

### §74 corrected sparse-path contract PASS; five-pair study RUNNING

The corrected independent radix fixture passed 1/1 in 12.541s, including C
bootstrap and actual owned-native execution. Together with the unchanged-code
11 passing checks in the preceding batch, all 12 targeted checks now pass.
The fixed-depth source exactly matches the already parity-checked pilot
candidate hash. Five AB/BA/AB/BA/AB pairs have started using the pinned existing
binaries, serialized without concurrent native builds. Raw wall/CPU/RSS and
output hashes are saved after each execution. A running study is not a pass.

### §74 five alternating pairs — correctness PASS, all five faster

The original optimized owned baseline and fixed-depth candidate completed all
10 fresh-process AB/BA/AB/BA/AB executions with exact independent C-bootstrap
stdout/stderr/exit parity. Baseline seconds: 59.714289, 59.603015, 61.790446,
63.126694, 62.998066. Candidate: 54.709537, 52.066750, 55.893081, 54.983744,
55.121805. Median 61.790446 → 54.983744s, ratio 0.8898422, 11.0158% lower;
all pairwise gains 8.38–12.90%. User/system CPU and whole-child RSS are raw in
docs/evidence/2026-11-01/u1b-fixed-path-five-pairs.json. RSS 100,856 KiB for
both may include inherited launcher pages; no per-owner RSS claim.

Candidate source hash dfa8a1a61dee1a4be0ddb5fb821c54098df80de33e705647b9619d0b224be60f
exactly matches the local source under focused tests; runtime hash unchanged.
This one Linux GCC host/one U1b reference workload is NOT general compiler
performance. Current frontend import closure has 33 modules and NO compiler.u1_*
modules: this change does not enter the existing production source pipeline.
A separate bounded #51 source-compiler profile is prepared, not a U1 speed claim.

Expanded profiling now supports optional readPath source counters and preserves
raw schema/phase data; candidate allocation profile is running. Baseline raw
231 snapshots are saved losslessly in u1b-word-boxing-records.json alongside
their schema/digest. Manual profiling workflow now retains raw data as well
as log; ordinary PR CI no longer runs the expensive profiler automatically.
Final smoke/physical and exact-head qualification remain pending.
