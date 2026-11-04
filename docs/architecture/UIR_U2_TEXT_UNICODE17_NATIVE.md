# U2 Managed Text / Unicode 17 canonical native slice

Status: opt-in bounded development slice, NOT production promotion or U2 acceptance.
Canonical structural UIR and private managed Text descriptor remain unchanged;
existing frozen Text semantics and 32-byte owned runtime ABI are preserved.

## Frozen contract

Text stores valid UTF-8 with scalar-sequence equality and no implicit Unicode
normalization. Views are explicit and read-only: bytes, scalars and Unicode 17
extended grapheme characters. Invalid Unicode scalars including surrogate code
points must terminate through the existing runtime fault path.

## New executable profile

The src/compiler/u2_text_native.eri adapter accepts one canonical block with
at most 128 SSA values, 256 instructions, no entry arguments and one scalar
return. It independently checks the full frozen UIR, exact eight imported
operation names, signatures, conservative effects, version and explicit Text
carrier descriptor. The accepted closed profile is:
- fromScalar, concat, copy and scalar-sequence equality
- byte, scalar and Unicode 17 extended-grapheme counts
- explicit slots and Text collector call.

The emitter calls existing Unicode17-owned runtime functions directly from
canonical instruction data. It does not use legacy source compiler lowering.
Rooted stack slots are registered before allocation and remain conservatively
live until function exit, with a registered temporary view slot during an
allocating Unicode view count. Other managed type families and all CFG/checked
failure opcodes are rejected before any assembly output.

The test's private ev_types table preserves existing descriptors 0..14 and
adds exact read-only view types 15..17 with bytes, scalars and characters names.
No new public ABI, source syntax, Unicode table or managed value layout is
introduced.

## Focused acceptance checks

- e plus U+0301: 3 UTF-8 bytes, 2 scalar values, 1 grapheme.
- U+00E9 versus decomposed sequence: unequal, no normalization.
- Copy of decomposed Text: equal by scalar sequence.
- U+1F469 + U+200D + U+1F4BB: 11 bytes, 3 scalars, 1 grapheme.
- Explicit collection between allocation and later observation, full
  graph/Text/failure/handler/allocator teardown checks.
- Invalid descriptor/import refuses before emission; surrogate scalar
  fails via the existing terminal Unicode fault path.

Not covered: arbitrary Text literal UIR, view indexing and escape, multi-block
CFG, recursion, Text-containing aggregates, complete root maps, checked
failures/cleanup, full physical resource evidence or four-platform qualification.
Keep PR #111 in draft and U2 #74 open.
