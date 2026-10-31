# U1a #72/#77 conformance boundaries and evidence

**Current: PR #105 QUALIFIED AND MERGED (`8c625b1ece6a229844def93e2bf9563c14e9e273`).** Its tested/merged
tree `0d8bf1f4a58f66a15bb9a89bd42f596091ed9c36` matches. U1a physical acceptance is evidenced; #77 administrative
closure follows this checkpoint. The older open/pending paragraphs below are
historical and superseded by the final section. Durable U3 artifacts and U2
managed semantics remain separately unfinished.

Checkpoint: 2026-10-31. [PR #98](https://github.com/eristavi/eristavi-lang/pull/98)
is **QUALIFIED and MERGED** on main, merge `b05bd1863181d2a70800586a0efa8f1469d5d8df`;
tested head `6b2fadf7aca6a6249a4adbf57e38bab15cb916e0`, identical tested/merged tree `de5e72f4d03a370f53356a70497d3dd9eae1ec67`.
The existing production compiler, language semantics, ABI and independent
Python oracles remain unchanged. #72 is closed as completed; #77 remains
open for specifically attributable physical U1a-owned IR resource evidence.
The prior qualified baseline was [PR #96](https://github.com/eristavi/eristavi-lang/pull/96).

## #72: shared successor contract

The canonical Eristavi function `compiler.u1_successors` owns the traversal
schema for jump/branch/switch successor *edge identities*. Its original
`count/edge` are consumed by the verifier and SSA promoter. This batch adds
`caseBits/choose` (the last ordinal is always the default), and redirects
Eristavi's independent reference evaluator and bounded simplifier/rebuilder
to that schema, rather than carrying separate handwritten switch-row walkers.
The Python mathematical/control-flow oracle intentionally retains an
independent switch decoder, avoiding a common-mode success in a broken helper.
The private C-native emitter still has an independent, verified switch adapter
at a different execution boundary; future U3 machine lowering must consult
the validated UIR successor/case schema, not silently invent a new encoding.

Acceptance fixtures: three dense case-table scales (8/32/128 arms); widely separated unsigned-sorted
case *bits*, including both signed endpoints; two different edges to the same
target; an SCC with two independent entries and finite loop counts; original
and promoted SSA snapshots and independent Python return/trace predictions.
Verify the pre-existing malformed unreachable switch/edge fixtures and
cancellation/budget tests. Captured owner peak, fresh allocation traffic,
work visits and before/after semantic parity must remain within the U1a
qualification policy. Five fresh-process, real C-native resource observations run these scaled
fixtures with exact output parity and per-function owned capacity/traffic/work
counters. Report raw process RSS separately, in platform-specific units.
This does **not** attribute runtime GC/allocator heap retention to individual
UIR buffers or prove the large owner/runtime physical-memory gate, which remains
an explicit follow-up acceptance condition.

## #77: ownership of remaining acceptance

| Requirement | U1a acceptance boundary | Explicitly deferred boundary |
| --- | --- | --- |
| Source origin/revisions | Immutable linked *in-memory* source IDs/digests, original fault anchors, bounded ordered parent sets, exact publication copies, revocation on changed tables and import/signature/source mismatch | U3 binds these logical identities to actual user-source revisions during frontend lowering |
| Artifact remap | Private diagnostic source-map *ingress/remap*, source-digest and native-contract rejection, correct stripped native fault location | U3 defines versioned frontend/native artifacts and cache/manifest checks; no public UIR binary schema or persisted trust flag is established by U1a |
| Simplification | Exact, bounded, transactional pred/i64/CFG transformations, unchanged effects/fault sites, verify after mutation, no unsupported speculative folding | U3 chooses any user-facing optimization pipeline; advanced inlining/GVN/aggregate scalar replacement are separate milestones |
| Accounting | U1a's owned buffers, metadata/functions, work/cancellation and quota behavior require direct UIR capacity/traffic evidence, same-revision cleanup and representative 8/32/128 switch/CFG stress | U2 owns managed Text/List/identity, GC roots and exactly-once cleanup; U3 owns end-to-end source→native physical RSS/stress and performance against existing compiler; U4 owns packaged artifacts |
| Physical observation | Record fresh-process, controlled C/owned U1a executor timings, peak RSS, raw matched inputs, UIR modeled vs backed allocations, independent behavior | Heap/GC attribution of general Eristavi managed runtime cannot be claimed by scalar UIR tests; whole-compiler performance and object/link/cache artifacts require U2/U3 |

**Important:** Moving artifact production to U3 does NOT waive the U1a private
source-map ingress/remapping security check or U1a owned-memory accounting.
The already-merged [PR #96 physical evidence](docs/evidence/2026-10-31/u1-native-physical.json)
is five fresh-process original/simplified scalar native execution pairs. It does
not establish packed physical UIR heap/GC, larger mixed-stress, or compiled
source-to-UIR comparison. Do not mark #77 fully accepted until outstanding
U1a-owned stress/resource accounting is independently evidenced, or the owner
signs off on a specific contract revision to move named gates.

## Verified focused evidence — 2026-10-31

On exact code head `33897f21b1a38d9c3b819d50acdd978b910489fe`, the
[focused smoke workflow](https://github.com/eristavi/eristavi-lang/actions/runs/41193213024)
passed **21/21** tests. The 8/32/128 dense switch families, wide sparse
signed-boundary cases and two-entry SCC all agreed with the independent Python
reference before and after mandatory SSA promotion. Five fresh C-native
process executions gave identical output; full raw values, capacities, work,
peak RSS and caveats are retained in
[docs/evidence/2026-10-31/u1-switch-acceptance.json](docs/evidence/2026-10-31/u1-switch-acceptance.json).
The 128-arm fixture's modeled UIR owner peak was 720,704 bytes, under the
unchanged 8 MiB development qualification ceiling. This is not an inferred
physical UIR heap size or a managed runtime GC acceptance claim.

[Four-platform CI 41193441427](https://github.com/eristavi/eristavi-lang/actions/runs/41193441427)
and [completed-batch qualification 41193441428](https://github.com/eristavi/eristavi-lang/actions/runs/41193441428)
both **passed** on the exact tested/merged tree. Issue #72 was formally
closed as completed. Issue #77 remains **OPEN** specifically because
process RSS plus modeled UIR owner counters do not prove that in-memory
UIR private backing/allocator/GC physical attribution and larger stress
gates are satisfied. Durable artifacts and managed GC remain U3 and U2
respectively, not something silently qualified by this U1a batch.

## Release policy

PR #98 met its coherent-revision release criteria and was merged without
changing the qualified code tree. Issue #72 is closed; issue #77 remains
open pending real private UIR physical owner/budget attribution. Do not
rerun expensive CI for docs-only corrections, widen resource limits,
or automatically run experimental full owned compiler self-build. For any
future substantive changes, use focused smoke and one exact-head final
four-platform CI/completed-batch qualification before merging.

## Final physical acceptance — PR #105, 31 October 2026

The final head `f1fba11ff5e11791ad8c5d635fbf90873c686fa9` passed four-platform full CI 41222506854 and
completed-batch qualification 41222506873. Merge `8c625b1ece6a229844def93e2bf9563c14e9e273` has the identical
tested tree `0d8bf1f4a58f66a15bb9a89bd42f596091ed9c36`. All 469 discovered tests per platform passed with
specified platform skips; bootstrap C/D repeatability/offline/unchanged-source
checks and owned integration offline audit passed. Full owned compiler self-build
remains skipped and uncertified.

The 65,536-word/4,096-page fixture deliberately makes every identity's initial
cache hash collide. Phase peak 7,853,712 B and cumulative traffic 21,957,296 B
satisfy the unchanged 8 MiB/64 MiB gates. Semantic-owner observation independently
identifies actual retained wrapper/body allocator addresses for metadata, function,
module/import, publication and scratch/storage structures, with requested layout
oracles separate from actual capacities. Stress backing is 6,653,840 B / 16,938
objects; every observed object and allocation-phase ledger is reclaimed. Shared
reservation/slack, runtime caches and diagnostic maps remain explicitly separate.
The current 20-sample C study is independent whole-process collector evidence,
not per-owner C attribution. See the source-hashed raw qualified record and report.

This meets the outstanding U1a-owned physical/resource gate. Existing qualified
source/revision/diagnostic and bounded-transform gates remain. General U2 managed
heap/root/cleanup and U3 persistent artifact/source/frontend integration are not
waived or declared complete. #77 administrative closure follows this checkpoint.
