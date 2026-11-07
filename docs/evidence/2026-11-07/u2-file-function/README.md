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
