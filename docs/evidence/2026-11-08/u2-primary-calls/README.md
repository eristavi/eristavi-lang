# Returned primary failures through File-owning calls

Latest verified implementation/test commit: `34faa47b07b52de061e1a94546748369cbdc693f`.
This documentation successor leaves source/test inputs unchanged.


8 November 2026. Base `46758d671d6f3d763067a737971fb5417b648612`.
Draft #121; #111 draft; U2 #74 OPEN. No release qualification claimed.

## Change

Replace the Function-wide primary-binding prohibition on defined checked calls
with the existing per-call SSA liveBefore guard. A future cleanup binding does
not imply a primary is active before a preceding call. The child can now fail
and the original returned context propagates through the parent's verified
resource cleanup. The caller may not pass/use a live primary during a defined
call without a future independently justified call contract.

`emitMixedFilePrimaryGroup` reuses the mixed-group admission/retained Plan
transaction. Assignments are exact 1-based owning member bindings, capped at
128 total and eight per member, privately linked to avoid bootstrap optional-
identity/generic empty-list limitations. Both preflight and emission use fresh
verification; duplicate sites and wrong member keys refuse. Default groups
allocate no new assignment nodes. No public ABI/frame/runtime adapter changes,
verification cache, timeout change, broad optimization or speedup claim.

## Exact observations

| Log | Result |
| --- | --- |
| focused-new.log | Initial new recursive/group tests: 2/2 PASS, 10.859 s, before first-primary-pointer instrumentation and assignment negatives. |
| final.log | Final code: 6/6 PASS, 39.671 s, 0 failures/skips. |
| live-call-refusal.log | Additional final negative: 1/1 PASS, 7.064 s. |

Final command:
`PYTHONPATH=.:tests python -m unittest
 test_u2_function_file_primary.U2FunctionFilePrimaryTests.test_recursive_child_failure_stays_primary_through_each_file_frame
 test_u2_function_file_primary.U2FunctionFilePrimaryTests.test_other_file_member_failure_stays_primary_through_caller_cleanup
 test_u2_function_file_primary.U2FunctionFilePrimaryTests.test_primary_group_assignments_refuse_foreign_missing_and_duplicate
 test_u2_function_file_primary.U2FunctionFilePrimaryTests.test_primary_chain_keeps_outer_owner_and_ordered_context
 test_u2_function_file_checked.U2FunctionFileCheckedTests.test_checked_file_owning_self_recursion_retains_each_frame_and_closes
 test_u2_function_file_checked.U2FunctionFileCheckedTests.test_file_owning_closed_checked_group_preserves_owner_across_child -v`.

Recursive generated execution tests depths 0/1/4/16; each uses clean, first-close-
only failure, and all-close-failure modes (12 executions). A different exact
File-owning member uses the same three modes (3 executions). Test-only runtime
instrumentation captures the first cleanup context; the final returned primary
must be that exact pointer after GC and all parent cleanups. Secondary counts
are zero for first-only failure and one per additional frame for all failures;
exact close counts and full post-scope resource/failure/Text/graph/handler
reclamation are checked. These are not a separate payload-per-frame ordering
oracle or deep RSS/pause/sanitizer evidence. Existing append-order tests cover
the primitive and primary-prefix ordering.

Group negatives reject missing, out-of-range, foreign-member and duplicate
assignments before assembly and check both Function owners retain no scratch.
The additional negative supplies a primary as an input to a defined call;
canonical input/signatures remain valid, but liveBefore refuses it before
output, confirming that safety guard was not weakened. Python compilation and
full patch check pass. inputs.sha256 pins final modified source/test inputs.

Development compilation initially exposed the bootstrap's requirement for an
explicit concrete group specialization even in clients using only single-body
entries. Added a nonexecuted shape anchor; ordinary import regression passes.
Known C-bootstrap identity-list pointer-qualifier warnings remain in actual
group logs. They are not waived and need separate qualification review.

## Deferred / recovery

Next remaining managed constructors and typed failure producers; explicit
already-active-primary call semantics/proofs, broader mutual/mixed combinations,
latest owned/C parity and hosted timeout failures, independent-origin/hostile-
root/allocator/sanitizer/physical evidence, main reconciliation and final four-
platform/full completed-batch gates. No broad/full/self-build CI manually
started and #51 stays paused. Automatic hosted runs after publish must be
checked independently; older success is not new-source qualification.
