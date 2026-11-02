# U2 continuation boundary — initial integration contract

**2 November 2026; implementation staging, not a public encoding or completed
canonical U2 profile.** Preserve the typed UIR proposal §§8–12 and all frozen
language rules. This records how verified private exit plans will connect to
canonical UIR. No new opcode numbers, source syntax or ABI layout are reserved.

| Boundary | Required typed behavior | Implementation state |
| --- | --- | --- |
| Fallible call | Signature declares normal result sequence and checked failure context type; exactly one normal/failure edge executes | Pending canonical registry/builder/verifier |
| Normal edge | Successful results exist only on this edge and enter exact typed destination parameters | Pending |
| Failure edge | Typed primary/secondary context exists only here; success results are unavailable | Pending |
| Acquisition | Successful edge introduces one lexical resource owner; failure introduces none | Pending |
| Close | Consumes the innermost active owner on BOTH successors, including checked close failure | Private plan routing independently verified; canonical ownership pending |
| Pending return | Payload travels on normal cleanup path; first cleanup failure cancels success | Private plan mode/route verified; typed payload transport pending |
| Already failing exit | Preserve primary type/data, append close failures in cleanup order | Private failure suffix verified; runtime context pending |
| Terminal defect | Standalone process termination; no checked failure edge or cleanup guarantee | Existing locked policy; no new adapter here |

The initial selected extension must be explicitly versioned and optional. A
consumer rejects unknown required contracts and cannot execute unsupported
managed/checked/resource operations as core scalar operations. Full type/root
metadata is required for aggregate and failure-context references. A scalar
error code or globally mutable error flag is not a substitute for a typed
failure context. Existing runtime helpers may appear only behind checked adapters.

Owner signatures must match each target edge exactly, including the surviving
lexical prefix. Unreachable blocks receive structural/type/local-owner checks.
The future canonical verifier must establish edge-specific payload availability,
SSA dominance and scoped ownership over loops and multiple exits. The current
private plan verifier establishes none of those whole-function properties.

Before integrating a plan, independently revalidate its exact current rows,
metadata owner, obligations and source origins. Frozen storage and unchanged
revision numbers confer no trust. `u2_cleanup_verify.prepare` is the new safe
private construction entry: construct, independently verify and release the
entire private plan on either invalid-plan or resource-limit refusal. Direct
builder output still requires fresh verification at every consuming boundary.

Failure contexts need amortized O(1) ordered secondary append and explicit GC
roots; resource owners cannot enter ordinary copy, identity or aggregate paths.
Whole-function expansion/root/runtime policies remain separate admission gates.
The preselected private depth/record/word and U1 ledger budgets remain unchanged.

Next implementation: canonical versioned signatures and typed fallible
terminators, then independent owner-signature/payload checks and runtime adapters.
No production frontend migration or U2 completion follows from this document.
