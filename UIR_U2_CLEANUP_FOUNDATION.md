# U2 initial cleanup-planning slice — 2 November 2026

**Implemented and locally focused-tested; not qualified or merged.** The user
postponed performance issue #51 and selected U2 #74 as the active milestone.
Production remains qualified PR #110. This slice changes no default compiler,
runtime, source semantics, public ABI, U1a/U1b layout or verification requirement.

## Contracts and prerequisite measurements

Follow DESIGN_PHILOSOPHY.md, LANGUAGE_SEMANTICS.md, RESOURCE_CLEANUP.md,
the typed UIR proposal §§8–12/20, U1 contract §12 and CI_QUALIFICATION.md.
Returns and checked failures require exactly-once reverse cleanup. A failed
close consumes its owner. The body failure remains primary; otherwise the first
cleanup failure cancels success and becomes primary. Later cleanup failures
remain ordered secondary context. Standalone terminal defects run no cleanup.

`tools/probes/u2_resource_baseline.py` first measured the **existing** Stage-0
and C-native implementations, not redesigned U2. At depths 2/8/32, 150 cases
match a separately specified direct stack oracle: every early return, deep
success, body failure, all/alternating close failures and failed acquisition.
The diagnostic closes real handles first and injects synthetic checked close
failures afterward; it does not simulate an OS fclose failure. Source/C hashes,
toolchain and one-pass build/runtime observations are indexed in
`docs/evidence/2026-11-02/u2-resource-baseline.json`. Its hash-pinned
`u2-resource-baseline-raw.zip` retains all raw cases, the probe snapshot and
per-file SHA-256 manifest; CRC and payload hashes were verified.

| Owner depth | Legacy generated C bytes | Static legacy close calls | Exit unwind sum X |
| --- | ---: | ---: | ---: |
| 2 | 82,088 | 9 | 7 |
| 8 | 108,304 | 60 | 52 |
| 32 | 455,517 | 624 | 592 |

These counts are legacy expansion observations, not new-UIR speedups. Native
binary sizes include the diagnostic driver. Runtime timings include process
startup and observers and establish no performance acceptance threshold.
No RSS or actual per-owner allocator measurement is claimed. The full 150-case
study remains opt-in; routine tests retain only the cheap depth-two subset.

Reproduce with `python tools/probes/u2_resource_baseline.py --depths 2 8 32
--output summary.json --archive raw.zip` from the repository root (one command).

`docs/architecture/UIR_U2_INITIAL_POLICY.json` was selected **before** planner
implementation: at most 128 active owners, 256 close records and 2,048 record
words for one exit. Existing 8 MiB peak / 64 MiB traffic function-ledger limits,
construction work accounting and 120-second watchdog remain. These are explicit
prototype admission policies, not measured physical capacities or source limits.
Whole-function X/A/expansion, payload and runtime budgets remain open.

## Actual implementation

`src/compiler/u2_cleanup_plan.eri` builds private source-exit planning data.
This is not another executable IR, canonical U2 instruction publication, an
ownership-verification stamp or a runtime resource implementation.

Inputs are frozen same-request metadata, a function owner/phase, ordered lexical
scope obligations, surviving prefix, original exit LocId and pending failure
mode. This private input convention uses increasing lexical-preorder scope IDs.
Each obligation retains resource contract, owner-value index and cleanup LocId.
IDs/ranges/origins are checked before allocating the plan. They are not yet
resolved against canonical resource contracts/SSA owner signatures.

For D exited owners, construction iteratively emits exactly D normal-mode and
D failure-mode closes. A normal successful close advances in normal mode. Its
failure edge advances to the NEXT failure-mode close, consuming the current
owner on both edges. Failure-mode closes advance on either outcome, preserving
the existing primary and appending any new failure when runtime lowering exists.
The final destinations distinguish pending success from checked propagation.
An initially failed exit enters the failure chain directly. Empty exits have no
close records. No suffix is repeated for combinations of close failures.

Construction is O(active depth + exited depth), with O(exited depth) owned
output; there is no recursion or cross-exit sharing. Plan/control/word backing
uses the existing owner ledger, closes on every checked construction refusal,
retains consumed traffic/work and freezes successful record storage.

## Focused evidence

- 30 actual compiled Eristavi plans at depths 0/2/8/32/128, with zero/half/full
  surviving prefixes and normal/already-failed entry modes.
- 1,602 independently checked paths: exhaustive failure masks through depth 8,
  and none/all/alternating failures at larger depths. A deliberately broken
  private failure edge that retries a consumed owner is rejected by the oracle.
- Exact source/exit origins, owner IDs, final continuation, reverse close order,
  stable primary and ordered secondary failures match the direct Python oracle.
- Duplicate/zero owner obligations, invalid surviving prefix and foreign LocId
  refuse before storage publication; six work allowances, zero traffic,
  cancellation and the preselected depth-129 limit leave no live/pending plan
  backing. Successful plan close and final request close restore charges.
- Seven focused tests pass: new planner, cheap Stage-0/native baseline and five
  existing native resource regressions. Planner also joins ordinary smoke CI.
  No full matrix, full qualification or owned compiler self-build was requested.

At depth 128, the six-plan lifecycle has modeled owner peak **212,128 B** and
traffic **643,456 B**. These ledger observations are not physical heap/RSS.
Raw exact module/fixture hashes and counters are in
`docs/evidence/2026-11-02/u2-cleanup-planner.json`.

Initial development errors were confined to the new fixture/tool: diagnostic
C entry signature, explicit generic element typing, no-value call syntax,
Text/Int output formatting and a bootstrap nested-index member-write limitation.
The final fixture uses existing supported element replacement; no production
compiler workaround or contract weakening was introduced.

## Next U2 gates

Define the versioned optional managed/checked/resource operation contracts and
bind this exit plan to canonical typed success/failure edges and owner scope
tables. Implement independent all-block scoped-owner verification, checked
payload availability, primary/secondary runtime context and root maps before
publication/execution. Complete Text/List/identity value/copy semantics, Unicode17,
managed-local promotion, loops/many exits/identity cycles and physical/fault
evidence. Plans do not certify these unimplemented features.

Retain the existing compiler as rollback/oracle. Use focused tests during U2
development; one final four-platform CI plus full completed-batch qualification
is required before merging a coherent compiler batch. U2 #74 stays OPEN; U3/U4
remain unimplemented. #51 stays OPEN but PAUSED by user instruction.
