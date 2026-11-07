````text
test_owned_and_c_generators_agree_on_direct_group (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_owned_and_c_generators_agree_on_direct_group) ... U2_GENERATOR_PHASE_SECONDS=2.372 marker=# U2_NATIVE_TRACE:group-member
U2_GENERATOR_PHASE_SECONDS=29.685 marker=# U2_NATIVE_TRACE:plan-admitted
U2_GENERATOR_PHASE_SECONDS=30.099 marker=# U2_NATIVE_TRACE:signature-admitted
U2_GENERATOR_PHASE_SECONDS=30.197 marker=# U2_NATIVE_TRACE:snapshot
U2_GENERATOR_PHASE_SECONDS=30.898 marker=# U2_NATIVE_TRACE:group-member
U2_GENERATOR_PHASE_SECONDS=110.201 marker=# U2_NATIVE_TRACE:plan-admitted
U2_GENERATOR_PHASE_SECONDS=110.354 marker=# U2_NATIVE_TRACE:signature-admitted
U2_GENERATOR_PHASE_SECONDS=110.448 marker=# U2_NATIVE_TRACE:snapshot
U2_GENERATOR_PHASE_SECONDS=112.374 marker=# U2_NATIVE_TRACE:plan-admitted
U2_GENERATOR_PHASE_SECONDS=113.999 marker=# U2_NATIVE_TRACE:signature-admitted
U2_GENERATOR_PHASE_SECONDS=114.115 marker=# U2_NATIVE_TRACE:snapshot
U2_GENERATOR_PHASE_SECONDS=115.583 marker=# U2_NATIVE_TRACE:publication-build
U2_GENERATOR_PHASE_SECONDS=117.177 marker=# U2_NATIVE_TRACE:publication-verify
ERROR

======================================================================
ERROR: test_owned_and_c_generators_agree_on_direct_group (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_owned_and_c_generators_agree_on_direct_group)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/d2c8eb25ab34/eristavi-lang/tests/test_u2_function_checked_group.py", line 329, in test_owned_and_c_generators_agree_on_direct_group
    owned=checkedTests.capture_traced_owned_generator(
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspace/scratch/d2c8eb25ab34/eristavi-lang/tests/test_u2_function_checked_native.py", line 44, in capture_traced_owned_generator
    raise subprocess.TimeoutExpired(command,timeout,
subprocess.TimeoutExpired: Command '['/tmp/tmph45angr7/direct-owned-group/generator.bin']' timed out after 120 seconds

----------------------------------------------------------------------
Ran 1 test in 141.326s

FAILED (errors=1)
````
