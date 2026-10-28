# Universal IR verification performance

This batch changes the verifier's implementation, retaining both verification
passes around unreachable-block removal and all existing checks and diagnostics.
It adds no syntax, runtime ABI change, unsafe memory access or target dependency.

## Implementation

- Build diagnostics only when their checks fail, including the detailed result
  register/class message. Successful checks still execute.
- Replace linked bit-mask lookup with a dense table of identity words. For `B`
  blocks and `W = ceil(registers / 62)`, the table has `(2B + 1)W` words: one
  shared scratch range and disjoint incoming/outgoing ranges for every flow.
  Copy the incoming mask into scratch before every transfer. No scratch mask is
  allocated during fixed-point iterations.
- Precompute the 62 safe signed-Int bit values once per verification. Retain the
  same intersection arithmetic, propagation order and convergence limit.
- Cache CFG successor references after validating them. Sparse block IDs retain
  their existing meaning; table size depends on block count, not the largest ID.
- Index function targets only after the existing contiguous-ID checks. Parse
  canonical ASCII `fN` symbols without repeated Unicode scans or formatting;
  preserve the prior numeric bound and rejection of leading zeros/non-ASCII.

All caches are local to the verification call. The public IR is not modified by
verification; checking a program again after mutation rebuilds the caches.
Structural validation still examines unreachable blocks before optimization.

## Correctness evidence

The focused batch ran 25 tests with one cross-assembler skip because local Clang
is unavailable. The new public-verifier probes check exact category, message and
source location across mask boundaries, partially initialized joins, loops,
exception successors, sparse IDs, cycles, malformed registers, invalid calls,
unreachable malformed instructions and mutation between verification calls.

The same 45-line oracle passed with the original and optimized implementations
as C bootstrap programs and native Eristavi programs. Native execution was checked
with both the bootstrap runtime and the unchanged, qualified owned runtime.
Ordinary CI additionally runs the native probes on Linux x86-64 and ARM64.

## Measurements

Measurements use baseline source `2c9b7d07f481e8ade3c7f9f5b446266a5ade9e4a`.
The native baseline compiler was relinked from the hash-verified assembly saved
by qualification #9, after checking its source manifest. The candidate was built
from a fresh bootstrap. Both use the same local bootstrap runtime object.
The owned microbenchmark uses the unchanged qualified runtime object with SHA-256
`f1f384cb6b2dd407f3f73474772ae38f85bd54f548d596429f3edbbdd2bb0103`.

The microbenchmark constructs 2,000 value registers, a partially initialized
diamond and 32 following blocks, then verifies the program eight times. Programs
run serially in ABBA order, with two samples per implementation/runtime. Process
CPU time and peak resident memory are captured with `wait4`; outputs must match.

| Native runtime | Baseline median | Optimized median | Ratio | Peak RSS baseline / optimized |
| --- | ---: | ---: | ---: | ---: |
| Bootstrap | 2.578 s | 0.850 s | 3.03x | 29.0 / 25.0 MiB |
| Owned | 22.167 s | 7.352 s | 3.02x | 9.25 / 9.25 MiB |

These are small paired benchmarks, not general language-performance claims.
Regenerate the workload with `tests/universal_verifier_cases.py:benchmark_program`.
Compiler inputs, assembly, raw command logs and JSON measurements were retained
with the local experiment.

A full fixed-source frontend compilation with the optimized native compiler
completed in 158.5 seconds, including 39.4 seconds in Universal IR optimization.
Its assembly exactly matched the qualified baseline SHA-256:
`b3f8938c9f0aece69832ab94f109a8268661116eeadadc8f22da2ad47047585a`.
The reference attempt reached a 300-second cap while still in that phase; it was
not repeated. Because that attempt did not finish, no exact whole-build speedup
is claimed. The optimized bootstrap process peaked at 1.28 GiB; a corresponding
baseline peak was not available from the terminated reference attempt.

## Qualification and limits

Run normal CI on the final revision, then request full qualification once for the
completed batch. That gate includes all three bootstrap self-builds and owned
integration, with saved traces and source identities. Read the successful logs
and verify the artifact comparisons before merging.

Owned microbenchmarks and integration do not establish repeated owned compiler
self-builds. That remains a separate explicit gate; the previous owned B-to-C
attempt on older source exceeded 900 seconds. Compiler emission also remains a
material cost after this optimization, so verifier timing is not total build time.
