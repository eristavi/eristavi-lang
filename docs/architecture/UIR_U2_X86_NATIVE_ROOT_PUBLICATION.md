# U2 x86-64 native scoped-root publication

Status: opt-in focused-tested development slice, 3 November 2026.
Governing philosophy and semantics remain unchanged; no extra executable IR,
source keyword, 32-byte public ABI alteration or new collector is introduced.

## Mechanism

The existing canonical opcode-46 checked invoke and independently verified
u2_root_map.eri supply one exact class-5 saved-failure root descriptor per
checked instruction, including unreachable instructions. The private
u2_native_root_x86_64.eri re-verifies this metadata on emission and generates
actual x86-64 assembler for scope binding, instruction-specific publication
and release. This uses the existing owned runtime evn_bind_roots ABI:
RDI=current scope, RSI=caller-owned writable root words, RDX=class bytes,
RCX=root count. The generated binder zeroes every root word before publishing
the scope root descriptor. Each publish writes the saved-failure pointer to
a unique slot; release clears it. Root storage is caller-owned and can reside
on the current stack frame, making independent recursive scopes possible in
principle. The emitter does not allocate heap storage, install a global
root table or change the collector. It handles at most 128 root records;
emission and initialization are O(N), publish/release O(1).

## Verified scope

[CI #41601414665](https://github.com/eristavi/eristavi-lang/actions/runs/41601414665):
81 executed / 78 passed / 0 failed / 3 skipped. A canonical five-invoke
UIR fixture generated native bind/publish/release helpers. The native probe
used the emitted helpers for one saved typed Text failure, forced multiple
collections, read the preserved payload, released the root and confirmed
reclamation.

[CI #41602009013](https://github.com/eristavi/eristavi-lang/actions/runs/41602009013):
81 executed / 78 passed / 0 failed / 3 skipped on source commit
a07478c1e84d8f8e9cc31d72ba9dde25297cf87e. The extended native
probe publishes two independent saved-failure records into two different
generated slots, forces GC, releases the first root, verifies the second
record remains typed and alive through collection, then releases the second
and verifies reclamation. The prior ordered-secondary Text, root-map
corruption and cleanup tests remained green.

## Unfinished acceptance

The checked-failure construction and control flow of the native probe are
handwritten test assembly; this is not an end-to-end native lowering of new
canonical UIR. Native backend register/stack allocation and independent
liveness validation for every managed Text/List/identity value, every
checked edge, nested cleanup, loops and recursion are still required.
Resource runtime adapters, Unicode17/value-copy-vs-identity semantics,
allocator/physical and fault evidence, independent reference/native parity,
and final completed-batch four-platform qualification remain mandatory.
No production merge or U2 issue closure follows from this development slice.
