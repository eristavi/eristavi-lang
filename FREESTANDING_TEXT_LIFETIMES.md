# Freestanding managed Text lifetime slice

Status: stacked review candidate, Linux/System-V x86-64 only; automatic qualification pending.

This extends the Text storage foundation with `evn_text`, Text-aware `evn_copy`,
Text-preserving scope exit/unwind and exact-byte Text output. Public syntax, ordinary
value semantics, ownership rules, and pinned Unicode 17 behavior are unchanged.
Text still cannot be indexed directly; no views are enabled by this slice.

The existing native ABI is retained: type 4 at +0, UTF-8 byte length at +8, immutable
data pointer at +16, zero tail at +24; slot link at +32. Copying a Text value shares
immutable storage. `evn_store` copies the entire existing value representation, so an
outer binding can safely receive Text created in a nested scope. Scope leave saves
all 32 bytes before freeing slots, re-slots the result, then collects. Leaving an
outer scope while nested scopes remain active preserves the same unwind behavior.

A separate private five-word registry tracks each owned Text buffer: next, original
reservation base, exact mapped length, logical length, and mark. The fixed layout is
checked alongside the unchanged value/slot/scope layouts. Registry records use the
owned allocator; byte mappings use the preceding validated storage helper. Empty
Text has null data and no buffer record. Storage is never freed merely because one
alias disappears. Collection runs after a constructor has installed its result slot
and after scope exit has re-slotted its escaping result, never in a construction gap.

The supported typed root graph consists of all active value slots, matching the
existing native heap collector's slot-root policy. Only type-4 slots mark Text
records; data pointers are matched to tracked bases before any heap payload is
interpreted. Duplicate aliases mark once. Sweep releases unreachable mappings with
the original exact base/length and frees their registry records. Root-map metadata
continues to be stored by the scope ABI; this slice does not implement root-map-based
slot pruning. No aggregate, interior view, failure, or resource graphs are enabled.

This is deliberately not the complete native collector migration. Slots retained
inside a long-lived scope retain their Text buffers. Root-map slot reclamation is
needed to bound ordinary loop temporaries independently of scope exit. The initial
registry lookup is linear and the prototype reserves pages per nonempty Text; no
performance or production-memory-efficiency claim is made. The private live-buffer
counter is a probe aid, not a public diagnostic API or RSS measurement.

The hosted regression covers shared copies, replacing an outer value with nested
Text, escaping results, outer-scope unwind, embedded NUL, multilingual byte output,
100 scope churn cycles with stable live Text-buffer count, full tracked release,
invalid UTF-8 faults and a real `.eri` function returning Text on the Eristavi-written
compiler path. ELF checks require no runtime imports, loader, dynamic section or
executable stack. No tests were manually run: normal GitHub CI supplies qualification.

The Text runtime is an explicit composition via `value_output_x86_64.textSource()`;
the previous scalar-only composition remains available and rejects unsupported kinds.
Text equality/concatenation, typed root-map slot pruning and Unicode views remain next.
The compiler/generator still use the bootstrap runtime and GNU as/ld are still required.
