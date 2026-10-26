# Freestanding Text storage foundation

Status: Linux x86-64 review candidate; automatic CI qualification pending.

This is the first storage slice for the Text runtime migration. It adds no public
syntax, types, manual memory controls, normalization rule or Unicode-version change.

`src/runtime/text_buffer_x86_64.eri` emits two private operations:

- `erist_rt_utf8_valid(pointer, count)` returns a normalized Bool machine word.
  It accepts ASCII (including embedded NUL), valid two/three/four-byte scalar
  encodings and empty input. It rejects stray continuations, overlong encodings,
  surrogates, scalars above U+10FFFF, invalid lead bytes and truncated sequences.
- `erist_rt_text_buffer_copy(pointer, count)` validates before allocating, reserves
  independent zero-initialized OS storage, and copies through the existing verified
  memory lowerer's one-byte store profile. It returns the original reservation base,
  exact mapped length and a private status. Empty success requires no reservation.

The trusted input ABI requires readable, stable source bytes for the specified count
throughout the operation. This includes compiler-owned literal storage; this helper
cannot establish arbitrary foreign-pointer validity. Null nonempty input, pointer-end
wrap and oversized copy requests are rejected before dereference. Raw source reads
are confined to this explicitly trusted input boundary. Destination writes and owned
byte reads use reservation-aware verified accessors. Their bounds cover the exact
mapping; callers separately retain logical Text byte length, excluding page padding.

Copy ABI: `rdi` source, `rsi` logical count; `rax` original base, `rdx` exact mapped
length, `rcx` status (0 success; 1 invalid input/UTF-8; 2 unsupported size; 3 reservation
failure; 4 internal store failure). On failure base and mapped length are zero. A
store failure releases the new reservation before returning. Callee-saved registers
and System V call-stack alignment are preserved. The successful owner must release
the original base/exact mapped length once, after every reference expires.

These are compiler-private storage operations, not ordinary `ev_value` Text helpers.
They are intentionally not wired into the scalar application runtime yet: scalar
scope leave only preserves scalar payloads and no heap collector traverses its roots.
Exposing Text there before lifetime integration would permit invalid references.

The next slice must integrate managed Text allocation/root tracking, scalar/Text copy
and scope escape semantics, then constructor/output/equality/concatenation. Existing
byte/scalar/grapheme views and pinned Unicode 17 tables must follow without replacing
grapheme count with byte or scalar count or introducing implicit normalization.

The added hosted regression checks encoding boundaries, multilingual/combining/emoji
bytes, embedded NUL, independent snapshots, page rounding, exact release, rejected
reservation-boundary accesses, and a truncated sequence ending at a protected guard
page. It checks static ELF imports and execution with an unavailable PATH. Tests have
not been manually run for this change; normal GitHub CI is the qualification path.
The generated target uses Linux syscalls and Eristavi-emitted code only. The generator
still uses the existing bootstrap runtime and assembly/linking still require GNU tools.
