# U2 private checked File acquisition bridge

Development component only; whole-Function File integration remains incomplete.
Governing contracts: DESIGN_PHILOSOPHY.md, LANGUAGE_SEMANTICS.md,
RESOURCE_CLEANUP.md, UIR_U2_SCOPED_OWNER_SLICE.md and
UIR_U2_FAILURE_ROOT_BOUNDARY.md. No source syntax or production ABI changes.

`u2_file_acquire_x86_64.emit` verifies the original canonical Function and
scoped-owner profile, the canonical checked-failure root map and the selected
opcode-46 acquisition. The metadata target must be the private version-one
`u2.file.openRead.v1` imported declaration (kind 2, effects 8, version 1),
with one opaque Text argument and the profile's one File result. Text, File
and failure carriers must be distinct. This is a new explicit private binding,
not a source-language function or a claim that arbitrary imports are File opens.

Emission checks precede all assembler output. The bridge reuses the existing
owned `erist_rt_file_open` read-only path and runtime handler adapter. It does
not reimplement File operations or deterministic cleanup.

Private embedding ABI: RDI is a caller-rooted boxed Text; RSI points to an
empty, registered class-1 result root; RDX points to a distinct empty,
registered class-5 failure root; RCX is the embedding runtime's File type
number. RAX is the selected result, R10 is 0 (success) or 1 (checked failure),
and RDX returns zero. Canonical type numbers never stand in for runtime numbers.

On success, publish the boxed File before handler retirement. On failure,
restore abandoned runtime slots/scopes before saving the typed failure, publish
the saved failure before clearing the runtime's current-failure root. Terminal
faults remain terminal. No output word may be reused until its prior result
has been consumed under the caller's ownership/root protocol.

The caller must establish root registration, retain the path through the call,
map actual canonical SSA inputs and outcomes, and consume the File through
verified cleanup. This helper does not verify an arbitrary caller's machine
addresses. No new collector or shadow executable plan is introduced.

Still required: whole-Function native acquisition/close dispatch and SSA owner
moves, explicit pending-failure binding for cleanup (never substitute an empty
context for a propagating body failure), all handler/normal/checked exits,
pending scalar/managed return transport, combined fault/root proofs and final
qualification. This bridge alone does not close any full U2 acceptance gate.
