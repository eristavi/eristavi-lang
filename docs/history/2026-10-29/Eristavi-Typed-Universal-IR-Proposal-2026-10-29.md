# Typed Universal IR — architecture proposal
Date: 2026-10-29
Status: Complete architectural recommendation for review. Not agreed, implemented, benchmarked, or frozen as a public format.
Baseline: Eristavi PR 57 head 8af0ffe3350c737550c3ab0e6c3fa89f60f6f091; inspected RevaSM main working architecture and machine.hpp.
Scope: Universal IR contracts and frontend/backend boundaries. Preserve Eristavi source semantics and existing ABI boundaries during migration.

## Recommendation
Use one language-neutral typed UIR framework with immutable SSA values, explicit basic blocks and block parameters, explicit mutable places, independently owned type metadata, and versioned semantic extensions. Construct it directly from the approved AST plus frozen semantic facts. Legalize operations through explicit profiles, then lower per function into a target-specific machine representation.

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
- blocks, branches, calls, returns, and terminal traps;
- typed local places and a restricted address/memory profile where required;
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
| addr | Authorized memory access, distinct from integers and code references |
| code/signature | Executable reference with a declared call contract |
| Managed/resource extension types | Explicitly selected semantic and lifetime contracts |

Eristavi Int maps to checked signed i64 operations; Float maps to strict binary64 and Bool to pred. These mappings do not restrict other frontends to Eristavi's primitive vocabulary.

Functions and operations may return zero, one, or several values. A no-value operation defines no fake void register. Source no-value functions return an empty result sequence, without adding a source Void type.

Concrete TypeIds use an immutable indexed table, separate from kind tags. Nominal ownership, field order, and source-required identity survive. Generic-template type expressions may refer to scoped bound parameters; executable functions may not contain unresolved inference variables.

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

## 5. Mutable places and value semantics
A source mutable local initially maps to an initialized typed place. Reads produce SSA values; writes are explicit operations. Source immutables and suitable temporaries can map directly to SSA. Promote eligible local places into SSA later, without forcing address-taking or a whole-function SSA-construction algorithm into the first frontend slice.

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
Resources use explicit owner capabilities and operation contracts distinguishing observation/use from consumption. Ownership follows control-flow edges; forwarding an owner to mutually exclusive successors is permitted, while duplicating ownership on one executing path is invalid.

The resource verifier checks acquisition, active uses, transfers, consumption, and every ordinary language-level exit. A fallible close consumes ownership on both success and cleanup-failure paths. Traps are terminal runtime defects, outside the ordinary checked cleanup guarantee.

The frontend consumes semantic cleanup obligations and builds explicit cleanup paths. Normal and checked-failure exits run reverse-order cleanup exactly once. Pending returns remain SSA values carried through cleanup. A cleanup failure cancels success. If a primary failure already exists, it remains primary; later failures append secondary context in cleanup order.

No new source borrowing/transfer syntax is introduced. These are internal contracts sufficient for existing with/resource operations, not a general borrow checker for Eristavi programs.

Share cleanup blocks when pending values, ownership state, active resources, and failure context match. Avoid both blindly duplicating cleanup for every exit and forcing unrelated exits through an opaque global dispatcher.

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

## 11. Address, lifetime, and provenance profile
An addr carries authority/provenance conceptually. Derivation cannot amplify rights or mix unrelated allocation bounds. Integers, addresses, code references, managed identity, and privileged physical addresses are distinct categories.

A verifier establishes structural/static obligations; dynamic bounds, permissions, initialization, and liveness checks remain where proof is unavailable. Invalid accesses in the checked profile trap. This does not impose a fat native pointer or dynamic table lookup on every proven-safe access.

Typed place creation requires an initializer. An uninitialized-memory extension, if needed by another frontend/runtime, has its own initialization rules and checks; it does not fabricate arbitrary undefined SSA values.

Internal allocator/runtime operations require the explicit build capability agreed earlier. Raw integer-to-address casts, foreign pointers, address equality, and unchecked memory are not smuggled into ordinary Eristavi source. Additional frontend profiles must state their semantics before acceptance.

Native endianness, address width, layout, and alignment are supplied by an explicit target/data-layout context when operations require them. A target-neutral instruction set is not a promise that every artifact involving sizeof or a native layout can be reused unchanged on every target.

## 12. Managed references and GC boundary
Managed roots remain distinct from arbitrary integers/addresses. Operations that can collect are identifiable. Backend root maps derive from actual liveness, including block-edge arguments, calls, and failure/cleanup paths.

Preserve the current owned runtime and public ABI through adapters initially. A collector rewrite, moving collection, or ABI replacement is not a prerequisite for the new UIR.

If a future moving collector is selected, raw addresses derived from managed objects cannot survive collection without explicit pinning/relocation support. Keep that boundary explicit now, without implementing moving GC.

Verifier/type metadata must describe references contained in aggregates and failure contexts. No GC-required value may disappear because spill-slot reuse or call lowering ignored a safe point.

## 13. Compact representation and ownership
Use per-function indexed storage for blocks, instructions, values, operands, results, and edges, plus module-owned immutable types/constants/signatures. Use typed 32-bit IDs with checked exhaustion. No linked object per operand or repeated string signatures on hot paths.

Keep large constants, variable-length operands, type data, and debug locations in side tables. Use operation-specific payloads/accessors. The exact instruction byte layout is chosen from required fields and measurements; the lexer's 24-byte token rule does not apply to instructions.

Use stable slot IDs through a mutation batch, with explicit live/dead state; do not renumber every value after every rewrite. Compact once at defined boundaries if useful. Decode sparse external/legacy IDs through a checked dense remapping instead of allocating memory proportional to the largest external ID.

Builders can hold incomplete blocks privately. Published functions must be complete. Release per-function builder/analysis scratch when its consumer finishes. Own source locations by SourceId/span or a compact LocId, without retaining frontend semantic graphs.

## 14. Operation registry
One authoritative registry describes each operation's operand/result rules, typed attributes, effects, permitted profile, and verifier requirements. Calls use FunctionIds and signature records. Runtime imports declare versioned contracts and capabilities.

Initial implementation can use ordinary compiler modules/static tables; generated tables are an optional build technique. Backends and verifiers must not maintain unrelated copies of helper-name string tests.

Every new operation includes semantics, malformed-input rejection cases, reference behavior, and a lowering path or a clear unsupported-target diagnostic. Unknown operations are not silently treated as pure or omitted.

## 15. Verification and transformations
Mandatory gates:
1. After initial complete UIR construction.
2. On serialized implementation/template ingress.
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

Align only where semantics match: arithmetic policy, pred/address separation, explicit effects, and block edges. RevaSM allocation-instance address identity is not automatically Eristavi source identity, and a terminal RevaSM trap is not a catchable Eristavi failure. Its current prototype does not establish complete Float, GC, or Eristavi resource support.

## 18. Generic templates and artifacts
Use the same framework for a declared generic-template profile with bound type parameters and constrained template operations. An executable profile requires completed specialization and concrete supported operations.

Template validation checks its parameter/operation constraints; instantiation rechecks substitutions and emits executable UIR. No unresolved mutable inference state is serialized, and no backend performs source type inference.

Keep existing source-template/JSON artifacts as compatibility adapters until the new profile is implemented. Format version, UIR profile, operation requirements, compiler/runtime compatibility, and dependency contract/body fingerprints are explicit.

Text dumps are debugging interfaces initially. Production binary format and extension naming are separate decisions; all implementation source remains .eri. UIR schema evolution is independent of RevaSM's eventual machine-architecture stability contract.

## 19. Optimization policy
Begin with bounded-cost transformations: safe constant folding, simple branch simplification, dead-block removal, copy propagation, and trivial block-parameter simplification. Preserve traps, checked failures, evaluation order, strict Float, effects, resources, and value semantics.

Scalar-place promotion, aggregate scalar replacement, copy elimination, inlining, common-subexpression elimination, loop transforms, and check elimination are separately measured additions. They need appropriate alias/effect/lifetime analysis and pass budgets, not blanket activation under the label optimized.

Use canonical target-independent constant evaluation, not host arithmetic behavior that changes overflow, remainder, rounding, or NaN rules.

The pass pipeline can offer different compilation/optimization budgets later. No new CLI names or promised optimization levels are selected here.

## 20. Implementation milestones and acceptance
This is a full architectural map, not a single rewrite milestone.

U0: Baseline current construction, verification, optimization, boxing/runtime-call counts, peak memory, and total pipeline time on fixed workloads. Keep compile-time and generated-program runtime measurements separate.

U1: Independent types, dense builders, true SSA, block parameters, initialized places, scalar operations, ordinary calls, and verifier. Eristavi checked i64 arithmetic is included from the first scalar slice. Keep old paths as a comparison oracle.

U2: Fallible continuations, managed value operations, resource cleanup, and existing runtime/ABI adapters. Existing semantics remain required for supported programs; do not replace the full compiler with a scalar-only candidate.

U3: Direct approved frontend-to-UIR construction and integration with one native target. Remove the old source-close Typed IR only after representative conformance and output/behavior comparisons succeed.

U4: Legalization, machine contracts, artifact/template migration, and backend parity in separately reviewed slices.

Acceptance:
- Scalar interpreter/reference behavior agrees with native outputs for checked arithmetic, signed division/remainder boundaries, strict Float, and terminal traps.
- Phi-like joins, loop-carried values, edge-specific call results, parallel-copy cycles, and dominance violations are covered.
- Malformed instructions in unreachable blocks are rejected.
- Value copies remain independent while identity fields preserve identity.
- Checked failures never become terminal traps accidentally; cleanup preserves pending returns and primary/secondary failures exactly.
- Resource misuse, use-after-consumption, dropped cleanup paths, wrong failure edges, missing live roots, and stale analysis revisions are rejected.
- Existing runtime/ABI compatibility, source-independent modules, generic relationships, and diagnostics survive adapter migration.
- Verify an IR again after mutation; a stale verified flag or cached analysis cannot hide a defect.
- Include a second minimal frontend or manually constructed core-only program that uses no Eristavi Text/List/GC/failure assumptions, to test actual core independence.
- Use targeted differential cases, malformed-IR mutation tests, arithmetic boundary generation, and metamorphic tests for transformations.
- Benchmark construction, verification, optimizations, memory, instruction/edge counts, runtime helper calls, root-map size, and generated execution separately. Set numeric gates from U0 evidence, not guessed whole-build speedups.
- Run expensive full compiler qualification only after the integration batch is ready.

No production code, CI workflows, tests, or benchmarks were started for this proposal. Detailed runtime ABI, machine representation, allocator, encoder, and linker decisions remain their own tool reviews.

## Sources
Eristavi snapshot: https://github.com/eristavi/eristavi-lang/tree/8af0ffe3350c737550c3ab0e6c3fa89f60f6f091
Inspected: UNIVERSAL_IR.md, UNIVERSAL_VERIFICATION.md, PRIVATE_MEMORY_LOWERING.md, FLOAT.md, INTEGER_REMAINDER.md; src/compiler/universal_model.eri, universal_lower.eri, universal_verify.eri, universal_optimize.eri, ir_x86.eri; compiler/erist/universal_ir.py, universal_passes.py, universal_analysis.py, universal_checked.py, universal_resources.py.
RevaSM working architecture: https://github.com/eristavi/RevaSM/blob/main/docs/architecture/working-architecture.md
RevaSM prototype interface: https://github.com/eristavi/RevaSM/blob/main/include/revasm/machine.hpp
This recommendation is grounded in the project's contracts and inspected code. Performance advantages remain hypotheses until measured.

