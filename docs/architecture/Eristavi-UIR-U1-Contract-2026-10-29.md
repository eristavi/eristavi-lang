# Eristavi UIR — concrete U1 operation and verification contract

Date: 2026-10-29
Status: Core U1 contract and scalar-first sequence agreed. PR #58/#59/#60 are merged, including initialized scalar cells, independent verification and mandatory cell-free SSA promotion. Final PR CI and completed-batch bootstrap repeatability/owned-integration qualification passed. Remaining U1a features, physical accounting, large owned stress and frontend/native integration remain pending. No public format is frozen.
Parent: Eristavi-Typed-Universal-IR-Proposal-2026-10-29.md, version 1, read for this specification.
Related contracts: agreed semantic architecture version 1; module/cache proposal version 3, including its pending UIR linkage clarification.
Source baseline: eristavi/eristavi-lang at 8af0ffe3350c737550c3ab0e6c3fa89f60f6f091. This is the inspected baseline, not a claim about today's latest GitHub head.

## 1. Decision and scope

U1 delivers a small executable, typed SSA contract for scalar computation, immutable aggregates, explicit control flow, direct calls, mandatory local promotion, and independently verified source provenance. The frontend eventually builds it from AST plus frozen semantic facts. No new source syntax or source-close executable Typed IR is introduced.

U1 is a functioning compiler-development slice, not a replacement for the full Eristavi compiler. The existing compiler remains the compatibility path until U2/U3 integration. An unsupported operation in a candidate UIR profile must be diagnosed explicitly; it must never be assigned guessed semantics.

Agreed delivery split: U1a implements pred, i64, strict f64, direct calls, branches/switches, returns, guards/traps, locations, independent verification, and mandatory promotion. U1b completes i8/i16/i32 and immutable aggregates within U1. The operation tables below define the full U1 contract; U1a's supported profile admits only its scalar subset and rejects unsupported types/operations explicitly. This is staged implementation, not a source-language restriction or an extra mandatory IR layer.

| Included in U1 | Deferred |
|---|---|
| pred, fixed-width integer bits, strict binary64, immutable structural aggregates | f32 execution and additional numeric formats |
| SSA values, block arguments, branch/switch, direct calls, return, guards/traps | Indirect calls, closures, general FFI |
| Private initialized virtual cells and mandatory promotion | Address-taking, aliased memory, aggregate scalar replacement |
| Independent type/signature/location tables and dense IDs | Managed Text/List/identity semantics, GC/root maps, resources and fallible calls: U2 |
| Independent verification and bounded initial simplification | New generic-template artifacts, universal address/provenance design, moving GC |

The architectural proposal's broader type vocabulary is not a requirement to implement every type in U1. U1 has no runtime byte-string or source-spelling Float literal operation; those belong to later explicitly specified services/adapters.

## 2. Ownership, IDs, and publication states

The program owns immutable types, signatures, constant payloads, function declarations, import contracts, and location tables. A function owns blocks, instructions, values, edges, and private construction cells. These records retain no AST, semantic Analyzer, live TypeVar, or old typed.Program.

Use distinct 32-bit ID APIs: TypeId, SignatureId, FunctionId, LocId, BlockId, InstId, ValueId, and private CellId. Reserve zero for absence, never for a valid operand or executable result. Check ID exhaustion, range arithmetic, capacities, and operand counts before allocation. Block/Inst/Value/Cell IDs are function-owned; cross-function use is invalid. Program-level IDs are remapped on artifact import and are not persistent symbol identities.

Indexed storage may contain explicitly dead slots during a mutation batch. IDs stay stable for that batch. Instruction order comes from block instruction ranges/lists of indices, not numerical InstId order. Public external sparse IDs must be bounded and remapped; never allocate an array sized by their maximum spelling.

Logical records include:

| Record | Required fields |
|---|---|
| Type | Kind and kind-specific immutable payload |
| Signature | Ordered parameter TypeIds and ordered result TypeIds |
| Function declaration | Logical symbol identity, owner module, SignatureId, definition/import kind, effect contract |
| Function definition | FunctionId, entry BlockId, current revision, block/value/instruction/edge storage |
| Block | Ordered parameter ValueIds, ordered instructions, exactly one terminator |
| Value definition | TypeId and unique defining block-parameter or instruction-result slot |
| Instruction | Operation kind, typed attributes, operand/result ranges, LocId |
| Edge | Target BlockId and ordered argument ValueIds; two edges to the same block remain distinct |
| Location | Source revision identity, byte span, diagnostic anchor, origin information |

These are logical fields, not a frozen byte layout. Variable-length records use pooled ranges. No linked allocation per operand or string-based runtime-helper signature reconstruction is required.

States are private builder -> complete construction form -> canonical verified U1 -> optionally transformed verified U1. A verifier stamp includes function/program revision and the exact contract context. Mutation invalidates it. Unfinished builders, failed promotion, cancellation, or budget exhaustion cannot publish a ready product. Transfer or freeze ownership before publication; no scheduler shares a mutable builder.

## 3. Exact type rules

| Type | Meaning |
|---|---|
| pred | Exactly false or true; no integer truthiness |
| i8, i16, i32, i64 | Exactly W bits; signed interpretation is two's-complement and selected by the operation |
| f64 | IEEE 754 binary64 under the strict value profile in section 5 |
| aggregate(T0, ..., Tn-1) | Immutable ordered components; empty aggregate is allowed as an actual value |

U1 aggregate elements recursively contain only U1 types. The by-value type graph is finite and acyclic. Aggregate equality is not an implicit U1 operation; a frontend lowers required scalar-field comparisons explicitly. Logical aggregates have no native byte padding, pointer identity, or target storage layout at this level. Nominal Eristavi value/identity mapping remains U2 work, not permission to equate distinct source nominal types.

Structural types and signatures have canonical interning within the program. Type equality is exact canonical TypeId equality after checked import remapping. A signature with zero results denotes no value, not an empty-aggregate result. UIR supports multiple result values without creating a source Void type.

Function parameters are the entry block's parameters, in signature order; they are not duplicated as separate value definitions. The entry has no incoming CFG edges. Other blocks may have any typed parameter sequence. Calls and returns must match complete ordered signatures exactly, without implicit numeric conversions.

## 4. Operation registry and integer semantics

Names below are internal symbolic names for review, not source keywords or frozen serialized opcode numbers. The registry is authoritative for arity, types, attributes, results, effects, locations, and profile membership. Unknown attributes, operation modes, and required contracts are rejected.

Let I denote one identical integer TypeId of width W, A one aggregate type, and T any U1 type. Every result is a fresh ValueId. Zero-result operations allocate none.

| Operation | Operands -> results | Required attributes and semantics |
|---|---|---|
| const.pred | () -> pred | Boolean value only |
| const.int | () -> I | Integer TypeId and exactly W validated bits; no truncation of an oversized payload |
| const.f64 | () -> f64 | Exactly 64 validated bits, including signed zero, infinities and NaNs |
| pred.not | pred -> pred | Boolean negation |
| pred.and / pred.or | pred, pred -> pred | Eager Boolean operations on already computed operands |
| i.add.wrap / i.sub.wrap / i.mul.wrap | I, I -> I | Mathematical operation reduced modulo 2^W |
| i.add.overflow / i.sub.overflow / i.mul.overflow | I, I -> (I, pred) | Required signedness=signed or unsigned; wrapped result plus true exactly when the mathematical result is out of that interpretation's range |
| i.cmp | I, I -> pred | Required relation eq, ne, slt, sle, sgt, sge, ult, ule, ugt, uge; signedness is encoded in the relation |
| i.div / i.rem | I, I -> I | Required signedness; zero divisor traps; signed minimum/-1 traps for BOTH operations |
| aggregate.make | T0, ..., Tn-1 -> A | Operand count/types exactly match A |
| aggregate.get | A -> Tk | Required static field index k in range |
| aggregate.set | A, Tk -> A | Required static field index; immutable replacement, preserving all other components |
| call | signature parameters -> signature results | Direct FunctionId; no checked-failure continuation in U1 |
| guard | pred -> () | Required TrapCode; continue if true, otherwise terminal trap at this instruction's location |

Integer division is exact unsigned division or signed division truncated toward zero. Remainder satisfies a=q*b+r mathematically; nonzero signed r has the dividend's sign. There is no host-language undefined overflow or poison. A trapping operation defines no result on its trapping execution; execution does not continue with an arbitrary placeholder.

The overflow-result bits are defined even when the overflow predicate is true. It is legal for another frontend to inspect them. Eristavi maps ordinary checked arithmetic to overflow reporting followed by pred.not and guard. Native selection may fuse that sequence without changing order or fault attribution. Signed unary negation uses signed subtraction of the operand from zero followed by its guard. Source-known invalid literals/arithmetic remain semantic diagnostics before UIR; an optimizer does not introduce new source diagnostics.

No initial shift, integer/Float conversion, bitcast, native address cast, saturation, or fast arithmetic operation is implied. Adding one requires its own complete registry entry and acceptance cases. Additional widths do not add new Eristavi integer source types.

## 5. Strict floating-point operation contract

| Operation | Operands -> results | Meaning |
|---|---|---|
| f.add / f.sub / f.mul / f.div | f64, f64 -> f64 | One binary64 operation, nearest ties to even |
| f.neg | f64 -> f64 | Sign negation, preserving the sign distinction of zero |
| f.cmp | f64, f64 -> pred | Required relation eq, ne, lt, le, gt, ge with Eristavi IEEE comparison behavior |

NaN comparisons are unordered: eq/lt/le/gt/ge are false when either operand is NaN; ne is true. Positive and negative zero compare equal. Subnormals use gradual underflow. Overflow produces the appropriate infinity. Floating division by zero follows IEEE results rather than integer fault semantics.

In this value profile, NaN payloads/signaling status and floating exception flags are not observable through UIR operations. Signaling NaNs do not introduce a new UIR trap; permitted NaN canonicalization must not change any supported observation. No bitcast or ambient floating-environment inspection is provided. A frontend needing those observations requires a separately defined profile, not a false claim of compatibility.

Each arithmetic operation rounds at binary64 precision. Do not reassociate, silently contract multiply-add, retain excess intermediate precision, or enable flush-to-zero/denormals-are-zero. Establish the required floating environment at execution/foreign adapter boundaries; a caller's ambient rounding/trap mode must not redefine the profile. This boundary is a runtime/ABI obligation, not an extra world-token operand.

Constant evaluation must implement these rules independently of unchecked host arithmetic. Decimal spelling is converted once in semantic literal processing; const.f64 contains the resulting bits.

## 6. Terminators, switches, and calls

| Terminator | Contract |
|---|---|
| jump edge | Exactly one successor |
| branch condition, trueEdge, falseEdge | pred condition, exactly two distinct edge records; targets may be equal |
| switch selector, cases, defaultEdge | Integer selector; zero or more unique same-width bit-pattern cases and exactly one default |
| return values | Exact function result arity/types; zero results allowed |
| trap TrapCode | No successor and no result; terminal runtime-defect outcome |

Every block, including an unreachable block, has exactly one final terminator and no instruction after it. A call is an instruction and may return normally, trap, or diverge according to its effect contract; its signature has no checked-failure result in U1. Forward declarations and recursion are supported through already resolved concrete signatures. Function identity is a declaration-table reference, never a parsed fN helper string.

An edge supplies exactly the destination parameter count/types. Arguments are values available at the predecessor terminator. Transfer is simultaneous: jump loop(y,x) swaps the two bindings, even when the backend reuses their physical locations. Never lower it as two destructive sequential assignments.

Switch compares integer bits, has no fallthrough, and chooses default when no case matches. Canonical case order is ascending unsigned bit-pattern order; use a temporary sorted index for duplicate validation rather than changing observable source evaluation. Cases contain no evaluated expressions or side effects. Sparse sets require no allocation proportional to the numeric case span. U1 does not mandate jump tables.

U1 has no variant-payload extraction. A future typed variant-tag operation can feed the integer switch; U2 must separately specify payload refinement checks and failure-edge availability. Including switch now does not silently implement checked errors or general sum types.

TrapCode initially contains integer_overflow, integer_zero_divisor, invalid_state, and compiler_unreachable. Guard may use an applicable code; there is no opcode granting arbitrary behavior after an unreachable assertion. A source-derived trap/guard/division needs its own diagnostic origin. If both exceptional division conditions are considered, zero-divisor and min/-1 are disjoint, so their fault choice is unambiguous.

The trap outcome is distinct from a checked failure. Agreed standalone policy: runtime-defect traps terminate the process without running resource/user cleanup and do not return to a host caller. Normal returns and checked failures retain required cleanup. No file flush, write durability, persistent/distributed-lock release, or crash-recovery guarantee follows from process termination. Recoverable embedding/isolation is a separate runtime design. U1 reference evaluation can report a terminal trap outcome without choosing a host exit status. Native trap execution still needs a validated reporting/runtime adapter; internal compiler bugs must not be presented as ordinary source type errors.

## 7. Effects and legal transformations

Constants, predicate/integer nontrapping arithmetic, comparisons, strict Float operations, and immutable aggregate operations are effect-free and terminating under this profile. Resource exhaustion in the compiler while constructing IR is not an effect of executing these logical operations. Aggregate physical materialization is a backend obligation; use scalar/register/stack representations rather than silently introducing observable managed-heap copy/allocation effects. A backend that needs such effects requires an explicit lowering/resource-exhaustion contract, not a false purity annotation. Native stack/execution resource-limit policy belongs to the runtime/ABI boundary and is not settled by classifying an aggregate operation as pure.

guard, i.div, i.rem, and trap carry terminal-fault effects. Calls have explicit conservative read/write, external/I/O, allocation, trap, and divergence summaries where relevant. An empty checked-failure contract is not a purity claim. Imported call summaries come from selected trusted/versioned contracts, not arbitrary per-call optimization hints.

For defined functions, derive conservative summaries from body operations and the call graph. Include potential divergence for reachable CFG cycles and recursive call cycles unless a separately validated termination proof exists. Propagate the finite effect flags with a worklist over callers. Check any declared upper bound against the derived summary. No verifier can establish the behavior of arbitrary native code solely from its signature; validating the selected runtime/import contract is an explicit trust boundary.

Instruction/CFG order defines the order of effects. Preserve the first observable fault, external effects, divergence, and required diagnostic location. A known-fault operation cannot move ahead of earlier I/O. A call cannot be deleted merely because its results are unused. Pure predicate operations do not implement source short circuit: source and/or build conditional CFG so skipped operands are not evaluated.

Initial optional simplification is limited to exact constant folding, safe branch/switch simplification, dead-block removal after structural validation, SSA substitution, and trivial block-parameter removal. Mandatory promotion is not disabled by a low-optimization mode. Inlining, global value numbering, aggregate scalar replacement, and loop/check transformations are later additions, not U1 prerequisites.

## 8. Private virtual cells and mandatory promotion

CellId is a private construction variable, not an address, SSA result, resource owner, or retained runtime reference. One declaration gives its type and one cell.init site. The three construction operations are:

| Operation | Contract |
|---|---|
| cell.init CellId, value | Initialize that cell with an exact-type SSA value; no result |
| cell.read CellId | Produce one fresh SSA result of the cell type |
| cell.write CellId, value | Replace the current value; no result |

The initializer is evaluated at its source-defined position. Its cell.init must dominate all reachable accesses and precede same-block accesses. An init site inside a loop can execute again each iteration and resets that private cell then; it has no observable storage identity. A declaration inside a possibly skipped branch cannot justify a read outside the initializer's dominance region. Pre-promotion validation checks these obligations directly, without whole-register definite-initialization bitsets.

U1 cells cannot escape, be addressed, be passed to calls, or contain managed/resource types. Consequently all well-formed U1 cells are eligible for promotion. Canonical published U1 contains no cells and no cell operations. Later profiles can introduce genuine storage with its own verified semantics; silently retaining a mutable-register implementation is not the U1 fallback.

Promotion algorithm:

1. Complete construction; validate all records/types/locations, including dead blocks, plus reachable SSA uses and initializer dominance. Remove dead construction blocks only after these checks.
2. Index each cell's definitions (init/write) and reads, by block and position. Mark uses before the first local definition as upward-exposed. Compute each cell's live-in set by predecessor worklist propagation that stops at a block definition when no earlier read needs the incoming value. Visit each (cell,block) liveness state at most once.
3. Compute dominators. For each cell, place parameters at its pruned iterated dominance frontier, limited to live-in blocks. Each new parameter is itself a definition for placement. Process deterministic block/cell order and mark visited placement pairs.
4. Walk the dominator tree using an explicit enter/exit work stack and current-value stacks. Block parameters establish incoming values; init/write update the current value; reads become SSA substitutions. For every outgoing edge, append the current value for each inserted destination parameter in its declared order. Restore stacks when leaving a dominator-tree subtree.
5. Resolve substitutions, fill all backedge arguments, remove cell operations and trivial parameters with corresponding edge arguments, and reverify the complete canonical function. Reject an absent incoming value; never invent undef, poison, or a zero initializer.

Let B be reachable block count, E reachable edge count, and N the instructions plus encoded operand/result entries scanned. For scalar-place liveness, let L be visited (cell,block) states plus predecessor visits. Let F count dominance-frontier construction and placement visits, P inserted parameters, and G inserted edge arguments. Promotion budget accounts for N+L+F+P+G plus dominance computation and exact type work. L/F/P/G can grow with cells times CFG size. No universally linear source-size or wall-time claim is made. Count one scanned adjacency/operand/frontier entry as one work event and record allocated capacity bytes separately from logical entry counts, so doubling buffer capacity cannot disappear from the memory report.

The initial implementation uses the simple Lengauer-Tarjan dominator algorithm with iterative DFS and path-compression data structures; budget O((B+E) log(max(2,B))) time and O(B+E) storage. The original paper establishes O(m log n) for its simple implementation; retaining that algorithm's invariants is a requirement, not a property of any algorithm that happens to use path compression. Validate it against an independent small-graph dominator-set oracle. Frontier work remains separately counted; a good dominator bound is not a bound on total SSA expansion. Build dominance for the exact CFG revision and revalidate if the CFG changes.

## 9. Deterministic independent verification

The verifier receives only the UIR plus the selected registry/profile/import context. It does not trust builder flags, semantic facts, optimization metadata, or an old revision's stamp. It may share basic range/graph utilities, but must derive its own checked facts from the supplied representation.

Validation order is phase -> stable function declaration order -> block storage order -> instruction/operand/edge order. Stable means the representation's defined order, not hash iteration or allocation addresses. A diagnostic identifies a category, function/block/instruction, and LocId when valid. Verifier diagnostics do not replace the earlier proposal's source diagnostic traversal order; these are internal/malformed-artifact errors.

| Phase | Required rejection checks |
|---|---|
| V0 bounds/contracts | Overflowing counts/ranges, unsupported schema/profile/operation/attribute, excessive declared resource use, invalid table ownership |
| V1 types/declarations | Invalid type graph, noncanonical/conflicting identities after remapping, unresolved types, duplicate declarations/definitions, wrong entry signature |
| V2 all-block structure | Bad IDs/definitions/results, dead-slot reference, missing/extra terminator, wrong operand/result type or arity, invalid call/field/case, bad edge target/arguments, entry-targeting edge |
| V3 locations | Missing required LocId, invalid source/span/anchor, malformed origin links or origin cycles |
| V4 reachable SSA | Use before definition, own-result use in its defining instruction, non-dominating definition, invalid block-parameter availability, wrong initializer dominance in construction form |
| V5 profile/effects | Construction cells surviving canonical publication, undeclared operations/contracts, understated defined-function effects, unavailable imported runtime contract |

Scan all instructions for existence/type/structure even when unreachable. Build reachability and dominators only for the reachable CFG. Same-block ordinary uses require an earlier instruction definition or a block parameter. A cross-block definition's block must dominate the use block. Terminator edge arguments are uses at that terminator. A block parameter is defined at its block entry and cannot be used in a predecessor unless it independently dominates that predecessor, as on a valid backedge.

Dead components must reference existing correctly typed values, but U1 does not pretend they have a meaningful executable dominance path. Any transformation making them reachable must pass the full verifier again. Predecessor edge counts and argument checks retain duplicate-target edges; do not collapse them into one edge and lose argument differences.

Verification uses indexed definition tables, iterative graph traversal, and dominator-tree entry/exit intervals for O(1) dominance queries after construction. Overall work is structural/operand scanning plus checked type/location graphs, dominance, switch-case duplicate checking, and effect propagation. Large case tables can require O(C log C) comparison sorting; do not call the entire verifier unconditionally linear. No per-block full-register definite-initialization masks are part of canonical SSA verification.

Required gates: complete construction before promotion, canonical publication after promotion, every changed optimization batch, decoded implementation ingress, and later post-legalization. Verify directly supplied IR even without serialized ingress. A successful stamp is session-local and bound to revisions of affected declarations, signatures, contracts, and locations as well as function instructions. No serialized trusted=true flag authorizes execution.

## 10. Source provenance and optimization rules

LocId refers to program-owned immutable metadata, not a borrowed AST node. The source identity includes logical module/file identity and content digest. Store half-open UTF-8 byte span and diagnostic anchor plus the existing diagnostic line/column convention. Keep a compact source map sufficient to report without source bytes; if source is reopened, validate its digest before showing excerpts. SourceId integers and checkout absolute paths are not serialized identity.

Every source-derived call, guard, division/remainder, and trap carries a nonzero valid LocId. Pure computations may also carry origins. Synthetic operations use a synthetic origin record with a reason and parent source origin when one exists; core-only hand-built functions may use an explicit synthetic module/function origin. Origin references form an acyclic graph, not arbitrary recursion.

Promotion preserves the initializer/computation's execution point and fault origins. Pure value substitution may change a value's defining site but does not rewrite the LocId of a consuming guard/call. Folding a successful pure operation may remove its runtime location. Folding a faulting operation must preserve its original runtime fault site/order; it does not create a new compile-time source error.

Two observable checks with different required diagnostic origins are not merged merely because the tested values match. Shared pure values can retain deterministic origin sets in side metadata. The future inliner must retain callee plus call-site chains. Later cleanup operations retain resource declaration/cleanup origin and relevant exit origin. Those are obligations on later passes, not U1 implementation of cleanup/inlining.

Required runtime-report locations survive machine selection and optional debug stripping. Full symbolic debugging is a separate feature. Final trap/report encoding and existing-runtime adapters are later implementation contracts; neither a bare CPU fault nor a debug-only line table alone proves diagnostic fidelity.

## 11. Illustrative valid SSA examples

This notation is documentation, not a new input language or frozen dump format. Constants and value definitions belong to their written blocks. @Ladd/@Lstep identify valid source locations.

Checked Eristavi addition:

```text
function add(a: i64, b: i64) -> (i64)
entry(a: i64, b: i64):
    (sum, overflow) = i.add.overflow signed a, b
    ok = pred.not overflow
    guard ok, integer_overflow @Ladd
    return sum
```

A mutable local becomes a block parameter, not a mutable result register:

```text
function choose(flag: pred, first: i64, second: i64) -> (i64)
entry(flag: pred, first: i64, second: i64):
    branch flag, left(), right()
left():
    jump join(first)
right():
    jump join(second)
join(value: i64):
    return value
```

Loop-carried source counter after promotion:

```text
function count(limit: i64) -> (i64)
entry(limit: i64):
    zero = const.int i64 0
    one = const.int i64 1
    jump test(zero)
test(index: i64):
    continue = i.cmp slt index, limit
    branch continue, body(), done(index)
body():
    (next, overflow) = i.add.overflow signed index, one
    ok = pred.not overflow
    guard ok, integer_overflow @Lstep
    jump test(next)
done(result: i64):
    return result
```

The uses of limit/one in dominated blocks are valid. A RevaSM adapter may later thread them explicitly; U1 does not force that cost on every target. A separate edge test jump loop(y,x) must preserve a swap when physical locations coincide.

## 12. U0 measurement protocol and budget gates

This specification prepares the plan; it records no new measurement results. Before implementing the corresponding U1/U2 slices, establish and record numeric acceptance and resource budgets from a reproducible baseline. Do not choose passing thresholds after inspecting a candidate's results. If a metric has no meaningful legacy analogue, explicitly set an initial capacity/work policy and measure candidate scaling; label it a policy, not a measured speedup.

Subsequent evidence record: Eristavi-UIR-U0-Baseline-2026-10-29.md and its evidence archive contain 60 source-pipeline samples across 12 fixtures, all 12 expected native application outputs, and 30 corrected paired native-verifier/runtime samples. That initial batch does not measure a new UIR. Its timing noise is too high for a narrow percentage regression gate, and its proposed exact merge/edge-count gates are not production input limits. Review the evidence before closing capacity/timing budgets; U2 and other explicitly unmeasured metrics remain open.

Pin source/compiler/runtime hashes, dirty inputs, host/CPU/OS, target/ABI, build flags, allocator/collector configuration, fixture digest, and command. Separate owned and bootstrap paths; a fast bootstrap result does not establish owned performance. Record wall/CPU time, peak RSS, output identity, and stage start/end events. Use five paired fresh-process baseline/candidate samples for comparable completed workloads, alternate order, and report raw samples/medians plus spread. State warm/cold cache and OS-page-cache conditions separately. A timed-out stage is censored, not a completed duration or evidence that the next stage dominates.

| Fixture | Required counters and observations |
|---|---|
| Scalar/boundary cases | Operations, guards, helper calls, exact values/trap kind/location |
| N mutable locals with diamond joins | Cells, definitions/reads, L/F/P/G, construction/promotion/verification time and memory |
| Nested and irreducible loops | Dominator work, live-in/frontier visits, backedge arguments, recursion-free traversal |
| Wide/sparse switches | Cases, edges, argument entries, case-validation time; no case-span allocation |
| Direct-call graph/recursion | Signature validation, effect-worklist events, conservative divergence |
| Pure aggregates and locations | Type/location graph size, source-map bytes, transformation/report fidelity |
| U2 nested resources and many exits | Owner scopes/signature/edge entries S, maximum depth, cleanup X/A and emitted close count |
| U2 repeated cleanup failures | Append operations/bytes, primary/secondary order, runtime growth; no repeated-prefix copying |

Vary graph/local/nesting sizes independently over at least three scale points. Include a fixed representative compiler input when the old path can complete it, but do not substitute another 900-second self-build for missing small-fixture evidence. Reuse existing qualified results only when their hashes, instrumentation, and workload make the comparison valid.

The U0 record must fill: fixture sizes/hashes; per-stage time/RSS baseline; input ceilings; dominance/frontier/live-in work ceiling; parameter/edge growth ceiling; verifier overhead budget; U2 owner/cleanup code-size and runtime budgets; and noise/repetition policy. None of these numerical fields is silently approved by this document. Correctness failures block acceptance regardless of speed. A resource-limit diagnostic must name the exhausted budget; cancellation checks occur at stage boundaries and bounded graph/worklist loops. Do not publish partial UIR on either outcome.

## 13. Acceptance matrix and delivery order

| Area | Positive cases | Mandatory rejection or preservation cases |
|---|---|---|
| Integer | Widths, wrap, signed/unsigned overflow flag, truncating division and signed remainder | Mixed widths, bad constants, zero divisor, signed min/-1 for div AND rem, no hidden wrap for Eristavi |
| Float | NaN/infinities, signed zero, ties, subnormals and non-FMA examples | Wrong NaN ne, FTZ, excess precision, silent reassociation/contraction, implicit conversion |
| SSA | Diamonds, nested/irreducible loops, simultaneous edge swap, repeated-target edges | Duplicate result, same-instruction self-use, use-before-definition, non-dominating use, wrong edge arity/type |
| Promotion | Outer and loop-local initializers, multiple writes, trivial merges, unused cells | Init not dominating use, missing incoming value, eligible cell surviving publication, moved effect/fault |
| Switch | Empty, dense/sparse, min/max bits, default, same target with different arguments | Duplicate bits, wrong case width, missing default, allocation by largest case value |
| Calls/effects | Forward calls, recursion, zero/multiple results, trusted import match | Signature mismatch, unsupported checked failure, undeclared runtime contract, dropped effect/divergence |
| Structure | Independent types and owners, bounded sparse-ID remap, dead-block typing | Cross-function ID, stale/dead value, malformed unreachable instruction, cyclic by-value type/origin graph |
| Locations | Original fault anchor through folding/promotion and artifact remap | Missing required origin, stale-source excerpt, merging distinct observable fault sites |
| Revisions | Reverify after instruction/CFG/signature/location mutation | Old verified flag or old analysis hiding a defect |
| Universality | Hand-built scalar/aggregate program with no Eristavi GC/List/failure ABI assumptions | Depending on old typed.Program or forcing the 32-byte Eristavi value ABI into core types |

Use an independent reference evaluator for scalar operations and CFG execution, an independent small-graph dominance oracle, generated arithmetic boundaries, malformed-IR mutations, and differential transformation cases. Evaluator fuel exhaustion is inconclusive for program behavior, not an Eristavi runtime fault. Evaluate side-effect order through a controlled test import contract. These are future validation requirements, not tests already implemented/run.

Delivery order:

1. Record the agreed scalar-first contract and terminal-trap policy; complete U0 numeric budget decisions before the corresponding rewrite begins.
2. Implement independent tables, registry, dense builders, scalar reference behavior, and structural/type/location validation.
3. Implement reachable SSA verification and mandatory promotion, with loop and expansion gates.
4. Implement bounded simplification and revision/invalidation discipline; verify every changed published batch.
5. Qualify the functioning U1 slice. Preserve the full existing compiler while U2 managed/failure/resource contracts and U3 native integration are completed.

Focused correctness checks belong with each substantive slice. Expensive compiler-wide/self-build qualification is batched at the integration gate, not repeated after every edit. No rewrite, workflow dispatch, or test execution is authorized merely by this document's existence.

## 14. Cache/artifact linkage and remaining decisions

No new production binary format or extension is selected. All compiler implementation remains .eri. Debug names in this document are not a public opcode-number allocation.

An action producing/consuming U1 must key the relevant encoding/schema, core operation contract, strict Float profile, construction/canonical profile, verification policy, compiler implementation identity, and selected import/runtime contracts. Its manifest declares the same requirements. Later legalization/ABI/target inputs enter the actions that actually consume them. Canonical in-memory IDs are remapped and cannot act as persistent cache identity. Source location data must participate in artifact content/provenance so a diagnostic cannot silently name another revision.

Decoded implementation IR is always reverified. Version/hash agreement does not establish semantics. Existing generic-source/JSON adapters remain in use; the module proposal's original item 8 still gates replacement generic artifacts on a separate template/profile design. U1 does not reopen filesystem decision FS-001 or public ABI decisions.

The initial U1a budget decision is specified in section 15, including explicit capacity/work policies for metrics without a legacy analogue. This closes the requirement to select U1a budgets before seeing a candidate. PR #58 implements the first ledger and construction adapter; complete enforcement and candidate compliance remain required. The scalar-first contract and standalone terminal-trap policy are agreed; native trap execution still requires the reporting/runtime adapter. U2 managed/failure/resource operation details and budgets remain a separate review. Later independent tool reviews cover machine IR, runtime/report ABI, register allocation, encoding, objects/linking, and packaging. This document specifies neither a speedup nor a completed compiler. U0 observations remain a separate evidence record.

## 15. Selected initial U1a resource and acceptance policy

Internal profile: uir-u1a-development-1. Canonical numerical data and fixture recipes are in Eristavi-UIR-U1a-Budgets-2026-10-29.json. MiB means 1,048,576 bytes. The profile was selected before new UIR code existed. It is an initial engineering policy, not a measured optimum, a public stability promise, or an assertion of candidate compliance. A later revision needs a recorded reason and fresh validation; do not increase a failed gate silently.

### Memory scopes and limits

| Scope | Peak owned capacity | Cumulative fresh allocation traffic |
|---|---:|---:|
| One function lifecycle, development ceiling | 64 MiB | 256 MiB |
| Shared UIR types/signatures/constants/locations | 128 MiB, also within request total | Within request traffic total |
| All UIR owners in one request, including retained published functions | 512 MiB | 2 GiB |
| Each fixed qualification function, including the initialized width-2,000 stress plan | 8 MiB | 64 MiB |

The qualification lifecycle covers construction, promotion, and eight verifier calls; eight calls are a stress workload, not eight mandatory production passes. Ordinary construction/canonical publication gates stay as specified earlier. All simultaneously live IR, builder buffers, tables, edge/operand pools, counters, and analysis scratch belonging to that function count toward its limit. Track actual allocated capacity rather than only element lengths. Function records/pools/scratch must use their function owner; parking them in shared metadata to evade the 8 MiB gate is invalid. Shared metadata is charged once at its owner, not once for every function referencing it. Its bytes still count toward request peak. Use a fresh request for each qualification fixture, permitting explicit scratch reuse within its eight verifier calls.

Capacity accounting covers UIR-owned backing storage and metadata. Allocator headers/rounding must be charged when the storage adapter exposes their reservation size; otherwise identify their excluded overhead explicitly. Earlier-stage source/AST/semantic owners, unrelated runtime pools/GC retention, and later native-backend storage are separately reported. Thus 8 MiB of UIR-owned capacity is not an 8 MiB process-RSS guarantee and is not derived from the old probe's 7.03 MiB RSS. Do not claim compliance while omitting UIR-private allocations outside the accounting boundary.

Peak and traffic answer different questions. Reusing existing scratch capacity adds no fresh traffic. Acquiring a larger buffer charges the full new backing allocation; keep the old allocation charged until it is actually released or exclusively transferred. Both exist during growth/copy, so peak cannot be computed as only the capacity difference. Cumulative traffic never decreases when a buffer is freed. Retained allocator pages are reported separately from active UIR ownership; this policy does not guarantee prevention of runtime/OS allocation failure.

### Count ceilings and work budgets

| Per-function stored count | Initial ceiling |
|---|---:|
| Blocks | 65,536 |
| Edges | 262,144 |
| Instructions, including terminators/construction operations | 1,048,576 |
| SSA value slots | 1,048,576 |
| Private cells | 65,536 |
| Inserted merge parameters | 1,048,576 |
| Total edge argument entries | 4,194,304 |

Counts include allocated/stored slots, including dead slots not yet compacted. These are independent admission ceilings, not a claim that all maxima fit together into the memory limit. The first exceeded applicable count, byte, or work limit stops the attempt. Reserve/check before allocation; bounded sparse-ID remapping is still mandatory. Count limits are not array sizes selected from the largest external ID.

| Work scope | Visit ceiling |
|---|---:|
| Function construction | 16,777,216 |
| One complete verification call | 16,777,216 |
| One function promotion | 33,554,432 |
| Whole request across all phases/functions | 268,435,456 |

A visit is an entry inspected, comparison, or hash probe. Bulk operations charge ceil(bytes/64) work units and retain byte counts separately. Variable-length metadata, sort comparisons, collision probes, and retries cannot hide behind one nominal operation. Budget accounting itself allocates no record and performs no virtual dispatch per visit. Admit bounded chunks, then record actual consumption and unused prepaid credits separately. Charges are checked wide integers; evaluate products against remaining quotas without overflowing, using division comparisons before multiplication where required.

The global work quotas supplement these algorithm-specific guards:

- Structural validation: at most 32*(R+1) visits in its scan component; R counts the encoded records, attributes, operands/results, edge arguments, cases, and origin links in the validated scope. Sort/dominance/effect-worklist components are separate categories within the complete verification limit, not hidden inside this linear scan claim.
- Dominator construction: at most 128*(B+E+1)*max(1,ceil(log2(max(2,B)))) recorded visits. B/E count the reachable CFG for that exact revision. This is an engineering work guard around the selected algorithm, not a new complexity theorem.
- Promotion: at most C*B distinct live-in states, C*E liveness predecessor visits, and C*B unique placement worklist states. Iterated-frontier entry visits are bounded by C*D, where D is the once-built CFG frontier entry count. Record frontier construction work too. All of it remains within the promotion visit quota.
- Inserted merge parameters are bounded by C*B and inserted merge-edge arguments by C*E, as well as their explicit count/byte ceilings. C counts candidate cells. These checks forbid repeatedly treating the same state as newly discovered; they do not erase legitimate cell-by-graph work.

These limits are chosen before candidate measurements as explicit fail-safe policies. Their powers-of-two capacities simplify checked admission and allow headroom beyond the measured fixtures; no hardware optimum or throughput guarantee is inferred. The 8 MiB/64 MiB qualification gates are deliberately tighter than general development ceilings so the initial fixtures cannot pass solely through a very large arena or excessive allocation churn.

### Exact qualification shape

Use all twelve pinned U0 source snapshots and expected outputs. At the canonical checkpoint after promotion/trivial-parameter cleanup and before optional CFG/constant transforms:

| Family, N=8/32/128 | Remaining cells | Inserted merge parameters | Inserted merge-edge arguments |
|---|---:|---:|---:|
| Diamond locals | 0 | N | 2N |
| Loop locals plus index | 0 | N+1 | 2(N+1) |
| Sequential calls | 0 | 0 | 0 |
| Sequential diamonds | 0 | N, one at each join | 2N |

Exclude function entry parameters and ordinary call arguments from merge counts. Native output, checked arithmetic, effect order, and source fault locations must remain correct. Resource budgets never excuse a correctness failure. f64 edge cases, malformed IR, sparse switches, parallel-copy cycles, irreducible graphs, cancellation, and post-mutation verification remain separate mandatory correctness cases before U1a acceptance; the integer fixtures do not cover them automatically.

Add an initialized diamond/16-chain stress family at widths 128, 512, and 2,000. Initialize every x[i]=i; branch on an input flag; update every local by checked +1 or checked +2; traverse the 16 chain blocks; return the checked sum. Observe both flag choices, which must produce width*(width-1)/2+width and width*(width-1)/2+2*width respectively. Its pruned join has width parameters and 2*width merge arguments. These recipes are test fixtures, not an additional production IR or source language.

The historical native wide() probe is not a matched timing baseline for this new family: it leaves some registers uninitialized on some paths and observes only selected initialized values. Initializing all cells or adding a checksum changes the work. Future legacy/candidate adapters must consume the same new logical recipe and independently reproduce both results. Run a fresh paired comparison when both adapters exist; do not attach the old 16.56-second number to different work.

### Timing and watchdog policy

For qualification workers, select 60 CPU seconds and 120 wall seconds per worker. These are broad test-harness watchdogs, not normal compiler deadlines, speed targets, or estimates. The largest completed old probe used at most about 19.12 CPU seconds in this batch, so the CPU watchdog provides roughly threefold headroom for development while still bounding an accidentally runaway test. Different hosts can need a documented harness override; a wall-only timeout under contention is inconclusive about generated-program semantics or steady-state performance.

Comparative timing remains informational for initial U1a. There is no invented 5-percent historical-median gate. Construction, promotion, verification, native lowering, interpreter startup, and reference evaluation are separate metrics; never compare a hand-built new-IR core time directly against the legacy source-to-assembly total. A matched core experiment constructs once, promotes if its representation requires it, and verifies eight times for both logical recipes; report those components separately and preserve the expected observations. A source-to-assembly comparison waits for U3 integration and equivalent supported behavior.

Use five fresh-process baseline/candidate pairs on the same host, same runtime profile/compiler flags, pinned inputs, and declared cache state; alternate order and serialize jobs. Report raw observations and spread. A candidate meeting the broad watchdog still needs the exact work, capacity, and correctness gates; finishing within 60 seconds alone cannot be described as optimized. Before U3 promotion, a representative integrated workload must have its own reviewed performance acceptance decision.

### Allocation, cancellation, and failure protocol

The first code slice implements the budget ledger with dense table/buffer ownership; this is not a separate general-purpose allocation subsystem. Logical API contracts:

| API | Required behavior |
|---|---|
| reserveCapacity(owner, bytes, reason) | Admit pending capacity and prospective traffic against the owner and every ancestor before allocation |
| commitReservation(reservation, handle) | Move a successful reservation into live capacity; commit fresh traffic |
| cancelReservation(reservation) | Remove a failed pending reservation; retain consumed work; add no successful allocation traffic |
| releaseCapacity(handle) | Lower live ownership only after release/exclusive transfer; never reduce cumulative traffic |
| transferCapacity(handle, destination) | Check destination branch, then transfer atomically; shared-ancestor live capacity and fresh traffic stay unchanged |
| chargeWork(phase, category, count) | Admit a bounded batch before its work; retain consumed and unused prepaid amounts distinctly |
| pollCancellation(attempt) | Stop that unfinished attempt; prevent later publication |
| snapshotCounters(owner) | Capture committed live/peak, pending/reserved peak, traffic, work, and exhausted-limit identity |

Use one request parent, child function lifecycles, and a shared-metadata child. Ownership transfer into a published request result is not release of its storage. Source and destination limits must be checked before changing any ownership or counters. Pending reservations consume admission headroom but are distinguishable from successfully committed bytes in measurements. A failed allocation rolls back its reservation; it does not roll back work already executed. This prevents retries from appearing free.

Poll at stage entry/exit, before allocations/growth, before publication, and at most every 1,024 element/work visits or 64 KiB of bulk data processed. No algorithm may conceal an unbounded loop, recursive graph traversal, or full-file hash behind one poll. Blocking host/allocator calls prevent a strict wall-latency promise; counters bound compiler work between polls.

Budget exhaustion produces a structured compiler resource-limit outcome with profile/phase/function, exhausted limit, requested/remaining amounts, and a valid source origin when available. It is neither a source type error nor a generated-program trap. Invalid IR retains its separate diagnostic category. Check counts/ranges with bounded arithmetic before reserve/decode.

A failed/cancelled attempt releases its owned scratch/private outputs and publishes no ready UIR, stale verifier stamp, or committed artifact. Existing independently committed valid products remain valid. Any mutating pass invalidates the old stamp before its first edit and keeps unfinished changes private. A retry has fresh function-attempt state, but consumed request-level work/traffic are not reset; failed attempts cannot become a cached ready result. No silent mutable-register fallback, verification bypass, automatic retry with enlarged quotas, or automatic budget increase is permitted.

Overrides are explicit internal request-profile values recorded before execution; no new CLI flag, source syntax, or production restriction is introduced now. Cache manifests/provenance record contract versions as specified earlier; resource values are recorded in attempt provenance. A compatible completed artifact may be reused only after current admission/verification requirements; neither an old budget profile nor a hash grants a bypass. Resource exhaustion must not silently select different operation semantics or partial optimizer output.

### Foundation implementation and next boundary

Foundation PR #58 remains merged as 6fb8b7bcd49418f398810ef9166acc888a35c4f5. [PR #59](https://github.com/eristavi/eristavi-lang/pull/59) merged as 8a2af1c95c0878a65aebbabb464ad1bf6c66db5e, including the C-bootstrap recovery fix. [PR #60](https://github.com/eristavi/eristavi-lang/pull/60) merged as cd421d859e3372796e59ddf236944efc1b6aaddb. Main's implementation tree equals tested tree c6a554e04c12d26c93650956709c5d57f1812ddf (promotion head 22b36c1de42a6bb1b6d54d03a9c69b7c49062082). Scalar-cell promotion, independent construction/canonical checks and transactional cleanup are implemented; production frontend/native integration remains separate. The full handover is [HANDOVER.md on GitHub](https://github.com/eristavi/eristavi-lang/blob/63297369fb7c41e9f13915f6102490f41ee9626a/HANDOVER.md), published in open documentation PR #61.

On 2026-10-30 the ten-test U1 focused batch passed, including both native runtime profiles and the 91-graph dominance oracle. Promotion independently compares 18 before/after IR pairs over 88 inputs, including complete guard/fault/location traces. Final GCC and Clang 18 -O2 differential/transactional checks pass, including eight negative cases and late-output failure/cancellation. Diamond, bounded-loop and sequential-diamond fixtures at N=8/32/128 meet their exact inserted-parameter/argument counts with eight additional verifications and unchanged modeled 8 MiB/64 MiB limits. The largest sequential case records 8,206,560 peak modeled bytes, 19,524,768 successful-allocation traffic bytes and 3,367,442 promotion-work units. These direct-IR fixtures are not the original source U0 workloads or a speedup benchmark. Per-case/source evidence lives in the repository's UIR_U1A_PROMOTION_EVIDENCE.json; original baseline measurements/archive are untouched. Both PR heads passed all four CI configurations. [Completed-batch qualification 41018345033](https://github.com/eristavi/eristavi-lang/actions/runs/41018345033) passed three bootstrap repeatability gates (C/D completed, offline audit successful, unchanged sources) and owned integration (repeatable=false, no C/D self-build, successful offline audit, unchanged sources). The separate full owned-self-build profile was intentionally skipped. Post-merge main CI was automatically triggered; this is separate from the completed pre-merge checks.

Mandatory scalar-cell promotion is implemented for the existing pred/i64/f64 construction profile; full U1a is not complete. Next are remaining scalar operations, calls/switches and strict Float execution, followed by source maps/origin chains, effects/import contracts, publication/revision capabilities and frontend/native integration. Scratch lifetime/claim-array reductions and phase-disjoint dominator storage reuse allow the selected direct-IR fixtures to pass modeled gates. Complete physical heap/GC accounting, packed native storage/physical ID layout, matched wider stress and owned-runtime performance qualification remain pending. The earlier combined owned graph/deep-chain run timed out at 120 seconds; that result remains unqualified. No limit was enlarged. One completed-batch full qualification was selected for the user-authorized merges. No separate 900-second full owned-self-build attempt was started.

Native reporting/ABI, U2 resources/failures, U1b aggregates/other widths, and the complete compiler rewrite remain separately staged. The contract above specifies requirements beyond this first implementation subset.

## Sources and grounding

- [Typed UIR architecture proposal](Eristavi-Typed-Universal-IR-Proposal-2026-10-29.md), version 1.
- [Semantic architecture](Eristavi-Semantic-Architecture-Proposal-2026-10-29.md), version 1.
- [Module/cache architecture](Eristavi-Module-Architecture-Proposal-2026-10-29.md), version 3.
- [Eristavi inspected source snapshot](https://github.com/eristavi/eristavi-lang/tree/8af0ffe3350c737550c3ab0e6c3fa89f60f6f091): FLOAT.md, INTEGER_REMAINDER.md, UNIVERSAL_VERIFICATION.md, src/compiler/universal_model.eri, src/compiler/universal_lower.eri, compiler/erist/universal_ir.py.
- [Lengauer and Tarjan, A Fast Algorithm for Finding Dominators in a Flowgraph](https://doi.org/10.1145/357062.357071): primary algorithm reference for the simple implementation's O(m log n) bound. It is not evidence of an Eristavi speedup.
- [Cytron et al., Efficiently Computing Static Single Assignment Form and the Control Dependence Graph](https://research.ibm.com/publications/efficiently-computing-static-single-assignment-form-and-the-control-dependence-graph): primary basis for dominance-frontier SSA construction. U1's live-in pruning, block-argument representation, publication rules, and budgets remain this project's explicit design choices.

Repository contracts support the required semantics and identify current representation differences. The proposed SSA/type/operation organization and algorithm choices are engineering recommendations, not measured proof of superiority. No external compiler framework becomes a dependency.
