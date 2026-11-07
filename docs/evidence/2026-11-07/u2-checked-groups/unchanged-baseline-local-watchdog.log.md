````text
test_owned_and_c_bootstrap_generators_emit_identical_checked_function (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_owned_and_c_bootstrap_generators_emit_identical_checked_function) ... U2_GENERATOR_TIMEOUT_PARTIAL_BYTES=0 U2_GENERATOR_PHASES=[]
ERROR

======================================================================
ERROR: test_owned_and_c_bootstrap_generators_emit_identical_checked_function (test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_owned_and_c_bootstrap_generators_emit_identical_checked_function)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/eristavi-u2-baseline/tests/test_u2_function_checked_native.py", line 648, in test_owned_and_c_bootstrap_generators_emit_identical_checked_function
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
subprocess.TimeoutExpired: Command '['/tmp/tmpd8tfs6_z/checked-owned-generator/owned-generator.bin']' timed out after 120 seconds

----------------------------------------------------------------------
Ran 1 test in 142.264s

FAILED (errors=1)
````
