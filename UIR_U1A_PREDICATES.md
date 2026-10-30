# U1a eager predicate operations (isolated compiler slice)

Checkpoint: 2026-10-30. Stacked on PR #62's opcode-classification hardening.
Authoritative design: `docs/architecture/Eristavi-UIR-U1-Contract-2026-10-29.md` §§4, 7, 9, 13; `HANDOVER.md`.

## Implemented

Add two pure, nontrapping, terminating **eager** predicate operations to the initial isolated U1a instruction registry:

| Op | Internal name | Operands -> results | Payload / extra | CFG edges |
| --- | --- | --- | --- | --- |
| 13 | `pred.and` | `pred, pred -> pred` | zero / zero | none |
| 14 | `pred.or` | `pred, pred -> pred` | zero / zero | none |

`pred.not` remains op 4. There is no implicit integer truthiness and no source-language `and/or` lowering change. Eager operators receive **already evaluated SSA values**; source short-circuit logic must still be lowered to conditional CFG by a future frontend adapter.

`u1_ops` gives canonical types, arity, and nonterminal classification. The builder exposes typed `andPredicate` and `orPredicate` methods; independent verification validates exact operand/result types and rejects unexpected payload/attribute bits, including in unreachable blocks. Promotion preserves operations >=13 rather than mistaking them for private cells, and independently verifies its rebuilt output. Cells remain exactly op 10–12.

## Focused differential evidence protocol

The existing U1 promotion fixture gains `pred-truth` (no cells) and `pred-merge` (one initialized scalar cell with a nontrivial diamond merge). All four Boolean input combinations are evaluated against independent Python truth-table expectations **before and after** promotion; existing trap/location traces must remain identical. `pred-merge` demands exactly one inserted parameter and two edge arguments. The existing verifier protocol adds positive, malformed payload, arity, operand type, restoration and unreachable malformed-operation checks.

The opcode-classification probe now checks known IDs through 14 and rejects 15 and 16. The former test assumption `op < 10` for canonical instructions is removed; canonical means **no 10/11/12 private cells**.

## Scope limits and next gates

This adds **no** calls, switch schema, strict Float arithmetic, new integer operation, runtime ABI, changes to production frontend/driver, or executable native backend for redesigned U1. New opcodes are local implementation IDs, not a frozen serialized ABI. Current modeled capacity/work policy is unchanged. CI is the actual compiled execution verdict; a GitHub commit alone does not constitute a passing test.

Next, reconcile complete scalar operation and effect schemas, then implement signed/unsigned integer wrap/overflow/cmp/div/rem with zero divisor and **signed MIN/-1** traps for **both** div and rem, and strict f64 environment and bit behavior as separate reviewed slices. Define multiway switch case/edge side tables and call signature/effect metadata before extending those categories. Batch full qualification at the completed compiler integration boundary. Do not rerun full owned-runtime self-build by default.
