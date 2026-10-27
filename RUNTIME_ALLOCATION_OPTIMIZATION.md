# Measured allocation and collector-index optimization

PR #42 passed CI #389 and owned integration before merging as
`49615aeef598d7895ba21ee93c3ecc7d78b31afb`. This batch continues from that runtime.
The source language, public value ABI, checked arithmetic and resource contracts
remain unchanged. The native frontend's 29-module source closure is unchanged.

## Investigation and retained changes

The review inventoried 63 compiler/runtime source files and followed measured costs
through checked memory access, allocation/free, slot pruning, graph/Text registries,
collector preparation/sweep, and runtime cleanup callers. This is a focused
performance/safety review, not a claim that every possible optimization is exhausted.

A new early full-compilation profile sampled 1,000 instruction pointers. Of 441
samples in checked 64-bit loads, 345 returned to the allocator region-validation
path and 75 to its next-region search. Collector interval-index construction and
registry lookup also appeared prominently. A follow-up 1,000-sample window after
the retained changes placed 30 samples in checked loads and 186 in graph-registry
chain traversal. The work reached within each window differs, so these fractions
are hotspot indicators rather than a whole-run speedup calculation. Sampling covered an early CPU window;
it does not establish the cost breakdown of a complete self-build.

Four changes were retained:

1. **Checked region lookup caching.** A 4,096-entry direct-mapped page cache sits
   between the existing last-region shortcut and the full region walk. Tags compare
   the complete page number; collisions use the existing fallback. Hits still pass
   through region magic, extent, block alignment, allocated-bit and size checks.
   Only successful frees populate the cache. Allocator regions remain mapped until
   release-all, which clears all cache state before releasing them. Added metadata
   is 96 KiB of nonowning BSS, with no extra allocator calls or block-layout changes.
2. **Geometric collector scratch.** The backing-owner interval index grows its
   requested capacity geometrically instead of reallocating at every small increase
   in graph count. Size scaling is checked; oversized doubling clamps to the exact
   validated requirement. Logical capacity is bounded by twice the required count
   at growth, with a minimum of 16 entries; existing allocator block reuse can have
   larger physical capacity. Scratch still releases when the graph heap empties.
3. **Pooled Text hashing.** The registry now mixes the full registered buffer base
   instead of only its page number. Multiple independent pooled buffers on one page
   no longer necessarily share a chain. Full-address collision comparisons and
   nonowning registry ownership remain unchanged; no extra hash-table memory is added.

4. **Graph registry sizing.** The registry uses 8,192 buckets instead of 4,096.
   Both tested input sizes benefited from this middle size; 16,384 buckets gave no
   consistent additional benefit across the two sizes. This adds 32 KiB of BSS;
   the bucket mask and sweep clear span change together. Exact membership checks
   and registry/sweep ownership remain unchanged. Total added fixed metadata for
   the retained page-cache/table changes is 128 KiB.

Additional graph/Text positive-lookup memoization was measured separately and
removed because it did not show a consistent benefit. The final implementation
contains neither speculative cache. Collector frequency, root categories and
tracing coverage were retained; validation checks were not removed.

## Validation

The broad runtime batch passed 34 checks. After the Text-hash change, 21
focused checks passed; after the final graph-table choice, 18 checks passed
(overlapping those batches). Three added regression probes cover:

- Interleaved allocation/free across 128 regions, bounded warm search work, cache-tag
  mismatch fallback, double-free/damaged-header rejection, release-all invalidation
  and reuse after teardown.
- Repeated interval-index preparation during growth, independently bounded allocation
  count, exact interior-owner lookup and scratch reclamation on an empty heap.
- Lookup of 256 independent pooled Text bases under a generous chain-probe bound,
  plus complete buffer/slot reclamation.

Existing checks cover OOM publication, root validation, graph cycles/depth, snapshots,
Unicode, Float values, file/process services and cleanup failures. Private callers
of free were reviewed for register use; the public calling convention is unchanged.
The suite contains 411 test methods. These checks are finite evidence, not a proof
of absence of all defects. Final-revision hosted CI and owned integration remain
required before merge.

## Native workload measurements

Three runs per size and profile used identical compiler-B assembly, changing
only the linked owned runtime. Input and every IR-report output byte matched.
Host-specific wall-time medians versus PR #42:

| Declarations | PR #42 runtime | This batch | Reduction |
| --- | --- | --- | --- |
| 160 | 4.975 s | 2.381 s | 52% |
| 320 | 34.565 s | 8.091 s | 77% |

A separate single 160-declaration run measured child-process peak resident memory
at 27,980 KiB before and 12,580 KiB afterward, with identical output hashes. This
includes runtime/allocator effects and does not establish a general memory bound.
The fixed page-cache overhead trades a small metadata allocation for fewer searches;
reduced scratch churn improves this workload's overall footprint despite that cost.

These are small native parsing/semantic/IR/report workloads, not completed compiler
self-builds. No additional 900-second attempt was started. Repeated owned compiler
self-builds remain unqualified, and the bootstrap runtime remains default. The next
qualification must use this final runtime; further optimization should follow
full-workload sampling rather than extrapolate these timings to universal speedups.
