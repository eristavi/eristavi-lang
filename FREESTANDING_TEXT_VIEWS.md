# Freestanding byte/scalar Text views

Status: Linux x86-64 review candidate; automatic CI qualification pending.

The explicit view runtime composition adds the existing `evn_view`, `evn_count` and
`evn_index` ABI for byte and scalar views. Source syntax and read-only view semantics
are unchanged. Dynamic view tags use the compiler-owned `ev_types` descriptors:
kind 12 and names `bytes`/`scalars`. Descriptor tags and storage are trusted compiler
ABI input, not arbitrary user addresses. Grapheme views are deliberately not enabled.

The existing 32-byte value layout is retained: dynamic type at +0, underlying UTF-8
byte length at +8, data pointer at +16 and view kind at +24 (1 bytes, 2 scalars).
Copies and scope returns preserve every field. The typed Text heap marks backing
storage from Text and supported view slots, so views can escape their source scope
and remain valid after the original Text slots disappear. Scalar indexing copies one
complete scalar into an independently managed Text; byte indexing yields Int 0–255.
Neither operation exposes writable storage or source-level pointers.

Counts/indexing inspect validated immutable UTF-8; scalar width comes from canonical
lead bytes, with span checks before slicing. Empty counts are zero, NUL is one byte
and one scalar, and negative/end indexes use the established bounds-fault message.
No normalization, grapheme approximation, host Unicode fallback or public lifetime
controls are introduced. View construction, copying, count/index results and scope
escape all complete their result before reaching a protected allocation safe point.

`value_output_x86_64.viewSource()` is the explicit composition; the existing scalar
and Text-only compositions remain intact. Applications provide their normal type
descriptor table; no fake table or weak-symbol fallback is linked into the runtime.

Automatic CI covers returned/copied views, source-scope escape, UTF-8/NUL observation,
2,000 allocation churn iterations, empty counts, byte/scalar bounds faults, complete
tracked buffer release and static/no-import ELF execution. No tests were run manually.
Grapheme views and Unicode library operations are next. This is not completion of
Float, aggregate/identity, failure/resource, compiler bootstrap or object/linker work.
