# File ownership with ordinary aggregate bindings — 8 November 2026

emitFileValuesChecked and emitFileValuesCheckedGroup supply the existing shared
carrier-aligned native aggregate binding vector to original File single-body
and homogeneous-group verification/emission cores. Existing APIs keep empty
bindings. Existing owner/SSA/descriptor/target/label/count/layout proofs, group
preflight-before-output, pending-return cancellation and lexical root handling
remain. No new source syntax, runtime/resource adapter, ABI, frame or semantics.
Nonexecuted concrete shape seeds address bootstrap generic specialization only.

The canonical fixture keeps a record containing its pending integer and path
Text across checked close, reads it on normal and failed-close paths, and leaves
all owner consumption to original lowering. Single and one-member group entries
execute normal/open-failure/close-failure cases with exact close counts and full
reclamation. Invalid bindings refuse without retaining a Plan. A further single
entry constructs a fresh typed context from the record after close, returns it
via class 5 and verifies one close plus full reclamation. This does not exercise
new aggregate bindings across a sibling or while a primary is live at close.

Remaining boundaries: primary-bound single/chain entries and mixed owning/
non-owning group entries still pass empty bindings; already-live-primary refusal
at owning defined calls remains. No blanket claim that File/producer integration
is complete. Original File operations and saved/typed context adapters were reused.
Known C identity-list qualifier warnings remain, with no suppression. Full final
qualification/owned repeatability and broader fault/physical evidence are pending.
