# Aggregate Lists and checked self-call integration evidence

Branch: compiler/u2-whole-function-file-roots-20261107.
Base: 47388598471fccf6c93bbbfaa7059f0d1484e3bf.
Verified source/test commit: 352b68b16b46c018b34ff0c31e6e7c7512a36e3f.
This documentation/evidence successor leaves implementation/tests unchanged.
Raw .log files are explicitly included despite the repository ignore rule;
the saved preceding value-aggregate logs are also retained in this successor.

Implemented two missing integrations, reusing completed work:

- Exact boxed ordinary List element admission and native imports support
  aggregate elements, multiple shapes, nested Lists and Text children.
- emitValuesChecked supplies existing aggregate layout bindings to checked
  self calls, retaining original class-1/class-5 publication and continuations.
  Save the caller's failure pointer before layout guards clobber RCX/RDX.

The independent reference exposed a bootstrap C typedef ordering defect for
nested Lists of records. Inner List declarations now precede outer declarations;
no source syntax or List semantics changed. Source/compiler full qualification
is still required before merge. Contract: UIR_U2_BOXED_LIST_NATIVE.md.

## Observed local results

- final.log: **17/17 PASS**, 121.449 s, zero failures/skips. Eleven new methods
  plus six immediate dependency methods. Actual generated native List loop,
  snapshots, multiple aggregate shapes/nesting, scalar/managed field contents,
  forced GC/final reclamation, exact descriptor/import/binding negatives,
  source-located terminal bounds, checked recursion/primary propagation and
  handler recovery pass. Existing aggregate/layout/nested/mixed-root and checked
  native/reference paths pass.
- checked-reference-final.log: **2/2 PASS**, 12.562 s, zero failures/skips.
  After the 17-method pass, strengthen only the recursive source oracle with
  parent-private List/record state and checked propagation. Rerun those two
  affected methods on unchanged implementation. Depths 0/1/5/32/64 exercise
  normal/failure paths and compare observable results against interpreter and
  current C-native source execution. Other methods' assertions are unchanged.
- checked-combinations.log: **3/3 PASS**, 16.896 s, preceding checked aggregate,
  aggregate List and handler-recovery probes. Recovery depths are 1/32.
- reference-fix.log: **2/2 PASS**, 8.336 s, independent new record/nested List
  and existing nested Int/Text source outcomes after typedef ordering fix.
- initial.log and checked.log retain successful first probes (8.773/8.413 s).
- focused.log retains the initial 5-method run: four passed and one failed
  because C typedef order named the outer nested record List first. That
  defect is fixed; failure is retained rather than omitted. No remaining
  focused failures. No assertions, timeouts or existing tests were weakened.

Source reference limits: ordinary record Lists and nested List outcomes agree
on 13. The canonical native envelope-with-Text-List composition has no new
source field annotation; its source oracle keeps the inferred List separately.
Recursive source oracle does store ordinary records in inferred Lists and
retains them through checked children, matching native counts/identity/error
contents. Native failure setup uses the existing saved-context runtime adapter;
compiler-generated typed failure construction remains pending.

## Commands and environment

Linux x86-64; regex 2026.9.29, unicodedata2 Unicode 17.0.0. PYTHONPATH includes
repository root, tests and the pre-existing pinned dependency site-packages.

```
python -m unittest -v test_u2_function_aggregate_list test_u2_function_value_aggregate.U2FunctionValueAggregateTests.test_nested_aggregate_snapshot_text_list_and_forced_gc test_u2_function_value_aggregate.U2FunctionValueAggregateTests.test_linked_layout_mismatch_and_out_of_table_are_terminal test_u2_function_nested_list.U2FunctionNestedListTests.test_nested_text_and_i64_snapshot_constructors test_u2_function_nested_list.U2FunctionNestedListTests.test_independent_source_snapshots test_u2_function_import_integration.U2FunctionImportIntegrationTests.test_mixed_text_list_calls_share_exact_whole_function_root_map test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_checked_recursive_normal_failure_edges_roots_and_reclamation
python -m unittest -v test_u2_function_aggregate_list.U2FunctionAggregateListTests.test_parent_private_aggregate_survives_checked_recursion_and_failure test_u2_function_aggregate_list.U2FunctionAggregateListTests.test_parent_private_list_of_aggregates_survives_checked_recursion
```

Full unchanged groups/smoke/four-platform suites and owned-generator repeatability
were not manually rerun. Prior local owned/C direct-group parity took 117.920 s
against 120 s on parent implementation 03b12c9, not this new revision; no new-head
owned parity or hosted timing success is claimed. No full-compiler owned
self-build, final release qualification or #51 work initiated.

Predecessor automatic CI was in progress when checked:
https://github.com/eristavi/eristavi-lang/actions/runs/42461868793
That run does not qualify these new inputs. #74 OPEN; #121/#111 DRAFT. Remaining
functionality and next recovery step are in HANDOVER.md and the contract.
