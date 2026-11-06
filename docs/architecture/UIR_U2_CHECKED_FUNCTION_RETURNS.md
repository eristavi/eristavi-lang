# Typed checked Function returns and recursive native outcomes

Implementation contract, 6 November 2026. Optional private U2 extension;
not source syntax, a public serialized format or a production promotion.

## Meaning before representation

A defined fallible Function has one explicit metadata FunctionId binding. Its
normal signature and checked failure signature are reread from the existing
frozen declarations and version-one fallible registry on every verification.
The binding cannot authorize a different same-signature Function or import.

A new private canonical terminator `return.failure` (47) consumes one SSA
failure payload of the bound function's exact failure type, produces no values
and has no successors. It is observable, with an original nonzero LocId; it is
not a terminal defect/trap and does not replace required resource cleanup.
The owner verifier requires an empty owner stack at either kind of return.
Ordinary returns keep the existing normal signature and opcode 8. Opcode 46
continues to deliver normal and failed results only on their declared edges.
Legacy verification/execution profiles refuse the optional binding/terminator.
No scalar status or global handler flag substitutes for a typed UIR failure.

The existing Function gains one private `definedTarget` integer (zero by default).
It is an owner-scoped FunctionId index, not a new type/IR table, memory address,
verification stamp or executable capability. An opt-in construction API binds
it before body construction, with an exact defined declaration and selected
fallible registry entry. The independent verifier rereads it even if revision
and frozen backing are unchanged. Other transformation profiles reject bound
fallible functions until they support the new contract explicitly.

## Initial native contract

Extend the existing whole-Function emitter and SSA liveness, not the earlier
closed helper/chain adapters. The selected profile admits the exact bound self
invoke and its normal/failure continuations over all original canonical blocks.
It reuses `u2_root_map.create/verify` to check every original invoke's exact
failure-destination root and declared failure type before emitting any code.
It transports an existing owned saved FailureContext pointer for the declared
failure payload type. Those SSA words are class-5 roots; Text/List/identity
remain class 1. This is not arbitrary failure construction or aggregate layout.

Private SysV arguments: RDI packed inputs, RSI registered class-1 normal-result
root words, RDX normal capacity, RCX registered class-5 failed-result root word.
Zero, one or two normal results are admitted. No-value success produces no
canonical SSA result or fake Void; unused machine return registers are cleared.
Normal machine outcome: R10=0, RAX/RDX normal words. Failure: R10=1,
RAX=saved FailureContext pointer, RDX=0. This status is a private machine ABI
encoding of two already typed UIR outcomes, not the UIR's failure value.

Each callee publishes its chosen managed normal results or failure context
into the caller's appropriate registered root words before retiring its own
scope. Parent liveBefore roots remain published throughout the call. The
caller stages results, selects exactly one original opcode-46 edge, performs
parallel transfer of edge-produced and carried values, publishes destination
liveEntry roots, then clears call temporary roots before any destination GC.
Negative outcome ordinals are not interpreted as positive SSA slot indices.

One additional class-5 temporary and one caller failure-root pointer extend
this profile's frame. Two existing raw return-save words are reused for invoke
outcomes. For V SSA words and R selected roots, checked stack allocation is
`align16(8*V + 8*R + 320)`, plus the saved register and return address; the
existing nonfallible profile retains its previous 304-byte constant. There is
no process-global recursion counter, alternate executable IR or new collector.
The existing 64-root, 64-block/256-value/512-instruction profile remains an
explicit admission cap. At most eight selected types include the failure
carrier (up to seven ordinary managed carriers in this checked profile).

The canonical Function's extra integer increases the owned graph backing by
one 32-byte value cell; its existing control lease and all accepted owner
peak/traffic limits remain unchanged. The independent physical observer is
updated from 17 to 18 fields and cross-checked against actual allocator records
and post-GC zero backing, rather than silently undercounting the new field.
No broad stack/RSS/GC-pause or performance claim follows from these bounds.

## Acceptance and boundaries

Independently verify wrong binding/owner/kind/signature/failure type, malformed
and unreachable failure returns, scalar payloads, attributes, missing LocId,
wrong normal/failure ordinal transport, stale metadata and missing roots.
Execute genuine canonical checked recursion with parent-private Text and live
class-5 contexts, success and failure propagation, caught/handled outcomes,
forced GC while multiple frames coexist, two managed normal returns, and full
reclamation. Compare a separate source/reference oracle where representable.

This extension does not itself complete arbitrary nested managed producers,
new failure constructors, automatic File acquisition/cleanup on every exit,
mutually recursive modules, general allocator/bad-root/RSS/pause/sanitizer
qualification or the final four-platform/finished-batch gates. Those gates
remain required; keep #74 open and #111 draft until all actually pass.
