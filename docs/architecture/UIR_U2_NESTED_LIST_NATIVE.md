# Whole-Function nested List native imports — 8 November 2026

Private opt-in U2 contract; source semantics, public 32-byte ABI, canonical
Function/SSA, independent verification and existing native adapters remain.
This extends UIR_U2_LIST_TEXT_NATIVE.md for List<List<i64>> and
List<List<Text>>. It does not qualify arbitrary managed constructors.

A nested List carrier has exactly one marker field naming its selected inner
List carrier. The outer descriptor is listOfManaged(inner), with ordinary value
copy policy. Both carriers and their exact descriptors must be selected;
List<Text> additionally requires the selected canonical Text carrier. Identity
children and missing/mismatched element relationships refuse admission. The
existing descriptor verifier still checks registry ownership and acyclicity.
The root gate can represent deeper List relationships; producer imports in this
batch support only the two explicitly named nested shapes.

Exact version-one imports have prefixes u2.list.list_i64. and
u2.list.list_text. with empty/copy/append/replace/count/get/collect suffixes.
They require imported kind 2, effects 63 and exact canonical signatures.
Append takes outer/inner List; replace takes outer/i64/inner List; get takes
outer/i64 and returns inner List; count returns i64. Existing ordinary List
runtime helpers implement the operations. Boxed children stay boxed and rooted;
no i64 boxing/unboxing is applied to an inner List. SSA destinations are
published using the existing root protocol before temporary roots retire.
Original LocId terminal bounds guards precede copy or mutation.

The eight-carrier cap bounds descriptor relationship scans. Only the matching
carrier/descriptor pair needs a child descriptor read; this avoids reading all
selected descriptors during each relationship check. No benchmark speedup is
claimed. No new runtime adapter, executable IR or ownership semantics.

Focused fixtures construct inner Lists in loops, append outer Lists, copy and
replace outer snapshots, retrieve and independently grow inner snapshots, and
check counts and beta/lambda contents. Forced block GC and final graph/Text/
failure/root/allocator reclamation use the established native execution harness.
Independent Stage-0 and current-native source programs return the same 13.
Negative cases cover descriptor/marker/missing child, effects and argument type;
get and replace bounds retain source-located terminal faults. This is not
recursive/checked/File combination, hostile-root, allocation-refusal, sanitizer,
physical-budget or four-platform qualification of nested Lists.
