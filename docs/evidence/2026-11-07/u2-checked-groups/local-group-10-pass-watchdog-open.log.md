````text
test_closed_group_refusals_precede_all_assembly (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_closed_group_refusals_precede_all_assembly) ... ok
test_different_member_recovers_failure_into_normal_parent_result (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_different_member_recovers_failure_into_normal_parent_result) ... ok
test_distinct_normal_signatures_and_result_positions (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_distinct_normal_signatures_and_result_positions) ... ok
test_list_value_crosses_mutual_frames_and_preserves_snapshot (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_list_value_crosses_mutual_frames_and_preserves_snapshot) ... ok
test_missing_sibling_handoff_roots_are_terminal_defects (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_missing_sibling_handoff_roots_are_terminal_defects) ... ok
test_mutual_checked_frames_gc_and_independent_source_outcomes (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_mutual_checked_frames_gc_and_independent_source_outcomes) ... ok
test_mutual_frames_preserve_primary_and_ordered_secondary_context (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_mutual_frames_preserve_primary_and_ordered_secondary_context) ... ok
test_mutual_native_frame_stack_bound_and_reclamation (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_mutual_native_frame_stack_bound_and_reclamation) ... U2_MUTUAL_STACK=[{"depth": 0, "function_stack_bytes": 592}, {"depth": 1, "function_stack_bytes": 1184}, {"depth": 5, "function_stack_bytes": 3552}, {"depth": 32, "function_stack_bytes": 19536}, {"depth": 64, "function_stack_bytes": 38480}]
ok
test_owned_and_c_generators_agree_on_direct_group (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_owned_and_c_generators_agree_on_direct_group) ... ERROR
test_preflight_work_and_capacity_refusal_release_owned_plans (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_preflight_work_and_capacity_refusal_release_owned_plans) ... ok
test_two_managed_results_cross_member_handoff (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_two_managed_results_cross_member_handoff) ... ok

======================================================================
ERROR: test_owned_and_c_generators_agree_on_direct_group (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_owned_and_c_generators_agree_on_direct_group)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/d2c8eb25ab34/eristavi-lang/tests/test_u2_function_checked_group.py", line 332, in test_owned_and_c_generators_agree_on_direct_group
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
subprocess.TimeoutExpired: Command '['/tmp/tmp3cak65zl/direct-owned-group/generator.bin']' timed out after 120 seconds

----------------------------------------------------------------------
Ran 11 tests in 248.405s

FAILED (errors=1)
````
