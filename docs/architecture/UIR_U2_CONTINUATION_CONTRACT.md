# U2 continuation boundary — initial integration contract

**2 November 2026; implementation staging, not a public encoding or completed
canonical U2 profile.** Preserve the typed UIR proposal §§8–12 and all frozen
language rules. This records how verified private exit plans will connect to
canonical UIR. No new opcode numbers, source syntax or ABI layout are reserved.

| Boundary | Required typed behavior | Implementation state |
| --- | --- | --- |
| Fallible call | Signature declares normal result sequence and checked failure context type; exactly one normal/failure edge executes | Pending canonical registry/builder/verifier |
| Normal edge | Successful results exist only on this edge and enter exact typed destination parameters | Destination arity/type binding implemented; edge-specific availability pending |
| Failure edge | Typed primary/secondary context exists only here; success results are unavailable | Structural typed-payload destination binding implemented; managed context/executable edges pending |
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

## Typed destination binding — implemented slice

`u2_continuation_bind.eri` binds version-one private descriptors to the EXISTING
canonical Metadata signatures/types and Function block/value parameter tables.
It neither creates a second executable IR nor adds an executable opcode.
The descriptor identifies the exact function/type-graph keys, function revision,
source and distinct normal/failure destination blocks, original LocId and two
result-tuple signatures (each has zero inputs). The normal tuple permits 0–16
results under this bounded private profile. Failure requires one declared
aggregate payload, never a scalar error-code substitute.

The structural aggregate is a language-neutral failure-payload shape supported
by current U1b types. It is NOT Eristavi's complete managed FailureContext:
Text/error sets, secondary context storage and GC roots remain unimplemented.
The existing independent aggregate graph gate remains required; this adapter
does not replace whole-metadata/type-graph verification.

Independent binding verification rereads both canonical destination parameter
sequences and exact types/definition owners/ordinals, checks ranges before
offset arithmetic, rejects entry/shared/source destinations, stale revisions,
foreign keys and unknown versions. It adds no ledger-owned storage or IR edits.
No selected-success flag skips checks of the failure destination.

`u2_cleanup_link.eri` prepares or freshly checks the combined private exit plan
and typed destinations. Owner and exit origin must match exactly. A successfully
verified link is not a canonical publication stamp; later consumers revalidate.
Cleanup plan allocation remains charged/closed through the prior checked entry.

Focused tests exercise zero and multiple normal results, an aggregate failure
payload, 16 same-revision canonical pool mutations per probe, overflowed ranges,
foreign/stale descriptors, scalar failure rejection, work refusal, restored
tables, valid-but-mismatched source origins and forged linked cleanup routing.
Both probes close all owners. Raw results and hashes:
`docs/evidence/2026-11-02/u2-continuation-binding.json`.

Still pending: register actual fallible signatures on FunctionIds and canonical
terminators/edges, introduce edge-produced payload definitions and verify their
availability/dominance, then scoped resource ownership and managed runtime/root
integration. Current bindings execute no calls and do not prove those properties.
