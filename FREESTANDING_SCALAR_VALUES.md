# Freestanding scalar `ev_value` ABI slice

> **Status: stacked runtime-independence review candidate; Linux x86-64 only**

This slice is the first standalone replacement proof for concrete helper symbols
from `runtime/value_runtime.c`. It does not change Eristavi source syntax, public
value semantics, ownership rules or the type system.

## ABI layout

The existing native C runtime defines `ev_value` as an `int type` followed by a
union whose largest current member is the 24-byte Text-view representation. Under
the Linux/System-V x86-64 ABI this gives the existing 32-byte value layout:

```text
+0   type (32-bit C int) + ABI padding   8 bytes total
+8   union payload begins                8 bytes
+16  remaining union storage             8 bytes
+24  remaining union storage             8 bytes
size                                    32 bytes
```

The freestanding scalar slice deliberately uses that existing size and offsets.
It stores the type as a zero-extended 64-bit word so the C `int` field and its
padding are deterministic. Int/Bool payloads live at `+8`; `+16` and `+24` are
zeroed for newly created scalar values.

## Implemented native helper symbols

`src/runtime/value_scalar_x86_64.eri` emits the existing native helper names for
the scalar subset:

- `evn_void`
- `evn_int`
- `evn_bool`
- `evn_copy` for Int/Bool/void
- `evn_store`
- `evn_truth`
- `evn_unary` for checked Int negation and Bool `not`
- `evn_binary` for Int arithmetic/comparisons and Bool equality/inequality

The helpers allocate through the Eristavi-emitted freestanding allocator and use
the checked scalar engine from the previous slice. Arithmetic defects therefore
flow into the libc-free scalar fault adapter.

Unsupported value kinds are rejected as internal runtime defects instead of being
silently reinterpreted as scalars.

## Composition

The standalone target is composed entirely from Eristavi-emitted runtime pieces:

```text
Linux syscall boundary
  -> verified allocator / reservation-aware free list
  -> checked scalar engine
  -> libc-free fault adapter
  -> 32-byte scalar ev_value helpers
```

The generated probe does not link `runtime/value_runtime.c`,
`runtime/native_gc_runtime.c`, libc, libm or CRT startup objects.

## Focused validation

The success probe verifies:

- `evn_int` type/payload/tail layout;
- Int addition through `evn_binary`;
- `evn_copy`;
- `evn_store`;
- Bool construction and `not`;
- ordered Int comparison returning Bool type;
- void construction;
- explicit release of all allocator regions.

A separate overflow probe constructs `INT64_MAX` and `1` through `evn_int`, invokes
the existing `evn_binary` ABI, and verifies the exact freestanding stderr fault and
exit status 1.

The full focused runtime-independence stack (page boundary, allocator, verified
memory lowering, verified free list, raw checked scalars and scalar faults) is
rerun alongside these probes.

## What remains intentionally outside this slice

This is not yet the full managed native runtime. In particular:

- scalar values are not yet linked into the existing `ev_slot_node` lifetime list;
- `evn_scope_enter`, `evn_scope_leave` and `evn_bind_roots` are not yet replaced;
- no native GC safe point or root traversal is implemented here;
- Float, Text, objects, Lists, identity/maybe, failures and resources remain on the
  later migration path.

Therefore this slice proves the scalar helper ABI and value representation but does
not yet remove the C runtime from arbitrary self-hosted application builds.

## Next boundary

The next coherent slice is the existing slot/scope ABI. The current C layout is
compatible with a private 32-byte `ev_value` followed by an 8-byte slot-list link,
and native scopes contain mark/previous/root/class/count fields. Porting those
lifetimes over the owned allocator will make scalar helper results reclaimable and
prepare the first real compiler-path substitution without changing the language.
