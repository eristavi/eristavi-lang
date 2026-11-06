# User-requested stop — unqualified U2 checked Function checkpoint

6 November 2026. Base revision `2bb0c01b54b894f9de813078d0c4a70e150110c5`.
The containing checkpoint commit is WIP, not a release or a qualified U2 result.
The latest full local feature/sanitizer passes preceded the later publication
batching change. Exact final-source complete validation has not been run.
No new expensive runs should start at this user-requested stop.

## Checkpoint source hashes

```json
{
  ".github/workflows/u2-function-managed-focused.yml": "5f58dcfbdc5c7540e19adf0ffa37b323719ca5b79f035f8abe0d35dca042bf2a",
  "src/compiler/u1_aggregate_finish.eri": "27633d4885365fa715800b6799383f725380f3962423a2253af7306f8e7d2cdb",
  "src/compiler/u1_builder.eri": "cabf8131779b8a809f8112535844c436abc14dc1349d640a7f51efe25a81bed4",
  "src/compiler/u1_ops.eri": "21e12c1cd94e94066adb45c197e3578bbb97a3adc7261e9571cabb80ee93c8db",
  "src/compiler/u1_physical.eri": "57c9da4ececa305dbb5918826f46b78f9666cc205f3d5d7b73d5e61496df6b12",
  "src/compiler/u1_verify.eri": "76b12efdb023d9e49a1fbc544f3482a75adddb784d088568ecf8d27bc08cb657",
  "src/compiler/u2_function_contract.eri": "183cdd9929d88860e181540d6f3e8e6a96f6a4a5be645583ab1c8a1cc5aff873",
  "src/compiler/u2_function_managed_x86_64.eri": "d28e51ff745e2617debd4a4a9876691c04e15bc3c200520647180f7ff88a3c92",
  "src/compiler/u2_managed_root_gate.eri": "af338cf0f5885122969d0f49d3376843b04f071a3fdf9bbcdc9468a9ed629371",
  "src/compiler/u2_scoped_owners.eri": "643f2415b98ebfd2a2c253877e67d87557e611c3a4aac715fd14735a6b5ca187",
  "src/compiler/u2_ssa_liveness.eri": "a1fe5ada71a974590a34e4302a6ac47c06461eb80142a4b032a65f2e40d62b85",
  "tests/fixtures/u2_function_checked_recursive.eri": "4ab3a0aebca689d9d61923eb3acb409a5b932198d2a2452b2ac3de268a327448",
  "tests/fixtures/u2_function_checked_recursive_reference.eri": "f8b46801a14554ca42a1bc8642d74ad67ea26606410b16c1149461afd96b80d0",
  "tests/test_u1_foundation.py": "0889a451a4b6da5a876dd91d46fc47d318d25b9b13624b36a1a16efb9cf07898",
  "tests/test_u1_owner_physical.py": "b5fc649b8cc2812ea90626c79155d546c184f61f6a87967904f209d2d0e401ad",
  "tests/test_u2_function_checked_native.py": "4bfbbd867da8e573a0f9fcf8b2eebc95db291637049f9c4559587456711d2911",
  "tools/run_ci_tests.py": "3882e91ca709b9c68ff7149e11d24b4474dd64b62e7a7209bbd2d4df71b42f08"
}
```

## Pre-batch coherent feature/compatibility run

```text
test_checked_failure_handler_returns_normal_through_parent_frames (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_checked_failure_handler_returns_normal_through_parent_frames) ... ok
test_checked_no_value_success_and_typed_failure_have_no_fake_result (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_checked_no_value_success_and_typed_failure_have_no_fake_result) ... ok
test_checked_one_scalar_result_and_failure_use_distinct_outcomes (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_checked_one_scalar_result_and_failure_use_distinct_outcomes) ... ok
test_checked_recursion_retains_complete_ordered_secondary_context (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_checked_recursion_retains_complete_ordered_secondary_context) ... ok
test_checked_recursive_normal_failure_edges_roots_and_reclamation (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_checked_recursive_normal_failure_edges_roots_and_reclamation) ... ok
test_checked_two_managed_normal_results_and_failed_result_are_disjoint (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_checked_two_managed_normal_results_and_failed_result_are_disjoint) ... ok
test_failure_return_cannot_bypass_an_active_file_owner (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_failure_return_cannot_bypass_an_active_file_owner) ... ok
test_malformed_body_and_dead_failure_returns_refuse_before_emission (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_malformed_body_and_dead_failure_returns_refuse_before_emission) ... ok
test_missing_native_failure_handoff_or_payload_is_a_terminal_defect (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_missing_native_failure_handoff_or_payload_is_a_terminal_defect) ... ok
test_mixed_text_and_identity_roots_across_loop_and_return (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_mixed_text_and_identity_roots_across_loop_and_return) ... ok
test_recursive_function_parent_only_text_roots_and_scalar_result (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_recursive_function_parent_only_text_roots_and_scalar_result) ... ok
test_recursive_import_or_mismatched_signature_rejected_before_emission (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_recursive_import_or_mismatched_signature_rejected_before_emission) ... ok
test_recursive_two_managed_results_handoff_before_child_scope_leave (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_recursive_two_managed_results_handoff_before_child_scope_leave) ... ok
test_reject_managed_producer_in_dead_block_before_emission (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_reject_managed_producer_in_dead_block_before_emission) ... ok
test_reject_mismatched_identity_descriptor_before_emission (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_reject_mismatched_identity_descriptor_before_emission) ... ok
test_whole_function_identity_phi_and_gc_with_rooted_return (test_u2_function_managed_native.U2FunctionManagedNativeTests.test_whole_function_identity_phi_and_gc_with_rooted_return) ... ok

----------------------------------------------------------------------
Ran 16 tests in 193.818s

OK
```

## Pre-batch bootstrap C ASan/UBSan (not owned assembly; LSan disabled for environment limitation)

```text
test_checked_failure_handler_returns_normal_through_parent_frames (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_checked_failure_handler_returns_normal_through_parent_frames) ... ok
test_checked_no_value_success_and_typed_failure_have_no_fake_result (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_checked_no_value_success_and_typed_failure_have_no_fake_result) ... ok
test_checked_one_scalar_result_and_failure_use_distinct_outcomes (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_checked_one_scalar_result_and_failure_use_distinct_outcomes) ... ok
test_checked_recursion_retains_complete_ordered_secondary_context (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_checked_recursion_retains_complete_ordered_secondary_context) ... ok
test_checked_recursive_normal_failure_edges_roots_and_reclamation (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_checked_recursive_normal_failure_edges_roots_and_reclamation) ... ok
test_checked_two_managed_normal_results_and_failed_result_are_disjoint (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_checked_two_managed_normal_results_and_failed_result_are_disjoint) ... ok
test_failure_return_cannot_bypass_an_active_file_owner (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_failure_return_cannot_bypass_an_active_file_owner) ... ok
test_malformed_body_and_dead_failure_returns_refuse_before_emission (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_malformed_body_and_dead_failure_returns_refuse_before_emission) ... ok
test_missing_native_failure_handoff_or_payload_is_a_terminal_defect (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_missing_native_failure_handoff_or_payload_is_a_terminal_defect) ... ok

----------------------------------------------------------------------
Ran 9 tests in 298.642s

OK
```

## 18-field physical owner/foundation/cleanup checks

```text
test_owned_actual_capacity_by_owner_and_gc_reclamation (test_u1_owner_physical.U1OwnerPhysicalTests.test_owned_actual_capacity_by_owner_and_gc_reclamation) ... U1A_OWNER_TIMING={"stage": "owner-physical-c", "wall_seconds": 0.0739490330006447}
U1A_OWNER_TIMING={"stage": "owner-physical-owned", "wall_seconds": 13.652066742999523}
U1A_OWNER_TIMING={"stage": "owner-physical-owned-diagnostic", "wall_seconds": 14.1107576050008}
U1A_OWNER_ACTUAL={"after_gc": {"backing": {"function": {"live": 0, "objects": 256, "observed_bytes": 91936, "reclaimed_bytes": 91936, "reclaimed_objects": 256}, "metadata": {"live": 0, "objects": 420, "observed_bytes": 154496, "reclaimed_bytes": 154496, "reclaimed_objects": 420}, "request": {"live": 0, "objects": 0, "observed_bytes": 0, "reclaimed_bytes": 0, "reclaimed_objects": 0}, "scratch": {"live": 0, "objects": 2668, "observed_bytes": 1048464, "reclaimed_bytes": 1048464, "reclaimed_objects": 2668}, "stress": {"live": 0, "objects": 16938, "observed_bytes": 6654480, "reclaimed_bytes": 6654480, "reclaimed_objects": 16938}}, "error": 0, "owners": {"function": {"allocations": 595, "live": 0, "peak": 87824, "reclaimed_bytes": 166192, "reclaimed_objects": 595, "traffic": 166192}, "metadata": {"allocations": 4458, "live": 0, "peak": 386160, "reclaimed_bytes": 1262240, "reclaimed_objects": 4458, "traffic": 1262240}, "request": {"allocations": 2, "live": 0, "peak": 640, "reclaimed_bytes": 640, "reclaimed_objects": 2, "traffic": 640}, "scratch": {"allocations": 11462, "live": 0, "peak": 1341824, "reclaimed_bytes": 3466656, "reclaimed_objects": 11462, "traffic": 3466656}, "stress": {"allocations": 72742, "live": 0, "peak": 7833696, "reclaimed_bytes": 21981776, "reclaimed_objects": 72742, "traffic": 21981776}}}, "before_gc": {"backing": {"function": {"live": 91936, "objects": 256, "observed_bytes": 91936, "reclaimed_bytes": 0, "reclaimed_objects": 0}, "metadata": {"live": 154496, "objects": 420, "observed_bytes": 154496, "reclaimed_bytes": 0, "reclaimed_objects": 0}, "request": {"live": 0, "objects": 0, "observed_bytes": 0, "reclaimed_bytes": 0, "reclaimed_objects": 0}, "scratch": {"live": 1088, "objects": 2668, "observed_bytes": 1048464, "reclaimed_bytes": 1047376, "reclaimed_objects": 2664}, "stress": {"live": 6654480, "objects": 16938, "observed_bytes": 6654480, "reclaimed_bytes": 0, "reclaimed_objects": 0}}, "error": 0, "owners": {"function": {"allocations": 595, "live": 64544, "peak": 87824, "reclaimed_bytes": 101648, "reclaimed_objects": 364, "traffic": 166192}, "metadata": {"allocations": 4458, "live": 287536, "peak": 386160, "reclaimed_bytes": 974704, "reclaimed_objects": 3412, "traffic": 1262240}, "request": {"allocations": 2, "live": 128, "peak": 640, "reclaimed_bytes": 512, "reclaimed_objects": 1, "traffic": 640}, "scratch": {"allocations": 11462, "live": 2560, "peak": 1341824, "reclaimed_bytes": 3464096, "reclaimed_objects": 11451, "traffic": 3466656}, "stress": {"allocations": 72742, "live": 7742272, "peak": 7833696, "reclaimed_bytes": 14239504, "reclaimed_objects": 47323, "traffic": 21981776}}}}
ok
test_owned_layout_contract_and_independent_large_radix_oracle (test_u1_owner_physical.U1OwnerPhysicalTests.test_owned_layout_contract_and_independent_large_radix_oracle) ... U1A_OWNER_TIMING={"stage": "owner-physical-c", "wall_seconds": 0.09666580300017813}
ok
test_prior_c_heap_evidence_remains_independent_not_a_multiplier (test_u1_owner_physical.U1OwnerPhysicalTests.test_prior_c_heap_evidence_remains_independent_not_a_multiplier) ... ok
test_opcode_categories_and_inline_edges_are_explicit (test_u1_foundation.U1FoundationTests.test_opcode_categories_and_inline_edges_are_explicit)
Future opcodes must never be mistaken for construction cells or CFG edges. ... ok
test_return_cannot_bypass_cleanup (test_u2_scoped_owners.U2ScopedOwnerTests.test_return_cannot_bypass_cleanup) ... ok

----------------------------------------------------------------------
Ran 5 tests in 52.557s

OK
```

## Earlier checked/registry/root focused run

```text
test_checked_failure_handler_returns_normal_through_parent_frames (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_checked_failure_handler_returns_normal_through_parent_frames) ... ok
test_checked_recursive_normal_failure_edges_roots_and_reclamation (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_checked_recursive_normal_failure_edges_roots_and_reclamation) ... ok
test_checked_two_managed_normal_results_and_failed_result_are_disjoint (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_checked_two_managed_normal_results_and_failed_result_are_disjoint) ... ok
test_failure_return_cannot_bypass_an_active_file_owner (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_failure_return_cannot_bypass_an_active_file_owner) ... ok
test_malformed_body_and_dead_failure_returns_refuse_before_emission (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_malformed_body_and_dead_failure_returns_refuse_before_emission) ... ok
test_canonical_invoke_and_outcome_only_payload_availability (test_u2_invoke.U2InvokeTests.test_canonical_invoke_and_outcome_only_payload_availability) ... ok
test_owned_native_reference_outcomes_and_ingress (test_u2_invoke.U2InvokeTests.test_owned_native_reference_outcomes_and_ingress) ... skipped 'opt-in Linux x86-64 owned-runtime invoke reference probe'
test_partial_invoke_construction_cannot_publish_and_closes_backing (test_u2_invoke.U2InvokeTests.test_partial_invoke_construction_cannot_publish_and_closes_backing) ... ok
test_reference_execution_selects_typed_outcome_and_preserves_fuel (test_u2_invoke.U2InvokeTests.test_reference_execution_selects_typed_outcome_and_preserves_fuel) ... ok
test_zero_normal_results_have_no_fake_ssa_value (test_u2_invoke.U2InvokeTests.test_zero_normal_results_have_no_fake_ssa_value) ... ok
test_multiple_targets_unused_contract_mutations_and_exact_cleanup (test_u2_fallible_registry.U2FallibleRegistryTests.test_multiple_targets_unused_contract_mutations_and_exact_cleanup) ... ok
test_all_canonical_invoke_failure_roots_and_refusals (test_u2_root_map.U2RootMapTests.test_all_canonical_invoke_failure_roots_and_refusals) ... ok

----------------------------------------------------------------------
Ran 12 tests in 101.174s

OK (skipped=1)
```

## Post-batch publication refusal matrix, corrected fixture

```text
test_whole_publication_table_refuses_corruption_and_releases_on_refusal (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_whole_publication_table_refuses_corruption_and_releases_on_refusal) ... ok

----------------------------------------------------------------------
Ran 1 test in 10.573s

OK
```

## Owned source generator at selected 120-second watchdog — FAILED

```text
test_owned_and_c_bootstrap_generators_emit_identical_checked_function (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_owned_and_c_bootstrap_generators_emit_identical_checked_function) ... ERROR

======================================================================
ERROR: test_owned_and_c_bootstrap_generators_emit_identical_checked_function (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_owned_and_c_bootstrap_generators_emit_identical_checked_function)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/d6ccfa3feba3/eristavi-lang/tests/test_u2_function_checked_native.py", line 465, in test_owned_and_c_bootstrap_generators_emit_identical_checked_function
    owned=subprocess.run([str(binary)],env={"PATH":"/unavailable"},
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/codex/runtimes/codex-primary-runtime/dependencies/python/lib/python3.12/subprocess.py", line 550, in run
    stdout, stderr = process.communicate(input, timeout=timeout)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/codex/runtimes/codex-primary-runtime/dependencies/python/lib/python3.12/subprocess.py", line 1209, in communicate
    stdout, stderr = self._communicate(input, endtime, timeout)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/codex/runtimes/codex-primary-runtime/dependencies/python/lib/python3.12/subprocess.py", line 2116, in _communicate
    self._check_timeout(endtime, orig_timeout, stdout, stderr)
  File "/opt/codex/runtimes/codex-primary-runtime/dependencies/python/lib/python3.12/subprocess.py", line 1253, in _check_timeout
    raise TimeoutExpired(
subprocess.TimeoutExpired: Command '['/tmp/tmpjbaiwmm0/checked-owned-generator/owned-generator.bin']' timed out after 120 seconds

----------------------------------------------------------------------
Ran 1 test in 152.515s

FAILED (errors=1)
```

## Owned source generator after batching — still FAILED

```text
test_owned_and_c_bootstrap_generators_emit_identical_checked_function (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_owned_and_c_bootstrap_generators_emit_identical_checked_function) ... ERROR

======================================================================
ERROR: test_owned_and_c_bootstrap_generators_emit_identical_checked_function (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_owned_and_c_bootstrap_generators_emit_identical_checked_function)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/d6ccfa3feba3/eristavi-lang/tests/test_u2_function_checked_native.py", line 465, in test_owned_and_c_bootstrap_generators_emit_identical_checked_function
    owned=subprocess.run([str(binary)],env={"PATH":"/unavailable"},
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/codex/runtimes/codex-primary-runtime/dependencies/python/lib/python3.12/subprocess.py", line 550, in run
    stdout, stderr = process.communicate(input, timeout=timeout)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/codex/runtimes/codex-primary-runtime/dependencies/python/lib/python3.12/subprocess.py", line 1209, in communicate
    stdout, stderr = self._communicate(input, endtime, timeout)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/codex/runtimes/codex-primary-runtime/dependencies/python/lib/python3.12/subprocess.py", line 2116, in _communicate
    self._check_timeout(endtime, orig_timeout, stdout, stderr)
  File "/opt/codex/runtimes/codex-primary-runtime/dependencies/python/lib/python3.12/subprocess.py", line 1253, in _check_timeout
    raise TimeoutExpired(
subprocess.TimeoutExpired: Command '['/tmp/tmpsh8gpb4x/checked-owned-generator/owned-generator.bin']' timed out after 120 seconds

----------------------------------------------------------------------
Ran 1 test in 152.077s

FAILED (errors=1)
```

## 20-second diagnostic; zero partial output; NOT a qualification run

```text
test_owned_and_c_bootstrap_generators_emit_identical_checked_function (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_owned_and_c_bootstrap_generators_emit_identical_checked_function) ... DEBUG_PARTIAL_STDOUT_BYTES 0
DEBUG_STDERR None
DEBUG_OUTPUT_TAIL b''
ERROR

======================================================================
ERROR: test_owned_and_c_bootstrap_generators_emit_identical_checked_function (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_owned_and_c_bootstrap_generators_emit_identical_checked_function)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/d6ccfa3feba3/eristavi-lang/tests/test_u2_function_checked_native.py", line 465, in test_owned_and_c_bootstrap_generators_emit_identical_checked_function
    owned=subprocess.run([str(binary)],env={"PATH":"/unavailable"},
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/u2-debug-owned-generator.py", line 13, in observed
    return original(command,*args,**kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/codex/runtimes/codex-primary-runtime/dependencies/python/lib/python3.12/subprocess.py", line 550, in run
    stdout, stderr = process.communicate(input, timeout=timeout)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/codex/runtimes/codex-primary-runtime/dependencies/python/lib/python3.12/subprocess.py", line 1209, in communicate
    stdout, stderr = self._communicate(input, endtime, timeout)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/codex/runtimes/codex-primary-runtime/dependencies/python/lib/python3.12/subprocess.py", line 2116, in _communicate
    self._check_timeout(endtime, orig_timeout, stdout, stderr)
  File "/opt/codex/runtimes/codex-primary-runtime/dependencies/python/lib/python3.12/subprocess.py", line 1253, in _check_timeout
    raise TimeoutExpired(
subprocess.TimeoutExpired: Command '['/tmp/tmpmlcf1l4k/checked-owned-generator/owned-generator.bin']' timed out after 20 seconds

----------------------------------------------------------------------
Ran 1 test in 54.862s

FAILED (errors=1)
```

## Diagnostic limitations

A short local debugger sampling attempt was denied with
`PermissionError: [Errno 1] ptrace attach`; its child was killed in `finally`.
No sampled PC/function evidence was obtained. No permissions escalation was
attempted. The stdout diagnostic had zero bytes at 20 seconds, so the source
code generator had not reached observable assembly emission at that point.
The full pre-output phase still needs instrumentation on continuation.

The initial publication-matrix test used a local named `dead`, shadowing the
fixture's existing block. This test-only error was corrected to `deadBit`;
the corrected matrix passed without weakening checks or resource budgets.

One canonical Function field was added, and both the actual owned physical
observer and independent schema pin were updated from 17 to 18. The accepted
8 MiB/64 MiB qualification budgets were retained. This is not a complete new
U2 RSS/GC-pause/fault study, a paired benchmark, or a whole-compiler speedup.

The new owned generator comparison is deliberately retained as an unresolved
watchdog failure. Do not omit/skip it to obtain a green CI result. No final
four-platform/completed-batch qualification, release or merge is claimed.
