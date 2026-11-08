# Eristavi compiler — current handover

Latest verified source/test commit: `5a6ea63b7447c2aeeb2bac5afbe31f4ad9802ba6`.
This documentation successor changes no compiler/test inputs.

## Active checkpoint — 8 November 2026: nested List native constructors

Branch `compiler/u2-whole-function-file-roots-20261107`; batch base
`68c92c1e187978b806455c24ecf95746db3d94d9`. Added native whole-Function
List<List<i64>> and List<List<Text>> empty/copy/append/replace/count/get/collect.
Exact nested carrier/descriptor relationships and import signatures/effects/
version are checked. Boxed inner Lists reuse existing List runtime helpers,
canonical SSA and root publication. No new runtime adapters, executable IR,
ABI or ownership semantics. Descriptor reads now occur only for the matching
carrier/descriptor relationship; no measured performance gain is claimed.

**4/4 final nested methods PASS**, 35.408 s; zero failures/skips. Generated
native loops/snapshots/outer copy/replace/retrieved-inner append, counts and
Unicode contents survive forced GC and final reclamation. Stage-0 and current
native source references agree on 13. Nested get/replace retain source-located
terminal faults. Wrong descriptor/marker/missing inner/effects/argument type
refuse before assembly. **7/7 immediate regressions PASS**, 38.559 s; zero
failures/skips. That run overlapped the final descriptor-read optimization;
final nested tests independently passed after that edit. No unresolved focused
failures. Logs, exact inputs and limits:
[nested evidence](docs/evidence/2026-11-08/u2-nested-lists/README.md),
[contract](docs/architecture/UIR_U2_NESTED_LIST_NATIVE.md).

**Precise recovery point / first next task:** bridge existing managed value
aggregate constructors/copies into canonical whole-Function native lowering,
starting with one generated positive fixture and independent value-copy
reference, plus wrong-descriptor refusal. Audit existing descriptor/runtime
coverage first; do not reimplement it or repeat completed File/call/List work.

Remaining: deeper/general managed construction, typed FailureContext producers,
remaining combined checked/recursive/File paths (including an already-live
primary across defined calls), comprehensive hostile-root/allocator/independent/
sanitizer/physical proof, current owned/C generator parity and hosted timeout
gates, main reconciliation and final four-platform/completed-batch qualification.
Nested List evidence here does not qualify those combined paths or budgets.
#74 OPEN, #121/#111 DRAFT; no merge or production promotion.

Predecessor hosted CI was in progress when checked:
https://github.com/eristavi/eristavi-lang/actions/runs/42431255401
No new-head hosted/owned parity success claimed. Broad/full/self-build CI and
final four-platform qualification deliberately deferred to preserve usage;
#51 remains paused. User reported about 45% allowance at batch start; exact
remaining quota is not inspectable. Work stops at this verified checkpoint.
Older next-step lists below are historical and superseded by this checkpoint.

Latest verified source/test commit: `2d01be312587f6e1d114d9bcb8955604ea7f30f8`.
This documentation successor changes no compiler/test inputs.


## Active checkpoint — 8 November 2026: List<Text> constructors and value copies

Branch `compiler/u2-whole-function-file-roots-20261107`; base
`443ac14c60780b2be2e0dadfc0936f9fc8fbf78a`. Added exact native whole-Function
List<Text> empty/copy/append/replace/count/get/collect admission, reusing the
existing graph runtime, canonical Function/SSA roots and source-located bounds
faults. The distinct marker carrier must map to `listOfManaged(text)` and the
canonical Text carrier. Text slots are directly rooted, not boxed as i64 or
unboxed to lengths. No new runtime adapter, public ABI or frame layout.

**6/6 focused tests PASS**, 31.631 s, zero failures/skips. Includes generated
Text-list loop/snapshot/copy/replace/content checks, forced GC and reclamation;
independent Stage-0/current-native source results; terminal source-located
bounds failure; wrong descriptor/effects/type refusal; existing List<i64> and
mixed Text/List roots regressions. Raw logs and hashes:
[Text-list evidence](docs/evidence/2026-11-08/u2-list-text/README.md).
[Contract](docs/architecture/UIR_U2_LIST_TEXT_NATIVE.md).

**Next:** nested Lists and managed aggregate constructors/copies, typed
FailureContext producers, remaining call combinations and broader hostile-root/
allocator/independent/sanitizer/physical evidence, current owned/C parity and
hosted timeout gates, main reconciliation and final four-platform/full release
qualification. #74 stays OPEN, #121/#111 DRAFT. Earlier green generator timings
do not qualify this new head. No broad/full/self-build CI or #51 work manually
initiated. Older next-step statements below are superseded by this checkpoint.


Latest verified implementation/test commit: `34faa47b07b52de061e1a94546748369cbdc693f`.
This documentation successor leaves source/test inputs unchanged.


## Active checkpoint — 8 November 2026: returned child failures through owned callers

Branch `compiler/u2-whole-function-file-roots-20261107`; batch base
`46758d671d6f3d763067a737971fb5417b648612`. Issue #74 remains OPEN; #121/#111
DRAFT. General managed constructors, independent/physical/fault proof and final
qualification remain incomplete.

Implemented child-failure propagation through File-owning recursive callers:
the child's original saved failure now reaches a proof-bound parent cleanup
instead of being required to recover first. Clean parent close keeps that same
primary; failed parent close appends its new cleanup context. Per-call
liveBefore still refuses an already-live unrelated primary across a defined
call. Removing the coarse Function-wide refusal does not remove this guard.

New `emitMixedFilePrimaryGroup` binds explicit PrimaryAssignments to exact
1-based owning members, pre-admits the closed group and freshly verifies each
member's primary cleanup before emission. Missing/out-of-group/foreign and
duplicate assignments refuse before output. Caps: 16 members, 128 assignments,
eight primary sites per owning member. Ordinary group entry passes no binding
metadata and allocates no assignment nodes; new metadata is private, bounded
and not a verifier cache or executable IR. Existing SSA/root/owner proofs and
public ABI remain. Bootstrap generic specialization needs a nonexecuted concrete
shape anchor; known identity-list qualifier warnings remain in actual group
fixture logs. No runtime/compiler-wide performance speedup is claimed.

Validation: **6/6 focused methods PASS**, 39.671 s; additional live-primary
call refusal **1/1 PASS**, 7.064 s. Generated recursive depths 0/1/4/16 and a
distinct File-owning member cover clean, first-close-failure and all-close-
failure paths. Tests assert first failure pointer identity, expected secondary
count, exact close count, forced GC and complete reclamation. Invalid group
assignments check both owner accounts; existing primary-prefix and legacy
recursive/mixed-group paths remain passing. See
[raw evidence](docs/evidence/2026-11-08/u2-primary-calls/README.md).

**Next:** implement remaining non-i64/nested managed List/aggregate constructors
and typed FailureContext producers. Separately needed: explicit semantics/proof
for calls made while a primary is already active, broader mutual/mixed failure
combinations, current owned/C generator parity and timeout gates, hostile root/
allocator/physical/sanitizer and independent origin evidence; reconcile main,
then final four-platform/full completed-batch qualification. No merge/promotion,
full owned self-build, broad CI or #51 restart was manually selected this batch.
All older next-step statements below are historical relative to this checkpoint.


Verified implementation/test checkpoint: `c25498fc715b6d954747644f36447dc414e08d44`.
This documentation successor leaves compiler/test inputs unchanged.


## Active batch — 8 November 2026: multi-owner primary cleanup prefixes

Branch `compiler/u2-whole-function-file-roots-20261107`; base
`97630a1227dec9846f258716d35e023cd8cb6b7a`. **Issue #74 audited and remains
OPEN:** managed/failure producers, deep independent/physical/fault evidence,
latest owned/C parity and final four-platform/completed-batch gates remain.
No merge or production promotion is justified by focused functionality alone.

Implemented `emitFileCheckedPrimaryChain`: up to eight explicit bound closes
can preserve a primary while several lexical File owners are live. Each close
consumes only the innermost owner, carries the surviving prefix/primary/pending
i64 through both original edges, and appends a close failure after prior
secondary context. The original owner/root/continuation/failed-mode Plan and
publication proofs are retained and generalized, not replaced.

Code-efficiency constraint: bind-to-primary emission uses an O(1) dense table,
allocated only for Functions with bindings; ordinary callers have no new table
or linked binding nodes. Binding requests have at most eight temporary nodes;
no runtime frame or public ABI change. No benchmark speedup claim.

Evidence and exact focused recovery are recorded in
[8 November primary-prefix evidence](docs/evidence/2026-11-08/u2-primary-prefix/README.md).
The first combined run had nine passes and one test directory collision; that
fixture-name issue is corrected and its affected combination rerun. No tests,
assertions or timeouts were removed/weakened. Existing C-bootstrap pointer-
qualifier warnings remain visible in group logs and need separate review.

**Next:** finish combined primary propagation through File-owning checked
recursive/groups; remaining managed List/aggregate/typed FailureContext
construction; hostile-root/allocator/physical/sanitizer and independent outcome
evidence; reconcile main and qualify exact finished revision on four platforms.
Latest owned-generator gates remain unresolved on recent hosted smoke; earlier
105.651 s evidence does not qualify this new code. Broad/full/self-build CI and
#51 were not manually started in this batch, to preserve the usage budget.
All older next-step statements below are superseded by this recovery section.


## New verified nested primary across File-owner prefixes — 7 November 2026

**Exact implemented/tested code** [`1f1b44b`](https://github.com/eristavi/eristavi-lang/commit/1f1b44b3f74d11d5e95e0d85f0c0ac9277ef9e8b).
[Focused CI #42412553696](https://github.com/eristavi/eristavi-lang/actions/runs/42412553696)
**4/4 PASS, zero errors/skips, 51.138 seconds** on hosted Linux x86-64 Clang.
The previous three-method functional run [#42412420675](https://github.com/eristavi/eristavi-lang/actions/runs/42412420675)
also passed at `c20efa9`, before two negative binding cases were added.

The original whole-Function emitter can now preserve the exact *inner*
File.close FailureContext as primary across the checked *outer* File.close
after the inner owner was consumed and only its surviving outer prefix
remains. On failed outer close, the new cleanup failure is appended as a
secondary in native execution; success leaves the original primary
unchanged. Roots survive forced GC and the 0/1/2 live File cleanup paths
are checked. The existing independent `verifyPrimary` still demands a
fully bound original checked source, one exact surviving owner,
failure-mode cleanup Plan, canonical successors, typed class-5 root and
source origin. We no longer incorrectly reject this safe case merely
because the enclosing Function earlier had depth two. This is NOT a
new generalized verifier, alternate IR, public ABI, or runtime error
semantics. Stale continuation and wrong-mode Plan are refused before
assembly; previous one-owner primary and ordinary nested File tests
remain green. See [new evidence](docs/evidence/2026-11-07/u2-nested-primary/README.md).

**Still unaccepted for U2 #74:** arbitrary sequences of active-primary
closes with two or more owners still live, complete managed List/Text/
aggregate/failure constructors, hostile/foreign/retired root and
allocator/sanitizer/RSS evidence, broader Stage-0/C/native origin parity,
latest owned/C generator output parity, main reconciliation and
exact-head four-platform/full completed-batch qualification.
The functional change is an isolated tested feature, not U2 completion.
Keep #121/#111 draft, #74 open and #51 optimization paused. Do not reuse
a prior-head CI result as latest-source qualification.


## Latest verified File-owning closed/mixed-group checkpoint — 7 November 2026

**Exact tested source-and-test head:** `58008fd395c740daa4d038191e0e029cad32559a`.
[GitHub Actions focused native CI #42405486672](https://github.com/eristavi/eristavi-lang/actions/runs/42405486672)
**5/5 tests PASS, zero failures/skips, 59.822 s**, Linux x86-64 Clang
at the above head. The established single-owner File CFG, nested
surviving-prefix/checked recovery and File-owning self-recursive execution
remain green. New tests cover checked calls to an independently bound
**different File-owning Function body** and a **resource-free helper** while
the caller keeps its own original canonical lexical File owner. Both use
per-Function roots/checked failure signatures, real native opens/closes,
forced GC and post-frame reclamation.

There are two separate bounded, optional entry points:
`emitFileCheckedGroup` for closed all-owning groups and
`emitMixedFileCheckedGroup` for mixed owning/nonowning checked groups.
Each group's member Plans are pre-admitted, then freshly reverified at output;
no arbitrary File object is transferred to another body. Mixed groups use
**explicit 1-based exact owner-profile indices (zero for no File)** rather
than an unsupported bootstrap List of optional identity records.
The native tests passed with **C-bootstrap incompatible-pointer qualifier
warnings** from the function-array emission path; these are not test failures
but need review before final compiler qualification.

An earlier [hosted U2 smoke #42400012947](https://github.com/eristavi/eristavi-lang/actions/runs/42400012947)
failed three owned-generator 120-s watchdogs; it remains a separate U2
qualification blocker. Latest focused success does **not** qualify owned/C
generator output equivalence for this group, broad Linux smoke, four-platform
CI, comprehensive primary-failure composition across nested prefixes, all
managed constructors, physical/fault evidence or the complete eight-gate U2
definition of done. Do **not** mark issue #74 done, merge #121/#111, promote
production or resume general optimization #51 on this evidence.

**Next functional/acceptance work:** safely compose explicit primary failure
contexts through nested File cleanup, extend remaining managed List/aggregate
construction/copy and typed FailureContext producers, test combined class-1/
class-5 roots and hostile/foreign/stale owner conditions, then gather fresh
independent Stage-0/C/new-native evidence, physical/sanitizer evidence and
exact final-tree four-platform/completed-batch qualification. Keep the older
checkpoint narratives below as historical, not today's remaining-work list.


## Latest implementation checkpoint — 7 November 2026 (nested owners and File-owning recursion)

**Verified exact implementation/test tree:** `8e5c8bd8de09d46586934b28dad2f7ac6f1729c1`.
[Focused native CI #42404765081](https://github.com/eristavi/eristavi-lang/actions/runs/42404765081)
**3/3 PASS, 0 failed, 0 skipped, 51.554 seconds**, Linux x86-64 Clang,
against the unmodified prior single-owner integration tests.

The original whole-Function x86-64 checked emitter now admits independently
verified **nested lexical File owners (maximum supported depth eight)**, retains
the precise outer-prefix roots after inner close, and accepts recovering checked
handler branches where an incoming error is dead before another File operation.
The canonical owner, liveness and original CFG proofs remain mandatory.
Generated nested code is executed with forced GC, inner acquisition recovery,
injected close failures, missing outer root rejection and exact 0/1/2 live
resource counts on the tested paths.

**File-owning checked self-recursion now has native execution evidence:** each
recursive Function frame separately opens and closes its File; depths
0/1/4/16, forced GC and injected close failures are covered. A fallible
recursive call cannot use/pass a File handle as an ordinary argument or
silently overwrite an unbound live FailureContext. The failed-child path
tested here RECOVERS before closing this frame's own resource. Cross-member
File-owning groups and arbitrary active-primary composition across multiple
nested owners are NOT admitted or qualified.

New test files: `tests/fixtures/u2_function_file_nested.eri`,
`tests/fixtures/u2_function_file_recursive.eri`. Focused smoke workflow:
`.github/workflows/u2-file-nested-focused.yml`.
The existing one-owner primary composition remains a separate focused-tested
slice; latest owned/C generator parity and full exact-head CI/four-platform
qualification remain pending. Older development summaries below are historical
and their former “next implementation step” statements are superseded by this
current section. **Keep #121 and #111 draft, issue #74 OPEN, #51 paused.**

**Known unrelated U2 CI gate:** [run #42400012947](https://github.com/eristavi/eristavi-lang/actions/runs/42400012947)
finished with failure after 178 tests because three owned-generator executions
exceeded the unchanged 120-second watchdog on hosted Linux Clang. No semantic
assertion failure was reported in that run. This result is not green evidence;
do not lengthen the watchdog or restart broad optimization as a substitute
for completing U2. The new targeted functional CI does not qualify full U2.


Updated 7 November 2026 (Asia/Nicosia). Active branch:
`compiler/u2-whole-function-file-roots-20261107`, draft PR #121 targeting
`compiler/u2-cleanup-foundation-20261102` (draft #111). Issue #74 remains OPEN.
Tested implementation commit: `2f5065cb32755e8560da4340852c25dc3610224f`.
This documentation successor changes no implementation or test input.
Baseline head: `0263208d7168b9a2a2365f7f105749df6a980ea7`.
**Latest implementation: whole-Function primary/secondary File composition.**
`emitFileCheckedPrimary` now consumes the freshly verified explicit binding.
A failed close retains its separate original typed outcome and appends the
complete new failure to the rooted original primary with the existing runtime
`erist_rt_failure_append`. A successful close preserves the primary unchanged.
Both paths consume the File SSA/root and carry the original primary through
canonical edges. Existing secondary context remains before the new close
failure. The source primary must use the Function's exact class-5 carrier.
Binding verification lives in `u2_primary_cleanup_bind`; the existing chain
verifier delegates to the same proof. A nonexecuted concrete bootstrap helper
seeds Scope-list generic construction for resource-free importing callers.

**Final focused tests: 6/6 PASS, 0 failed/skipped, 43.420 s.** Four generated
primary scenarios cover clean/failing close with/without an existing secondary,
forced GC, retained primary identity, ordered append and final reclamation.
Stale binding and normal-mode Plan refuse before output. Existing nested helper,
File handler and depth-64 checked-recursion regressions pass. Early bootstrap
specialization failures are retained in `primary-native.log`; corrected exact
run is `primary-final.log`. No timeouts or assertions were weakened.

This finishes the bounded single-owner primary-composition implementation,
not full U2. Next: nested ownership/surviving prefixes in general Function
emission, then File-owning recursive/group frames. New-primary owned-generator
parity, broad smoke, deep physical/sanitizer and final qualification remain
pending; prior 105.651 s parity applies to the earlier single-owner revision.
Base: `5312f5042c9aa8276d33287f29a72ba8afb8ea44`. Keep drafts and #74 open.

**Current checkpoint: owned File generator timeout RESOLVED locally.**
The initial managed Plan was discarded before constructing the File-extended
Plan. Diagnostic trace measured **17.711 s** in that redundant first Plan;
mandatory publication verification took **36.109 s** and remains intact.
Descriptor admission now returns selected types separately; File emission
constructs one SSA Plan. Legacy create still performs the same admission and
Plan creation. Full independent publication and lexical owner proofs remain.

Uninstrumented owned generator: **105.651 s**, unchanged 120-second watchdog;
byte-identical owned/C assembly, static-link audits and generated File success/
close-failure execution PASS. Full File class **5/5 PASS**, 164.210 s; shared
managed/checked-recursive regressions **2/2 PASS**, 14.333 s.
Baseline traced run timed out at 120 s. These are targeted measurements,
not five paired timings, RSS/GC-pause or whole-compiler performance evidence.
See `owned-baseline-trace.log`, `owned-fixed.log` and `plan-regressions.log`
in the batch evidence folder. No timeout or assertion was weakened.

Next resume explicit checked-chain primary binding and failure composition,
then nested surviving prefixes; full File integration remains incomplete.
Implementation base is `71436a23c0dd315d765ee8d5e4837b4d97d5d8c5`;
this successor contains the measured fix. Prior evidence below is historical.
**Final focused validation: 8/8 PASS, 0 failed, 0 skipped, 69.823 seconds.**
The command, source hashes and raw log are recorded in
[the batch evidence](docs/evidence/2026-11-07/u2-file-function/README.md).
No merge, production promotion, final four-platform qualification, #51 work,
or experimental owned full-compiler self-build is authorized by this checkpoint.

## Current File implementation and recovery

The general whole-Function emitter now has an opt-in `emitFileChecked` entry.
Actual original opcode-46 File.openRead/close calls select original typed edges;
acquisition is immediately rooted, checked close consumes the original SSA and
lexical root on both outcomes, and pending scalar success is cancelled on close
failure. Handler recovery, class-1/class-5 forced-GC roots and final reclamation
are exercised by compiler-generated execution. Existing independent owners,
SSA publication, native resource adapters and the 32-byte public ABI are reused.

**Bounded, not full integration:** one lexical owner only. Nested owners,
surviving prefixes, active-primary/ordered-secondary composition and File-owning
recursive/group calls remain refused. General all-exit acceptance, deeper
foreign/stale root and physical/sanitizer evidence, main reconciliation and final
four-platform/completed-batch qualification remain open. Do not repeat completed
checked-group work or the single-owner open/close slice.

**Exact next implementation step:** extend File close emission to consume the
original active FailureContext through the existing verified suffix-cleanup
infrastructure, proving primary preservation and ordered secondary failures;
then admit nested owners/surviving prefixes. Retain current refusal gates until
each combination has native positive/negative evidence.

Previous smoke [#42360813812](https://github.com/eristavi/eristavi-lang/actions/runs/42360813812)
on `8104d8e8b1819765addab4fde3854fd37ccd81b2` is now confirmed SUCCESS:
**171 run / 168 passed / 0 failed / 3 intentional skips**, 1611.120 seconds.
Scope/patch passed; the four-platform matrix was skipped. No newer branch run
was present at initial inspection. This verifies the prior foundation, not the
new integration. Earlier failed attempts and exact focused fix evidence remain
in [the historical checkpoint](docs/history/2026-11-07/file-roots-before-function-integration.md).

The current batch's broader Linux smoke, owned/C generator parity and final
qualification are deliberately not initiated locally to protect the usage
budget. Any automatically triggered hosted smoke must be reported separately
and must not be assumed successful. All standing instructions below continue.

## Latest verified development checkpoint — 7 November 2026

**Checked calls between different defined Functions and mutual recursion are
implemented and focused-tested within the existing bounded native profile.**
`emitCheckedGroup` resolves original opcode-46 FunctionIds to exact bound bodies;
different normal signatures and caller-rooted managed/failure results reuse the
existing canonical CFG, SSA and owned runtime. This does not complete all U2.

[Focused run #42349932276](https://github.com/eristavi/eristavi-lang/actions/runs/42349932276)
**29/29 PASS**, 651.252 s, on exact checkpoint `43d56f2`, plus word-path
prerequisite **1/1 PASS**. The 11 new group methods cover mutual depths
0/1/5/32/64 under forced GC, cross-member recovery, swapped normal result layouts,
two managed results, List snapshot independence, complete ordered saved failure
context, missing sibling roots, 14 target/type/count/dead-origin refusals, later-
member budget-refusal cleanup and actual stack measurements. Independent frozen
mutual source compares Stage-0/current C-native/new native outcomes.

Uninstrumented owned/C generators emit **byte-identical assembly**; static ELF,
no loader/undefined symbols/non-executable stack and native normal/failure
execution all pass. Existing self-recursive generator: **103.728 s**; new direct
group generator: **101.624 s**, both within unchanged **120 s** watchdog. The direct
fixture retains the established scalar edge specialization needed by bootstrap C;
its C build runs first to fail fast. No test was removed or timeout raised.

[Linux smoke #42349932257](https://github.com/eristavi/eristavi-lang/actions/runs/42349932257)
**170 run / 167 passed / 0 failed / 3 intentional opt-in skips**, 850.922 s,
on exact checkpoint `43d56f2`; scope/patch SUCCESS. Full four-platform matrix
SKIPPED, not qualified. Both generators also passed within the unchanged watchdog
in this smoke (legacy 78.363 s, group 74.805 s). No full completed-batch release
qualification, production promotion or merge is claimed.

Bootstrap C ASan/UBSan: **4/4 selected methods PASS**, 84.670 s, plus corrected
C direct-generator probe PASS; `-O0`, halt-on-error, `detect_leaks=0`. This does
not sanitize emitted assembly or qualify LSan. Actual mutual-fixture Function
stack: **592 bytes/frame**, 38,480 bytes at depth 64; excludes runtime/collector
helper stack and RSS. Native post-scope reclamation and existing charged-owner
work/capacity refusal checks pass. Local owned generator watchdogs also fail on
unchanged prior `6fe0024`; retained diagnostic failures are not green evidence.
Hosted exact-source runs above are the recorded development gate.

The group is capped at **16 members / 1024 total SSA values / 2048 instructions**;
existing per-body 8-input/2-result/64-root/64-block/256-value/512-instruction limits
remain. Initial checked groups use the caller's one exact saved-context failure
carrier. Other call combinations, new failure construction, nested producers and
full File owner/cleanup integration remain open. Plans are privately retained
only for this bounded transaction, remain charged to their owners and are freshly
rederived/compared by full `ssa.verifyPublications` before each body's output.
All retained Plans/phases close on completion and any later-member refusal.
No cached verified flag, new IR layer, public ABI or production default change.

**Next step — do not repeat the completed call-group work:** integrate original
whole-Function File acquisition/consumption, owner proof, reverse exactly-once
cleanup, pending returns and every normal/checked/handler exit. Complete the
remaining call combinations and managed/failure constructors, combined roots,
independent/physical/fault evidence; reconcile main and perform final exact-source
four-platform/completed-batch qualification only for the coherent finished U2.
Keep #111 DRAFT and #74 OPEN until all eight DoD gates pass. No justified U2 %.

[Contract](docs/architecture/UIR_U2_CHECKED_CALL_GROUPS.md) ·
[Raw evidence, input hashes and limits](docs/evidence/2026-11-07/u2-checked-groups/README.md) ·
[Superseded development checkpoints](docs/history/2026-11-07/u2-checked-group-development.md).
The user required this batch to stay within a five-hour session budget. Do not
run experimental full owned-compiler self-builds; separate #51 remains paused.

## Implemented scope — reuse rather than repeat

| Component | Current boundary |
| --- | --- |
| Canonical scalar CFG | Original Function reverified including dead blocks, simultaneous block arguments, i64/pred, branch/switch/backedges/return; bounded private x86-64 backend. |
| Managed roots and calls | Exact per-ValueId entry/before/after liveness; class-1 Text/List/identity, loops, nonfallible self calls and up to two caller-rooted results. Checked `emitCheckedGroup` adds exact different/mutually recursive defined targets, original normal/failure edges, negative outcome ordinals/carried SSA and class-5 saved contexts. Child publishes into registered caller roots before scope retirement. Other call combinations/full File integration remain open. |
| Checked return contract | `u2_function_contract.eri` binds exact frozen FunctionId/signatures; optional opcode 47 `return.failure`. Fresh verifier checks binding/type/arity/attributes/origin, including dead blocks; legacy profiles refuse it. Scoped owners must be empty on both return kinds. Zero, one and two normal results supported; no fake Void SSA. |
| Text / Unicode17 | Established 12 imports: scalar construction, immutable concat/copy/equality, views/counts/indexes, NFC and collection; mixed Text/List loops. Unicode17 remains frozen. |
| List<i64> | Empty/copy/append/count/get/replace/collect with rooted snapshots/boxes and original source/LocId bounds faults, including negative/end bounds. Nested/non-i64 producers remain open. |
| File cleanup / failures | Checked typed edges, owner prefixes, reverse exactly-once closes, primary/ordered-secondary failure roots; bounded two-stage native chain and recursive runtime probes. Single-owner File.openRead/close now runs in whole-Function CFG through emitFileChecked; nested composition and owned recursive/group integration remain open. Whole-Function checked recursion propagates existing saved contexts. |
| Private physical schema | Function gained `definedTarget` (default zero): **18** owned graph cells, previously 17. Physical observer and independent pin updated; capacity/traffic budgets unchanged. |
| Publication proof | `ssa.verifyPublications` freshly verifies the full plan and all ordered IDs/entry/before/after bits, including dead code, before each body's output. Checked groups reuse private immutable Plans within one bounded transaction, never a verified flag. Derived plans close on comparison-work refusal; all group Plans/phases close on any failure. |

Contracts: [checked Function returns](docs/architecture/UIR_U2_CHECKED_FUNCTION_RETURNS.md),
[managed recursion](docs/architecture/UIR_U2_FUNCTION_MANAGED_RECURSION.md).

## Evidence and limits

The current 7 November gate is recorded above and in the linked checked-group
report. The scoped 6 November records below are historical inputs, not automatic
qualification of later changes.

[Raw logs and source hashes](docs/evidence/2026-11-06/u2-checked-function-stop-checkpoint.md)
retain detailed measurements and earlier failed attempts. Never treat older passes
as validation of later implementation changes.

| Evidence | Result and scope |
| --- | --- |
| Checked + existing managed tests, before publication batching | **16/16 pass**, 193.818 s: checked recursion depths 0/1/5/32/64, handler recovery, zero/scalar/two-managed returns, primary + two ordered secondary failures, malformed/dead returns/ordinals, legacy and missing-payload/handoff refusal; narrow Stage-0/old-C/new-native comparison. |
| Bootstrap C ASan/UBSan, before batching | **9/9 pass**, 298.642 s, `-O0`, `halt_on_error=1`, `detect_leaks=0`. LSan unavailable due to thread-inspection restrictions. Does not sanitize emitted owned assembly. |
| Owner physical/foundation/cleanup guards | **5/5 pass**, 52.557 s; actual backing/traffic/reclamation, 18-field schema and cleanup bypass refusal. Relevant builder/observer source unchanged since that run. |
| Publication corruption/refusal matrix after batching/fix | **1/1 pass**, 10.573 s: duplicate/foreign IDs, missing/dead/nonbinary flags, dead-entry corruption, forged backing, stale revision, extra rows and budget-refusal reclamation. Existing public SSA liveness negative also passed. |
| Owned/C comparison | **PASS on `4b71966`**: full focused **18/18**, 98.399 s generator (120 s limit), byte-identical C/owned assembly, static ELF checks and depth-32 checked recursion/GC, [#42272620378](https://github.com/eristavi/eristavi-lang/actions/runs/42272620378). |
| 6 November Linux smoke | **`4b71966` 159 run / 156 pass / 0 fail / 3 skips**, [#42272620164](https://github.com/eristavi/eristavi-lang/actions/runs/42272620164); full cross-platform matrix intentionally skipped. |
| Final acceptance | Four-platform full CI and completed-batch qualification **not performed** for current implementation. No merge, production promotion or public 32-byte ABI change. |

## Remaining before #74 can close

1. Reuse the tested checked-group implementation; extend remaining call
   combinations outside this profile (including nonfallible helper targets and
   mixed failure carriers as required), and integrate File acquisition/consumption,
   owner proof, reverse cleanup, pending returns and all handler exits in original
   whole-Function lowering.
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
| U2 | Checked defined-call groups/mutual recursion focused and Linux smoke green. Remaining resource/managed semantics, deep proof and final qualification unaccepted; #74 open, #111 draft. |
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

## Publication patch-check correction

Automatic [CI #42397322506](https://github.com/eristavi/eristavi-lang/actions/runs/42397322506)
on documentation head `5329f323952e0ed62cff8af2d5f3482eb104a800` failed the
scope/patch job on an extra blank line at EOF in the newly archived historical
handover. Smoke and matrix were skipped, not failed compiler tests. The archive
newline is corrected in this documentation-only successor; source/test hashes
and the 8/8 local result are unchanged. The full staged patch is checked against
the parent PR branch, including added files. Hosted rerun remains unqualified.
