# Superseded U2 development checkpoints

Historical snapshot from `43d56f2`; do not resume its pending/next-step lists.
Current status is in `HANDOVER.md` and the checked-group evidence report.

# Eristavi compiler — current handover

Updated 7 November 2026 (Asia/Nicosia). Closed checked-call group candidate under validation; U2 functionality and final qualification pending.
Branch: `compiler/u2-cleanup-foundation-20261102`; [PR #111](https://github.com/eristavi/eristavi-lang/pull/111) remains DRAFT; #74 remains OPEN.
Original checked-return checkpoint: `3100dc8e82f8e496d61fd38d0cdab5311416bd36`.
Prior publication implementation: `e40a64b3c8b7774dc68d3220f6b208ee38854ca6`. Earlier exact diagnostic: `a51182e663e645777186e9f6551bdc7081f36916`.
Latest implementation/test commit: `4b71966deb60da883b325936987b7f558ac7fe23` — focused and smoke green, not U2-complete.
No final four-platform qualification or merge. Optimization #51 remains PAUSED.

## Active development — 7 November 2026

Authorized batch: checked calls between distinct defined Functions and mutual
recursion, preserving exact managed/failure roots and independent evidence.
Current implementation `5dcc85f69ac458f83730957a9defd4b2fa3d0d7e` (following
initial candidate `c61afa9`) extends the existing emitter with bounded `emitCheckedGroup`; contract:
`docs/architecture/UIR_U2_CHECKED_CALL_GROUPS.md`. Further local refinements and
11 focused tests are under validation; not final accepted evidence. The direct
generator parity caller now retires its external ingress failure root after the
first generated root publication, matching the established mutual-call probe.

Preliminary mutual/handler/two-managed-result/negative checks passed; differing
normal result layouts, ordered secondary failures, missing sibling handoffs,
work/capacity-refusal reclamation and actual 592-byte/frame stack probe passed.
Hosted candidate legacy checks: managed/checked **18/18 pass** and word-path
prerequisite **1/1 pass**, run #42348095750; generator 107.514 s under unchanged
120 s watchdog. Existing Text/List integration #42348095794 also SUCCESS.
These hosted results cover `c61afa9`, not later implementation changes.

New group generator watchdog attempts timed out at 120 s; local baseline on
unchanged `6fe0024` also times out here. New diagnostic phase trace nevertheless
identified redundant full SSA Plan construction (~27 s/member per construction).
Local refinement retains existing immutable Plans for a bounded group transaction,
then freshly rederives/compares each with full `ssa.verifyPublications` before
emitting that body. No verified flag, new IR or bypass. Unused preflight machine
publication production was removed. Cleanup must release all retained Plans and
phases on completion or a later-member failure. Native frame/root ABI unchanged.
The refined retained-plan path passes both the new List snapshot/GC execution
and later-member work/capacity-refusal reclamation checks (2/2). A complete
11-method focused run and exact-source hosted smoke are now running/pending.
Changed-input bootstrap C ASan/UBSan **4/4 PASS**, 84.670 s, `-O0`,
`detect_leaks=0`, halt-on-error; this does not instrument emitted owned assembly.
The local focused suite passed 10/11 methods; only its owned generator watchdog
remained open (unchanged baseline also times out locally). Hosted #42349153243
passed **28/29 methods**: legacy owned generator **76.004 s**, new group owned
generator **62.882 s**, both below 120 s. The remaining failure was the C comparison
fixture missing an existing concrete scalar-edge specialization (`checkEdge`).
Restore the same unreachable `build.jump` specialization used by the established
fixtures; a fast C-only build/emission now PASSES (17,007 emitted bytes). C fixture
compilation now precedes the expensive owned generator. No production code or
watchdog change. Full corrected exact-source hosted checks remain pending. The old single-body entry remains direct rather
than routing through a new generic wrapper, preserving bootstrap specialization.
Local baseline timeout is recorded as an environment limit, not a new regression;
its exact hosted counterpart passed on `c61afa9`.

Preserve `4b71966` below as the previous verified implementation until new gates
pass. PR #111 remains DRAFT; #74 OPEN. No final matrix, merge or #51 restart.
The user requires this batch to stay within a five-hour session budget; reserve
time for exact-source testing, publishing code/evidence and this handover.

## Previous verified development checkpoint — 6 November 2026

**The owned/C generator watchdog blocker is RESOLVED for the focused
checked Function fixture.** Implementation/tests latest exact head
`4b71966deb60da883b325936987b7f558ac7fe23`, tested on
[managed Function run #42272620378](https://github.com/eristavi/eristavi-lang/actions/runs/42272620378):
**18/18 PASS**, including original uninstrumented, statically linked,
byte-identical owned-vs-C generated assembly and depth-32 forced-GC
checked recursion. The owned source generator took **98.399 seconds**
within the unchanged **120-second watchdog**, with original malformed
root/refusal cases still tested. A separate prerequisite
`test_u1_words_path` passed **1/1 on both bootstrap C and owned
runtimes**, including exact missing-path depth and work-budget failure
charges. All checked/managed class tests and the dedicated radix gate
completed successfully; no test was deleted or timeout raised.

[Linux smoke #42272620164](https://github.com/eristavi/eristavi-lang/actions/runs/42272620164)
also **PASS: 159 run / 156 passed / 3 intentionally skipped** on the
exact implementation, with patch/scope SUCCESS; the full four-platform
matrix was **SKIPPED, not qualified**. Earlier
[Text/List #42270143006](https://github.com/eristavi/eristavi-lang/actions/runs/42270143006)
**12/12 PASS** on the previous production source before the word-reader
change; Linux smoke covers current Text/List behavior. Original
U2 checked Function `roots.create` proof and independent final
`ssa.verifyPublications` proof remain; private checked emission
no longer repeats the intermediate full plan reconstruction.
Successful radix `words.get` reads now charge the same seven work units
in one bounded call when complete/affordable, with original per-level
fallback for invalid backing or limited budget. No public source/ABI,
allocator, GC or frozen semantic change. **This is a passing focused
candidate, NOT complete #74 acceptance or production qualification.**

**Current next step — implementation (do not rerun solved stages):**
complete GENERAL whole-Function checked UIR integration beyond bounded
self-recursion: arbitrary and mutual calls; original typed
`File` acquisition, move/consume and exactly-once reverse cleanup on
every normal/checked/handler exit; nested managed List/aggregate value
copy/identity and new typed FailureContext construction; complete
class-1/class-5 roots and root/owner/fault negatives. Then run broad
independent Stage-0/current-native/new-native source-origin outcome
comparisons; allocator/sanitizer/physical backing, traffic, RSS, GC-pause
and fault-injection evidence under existing budgets. Reconcile main
(conflicts previously seen in `HANDOVER.md` and checked-chain
architecture; inspect current merge base), qualify the single final
implementation on four platforms and completed-batch gates, then
merge PR #111 / close #74 **only when its eight DoD conditions pass**.
There is no justified % completion claim while these functional gates
remain open. Separate performance #51 remains PAUSED.

**Release state:** PR #111 DRAFT, unmerged and currently GitHub reports
`mergeable=false`; issue #74 OPEN and eight top-level DoD checkboxes
unchecked. Keep the production default and 32-byte ABI unchanged.
The final full owned-compiler self-build is explicitly excluded without
authorization. This documentation-only checkpoint follows the exact
`4b71966` passing implementation; do not call a docs-only commit a
new tested compiler.

Targeted reproduction:

```sh
PYTHONPATH=tests:. python -u -m unittest -v test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_owned_and_c_bootstrap_generators_emit_identical_checked_function
```

This builds an individual source generator with the owned resource runtime,
requires byte-identical assembly to the C generator, then executes the generated
checked Function at depth 32. Retain static ELF, no undefined symbols/loader and
non-executable-stack checks. Keep the test and its gate; do not skip it or silently
increase the timeout. Local `ptrace` was denied (EPERM). No measured speedup is
established. This probe is not a full owned-compiler self-build.

The solved checked/managed classes (18 methods) and latest Linux smoke
are verified on `4b71966`; do not repeat them without changed relevant inputs.
After completing the remaining generalized U2 semantics, validate new
SSA/root/owner/registry negatives, changed-input ASan/UBSan and physical/fault
evidence; then run the full four-platform and completed-batch qualification
once for the coherent final revision. Existing sanitizer/physical evidence is
only reusable within its documented older source scope.
