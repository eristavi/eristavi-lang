# Production hardening

Reviewed against main `5e889faa9ba32187b9c3584a7a828ded7d202055` on
2026-10-25. The governing source-language documents remain frozen. This work
changes implementation lifetime and validation, not programmer-visible ownership,
syntax, value semantics, checked effects, or deterministic resource rules.

## Which runtime is being hardened

The Python Stage-0 compiler and the Eristavi-written offline compiler are separate
implementations. Stage-0's direct x86-64 backend already has typed tracing and
register/root planning. Those capabilities are not yet part of the offline
compiler's boxed runtime. Its implementation is `runtime/value_runtime.c`, linked
as a prebuilt object by both Eristavi-written native consumers. See
`OFFLINE_TOOLCHAIN.md` for the exact bootstrap boundary.

Self-compilation and finite differential tests establish a useful working
baseline; they do not establish production memory behavior or complete parity.

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

The x86-64 and ARM64 consumers now emit root maps from the independently verified
Universal register table. Every value-class spill and saved parameter is a root;
other register classes are excluded. Spills are zero-initialized before helper
calls, and each native function binds its map to its runtime scope. Root words are
read as address bits, without dereferencing heap-field references or stale dead
register values. This is conservative register rooting, not a new liveness pass.

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

This collector handles **temporary value slots only**. Aggregate/Text buffers,
saved failures and prefix-append bookkeeping still need managed reclamation.

## Remaining priorities

| Priority | Finding | Completion evidence |
| --- | --- | --- |
| P0 | Aggregate/Text buffers and saved failure state still use process-lifetime allocations. | Managed reclamation preserves snapshots, identity cycles, Text views and primary/secondary payloads under allocation stress and forced collection. |
| P1 | Compiler/runtime performance is unqualified beyond correctness and self-build. | Repeatable timing and peak/live-memory baselines; profile before changing representation or register allocation. |
| P1 | Target/runtime/release qualification is narrower than production support. | Address/undefined checks, malformed-input and allocation-failure cases, runtime/loader compatibility and complete package integrity/provenance checks. |
| P2 | Native macOS/Windows packaging and Stage-0 artifact/backend parity remain absent. | Native execution and offline package gates on each supported OS/ABI, with explicit compatibility contracts. |

Memory work must keep ordinary value copies and explicit shared identity distinct.
Scarce resources must continue to close through `with`, independently of garbage
collection. Existing Stage-0 analyses can inform the design; their serialized IR
and root protocol must not be assumed compatible with the offline compiler.

Do not label the toolchain production-ready while the P0 allocation paths remain.
No new source syntax or manual lifetime annotations are needed for these fixes.
