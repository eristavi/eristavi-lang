# Lists containing ordinary managed values — 8 November 2026

Private canonical U2/native contract, extending the existing aggregate and List
contracts. No source-written generic type arguments, language syntax changes,
new executable IR, copy rules, resource adapters or public 32-byte ABI changes.

## Exact ordinary element relationships

The existing List descriptor (kind 2, managed element domain 1, copy policy 1)
can now select an ordinary value aggregate child (kind 4), in addition to Text
and List children. The List marker has exactly one field naming that selected
canonical child carrier. Both descriptors and every aggregate field remain
subject to independent registry/root/Function verification and existing caps.
Identity children and unselected/mismatched relationships still refuse.

Version-one imported symbols use u2.list.boxed.C.operation, where C is the
original canonical List carrier index and operation is empty/copy/append/
replace/count/get/collect. The suffix supplies declaration-name uniqueness for
multiple List shapes in one Function. It is neither source syntax nor proof:
exact declaration kind/effects/version, arity, selected child relationship and
all canonical argument/result types are independently checked. Unknown legacy
names alone reach this bounded lookup; successful old import matches avoid
new suffix formatting. At most eight selected relationships and seven operations
are scanned, stopping after the exact match. No speedup is claimed.

These operations use the same List graph helpers and class-1 temporary roots.
An aggregate or inner List remains boxed; no integer boxing/unboxing is applied.
Get/replace bounds use the original LocId-aware terminal fault path. Existing
ordinary aggregate runtime bindings still guard native layout kind/count/fields
and ev_types_end before accessing a descriptor. No alternative runtime layout.

The generated fixture uses multiple aggregate List shapes, List-valued children,
a loop, copy/append/replace/get/count/collect, original/retrieved snapshots,
Text contents, forced GC and final reclamation. Source interpreter/current-C
references cover ordinary record Lists and nested Lists. The native envelope
containing a Text List is an additional canonical composition check; the source
oracle keeps that List in separate inferred storage and does not introduce a
new field annotation syntax.

## Checked self-call integration

emitValuesChecked supplies aggregate bindings to the existing independently
verified single-Function checked/self-recursive entry. Original FunctionId,
SignatureId, failure declaration, canonical invoke/continuation SSA and class-5
FailureContext handoff remain authoritative. Save the caller failure-handoff
pointer before layout guards use RCX/RDX. Guards run before managed allocation;
no new failure state, frame shape, recursion semantics or cleanup rules.

Native fixtures carry parent-private aggregates or Lists of aggregates across
checked children, retain nested Text across GC and read it on both outcome
paths. Depths 0/1/5/32/64 cover ordinary returns and the same propagating primary;
handler recovery at depths 1/32 returns normally through remaining parents.
A source reference with parent-private List/record state independently checks
counts, identity result and propagated error contents on interpreter/current C.
The failure contexts are created through the existing test runtime adapter;
this is not a new compiler-generated typed FailureContext producer.

## Independently discovered bootstrap issue

The source comparison exposed lexical typedef ordering in the C backend:
a nested List of records could be declared before its inner List typedef.
Declare extra List typedefs by nesting depth, then lexical order. Existing
record forward declarations, helper semantics and all assertions remain.
This touches bootstrap code generation and requires final full qualification
before merge; focused source/reference results do not qualify that gate.

## Remaining boundaries

Other field families and identity-containing aggregates, kind-4 managed-operation
and deep-fixability composition, typed failure producers, aggregate closed/mutual
checked groups and File-owned combinations remain. Already-live primary state
across File-owning defined calls remains refused. Hostile-root/allocator/
sanitizer/physical/broad independent evidence, current owned/C and hosted
watchdog repeatability, branch reconciliation and final four-platform/full
qualification remain pending. No owned full-compiler self-build or #51 work.
