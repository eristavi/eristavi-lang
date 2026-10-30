# Typed Universal IR — architecture proposal
Date: 2026-10-29
Status: Core direction and initial U1 contracts agreed. Foundation PR #58, verifier/recovery PR #59 and scalar-cell promotion PR #60 are merged. Both final PR heads passed four-job CI; the completed implementation batch passed full bootstrap repeatability/offline qualification plus owned integration. U1a remains incomplete: operations/provenance/integration, physical accounting and larger owned-runtime performance gates remain pending. No public format is frozen.
Baseline: Eristavi PR 57 head 8af0ffe3350c737550c3ab0e6c3fa89f60f6f091; inspected RevaSM main working architecture and machine.hpp.
Scope: Universal IR contracts and frontend/backend boundaries. Preserve Eristavi source semantics and existing ABI boundaries during migration.

## Recommendation
Use one language-neutral typed UIR framework with immutable SSA values, explicit basic blocks and block parameters, independently owned type metadata, and versioned semantic extensions. Construct it directly from the approved AST plus frozen semantic facts. Private construction may use initialized local places, but U1 must promote every eligible place before publishing canonical UIR. Legalize operations through explicit profiles, then lower per function into a target-specific machine representation.

The architecture minimizes redundant representations without pretending that fewer passes always produce faster compilation or better machine code. There is no additional mandatory source-close executable Typed IR. Semantic facts and temporary frontend analysis summaries remain distinct from an executable program IR.

## 1. What the code establishes
The owned universal_model stores coarse value classes, linked instructions/operands/blocks/registers, and helper names whose signatures are reconstructed in verifier functions. Its virtual registers are mutable: copy and loop-increment operations can assign an existing result register. Definite-initialization dataflow is therefore required for those registers. Program.types retains a typed.Program rather than independent UIR metadata.

The owned backend assigns stack storage to virtual registers and builds a whole-function register/parameter root description. Most source operations become boxed runtime helper calls. The bootstrap model instead carries richer semantic types and a broader analysis/allocation path. These implementations are not interchangeable representations or equally mature backends.

The new design addresses those boundaries directly. Source inspection identifies mechanisms; it does not measure their dynamic contribution or prove a whole-build speedup.

## 2. Language-neutral core and explicit extensions
The core provides:
- typed constants and immutable SSA values;
- integer/predicate/floating operations with specified behavior;
- aggregates and tagged variants;
- blocks, conditional branches, multiway switches, calls, returns, and terminal traps;
- initialized typed local places for storage that genuinely needs them;
- declarations, signatures, imports, constants, locations, and effect contracts.

Versioned semantic extensions provide managed references, ordinary value snapshots/copies, UTF-8 Text services, growable collections, resource ownership, checked-failure context, and other operations that genuinely require those contracts. Their semantics must be specified independently of Eristavi keyword spellings.

A frontend can use only core arithmetic and control flow without adopting Eristavi's GC, List semantics, failures, or public value ABI. Universal means adaptable and semantically explicit, not automatic support for every language feature.

Use one operation registry and fixed internal schemas initially. A general plugin framework or extensible parser/dialect DSL is not required. Unknown required operations/profiles are rejected; declared legalization paths may translate supported extensions.

## 3. Independent types
Own UIR types directly; do not retain AST, semantic contexts, or the old typed.Program to decode them.

| Kind | Proposed meaning |
|---|---|
| pred | Boolean condition, distinct from integers |
| i8/i16/i32/i64 | Fixed-width bit patterns; operation chooses signed/unsigned interpretation |
| f32/f64 | Explicit floating-point semantics |
| Aggregate | Ordered fields/components with logical types |
| Variant | Explicit tag plus typed alternatives |
| Local place | Mutable typed storage initialized at creation |
| code/signature | Executable reference with a declared call contract |
| Managed/resource extension types | Explicitly selected semantic and lifetime contracts |

Eristavi Int maps to checked signed i64 operations; Float maps to strict binary64 and Bool to pred. These mappings do not restrict other frontends to Eristavi's primitive vocabulary.

Functions and operations may return zero, one, or several values. A no-value operation defines no fake void register. Source no-value functions return an empty result sequence, without adding a source Void type.

Concrete TypeIds use an immutable indexed table, separate from kind tags. Nominal ownership, field order, and source-required identity survive. Executable functions may not contain unresolved inference variables. A new generic-template type system/profile is deferred to a separate artifact design.

## 4. SSA values and block parameters
Each ValueId has one definition and one type. Definitions include function parameters, block parameters, and instruction results.

Permit references to dominating definitions across blocks. Use block parameters for joins and loop-carried values. Do not require every dominating value to be manually threaded through every intervening block.

Every branch edge supplies exactly the destination parameter count and types. All edge arguments are evaluated in the predecessor state and assigned simultaneously. Backends must resolve parallel moves, including cycles; sequential assignment is not equivalent.

Example, illustrative notation only:
  entry: branch condition, left, right
  left:  jump join(left_value)
  right: jump join(right_value)
  join(result: i64): return result

SSA identity is independent of physical registers or stack slots. Dominance verification replaces mutable-register definite-initialization analysis for SSA values; it does not eliminate memory, lifetime, or ownership checks.

### Multiway dispatch
U1 includes switch(selector, cases, default). Selectors are integer or explicit variant-tag values; case constants must be unique and type-correct. Every case and the required default is an ordinary typed edge with simultaneous block arguments. Case selection has no fallthrough. Storage/serialization use deterministic case order; source handler priority is resolved by the frontend before building the case table.

U2 maps checked-error/variant dispatch onto switches. Payload projection requires the matching variant refinement, established by the selected edge or an explicit checked operation; merely claiming a payload type is insufficient. An exhaustive variant switch may route its default to an invalid-tag trap, never to undefined behavior. The machine backend separately chooses a comparison chain, tree, or jump table from measured target costs; the UIR does not mandate a jump table.

## 5. Mutable places and value semantics
A private frontend builder may initially map a mutable local to an initialized typed place. This is temporary construction state, not the published optimization contract. Mandatory place promotion belongs to U1, including the default compilation path. Source mutability does not itself require runtime memory.

Eligibility is decided from all uses: a function-local initialized cell whose accesses are only direct reads/writes, whose address never escapes or is observed, and whose lifetime needs no memory identity. Scalar and whole-value locals qualify; an aggregate projection qualifies only after a semantics-preserving whole-value update is represented explicitly. Heap fields, aliased storage, address-observed cells, and resource owners are not promoted by pretending they are scalar locals. Managed handle bindings join this rule in U2; any required value-copy/snapshot operation remains explicit.

U1 algorithm: index uses/definitions, remove unreachable construction blocks after structural checks, compute dominance and live-in information for candidate places, insert block parameters at the pruned iterated dominance frontier, then rename using one current-value stack per place while walking the dominator tree with an explicit work stack. Fill predecessor arguments from predecessor values, delete direct place reads/writes, and simplify trivial parameters. Loop backedges are filled before publication; edge assignments stay simultaneous. Initializers remain in their original evaluation position. A missing incoming initialization is a compiler error, not an invented undefined value.

Record CFG nodes/edges, scanned uses, frontier visits, inserted parameters, edge arguments, and elapsed time. Frontier placement and live-in computation are not claimed universally linear; irreducible/dense CFGs can grow substantially. U1 must establish numerical work/memory limits from U0 fixtures before implementation acceptance. Limits produce an explicit compiler resource-limit diagnostic; there is no silent fallback to mutable virtual registers. Acceptance requires zero eligible places remaining and verified dominance for diamond joins, nested loops, and loop-carried mutable locals. Optional aggregate scalar replacement and promotion of genuine aliased storage are later optimizations.

Logical place projections and raw byte addresses are different concepts. Preserve aggregate field/index operations until their semantics can be lowered safely.

Managed ordinary values must preserve snapshot/value semantics. A List or nominal assignment must not silently become shared mutable identity. Managed copy/snapshot/update operations specify their logical behavior; implementations may use eager copying, copy-on-write, persistent sharing, or proven copy elimination only when equivalent.

Identity references preserve logical identity when copied. Identity equality is not raw pointer-bit equality. A value copy containing identity fields preserves the identities of those fields according to source semantics.

Allocation-backed operations initially carry conservative allocation/fault effects. Eliding a potentially failing copy/allocation requires an explicit approved resource-exhaustion/representation policy and proof; do not casually call every runtime copy pure.

## 6. Arithmetic without hidden flags or undefined overflow
Keep wrapping arithmetic and overflow-reporting arithmetic distinct. For add/subtract/multiply, an overflow-reporting operation returns a defined wrapped result plus a predicate, with signedness explicit. Eristavi follows it with a guard that produces the defined arithmetic trap on overflow. Native selection may combine this into arithmetic plus an overflow branch.

The wrapped result is defined even when overflow is reported; there is no poison value or implicit undefined behavior. Other frontends can use wrapping arithmetic deliberately.

Division/remainder specify signedness, truncation, zero-divisor behavior, and the signed-minimum/-1 case. A checked division/remainder operation can trap directly under a declared contract. Eristavi preserves its existing exceptional remainder rule.

Guard/trap operations are observable terminal outcomes. A guard does not create a general checked-language failure or run arbitrary handlers.

Required source compile-time diagnostics remain frontend responsibilities. UIR optimizations must preserve the IR's runtime behavior and cannot invent Eristavi-specific diagnostic rules for another frontend.

## 7. Floating-point and constants
Operations specify precision, rounding, NaN/ordered-comparison behavior, signed zero, and subnormal handling. The Eristavi profile uses binary64, nearest-ties-even, gradual underflow, and its locked NaN observability rules.

No implicit fast-math, reassociation, flush-to-zero, excess precision, or multiply-add contraction. Explicit fused operations or relaxed profiles require their own contracts. Another frontend that observes NaN payload bits must select a compatible profile rather than inherit Eristavi's permitted canonicalization.

Constants hold validated values/bit patterns. Do not parse Float source spelling in generated programs. UTF-8 constants use explicit lengths and may contain zero bytes; physical null termination is a runtime ABI detail.

Foreign-call boundaries must respect the selected floating environment; ambient host state cannot silently redefine operations.

## 8. Checked failures use explicit continuations
Use an ordinary call for a signature with no checked failure result. For fallible contracts, use a call terminator with normal and failure successors. Success results and failure context are available only on their corresponding edges, delivered through typed block parameters.

The mechanism is language-neutral: the failure payload/context has an explicit declared type. Eristavi's error sets, handlers, and propagation map onto it; no global error_pending flag, hidden mutable handler stack, setjmp/longjmp requirement, or exception ABI is intrinsic to the UIR.

Eristavi try branches to the caller's appropriate failure/cleanup path. else error uses explicit type/tag dispatch and typed handler blocks. A source call's declared failure contract must match its IR signature and handling/propagation edges.

Existing runtime error-state helpers may remain behind a migration adapter. They must not become the permanent abstract IR semantics or leak into unrelated frontends.

## 9. Resource and cleanup extension
### U2 is a scoped-owner profile
The initial extension verifies Eristavi's existing lexical with ownership. It does not implement arbitrary ownership transfer, heap-stored owners, escaping borrows, or general linear types for other frontends. Those features would need separate contracts. Resource values cannot pass through ordinary copy/aggregate/store/capture operations. Runtime resource calls declare observation versus acquisition versus consumption; observation cannot retain ownership beyond the call.

Each block has an ordered owner signature, outermost to innermost, with explicit owner block parameters. Each entry identifies the lexical owning scope and resource contract. Validate these scope identities and nesting against the function's owned scope table; a scope cannot occur twice in an active stack. The entry block starts empty for ordinary Eristavi functions. Successful acquisition introduces one owner in its designated lexical scope; a failed acquisition introduces none. Observing a resource requires its currently active owner. Closing consumes the innermost owner before either close continuation; a failed close never restores ownership. A return or propagated checked failure requires an empty owner state, after its required cleanup. A scope-local normal continuation must have the exact surviving outer prefix.

### Ownership verification algorithm and budget
After structural/type/SSA checks, validate each block independently against its declared owner signature. Build a dense, generation-marked ValueId-to-active-owner index for that block. Scan instructions once, updating the ordered active stack and rejecting inactive use, duplicate owner, copy, escape, or non-LIFO consumption. At each successor, match the resulting owner stack position-by-position against the target signature and actual owner arguments, with exact lexical scope and contract correspondence. A branch may forward the same active owners to mutually exclusive successors; each individual edge must carry every surviving owner exactly once and no consumed owner. Edge-specific acquisition results exist only on the acquisition-success edge.

This is an inductive CFG check: a valid entry state plus every valid block/edge establishes validity on every finite execution path, including loop iterations. Backedges must match the same explicit signature. It needs no whole-program path enumeration or repeatedly merged ownership bitsets. Nontermination is not a resource-scope exit. All blocks receive local structural/owner checks, including dead blocks; entry reachability and dominance are checked separately.

Let N count instructions, ordinary operands, and scope-table records, V SSA values, and S the total owner-signature entries plus owner-edge arguments actually encoded. The ownership check has O(N+V+S) time with dense indices and O(V+Q+Rmax) reusable scratch, where Q is the number of owner scopes, in addition to the stored IR. This is linear in the encoded representation, not necessarily in source size: S can be O(E*Rmax). Count S, stack depth, scans, and scratch bytes in U0/U2 fixtures. Implement no per-block full-register bitset and no repeated whole-function ownership fixed point. Numerical acceptance/resource limits must be fixed from U0 fixtures before U2 implementation begins; they remain an open design gate, not a promise to choose a budget after seeing a candidate pass. These algorithmic bounds are not runtime measurements.

### Cleanup construction algorithm and budget
Consume the semantic cleanup obligations to make a finite exit plan: active owner stack, normal destination/arguments, checked-failure destination/arguments, and the respective scope prefixes that survive. Pending return values remain typed SSA arguments. No scan of arbitrary UIR is used to rediscover source scope nesting.

For each exit plan, build a reverse-order normal cleanup chain and a failure cleanup suffix chain. A successful close continues with the same pending outcome. The first failed close on a normal path discards the pending successful return and starts a primary FailureContext. A failed close while a primary context exists appends secondary context in order. Both close edges have already consumed that owner. Continue cleaning the remaining required scopes even when a close reports a checked failure. At the chosen stop prefix, route to the appropriate normal or checked-failure continuation. Different handler boundaries are explicit distinct plans, not guessed from error names.

Memoize the failure suffix within an exit plan by remaining owner-stack suffix and typed failure continuation, so each required suffix is emitted once. For a plan with one normal/failure routing pair and R relevant owners, there are at most R normal closes plus R failure-mode closes, rather than one duplicated path for every combination of close failures. Construct iteratively, without recursion proportional to source nesting. Additional distinct routing/signature plans are charged explicitly.

U2 deliberately does not share cleanup chains across distinct source exits. The previous promise to share whenever state matches is withdrawn. Exact cross-exit sharing is an optional later, separately measured optimization; no ownership-state equivalence or SSA-value equality algorithm is needed for U2. Within-plan suffix reuse is fully specified above.

Let X be the sum of relevant unwind depths over the distinct exit/routing plans and A the emitted argument/payload entries. Construction and output are O(X+A), with at most 2X close operations for the simple routing pairs above. X can be exit-count times nesting depth; record it rather than calling the output linear in source size. Failure-context append must use an ordered tail/builder representation with amortized O(1) append, not repeatedly copy all previous secondary failures; its allocation failure follows the terminal-runtime-defect policy. Repeated close failures must not cause exponential code growth or quadratic context copying. Before U2 implementation begins, fix numerical limits for X, A, owner depth, emitted code size, memory, and runtime cleanup overhead from U0 stress fixtures. If cross-exit duplication exceeds the agreed size budget, stop U2 acceptance and review sharing, rather than silently publishing an unbounded optimization promise.

### Terminal traps and external resources — agreed standalone policy
A runtime-defect trap terminates the standalone process without running user/resource cleanup. This policy was explicitly agreed on 2026-10-29. It applies to arithmetic/bounds faults, runtime-internal defects, and catastrophic allocation failure, including failure during cleanup. It cannot return to a host caller and continue using that process as though the resource protocol completed. A recoverable embedding/isolation/unwinding mode is a separate runtime design and is not supplied by this UIR proposal.

This is a narrow fail-stop guarantee, not a blanket claim that skipped cleanup is safe. The OS normally reclaims process-owned file descriptors and address space; user buffers need not flush, writes need not become durable, temporary files may remain, and application protocols may be incomplete. Lock release is not promised: persistent/distributed locks and shared-state invariants may survive process death or need explicit owner-death recovery. No lock resource implementation is claimed to exist here. A future lock API must define its crash behavior before admission.

This policy is compatible with RESOURCE_CLEANUP.md's explicit distinction between ordinary language-level exits and runtime defects. That document alone did not establish the stronger no-unwind/process-termination policy; the explicit joint decision above now records it for the standalone execution profile. Ordinary returns and checked failures retain exactly-once reverse cleanup and stable primary/secondary failure composition. Runtime/reporting implementation and qualification remain pending.

## 10. Effects and ordering
The operation registry defines, rather than guesses from names:
- memory reads/writes and relevant regions where known;
- allocation and possible collection;
- I/O or external effects;
- traps, checked failures, divergence;
- resource observation/consumption and lifetime effects.

Effects are ordered by instruction order and CFG execution. A pass may reorder only with the necessary dependency, alias, trap, and lifetime proof. Pure arithmetic needs no universal world-token operand.

Unknown foreign calls are conservative. Empty fails is not purity, readonly is not necessarily nontrapping, and pure-but-diverging calls cannot automatically be erased.

Memory SSA/effect-token analyses can be added if measured optimization needs justify them. They are not a mandatory new operand on every initial instruction.

Optimization metadata cannot change semantics. Initial core has no assumption or unreachable construct that permits arbitrary behavior for an otherwise defined program; an explicit unreachable-execution outcome is a terminal trap. Unsafe/raw foreign-memory semantics require a separately declared profile, not silent weakening of the safe core.

## 11. Reserved: runtime memory profiles
An abstract addr/provenance system, foreign-pointer model, privileged physical addresses, and uninitialized-memory profiles are outside this core proposal. Do not reserve concrete opcodes/layouts or shape U0-U4 around hypothetical frontends. Runtime-private memory lowering already exists in Eristavi and must keep its current verified capability boundary through a compatibility adapter; redesigning that boundary is a separate runtime/machine-lowering document, not permission to erase its checks.

The core still needs initialized typed places, explicit effects, and target layout inputs wherever an actual operation consumes them. These requirements do not imply a universal address-capability architecture.

## 12. Managed references and GC boundary
Managed roots remain distinct from arbitrary integers/addresses. Operations that can collect are identifiable. Backend root maps derive from actual liveness, including block-edge arguments, calls, and failure/cleanup paths.

Preserve the current owned runtime and public ABI through adapters initially. A collector rewrite, moving collection, or ABI replacement is not a prerequisite for the new UIR.

Moving collection, pinning, relocation values, and statepoint protocols are reserved for a separate collector design. They add no required operations, profiles, or acceptance work to U0-U4. Keep the existing collector contract explicit.

Verifier/type metadata must describe references contained in aggregates and failure contexts. No GC-required value may disappear because spill-slot reuse or call lowering ignored a safe point.

## 13. Compact representation and ownership
Use per-function indexed storage for blocks, instructions, values, operands, results, and edges, plus module-owned immutable types/constants/signatures. Use typed 32-bit IDs with checked exhaustion. No linked object per operand or repeated string signatures on hot paths.

Keep large constants, variable-length operands, type data, and debug locations in side tables. Use operation-specific payloads/accessors. The exact instruction byte layout is chosen from required fields and measurements; the lexer's 24-byte token rule does not apply to instructions.

Use stable slot IDs through a mutation batch, with explicit live/dead state; do not renumber every value after every rewrite. Compact once at defined boundaries if useful. Decode sparse external/legacy IDs through a checked dense remapping instead of allocating memory proportional to the largest external ID.

Builders can hold incomplete blocks privately. Published functions must be complete. Release per-function builder/analysis scratch when its consumer finishes.

### Source provenance through transformations
Use a module-owned immutable location table. LocId resolves to a source identity/revision digest, half-open UTF-8 byte span, diagnostic anchor, and optional parent origin. Session SourceIds are remapped on artifact load; a stale host path or session-local integer is not source identity. Artifact diagnostics must remain useful without source text: retain logical module/file identity and line/column mapping or an equivalent compact source map. Reopen source only after digest validation, never attach current edited bytes to an old span.

Every source-derived operation that can trap, fail, perform cleanup, or otherwise produce a runtime report has a nonzero LocId. Synthetic operations name their transformation reason and a parent source origin. Operation replacement preserves the original diagnostic anchor. Inlining adds callee origin plus call-site chain. A shared cleanup suffix retains its resource/cleanup origin and the relevant exit origin; it must not attribute an arbitrary return to another exit.

Merged pure values may keep a deterministic ordered origin set in side metadata. Do not merge distinct observable trap/failure sites merely because their value computations match; either prove diagnostic behavior preserved or retain distinct checks. A folded successful pure operation needs no surviving runtime location; a preserved fault keeps the original fault site and evaluation order. No optimization invents a new source-language compile-time error from a runtime fault.

Pass APIs must carry/remap provenance, and verification rejects missing/invalid required locations and cyclic origin chains. Location indices are stored in deterministic table order, not pointer/hash iteration order. Machines preserve required LocIds through selection until final trap/runtime-report and optional debug-line mapping is emitted. Full symbolic debugger support is a separate deliverable; essential error locations are not optional debug stripping. Test location stability under folding, block merging, promotion, inlining, cleanup, and artifact round trips.

## 14. Operation registry
One authoritative registry describes each operation's operand/result rules, typed attributes, effects, permitted profile, and verifier requirements. Calls use FunctionIds and signature records. Runtime imports declare versioned contracts and capabilities.

Initial implementation can use ordinary compiler modules/static tables; generated tables are an optional build technique. Backends and verifiers must not maintain unrelated copies of helper-name string tests.

Every new operation includes semantics, malformed-input rejection cases, reference behavior, and a lowering path or a clear unsupported-target diagnostic. Unknown operations are not silently treated as pure or omitted.

## 15. Verification and transformations
Mandatory gates:
1. After initial complete UIR construction.
2. On serialized implementation ingress; a future serialized UIR template profile must define its own verification gate in the separate artifact design. Existing embedded-source templates retain their frontend checks.
3. After an optimization batch publishes a changed function/program.
4. After legalization, before machine lowering consumes the resulting legal profile.

A verifier result is tied to the exact IR revision and contracts. It cannot authorize later mutation. Unchanged verified products may retain a session-local stamp; new serialized bytes are not trusted just because a manifest hash matches.

Check:
- owned/scoped IDs, ranges, unique definitions, type/signature consistency;
- one terminator per block, existing targets, edge arity/types;
- instruction use order and dominance on executable reachable paths;
- all blocks' structural/type validity, including unreachable blocks;
- referenced values exist and have the claimed type even in unreachable blocks;
- call normal/failure edges, resource/lifetime/profile obligations, and initialized-place rules;
- target-legal operation sets and relevant ABI/runtime contracts at the lower boundary.

Passes that introduce reachability must re-establish dominance/availability; unreachable code is not a loophole for malformed operations. Required availability analysis follows the reachable CFG rather than imposing a meaningless execution path on dead components.

Use direct def/use tables, iterative graph traversal, and per-function scratch. Ordinary SSA values do not require whole-register initialization bitsets on every block; explicit memory/resource analyses remain separate. Do not claim dominance or resource verification has no cost or is universally linear.

A verifier stamp proves only the checked invariants, not equivalence to Eristavi source or correctness of an optimization. Lowering and transformation semantics need independent validation.

Each pass declares preserved/invalidated analyses. Revision-check dominance, uses, liveness, alias, ownership, and root maps. Unknown edits invalidate conservatively. Verification and analysis do not mutate semantic instruction fields to store visitation marks.

## 16. Progressive lowering with one UIR framework
Use explicit legality profiles:
- semantic UIR: typed source-neutral operations retaining value/copy/collection/resource intent;
- executable legal UIR: required extensions reduced to supported operations and declared runtime calls;
- target machine representation: instructions, register classes, call clobbers, stack and root locations, and encoding requirements.

These profiles share IR infrastructure and operation contracts; they do not justify constructing several complete source-close program trees. Lower per function where practical and release previous temporary representations.

Types and operations requiring runtime behavior stay explicit until their lowering decision is made. Core scalar arithmetic can lower directly to native operations. A missing capability produces a diagnostic, not silent routing through C or another compiler.

A small target-specific machine representation is justified by instruction selection, register allocation, ABI, and encoding. Its detailed design is the next tool boundary, not frozen here.

## 17. ABI and RevaSM
The UIR does not prescribe the public 32-byte Eristavi value ABI for other languages. Keep that ABI at existing boundaries during migration. Internal unboxed scalars and target-specific representations are allowed behind explicit adapters and independently agreed ABI contracts.

RevaSM remains a peer machine target alongside x86-64, ARM64, and future RISC-V. The UIR is not RevaSM and native targets do not have to pass through RevaSM.

RevaSM currently requires explicit block parameters for nonlocal values in its prototype. The UIR permits dominating cross-block uses; its RevaSM backend must thread required incoming values explicitly. This conversion does not change the other backends' IR contracts.

U4 must budget this adapter as a separate subtask: compute live-in requirements, add incoming parameters, supply/remap predecessor arguments, handle loops and parallel edges, and verify the converted function. Compute required propagation from value uses with a visited (block,value) worklist rather than rescanning all values on every block. Charge predecessor visits and every inserted parameter/edge argument explicitly; high fan-in/live-through sets can make representation growth substantial. Track analysis time, peak scratch, added parameters/arguments, and emitted size. Do not label the cost negligible or assign a calendar estimate before a prototype measurement. This remains separate from RevaSM's larger Float/runtime/resource support gaps.

Align only where semantics match: arithmetic policy, predicates, explicit effects, and block edges. RevaSM allocation-instance address identity is not automatically Eristavi source identity, and a terminal RevaSM trap is not a catchable Eristavi failure. Its current prototype does not establish complete Float, GC, or Eristavi resource support.

## 18. Artifact/cache linkage; generic profile reserved
Use concrete executable UIR in the initial framework. A new generic-template profile is reserved for a separate artifact proposal; its types, operations, serialization, and specialization algorithm are not defined here and do not block U1-U3 or concrete UIR migration in U4.

Generic reuse is nevertheless an existing Eristavi requirement. Preserve the current embedded-source/JSON template adapters and their fresh semantic instantiation until the separate replacement is designed and validated. Do not claim source-independent generic compatibility can simply be deleted. No mutable inference state may leak into immutable contracts or shared callers.

The module proposal's original item 8 (new implementation/generic artifacts) depends on these UIR contracts. Concrete implementation artifact redesign is gated on stable operation/type/verification contracts here; replacement generic artifacts are additionally gated on the separate generic artifact decision. Neither blocks module-cache correctness M1a or immutable-input reuse M1b. Both documents must say this explicitly.

For every action that produces or consumes UIR, the canonical cache key includes the UIR encoding/schema version, exact semantic and legality profile versions, sorted required operation/extension contract versions, verification-policy version, and applicable runtime-import/ABI contract versions. Include these in the committed manifest too. Compiler build identity remains independently required; schema/profile versions never replace it. Consumed dependency bodies/templates and relevant target layout inputs remain key inputs as specified in the module proposal.

Changing any one relevant UIR contract version with source/compiler/options otherwise fixed must miss the affected action; an incompatible explicit precompiled input must fail with an unsupported-contract diagnostic. A compatible hash/manifest is not a verification stamp. Mandatory IR verification still occurs on decoded implementation material. Unrelated check-only stages need not miss solely for a backend profile they never consume.

Text dumps are debugging interfaces initially. Production binary encoding and extension naming are separate decisions; implementation source remains .eri. UIR schema evolution is independent of RevaSM's eventual machine-architecture stability contract.

## 19. Optimization policy
Begin with bounded-cost transformations: safe constant folding, simple branch simplification, dead-block removal, copy propagation, and trivial block-parameter simplification. Preserve traps, checked failures, evaluation order, strict Float, effects, resources, and value semantics.

Eligible local-place promotion is mandatory U1 canonicalization, including the default pipeline. Aggregate scalar replacement, more advanced copy elimination, inlining, common-subexpression elimination, loop transforms, and check elimination are separately measured additions. They need appropriate alias/effect/lifetime analysis and pass budgets, not blanket activation under the label optimized.

Use canonical target-independent constant evaluation, not host arithmetic behavior that changes overflow, remainder, rounding, or NaN rules.

The pass pipeline can offer different compilation/optimization budgets later. No new CLI names or promised optimization levels are selected here.

## 20. Implementation milestones and acceptance
This is a full architectural map, not a single rewrite milestone.

U0: Baseline current construction, verification, optimization, boxing/runtime-call counts, peak memory, and total pipeline time on fixed workloads. Add mutation-heavy diamonds/loops, deeply nested resources/many exits, repeated cleanup failures, switch-heavy handlers, and source-location fixtures. Keep compile-time and generated-program runtime measurements separate. Fix numerical work, expansion, memory, and timing gates before the corresponding U1/U2 implementation begins; this document specifies algorithmic envelopes but invents no measured thresholds. Initial scalar/control-flow evidence is recorded in Eristavi-UIR-U0-Baseline-2026-10-29.md: 60 pipeline samples across 12 fixtures and 30 corrected paired native-verifier/runtime samples, with explicit limitations and remaining coverage. This is neither the entire U0 program nor a new-UIR speedup. The standalone terminal-trap policy is agreed, while budget gates remain open.

Subsequent U1a budget decision: U1 contract section 15 and its machine-readable profile set explicit owned-capacity, allocation-traffic, count, work, cancellation, and qualification-watchdog limits before candidate construction. Budget selection is closed; candidate compliance and U2 budgets remain pending. Comparative timing is informational for initial U1a. PR #58 implements the first ledger and construction adapter under this policy, with the accounting limits recorded below.

U1: Independent types, dense builders, true SSA, block parameters, temporary initialized-place construction plus mandatory eligible-place promotion, switch, scalar operations, ordinary calls, locations, and verifier. Eristavi checked i64 arithmetic is included from the first scalar slice. Gate on verified loop-carried mutable locals and zero eligible places remaining. Keep old paths as a comparison oracle.

Agreed U1 delivery sequence: U1a first covers pred/i64/strict f64 and the control-flow/call/guard/location/verifier/promotion machinery; U1b completes other integer widths and immutable aggregates. Unsupported profile operations are explicit. This staging does not change source semantics or add a new executable Typed IR.

U2: Fallible continuations, managed value operations, scoped-owner verification and the proposed bounded cleanup chains, managed-local promotion, and existing runtime/ABI adapters. Gate on detailed operation/algorithm review, owner/cleanup stress budgets, and normal/failure location fidelity. Standalone terminal traps follow the agreed policy. Existing semantics remain required for supported programs; do not replace the full compiler with a scalar-only candidate.

U3: Direct approved frontend-to-UIR construction and integration with one native target. Remove the old source-close Typed IR only after representative conformance and output/behavior comparisons succeed.

U4: Legalization, machine contracts, concrete implementation-artifact migration/cache versioning, and backend parity in separately reviewed slices. Include measured RevaSM live-in threading/edge-argument conversion as an explicit subtask. Retain existing generic-template adapters; replacing them waits for a separate artifact/profile decision. Moving GC and a new addr/provenance architecture are excluded.

Acceptance:
- Scalar interpreter/reference behavior agrees with native outputs for checked arithmetic, signed division/remainder boundaries, strict Float, and terminal traps.
- Phi-like joins, loop-carried values, edge-specific call results, parallel-copy cycles, and dominance violations are covered.
- Mandatory promotion eliminates every eligible mutable local; noneligible places retain explicit storage semantics.
- Switch duplicate cases, malformed edge arguments, invalid payload refinements, exhaustive defaults, and handler selection are covered.
- Malformed instructions in unreachable blocks are rejected.
- Value copies remain independent while identity fields preserve identity.
- Checked failures never become terminal traps accidentally; cleanup preserves pending returns and primary/secondary failures exactly.
- Resource misuse, use-after-consumption, dropped cleanup paths, wrong failure edges, missing live roots, and stale analysis revisions are rejected.
- Loop/backedge owner signatures, failure during close, many exits at deep nesting, suffix reuse, secondary-failure order, and nonquadratic append are covered; count actual owner-edge and cleanup expansion.
- Fault fixtures verify the agreed termination policy without promising file flush, persistence, or lock release; checked-failure fixtures still require full cleanup.
- Existing runtime/ABI compatibility, source-independent modules, generic relationships, and diagnostics survive adapter migration.
- Location provenance survives promotion, optimization, cleanup, machine lowering, and artifact round trips without attributing errors to stale source bytes.
- Independently vary schema, semantic profile, extension, verifier, and runtime contract versions: affected UIR actions miss, incompatible explicit dependencies diagnose, and unchanged eligible actions still hit. Retain the separate compiler A/B invalidation regression.
- Verify an IR again after mutation; a stale verified flag or cached analysis cannot hide a defect.
- Include a second minimal frontend or manually constructed core-only program that uses no Eristavi Text/List/GC/failure assumptions, to test actual core independence.
- Use targeted differential cases, malformed-IR mutation tests, arithmetic boundary generation, and metamorphic tests for transformations.
- Benchmark construction, verification, optimizations, memory, instruction/edge counts, runtime helper calls, root-map size, and generated execution separately. Set numeric gates from U0 evidence, not guessed whole-build speedups.
- Run expensive full compiler qualification only after the integration batch is ready.

## U1a foundation implementation status

Foundation PR #58 remains merged as 6fb8b7bcd49418f398810ef9166acc888a35c4f5. [PR #59](https://github.com/eristavi/eristavi-lang/pull/59) merged as 8a2af1c95c0878a65aebbabb464ad1bf6c66db5e, including the C-bootstrap recovery fix. [PR #60](https://github.com/eristavi/eristavi-lang/pull/60) merged as cd421d859e3372796e59ddf236944efc1b6aaddb. Main's implementation tree equals tested tree c6a554e04c12d26c93650956709c5d57f1812ddf (promotion head 22b36c1de42a6bb1b6d54d03a9c69b7c49062082). Scalar-cell promotion, independent construction/canonical checks and transactional cleanup are implemented; production frontend/native integration remains separate. The full handover is [HANDOVER.md on GitHub](https://github.com/eristavi/eristavi-lang/blob/63297369fb7c41e9f13915f6102490f41ee9626a/HANDOVER.md), published in open documentation PR #61.

On 2026-10-30 the ten-test U1 focused batch passed, including both native runtime profiles and the 91-graph dominance oracle. Promotion independently compares 18 before/after IR pairs over 88 inputs, including complete guard/fault/location traces. Final GCC and Clang 18 -O2 differential/transactional checks pass, including eight negative cases and late-output failure/cancellation. Diamond, bounded-loop and sequential-diamond fixtures at N=8/32/128 meet their exact inserted-parameter/argument counts with eight additional verifications and unchanged modeled 8 MiB/64 MiB limits. The largest sequential case records 8,206,560 peak modeled bytes, 19,524,768 successful-allocation traffic bytes and 3,367,442 promotion-work units. These direct-IR fixtures are not the original source U0 workloads or a speedup benchmark. Per-case/source evidence lives in the repository's UIR_U1A_PROMOTION_EVIDENCE.json; original baseline measurements/archive are untouched. Both PR heads passed all four CI configurations. [Completed-batch qualification 41018345033](https://github.com/eristavi/eristavi-lang/actions/runs/41018345033) passed three bootstrap repeatability gates (C/D completed, offline audit successful, unchanged sources) and owned integration (repeatable=false, no C/D self-build, successful offline audit, unchanged sources). The separate full owned-self-build profile was intentionally skipped. Post-merge main CI was automatically triggered; this is separate from the completed pre-merge checks.

Mandatory scalar-cell promotion is implemented for the existing pred/i64/f64 construction profile; full U1a is not complete. Next are remaining scalar operations, calls/switches and strict Float execution, followed by source maps/origin chains, effects/import contracts, publication/revision capabilities and frontend/native integration. Scratch lifetime/claim-array reductions and phase-disjoint dominator storage reuse allow the selected direct-IR fixtures to pass modeled gates. Complete physical heap/GC accounting, packed native storage/physical ID layout, matched wider stress and owned-runtime performance qualification remain pending. The earlier combined owned graph/deep-chain run timed out at 120 seconds; that result remains unqualified. No limit was enlarged. One completed-batch full qualification was selected for the user-authorized merges. No separate 900-second full owned-self-build attempt was started.

U0 baseline measurements remain separate and are not evidence of a new-UIR speedup. Detailed runtime ABI, machine representation, allocator, encoder, and linker decisions remain their own tool reviews.

## Sources
Eristavi snapshot: https://github.com/eristavi/eristavi-lang/tree/8af0ffe3350c737550c3ab0e6c3fa89f60f6f091
Inspected: UNIVERSAL_IR.md, UNIVERSAL_VERIFICATION.md, PRIVATE_MEMORY_LOWERING.md, FLOAT.md, INTEGER_REMAINDER.md, RESOURCE_CLEANUP.md, OWNED_RESOURCE_RUNTIME.md; src/compiler/universal_model.eri, universal_lower.eri, universal_verify.eri, universal_optimize.eri, ir_x86.eri; compiler/erist/universal_ir.py, universal_passes.py, universal_analysis.py, universal_checked.py, universal_resources.py.
RevaSM working architecture: https://github.com/eristavi/RevaSM/blob/main/docs/architecture/working-architecture.md
RevaSM prototype interface: https://github.com/eristavi/RevaSM/blob/main/include/revasm/machine.hpp
This recommendation is grounded in the project's contracts and inspected code. Performance advantages remain hypotheses until measured.

