# Reservation-aware verified free list

> **Status: stacked I1 review candidate; Linux x86-64 only**

This slice removes the remaining allocator metadata exception without changing the
Eristavi source language or design philosophy. Reusable blocks are still an
implementation detail; ordinary Eristavi programs gain no pointers, address casts,
ownership syntax, manual allocation API or unchecked integer behavior.

## Free-list representation

A free-list entry is no longer a naked block address. The allocator carries a
reservation-aware triple:

```text
region base + exact mapped length + block offset
```

The global free-list head uses that triple, and every free block stores the next
entry using the same representation.

The private block header is therefore 32 bytes:

```text
+0   payload capacity / allocation flag  8 bytes
+8   next free region base               8 bytes
+16  next free exact region length       8 bytes
+24  next free block offset              8 bytes
+32  payload begins
```

The region header remains the reservation-aware 48-byte layout introduced by the
previous lowering slice.

## Verified access path

Free-list traversal, first-fit selection, unlinking, relinking and block-state
updates now use `erist_rt_memory_load64` / `erist_rt_memory_store64`, which are
generated from the verified compiler-private memory IR.

The free-list scanner rejects:

- a block offset before the allocator's region metadata;
- a block offset that is not 16-byte aligned;
- a free-list entry whose allocation bit is still set;
- zero payload capacity;
- block extents that overflow or extend beyond the exact mapped region.

The private push helper also follows the System V AMD64 stack-alignment contract
before calling the generated memory helpers.

Only allocator state in static `.bss` storage is accessed directly. Reserved-region
metadata is no longer read or written through unchecked handwritten offsets.

## First-fit behavior

The allocator preserves first-fit reuse. A focused probe constructs a list where
the head block is too small and the second block is suitable. Allocation must skip
the head, unlink the second entry through verified stores, return that block, and
then successfully reuse the original head on the following allocation.

This proves both non-head unlinking and preservation of the remaining free-list
entry rather than only testing head reuse.

## Focused validation

The branch-focused tests cover:

1. direct freestanding Linux page reservation/release;
2. allocator alignment, ordinary head reuse, double-free rejection and release;
3. verified private memory IR lowering including bounds/alignment failures;
4. reservation-aware non-head free-list traversal and reuse.

All focused probes assemble and link without standard runtime objects and execute
without libc, CRT startup, a dynamic loader or the old C value runtime in the
generated target.

GNU `as` and `ld` remain the explicit assembly/link boundary at this stage, and the
generator still runs on the qualified bootstrap runtime.

## Next boundary

With allocator region and free-list metadata now expressed through the restricted
memory profile, the next I1/I2 boundary is the first actual value-runtime migration
off `runtime/value_runtime.c`. That work should proceed in dependency order,
beginning with bootstrap-independent checked scalar/runtime services before Text,
ordinary managed values, failures/resources and finally the typed collector.
