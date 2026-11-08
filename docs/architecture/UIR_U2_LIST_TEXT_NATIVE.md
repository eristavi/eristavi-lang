# Whole-Function List<Text> native imports — 8 November 2026

Private opt-in U2 development contract, not full qualification or source syntax.
Follow frozen ordinary List value semantics and Unicode17 Text invariants.
Copies/appends/replacements must preserve independent List snapshots. Elements
are valid immutable Text values, not raw UTF-8 pointers or i64 scalar boxes.

Admission uses the existing managed descriptor `listOfManaged(text)` (kind 2,
element domain 1, element descriptor 1, copy policy 1). Its distinct canonical
opaque carrier has exactly one marker field naming the selected canonical Text
carrier, which must itself be mapped to the canonical managed Text descriptor.
The marker is metadata only; ordinary aggregate producers remain refused.
Nested List admission is extended by UIR_U2_NESTED_LIST_NATIVE.md; other
managed element kinds remain unsupported by these producer imports.

Version-one exact imports `u2.list.text.empty/copy/append/replace/count/get/collect`
require imported kind 2, effects 63 and version 1, with independently checked
canonical signatures. Append takes List/Text; replace takes List/i64/Text;
get takes List/i64 and returns Text. Count returns i64, collect has no result.
No malformed same-shape symbol or mismatched element relationship authorizes
native lowering.

Whole-Function instruction lowering shares existing List runtime helpers and
rooted temporary slots. The snapshot is rooted before helper calls. Already
boxed Text is rooted directly rather than passed through evn_int; get retains
the boxed Text result rather than unboxing its length. Destination SSA roots
are published before retiring temporary roots. Bounds guards precede copying
or replacement and use the same original LocId-aware terminal fault emission.
All existing independent Function/SSA publication checks remain mandatory.
No alternate executable IR, runtime adapter, frame layout or public ABI change.

Work stays bounded by existing Function/root/call caps. Root admission adds at
most eight carrier comparisons for the Text marker; import symbol search adds
seven fixed names. No new runtime allocations beyond existing List/Text value
operations, temporary slots or collector semantics. No compiler-wide speed or
memory qualification is claimed.

Tested: generated empty/append/copy/replace/count/get/collect, Unicode beta/lambda
values, loops and snapshot independence, forced GC and final graph/Text/failure
reclamation. Independent Stage-0/current-native source outcomes agree. An
out-of-range Text get retains original source terminal diagnostics; descriptor,
import effects and argument-type negatives refuse before assembly output.
Deeper nested Lists, user managed aggregates, new typed failure construction and the
remaining combined/fault/physical/four-platform U2 acceptance gates remain.
