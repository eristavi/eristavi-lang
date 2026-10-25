# Native heap reclamation

> **Status: P0 production-hardening candidate for the Linux offline/native runtime**

The Eristavi source-language contract is unchanged. There are no ownership annotations,
manual frees, pointer syntax, finalizers, or new keywords. Ordinary values keep value
semantics, `identity` keeps explicit shared identity, checked failures retain their
existing contracts, and scarce external resources still close deterministically through
`with`.

## Scope

`runtime/native_gc_runtime.c` is the native-only reclamation layer used by the offline
Linux runtime candidate. It wraps the pinned `runtime/value_runtime.c` bootstrap asset
and implements non-moving mark-and-sweep reclamation for allocations reachable through
Eristavi runtime values.

The generated-C/reference route remains separate and keeps its existing arena behavior.
`ERIST_HEAP_STATS` also remains a separate diagnostic build: its allocation registry
intentionally retains every tracked allocation and therefore cannot be used as a tracing
reachability structure.

## Why collection happens at safe points

An aggregate is created before all of its fields have been initialized. Running a tracer
inside the allocator could therefore inspect incomplete `ev_value` storage. The native
wrapper instead collects only after pointer-ABI operations have completed and their
results have been installed in runtime slots/scopes. Externally constructed object data
is zero-initialized before its first possible collection.

The default collection interval is controlled privately by `ERIST_HEAP_GC_INTERVAL` and
can be reduced to one in hardening tests. It is not a source-language setting or public
ABI.

## Roots

A collection begins from the runtime state that can still be observed by the executing
program:

- active native value slots;
- active native scopes;
- verified Universal-IR root maps attached to those scopes;
- value-class roots (`valueClass == 1`);
- checked-failure roots (`valueClass == 5`);
- active checked/resource handler frames;
- the current global checked failure;
- temporary result roots explicitly carried across a collector safe point.

Root-map handler/scope administrative pointers are retained as runtime administration,
not interpreted as Eristavi values.

## Typed traversal

The tracer follows Eristavi runtime layouts rather than conservatively scanning arbitrary
payload bytes.

- `Text` marks its backing byte allocation.
- Text views mark the original Text backing allocation.
- nominal values mark their object header, field storage and every field value.
- `List` marks its object header, element storage and every element value.
- `maybe` marks its wrapper and contained value when present.
- `identity` marks its wrapper and contained shared value; cycles are therefore supported.
- file resources mark their runtime record, Eristavi path Text and runtime path buffer.
- user checked failures mark the saved failure object and typed Eristavi error payload.
- `std.files.FileError` marks its concrete message/path Text payload.
- secondary cleanup failures are traversed in order.

The collector is non-moving. Interior references used by mutation therefore remain
stable for the duration of an operation.

## Prefix append metadata is weak

Text concatenation and List append can preserve old snapshots while extending a backing
prefix. `eri_text_append_buckets` is an optimization index, not a language root.

During collection an index node survives only when its backing data allocation is already
reachable from an Eristavi value. Dead index nodes are unlinked before sweep. The index
can therefore accelerate later compatible appends without keeping otherwise dead Text or
List storage alive.

## Deterministic resources

Garbage collection does not replace `with`. File handles and future sockets or other
scarce resources remain governed by deterministic resource cleanup. The heap collector
only reclaims unreachable runtime storage after the language-defined cleanup path has
finished with the resource.

No finalizer semantics are introduced.

## Validation

`tests/fixtures/native_heap_gc.c` and `tests/test_native_heap_gc.py` force collection at
nearly every opportunity and cover:

- reachable Text nested inside a nominal value;
- prefix-backed Text remaining valid while rooted;
- weak prefix-index removal after the value dies;
- an unreachable `identity` cycle;
- saved checked-error payloads surviving collection;
- 10,000 iterations of transient Text/object allocation;
- bounded live/peak native heap measurements;
- zero tracked live blocks after all roots have been released;
- AddressSanitizer and UndefinedBehaviorSanitizer execution.

The Linux offline bundle is also built with this runtime candidate so repeated compiler
self-build and the no-Python/no-C-compiler application audit exercise the collector.

## Current boundaries

This is deliberately a bootstrap production-hardening collector, not a claim of final GC
architecture. Before a production release it still needs broader allocation-failure
injection, long-duration workload baselines, collector pause/throughput measurements,
and explicit target/runtime qualification.

The current implementation is single-runtime and stop-the-world. It is not generational,
concurrent, compacting, or incremental. Those properties are not required by the source
language and should be considered only if measurements demonstrate a need.

The runtime itself is still a C-origin bootstrap artifact. Replacing that boundary with
an Eristavi-owned runtime remains a separate toolchain-independence milestone.
