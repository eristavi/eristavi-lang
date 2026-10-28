# Heap-scaled collection scheduling

PR #44 passed CI #393 (four test jobs) and owned integration qualification #7,
then merged as 67e074fe7079700d614a1ec7e1372f3080cfe915.
The unchanged 29-module frontend closure was checked against the fresh compiler-B
source manifest before reusing its assembly for the following runtime diagnostics.

## Diagnosis and rejected candidate

A bounded 120-CPU-second trace of the merged runtime found graph registry chain
traversal in 14.5% of the final window's samples, versus 73% in the earlier
pre-#44 trace. These windows reached different heap/work states; this is not a
whole-build speedup measurement. The newer trace reached about 264,000 live graph
objects. Clearing graph marks and sweeping together occupied 33.7% of the final
window. Most of the 8,368 collections in the first window happened during small
heap startup. Later windows still performed 4.7–15.9 graph collections per CPU
second, often with hundreds or a few thousand new graph objects per collection.
The existing budget was half the retained graph/failure/Text record count, with
a minimum of 128 safe points, but capped at 65,536 even for much larger heaps.

An epoch-marking candidate removed the routine mark-clearing traversal and passed
17 checks. Fixed-input IR timings showed no consistent benefit: 160 declarations
1.871/1.948 seconds before/after, 320 declarations 6.725/6.801 seconds (three runs
per profile), and one 640-declaration pair 28.151/27.712 seconds. Every output
matched. That candidate and its private epoch state are excluded from this change.

## Retained change

Retain the existing dirty-heap and safe-point gates and the 128-safe-point minimum,
but allow the existing half-live-count interval to continue scaling above 65,536.
Check both additions before dividing the combined graph/failure/Text count by two.
No mark, sweep, exact membership, root, object layout, public ABI, source-language,
or scoped resource-cleanup logic changes. Explicit full collection still performs
all tracing and reclamation immediately. The tests verify a 200,000-object live
heap receives a 100,000-safe-point budget, collection is deferred just below that
boundary and happens at the boundary, and an empty heap returns to budget 128.

A larger interval can retain unreachable memory longer. Record counts are not a
byte-based memory bound. The measurements below describe this compiler checkpoint,
not a universal memory limit or a repeated owned-self-build qualification.

## Validation and measurements

The completed runtime batch passed 25 checks, covering the new scheduler probe,
growth and reclamation, deep/cyclic graphs, roots, Text values, file/process
services, exactly-once cleanup, secondary cleanup failures and terminal OOM.
A tightened scheduler-boundary probe passed separately after adding the explicit
below/at-boundary assertions; the production implementation did not change.

A diagnostic comparison stopped both compilers at entry to the sixteenth lexer
invocation on the same full compiler input. It is a matched compilation prefix,
not a completed compiler build, and intentionally terminates at the checkpoint.
The first pair used 73.187 versus 59.934 CPU seconds (18.1% less); peak child RSS
was 110,896 versus 111,724 KiB. The compiler body and tracing hooks were identical;
only the linked runtime scheduling cap differed. A repeat using the final emitted
runtime, including checked budget additions, is recorded below.

The bootstrap runtime remains default. Owned B-to-C repeatability, C reproduction,
and the final offline audit remain unqualified until a full attempt completes.

Final-runtime repeat (candidate first, reference second): 71.047
versus 61.285 CPU seconds (13.7% less);
peak RSS 110,896 versus 111,720 KiB. Both reached the same
checkpoint. Two pairs are limited host-specific evidence, not a universal speedup.
Normal CI and owned integration are required on the final PR revision.
