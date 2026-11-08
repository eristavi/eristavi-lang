# Canonical whole-Function List<Text> constructors

Latest verified source/test commit: `2d01be312587f6e1d114d9bcb8955604ea7f30f8`.
This documentation successor changes no compiler/test inputs.


8 November 2026. Base `443ac14c60780b2be2e0dadfc0936f9fc8fbf78a`.
Draft #121, #111 draft, U2 #74 open. This is bounded development evidence.

Exact typed symbol/version/effects/signature admission and managed element
marker gate now connect List<Text> to the existing whole-Function emitter.
Runtime helpers, snapshot behavior, class-1 roots and source-fault formatting
are reused. Text elements remain boxed Text slots; no i64 boxing/unboxing.
Nested List and user-managed-aggregate/failure producers remain unimplemented.
No new executable IR, runtime adapter, public ABI or frame allocation.

`final.log`: **6 methods passed / zero failed / zero skipped, 31.631 seconds**.
`focused.log`: first two new methods passed, 13.759 seconds, before independent
reference and bounds cases were added. Python compilation and patch check pass.
Inputs are pinned in inputs.sha256.

Final command:
`PYTHONPATH=.:tests python -m unittest test_u2_function_list_text
 test_u2_function_import_integration.U2FunctionImportIntegrationTests.test_existing_list_snapshot_append_count_gc_in_whole_function
 test_u2_function_import_integration.U2FunctionImportIntegrationTests.test_mixed_text_list_calls_share_exact_whole_function_root_map -v`.

The generated canonical program creates beta Text, appends it into a growing
List loop, keeps an old one-element snapshot, copies a three-element List,
replaces the copy's first element with lambda Text, collects, and compares both
original and replacement contents. It returns 4 only when content checks pass;
the caller asserts that result and full post-scope reclamation. Original and
copied lists remain independently rooted across allocating helpers and CFG GC.
Independent source fixture uses ordinary literals/List mutation and is executed
by Stage-0 and current C-native; both output 4. Out-of-range get exits with a
terminal source-located fault. Wrong descriptor, effects and argument type
reject before assembler output. Existing i64/mixed-root regressions pass.

No benchmark speedup/physical-memory claim. Original metadata caps remain;
Text marker selection scans at most eight selected carriers and adds seven
fixed import names. No unneeded i64 boxing of Text is emitted. Full current-head
owned/C generator parity, hostile/fault/sanitizer/physical evidence, broad smoke
and four-platform/completed-batch release gates remain pending. No expensive
workflow was manually started for this batch. Any automatic CI result after
publication must be inspected independently; issue #74 is not accepted.
