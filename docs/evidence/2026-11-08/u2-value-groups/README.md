# Closed checked aggregate/producer group evidence

Branch compiler/u2-whole-function-file-roots-20261107.
Base 11702f30cdf440234cce448a74a91ffe856fa906.
Verified source/test commit: 2af590bfaefc3efbac08a4cac0041c63ac10cb94.
This documentation/evidence successor leaves source/test inputs unchanged.

The shared aggregate binding vector now reaches original closed-group preflight
and emission. Existing ordinary group API retains empty bindings; no group,
canonical SSA, runtime or failure implementation was recreated. See the new
UIR_U2_VALUE_GROUP_NATIVE.md contract for exact boundaries.

focused.log preserves an initial fixture-generation error: renaming the local
call variable also renamed ab.call to ab.callB. corrected.log records 2/2 PASS
(25.528 s) after fixing that fixture typo. Final tests strengthen siblings with
distinct codes and source references; final.log records their results. Existing
C identity-list qualifier warnings are retained; assertions/timeouts unchanged.
Logs normalize trailing whitespace only to satisfy the patch gate.

Final selection (PYTHONPATH contains repository/tests and pinned dependency
site-packages; Linux x86-64, regex 2026.9.29, Unicode 17):

```
python -m unittest -v test_u2_function_value_group test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_preflight_work_and_capacity_refusal_release_owned_plans test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_two_managed_results_cross_member_handoff test_u2_function_failure_producer.U2FunctionFailureProducerTests.test_constructs_typed_primary_without_failure_ingress
```

Actual mutual dispatch is checked via 42/52 leaf and 43/53 parent codes, not
assembly patterns alone. Depths 0/1/5/16/64 cover both outcomes, forced GC,
class-5 preservation, typed payloads and final reclamation. Interpreter/current C
mutual-source results agree. Invalid second-body origin and other group/binding
negatives refuse before all assembly. No full unchanged suites, owned compiler
self-build, owned generator repeatability, #51 or final qualification initiated.

Predecessor hosted run was in progress when checked:
https://github.com/eristavi/eristavi-lang/actions/runs/42468744031
No new-head hosted result claimed. #74 open, #121/#111 draft. Remaining File
combinations and broader qualification are recorded in HANDOVER.md.

The first combined final.log run passed group/refusal/handoff cases but failed
single-body generator bootstrap specialization for the new group core. A
nonexecuted concrete shape anchor, following the existing bootstrap pattern,
fixes that inference boundary without changing admission. verified.log records
the corrected final run. No claims of runtime/compile speedup.

Final verified.log: **5/5 PASS**, 51.725 s, zero failures/skips. Two new
methods and three immediate compatibility methods. No unresolved focused
failures; retained C qualifier warnings remain a known separate limitation.
