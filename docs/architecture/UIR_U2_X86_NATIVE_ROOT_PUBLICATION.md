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

## Native slot placement verifier — unqualified follow-up

The private `u2_native_slots_x86_64.eri` plan binds the exact verified
canonical root-map object, function/type keys, and source revision to a
bounded one-word-per-checked-invoke x86-64 frame layout, including dead
instructions. It independently checks every record before any assembly
emission. The closed placement is contiguous at offsets `0, 8, ...`, with
class 5 for every root, a separate scope-pointer word immediately after
the roots, and a 16-byte-aligned frame allocation including that word.
A missing/duplicate/overlapping/misaligned/wrong-class/foreign/stale/closed
placement must fail rather than silently reuse another slot. The emitter
now consumes verified offsets instead of constructing unexamined displacements.
Its compatibility `emit` entry creates and releases that private plan.

The focused test additionally checks forged instruction IDs, wrong classes,
misalignment, overlap, missing entries, a stale revision, foreign metadata,
closed plans and returned owner backing; a separate Python assembler oracle
checks unique bind, publish and release offsets before native execution.
This does **not** establish general canonical SSA live intervals, root
publication for other managed values, recursion, arbitrary loops or
machine lowering of complete UIR bodies. Preserve draft #111 and issue #74
until the remaining U2 gates pass. The exact source head and CI evidence
are recorded in HANDOVER.md after the smoke completes.

## Canonical SSA liveness, root-obligation analysis (unqualified)

The private `u2_ssa_liveness.eri` analyzes the existing Function value,
instruction and edge tables, not an alternate executable representation.
It selects explicit structural TypeIds, bounds each analysis to 32 tracked
values and 64 blocks, and maps predecessor edge arguments to each live
target block parameter independently. Invoke-produced negative edge values
are **not** predecessor SSA uses. Loop backedges converge through a monotone
bounded fixpoint. Uses at allocating calls and checked cleanup are queried
before the real instruction; a call's newly produced value is live only
after its definition. Verification independently recomputes all selected
root-obligation facts and rejects mismatches. This is the **precondition**
for native root publication, not publication itself.

These U1b aggregate TypeIds are not automatically GC pointers. A further
closed, independently verified managed type/root-class registry and actual
register/stack lowering must identify Text, List and identity references
before emitted machine frames can publish the complete correct root set.
Do not equate this liveness slice with full U2 coverage or run final CI
for an uncompleted backend.
