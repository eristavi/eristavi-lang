# U2 managed Text/List/identity semantic descriptors

Status: opt-in development on draft PR #111; focused validation pending.
Locked design: `DESIGN_PHILOSOPHY.md`, `LANGUAGE_SEMANTICS.md`, `COLLECTIONS.md`, `IDENTITY_EQUALITY.md`.

The first managed-runtime integration gate adds a **private semantic descriptor
registry**, not a second executable UIR, a new public type syntax or a native
heap/GC layout. The qualified U1/U1b structural type graph is unchanged.
A metadata-owner-scoped registry refers to that frozen graph, with a unique
identity key and exact graph identity, and uses a separate local TypeId
namespace. Every managed descriptor has exactly four words:

- kind: 1 = Text, 2 = List, 3 = identity;
- elementDomain: 0 = structural aggregate graph, 1 = managed descriptor table;
- element: previous descriptor index or existing structural TypeId;
- copyPolicy: 1 = ordinary value/snapshot semantics, 2 = shared identity alias.

Canonical row 1 is Text (1,0,0,1); other rows are List and identity only.
Descriptor rows may refer to earlier managed entries but never forward/cyclic
ones. Distinct List and identity wrappers never intern to the same TypeId.
Repeated identical relationships intern to one deterministic descriptor.
List copyPolicy 1 does not permit physical in-place aliasing; identity
copyPolicy 2 preserves logical sharing, not raw address comparison.
Nested List identity positions reject deep-fixability. Text/view contents
are governed by Unicode 17 and frozen Text semantics, not by this descriptor.

## Accepted boundaries for this incremental implementation

The metadata-backed registry is bounded to 64 descriptors (256 words), and
uses fixed-size owner-charged radix backing. Construction phases use the
existing accounting/cancellation protocol. A storage failure poisons the
registry until close; no partial record can be frozen for publication.
The independent checker reruns the existing structural graph verifier,
validates all records including unreachable type rows, rejects forged
copy policy and missing/stale backing, and reports counts. All code remains
opt-in and uses existing ordinary .eri / bootstrap flow.

**NOT implemented by these descriptors:** canonical UIR managed type
references/operations, actual owned Text/List/identity allocation or copy
lowering, Unicode 17 runtime behavioral conformance for the redesigned UIR,
root-class mapping, automatic machine safe-point publication, recursive
frame lifetime handling, runtime resource adapters, or full four-platform
qualification. The currently qualified owned runtime already supports
Text/List/identity via its separate existing production mechanisms, but
calling those mechanisms from complete redesigned UIR is still pending.

See `HANDOVER.md` for latest tested source head. Keep U2 #74
open and PR #111 draft until all semantic, runtime and qualification gates
are satisfied.
