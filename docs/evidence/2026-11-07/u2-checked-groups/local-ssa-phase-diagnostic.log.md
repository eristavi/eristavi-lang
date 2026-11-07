````text
test_owned_and_c_generators_agree_on_direct_group (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_owned_and_c_generators_agree_on_direct_group) ... U2_GENERATOR_PHASE_SECONDS=2.312 marker=# U2_NATIVE_TRACE:group-member
U2_GENERATOR_PHASE_SECONDS=8.369 marker=# U2_SSA_TRACE:canonical-start
U2_GENERATOR_PHASE_SECONDS=25.408 marker=# U2_SSA_TRACE:canonical-done
U2_GENERATOR_PHASE_SECONDS=25.423 marker=# U2_SSA_TRACE:select-start
U2_GENERATOR_PHASE_SECONDS=26.145 marker=# U2_SSA_TRACE:select-done
U2_GENERATOR_PHASE_SECONDS=26.930 marker=# U2_SSA_TRACE:uses-start
U2_GENERATOR_PHASE_SECONDS=27.295 marker=# U2_SSA_TRACE:flow-start
U2_GENERATOR_PHASE_SECONDS=28.646 marker=# U2_SSA_TRACE:flow-done
U2_GENERATOR_PHASE_SECONDS=28.648 marker=# U2_SSA_TRACE:plan-done
U2_GENERATOR_PHASE_SECONDS=28.648 marker=# U2_NATIVE_TRACE:plan-admitted
U2_GENERATOR_PHASE_SECONDS=29.063 marker=# U2_NATIVE_TRACE:signature-admitted
U2_GENERATOR_PHASE_SECONDS=29.158 marker=# U2_NATIVE_TRACE:snapshot
U2_GENERATOR_PHASE_SECONDS=29.821 marker=# U2_NATIVE_TRACE:group-member
U2_GENERATOR_PHASE_SECONDS=36.519 marker=# U2_SSA_TRACE:canonical-start
U2_GENERATOR_PHASE_SECONDS=54.949 marker=# U2_SSA_TRACE:canonical-done
U2_GENERATOR_PHASE_SECONDS=54.963 marker=# U2_SSA_TRACE:select-start
U2_GENERATOR_PHASE_SECONDS=55.484 marker=# U2_SSA_TRACE:select-done
U2_GENERATOR_PHASE_SECONDS=56.012 marker=# U2_SSA_TRACE:uses-start
U2_GENERATOR_PHASE_SECONDS=56.279 marker=# U2_SSA_TRACE:flow-start
U2_GENERATOR_PHASE_SECONDS=57.457 marker=# U2_SSA_TRACE:flow-done
U2_GENERATOR_PHASE_SECONDS=57.459 marker=# U2_SSA_TRACE:plan-done
U2_GENERATOR_PHASE_SECONDS=57.460 marker=# U2_NATIVE_TRACE:plan-admitted
U2_GENERATOR_PHASE_SECONDS=57.620 marker=# U2_NATIVE_TRACE:signature-admitted
U2_GENERATOR_PHASE_SECONDS=57.707 marker=# U2_NATIVE_TRACE:snapshot
U2_GENERATOR_PHASE_SECONDS=58.873 marker=# U2_NATIVE_TRACE:plan-admitted
U2_GENERATOR_PHASE_SECONDS=59.320 marker=# U2_NATIVE_TRACE:signature-admitted
U2_GENERATOR_PHASE_SECONDS=59.424 marker=# U2_NATIVE_TRACE:snapshot
U2_GENERATOR_PHASE_SECONDS=60.150 marker=# U2_NATIVE_TRACE:publication-build
U2_GENERATOR_PHASE_SECONDS=61.221 marker=# U2_NATIVE_TRACE:publication-verify
U2_GENERATOR_PHASE_SECONDS=61.260 marker=# U2_SSA_TRACE:canonical-start
U2_GENERATOR_PHASE_SECONDS=98.579 marker=# U2_SSA_TRACE:canonical-done
U2_GENERATOR_PHASE_SECONDS=98.611 marker=# U2_SSA_TRACE:select-start
U2_GENERATOR_PHASE_SECONDS=100.177 marker=# U2_SSA_TRACE:select-done
U2_GENERATOR_PHASE_SECONDS=101.874 marker=# U2_SSA_TRACE:uses-start
U2_GENERATOR_PHASE_SECONDS=102.661 marker=# U2_SSA_TRACE:flow-start
U2_GENERATOR_PHASE_SECONDS=106.550 marker=# U2_SSA_TRACE:flow-done
U2_GENERATOR_PHASE_SECONDS=106.558 marker=# U2_SSA_TRACE:plan-done
U2_GENERATOR_PHASE_SECONDS=112.990 marker=# U2_NATIVE_TRACE:assembly-begin
U2_GENERATOR_PHASE_SECONDS=113.403 marker=# U2_NATIVE_TRACE:plan-admitted
U2_GENERATOR_PHASE_SECONDS=113.614 marker=# U2_NATIVE_TRACE:signature-admitted
U2_GENERATOR_PHASE_SECONDS=113.726 marker=# U2_NATIVE_TRACE:snapshot
U2_GENERATOR_PHASE_SECONDS=115.096 marker=# U2_NATIVE_TRACE:publication-build
U2_GENERATOR_PHASE_SECONDS=115.727 marker=# U2_NATIVE_TRACE:publication-verify
U2_GENERATOR_PHASE_SECONDS=115.762 marker=# U2_SSA_TRACE:canonical-start
ERROR

======================================================================
ERROR: test_owned_and_c_generators_agree_on_direct_group (test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_owned_and_c_generators_agree_on_direct_group)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/eristavi-u2-group-diag/tests/test_u2_function_checked_group.py", line 329, in test_owned_and_c_generators_agree_on_direct_group
    owned=checkedTests.capture_traced_owned_generator(
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/eristavi-u2-group-diag/tests/test_u2_function_checked_native.py", line 44, in capture_traced_owned_generator
    raise subprocess.TimeoutExpired(command,timeout,
subprocess.TimeoutExpired: Command '['/tmp/tmpxig99vga/direct-owned-group/generator.bin']' timed out after 120 seconds

----------------------------------------------------------------------
Ran 1 test in 137.230s

FAILED (errors=1)
````
