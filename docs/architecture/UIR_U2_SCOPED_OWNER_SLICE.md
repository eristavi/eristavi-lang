# Initial canonical scoped-owner verification

Selected before implementation, 2 November 2026. This is an optional bounded
verification slice, not full resource execution, managed types or U2 acceptance.
It consumes the canonical Function pools and the selected fallible registry.

The first profile admits one explicit resource contract: an acquisition
FunctionId returning one opaque aggregate handle and a close FunctionId taking
that handle and returning no normal values. Both use typed checked-failure
edges. The selected handle TypeId is reserved for resource interpretation in
this profile; ordinary construction, copying, wrapping, returning and other
calls cannot use it. This is a private representation contract, not a new source
type or a raw address. Managed resources and production native adapters still
need independent type/root/runtime acceptance.

Each function owns lexical scopes (parent scope, cleanup LocId), block owner
signatures and signature entries (scope, canonical block-parameter ValueId).
Scopes are indexed in lexical preorder with earlier parents. Entry starts empty.
An acquisition introduces the next scope only on success. Close consumes the
innermost owner before BOTH outcomes, retaining its exact cleanup origin.
All remaining owners travel explicitly through canonical edge arguments.
Returns require an empty stack. Unsupported owner observation/capture refuses.

Before candidate measurements, select maximum depth 128 (the existing cleanup
policy), at most 65,536 scopes and 262,144 encoded signature entries, subject
to original function/shared/request memory, traffic, work and watchdog limits.
These are admission ceilings, not a claim all maxima simultaneously fit.

After fresh independent canonical verification, scan each block locally against
its signature. Use dense per-ValueId role/active indices, a topological type
containment map and a reusable 128-owner stack. Validate every edge against the
target signature, including loops and dead blocks. No path enumeration,
per-block register masks or ownership fixed point. Cost is O(N+V+T+S), including
encoded type fields and owner-edge arguments; reusable scratch is
2(V+1)+(T+1)+256 words, plus the stored profile. All accesses use the existing
charged word adapter; report work separately from actual allocator backing/RSS.

Acceptance includes nested acquisitions, failure before acquisition, failure
during close, reverse cleanup, loop signatures, missing/dropped/duplicated or
consumed owners, ordinary copy/escape and malformed dead signatures. A passing
owner verifier does not prove runtime adapter behavior or primary/secondary
failure composition. Those remain mandatory downstream gates.
