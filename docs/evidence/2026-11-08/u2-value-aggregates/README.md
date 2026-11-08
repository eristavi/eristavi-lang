# Canonical value aggregate native integration evidence

Branch: compiler/u2-whole-function-file-roots-20261107.
Base: be626b9ba48d2cee93701df94537b09132292d11.
The documentation successor pins the exact verified source/test commit.

New functionality: private ordinary aggregate descriptor and root admission;
canonical make/get/set native lowering through existing graph helpers; nested
aggregate/Text/List snapshots, exact linked runtime layout checks, existing
root temporary protection and source-value independence. Source-language type
syntax and semantics are unchanged. See UIR_U2_VALUE_AGGREGATE_NATIVE.md for
explicit supported fields, binding caps and limitations.

Environment: Linux x86-64; pinned regex 2026.9.29 and unicodedata2 Unicode 17.0.0
loaded from the pre-existing environment's site-packages using PYTHONPATH,
along with tests and repository root. Restoring dependency visibility was
required after resumption; no dependency versions or assertions changed.

initial.log records the first successful generated native probe after fixing a
local result-index typo and concrete bootstrap specialization for empty native
layout vectors. focused.log records the subsequent four-method pass (47.488 s).
regressions.log records predicate fields plus three immediate dependencies:
4/4 PASS, 23.860 s. final.log: **20/20 PASS**, 312.618 s, zero failures/skips, on final source.
This includes six new aggregate methods, three immediate descriptor/opaque/
mixed-root dependency methods and eleven checked-group compatibility methods.
The latter verify unchanged checked paths after the common private compile-call
signature extension; they do not reimplement those completed features.
Owned/C direct-group generator output parity passed locally with
U2_DIRECT_GROUP_OWNED_GENERATOR_SECONDS=117.920 against the unchanged 120-second
limit. This is one local observation with little margin, not hosted repeatability
or a resolution of all previous timeout gates. Subtests are not separate methods.

Final command (with the dependency site-packages prefix described above):

```
python -m unittest -v test_u2_function_value_aggregate test_u2_managed_types test_u2_function_managed_native.U2FunctionManagedNativeTests.test_reject_managed_producer_in_dead_block_before_emission test_u2_function_import_integration.U2FunctionImportIntegrationTests.test_mixed_text_list_calls_share_exact_whole_function_root_map test_u2_function_checked_group.U2FunctionCheckedGroupTests
```

No focused failures remain. Initial dependency visibility, local result-index and
empty-layout specialization issues were corrected before this final pass.
No timeouts, assertions or existing tests were changed.

Native outputs match expected 7 and final graph/Text/failure/handler/allocator
reclamation. Independent Stage-0 and current-native source references also
produce 7. Negative input cases must refuse before .section output. Linked
layout defects must exit with terminal runtime faults, not checked failures.
Missing native symbols are link-time failures. The linked runtime table is
trusted metadata; forged arbitrary native field-table pointers are out of scope.

No claim of full U2 qualification. Remaining: additional field/value families,
Lists containing aggregate elements, typed FailureContext producers, aggregate
checked/recursive/File combinations, complete allocator/hostile-root/independent/
sanitizer/physical evidence, current owned/C parity/hosted timeout gates, branch
reconciliation, four-platform CI and completed-batch qualification. No owned
full-compiler self-build, final qualification or #51 optimization work initiated.

Predecessor smoke CI succeeded on be626b9:
https://github.com/eristavi/eristavi-lang/actions/runs/42432076793
This does not qualify the new source. New-head hosted CI is pending publication.
