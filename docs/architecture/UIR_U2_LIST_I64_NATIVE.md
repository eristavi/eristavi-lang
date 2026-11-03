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
Only canonical i64 constants, direct calls and a scalar return are admitted.

The closed adapters are empty, copy, append, replace, count, get, and collect.
List inputs/results use the opaque carrier; elements/index/count use i64.
Mutation adapters produce a new logical List SSA result; the owned boxed ABI is
retained behind native adapters. This is distinct from the general managed
registry, and is not production frontend integration or arbitrary List support.

Bounds fixed before executing the candidate: one block, no parameters, one i64
return, <=128 SSA values and <=256 instructions, seven exact declarations.
Existing U1 owner/work/traffic/cancellation limits remain binding. No limit was
raised. The deliberately simple last-use emitter scans later operand uses per
value/instruction: O(V*N^2*P) bounded work and O(V) target frame storage, not a
claimed scalable optimizer. Native root storage is one eight-byte word per SSA
value, plus scope and scalar-return scratch and SysV alignment. This profile
must be redesigned/measured before lifting these bounds.

## Native execution and root lifetime

The Eristavi-written emitter walks the canonical per-block instruction chain.
It publishes zeroed class-1 words through evn_bind_roots before managed calls.
Every boxed result is stored before a subsequent possible collection; the result
of a copy is published before append/indexed replacement can allocate. After
an instruction, words with no later canonical operand use are cleared. Values
still used later survive explicit collect calls. The scope is released before
returning the unboxed scalar, preventing abandoned stack-root access.

The target adapter currently requires the owned Linux/System-V x86-64 graph
runtime and its existing descriptor table (Int index 1, List-of-Int index 7).
The native harness supplies that exact table. This is a closed test/runtime
boundary, not arbitrary foreign-runtime compatibility or a public ABI promise.

## Evidence and boundaries

The focused native test independently checks original element 10, modified
entries 20, original count 1 and modified count 2 after explicit collections.
It audits static native executables and confirms full graph/Text/failure/handler
reclamation through the existing independently checked harness. Negative List
index and injected first graph-allocation refusal terminate; malformed import
version/effects and malformed aggregate construction emit no native assembly.

This does NOT close U2: multi-block managed types/phis/loops/recursion, managed
local promotion, nested/Unicode/identity adapters, checked resource/failure
integration, exact source fault reports, all allocation-failure boundaries,
independent machine-root proof and physical/latency qualification remain open.
The generated path executes actual canonical UIR calls through owned runtime
helpers; it does not route through the old source lowering. GNU as/ld and the
bootstrap compiler remain test/build tools. Keep PR #111 draft and #74 open.
