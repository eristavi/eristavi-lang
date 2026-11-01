# U1b fixed-depth word-read optimization — 1 November 2026

Status: QUALIFIED / MERGED in PR #106; U1b #73 closed/completed. Five pairs, 12 focused checks, local smoke 49/49, physical backing and independent scaling PASS. Final four-platform/full qualification PASS. Follow HANDOVER §77.

## Cause and selected change

The corrected full linked U1b profile measures repeated verification plus boxed
scalar/helper amplification, not GC as the main time consumer. In one complete
fixture, 538,206 radix traversals read 3,229,200 current children and the generated
program created about 920 million boxed values. Counts cover the full fixture's
successful and deliberately refused/cancelled attempts, not one user execution.

The word store is a fixed six-level radix-16 directory with sixteen-word pages.
Its creating pageAt() had also handled every get/set with create=false. That paid
for loop condition/divisor updates and creation-mode tests despite a known fixed
noncreating topology. The bounded candidate adds a private readPath() for get/set:
resolve the CURRENT root; at each of the original six levels charge one work unit,
read the current selected child, require its presence; finally require the current
page. Push continues using the original creating path.

For pageIndex=index/16, the same child ordinals are computed in order with divisors
1048576, 65536, 4096, 256, 16, 1, modulo 16. The loop unrolling has no cache,
retained page pointer, builder trust flag or cross-invocation verification reuse.
Every subsequent read observes any changed root/child/page. Range/owner/lifetime,
phase/work/cancellation and frozen-write checks remain at their existing boundary.
Get/set still charge exactly seven work units. Missing root/child/page and each
quota refusal retain their old order, categories and consumed work.

No U1 record or Metadata/Function/Words layout, public value ABI, source vocabulary,
collector schedule or memory/work policy changes. Qualification owner ceilings
remain 8 MiB peak/64 MiB traffic. Allocation traffic, retained owner backing and
process RSS remain distinct measures.

## Independent behavior and failure checks

All 12 focused checks passed after one new fixture's optional-narrowing repair:
C/owned foundation and exact owner-poll/work contracts; radix boundaries across all
levels through 33,554,431; sparse malformed path detection at root, each child and
page; same-object mutation/restoration and frozen/closed reads; exact consumed
work/traffic on allowances 0–6; linked stale/signature/foreign-owner/malformed dead
and uncalled bodies; mid-execution cancellation and terminal bootstrap allocator
refusal. The sparse fixture deliberately materializes selected paths to test every
radix digit without allocating millions of unrelated records; it is not a claim
that normal append-only construction creates sparse stores.

## Five paired uninstrumented native executions

Baseline: c2423d5 word source, already containing the qualified same-owner poll
optimization. Candidate source SHA-256:
`dfa8a1a61dee1a4be0ddb5fb821c54098df80de33e705647b9619d0b224be60f`.
Both use identical generated owned runtime, unchanged full fixture, exact independent
C-bootstrap expected stdout/stderr/exit and fresh native processes. Run order is
AB/BA/AB/BA/AB; no concurrent native builds. Binaries were built/pilot-run; OS page
caches were not flushed or controlled. Local Linux x86-64 GCC 13.3, -O2.

| Pair | Order | Baseline s | Candidate s |
| --- | --- | ---: | ---: |
| 1 | AB | 59.714289 | 54.709537 |
| 2 | BA | 59.603015 | 52.066750 |
| 3 | AB | 61.790446 | 55.893081 |
| 4 | BA | 63.126694 | 54.983744 |
| 5 | AB | 62.998066 | 55.121805 |
| Median | | 61.790446 | 54.983744 |

All ten executions correct, all five pairs faster. Ratio of medians 0.8898422:
11.0158% lower wall for this workload. Pairwise improvements 8.38–12.90%. Raw
CPU/RSS/output/source/runtime/binary hashes are in
[paired evidence](../evidence/2026-11-01/u1b-fixed-path-five-pairs.json).
Whole-child RSS 100,856 KiB in both may include inherited launcher high-water pages;
this is not owner heap attribution. A separate one-pair pilot is preserved as
historical development evidence, not substituted for these five pairs.

The current production frontend's transitive import closure contains no compiler.u1
modules. Thus this is reference UIR storage/verification improvement, not production
source-compilation speedup, U3 promotion or removal of the historical 830× cross-runtime
disparity. Do not multiply this result by unrelated historical ratios.

## Instrumented cost comparison

Separate full profiles both pass exact output and 231-snapshot accounting. Their
instrumented clocks are not a speed comparison; compare reconciled event counts:

| Measure | Baseline | Candidate |
| --- | ---: | ---: |
| Successful allocator entries | 951,197,434 | 918,504,253 |
| Boxed value creations | 919,544,101 | 886,851,050 |
| Cumulative actual allocator capacity traffic B | 76,185,950,512 | 73,569,249,040 |
| Slot collections | 442,049 | 198,485 |
| Current radix-child reads | 3,229,200 | 3,229,200 |
| budget.work calls | 3,794,180 | 3,794,180 |
| budget.active calls | 8,278,710 | 8,278,710 |
| Verifier reads | 152,310 | 152,310 |

Budget polls and get/set/push counts are also identical. About 32.69 million
unnecessary boxed temporaries and 2.62 GB cumulative capacity traffic are removed;
no checks were deleted to obtain the improvement. Physical allocations/traffic are
not modelled UIR-owner charges or simultaneously live RAM. The generic evn_copy
counter includes managed values, not only numeric scalars. Raw lossless compressed
records, schemas, hashes and summaries are in the evidence directory.

## Remaining work and release boundary

Smoke/actual backing and final four-platform CI plus full bootstrap repeatability/offline and owned integration all passed for the exact final revision.
Experimental full owned compiler self-build remains excluded. A separate bounded
current source-compiler diagnostic continues #51; it is not before/after evidence
for this U1-only source change.

Larger scalar unboxing needs typed-region, alias/escape/liveness, root-map and
allocation-exhaustion proof that the current generic boxed backend does not yet
provide. Shared type validation needs an invocation-owned immutable-context proof.
Both remain explicit #51 follow-ups; no speculative backend rewrite or trust cache
is adopted. U2/U3/U4 stay separate. U1b may be accepted only as its qualified bounded
reference scope with these limits explicitly recorded, not as an optimized production
compiler or completion of all performance work.

## Final local acceptance and bounded source-compiler evidence

Local expanded smoke passed 49/49 in 168.513s. Forced-collision stress peak
7,830,912 B and traffic 21,973,968 B remain within original 8 MiB/64 MiB gates.
All tagged backing reclaimed, including 6,654,368 B across 16,938 stress objects.
U1b type/value backing (44,448 B metadata; 22,720 B function) fully reclaimed.
Five independent physical scale points passed: width 8/32/128 at depth 2, depth
2/8/32 at width 8. Raw owner/scaling data are under evidence/2026-11-01/.

Current owned frontend B was bootstrap-built once (15.152s assembly/link path),
then compiled typed_ir.eri once in 2.186s with exact bootstrap assembly hash
172769263e830e6bb555926612972f8b807b8a6f9261e0ca88087165f135cfb7. Inclusive
phase observations: analyze-project 0.459s, typed lowering 0.297s, typed verify
0.427s, universal lowering 0.588s, universal optimization 0.529s. Nested phases
overlap; do not sum them as independent work. Child RSS 17,016 KiB is whole
process, not owner backing.

The larger ir_verify.eri attempt reached the UNCHANGED 90-second cap during
old Universal IR optimization. Completed inclusive phases include analysis
10.519s, typed lowering 6.506s, typed verification 8.966s and universal lowering
24.960s. It is censored, with no complete output parity or total-duration claim.
No retry or raised watchdog was used. All source hashes remained unchanged,
and B never compiled frontend: no excluded full owned self-build. Raw phase
records/manifests are retained as u1b-source-compiler-* evidence. This fulfills
the current bounded diagnostic part of #51 and identifies remaining work; it
does not close #51 or establish source compilation speedups from the U1 change.

Disposition: this bounded U1b reference-storage improvement is accepted after passing exact-head four-platform/full qualification. Keep much larger boxing and
current production universal-optimizer work explicit in #51, without promoting
U3 or weakening verification/resource gates.


## Final hosted qualification and merge

Exact qualified head `bd0a159975d73239f87300debce89c453a59ebb1`; [CI 41313784760](https://github.com/eristavi/eristavi-lang/actions/runs/41313784760) and [qualification 41313784884](https://github.com/eristavi/eristavi-lang/actions/runs/41313784884) both SUCCESS. Full suites: 491 discovered each, Linux GCC/Clang 8 skips, ARM64 118, macOS 127. Three bootstrap C/D repeatability/offline audits passed with unchanged sources. Owned static/offline integration passed; experimental owned frontend self-build intentionally skipped and not certified.

[PR #106](https://github.com/eristavi/eristavi-lang/pull/106) merged at `b86d54f2f6268d12831bb0b09f3016b1dd3c1f67`; tested and merged tree `e81f594294f4c0700a0a572ec4434742199d4573` match, unchanged main base and ordinary two-parent merge. U1b #73 closed/completed under the explicit reference boundary; #51 remains open. Machine-readable final qualification evidence: [u1b-final-qualification.json](../evidence/2026-11-01/u1b-final-qualification.json). Postmerge documentation does not alter qualified code, tests, tools or workflows and requires only lightweight checks.
