# Issue #51 — actual Universal verifier temporary storage

**Measured; no production optimization adopted.** The largest production routine
uses **6,919,776 bytes of live initialization-mask backing** for 183,312 bytes of
logical word payload, plus **131,200 bytes of register classes** and **227,648
bytes of Flow tracking** at the end of its first verification. Its directly
measured allocation peak is **7,861,424 bytes**, while mask helpers generate
**751,790,768 bytes of allocation traffic**. Physical backing and repeated boxed
temporaries are both material; reducing the mask count alone does not solve the
per-access allocation cost.

Baseline main `4a07bc988cc57407635a4d81f21a92d5dfc74b55`, production qualified
PR #110. The complete handover and governing philosophy, semantics, relevant IR
contracts and CI policy were reviewed. Only opt-in diagnostic tools and records
were added. Compiler/runtime source, ABI, both verification passes, GC policy,
memory/work limits and the 90-second diagnostic cap are unchanged. No experimental
owned compiler self-build or new production qualification was run.

## Production routine: exact completed boundary

Owned compiler B compiled `src/compiler/ir_verify.eri`. Its first Universal
verification completed; its second was partial when compilation hit 90 seconds.
Function 161's completed first-pass endpoint independently agrees with the prior
UIR census: **R=2,306 registers, B=301 blocks, W=38 words/mask** and
**N=(2B+1)W=22,914 identity words**. These are real production measurements,
not extrapolation from the matching fixture.

| Structure at routine end | Actual allocated capacity | Distinct graph allocations |
| --- | ---: | ---: |
| Mask list and its backing owner | 1,048,704 B | 2 |
| Word record bodies | 2,935,328 B | 22,914 |
| Identity wrappers around words | 2,935,744 B | 22,914 |
| **All initialization masks** | **6,919,776 B** | **45,830** |
| Register-class list and backing owner | 131,200 B | 2 |
| Flow record bodies | 96,320 B | 301 |
| Flow identity/maybe/successor wrappers | 131,328 B | 1,026 |
| **These semantic roots together** | **7,278,624 B** | **47,159** |

The masks contain 183,312 logical u64 payload bytes: physical backing is **37.75×**
that amount. This is a representation ratio, not a promised reduction or speedup.
Register-class logical u64 payload is 18,448 bytes; the list uses tagged 32-byte
cells, geometric capacity and ownership headers. Each Word needs both its record
body and identity wrapper. Reused allocator blocks can be slightly larger than
the nominal request, which explains nonuniform per-word capacity.

| Allocation scope for this routine | Actual cumulative capacity traffic |
| --- | ---: |
| Mask-list construction/growth | 4,297,408 B |
| Word-body construction/detachment | 10,975,216 B |
| Word identity wrappers | 5,118,576 B |
| Mask helpers: words/fill/defined/define/copy/intersect | **751,790,768 B** |
| Register-class table construction | 483,968 B |
| Flow bodies and wrappers | 547,200 B |
| Remaining verification temporaries | 364,429,120 B |
| **Routine total** | **1,137,642,256 B** |

Of the mask-helper traffic, **749,286,528 B comes from 7,808,145 boxed-value-slot
allocations**; only 256 B remains live in that group at the endpoint. The rest is
short-lived allocator blocks. This group measures dynamic helper scopes rather
than all mask-related work; Word/list creation is separately attributed above.
Register-class traffic covers table construction. Integer temporaries from all
class reads cannot be uniquely separated from the remaining-verification group.

The routine has **7,686,192 B of source-site allocations still retained** at this
endpoint, including garbage and slots outside the semantic roots, and an exact
concurrent **7,861,424 B peak**. These quantities are maintained on every successful
allocation and actual free; the peak is **not a sum of category peaks**. The
register-class graph group alone peaks at 421,184 B during construction, versus
131,200 B semantically reachable at the final boundary.

Across all verifier scopes, the largest global peak captured before the final
record is **14,169,888 B**. This includes still-retained allocations from earlier
scopes and shared runtime growth allocated during verification. It is an exact
peak through that recorded boundary, and only a **lower bound for the full capped
run**. The cap yielded 508 complete records: 254 mask-ready, 253 routine-end and
one first-pass verification-end record. There is no large-source complete-output,
exit-GC audit or full-run peak claim.

## Completed source and independent fixtures

`typed_ir.eri` completes with byte-identical assembly against the independent
C-bootstrap compiler, with 134 routine verifications across both passes.
The production-run ledger records **267,043,968 B traffic / 439,152 B concurrent
peak**, and zero tracked live bytes at normal entry return, before extra audit GC.
A separate final-tool fixture run gives 267,043,744 B / 439,088 B. Minor capacity
differences reflect allocator reuse/binary layout; timings are not performance
evidence. Its largest-mask routine (46, R=69/B=13/N=54) has 16,000 B of mask
backing, 4,224 B of register classes and 9,408 B of Flow tracking at its second
endpoint.

Six public-API fixtures independently specify register/block counts. Each verifies
the same graph twice, matches C/owned plain/observed stdout `2\n`, has exact
R/B/N on all four snapshots and reclaims every tracked allocation after the
separate post-output audit. First-round completed semantic snapshots:

| Registers | Blocks | Mask words | Mask backing | Class backing | Flow backing | Direct routine peak |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | 4 | 9 | 2,944 B | 256 B | 2,880 B | 55,104 B |
| 62 | 4 | 9 | 2,944 B | 2,176 B | 2,816 B | 86,832 B |
| 63 | 4 | 18 | 5,760 B | 4,224 B | 2,816 B | 93,216 B |
| 67 | 8 | 34 | 11,040 B | 4,224 B | 5,744 B | 104,208 B |
| 135 | 12 | 75 | 23,712 B | 8,320 B | 8,448 B | 158,544 B |
| 2,306 | 301 | 22,914 | 6,915,136 B | 131,200 B | 213,088 B | 7,840,560 B |

The last fixture matches the production routine's shape but has different
instructions/CFG, so its traffic and peaks do not replace production data. Its
two-round ledger peaks at 9,419,904 B globally and has 9,157,120 B still tracked
after normal entry return; the first extra diagnostic collection reclaims all
of it. This shows allocation retention under the existing cadence, not a leak
or a reason to force extra collections in production.

Two negative observer controls PASS: incorrect graph-kind attribution and a
deliberately tiny observer invocation bound both refuse with event99 / exit125.
All category traffic/live/freed totals reconcile to invocation aggregates, and
all aggregate ledgers reconcile traffic = live + freed. Source hashes remain
unchanged. These are focused diagnostic checks, not production qualification.

## Method and accounting limits

The observer is allocation-free freestanding C linked only into disposable
emitted x86-64 assembly. It reads successful allocator blocks' capacity fields,
including the **actual 32-byte allocator header**, alignment and unsplittable
reuse remainder. Graph backing includes its 64-byte header, tagged cells and
ownership chain. Runtime descriptors and source schema checks validate the
current reversed nominal-field layout; unexpected types, formula/layout drift,
untracked ownership, overflow or observer bounds refuse the measurement.

The pointer map is **not a GC root**, and snapshots do not call identity-cache-
invalidating getters. Semantic snapshots count only the three current
verifier-owned roots and backing owners; they do not traverse input Block/IR
graphs. Allocation attribution lasts from successful allocation until real free,
including frees after the originating invocation has returned. Shared runtime
growth is accounted to sid0, rather than charged to a single routine.

Existing input IR, runtime allocations made before verification, fixed runtime
scratch, allocator arena slack and the whole call stack are outside this ledger.
The unmodified native routine frame reserves 4,192 bytes; instrumentation adds
32-byte scope saves plus hook/C call stack space. The observer's own separately
measured BSS is **18,907,552 B**, excluded from compiler allocation figures. Binary
layout and hook overhead can perturb allocator reuse, so these are instrumented
actual capacities, not an assertion of unchanged uninstrumented RSS or latency.

A separate **uninstrumented** completed `typed_ir.eri` compiler process has Linux
`ru_maxrss` **17,056 KiB**, with independent assembly parity. This is whole-process
RSS, including source IR and runtime/static storage, and cannot be assigned to
verification or compared directly with the observer's process RSS. Two explicit
GC audits occur only after output in diagnostic executables, outside measured
verification; they are not a production policy change.

## Evidence and next step

- [Summary](../evidence/2026-11-01/issue51-verifier-storage-summary.json).
- [Raw records, decoded ledgers, outputs, manifests and reproduction tools](../evidence/2026-11-01/issue51-verifier-storage.zip).
- Opt-in harness: `tools/probes/production_verifier_storage.py` and
  `tools/probes/verifier_storage_observer.c`.

Archive CRC and each file's SHA-256 were verified. The summary pins the archive
hash. The final decoder revalidates the production run; the final six-fixture
run also tests the removal of an unused C reporting function and the stronger
ledger checks. No production implementation input changed.

Next review a **bounded compact scratch representation plus a typed scalar
access path**: reducing retained graph count and per-access boxing together is
now supported by physical evidence. Design must first prove type validity,
escape/lifetime ownership, GC roots, exhaustion/fault behavior and portability,
while preserving independent malformed-input and mutation checks. This report
does not approve a particular implementation or revive rejected cross-block
projection. Issue #51 remains OPEN; U2/U3/U4 are unchanged; production remains
qualified PR #110. A new production change still needs independent correctness
and paired performance evidence followed by its prescribed final qualification.
