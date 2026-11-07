# Eristavi compiler — current handover

Updated 7 November 2026 (Asia/Nicosia). Active, **focused-green File-root fix / full smoke pending** on separate branch
`compiler/u2-whole-function-file-roots-20261107`, [draft PR #121](https://github.com/eristavi/eristavi-lang/pull/121) targeting the checked U2 branch. Parent [PR #111](https://github.com/eristavi/eristavi-lang/pull/111) remains DRAFT/unmerged and U2 #74 OPEN. The previous checked Function group batch remains fully focused/Linux-smoke green; complete File integration and final qualification remain OPEN.
Parent checked-group implementation: `5dcc85f69ac458f83730957a9defd4b2fa3d0d7e`.
Parent checked-group tested checkpoint: `43d56f2f526fd57db5d790413217de439858b7a5`.
File fix tested checkpoint: `8104d8e8b1819765addab4fde3854fd37ccd81b2` — focused 3/3 PASS.
Prior full-smoke checkpoint `0352563` failed; broader fixed-code rerun pending.
No final four-platform qualification or merge. Optimization #51 remains PAUSED.

## File-root regression fix — 7 November 2026

The failing native probe used a hardcoded SSA offset 24 for the surviving outer
File after the inner close, whereas the original canonical ValueId requires
byte offset 32. The generated root helper correctly refused the missing source.
The test now exports actual ValueId offsets and close instruction IDs from its
original canonical fixture, uses those symbols for every handoff/close, and
reserves the full admitted 256-word SSA frame separately from roots/scope locals.
A negative native probe deliberately omits that handoff and must still fault;
the correct nested-close/forced-GC/reclamation probe must succeed.

Local focused File-root test PASS (positive and missing-handoff negative), 6.267 s.
[Focused CI #42360810124](https://github.com/eristavi/eristavi-lang/actions/runs/42360810124)
on exact fix checkpoint `8104d8e`: **3/3 PASS**. File probe 1/1, 13.206 s;
original generator parity gates 2/2, 255.978 s. Owned generators took **98.233 /
98.333 s**, both within unchanged **120-second** limits. Production emitter/runtime,
source semantics and watchdogs are unchanged; no cause is claimed for prior
runner timing variability. [Evidence/logs](docs/evidence/2026-11-07/u2-file-root-fix.md).
Broader [smoke rerun #42360813812](https://github.com/eristavi/eristavi-lang/actions/runs/42360813812)
is still running; do not mark it passed. No full qualification is claimed.
Whole-Function File lowering remains unintegrated; keep #121/#111 draft.

## Active File ownership checkpoint — 7 November 2026 (partial, NOT accepted)

**Do not repeat completed checked Function groups.** The next major block is
whole-Function File acquisition/consumption and reverse cleanup across original
canonical checked, normal, handler and recursive exits; this is **NOT done**.

- On child branch `compiler/u2-whole-function-file-roots-20261107`, draft
  [PR #121](https://github.com/eristavi/eristavi-lang/pull/121),
  source `src/compiler/u2_function_file_roots_x86_64.eri` (first implementation
  `f0b93b427cdd247be8840fe514ee10bd0f48ff15`): a bounded private emitter
  independently reruns the full original canonical scoped-owner proof,
  snapshots all original block root signatures and checked File consumption
  operands, then emits native class-1 File-root registration, per-block lexical
  owner publication (including dead blocks) and consumed-handle SSA/root-slot
  clearing on checked File.close. No separate executable IR, source syntax,
  moving GC, default-compiler edit or public ABI change.
- Added `tests/test_u2_function_file_roots.py` and an entry in the focused
  smoke selector. Test dynamically reuses the established 11-block original
  ownership fixture, checks emitted class/entry/close symbols and assembled
  object, and physically opens/closes two nested File handles while forcing
  real owned-runtime GC and post-scope reclamation. The test drives these
  transitions itself; the original whole-Function native CFG still does not.
  Source+test checkpoint `282e87b14fddabcb912c296910323b7b3bd8007c`.
- **Prior full-smoke validation: FAILED**, [CI #42352695186](https://github.com/eristavi/eristavi-lang/actions/runs/42352695186)
  on exact File checkpoint `0352563`, completed 7 November 2026.
  **171 run / 165 passed / 1 failure / 2 errors / 3 intentional skips**,
  1562.932 s. Scope/patch and Python compilation passed; full matrix skipped.
  The new `test_verified_lexical_owner_roots_cover_every_original_block_and_consumption`
  fails during native execution with exit 1 and
  `Eristavi runtime fault: invalid internal scalar value operation`
  (test line 251). Both the existing self-recursive and direct checked-group
  owned/C generator gates also hit their unchanged **120-second watchdogs**.
  The File fault was subsequently traced to the fixture handoff above. The
  timeout causes were not established; isolated reruns now pass unchanged. Do not
  infer a semantic regression or waive/increase the limits.
  Earlier green #111 evidence does NOT qualify this new File code.
  This failure record predates the focused test-fixture fix described above.
- Architecture and intentional boundaries:
  [whole-Function File ownership contract](docs/architecture/UIR_U2_WHOLE_FUNCTION_FILE_OWNERSHIP.md).
  The root/poison helpers are *not yet called by*
  `u2_function_managed_x86_64.eri`. No File.open/close is emitted there;
  no general checked/handler/multi-exit cleanup, primary/secondary handoff,
  recursive File frame, or native File checked success/failure path is completed.
  **Do not label PR #121 or U2 #74 accepted; do not merge #121/#111 yet.**
- Next: reuse the passing focused File-root fix; check the broader smoke result,
  then connect actual original
  acquisition, checked File.close and root
  publication to whole-Function emission, preserving original typed SSA edges,
  surviving owner prefixes, pending returns and existing class-5 FailureContext.
  Reuse verified real close adapters; prove arbitrary exit sets and recursive
  frames with independent outcomes, bad-root/owner/allocator faults and physical
  RSS/GC-pause evidence. Reconcile main and run final four-platform/completed
  qualification only on coherent finished U2. No owned full self-build, paused
  #51 work or unnecessary full CI.

