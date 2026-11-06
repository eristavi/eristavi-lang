# Whole-Function managed recursion — scoped development evidence

Exact implementation and test source: `50113f7103a0790f83b59475ae3256736c43ebdd`.
This is nonfallible self recursion, not general checked recursion or U2 closure.

The original UIR Function retains parent-private Text while child frames run
actual collector passes, returns the original identity and a scalar total,
then reclaims all child Text/graph/allocator state. A second case transfers two
managed results before child scope retirement. Independent frozen source runs
on Stage-0 and the old C-native compiler agree with the new native results.
No source/frontend-to-new-UIR pipeline or broad differential corpus is claimed.

Hosted exact-source results:

- [Managed Function focused run #42245608757](https://github.com/eristavi/eristavi-lang/actions/runs/42245608757): SUCCESS **7/7**, 76.287 s.
- [Existing Text/List integration #42245608781](https://github.com/eristavi/eristavi-lang/actions/runs/42245608781): SUCCESS **12/12**, 126.162 s.
- [Broad Linux smoke #42245608877](https://github.com/eristavi/eristavi-lang/actions/runs/42245608877): SUCCESS **147 run / 144 passed / 0 failed / 3 intentional skips**, 637.800 s. Scope/patch SUCCESS; final four-platform jobs SKIPPED. This timing is not a paired performance comparison.
- [Timestamped hosted test transcripts](u2-managed-function-recursion-hosted.md) preserve the exact-source test/result lines.

## Exact-source manifest

```json
{
  "implementation_commit": "50113f7103a0790f83b59475ae3256736c43ebdd",
  "implementation_tree": "fecf6dc5c8b958954b1fa169e8ecbfe9d2728b55",
  "platform": "Linux-6.18.57-x86_64-with-glibc2.39",
  "python": "3.12.14 (main, Aug 25 2026, 14:00:49) [Clang 22.1.3 ]",
  "cc": "cc (Ubuntu 13.3.0-6ubuntu2~24.04) 13.3.0",
  "sha256": {
    "src/compiler/u2_function_managed_x86_64.eri": "8f656cf4a2b49c8494f67039ae331b6f0f1bdb9f155527ca4323d09745b8070d",
    "tests/test_u2_function_managed_native.py": "f40ebc1481a170f41b89e150e82f4e0692dee0e20d6017ebd500a306bb11e8da",
    "tests/fixtures/u2_function_managed_recursive.eri": "ccd97bd96bcaa89d35dce9965d6b81c436d131908aa0631b9eef9b7db1503dbd",
    "tests/fixtures/u2_function_managed_recursive_reference.eri": "5ed497f2c7dc4f8f5db50250f99d1abd581ac54296427f43f446dc74de579a9f"
  },
  "depths": [
    0,
    1,
    5,
    32,
    64
  ],
  "dual_managed_return_depth": 32,
  "reference_expected_totals": [
    6,
    7,
    11,
    38,
    70
  ],
  "ordinary_local_methods": 7,
  "asan_ubsan_methods": 7,
  "leak_sanitizer": "not qualified: sandbox thread inspection failed",
  "owned_assembly_sanitizer": "not instrumented",
  "full_U2_acceptance": false
}
```

## Local consolidated positive/negative/source comparison

```sh
PYTHONPATH=tests:. python -m unittest -v test_u2_function_managed_native
```

```text
test_mixed_text_and_identity_roots_across_loop_and_return (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_mixed_text_and_identity_roots_across_loop_and_return) ... ok
test_recursive_function_parent_only_text_roots_and_scalar_result (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_recursive_function_parent_only_text_roots_and_scalar_result) ... ok
test_recursive_import_or_mismatched_signature_rejected_before_emission (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_recursive_import_or_mismatched_signature_rejected_before_emission) ... ok
test_recursive_two_managed_results_handoff_before_child_scope_leave (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_recursive_two_managed_results_handoff_before_child_scope_leave) ... ok
test_reject_managed_producer_in_dead_block_before_emission (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_reject_managed_producer_in_dead_block_before_emission) ... ok
test_reject_mismatched_identity_descriptor_before_emission (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_reject_mismatched_identity_descriptor_before_emission) ... ok
test_whole_function_identity_phi_and_gc_with_rooted_return (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_whole_function_identity_phi_and_gc_with_rooted_return) ... ok

----------------------------------------------------------------------
Ran 7 tests in 55.714s

OK
```

## Final additional zero/foreign FunctionId refusal

```sh
PYTHONPATH=tests:. python -m unittest -v test_u2_function_managed_native.U2FunctionManagedNativeTests.test_recursive_import_or_mismatched_signature_rejected_before_emission
```

```text
test_recursive_import_or_mismatched_signature_rejected_before_emission (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_recursive_import_or_mismatched_signature_rejected_before_emission) ... ok

----------------------------------------------------------------------
Ran 1 test in 33.335s

OK
```

## C-bootstrap AddressSanitizer and UBSan

```sh
CFLAGS='-O0 -fsanitize=address,undefined -fno-omit-frame-pointer' ASAN_OPTIONS='detect_leaks=0:halt_on_error=1' UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1' PYTHONPATH=tests:. python -u -m unittest -v test_u2_function_managed_native
```

```text
test_mixed_text_and_identity_roots_across_loop_and_return (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_mixed_text_and_identity_roots_across_loop_and_return) ... ok
test_recursive_function_parent_only_text_roots_and_scalar_result (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_recursive_function_parent_only_text_roots_and_scalar_result) ... ok
test_recursive_import_or_mismatched_signature_rejected_before_emission (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_recursive_import_or_mismatched_signature_rejected_before_emission) ... ok
test_recursive_two_managed_results_handoff_before_child_scope_leave (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_recursive_two_managed_results_handoff_before_child_scope_leave) ... ok
test_reject_managed_producer_in_dead_block_before_emission (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_reject_managed_producer_in_dead_block_before_emission) ... ok
test_reject_mismatched_identity_descriptor_before_emission (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_reject_mismatched_identity_descriptor_before_emission) ... ok
test_whole_function_identity_phi_and_gc_with_rooted_return (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_whole_function_identity_phi_and_gc_with_rooted_return) ... ok

----------------------------------------------------------------------
Ran 7 tests in 188.653s

OK
```

## LeakSanitizer initialization failure

```sh
CFLAGS='-O0 -fsanitize=address,undefined -fno-omit-frame-pointer' ASAN_OPTIONS='detect_leaks=1:halt_on_error=1' UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1' PYTHONPATH=tests:. python -u -m unittest -v test_u2_function_managed_native
```

```text
setUpClass (test_u2_function_managed_native.U2FunctionManagedNativeTests) ... ERROR

======================================================================
ERROR: setUpClass (test_u2_function_managed_native.U2FunctionManagedNativeTests)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/d6ccfa3feba3/eristavi-lang/tests/test_freestanding_graph_values.py", line 72, in setUpClass
    if (emitted.returncode,emitted.stderr)!=(0,''): raise AssertionError(emitted.stderr)
                                                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ==12==Can't open /proc/11/task for reading.
==11==LeakSanitizer has encountered a fatal error.
==11==HINT: For debugging, try setting environment variable LSAN_OPTIONS=verbosity=1:log_threads=1
==11==HINT: LeakSanitizer does not work under ptrace (strace, gdb, etc)


----------------------------------------------------------------------
Ran 0 tests in 5.146s

FAILED (errors=1)
```

## Interpretation and failures

The ASan/UBSan run instrumented the bootstrap-generated C runtime and compiler
programs, including the UIR assembly generators and old C-native reference.
The emitted owned assembler runtime and native Function are **not** instrumented
by ASan/UBSan. Their physical collector/root/reclamation checks are separate.
Leak detection was disabled only in the successful ASan/UBSan run because the
preceding zero-test LSan attempt failed to inspect `/proc/11/task`. Do not report
this as passing LSan or full owned-runtime sanitizer acceptance. An earlier
`-O1 -g` ASan/UBSan attempt ended with shell status 5 and an empty log, without
a test result; it is not passing evidence.

The first new native recursion harness linked the old generic graph descriptor
table, which lacks the existing Unicode17 view descriptors; all five new depth
cases faulted. Reusing the already established Unicode17 descriptor fixture
fixed the harness, after which the same compiler recursion path passed. No
runtime descriptor semantics or verifier checks were weakened.

No actual RSS, per-owner backing/traffic or GC pause/throughput scale study was
performed for this combined path. The remaining #74 definitions of done,
checked failure/cleanup integration, nested managed constructors/copies,
comprehensive bad-root/allocator refusal, full four-platform CI and batch
qualification remain open. This evidence cannot authorize merge or closure.
