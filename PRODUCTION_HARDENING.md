# Production hardening

Reviewed against main `8e57f3246952b2f397aa6f7c77d42a1566a70bba` on
2026-10-25. The governing source-language documents remain frozen. This work
changes implementation lifetime and validation, not programmer-visible ownership,
syntax, value semantics, checked effects, or deterministic resource rules.

## Which runtime is being hardened

The Python Stage-0 compiler and the Eristavi-written offline compiler are separate
implementations. Stage-0's direct x86-64 backend already has typed tracing and
register/root planning. The offline compiler keeps the pinned C bootstrap
implementation in `runtime/value_runtime.c`; native Linux bundles now wrap it with
`runtime/native_gc_runtime.c`, which supplies typed non-moving heap reclamation for
the native pointer ABI. Both files remain bootstrap runtime artifacts rather than
Eristavi source. See `OFFLINE_TOOLCHAIN.md` for the exact boundary.

Self-compilation and finite differential tests establish a useful working
baseline; they do not by themselves establish production memory behavior or
complete target parity.

## First patch: native checked-unwind administration

The review found two concrete retention paths:

- `evn_frame` allocated every native checked/resource handler on the heap, while
  pop and cleanup only moved the active handler pointer; completed frames leaked.
- `longjmp` skipped called functions' scope exits. A catch in a still-running
  caller retained the abandoned scopes and temporary slots until that caller
  eventually returned.

Native frames now record the scope/slot boundary and whether they received a
checked jump. Popping frees every completed frame through the requested boundary.
An exceptional pop also restores the scope/slot boundary immediately. A normal
pop retains successful expression results. Resource normal/unwind paths use the
same release operation; file cleanup order and primary/secondary failures are
unchanged. The jump buffer remains the first field, preserving the existing
opaque native calling convention.

The reclamation boundary is intentionally precise: caller locals predate the
handler; ordinary aggregate/Text buffers and checked-failure payloads have separate
ownership. Releasing temporary slots must not destroy a caller's stored value,
an identity mutation, an error payload, or a resource needed by scoped cleanup.

Validation includes:

- allocation-counted tests for 10,000 grouped normal handler exits and 10,000
  failures crossing nested calls, checking a return to baseline after each exit;
- surviving normal results/caller mutations and nested resource unwinding;
- the same tests under AddressSanitizer and UndefinedBehaviorSanitizer;
- 1,000 generated-program catches preserving caller state and typed payloads;
- injected cleanup failures in both generated C and native execution, preserving
  one primary failure and ordered secondary failures;
- the full regression suite and the existing Linux native self-build/offline gates.

The allocation counter covers the isolated administrative tests, not total
application heap usage. Locally, LeakSanitizer cannot inspect tasks in the sandbox;
`ASAN_OPTIONS=detect_leaks=0` permits address/undefined checks while explicit
allocation counts still enforce administrative reclamation. Hosted CI can retain
LeakSanitizer's default behavior.

## Second patch: bounded native temporary slots

The x86-64 and ARM64 consumers emit root maps from the independently verified
Universal register table. Every value-class spill and saved parameter is a root;
other register classes are excluded. Spills are zero-initialized before helper
calls, and each native function binds its map to its runtime scope. Root words are
read as address bits, without dereferencing heap-field references or stale dead
register values.

Before allocating another temporary slot, the runtime periodically retains slots
named by active root maps and scope/handler boundaries, then frees the rest.
Collection starts at 4,096 slots and allows another 4,096 allocations beyond the
survivor count. Scope exits lower that threshold again. Temporary storage therefore
depends on active register frames/boundaries plus the collection allowance, rather
than the number of loop iterations. Snapshot pointers are retained until no root
names them; cells are never blindly reused while aliases can still observe them.

Checked unwinding removes abandoned root frames with their scopes before any
subsequent collection. Successful returns copy their result before releasing the
callee's scope. The native runtime/helper boundary is private; a matching consumer
and runtime object must be packaged together. Unregistered C embedding scopes and
the explicit generated-C export retain their existing arena behavior.

Validation adds a bounded-slot test at 1,000 and 100,000 iterations, both below
4,200 live temporary slots, plus collection at every allocation opportunity under
address/undefined sanitizers. The forced cases exercise snapshots, identity,
short-circuiting, recursion, nine arguments, checked failures and normal/failing
resource scopes. Independent reported IR classes are cross-checked against both
emitted root maps. Runtime unit tests check duplicate roots, non-value words,
scope-boundary retention and allocation balance.

## Third patch: allocation accounting foundation

`ERIST_HEAP_STATS` enables an allocation registry and payload-byte counters by
family, without changing ordinary builds or automatically reclaiming objects.
The object/Text/failure stress baseline measures retained growth separately from
reclaimed native administrative storage. Resize, alignment, accounting and
sanitizer checks are included. `HEAP_DIAGNOSTICS.md` defines the counters, private
profiling workflow and limitations. The diagnostic registry intentionally retains
tracked allocations and is therefore kept separate from the tracing collector.

## Fourth patch: typed native Object/Text/failure reclamation

The Linux offline/native runtime candidate now uses a non-moving mark-and-sweep
layer in `runtime/native_gc_runtime.c`. Collection occurs only at pointer-ABI safe
points after runtime operations finish constructing their results. Native object
field storage is zero-initialized before the first possible collection so partially
constructed aggregates have a defined trace state without adding source-level
initialization or lifetime rules.

Strong roots are the active native value slots, scopes, verified Universal-IR value
and failure root-map entries, handler frames, current checked failure, and explicit
temporary results carried across collector safe points. Traversal is typed:

- Text and explicit Text views retain their backing bytes;
- nominal values and Lists retain headers/storage and recursively traverse values;
- `maybe` and `identity` traverse their contained value, including identity cycles;
- file resources retain runtime/path storage but still close through `with`;
- user errors, `FileError`, and ordered secondary cleanup failures retain their
  typed payloads and Text.

Prefix-append indexes are weak implementation metadata. An index node survives only
while its backing Text/List allocation is already strongly reachable; dead indexes
are unlinked before sweep. The collector is non-moving, so existing interior
mutation references remain stable during an operation. It does not introduce
finalizers; deterministic scarce-resource cleanup remains independent of GC.

Forced-collection tests run with a collection interval of one and cover reachable
nested Text, weak prefix buffers, unreachable identity cycles, saved checked
failures, and 10,000 transient allocation iterations. Normal and sanitizer builds
must return to zero tracked live blocks after all roots are released. The offline
bundle itself links the collector-enabled runtime, so compiler B/C repeated
self-build and the no-Python/no-C-compiler audit exercise the same implementation;
the audit additionally executes 100,000 iterations of ordinary Eristavi Text/List
allocation.

See `NATIVE_HEAP_GC.md` for the root/traversal contract and remaining qualification
limits. The generated-C/reference route intentionally retains its existing arena
behavior and is not silently redefined by this native-runtime milestone.

## Remaining priorities

| Priority | Finding | Completion evidence |
| --- | --- | --- |
| P1 | Collector/runtime performance is unqualified beyond correctness, stress and self-build. | Repeatable allocation rate, pause, throughput and peak/live-memory baselines; profile before changing representation, interval or register allocation. |
| P1 | Allocation-failure and long-duration runtime qualification are incomplete. | Injected allocator failures at collector/runtime boundaries, longer mixed workloads, sanitizer coverage and stable failure behavior. |
| P1 | Target/runtime/release qualification is narrower than production support. | Malformed-input and allocation-failure cases, runtime/loader compatibility and complete package integrity/provenance checks. |
| P2 | Native macOS/Windows packaging and Stage-0 artifact/backend parity remain absent. | Native execution and offline package gates on each supported OS/ABI, with explicit compatibility contracts. |

Memory work must keep ordinary value copies and explicit shared identity distinct.
Scarce resources must continue to close through `with`, independently of garbage
collection. The collector remains stop-the-world and single-runtime; generational,
concurrent, incremental or compacting collection should be considered only if
measurements justify the added complexity.

Do not label the toolchain production-ready while the remaining P1 release and
runtime qualification gates are open. No new source syntax or manual lifetime
annotations were needed for these fixes.
