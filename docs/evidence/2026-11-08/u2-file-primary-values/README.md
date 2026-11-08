# File primary aggregate bindings — 8 November 2026

Verified source/test commit: `375c983fd6da7170463d2d726912bb27f59cbe22`.
Branch: `compiler/u2-whole-function-file-roots-20261107`.

`focused.log`: 2/2 PASS in 26.109 s before explicit close-count assertions
were added. `final.log`: 5/5 PASS in 40.952 s, zero failures/skips, final inputs.
Known bootstrap C identity-list qualifier warnings remain unsuppressed. Logs
preserve output with trailing whitespace normalized for repository patch checks.

Final command (repository root; pinned dependencies):

```sh
PYTHONPATH=/workspace/scratch/a3215a4d2dcb/eristavi-venv/lib/python3.12/site-packages:tests:. python -m unittest -v \
 test_u2_function_file_value.U2FunctionFileValueTests.test_primary_values_and_nested_chain_preserve_context_and_aggregate \
 test_u2_function_file_value.U2FunctionFileValueTests.test_primary_values_refuse_bad_layout_and_cleanup_binding_without_leaks \
 test_u2_function_file_primary.U2FunctionFilePrimaryTests.test_generated_primary_preservation_and_secondary_append \
 test_u2_function_file_primary.U2FunctionFilePrimaryTests.test_primary_chain_keeps_outer_owner_and_ordered_context \
 test_u2_function_file_primary.U2FunctionFilePrimaryTests.test_live_primary_at_defined_call_still_refuses_before_output
```

Actual generated native single-primary and two-owner chain executions retain a
record across cleanup. On normal and failed final-close paths, its integer field
must equal 42 or the external caller rejects the ordinary return. Both entries
exercise successful/failing closes with/without existing secondary context;
primary identity, ordered secondary append, reverse cleanup, exact one/two close
counts and final reclamation are asserted. Wrong layout, duplicate primary
binding and wrong surviving owner prefix refuse without output or Plan leaks.
Legacy primary/chain execution and live-primary refusal pass unchanged.

No runtime adapter, ABI, source syntax, ownership proof or timeout changed.
The formerly duplicated single/chain admission bodies now share one core;
no measured speedup is claimed. Mixed group bindings and sibling producer plus
owning cleanup remain next. No new full source oracle, broad fault/sanitizer
qualification, current owned timing, four-platform or release gate is claimed.
Predecessor hosted run was in progress at inspection:
https://github.com/eristavi/eristavi-lang/actions/runs/42472248786
Final qualification deliberately deferred to preserve the reported 17% allowance.
