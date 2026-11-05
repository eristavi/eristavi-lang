# Optional canonical List-i64 native execution — bounded development slice

The accepted managed operation shape requires immutable SSA snapshots: source
append/replacement returns no value; internal lowering returns a replacement
List handle. This slice consumes the existing canonical Function/Metadata pools.
It adds no second executable representation, source syntax or public value ABI.

## Selected legal profile

`u2_list_i64.eri` freshly runs canonical aggregate verification before emission,
then checks a closed version-one seven-import contract. These declarations must
have exact symbols, signatures, import kind, conservative effect mask 63 and
version 1. The profile interprets one explicitly supplied empty aggregate TypeId
as an opaque List-i64 carrier. It is NOT a generally constructible aggregate or
universal managed type encoding. All aggregate make/get/set operations refuse.
Canonical i64/predicate constants, integer comparisons, direct calls, typed
jumps/branches and scalar returns are admitted. Unsupported opcodes refuse.

The closed adapters are empty, copy, append, replace, count, get, and collect.
List inputs/results use the opaque carrier; elements/index/count use i64.
Mutation adapters produce a new logical List SSA result; the owned boxed ABI is
retained behind native adapters. This is distinct from the general managed
registry, and is not production frontend integration or arbitrary List support.

Bounds fixed before executing the candidate: up to 64 blocks and 512 edges, no entry parameters, one i64
return, <=128 SSA values and <=256 instructions, seven exact declarations.
Existing U1 owner/work/traffic/cancellation limits remain binding. No limit was
raised. The deliberately simple last-use emitter scans later operand uses per
value/instruction: O(V*N^2*P) bounded work and O(V) target frame storage, not a
claimed scalable optimizer. Native root storage is one eight-byte word per SSA
value, plus scope/scalar-return words and one eight-byte edge-capture word per
SSA value, with SysV alignment. This profile
must be redesigned/measured before lifting these bounds.

## Native execution and root lifetime

The Eristavi-written emitter walks the canonical per-block instruction chain.
It publishes zeroed class-1 words through evn_bind_roots before managed calls.
Every boxed result is stored before a subsequent possible collection; the result
of a copy is published before append/indexed replacement can allocate. After
an instruction, words with no later canonical operand use are cleared. Values
still used later survive explicit collect calls. The scope is released before
returning the unboxed scalar, preventing abandoned stack-root access.

The target adapter requires the owned Linux/System-V x86-64 graph
runtime and its descriptor table (Int index 1, Bool index 3, List-of-Int index 7).
Native entry checks these descriptor kinds and the List element relationship
before allocating or registering roots. The harness independently mutates the
List descriptor to confirm rejection. This is a closed test/runtime
boundary, not arbitrary foreign-runtime compatibility or a public ABI promise.

## Evidence and boundaries

The focused native test independently checks original element 10, modified
entries 20, original count 1 and modified count 2 after explicit collections.
It audits static native executables and confirms full graph/Text/failure/handler
reclamation through the existing independently checked harness. Negative List
index and injected first graph-allocation refusal terminate; malformed import
version/effects and malformed aggregate construction emit no native assembly.

This does NOT close U2: general managed types, arbitrary CFG profiles/recursion,
managed local promotion, nested/Unicode/identity adapters, checked resource/failure
integration, general fault reports and all allocation-failure boundaries,
independent machine-root proof and physical/latency qualification remain open.
The generated path executes actual canonical UIR calls through owned runtime
helpers; it does not route through the old source lowering. GNU as/ld and the
bootstrap compiler remain test/build tools. Keep PR #111 draft and #74 open.


## 5 November experimental per-instruction retirement (unqualified)

A new development candidate on draft PR #111 uses `ssa.liveAfter` after each
nonterminal, non-branch instruction to clear selected List SSA root words in
multi-block functions, after a boxed result is published and after its last
operand use. The verified successor-edge root retirement still runs after
parallel edge moves. It does not change single-block last-use behavior or
the >32-selected-List conservative fallback.

The candidate also adds after-invoke publication refusal tests and a physical
native loop check that an obsolete List root word is zero before the following
forced collector, while a live loop-carried snapshot remains rooted. These
new assertions are provisional until exact-head focused CI is green.
No performance, collector-efficiency, RSS or general managed-root acceptance
claim follows merely from this source change. The prior historical evidence
in this file remains evidence for the older edge-only implementation.

## CFG, registry and fault-origin follow-up

`emitManaged` freshly verifies the complete managed registry/structural graph,
then requires an exact ordinary List descriptor with structural i64 elements.
Foreign, unsupported-version or wrong-family descriptors refuse before assembly.
The structural carrier remains the selected private legal representation; this
is not a new generic canonical managed type encoding. The lower-level `emit`
entry retains its explicit closed-carrier contract for compatibility.

Each canonical block has its own machine label. Every edge captures its entire
source tuple before destination stores, then jumps to its target. This handles
cyclic parallel moves and backedges without allocating or collecting while edge
scratch is live. No global instruction-ID execution order is assumed.

For multi-block functions with at most **32 selected List-carrier SSA values**,
the emitted edge first captures the complete outgoing tuple and installs all
destination parameters without any allocating call. It then reads independently
recomputed, revision-bound canonical SSA live-in facts for that particular
successor and emits root-word clears for List-carrier ValueIds that cannot be
used on that successor. A backedge therefore does not retain the old List
snapshots of previous iterations solely because they appeared earlier in the
same function. The published root table and class/slot offsets do not change.
Scalar boxed values and List values that die *within* a block remain
conservatively rooted until the next edge or scope exit. The established
128-value native profile remains available: more than 32 selected List values
fall back to the former conservative all-block retention behavior.

The plan is constructed using a private frozen non-fallible contract registry,
then independently reverified against the exact canonical Function/revision
before emitting machine text. It is closed after emission or on reported errors.
The tracked carrier is legal only under the separately verified closed
List-of-i64 managed descriptor; there is no general managed-type encoding.
This is **successor-edge List root retirement**, NOT full per-instruction
CFG/SSA exact release, not complete machine root-map validation, and not
general Text/identity/cleanup root acceptance.
The independent Python frame oracle checks the known fixture's class count,
zeroed nonoverlapping root offsets and SysV-aligned root/scope/edge capacity.
The existing single-block last-use clearing remains unchanged.

List get/replace perform a checked index preflight through the owned exact
object lookup. A bounds fault prints immutable logical source name, line and
column using the existing EINTR/partial-write-safe writer, then takes the
existing terminal bounds path. Synthetic locations follow their primary origin
chain or receive an explicit synthetic LocId label. No source text is reopened
or incorrectly attached from a different revision. This covers List bounds
origins, not every possible target fault or diagnostic origin chain.

Native probes cover growing a loop-carried List while an original snapshot
retains count 1, a cyclic swap returning 20/10, explicit GC and full reclamation.
Wrong managed family/version, malformed CFG edge, runtime descriptor mismatch,
source bounds origin and independent root-frame layout are tested separately.
No full U2 qualification, production switch or milestone closure follows.
