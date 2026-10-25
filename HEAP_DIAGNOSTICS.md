# Heap accounting foundation

This is an opt-in diagnostic build facility for `runtime/value_runtime.c`.
It measures allocations; it is deliberately separate from the native tracing
collector in `runtime/native_gc_runtime.c`. The frozen language philosophy, source
syntax and ownership semantics are unchanged.

## Use

With a matching native offline bundle and repository checkout on Linux:

```sh
/path/to/bundle/bin/erist build-asm app.eri -o /tmp/app.s
cc -std=c11 -O2 -DERIST_NATIVE_RUNTIME -DERIST_HEAP_STATS \
    /tmp/app.s runtime/value_runtime.c -lm -o /tmp/app-profile
/tmp/app-profile
```

The diagnostic executable preserves application stdout and writes one JSON report
to stderr after its entry function completes. Fatal runtime exits before that point
do not emit a report. The ordinary bundle is built without `ERIST_HEAP_STATS` and
does not emit statistics. Profiling requires a development C toolchain; normal
offline application builds retain their existing requirements.

In a C harness, `eri_heap_write_stats(stream)` produces the same report and
`eri_heap_check()` validates the registry against its live counters. These are
private diagnostic helpers, not source-language functions or a stable runtime ABI.
The explicit C export can be instrumented by a development harness as well; its
generated entry point does not automatically print native-runtime diagnostics.

## Meaning of the report

The experimental format is `eristavi-heap-stats-v1`. It contains total counters and
the same counters by allocation family:

| Counter | Meaning |
| --- | --- |
| `allocations` | New blocks, including `realloc(NULL, size)`. |
| `reallocations` | Resize requests for existing blocks; their category is preserved. |
| `frees` | Released blocks; freeing NULL has no effect. |
| `live_allocations` | Blocks that have not been freed. |
| `live_bytes` | Requested payload sizes of those blocks. |
| `peak_allocations`, `peak_bytes` | Maximum simultaneous live counts/payload bytes. |
| `requested_bytes` | Cumulative requested bytes, including each resize's new size. |

The object header/data, Text buffers, prefix index, checked-failure state, native
slots/scopes/handlers/root tables, Unicode normalization scratch and file wrappers
have separate families. `other` includes remaining runtime allocation paths, such
as legacy collection helpers and path/read buffers. Prefix-backed List storage is
object data; prefix-backed Text storage is Text. Buffer capacity, rather than its
visible value length, is counted when capacity was the allocation request.

These are **payload-byte counters**, not RSS or reachable/live-language-value
measurements. They exclude diagnostic headers, allocator overhead, the backing
byte used for a zero-size request, stack/static storage, and allocations performed
inside libc/OS services. Foreign path buffers returned by `realpath`/`_fullpath`
continue to use the corresponding raw allocator/free boundary. Category peaks
need not occur together, so their sum is not the total peak.

Diagnostic headers preserve `max_align_t` alignment. A linked registry records
size/category for each tracked block and updates neighbors when a resize moves
it. The registry retains references to all unfreed blocks. Consequently its
consistency check, and sanitizer reachability while it is enabled, do not prove
that application values are reachable or that the language heap is leak-free.
Categories are allocation families, not tracing descriptors.

## Validation and baseline

Tests cover zero-size blocks, alignment, head/middle/tail resizing, category
preservation, payload preservation, NULL frees, arithmetic overflow rejection,
JSON totals and allocation balance under address/undefined sanitizers. Native
integration compares ordinary and diagnostic builds of the same assembly and
forces frequent temporary-slot collection while checking unchanged stdout.

The raw-runtime stress fixture runs two batches of 100 ordinary value/List/Text
and checked-failure operations. On the tested 64-bit host, the pre-collector
baseline retained payload bytes from 55,100 to 110,200; object/data/Text/failure
families grew independently, while slot/scope/handler/normalization scratch storage
was released. Test-only shutdown freed all remaining blocks after every application
value was dead and checked a zero live balance. That teardown was measurement
infrastructure, not a proposed collector.

## Relationship to native reclamation

The native collector described in `NATIVE_HEAP_GC.md` uses its own allocation
registry and typed reachability rules. It is intentionally not compiled together
with `ERIST_HEAP_STATS`: the diagnostic registry above keeps references to every
tracked allocation and would therefore corrupt a tracing reachability test.

The accounting fixture remains useful as an independent historical baseline and
for allocator/category diagnostics. The tracing collector is validated separately
with forced collection, typed root maps, identity cycles, saved failures, weak
prefix indexes and long-running allocation stress.
