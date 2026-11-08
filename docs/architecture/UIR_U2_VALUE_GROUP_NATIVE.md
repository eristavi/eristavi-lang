# Aggregate bindings across closed checked groups — 8 November 2026

Private U2 extension, no source syntax, public ABI, frame, root layout, ownership
or runtime adapter changes. emitValuesCheckedGroup carries the existing shared
carrier-aligned native aggregate binding vector through the original complete
group preflight and emission. emitCheckedGroup retains concretely typed empty
bindings. Both use one core; original closure/target/label/count limits, fresh
Function/SSA/root checks, preflight-before-any-output and machine publication
verification remain. Constructor and context capture helpers are unchanged.

The canonical fixture has two distinct defined FunctionIds and bodies, calling
one another through original checked invokes. Both construct error aggregates
and saved contexts, retain parent class-5 snapshots across the child, and return
fresh failures through the original handoff. Different sibling base codes
42/52 make actual dispatch observable: normal-child parent failures are 43/53.
Depths 0/1/5/16/64 cover success and failure; beta payload and discarded lambda,
typed matching, returned context count and full reclamation remain checked.
Independent mutual-recursion interpreter/current-C source outcomes agree.

Malformed layout vector, duplicate labels, missing member, wrong sibling target
and invalid source origin in the second body refuse before any assembly. The
last case allows the first member's preflight to succeed, then independently
rejects the later member. Existing capacity/work-refusal cleanup, two-result
handoff and single-body producer are immediate compatibility evidence.

Still pending: aggregate/producer bindings in File-owned groups/calls, existing
already-live primary restrictions, carrier-overlap cases, other field families,
identity-containing aggregates and kind-4 operation/deep-fixability composition.
Hostile-root/allocator/sanitizer/physical/broad independent proof, current owned/C
and hosted timeout repeatability, reconciliation and final exact-head platform/
completed-batch qualification remain open. Existing C identity-list qualifier
warnings are retained; no warning suppression or compiler change in this batch.
