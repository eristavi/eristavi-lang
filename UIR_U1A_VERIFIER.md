# U1a foundation-profile verifier

This is the next isolated slice after foundation PR #58 (merged as
`6fb8b7bcd49418f398810ef9166acc888a35c4f5`). It validates the existing nine-operation
construction profile. It does not complete U1a or replace the production pipeline.

`src/compiler/u1_verify.eri` derives checked facts directly from the function and
independent metadata. It imports neither semantic analysis nor old Typed IR.
Builder completion, a previous report, and unchanged revision numbers cannot
bypass a new verification call. The shared operation registry specifies types;
the verifier independently checks actual records, ownership, ranges and uses.

## Validation order

| Stage | Checks in this slice |
| --- | --- |
| V0 | Ownership, immutable/complete input, table shapes and count ceilings; bounds before offset arithmetic |
| V1 | Scalar types, canonical signatures/hash chains/pools, source identity/digest encoding and entry signature context |
| V2 | All blocks including unreachable ones, unique definitions, instruction order, result/operand types, terminators, edges and argument order |
| V3 | All source spans/anchors/positive coordinates, required locations, rejection of unsupported origin records |
| V4 | Reachable SSA: use before definition, own-result use, block-parameter availability, cross-block dominance and edge-argument uses |

Malformed IR produces `InvalidIR` with category, stage, block, instruction and a
valid location when available. Resource exhaustion and cancellation retain their
separate `budget.LimitError` categories. Once admitted, verification releases its
workspace and finishes its phase on success or failure. Pre-admission cancellation
allocates no workspace. No unfinished result is returned.

Within record validation, blocks and instructions use their defined storage/list
order. Metadata scans use table order. Pool layout checks precede block scans.
The verifier rejects orphan records, duplicate claims and cyclic instruction
lists. It checks every existing typed record even in dead components; executable
dominance requirements apply only to reachable blocks. Duplicate-target edges
remain separate, with their own ordered argument ranges.

## Dominance

`src/compiler/u1_dominance.eri` implements the agreed simple Lengauer–Tarjan
algorithm: iterative DFS, semidominators, link, iterative path compression,
buckets, immediate-dominator correction and iterative tree intervals. Its graph
uses indexed block/edge arrays and explicit bounded stacks; no CFG recursion,
per-block register masks, or repeated whole-function dominator-set intersection.

Construction has the simple algorithm's O((B+E) log(max(2,B))) bound and O(B+E)
storage. Final tree intervals support O(1) use queries. The dominator component
counts array/adjacency/stack accesses against the selected
`128*(B+E+1)*ceil(log2(max(2,B)))` envelope for the reachable graph. Storage
initialization and subsequent O(1) use queries consume the global verification
quota separately. They cannot consume an ever-growing dominator-build allowance.

The structural scan separately guards its read visits with `32*(R+1)`, where R
is the checked encoded word count in this profile. Canonical signature collision
comparisons and source-identity duplicate comparisons consume additional global
work. Source duplicate checking is currently pairwise; metadata comparison cost
is not claimed to be universally linear. The page adapter also charges its
internal accesses to the existing verification/request quotas.

Scratch tables belong to the function owner. Their conservatively modeled
capacity, traffic and actual charged work use the existing ledger. Inputs remain
unchanged. `Report` contains observations and a revision, not a trusted stamp,
cached privilege or an executable-publication capability.

## Focused evidence

Reproduce the ordinary focused checks with installed project dependencies:

```sh
python3 -m unittest discover -s tests -p 'test_u1*.py' -v
```

The added tests cover 37 protocol scenarios, including corruption without a
revision increment, Int64-max instruction IDs/counts/ranges, missing backing,
foreign tables, malformed unreachable blocks, invalid source metadata, SSA
diamond/loop errors, repeated targets, simultaneous loop swaps, zero/multiple
results, raw f64 bit constants, cancellation and partial-workspace exhaustion.
The f64 checks concern typed bit payloads, not execution of Float arithmetic.

The final local focused batch passed all seven foundation/verifier tests on
2026-10-30, including both native runtime profiles. No tests were skipped on
this Linux x86-64 host. Full cross-platform PR CI remains a separate result.

A separate Python dominator-set intersection oracle checks all immediate
dominators and all block-pair dominance answers on 91 fixed/seeded graphs
(2,816 observations). Cases include all 16 two-node directed graphs, entry
cycles, parallel edges, irreducible loops and unreachable components. Bootstrap
testing additionally traverses chains of 128, 512 and 2,048 blocks.

Eristavi-emitted assembly is independently linked with the bootstrap and owned
runtimes. Both run the protocol, all 91 oracle graphs and a 128-block chain. The
owned ELF is checked for absence of a dynamic interpreter/section, undefined
imports and an executable stack. Execution uses an unusable PATH.

An initial combined native graph test, including all three deep chains, timed
out on the owned runtime at 120 seconds. A diagnostic 60-second run completed
all 91 small graphs with all 2,816 observations correct before entering the
128-block chain. A fresh 128-block owned chain completed with the correct result
in about six wall seconds on this host. Those are debugging observations, not
a matched performance benchmark or attribution to a particular runtime defect.
The routine native regression therefore covers the 128-block chain; larger
owned-chain stress remains explicitly unqualified. No timeout, memory or work
gate was raised, and the initial timeout is not relabeled as a passing test.

## Remaining boundary

The current verifier supports only operations 1–9 in `u1_ops.eri`. Direct calls,
switches, further scalar operations and strict Float execution require their
registry entries and validation tests. Source-map/content consistency, synthetic
origins and origin chains are not implemented. Nonzero reserved origin fields
are rejected, rather than interpreted as a supported extension.

The subsequent UIR_U1A_PROMOTION.md slice implements initialized scalar cells,
mandatory promotion and canonical cell rejection. Publication stamps, mutation
API/invalidation, effect/import validation, native lowering and integration
remain staged work. Safe radix storage is not packed native storage; full
physical allocation accounting and the 8 MiB qualification gate are still
unproven. The owned-runtime large-stress timeout is an open performance issue,
not evidence that the verifier or complete toolchain is qualified or optimized.

No language syntax/semantics, production compiler entry, runtime, ABI,
filesystem policy, or workflow is changed by this slice. No new compiler
self-build, 900-second test, full qualification or workflow dispatch is part of
this change. PR #57 remains separate.
