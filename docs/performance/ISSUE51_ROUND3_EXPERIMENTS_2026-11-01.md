# Issue #51 — production compiler optimization round three

**Disposition: investigation completed; six private candidates NOT ADOPTED.**
Production remains the qualified PR #110 implementation. No compiler/runtime
source, ABI, language behavior, memory limit, GC cadence or verifier gate was
changed on main. Full optimization is **not complete**: the large source still
reaches its unchanged 90-second diagnostic cap. U2/U3/U4 remain separate.

Baseline: `00b2043e6e4c612b0ebbc4e78f338698a6d49345` (after qualified #110).
Work followed the complete handover, governing philosophy/semantics, production
Universal IR/verification contracts, typed-UIR and semantic architecture and CI
policy. Experiments used private source copies or disposable emitted assembly.
C bootstrap builds owned compiler B; B never compiles frontend.eri or builds C/D.

## Current-source attribution

The bounded baseline probe completed small `typed_ir.eri` with exact independent
C-bootstrap assembly parity: plain owned B 2.119849s, instrumented 2.571422s.
These are different executables, **not a speed comparison**. Large `ir_verify.eri`
plain and instrumented commands were both censored at 90s.

At the large source's first completed Universal verifier interval, the observer
recorded 7,443 transfers, 5,369 intersections, 14,886 mask copies, 54,122 define
operations, 24,306,776 boxes, 197,526 graph allocations and 199 GCs. It prepared
the interior-owner index 199 times for 223 owner queries. Inclusive observed GC
elapsed was 36.827100s within the 44.494885s observed verifier interval. Observer
overhead and overlap prohibit treating these as uninstrumented CPU fractions.

A separate 5ms in-process SIGPROF diagnostic collected 16,757 samples during a
90s capped large-source run. The sampled small source emitted exactly the
independent reference assembly. Main large-source sampled locations:

| Location | Samples | Share |
| --- | ---: | ---: |
| Clear graph marks | 2,023 | 12.07% |
| Sweep graph objects | 1,820 | 10.86% |
| Fill graph interval index | 1,750 | 10.44% |
| Graph object marking entry | 1,575 | 9.40% |
| Graph exact-find chain | 1,449 | 8.65% |
| Checked memory load helper | 1,151 | 6.87% |
| Graph index sift loop | 1,137 | 6.79% |

These are approximate exclusive instruction-location samples, not additive
inclusive function timers. Sixteen-byte histogram bins can straddle symbol
boundaries. Full symbol/function rankings and raw histograms are preserved.
The large sampled run exited 124 at the cap and has no complete-output claim.

## Experiments and decisions

| Private candidate | Correctness evidence | Measurement and disposition |
| --- | --- | --- |
| Dirty-flow scheduling | Existing public verifier oracle, C and owned, baseline/candidate exact errors/output | Small pilot 1.869458→1.969271s; large both censored. No convincing gain; not adopted |
| Hole-based heapsort sift | 128 independent unsigned-key sorting cases, including empty/singleton/duplicates/extremes; exact compiled output | Small pilot 1.771283→1.738715s; separate semantic-types module 2.477930→2.838964s. Inconsistent one-pair signal; not adopted |
| GC mark epochs | Exact public verifier output; rooted/dead objects, repeated marking without sweep, forced 64-bit wrap reset and final reclamation passed | Small pilot 1.720189→1.740071s; medium 2.477930→2.661190s; large censored. Not adopted |
| Adaptive interior index | Exact public verifier output; original validated linear owner path for the first queries, preparation at query four | Small pilot 1.994658→2.124649s; large censored. Not adopted; no production safety qualification claimed |
| Project only cross-block registers, all routines | Public C+owned verifier oracle; first large verifier counters completed | Five pairs: **6.509% slower**, zero favorable pairs. Not adopted |
| Projection only at ≥64 blocks | Public C+owned oracle plus 20 independent initialization/error/location cases on baseline/candidate C+owned | Five pairs: **2.254% slower**, two favorable pairs. Large censored. Not adopted |

Single-pair results select or reject pilots; they establish neither a general
regression nor a speedup. The common-medium comparison is one serialized pass,
not a replicated performance result. Counter and timing scopes are distinct.

### Projection evidence and limit

The independent C-bootstrap UIR census found that the heaviest routine has 2,306
registers and 301 blocks, but only 120 registers occur in multiple blocks.
Its existing masks contain 22,914 identity words. A cross-block projection could
reduce that component to 1,206 words, before counting its new per-register state.
The original full large workload has 35,438 mask words. Merely dropping registers
never used as operands would only reduce that to 32,678, so that weaker candidate
was not implemented.

The all-routine projection actually reduced the first completed large verifier
interval from 24,306,776 to 16,186,747 boxes (−8,120,029), graph allocations from
197,526 to 92,696 (−104,830), and GCs from 199 to 170. These are operation counts,
**not live bytes, peak memory, RSS or a full compilation speedup**. Additional
classification/lookup and local-state work failed the small compilation timing
test. Instrumented wall intervals must not substitute for paired timing.

| Five alternating small-source pairs | Baseline median | Candidate median | Favorable pairs |
| --- | ---: | ---: | ---: |
| All-routine projection | 1.718869s | 1.830758s | 0/5 |
| ≥64-block projection | 1.754298s | 1.793846s | 2/5 |

All twenty timed compilation outputs equal the independent C-bootstrap assembly
for the identical target path/root. Timings are serialized, fresh-process,
alternating baseline/candidate on one Linux host and the identical owned runtime.
CPU user/system samples and exact compiler hashes are retained. Baseline C tools
were built with GCC -O2; private projection C bootstrap tools used GCC defaults.
Those C executables supply correctness and emit fixed native B assembly; their
execution speeds are **not compared**. No C optimization flag is applied to the
timed owned assembly binaries. This is local evidence, not a cross-platform
performance certification or a claimed C/owned runtime speed ratio.

The 20 extra projection checks exercise the ≥64-block path, sparse definite
initialization across 62-bit boundaries, loops/handlers, local read-before-write,
zero projected registers, cyclic operands and exact original diagnostic locations.
The source algorithm retained structural/dead-block validation and fresh analysis
per invocation. Passing these checks does not justify shipping a slower candidate.

## Evidence and recovery

- [Machine-readable summary](../evidence/2026-11-01/issue51-round3-summary.json).
- [Lossless experiment archive](../evidence/2026-11-01/issue51-round3-experiments.zip):
  raw boundary records, sample histograms, symbol rankings, paired CPU/wall
  measurements, source/runtime patches, original harnesses, logs and per-file
  SHA-256 manifest with explicit recovery paths. The summary pins archive SHA-256.
- Archives contain private experiments, **not installed production code**. Recover
  against the pinned baseline and map the recorded task paths to fresh scratch.
  Reuse relevant valid evidence rather than automatically repeating capped runs.

## Next engineering boundary

Issue #51 remains OPEN. A meaningful next implementation must reduce the physical
cost of verifier scratch without adding per-access boxed state. First measure
actual owned capacity and allocation sites for mask words, register classification
and their temporary values separately. Then review a bounded compact storage or
backend-private scalar path with type/escape/liveness/GC-root/exhaustion proofs.
The current universal boxed representation is a measured concern; this round does
not prove a particular replacement or a compiler-wide causal speedup.

Do not revive these unchanged rejected candidates or alter collector thresholds
as a timing shortcut. Keep both Universal verification passes, all malformed and
same-revision mutation checks, original ABI/source/fault/cleanup behavior and
resource ceilings. A new production implementation requires independent paired
oracles/timings and one final exact-head full CI plus prescribed qualification.
No expensive final qualification or experimental owned full self-build was run
for these unadopted private experiments. All probe processes have completed.


## Publication authorization

The user explicitly approved publication of the full handover and raw experiment
archive to the public project repository and instructed that project records
should always be published routinely. The previous automatic-review block is
historical. This documentation/evidence batch contains no production source
change; verify the remote commit/ref before declaring publication complete.
