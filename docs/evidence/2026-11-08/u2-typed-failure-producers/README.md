# Typed FailureContext native producer evidence

Branch: compiler/u2-whole-function-file-roots-20261107.
Base: a72a24e5f2d4a6dd734a3aed2dcf1ed396ed2cda.
Verified source/test commit: 12835510a6260f241c6bac7279571f4b8c1d824d.
This documentation successor leaves implementation/test inputs unchanged.

Implemented exact canonical native capture of selected ordinary aggregate error
payloads, immediate existing class-5 temporary publication and original SSA
live-after publication before retirement. Existing saved-failure runtime handles
construction; no duplicate adapter, source syntax, ABI/frame or ownership change.
See UIR_U2_TYPED_FAILURE_PRODUCER_NATIVE.md for the bounded contract and limits.

## Observed results

- final.log: **10/10 PASS**, 89.189 s, zero failures/skips: six new producer
  methods plus four immediate aggregate/checked/mutual-order/reference methods.
- nested-payload.log: **1/1 PASS**, 7.655 s, zero failures/skips. Add only a new
  test for a saved payload containing a List of Text; implementation unchanged.
- focused.log: preceding **4/4 PASS**, 55.542 s; probe-fixed.log: **1/1 PASS**,
  7.900 s. These precede the final legacy-fast-path preservation and OOM/unchecked
  checks; final.log covers those changes.
- initial.log preserves the initial eight failing subcases: expected output was
  already correct, but my new test caller used the wrong scope-leave ABI and
  faulted during cleanup. Correct to the existing (scope, void-value) contract;
  all original reclamation assertions remain. No unresolved focused failures.

Native depth/Bool-only inputs provide no FailureContext ingress. The generated
Function constructs primary and discarded contexts, preserves beta/typed codes
through another capture and forced GC, then normal/checked recursive returns.
Depths 0/1/5/16/64 cover successful leaf return, newly created leaf primary code
42, and a retained parent primary code 43 after successful child return. The
external caller creates no failure, verifies typed matching/fields and one live
returned context, then audits complete reclamation. Interpreter and current
C-native source outputs match. Message ordinals 0/1/4 execute. Missing/incorrect
message/carrier/effects/version/kind/descriptor/signature/layout/LocId and an
unchecked entry refuse before assembly. Context allocation refusal is terminal
OOM, not a fabricated checked outcome. Nested payload cases retain List/Text
through the context alone on depths 1/5. Their exact extra payload layout is
canonical-native evidence, not a new source field annotation or full source oracle.

## Commands and input evidence

Linux x86-64, pinned regex 2026.9.29 and Unicode 17.0.0 unicodedata2, loaded via
the pre-existing dependency site-packages plus repository/tests PYTHONPATH.

```
python -m unittest -v test_u2_function_failure_producer test_u2_function_aggregate_list.U2FunctionAggregateListTests.test_parent_private_list_of_aggregates_survives_checked_recursion test_u2_function_checked_native.U2FunctionCheckedNativeTests.test_checked_recursive_normal_failure_edges_roots_and_reclamation test_u2_function_checked_group.U2FunctionCheckedGroupTests.test_mutual_frames_preserve_primary_and_ordered_secondary_context test_u2_typed_failure_context
python -m unittest -v test_u2_function_failure_producer.U2FunctionFailureProducerTests.test_saved_typed_payload_keeps_nested_list_and_text_alive
```

No timeouts/assertions/existing tests changed. No repeated full unchanged suites
or owned full-compiler self-builds. Current owned/C generator repeatability and
hosted timing were not manually rerun; no success claimed. Explicit raw log
inclusion bypasses the repository's .log ignore rule. inputs.sha256 records
current implementation and final test inputs.

Predecessor exact-head smoke CI SUCCESS:
https://github.com/eristavi/eristavi-lang/actions/runs/42463546118
That run does not qualify this new code. Final four-platform/completed-batch
qualification deliberately deferred. #74 OPEN, #121/#111 DRAFT; no merge,
production promotion or #51 work. Remaining functionality and exact recovery
step are in HANDOVER.md and the producer contract.

## Hosted patch-check correction

https://github.com/eristavi/eristavi-lang/actions/runs/42468562936 failed scope
job 128693690432 on a trailing space in initial.log's first test-status line;
smoke and matrix did not execute. Normalize that log line's trailing whitespace
without removing the failed evidence or changing implementation/tests/assertions.
The corrected head requires its own hosted result; none claimed here.
