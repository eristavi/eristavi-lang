# File aggregate binding execution evidence

Branch compiler/u2-whole-function-file-roots-20261107.
Base ddf98947c88abde97942072d3a378dd223102ebe.
Verified source/test SHA: 19ad90ab80b048789ed0273fb6db0d36f342cfae.
Documentation/evidence successor leaves implementation/tests unchanged.

final.log: **5/5 PASS**, 39.502 s, zero failures/skips (two new methods plus
three immediate File/primary/guard regressions). producer.log: **1/1 PASS**,
7.869 s, implementation unchanged, adds fresh context after File consumption.
focused.log: initial **2/2 PASS**, 16.164 s. No unresolved focused failures.
Known C pointer-qualifier warnings remain unsuppressed. Logs normalize trailing
whitespace only; assertions, timeouts and existing tests unchanged.

Actual static native execution covers single and one-member homogeneous group
normal/open-failure/close-failure outcomes, aggregate liveness across close,
exactly-once consumption, pending-return cancellation and final reclamation.
An invalid vector refuses without leaking a Plan. New context construction after
close executes using the existing typed adapter and class-5 handoff. Existing
source-reference File behavior is historical evidence; no new full independent
oracle for the added record composition is claimed. Existing primary ordering
and live-primary refusal regressions pass. Primary/mixed bindings and sibling
composition remain unfinished; see UIR_U2_REMAINING_CHECKLIST.md.

Commands (Linux x86-64; repository/tests and pinned dependency site-packages on
PYTHONPATH; regex 2026.9.29, Unicode 17):

```
python -m unittest -v test_u2_function_file_value test_u2_function_file_checked.U2FunctionFileCheckedTests.test_generated_acquire_close_failure_handler_and_reclamation test_u2_function_file_primary.U2FunctionFilePrimaryTests.test_generated_primary_preservation_and_secondary_append test_u2_function_file_primary.U2FunctionFilePrimaryTests.test_live_primary_at_defined_call_still_refuses_before_output
python -m unittest -v test_u2_function_file_value.U2FunctionFileValueTests.test_fresh_typed_context_after_file_consumption
```

No broad unchanged suites, owned full-compiler self-build, #51 work or final
qualification initiated. Current owned/C/hosted timing repeatability and full
four-platform qualification remain pending. Predecessor CI was in progress:
https://github.com/eristavi/eristavi-lang/actions/runs/42470224168
#74 open; #121/#111 draft. No merge/promotion.
