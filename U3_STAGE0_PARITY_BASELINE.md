# U3 Stage-0 / production-native observable baseline

Checkpoint 2026-10-30. See issue #75 and `docs/architecture/ERISTAVI_U1_TO_U3_EXECUTION_PLAN.md`.

This **pre-U3** test preserves a small deterministic, frozen sample of the existing supported Eristavi language rather than pretending the new U1a/U2 scalar compiler has already been integrated. It reads accepted cases by name directly from the frozen `tests/fixtures/semantic_cases.json` without copying or modifying the user-visible language.

For each case, Stage-0 `erist run` and the existing native C bootstrap compiler are invoked separately from the same source-root. Exit code and stdout must match exactly, with Stage-0 expected to exit successfully. The two simplest cases also compare the existing Linux x86-64 direct native backend where the host supports it. Cases cover plain output, inferred functions, mutual recursion, List value copy and checked-error handlers. Other semantic diagnostic conformance remains covered by `tests/test_self_hosting_semantics.py` and the frozen corpus.

**Next U3 gate:** build the new direct AST+frozen semantic facts→typed UIR adapter in shadow mode, then compare its verification, source-origin records, program execution and diagnostics to this reference. Neither this test nor the existing legacy Universal IR emitter is the approved new typed UIR compiler. Do not switch production lowering or public artifacts until full U1b/U2 and native runtime/ABI conformance are independently qualified. No source syntax, compiler runtime, native backend, cache or ABI change is made in this PR.
