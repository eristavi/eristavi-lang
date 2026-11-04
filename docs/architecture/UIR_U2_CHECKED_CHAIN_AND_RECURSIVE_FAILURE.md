# U2 — bounded checked File cleanup chain and recursive failure roots

**Checkpoint:** 4 November 2026. **Status:** opt-in developmental proof on
[unmerged draft PR #111](https://github.com/eristavi/eristavi-lang/pull/111).
This is **not** full redesigned-UIR Function/native code generation, completed
U2 acceptance, or production ABI migration.

## Governing meaning

Read `DESIGN_PHILOSOPHY.md`, `LANGUAGE_SEMANTICS.md`,
`RESOURCE_CLEANUP.md`, the canonical checked-invoke/owner/root contracts,
and `CI_QUALIFICATION.md` before changing this code. The invariant is:
if an original checked error is already propagating, subsequent File cleanup
cannot replace it; failures append as secondary context in encounter order.
Every lexical File is closed exactly once, in reverse nesting order.
An ordinary success value must not appear on a checked failure edge.
Terminal runtime faults are not ordinary checked failures.

The implementation reuses the existing canonical opcode 46, version-two
carried SSA edge pools, original `u2_cleanup_plan.Plan` and independent
verifier, `u2_scoped_owners`, the class-5 failure root map, and the existing
owned x86-64 resource runtime. It adds no source syntax, executable
intermediate representation, new collector, runtime public ABI, or
production compiler/backend change.

## Step A — exact checked path admission, including already-failing entry

New `src/compiler/u2_checked_chain_verify.eri` admits a closed, bounded
three-instruction canonical checked File-close route:

1. The inner File.close has a normal successor with a live outer File and
   pending predecessor `i64`, and a failure successor with the original typed
   failure, outer File and same pending `i64`. Both edges are independently
   checked by `u2_checked_ssa_bind.verify` and whole-function canonical
   SSA/ownership checking.
2. The normal outer File.close is itself independently checked against its
   correct File owner, original cleanup obligations, exact normal/failure
   successor ValueIds, and class-5 root. A failed close cannot finish the
   pending successful return.
3. The *already-failing* outer File.close is validated independently against
   the original inner failure successor, its lexical outer owner, verified
   `failed=true` cleanup plan, exact opcode-46 source and argument,
   typed normal/failure block signatures, the failure-only `-1` ordinal,
   and exact transport of the original primary and pending `i64` on
   **both** outer outcomes. Its new checked failure has a separate first
   result, while the original failure remains carried; the checked failure
   root map must name the exact new failure destination and source origin.

The verifier does not trust cached proof flags or a new graph. It checks
the authoritative frozen canonical Function, current revision and original
owned metadata. Corrupting the original-primary transfer is rejected by
the canonical verifier or the path gate; the fixture restores the exact
original edge and re-verifies before native emission. Builder-only
`parameter()` lookups are captured **before Function completion**:
calling the mutable builder on a frozen UIR was a test-fixture error,
not an allowed verifier shortcut.

## Step B — actual second-stage native File close for both outcomes

After path admission, the canonical nested-owner fixture emits three
private helpers from the ORIGINAL independent cleanup plans:

- `erist_u2_ssa_71` executes the verified inner checked close, writes
  exact normal/failure SSA continuation slots, moves the surviving File
  and clears consumed source SSA handles, and pins the saved failure through
  allocation/GC.
- `erist_u2_cleanup_73` executes the verified normal-entry *outer*
  File close; only actual checked cleanup success completes that path.
- `erist_u2_cleanup_74` executes the verified **already-failing**
  outer File close; it keeps the original saved primary and appends any new
  cleanup failure to the same rooted context. The helper never converts
  the incoming failure to success.

`tests/test_u2_checked_ssa_prefix.py` executes the generated first and
second stages with the existing owned runtime, for three predecessor i64
values and two actual File-close outcomes, with forced GC, consumed-handle
poisoning, surviving owner checks, exactly-once close and the unchanged
primary/ordered secondary linked context. It asserts an error-mode outer
helper cannot return successful completion. This is private machine
adaptation **selected by the test caller**, not the general Function-level
native branch-label/handler dispatcher for all canonical blocks.

## Step C — physical recursive propagation through live frames

New `tests/test_u2_recursive_native_cleanup.py` uses the unchanged native
File cleanup helper emitted from an independently verified three-resource,
`failed=true` plan. It executes actual recursive native stack frames,
each with its *own registered scope* and three File roots plus the shared
managed class-5 saved-failure root. It tests clean closes and injected
checked close failures at depths 2 and 5, forces real collector passes
while parent and child scopes overlap, and checks:

- original body failure remains the primary throughout nested unwinding;
- each File is consumed exactly once; no resource survives final unwind;
- cleanup appends secondary errors in **inner-frame-first and
  reverse-within-frame** order, checking the *actual linked payload paths*
  against an independently constructed Python oracle rather than counts;
- child scopes can close without invalidating a live parent failure context;
- after root release, the existing runtime finish/leak audit succeeds.

This establishes a bounded **recursive runtime** and original-plan
conformance property. It is NOT yet canonical recursive checked-call lowering
with automatically published machine roots for all managed Text/List/identity
values or an independent new UIR runtime executable oracle.

## Tested revisions and negative/debug disposition

- [Dedicated Linux x86-64 focused #41886639816](https://github.com/eristavi/eristavi-lang/actions/runs/41886639816):
  **PASS, 7/7 tests, 0 failures**, after correcting a test's
  frozen-Function builder lookup.
- [Dedicated focused #41886845027](https://github.com/eristavi/eristavi-lang/actions/runs/41886845027):
  **PASS, 7/7 tests, 0 failures**, including both independently verified
  outer native-helper emission profiles.
- Code revision `87c244abc912d13f54b2730a69991ded050c36d1`:
  [dedicated native #41886929286](https://github.com/eristavi/eristavi-lang/actions/runs/41886929286)
  **PASS, 7/7 tests, 0 failures**. The test physically executes both
  second-stage helpers, checks the incoming primary remains unchanged,
  and verifies one appended secondary on the failing outer close.
- [Exact-code Linux Clang smoke #41886934726](https://github.com/eristavi/eristavi-lang/actions/runs/41886934726)
  **SUCCESS: 105 run / 102 passed / 0 failed / 3 intentional skips**,
  579.788 seconds, including native nested File and recursive frame checks.
  The same-code [sibling Linux smoke #41886929188](https://github.com/eristavi/eristavi-lang/actions/runs/41886929188)
  also **SUCCESS: 105 run / 102 passed / 0 failed / 3 skips**
  in 600.284 seconds. Both runs use the same exact implementation SHA;
  this duplicate adds no new acceptance requirement. Full four-platform
  matrix and completed-batch qualification were **not run**.
- Exploratory red checks before these passing revisions exposed a
  *test-fixture* bug: obtaining `build.parameter` after Function completion
  rejected valid U1a accounting state. Pre-capturing those typed ValueIds
  during construction resolved it. Temporary emitted debugging labels were
  removed. The semantic accounting verifier and frozen UIR rules were not
  relaxed.

## Remaining non-negotiable U2 acceptance

The route admitted here is a selected two-stage File-close profile with
caller-provided source SSA frame and test-caller-selected machine helpers.
General Function instruction/producer lowering, arbitrary checked
continuation block dispatch, mixed managed values, complete Unicode17
primary and ordered secondary `FailureContext` values, precise
per-instruction and recursive native Text/List/identity root publication,
foreign/dead roots and allocator-refusal faults, physical RSS/retained
capacity/GC pause evidence, independent Stage-0/new UIR/native parity with
stable source origins, and final exact-head four-platform plus completed-batch
qualification are still OPEN.

Keep PR #111 **draft/unmerged**, issue #74 **open**, default production
compiler/32-byte public ABI unchanged, U3/U4 migration separate, optimization
#51 paused. Do not run the excluded owned compiler self-build as a shortcut.
