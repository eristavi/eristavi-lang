# U1a i64 integer operations — isolated implementation slice

Checkpoint: 2026-10-30. Authority: `docs/architecture/Eristavi-UIR-U1-Contract-2026-10-29.md` §§3–4, 7–10, 13–15; `INTEGER_REMAINDER.md`; `HANDOVER.md`.

## Private operation registry

Existing `i.add.overflow.signed` op 3 is unchanged. New internal operation IDs (not a frozen serialized format):

| ID | Operation | Results | Attributes |
| --- | --- | --- | --- |
| 15 | `i64.add.wrap` | i64 | none |
| 16 | `i64.sub.wrap` | i64 | none |
| 17 | `i64.mul.wrap` | i64 | none |
| 18 | `i64.cmp` | pred | relation 1–10 |
| 19 | `i64.sub.overflow.signed` | i64, pred | signed by op ID |
| 20 | `i64.mul.overflow.signed` | i64, pred | signed by op ID |
| 21 | `i64.add.overflow.unsigned` | i64, pred | unsigned by op ID |
| 22 | `i64.sub.overflow.unsigned` | i64, pred | unsigned by op ID |
| 23 | `i64.mul.overflow.unsigned` | i64, pred | unsigned by op ID |

All require exactly two i64 SSA operands and a source location; absent attributes/payloads are zero. Compare relation: 1 eq, 2 ne, 3 slt, 4 sle, 5 sgt, 6 sge, 7 ult, 8 ule, 9 ugt, 10 uge. Builder and independent verifier both reject invalid relation codes and malformed operands, results and other attributes.

Operations use exact 64-bit two's-complement bit vectors. Wrapping arithmetic yields low 64 bits. For signed overflow, compare the **unbounded signed** mathematical result to the signed 64-bit range. For unsigned overflow, interpret both operands as unsigned 64-bit bit patterns and compare the **unbounded unsigned** result to [0, 2^64-1]. Even when overflow is true, the wrapped value remains defined; no poison, silent trap, or automatic source Eristavi checked arithmetic is introduced. Compared unsigned relations use bit-pattern order, not signed host order.

## Evidence and boundaries

Two new C-bootstrap-compiled U1a probe functions are independently evaluated before and after mandatory SSA promotion: `i64-arithmetic` (all nine new op IDs plus legacy signed add/overflow, with ten comparison modes) and `i64-merge` (a mutable i64 cell, diamond merge and post-merge operations). Independent Python cases cover 11 x 11 signed boundary pairs, and both conditional paths for the merge fixture. All original differential/trap/fault traces remain enforced. Malformed verifier coverage includes invalid wrap payload, invalid comparison relation, wrong operand type, wrong result type, and an invalid instruction in an unreachable block.

This is a candidate *isolated IR construction/verification* slice, not a production native-code lowering path. It makes no performance claim and changes no source language, production frontend, C/owned runtime, instruction layout, ownership budgets, machine ABI or backend. The existing signed `i.add.overflow` operation remains ID 3. **Trapping division/remainder**, their own source fault provenance and runtime reporting adapters, strict binary64, calls and switches remain separate reviewed implementation gates. No shortcut via the host's undefined signed-overflow behavior is permitted.

CI and completed-batch qualification must be reported only from the exact committed revision; the initial patch's static checks are not a claim that compiled tests passed.
## CI-discovered integration regression

The initial candidate test run exposed a lingering numeric-cell category comparison in U1a SSA promotion. The corrected slice replaces `instruction(state,cursor,0) >= 10` with `ops.isCell(...)` and adds a guard for that missed pattern. The `i64-merge` fixture and shape requirements remain unchanged. CI and completed-batch qualification must be evaluated on the corrected head.
