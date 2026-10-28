# Typed-IR verification and lowering performance

Typed-IR verification remains mandatory before Universal IR construction. The
`verify` and `lower` APIs retain their existing behavior; optional tracing uses
`verifyWithTracing` and `lowerWithTracing`. Both native backends and the `uir`
command forward the trace flag. Successful untraced commands remain silent.

The `universal-lower` phase includes `typed-ir-verify`, with nested structural,
descriptor and function validation phases. `universal-lower-function` records the
actual construction work separately. Failures leave the active phase open and
preserve the original diagnostic. Subjects are JSON quoted.

## Local table ownership

Previously the structural verifier compared each local against every local in
every previous table, including earlier elements of its own table. For L locals
this required O(L²) identity comparisons and retained L temporary records.

The verifier now detects each table's cycles with slow/fast cursors, finds its
tail, then compares that tail against earlier nonempty table tails. Two finite
singly linked lists share any node exactly when they share their tail. This
requires O(L + F²) comparisons and O(F) temporary records for F functions. It
keeps the existing error category, message and source location. No identity or
index assumptions are introduced, no local tables are mutated, and no safety
checks or verification passes are removed. Other verifier scans remain.

Regression coverage includes self cycles, two-node cycles, cycles with a prefix,
shared heads, distinct heads with a shared tail, disjoint and empty tables, exact
shared-table diagnostics, repair followed by repeated verification, and native
execution of the malformed-IR oracle. Existing node-mark cleanup is preserved.

## Bounded measurement

`tests/typed_ir_verifier_cases.py::benchmark_program()` constructs 64 functions
with 8 ordinary local declarations each and verifies the same program 3 times.
The baseline uses the old local ownership loop with otherwise identical traced
verifier source. Both harnesses are emitted by the same seed and statically
linked against the same previously qualified owned runtime object using GCC.
Both print exactly `ok`. There is no performance threshold in CI.

Two serial samples per implementation, in ABBA order, measured:

| Implementation | Median wall seconds | Peak resident memory |
| --- | ---: | ---: |
| Previous local ownership scan | 6.059 | 9,344 KiB |
| Cycle detection and tail comparison | 1.409 | 9,344 KiB |

This is about 4.30× faster for this verifier workload. It is not a full compiler
self-build measurement. Host scheduling and memory reclamation affect timings.
An earlier 2,048-local baseline probe hit its 60-second cap and was not repeated.
The smaller completed comparison is the basis for the figures above.

## Qualification boundary

The preceding owned compiler attempt timed out at 900 seconds while the broad
`universal-lower` phase was active. That trace could not distinguish verification
from construction, so it does not prove which subphase dominated. The preceding
completed phases were analysis (224.8 seconds) and typed lowering (340.1 seconds).
This batch improves a proven quadratic scan and exposes the missing phase detail;
it does not establish full owned compiler repeatability. Normal CI and full
qualification are required before merge. A further owned self-build is justified
only after the completed batch passes those gates.
