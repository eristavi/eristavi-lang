# Eristavi compiler — handover

Checkpoint: 30 October 2026, Asia/Nicosia. This replaces the 28 October
measurement-first checkpoint. Resume the compiler redesign described here;
historical PR #46–#50 measurements are background, not the next task.

## Start a new chat with this

> Continue Eristavi from this handover. Verify GitHub main, the merge records and
> current instructions first. Preserve the language and approved architecture.
> The new typed UIR foundation, independent verifier and scalar-cell SSA promotion
> are implemented; the existing production compiler still uses its old pipeline.
> Next, inventory the agreed U1a contract against the implementation and prepare
> the remaining scalar/call/switch/strict-Float slice. Audit numeric operation
> classification and CFG successor walkers before adding operations. Keep tests
> focused; batch expensive qualification. Do not rerun the old 900-second owned
> self-build or claim the entire redesigned compiler is complete.

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
