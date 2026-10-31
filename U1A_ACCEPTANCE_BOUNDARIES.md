# U1a #72/#77 conformance boundaries and evidence

Checkpoint: 2026-10-31. This is an **integration candidate**, not a declaration
that U1a or its remaining GitHub issues have passed final qualification.
The existing production compiler, language semantics, ABI and independent Python
oracles must remain unchanged. The baseline qualified implementation is
[PR #96](https://github.com/eristavi/eristavi-lang/pull/96), tested at
`eec1dfee100be8c0f9b88a71a98b4866f36fab66`.

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

Acceptance fixtures: a 32-arm dense case table; widely separated unsigned-sorted
case *bits*, including both signed endpoints; two different edges to the same
target; an SCC with two independent entries and finite loop counts; original
and promoted SSA snapshots and independent Python return/trace predictions.
Verify the pre-existing malformed unreachable switch/edge fixtures and
cancellation/budget tests. Captured owner peak, fresh allocation traffic,
work visits and before/after semantic parity must remain within the U1a
qualification policy. A large-count/multi-scale stress family and actual
physical allocation/GC measurements are distinct evidence requests and are
not silently satisfied by these small correctness fixtures.

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

## Release policy

Use local/static checks and focused Linux smoke on incremental candidate
revisions. After the final coherent compiler-code revision, run **one**
four-platform full CI and required completed-batch qualification on the same
exact head. Compare the final tested Git tree against the merge tree.
Do not automatically run the experimental owned full compiler self-build,
do not dilute prior budget gates and do not merge or close #72/#77 based solely
on candidate code or historical green runs.
