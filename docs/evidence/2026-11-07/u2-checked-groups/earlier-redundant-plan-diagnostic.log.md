````text
test_owned_and_c_generators_agree_on_direct_group (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_owned_and_c_generators_agree_on_direct_group) ... U2_GENERATOR_PHASE_SECONDS=2.786 marker=# U2_NATIVE_TRACE:group-member
U2_GENERATOR_PHASE_SECONDS=29.230 marker=# U2_NATIVE_TRACE:plan-admitted
U2_GENERATOR_PHASE_SECONDS=29.672 marker=# U2_NATIVE_TRACE:signature-admitted
U2_GENERATOR_PHASE_SECONDS=29.775 marker=# U2_NATIVE_TRACE:snapshot
U2_GENERATOR_PHASE_SECONDS=30.414 marker=# U2_NATIVE_TRACE:group-member
U2_GENERATOR_PHASE_SECONDS=57.385 marker=# U2_NATIVE_TRACE:plan-admitted
U2_GENERATOR_PHASE_SECONDS=57.552 marker=# U2_NATIVE_TRACE:signature-admitted
U2_GENERATOR_PHASE_SECONDS=57.650 marker=# U2_NATIVE_TRACE:snapshot
U2_GENERATOR_PHASE_SECONDS=58.864 marker=# U2_NATIVE_TRACE:group-member
U2_GENERATOR_PHASE_SECONDS=90.414 marker=# U2_NATIVE_TRACE:plan-admitted
U2_GENERATOR_PHASE_SECONDS=90.874 marker=# U2_NATIVE_TRACE:signature-admitted
U2_GENERATOR_PHASE_SECONDS=90.992 marker=# U2_NATIVE_TRACE:snapshot
U2_GENERATOR_PHASE_SECONDS=91.772 marker=# U2_NATIVE_TRACE:publication-build
U2_GENERATOR_PHASE_SECONDS=92.859 marker=# U2_NATIVE_TRACE:publication-verify
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
subprocess.TimeoutExpired: Command '['/tmp/tmpk0npjitv/direct-owned-group/generator.bin']' timed out after 120 seconds

----------------------------------------------------------------------
Ran 1 test in 143.338s

FAILED (errors=1)
````
