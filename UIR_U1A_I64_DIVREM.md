# U1a signed and unsigned i64 division and remainder (isolated implementation)

Checkpoint 2026-10-30. Authoritative references: `docs/architecture/Eristavi-UIR-U1-Contract-2026-10-29.md` §§4,6,7,9,10,13; frozen `INTEGER_REMAINDER.md`; `CI_QUALIFICATION.md`; `HANDOVER.md`.

## Explicit, private i64 opcode registry

| Op | Meaning | Operands / results | Traps |
| --- | --- | --- | --- |
| 24 | signed i64 division | i64, i64 → i64 | zero divisor (code 2); signed MIN/-1 (code 1) |
| 25 | signed i64 remainder | i64, i64 → i64 | zero divisor (code 2); signed MIN/-1 (code 1) |
| 26 | unsigned i64 division | i64, i64 → i64 | zero divisor (code 2) |
| 27 | unsigned i64 remainder | i64, i64 → i64 | zero divisor (code 2) |

All four require a valid nonzero instruction `LocId`, zero payload and zero other attributes. IDs are local U1a implementation choices, **not** frozen serialized/public IR opcode numbers. Signedness is encoded in the opcode. The builder and independent verifier enforce exact arity/types; verifier also scans unreachable blocks for malformed records. Existing cell ops 10/11/12 and all earlier operation IDs remain unchanged.

The new `ops.mayTrap(op)` explicitly classifies a guard and these four operations as capable of a **terminal runtime-defect effect**. It does **not** classify them as CFG terminators: successful execution continues in the same basic block. No result is published if an instruction traps. These defects do not enter the checked `fails` mechanism or run user/resource cleanup, and must not be confused with a host C/CPU division fault.

For signed operands `a,b`, divide truncates mathematically toward zero and nonzero remainder takes the dividend's sign, satisfying `a = q*b+r`. Both signed MIN/-1 cases trap with integer overflow (1), even though the mathematical remainder is zero. A zero divisor traps with integer zero divisor (2) in all signed/unsigned operations. Signed MIN/-1 and divisor-zero are disjoint and their fault choice is unambiguous. Unsigned input words are interpreted as 0..2^64-1 bit patterns; outputs are recorded as the same 64 bits in i64 form. Neither evaluator nor backend may use floating division for these operations or inherit host signed-overflow UB.

## Differential and malformed IR tests

The independent Python reference executor reports `('trap',(TrapCode,LocId))` and an ordered fault trace at the operation itself before producing an output value. Its quotient/remainder implementation uses exact unbounded integers. A separate mathematical expectations oracle uses `divmod` of magnitudes for signed cases, keeping the expected-results path independent of the evaluator's remainder formula.

New fixture names: `div-signed`, `rem-signed`, `div-unsigned`, `rem-unsigned`, `div-merge`, `div-fault-order`. Each covers the deterministic 16×16 signed boundary grid. `div-merge` adds both branch choices through an initialized mutable i64 cell, expecting **exactly one** promoted block parameter and two edge arguments. `div-fault-order` places a guard first, then an **unused** signed remainder and a later unsigned division: it detects illegal deletion or fault reordering and checks exact original source LocIds. Before/after promotion execution, final values, faults and trace must agree; promotion must be transactional and cell-free.

Independent `test_u1_verifier.py` adds valid and deliberately malformed div/rem instructions: bad payload/extra, wrong operand or result type, wrong arity, missing required location, bad instruction in unreachable block, and recovery after restoration. Existing cancellation, quota, cleanup, deterministic repeated-execution, and structural/dominance tests remain in place.

## Release constraints and remaining work

This slice does **not** implement a production machine-code runtime fault adapter, source-level constant diagnosis, serialized IR compatibility, effect-aware global optimizer, call/switch contract, strict f64 arithmetic, full origin chain, or U2/U3 integration. The old production compiler and its language semantics are untouched. Later backends must validate fault category/order, reporting/LocId, and cleanup policy independently; these direct-IR differential fixtures are not a native backend correctness certificate.

Do not claim the implementation is qualified based only on source review. Require focused U1 tests, four-platform CI and the explicit `CI_QUALIFICATION.md` full completed-batch qualification on the exact final implementation head. The separate full owned-compiler self-build is an unqualified, manual experiment and must remain skipped by default.
## Initial CI verification-protocol correction

The initial PR #67 CI run (head `a29ad46`) failed one newly added test: `divrem-arity`. The independent verifier correctly detected the malformed first instruction's operand count during its global canonical operand-pool scan, before entering any block. That produces **V2 / block 0**, while the test had incorrectly asserted V2 / block 1. The fix changes only the test's expected failure block; the malformed count remains rejected, and no verifier/builder or arithmetic semantics were weakened. The test harness now also prints the probe's stdout tail upon nonzero exit for future precise diagnosis. The corrected head requires fresh CI and full qualification before merge.
