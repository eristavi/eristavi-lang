# Whole-Function nested List constructor evidence — 8 November 2026

Branch: compiler/u2-whole-function-file-roots-20261107.
Base: 68c92c1e187978b806455c24ecf95746db3d94d9.
Verified source/test commit: 5a6ea63b7447c2aeeb2bac5afbe31f4ad9802ba6.
This documentation successor leaves source/test inputs unchanged.

Implemented List<List<i64>> and List<List<Text>> empty/copy/append/replace/
count/get/collect through canonical native Function lowering. Marker/descriptor
relationships and exact imported contracts are independently checked. Existing
List graph helpers and rooted SSA publication are reused. No runtime/public ABI
or ownership semantics change. Relationship admission reads the child descriptor
only after finding the exact matching carrier/descriptor pair; no measured
compiler-wide performance improvement is claimed.

Commands (Linux x86-64; PYTHONPATH=tests:.):

```
python -m unittest -v test_u2_function_nested_list
python -m unittest -v test_u2_function_list_text test_u2_function_import_integration.U2FunctionImportIntegrationTests.test_existing_list_snapshot_append_count_gc_in_whole_function test_u2_function_import_integration.U2FunctionImportIntegrationTests.test_mixed_text_list_calls_share_exact_whole_function_root_map test_u2_function_managed_native.U2FunctionManagedNativeTests.test_reject_mismatched_identity_descriptor_before_emission
```

final.log: **4/4 PASS**, 35.408 s, zero failures/skips.
regressions.log: **7/7 PASS**, 38.559 s, zero failures/skips.
final.log records the four nested-List methods on final source. regressions.log
records seven immediate dependency methods. The regression run overlapped the final
descriptor-read optimization and is dependency evidence, not a pinned full
regression pass for that last edit. The explicit final nested run verifies the
final source after that optimization. No unchanged large suites were rerun. focused.log records the preceding four-method pass
before that read optimization; initial.log is the initial one-method probe.

Native fixtures cover loop-produced inner Lists, independent snapshots, outer
copy/replace, retrieved-inner append without outer mutation, count and element
contents. They return 13, matching independent Stage-0 interpreter and current
native source references. Forced GC uses the established runtime harness and
checks final graph, Text, failure, handler and allocator reclamation. Descriptor,
marker, missing-inner, effects and argument-type negatives refuse before output.
Nested get/replace bounds preserve terminal source diagnostics. Subtests are
not counted as separate unittest methods.

Untested: arbitrary/deeper constructors, aggregate and typed FailureContext
producers, nested List combinations with checked recursion/File cleanup,
comprehensive hostile roots and allocator refusals, sanitizer/physical budgets,
current owned/C generator parity, hosted timeout gates and final four-platform
qualification. #74 remains open; #121/#111 remain draft. No broad/full/self-build
CI, #51 work or final platform qualification manually initiated.

Predecessor hosted CI was still in progress when checked:
https://github.com/eristavi/eristavi-lang/actions/runs/42431255401
That run does not qualify the new source. New-head hosted status is pending.
