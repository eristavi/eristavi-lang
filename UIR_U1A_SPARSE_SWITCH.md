# U1a sparse integer switch and common CFG successor schema

Checkpoint 2026-10-30. Candidate, not qualified or merged. Governing source: `docs/architecture/Eristavi-UIR-U1-Contract-2026-10-29.md` §§6,8,9,13 and frozen Eristavi semantics.

## Internal IR and canonical cases

Private op 35 `switch.i64` consumes one i64 selector, produces no SSA result, and terminates a block. Its payload indexes a separate owned switch header (firstCase, count, defaultEdge). Cases are a dense **count-sized** array of (i64 bit pattern, EdgeId) with strictly increasing **unsigned 64-bit** bit order. There is one mandatory default and zero or more cases. Unsigned order compares signed words without overflow or floating conversion. Neither builder nor verifier allocates a table based on the largest case integer.

The `build.EdgeId` is nominal/function-owned. Each switch arm and default receives a *distinct ordinary typed edge record*, even if two edges target the same block. Every edge has simultaneously transferred typed block parameters. Orphan, duplicate-owner, missing-default, malformed pool and invalid/unsorted cases are rejected. Builder validates count, selector, case order and typed owner before publishing terminators. Completed functions freeze both new case stores.

`compiler.u1_successors` is the common schema used by independent structural/SSA verifier and SSA promoter, including existing jump and branch. It enumerates all case edges then the default. `ops.inlineEdges` remains limited to the original jump/branch inline attribute slots and is not used to undercount a switch. The independent verifier checks case pools globally before block traversal, including unreachable records, then claims every header and edge. Promotion rebuilds sparse case tables and remaps successor edges transactionally while preserving original LocIds, SSA values and simultaneous arguments.

## Independent tests

A separate Python reference evaluator executes the new switch independently of builder, verifier or promoter and checks original/promoted outcomes. Fixtures include three sparse values (zero, signed MAX, signed MIN), a default case, an initialized i64 cell with four definitions and a join, and multiple distinct edges targeting the **same** successor with different value arguments. The verifier protocol rejects duplicate case bits, invalid case/default edges, invalid header/extra field and wrong selector type, and requires valid restoration.

## Explicit limits

This slice is only i64; U1b other widths remain separate. No U2 variant refinement, source syntax extension, native machine switch selection or public serialized case format is provided. No jump-table allocation by sparse numeric span is allowed. Tests/physical resource measurements and compiled native adapter conformance are independent gates. No production compiler source pipeline is replaced. No full experimental owned self-build is attempted.

Before merging this PR, require exact-head CI success on Linux GCC/Clang, ARM64 and macOS; completed-batch full qualification; and a verified clean integration with any concurrently merged U1a call/origin code. Record the final merge and source tree in `HANDOVER.md`.
