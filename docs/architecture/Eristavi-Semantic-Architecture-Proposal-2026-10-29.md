# Eristavi semantic-analysis architecture — agreed design
Date: 2026-10-29
Status: Architecture and acceptance criteria agreed on 2026-10-29. Implementation and validation have not started. Candidate optimizations remain subject to the documented measurements; detailed UIR and lowering contracts remain separate decisions.
Baseline: inspected repository snapshot 8af0ffe3350c737550c3ab0e6c3fa89f60f6f091.
Scope: Binding, static type inference, inferred generic contracts, flow-sensitive facts, checked failures, resources, and the semantic-to-UIR boundary. Preserve the source language.

## Recommendation
Analyze the agreed immutable indexed AST using explicit binding identities, immutable type descriptions, attempt-owned inference state, and immutable published semantic facts. Separate services for binding, inference, flow, checked failures, and resources, while keeping their invocation order compatible.

These are logical service boundaries, not a requirement for six complete AST traversals. Reuse a structured traversal where checks share context. Do not introduce another mandatory executable Typed IR or a second serialized control-flow program.

## 1. Evidence and limits
The owned semantic model currently represents concrete types, inference variables, variable links, and inferred property flags in one mutable Type record. semantic_types.resolve follows links without compression; the Python typesys.resolve already compresses paths. No new timing measurement attributes a significant fraction of compilation to this difference.

Scope bindings, clone maps, failure names, and several lookups are linked records. Expression facts are attached to nodes through token/location structures, with newest-first lookup. Some target/mutability checks call expression analysis again on the same path. These establish repeated operations and representation coupling, not their measured performance share.

Analyzer state includes mutable specialization maps and inference variables. Existing generic-call handling deliberately freshens parameter/result relationships; this behavior must survive the redesign.

Semantic blocks currently return a Boolean termination result. Optional-value narrowing uses linked mutable records. Resource checking has std.files-specific cleanup assumptions. These are opportunities for clearer contracts; no unsoundness claim is made without a focused reproducer.

Reviewed sources: src/compiler/semantic.eri, semantic_model.eri, semantic_types.eri; compiler/erist/semantic.py and typesys.py; SCOPE.md, GENERICS.md, CONDITIONS.md, RESOURCE_CLEANUP.md; recursive-inference tests and owned semantic conformance/report machinery.

## 2. Ownership and products
| Product | Owner and mutability |
|---|---|
| Parsed syntax | Immutable module AST owner |
| Declaration/field/binding identities | Session/module registries with explicit scope |
| Concrete type descriptions | Immutable canonical type store |
| Type variables and unification links | One semantic stage attempt |
| Flow state and cleanup stack | One body-analysis attempt |
| Published generic contracts | Immutable schemes with bound parameter slots |
| Published body facts | Immutable, keyed by AST ID and analysis owner/context |
| Diagnostic builder and constraint provenance | Attempt-owned, formatted only when needed |

Use checked 32-bit DeclId, BindingId, FieldId, TypeId, and appropriate auxiliary references with distinct APIs. IDs identify their owning tables; do not serialize session numbers as permanent identities.

A TypeId denotes an immutable concrete description, not a mutable inference cell. Generic frozen type references can refer to bound parameter slots owned by a scheme. No live mutable TypeVar crosses the publication boundary.

Publish only after required validation completes. Failed/cancelled attempts release mutable state and cannot leave a ready contract. Completed independent products remain valid under the agreed module-session rules.

## 3. Binding and scopes
Collect module declaration headers before resolving their references, preserving order-independent module declarations. Assign DeclIds once. Keep import/export namespaces explicit and preserve existing ambiguity rules.

Represent each local declaration with BindingId and every resolved name use with its binding/declaration target. Later stages should not repeat string-based name resolution.

Use an active-local lookup table plus a scope undo stack as the initial candidate representation. An initializer is checked before its new binding becomes visible. On leaving a scope, remove only entries introduced there. This implements declaration-before-use, no self-reference, and the existing no-shadowing/redeclaration rules without inventing new namespace restrictions.

Parameters, loop variables, resource bindings, and handler error bindings use the same binding mechanism. Separate functions have independent local state. Scope conflict diagnostics retain both declaration spans.

Module collection, body binding, and type checking may be interleaved according to the compatibility schedule; an eager whole-project binding pass must not change the first diagnostic accidentally.

## 4. Concrete types and inference references
Store concrete primitives, nominal types, List, maybe, identity, resource types, and Text views using explicit variants. Preserve no-value and checked-error categories where current semantics needs them; these are compiler concepts, not new source type names.

Nominal type identity includes its logical declaring module/DeclId, not a diagnostic Text string or physical checkout location. Constructed concrete types may be canonicalized by constructor and child TypeIds.

During inference, references distinguish concrete types, inference variables, and applications containing variables. A List of an unresolved variable cannot be treated as a complete immutable concrete TypeId.

Keep immutable descriptions independent of the mutable solver. This is the architectural commitment; canonicalization policy and hot-cache choices remain measurable implementation decisions.

## 5. Inference solver
Keep static unification with occurs checking and Eristavi's current assignment/join rules. No dynamic fallback, implicit numeric widening, or new source generic syntax.

The proposed solver representation uses indexed variable cells with parent/rank, optional binding, and explicit constraints. Union by rank/size and path compression are candidates for the owned implementation; compare link visits and time before claiming a benefit. Both techniques operate only on attempt-owned state.

Merge all obligations when joining variables: allowed operations, deep-fixed eligibility, and equality requirements. Distinguish unconstrained from an empty/impossible allowed set. Binding a variable to a concrete type must discharge or retain its obligations; it cannot silently drop them.

Use bounded iterative occurs checks for deeply constructed inference types. Keep finite representation limits explicit. Distinguish recursive inference equations from legal nominal recursion rather than rejecting every type graph cycle.

Retain compact cause/source information for constraint failures, so diagnostics can explain the two conflicting requirements without exposing allocation-order type-variable numbers.

## 6. Inferred generic contracts and recursion
Derive immutable generic schemes from declaration/body relationships. For example, preserve(value) has one bound parameter shared by its argument and result. Operation requirements are part of the scheme, including inferred List relationships and fixed/equality eligibility.

Every call instantiates the whole parameter/result relationship with fresh variables using one substitution map, preserving repeated variables across the signature. Interleaved Int and Text calls cannot mutate the published scheme or each other's inference state.

Track result-inference dependencies separately from ordinary call edges. Direct/mutual calls are not by themselves an invalid inference cycle. Preserve explicit-result recursion and permitted no-value recursion. Require an explicit returns contract where a result actually depends cyclically on an unresolved inferred result, as the language specifies.

Analyze the generic body under its inferred relationships and validate concrete uses against the scheme. Any specialization-specific semantic work has a distinct context key; a single ExprId table cannot be overwritten by incompatible specializations.

Specialization keys use declaration/template identity, canonical type relationships, relevant dependency/body fingerprints, and compilation profile. Do not derive identity by formatting user-facing type names or persisting fresh variable IDs.

## 7. Explicit semantic facts
For each required expression/context, record its frozen type reference, resolved binding/call/field target, checked-failure information, and any required place/value or literal information.

Facts are addressed directly by the indexed AST and their analysis owner. Flow-sensitive information additionally names its program point/flow context. Do not reuse a result merely because the AST node matches if narrowed bindings or the analysis context differ.

Analyze an assignment destination through a dedicated place operation that returns root binding, projections, target type, mutability/resource restrictions, and applicable expression facts. This avoids repeatedly walking and rechecking the same base through independent mutable(), target(), and expression() routines.

Place metadata is semantic data. It is not another executable instruction IR and does not decide machine addresses or ABI.

Facts distinguish not-required/unreachable nodes from analyzed nodes. Do not manufacture an unknown or no-value type for a missing required fact. Downstream lowering receives only complete facts for code it must lower.

## 8. Flow and function completion
Use a structured flow summary with distinct outcomes: normal continuation, value return, bare return, checked failure, and divergence when current semantics can establish it. This replaces an overloaded Boolean in the analysis contract.

Maintain branch-local optional-value facts keyed by BindingId. Fork incoming facts for alternatives; merge only normal successors. Preserve narrowing after the other branch terminates. Invalidate a predicate when a write can change it; do not indiscriminately invalidate every local after every call.

Respect short-circuit control flow and condition evaluation order. The initial migration preserves the currently accepted narrowing patterns. Expanding accepted compound-condition proofs is a separate conformance decision, even when the new representation could support it.

Loops require conservative joins and bounded worklists if a fixed point is necessary. Do not promise a post-loop fact not valid on every surviving path. Do not silently classify any while loop as divergence merely to satisfy a return check.

Use transient control points, edge facts, or structured summaries where useful. There is no separately materialized instruction-level semantic CFG, no new mandatory IR verifier, and no requirement to serialize this analysis state. The later UIR design owns executable basic blocks.

Preserve the existing policy for checking unreachable code during migration. Changing which unreachable errors are reported needs explicit review.

## 9. Checked failures
Represent failures by resolved error-type identities through a small deterministic set interface. Choose sorted small vectors, bitsets, or interned sets from measured cardinalities rather than assuming one representation is optimal.

Keep checked failures distinct from arithmetic/bounds/runtime defects and from mutation or I/O effects. An empty fails set does not mean a function is pure.

Function fails contracts remain explicit. try checks the surrounding propagation contract. else error checks handler typing, ordering, coverage, and required path termination. Catch-all handling preserves the primary error binding and its propagation context.

Semantic checking records which operations are discharged by a handler or propagated by try. It must not lose callee or argument failure obligations when constructing expression facts.

Full optimization effect semantics are part of UIR design; this proposal does not make a new interprocedural purity analysis a prerequisite.

## 10. Resources and cleanup
Read cleanup-failure contracts from typed resource metadata, using standard-library contracts for current resources. Do not permanently encode every resource as std.files.File or assume every cleanup throws FileError.

Each reachable with introduces one scoped owner and a cleanup obligation. Track obligations in reverse acquisition order for each language-level exit: fallthrough, return, and checked failure propagation.

Publish cleanup requirements and exit context to lowering. UIR lowering decides the verified operations/edges implementing them; it must not infer the resource rules anew from names.

Preserve exactly-once cleanup, no implicit resource copying or escape, and the existing absence of borrowing/transfer syntax. Preserve primary/secondary failure composition: cleanup failure cancels an otherwise successful return; an already propagating body failure stays primary and cleanup failures remain secondary context.

Runtime defects remain outside the ordinary checked-failure model. No new guarantee of cleanup after arbitrary process or hardware termination is introduced.

## 11. Structural properties
Centralize deep-fixed eligibility, equality eligibility, and resource-containment queries over resolved nominal metadata. Keep visibility separate from structural metadata required by the compiler.

If profiling shows repeated property walks, memoize only complete immutable type/metadata results. Do not publish a definitive result for a partly inferred type. A worklist/SCC treatment can handle recursive metadata, with property-specific rules rather than a blanket assume-true-on-cycle policy.

Identity equality and Float IEEE equality retain their language semantics. Equality eligibility is not a license to assume every value is reflexively equal or to reorder observable computation.

## 12. Literals, diagnostics, and ordering
Frontend literal processing converts validated source spelling once under the correct numeric/sign context, preserving checked 64-bit Int and Float behavior. Include minimum Int, neighboring out-of-range values, separators, and nondecimal spellings in boundary coverage. The owned checker's positive-magnitude accumulation before unary handling is a specific boundary to verify, not a newly reproduced bug claim.

Store byte spans and structured diagnostic codes with related declarations/constraint causes. Format lines, scalar columns, and type explanations on demand using shared source data.

Keep the agreed module-layer depth-first diagnostic schedule. Within owned semantic phases, retain existing check order, including current reverse declaration traversal and demand-driven callee checks. New lookup indices must not silently change that order.

Do not claim the bootstrap and owned checker have identical first-error behavior. Preserve each migration path's diagnostic fixtures and record disagreements against the language specification. A later deliberate diagnostic-order change must be named separately.

## 13. Handoff to typed Universal IR
The frontend publishes syntax references plus frozen semantic facts, resolved declarations/types, inferred schemes, and cleanup/failure obligations. UIR construction consumes these directly.

No additional materialized executable Typed IR is required by this proposal. The detailed UIR operation set, generic body encoding, checked-failure lowering, and cleanup edge representation remain decisions to take together.

Release body-analysis scratch after publication and AST storage after its final consumer finishes. Retain source and diagnostic data while needed. Mandatory semantic checks and UIR verification remain in the compilation path.

## 14. Milestones and acceptance
Do not combine this into one rewrite or block the already agreed cache milestone.

S0: Record current semantic acceptance, inferred contracts, error priority, time, peak memory, body-check counts, inference link visits, fact lookups, property traversals, and specialization counts on the existing semantic corpus and selected compiler modules.

S1: Introduce binding/type/inference/fact ownership contracts and compatibility adapters using existing behavior. Keep stage contexts isolated and preserve traversal order. Integrate the indexed AST without requiring all optimizations at once.

S2: Change solver, place checking, or structural-property representations in independently measured slices. A linked scan by itself is not a demonstrated bottleneck.

S3: Introduce explicit flow and cleanup summaries in a separate correctness-focused slice. Validate every existing supported branch/handler/resource case before removing the old path.

S4: Connect the approved semantic products to UIR after agreeing the lowering contracts.

Required acceptance:
- Existing semantic corpus acceptance and normalized inferred contracts remain correct.
- Local visibility, initialization order, no-shadowing, duplicate names, module privacy, and entry boundaries are preserved.
- Fresh generic instantiations retain shared signature relationships without contamination across calls, attempts, or failures.
- Recursive and mutually recursive inference respects explicit-result and no-value rules.
- Branch joins, optional narrowing, assignments, loops, short-circuit expressions, and handler termination are tested at the supported contract boundary.
- Cleanup is exactly once and reverse-order; successful-return/cleanup-failure and body-failure/cleanup-failure combinations preserve their specified primary/secondary behavior.
- Deep fixed/equality checks handle recursive metadata and unresolved obligations correctly.
- Same AST in different flow/specialization contexts cannot retrieve another context's stale facts.
- Allocation failure, cancellation, deep types, and resource limits leave no ready incomplete product and allow a clean retry.
- Measured slices report timing, memory, action counts, and scaling against the same inputs/runtime tier. Numerical budgets are set from S0 measurements; no whole-build speedup is asserted here.

No production code, workflows, tests, or benchmarks were started for this design. The module plan is agreed separately; this semantic architecture and its acceptance criteria are now agreed.

## Sources
Eristavi repository snapshot: https://github.com/eristavi/eristavi-lang/tree/8af0ffe3350c737550c3ab0e6c3fa89f60f6f091
Source files and locked language documents identified in section 1, plus LANGUAGE_SEMANTICS.md, FUNCTION_RETURNS.md, FIXED_IMMUTABILITY.md, ERRORS.md, VALUE_EQUALITY.md, and existing frontend/semantic conformance fixtures.
The justification is Eristavi's own contracts and inspected implementation. No external compiler or build-system dependency is introduced.

