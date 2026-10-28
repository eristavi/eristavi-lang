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

## Function-local table construction

The typed lowerer previously walked the entire existing local table on every
append. A private per-function tail now makes each append O(1), reducing table
construction from O(L²) to O(L). Parameter construction starts with an empty
tail; body lowering seeds its tail from the existing parameters. The tail and
local indices span nested lexical scopes, while name bindings retain their
existing save/restore behavior. Public typed IR, declaration order and diagnostics
are unchanged. No runtime or value ABI changes are involved.

`lowering_benchmark_program()` in `tests/typed_ir_verifier_cases.py` creates one
parameter, 192 ordinary function locals, and three entry locals across scopes.
The qualified owned compiler from PR #48 and a candidate linked to the same
qualified runtime object compiled the same source with `ir --trace-phases`.
Four serial ABBA samples produced byte-identical reports. Captured stderr and
phase balance were checked within each command; incomplete captures were excluded.

| Typed lowering | Median seconds |
| --- | ---: |
| Previous append scan | 0.319 |
| Cached tail | 0.154 |

This is about 2.07× faster for that phase and workload. Whole-command timings
varied substantially in report serialization and unrelated phases, so no overall
compiler speedup is inferred. Existing specialization tests now check parameter
and nested-branch local order across Int, Float, Bool and Text specializations.

## Bounded owned-runtime probes after PR #48

The qualified owned compiler completed a 32-function scalar source in 9.0 seconds
and the typed-IR compiler module in about 12 seconds. The scalar source produced
identical assembly with the qualified bootstrap compiler. Universal IR optimization
was the largest phase in both small probes (about 3.7 and 3.5 seconds).

A larger `compiler/ir_verify.eri` probe was capped at 90 seconds. It completed
analysis in 45.1 seconds and typed lowering in 28.0 seconds, then timed out inside
per-function typed-IR verification. Structural validation completed in 3.9 seconds.
This is a partial compiler-module probe, not an owned compiler self-build or proof
that Universal IR construction dominates. No unchanged 900-second attempt was
repeated. Recursive analysis phases may overlap; their durations must not be summed
as exclusive work.
