# Freestanding scalar slot/scope lifetime ABI

> **Status: stacked runtime-independence review candidate; Linux x86-64 only**

This slice ports the existing native scalar slot/scope lifetime ABI onto the
Eristavi-owned allocator. It does not change Eristavi source syntax, public
ownership semantics, failure semantics, or the type system.

## Existing ABI matched

The private verifier in `src/compiler/runtime_value.eri` fixes the Linux/System-V
x86-64 layouts used by the current native runtime:

```text
ev_value (32 bytes)
  +0   type / ABI padding
  +8   scalar payload
  +16  union tail
  +24  union tail

ev_slot_node (40 bytes)
  +0   embedded 32-byte ev_value
  +32  next slot

ev_scope (40 bytes)
  +0   slot mark
  +8   previous scope
  +16  roots pointer
  +24  root-class pointer
  +32  root count
```

These are compiler/runtime implementation layouts, not public Eristavi types.

## Scalar slots

`erist_rt_value_new` now allocates the existing 40-byte slot-node shape rather
than an unlinked 32-byte value. Every scalar `evn_*` result is pushed onto the
private `.Lvalue_slots` stack and returns the address of the embedded value at the
start of that slot node.

This preserves the existing pointer ABI while making scalar results reclaimable at
scope boundaries through the owned allocator.

## Scope helpers

`src/runtime/value_scope_x86_64.eri` emits the existing native helper names:

- `evn_scope_enter`
- `evn_bind_roots`
- `evn_scope_leave`

`evn_scope_enter` records the current slot mark and previous scope, zeroes root
metadata, and pushes a 40-byte scope object allocated by the freestanding allocator.

`evn_bind_roots` stores the compiler-provided root-address array, root-class array,
and count. The count is checked against `SIZE_MAX / sizeof(uintptr_t)`. The metadata
is intentionally only stored in this slice; GC tracing remains a later collector
migration step.

## Scope leave semantics

The implementation matches the existing C wrapper contract rather than narrowing
it:

1. the scalar result value is copied before any slot is reclaimed;
2. all slots created after the target scope's mark are popped and returned to the
   owned allocator;
3. all active scopes down through the target scope are reclaimed, so leaving an
   outer scope while nested scopes remain active performs the same unwind as the
   current runtime;
4. the copied scalar result is re-slotted in the surviving outer scope (or the
   top-level slot stack) and returned.

Only Int, Bool and void values are accepted by this scalar-only lifetime slice.
Other value kinds remain on the later migration path rather than being partially or
incorrectly copied.

## Focused validation

The scope probe verifies both ordinary nested leave and outer-scope unwind:

- enter an outer scope;
- bind root/class metadata and confirm the ABI fields;
- create outer and nested scalar slots;
- leave the nested scope with a scalar result and verify that result survives in
  the outer scope;
- leave the outer scope and verify the result is re-slotted outside it;
- start a second nested structure, bind metadata to the still-active outer scope
  while an inner scope exists, then leave the **outer** scope directly;
- verify both scopes are unwound and the nested scalar result is preserved;
- explicitly reclaim the final top-level test slot and allocator regions.

The full focused runtime-independence stack is rerun alongside this probe:
freestanding Linux memory, allocator, verified memory lowering, reservation-aware
free list, checked scalar operations/faults, and scalar `ev_value` helpers.

The final focused run is green and the generated probe has no libc, libm, CRT,
dynamic-loader, or old C value-runtime dependency.

## What remains

This slice stores native root metadata but does not yet implement the typed GC over
those roots. It also does not port Float, Text/Unicode, objects, Lists,
maybe/identity, failures, resources, or the full native collector.

GNU `as` and `ld` remain the explicit assembly/link boundary, and the Eristavi
source generator still runs on the qualified bootstrap runtime.

## Next boundary

The next runtime-independence boundary is the first collector/root integration over
these owned slots/scopes, initially for the scalar-only graph where no payload
contains managed references. From there, managed value families can be migrated in
dependency order without changing the language surface.
