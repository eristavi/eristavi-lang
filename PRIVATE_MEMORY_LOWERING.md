# Verified private memory lowering

> **Status: stacked I1 review candidate; Linux x86-64 only**

This slice continues toolchain-independence work without changing the Eristavi
source language, grammar, public type system or design philosophy. Machine words,
reservation bases, checked addresses and fixed-width memory operations remain
compiler-private implementation concepts. Ordinary programs still have no pointer
syntax, address casts, manual allocation API, ownership annotations or unchecked
`Int` behavior.

## What changed

`src/compiler/runtime_memory_ir.eri` now models a restricted private memory profile:

- class 7: machine word;
- class 8: original reservation base;
- class 9: checked derived address;
- checked power-of-two alignment;
- platform reservation producing **both** base and exact mapped length;
- exact release requiring the matching base/length pair;
- bounds- and alignment-checked address derivation;
- fixed-width 1/2/4/8-byte load and store;
- private helper-ABI parameters for runtime implementation helpers.

Reservation bases and exact mapped lengths carry verifier-only provenance. A base
from one reservation cannot be combined with the length from another reservation.
Derived addresses retain reservation provenance, while ordinary transformed machine
words deliberately do not.

This is a compiler/runtime invariant, not a source-level ownership system.

## x86-64 lowering

`src/compiler/runtime_memory_x86.eri` lowers only verified private memory programs.
It emits System V AMD64 assembly and uses the existing freestanding Linux platform
boundary for reserve/release.

The private helper result ABI is:

```text
rax = result machine word
rdx = 0 on success, 1 on checked memory-operation failure
```

All six incoming SysV integer argument registers are snapshotted into private stack
slots before lowering. This prevents one private operation from clobbering a later
helper argument and keeps lowering independent of instruction ordering accidents.

Checked derived addresses enforce at runtime:

- mapped length is at least the access width;
- offset is at most `length - width`;
- requested alignment is satisfied;
- base-plus-offset arithmetic does not overflow.

## Allocator integration

The allocator now stores linked regions as reservation pairs rather than naked
region addresses. Its private 48-byte region header is:

```text
+0   next region base          8 bytes
+8   next region exact length  8 bytes
+16  current mapped length     8 bytes
+24  used/bump offset          8 bytes
+32  private magic             8 bytes
+40  alignment padding         8 bytes
```

The block header remains 16 bytes:

```text
+0   payload capacity/flag     8 bytes
+8   next free block           8 bytes
+16  payload begins
```

Verified private `load64` / `store64` helpers are generated from the restricted
memory IR and are used for:

- new-region header initialization;
- current-region used-offset reads/writes;
- bump-path block-header initialization;
- allocated-block capacity reads/writes during free;
- region magic validation;
- linked-region base/length traversal;
- release-all traversal before exact `munmap`.

The free-list scan/relink path still directly accesses block headers because the
current free-list representation stores absolute block addresses without their
reservation pair. This is the remaining deliberate exception in this slice. It is
not exposed to user code and must be removed or redesigned before claiming that all
allocator metadata access is expressed through the private verified memory profile.

## Focused validation

The focused preflight exercises three independent freestanding probes:

1. direct Linux page reservation/release;
2. allocator alignment/reuse/release behavior;
3. private memory IR verification and x86 lowering.

The lowering probe covers a successful reserve/derive/store/load/release path plus
runtime rejection of an out-of-bounds access and a misaligned access. The resulting
binary is assembled/linked without standard runtime objects, has no interpreter or
dynamic section, has no unresolved symbols, and runs with an unusable `PATH`.

A preflight failure during development exposed an x86 ABI-clobber bug: the generic
store helper consumed `%rcx` only after an earlier operation had reused that register.
The fix snapshots all six incoming arguments at function entry. No source-language
rule or verifier rule was weakened.

## Dependency boundary

The generated target code still uses GNU `as` and `ld` as the current development
assembly/link boundary. The Eristavi generator still runs on the qualified bootstrap
runtime. Neither dependency is hidden or described as eliminated by this slice.

The generated memory operations themselves do not require libc, libm, CRT startup,
the dynamic loader or the old C value runtime.

## Next boundary

The next runtime-independence work should remove the remaining naked free-list block
accesses by giving reusable blocks verifiable region provenance, then use the same
private lowering foundation for the first C-runtime value services in dependency
order. Public Eristavi semantics remain frozen while this work proceeds.
