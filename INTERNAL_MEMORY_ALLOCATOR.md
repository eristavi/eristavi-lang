# Private memory/layout and allocator slice

> **Status: I1 review candidate; Linux x86-64 only**

This change continues the freestanding foundation without changing Eristavi's
public source language, frozen semantics or design philosophy. There is still no
pointer syntax, manual allocation API, ownership annotation, unchecked `Int`, or
reinterpretation of `identity` as an address.

## Compiler-private layout verification

`src/compiler/runtime_memory.eri` describes only build-time runtime metadata. Its
layout verifier requires:

- positive power-of-two layout alignment;
- layout size aligned to the declared alignment;
- field widths restricted to 1, 2, 4 or 8 bytes;
- field alignment no stronger than the containing layout;
- aligned, in-bounds field offsets;
- no overlapping fields;
- a bounded field list.

The allocator emitter is gated by this verifier before it emits target code.
These records are not public Eristavi types and do not become source-level machine
words, regions or addresses.

The current fixed internal layouts are:

```text
region header (32 bytes, 16-byte aligned)
  +0   next region base       8 bytes
  +8   mapped length          8 bytes
  +16  bump/used offset       8 bytes
  +24  private magic          8 bytes

block header (16 bytes, 16-byte aligned)
  +0   payload capacity/flag  8 bytes
  +8   next free block        8 bytes
  +16  payload begins
```

The low bit of the aligned capacity is private allocation state. Payload
capacities are multiples of 16, so that bit is not part of the capacity.

## Restricted memory-operation profile

`src/compiler/runtime_memory_ir.eri` pins the first compiler-private operation
model needed to break the runtime bootstrap cycle. It deliberately exists below
ordinary source semantics.

Private value classes are:

- class 7: machine word;
- class 8: original reservation base;
- class 9: checked derived address.

The verifier accepts only a restricted sequence of primitives:

- machine-word constant;
- checked power-of-two align-up;
- reserve from a checked word size;
- release using the original reservation base and exact length;
- bounded/aligned address derivation from reservation base + region length + offset;
- fixed-width load from a checked derived address;
- fixed-width store to a checked derived address.

Registers must be contiguous, operands must already be defined with the expected
private class, results cannot be defined twice, and only address derivation can
produce the address class. In particular there is no operation that reinterprets
ordinary `Int`, `identity` or an arbitrary integer as an address.

This is the verifier/profile foundation. It is not yet a public Universal-IR
surface and it does not change the source grammar or type system. The next lowering
step will connect these verified concepts to the shared runtime implementation
pipeline without exposing them to ordinary programs.

## Allocator boundary

`src/runtime/allocator_x86_64.eri` emits a target allocator on top of the previous
`erist_rt_reserve` / `erist_rt_release` Linux syscall boundary.

Private ABI:

- `erist_rt_alloc(rdi=requested bytes) -> rax=payload or 0`
- `erist_rt_free(rdi=payload) -> rax=0 or -1`
- `erist_rt_allocator_release_all() -> rax=0 or first negative munmap result`

Properties of this slice:

- positive allocation requests are rounded to 16-byte payload capacity;
- returned payload addresses are 16-byte aligned;
- small allocations use a 64 KiB minimum region;
- larger requests receive a sufficiently large page-rounded region through the
  existing reserve helper;
- completed blocks enter a first-fit free list and can be reused;
- zero free is a no-op;
- misaligned, out-of-region and already-free owned pointers are rejected before
  changing allocator state;
- all mapped regions are linked through raw region headers and can be explicitly
  released;
- allocator state itself lives in static freestanding storage rather than managed
  Eristavi values.

This allocator intentionally does not yet split or coalesce free blocks, return an
individual empty region to the kernel, or implement the final managed heap/GC.
Those are optimization and later-runtime concerns, not reasons to alter the source
language.

## Dependency boundary

The **generated allocator probe** contains no libc, libm, CRT startup object,
dynamic loader or old C value runtime. It uses direct Linux x86-64 syscalls via
the previous freestanding helpers. GNU `as` and `ld` are still development/build
boundaries at this stage.

The Eristavi generator itself still executes on the qualified bootstrap runtime.
That is expected during I1 and must not be confused with the dependencies of the
generated target runtime.

## Focused validation

`tests/test_internal_memory_allocator.py` builds the Eristavi generator, emits the
freestanding assembly, assembles/links it without standard runtime objects, checks
for unresolved imports/interpreter/dynamic loading and executes it with an unusable
`PATH`.

The target probe covers:

- private memory-profile verification before emission;
- 16-byte alignment;
- writes through the first and last byte of aligned payload capacity;
- free-list reuse of a released block;
- double-free rejection;
- zero free;
- a large allocation that forces another region;
- explicit release of all regions;
- fresh allocation after complete release;
- rejection of a misaligned derived pointer.

The focused Ubuntu preflight builds both freestanding generators and executes both
target probes before any full regression/self-build qualification is requested.

## Next boundary

Lower the verified private word/reservation/address operations into the shared
runtime implementation pipeline and make the allocator consume those operations
instead of relying on handwritten assembly templates for its metadata accesses.
The allocator must remain below managed values. Once that boundary is qualified,
port checked scalar helpers, then Text/Unicode storage, ordinary values/identity,
failures/resources and finally the typed collector away from the C bootstrap
runtime in dependency order.
