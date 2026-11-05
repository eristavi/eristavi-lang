# U2 Managed Text / Unicode 17 canonical native slice

Status: opt-in bounded development slice, NOT production promotion or U2 acceptance.
Canonical structural UIR and private managed Text descriptor remain unchanged;
existing frozen Text semantics and 32-byte owned runtime ABI are preserved.

## Frozen contract

Text stores valid UTF-8 with scalar-sequence equality and no implicit Unicode
normalization. Views are explicit and read-only: bytes, scalars and Unicode 17
extended grapheme characters. Invalid Unicode scalars including surrogate code
points must terminate through the existing runtime fault path.

## New executable profile

The src/compiler/u2_text_native.eri adapter accepts one canonical block with
at most 128 SSA values, 256 instructions, no entry arguments and one scalar
return. It independently checks the full frozen UIR, exact twelve imported
operation names, signatures, conservative effects, version and explicit Text
carrier descriptor. The accepted closed profile is:
- fromScalar, concat, copy and scalar-sequence equality
- byte, scalar and Unicode 17 extended-grapheme counts
- explicit slots and Text collector call;
- read-only zero-based byte/scalar/character indexed access, with explicit
  negative/end-of-view terminal bounds and Text/Int result types;
- explicit Unicode NFC normalization, never implicit for equality.

The emitter calls existing Unicode17-owned runtime functions directly from
canonical instruction data. It does not use legacy source compiler lowering.
Rooted stack slots are registered before allocation and remain conservatively
live until function exit, with a registered temporary view slot during an
allocating Unicode view count. Other managed type families and all CFG/checked
failure opcodes are rejected before any assembly output.

The test's private ev_types table preserves existing descriptors 0..14 and
adds exact read-only view types 15..17 with bytes, scalars and characters names.
No new public ABI, source syntax, Unicode table or managed value layout is
introduced.

## Focused acceptance checks

- e plus U+0301: 3 UTF-8 bytes, 2 scalar values, 1 grapheme.
- Indexed byte 0/1 = 101/204; scalar 1 equals U+0301 and character 0
  returns the entire e+U+0301 grapheme.
- U+00E9 versus decomposed sequence: unequal, no normalization.
- Copy of decomposed Text: equal by scalar sequence.
- U+1F469 + U+200D + U+1F4BB: 11 bytes, 3 scalars, 1 grapheme.
  Byte 0 is 240, scalar 0 is U+1F469 and grapheme 0 is the ZWJ sequence.
- Explicit NFC transforms e+U+0301 into U+00E9 without modifying source.
- Negative and end-of-view indexes emit the exact existing terminal bounds fault.
- Explicit collection between allocation and later observation, full
  graph/Text/failure/handler/allocator teardown checks.
- Invalid descriptor/import refuses before emission; surrogate scalar
  fails via the existing terminal Unicode fault path.

Not covered: arbitrary Text literal UIR, view escape, multi-block
CFG, recursion, Text-containing aggregates, complete root maps, checked
failures/cleanup, full physical resource evidence or four-platform qualification.
Keep PR #111 in draft and U2 #74 open.

## Incremental CFG root-retention slice (development, not U2 acceptance)

Canonical Text admits a bounded verified CFG with at most 64 blocks, 512 edges,
128 SSA values and 256 instructions. The native emitter handles boxed Int/Bool
comparisons, branches and simultaneous edge arguments, including cycles, with
GC registered roots persisting conservatively through joins and backedges.
An unregistered edge scratch area is used only while no allocator or safe
point executes. A focused fixture appends combining accent Text across loop
backedges, forces collection and later reads both an old immutable snapshot
and the final string.

This is NOT exact machine-root liveness/release, per-instruction publication,
cross-function recursion, checked failure execution, deterministic cleanup
or physical retained-capacity proof. Those remain required acceptance gates.

## Failure-context Text retention — independent reference checkpoint

The existing typed `FailureContext` reference fixture now additionally
retains decomposed UTF-8 Text primary payloads and ordered Unicode17 emoji
and flag cleanup secondary payloads. It verifies no implicit normalization,
byte/scalar/grapheme integrity and deterministic secondary order after
several allocations, then releases charged context storage. The dedicated
Text-focused test workflow selects this fixture alongside native Text tests.
This is **reference validation only**: native canonical Text checked invoke,
recursive frames, scope cleanup adapters and root publication for saved
failures remain unimplemented and must not be reported complete.

## Bounded recursive native Text frames (candidate; qualification pending)

An isolated canonical Text self-recursion variant admits one verified local
declaration `u2.text.recurse` whose exact signature is
`(Text, i64) -> i64`. The original 12 external Text imports are unchanged.
The independent structural UIR verifier is rerun before emission; the
new variant additionally checks the exact local declaration name, contract,
entry parameter types, structural Text carrier, and no foreign FunctionIds.
An ordinary Text-only profile with no entry args still uses the original
emission path, unmodified.

The self-call is a *real* x86-64 function invocation. Each invocation enters
a separate scope, copies its inbound boxed Text and integer arguments to
registered stack roots before collection, and keeps its caller roots alive
while the callee allocates, collects and returns. Each return leaves its own
scope exactly once and decrements a private, bounded, single-thread depth
counter. The maximum number of simultaneously active frames is 32; a 33rd
invocation takes the existing terminal internal fault, without creating a
new source-level checked failure. The fixture exercises nested copies,
concatenation, explicit collection and the original parent Text after a
callee returns; its terminal depth test is deliberately isolated.

This is deliberately NOT general canonical interprocedural lowering, dynamic
dispatch, mixed managed signatures, typed checked-failure unwind,
cancellation-safe recursion, precise per-instruction SSA root retirement, or
physical root retention proof. The private depth counter is not thread-safe;
parallel execution must reject this profile until it has per-thread or
per-invocation depth administration. Do not merge U2 on this evidence alone.

## 5 November 2026 — bounded precise canonical CFG Text roots: Linux verified

The exact implementation at [ca88c31](https://github.com/eristavi/eristavi-lang/commit/ca88c3120236cad790d3269efa0d308afebffde6) adds an opt-in, independently verified `ssa.Plan` for the closed opaque structural Text carrier. In non-recursive **multi-block** canonical Function profiles with at most **32 selected Text SSA values**, it clears a dead Text root word after the corresponding instruction has finished using its operands and stored its result. At CFG edges it first captures every predecessor argument and writes all successor block-parameter slots, **without allocation**, then clears selected roots independently proven dead on that successor. This applies to loop backedges and preserves live captured Text across the next allocation or collection.

The new native probe uses exact canonical ValueId-derived frame offsets, reads the emitted machine frame immediately before a real owned-runtime collector safe point, and requires a dead concat input to be zero and two live cross-block/loop-carried Text inputs to remain nonzero. [Focused Linux Clang #41985303525](https://github.com/eristavi/eristavi-lang/actions/runs/41985303525) **PASS 8/8 methods, 0 failures**. [Exact-code Linux Clang smoke #41985303605](https://github.com/eristavi/eristavi-lang/actions/runs/41985303605) **PASS 107 run / 104 passed / 0 failures / 3 skips**. The earlier malformed test insertion and Eristavi handled-call error were corrected before this evidence and remain visible in prior failed CI runs.

The <=32-selected-Text-value upper bound and 128-value/256-instruction closed profile are unchanged. Existing single-block and local 32-frame recursive Text keep conservative roots, as do multi-block profiles with >32 selected Text values. Temporary view objects keep their separate registered view root. This does **not** add identity or checked failure root admission, a general managed UIR representation, interprocedural or thread-safe recursion, dynamic owned resource cleanup, a full machine root-map verifier, physical RSS/GC pause evidence, U2 final four-platform qualification, or a new public ABI. PR #111 stays DRAFT and U2 #74 OPEN. The earlier sections above are historical boundaries superseded only where this later section states so.
