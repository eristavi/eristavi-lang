# Adaptive owned graph registry

A bounded compiler trace on main commit 8dded48 found 6,901 of 12,000 CPU samples
in graph registry chain traversal. The final 10-second window attributed 73% of
samples to that loop. These partial windows do not establish whole-build costs.
A separate stable collector-entry snapshot captured 102,239 graph objects in an
8,192-bucket registry. Actual cumulative lookup work was 439,696,737 probes for
66,503,069 successful lookups, averaging 6.61 probes with a maximum of 39.

This change uses stronger address mixing for dynamic tables and grows the private table during sweep,
where chains are already being cleared and rebuilt. The initial 8,192 buckets
remain static and retain their existing hash. First growth occurs only above
65,536 graph objects; this avoids adding allocation/rebuild costs on smaller
heaps. Dynamic tables mix the address using xor shifts and one 64-bit multiply.
The desired capacity doubles until the pre-sweep object count is
at most twice capacity, capped at 134,217,728 buckets (1 GiB of table storage).
This is a sweep-time sizing target, not a guaranteed load bound between sweeps.
Allocation failure keeps the existing table. Successful growth replaces and frees
the previous dynamic table. An empty graph heap releases the dynamic allocation,
resets the mask, and clears the static table before reuse. Capacity is bounded
before byte scaling, and the table is nonowning metadata.

Full pointer comparisons remain mandatory on lookup. Marking, graph layouts,
roots, collector cadence, diagnostics, public value ABI and source semantics are
unchanged. No table allocation occurs while marking. Snapshot and backing-owner
records continue to use the same registry and tracing rules.

The new probes retain and find 140,000 objects through two successive growths,
reject interior addresses, reclaim the table on an empty heap, and reuse the
registry. A forced table-allocation failure exercises the same workload with the
original table. Five focused checks and a 13-check graph/Text/cache batch passed
(overlapping batches). Additional measurements are recorded below. These checks
do not qualify repeated owned self-builds; the earlier B-to-C timeout remains an
open milestone until a completed qualification proves otherwise.

## Final measurements and limits

The first implementation applied two-multiply mixing and early growth to every
heap. The 320-declaration probe regressed, so that policy was revised. The final
implementation retains the original hash/table through 65,536 objects and uses
one-multiply mixing after growth. Three alternating before/after runs produced
byte-identical IR reports: medians 2.127 versus 2.117 seconds for 160 declarations,
and 8.248 versus 8.271 seconds for 320. These small cases are effectively unchanged
within observed timing variation; no small-workload speedup is claimed.

A final diagnostic, stopped at the next stable collector entry after 30 CPU
seconds, observed 111,676 objects and 65,536 buckets. Across that run, 81,390,996
successful lookups performed 245,739,431 probes (mean 3.02; maximum 30), with no
misses. The original diagnostic averaged 6.61 probes (maximum 39). These are
cumulative observations from runs that reached different work/heap states, not a
fixed-workload compilation speedup. Diagnostic counter updates also perturb time.
All diagnostic instrumentation is excluded from production code. Compiler-body
assembly was held identical; only the linked runtime changed. No new 900-second
self-build was run. Final-revision hosted CI and owned integration are still
required before merge.
