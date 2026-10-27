# Independent small-Text storage

The Linux x86-64 owned runtime pools managed Text storage requests of 1–256 bytes.
A 16 KiB reservation contains a 64-byte slab header and sixty blocks, each with a
16-byte ownership/free-list header and 256 bytes of independent Text capacity.
Only the backing reservation is shared. Distinct Text constructions retain distinct
buffers; immutable-prefix sharing within one buffer keeps its existing rules.
Source syntax, type semantics and the 32-byte value ABI are unchanged.

## Ownership and access

Available slabs form an intrusive doubly linked list. A full slab leaves the list;
its first released block puts it back. Allocations first reuse returned blocks,
then consume uninitialized blocks. Block headers retain their owning slab and an
allocated sentinel. Exact block offsets and that sentinel are checked on release.
The final released block unlinks and unmaps the slab immediately. Empty slabs are
not cached, including during cleanup of unpublished constructor results. A live
block retains its 16 KiB slab until the last block in that slab is released.

Managed Text records keep the exact buffer base and storage capacity. Capacity 256
identifies a pooled slice; larger reservations retain their page-rounded capacity
and original base/length pair. Collector sweep and unpublished-output cleanup use
`erist_rt_text_storage_release`, which returns one slice or releases the original
large reservation. Registry entries continue to own buffers, never entire slabs
belonging to other Text values. Empty Text allocates neither a slice nor a record.

The raw storage foundation remains page-backed. Its verified memory IR and
reservation-pair provenance rules are unchanged. Managed byte-access wrappers
first check the slice offset, allocated block header and slab-relative block
position, then translate to the original slab base/length and checked byte offset.
The existing verified load/store helper performs the final reservation-bounded
access. Pool capacity is never supplied to that helper as a raw OS reservation.
These private helpers require live, runtime-owned input storage, as their existing
raw counterparts require real readable/writable reservations.

Requests larger than 256 bytes keep the existing reservation path. Concatenation
uses the same storage selector for new capacity; appending within an existing
buffer still writes only beyond its greatest published prefix. Older snapshots,
branched concatenation, Unicode views and embedded NUL bytes retain their contracts.

## Validation and measurements

The completed local batch passed 29 checks across raw storage, pools, capacity,
allocation failures, exact roots, Text lifetimes/views, Unicode, Float, graphs,
resources and cleanup. Two dedicated probes check hundreds of independent buffers,
bounds, reuse without another reservation, double return while a slab remains
live, interleaved empty-slab release, reuse after complete teardown, failed slab
growth with existing live buffers, and the 257-byte large-storage boundary.
The allocation-failure harness retains its thirteen original cases and adds three
cases with a preexisting live pooled neighbor. Failed copy/record publication must
return only the unpublished slice and preserve that neighbor; slot-allocation
failure must leave published registry/pool counts consistent.

The compiler token/report probe uses identical compiler-B assembly and input files,
changing only the linked owned runtime. Three alternating runs per size produced
these medians on this Linux x86-64 host; every output byte matched:

| Declarations | PR #38 runtime | Pooled runtime | Reduction |
| --- | --- | --- | --- |
| 200 | 1.339 s | 0.682 s | 49% |
| 400 | 3.032 s | 1.751 s | 42% |
| 800 | 10.159 s | 5.362 s | 47% |

On the 200-declaration probe, OS reservations fell from 90,979 to 2,478 (97% fewer)
and releases from 89,234 to 1,825. Before pooling, 89,747 reservation requests were
at most 256 bytes. Remaining reservations include root-index scratch and larger
Text/allocator storage. These are host-specific token/report measurements, not a
full compiler throughput or repeatability claim. Normal CI and owned integration
must qualify the final PR revision before merge.

A bounded full owned self-build attempt still timed out during B-to-C emission at
900 seconds. It reused only the previously verified compiler-B assembly, checking
its recorded hash and all 29 unchanged compiler source modules, and regenerated
the owned runtime emitter/object. This does not qualify compiler C or repeatability,
and the bootstrap profile remains default. A final targeted pool run also checks
null-input rejection before block-header access. Full-compilation phase profiling
is required before the next expensive owned rebuild.

A separate 30-second diagnostic run instrumented compiler function entries without
changing source semantics. Its trace reached module loading, parsing and semantic
analysis, but not typed-IR lowering or assembly emission within that budget. This
identifies an early profiling target; it does not establish which stage dominates
the complete 900-second run. The trace is diagnostic evidence, not qualification.
