# Single-owner whole-Function File integration — 7 November 2026

This is a bounded development checkpoint, not full U2 acceptance or release
qualification. Branch `compiler/u2-whole-function-file-roots-20261107`, draft
PR #121; parent #111 draft, issue #74 open. Source baseline was
`0263208d7168b9a2a2365f7f105749df6a980ea7`.

Exact tested implementation commit: `2f5065cb32755e8560da4340852c25dc3610224f`.

## Implemented

`emitFileChecked` extends the existing original-Function native emitter with
one independently verified lexical File owner. Exact imported symbols,
version/effects/signatures and the two-Text FileError carrier are checked before
output. The existing File runtime, lexical root/poison helpers, original SSA
edge transport and class-5 failure publication are reused. Acquisition publishes
immediately; close consumes on both outcomes. A carried pending scalar return
is cancelled on cleanup failure; ordinary handlers can recover.

Nested scopes, surviving owner prefixes, live primary/secondary composition,
File-owning checked recursive/group calls and all-exit release acceptance are
NOT completed. These combinations remain refused rather than reinterpreted.
No production compiler, public ABI, runtime adapter semantics or timeout changes.

## Verification

**Final result: 8 tests passed, zero failed, zero skipped, 69.823 seconds.**
Python compilation and `git diff --check` also passed.

The final command is preserved below; its raw outcome is in `focused.log`.
Environment: Linux x86-64, Python 3.12.14, GCC 13.3.0; pinned regex 2026.9.29 and
unicodedata2 17.0.0. `inputs.sha256` pins the changed compiler/test inputs.

```sh
PYTHONPATH=.:tests python -m unittest \
  test_u2_function_file_checked \
  test_u2_function_file_roots \
  test_u2_function_managed_native.U2FunctionManagedNativeTests.test_whole_function_identity_phi_and_gc_with_rooted_return \
  test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_checked_recursive_normal_failure_edges_roots_and_reclamation \
  test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_different_member_recovers_failure_into_normal_parent_result -v
```

The four new methods cover six generated execution cases (success, acquisition
failure and injected close failure, each with propagation or handler recovery),
exact close-call counts, pending-return cancellation, forced GC and complete
post-scope reclamation; independent Stage-0/current-C source results for success
and acquisition failure; missing owner and caller failure roots; deterministic
OOM during acquisition and cleanup-failure construction; wrong symbol/effects,
wrong FileError shape, malformed/stale owners and a live primary. Refusals must
precede assembly output. Retained Plan accounting is checked on success and
Unsupported refusal. Allocator failures remain terminal; no unwind is claimed.

The other four methods preserve the existing two-owner root-helper foundation,
managed identity CFG, checked self-recursion (depths 0/1/5/32/64) and checked-group
handler behavior. They do not claim recursive File integration. New native
assembly is generated through the bootstrap C compiler; owned-generator parity,
sanitizer/RSS/GC-pause qualification and broad independent origins are pending.

Earlier development attempts failed on a missing Python dependency, absent
bootstrap scalar specialization, generic optional-profile specialization and
incomplete test-fixture checked-error handlers. Those were corrected before the
final run; no assertions, tests or timeouts were weakened. Intermediate logs
from the interrupted environment were lost; the retained final log is the
current evidence, not a reconstruction of those logs.

## Hosted evidence and deferred work

Previous [smoke #42360813812](https://github.com/eristavi/eristavi-lang/actions/runs/42360813812)
was inspected: 171 run, 168 passed, zero failed, three intentional skips,
1611.120 seconds on `8104d8e8b1819765addab4fde3854fd37ccd81b2`.
The four-platform matrix was skipped. This is prior-foundation evidence only.

No broad Linux smoke, full matrix, owned full self-build or #51 optimization was
manually started for this batch. Any automatically triggered CI after publication
must be checked independently. Next: compose an original active FailureContext
with verified suffix cleanup, then admit nested owners and surviving prefixes.

## Publication patch-check correction

Automatic [CI #42397322506](https://github.com/eristavi/eristavi-lang/actions/runs/42397322506)
on documentation head `5329f323952e0ed62cff8af2d5f3482eb104a800` failed the
scope/patch job on an extra blank line at EOF in the newly archived historical
handover. Smoke and matrix were skipped, not failed compiler tests. The archive
newline is corrected in this documentation-only successor; source/test hashes
and the 8/8 local result are unchanged. The full staged patch is checked against
the parent PR branch, including added files. Hosted rerun remains unqualified.

## Continuation: owned-generator parity blocked

New `test_owned_and_c_generators_emit_identical_file_cfg` executes the bounded
source generator on the existing owned runtime under the established 120-second
watchdog. C generation and static ELF/no loader/no undefined symbols/nonexecuting
stack checks passed. Owned generator timed out: **1 test, 1 error, 149.521 s**.
See `owned-parity.log`; parity and generated application probes were not reached.
The regression is retained; timeout/assertions unchanged. Earlier 8/8 remains
valid only for the preceding test set. Python compile and full patch check pass.

Next inspect duplicate managed/File Plan creation cost before further extension.
No bottleneck attribution is established. The architecture now explicitly requires
the existing checked-chain failed-entry binding to identify active primary
propagation; liveness alone cannot authorize failure-context mutation.
Hosted #42397453782 scope passed, Linux smoke was running at inspection.

## Timeout resolution

Temporary copied-source trace: initial Plan begins 2.328 s, finishes 20.039 s
(**17.711 s**); second File Plan begins 20.042 s, compile starts 33.268 s;
publication verification starts 54.024 s and finishes 90.133 s (**36.109 s**).
The traced baseline still timed out at 120 s. Markers are opt-in GAS comments
in a temporary source copy; no production profiling output was added.

Fix: extract descriptor/type admission as `selectTypes`; legacy `create` wraps
it with the same SSA construction. File entry uses that admission, checks its
carrier is distinct, and constructs a single extended Plan. Mandatory fresh
publication and original owner verification remain. A compile-time-false
fixture block establishes the bootstrap's required legacy generic specialization;
it executes no Plan construction. The generic bootstrap requirement is unchanged.

Uninstrumented revised generator **105.651461352 s**, byte-identical owned/C
assembly, static-link/no loader/no undefined/executable-stack audit and real
File success/close-failure execution PASS. Full File class **5/5**, 164.210 s;
managed identity + checked recursion **2/2**, 14.333 s. No failures/skips.
Patch and Python compilation pass. See retained logs. Only targeted single
before/after evidence: no five-pair statistics or general performance claim.
No final qualification/merge; resume primary composition after this checkpoint.

## Primary binding extraction

Standalone `verifyPrimary` now owns the existing chain's failed-route checks;
the chain delegates rather than maintaining a competing verifier. Additional
admission checks bind exact source parameter shape, selected lexical cleanup
origin, instruction owner/range and failed-mode Plan. Direct fixture compares
its report to full chain facts and rejects a normal-entry Plan. Existing
primary-transfer corruption/restore and native prefix/dispatch tests remain.
Command: `PYTHONPATH=.:tests python -m unittest test_u2_checked_ssa_prefix -v`.
**2/2 PASS, 9.153 s**, no skips/failures; see `primary-binding.log`.
This completes reusable binding admission only. General Function composition,
nested acquisition and File-owning recursive integration remain open.

## Whole-Function primary composition — implemented

`primary-final.log`: **6/6 PASS**, 43.420 s, no failures/skips. New tests drive
actual generated acquire/bridge/close/return.failure CFG with an existing saved
primary. Four combinations cover clean/failing close and absent/existing
secondary. Assert original pointer identity, ordered linked context, forced GC
and full post-scope reclamation. Stale pair and normal-mode Plan refuse before
output. Fixture checks retained Plan accounting on success/Unsupported refusal.
Existing two-stage prefix/dispatch, ordinary File handler and checked-recursion
regressions pass. `primary-native.log` retains initial bootstrap specialization
failures corrected by the concrete nonexecuted Scope-list anchor.

Command: `PYTHONPATH=.:tests python -m unittest
 test_u2_function_file_primary.U2FunctionFilePrimaryTests
 test_u2_checked_ssa_prefix
 test_u2_function_file_checked.U2FunctionFileCheckedTests.test_generated_acquire_close_failure_handler_and_reclamation
 test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_checked_recursive_normal_failure_edges_roots_and_reclamation -v`.
New primary owned/C generator parity, broad CI, nested general Function ownership
and release qualification remain pending. Earlier parity does not qualify this
new revision. No broad/self-build/qualification workflow manually initiated.

## Native nested-owner and owning-recursion continuation

**Exact code/test tree** `8e5c8bd8de09d46586934b28dad2f7ac6f1729c1`
after the fixture-only typed transferred-failure correction, nonshadowing
pre-0.1 local correction and aggregate-aware checked-recovery edge builder.

[Focused GitHub CI #42404765081](https://github.com/eristavi/eristavi-lang/actions/runs/42404765081):
**3 tests / 3 pass / 0 fail / 0 skip, 51.554 s** on Linux x86-64
Clang with no changed watchdog/assertions. All three tests executed:
- `test_nested_lexical_file_owners_and_recovering_handlers`: two nested
  owners, successful and failing acquisitions/closes, saved outer root,
  forced GC, missing-owner hard rejection
- `test_generated_acquire_close_failure_handler_and_reclamation`: unchanged
  single-owner success, checked failure/recovery, cleanup and GC regression
- `test_checked_file_owning_self_recursion_retains_each_frame_and_closes`:
  self-recursive File-owning frames depth 0/1/4/16, close failures and full
  no-open-resource check

Previous CI attempts [#42403907261](https://github.com/eristavi/eristavi-lang/actions/runs/42403907261)
and [#42404551595](https://github.com/eristavi/eristavi-lang/actions/runs/42404551595)
initially failed on corrected fixture construction; they do not establish
additional source semantics. Only the successful exact-head targeted result
above qualifies this development slice. Complete U2 remains unaccepted.
