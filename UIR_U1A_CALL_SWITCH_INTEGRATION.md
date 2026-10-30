# U1a calls + sparse switches — integrated candidate

2026-10-30. This branch reconciles original [PR #78](https://github.com/eristavi/eristavi-lang/pull/78) at `6bd61476970c8d0c762450c97c3d249f1bce021c` and [PR #79](https://github.com/eristavi/eristavi-lang/pull/79) at `c19d19caeaf792d33553b3780920852ef01e5c10`, on main base `2243cf8823b61a5b07a239ff51e8ac748ba2caf9`. Their Git histories are preserved as additional merge parents.

## Reconciliation
Both branches independently modified `src/compiler/u1_builder.eri`, `src/compiler/u1_verify.eri`, `src/compiler/u1_ops.eri`, and `tests/test_u1_foundation.py`. Their builder and verifier line edits are disjoint and both are retained. Exactly three direct text conflicts were resolved:
- The op registry accepts both op 34 `call.direct` and op 35 `switch.i64`.
- `ops.operands` keeps signature-dependent calls and one-selector switches, with switch still a terminator while calls are nonterminating observable effects.
- The foundation probe expects known operations through 35.

Unique module declarations, call signature tests, sparse switch edge data/successors, dominance/SSA promotion, and all original malformed/differential fixtures were copied unchanged. No production compiler, source syntax, ABI or runtime path is replaced.

## Verification gates
This is a **candidate until exact combined-revision CI and full qualification pass**. Parent PR #78 and #79 independent green results are not evidence for the combined tree. The current U1a direct-call implementation covers typed declarations and independent call verification; executable multi-function calls, recursive call effect/SCC derivation and versioned import trust remain separate issue #71. Switch profile covers sparse i64 case routing; U2 managed/failure semantics and U1b widths are separate.

Run four-platform normal CI; then completed-batch qualification: three bootstrap repeatable/offline + owned integration, excluding the explicitly unqualified experimental full owned-compiler self-build. Before merging compare final tested Git tree to resulting main tree, update handover with final evidence. Avoid unrelated PR merges.
