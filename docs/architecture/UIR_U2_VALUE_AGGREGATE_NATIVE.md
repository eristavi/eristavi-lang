# Whole-Function ordinary value aggregates — 8 November 2026

Private opt-in U2 integration. Source syntax, frozen ordinary value semantics,
canonical Function/SSA and aggregate operations 43/44/45, independent verifiers,
public 32-byte ABI and existing owned graph helpers remain authoritative.
No executable IR, resource adapter, collector or competing copy semantics added.

## Representation gap and bounded extension

The previous semantic table distinguished only Text, List and identity. None
can correctly describe an ordinary aggregate. Add private descriptor kind 4,
structural domain 0, exact canonical aggregate TypeId, copy policy 1. This keeps
the existing four-word descriptor layout and 64-entry accounting cap. Identical
relationships intern; primitive payloads, wrong policy/domain, foreign ownership
and invalid structural shapes refuse construction or independent verification.
Report.types includes these rows; Report.lists/identities retain their meanings.

Root selection requires every field to be predicate, i64, or an explicitly
selected Text, List or ordinary aggregate carrier. Exact descriptor/field
relationships are verified; identity fields, optional/Float/narrow fields,
FailureContext fields and unselected children remain unsupported here. Existing
structural graph verification supplies acyclicity. At most eight selected
carriers and 32 fields per value aggregate are admitted. This extension does
not add kind 4 support to managed operation selectors or deepFixable, whose
field-composition work remains pending rather than guessed.

## Native integration

emitValues is the explicit nonchecked entry. Its runtime type index vector is
aligned with selected carriers. Aggregate entries require distinct indices in
6..255; missing, zero or duplicate aggregate bindings refuse before output.
Text and List field mappings retain the existing runtime indices 4 and 7;
predicate/i64 use 0/1. Nested aggregate fields use the selected child's binding.
This is a private runtime binding, not source-written generic arguments.

The linked native descriptor table remains trusted compiler/runtime metadata.
Before allocation, each aggregate binding is checked against the existing
published ev_types_end boundary, ordinary aggregate kind 6, exact field count,
non-null field table for nonempty shapes and exact ordered field type indices.
A stale binding or out-of-table index is a terminal internal defect, never a
checked failure. Missing native table symbols fail at link time. This is not a
validator for arbitrary malicious pointers in a forged linked field table.

Canonical make uses evn_object and evn_init. Get uses evn_member; scalar fields
are unboxed and managed fields retain boxed slots. Set uses evn_copy,
evn_member_ref and evn_store, preserving the old SSA value and ordinary snapshot
semantics. Predicate/i64 fields use existing boxing helpers. The two existing
class-1 temporary roots protect partial objects and boxed fields across helper
calls. Original live-before roots remain published; live-after publication
precedes temporary retirement. No new frame layout or root authority.

New field emission/layout work is charged before output using existing budget
work chunks. Old entry points pass a concretely typed empty binding vector;
a nonexecuted inference branch supplies its Int element type for the current
bootstrap. Aggregate operand classification storage is built only when bindings
are supplied. No speedup or physical-memory qualification is claimed.

## Evidence boundary

Real generated native make/get/set constructs nested aggregates containing
Text and Lists, retains old/new snapshots through forced block GC, validates
counts/contents and passes final graph/Text/failure/handler/allocator reclamation.
Separate predicate fields test scalar boxing/unboxing. Stage-0 and current
native source references agree on record copy/update outcomes. Refusals cover
missing/duplicate/invalid bindings, wrong descriptor/shape, missing child,
new descriptor policy/domain and primitive shape. Linked kind/count/field-order
mismatches and out-of-table bindings remain terminal defects.

This does not finish Lists containing aggregate elements, identity-containing
aggregates, additional field families, typed failure producers or checked/
recursive/File combinations through emitValues. They remain U2 integration
work, as do allocator/hostile-root/sanitizer/physical and exact-head hosted/full
qualification. No new source syntax, production routing or promotion.
