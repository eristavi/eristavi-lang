# Isolated U1a strict binary64 operation and oracle slice

Checkpoint: 2026-10-30. Governing contracts: `FLOAT.md`, `LANGUAGE_SEMANTICS.md`, `docs/architecture/Eristavi-UIR-U1-Contract-2026-10-29.md` §§4–7 and §13, and `CI_QUALIFICATION.md`. This is **not** a declaration of complete U1a or runtime/backend floating-environment certification.

## Private scalar operations

Internal U1a operation IDs (not stable serialization):
- 28 `f.add`, 29 `f.sub`, 30 `f.mul`, 31 `f.div`: two f64 SSA operands → one f64 SSA value, zero payload and extra attribute.
- 32 `f.neg`: one f64 → one f64, zero payload and extra attribute.
- 33 `f.cmp`: two f64 → one pred, required relation payload 1 eq, 2 ne, 3 lt, 4 le, 5 gt, 6 ge; other attributes zero.

They are type-checked in the builder and **independent** verifier, including after mutation and in unreachable blocks. The existing private cell class remains **only** op IDs 10/11/12, and independent SSA promotion reconstructs the new pure operations without assuming all canonical operation IDs are below 10.

The U1 scalar contract prescribes a strict **binary64 round-to-nearest-ties-even operation at every arithmetic step**, negative zero, infinities, gradual underflow, exact unordered NaN comparison semantics, no integer-style float divide-by-zero trap, and no implicit arithmetic contraction/reassociation. NaN payload and signaling flags are not core-U1 observations. In the reference evaluator, a NaN arithmetic result is canonicalized to quiet NaN for comparison; sign flipping for `f.neg` preserves raw operand sign/zero, and signed zero remains visible.

## Independent, differential evidence

The test harness `tests/test_u1_promotion.py` now provides an **exact rational binary64 expected-result oracle** separate from its host-Float reference executor:
- It decodes input bit patterns into integer/Fraction significands and exponents, handles infinities and NaNs by class, and rounds finite arithmetic with integer quotient/remainder and ties-to-even at the normal/subnormal boundary, including zero and overflow.
- It independently compares finite rationals, signed infinities and NaN unorderedness for six relations.
- The `float-arithmetic` fixture uses all six new operation IDs and comparison modes across a 15×15 grid of +0/-0, subnormals, normal boundaries, ±1, adjacent representables, maximum finites, infinities and NaN.
- The `float-merge` fixture checks a mutable f64 cell through a diamond before/after canonical SSA promotion; it requires exactly one inserted block parameter and two edge arguments.
- The `float-nonfma` fixture computes multiply followed by add on the classic `(1+2^-27)(1-2^-27)-1` counterexample; its independent expected result is rounded zero, not the nonzero fused result.
- The malformed verifier protocol rejects wrong Float operand/result type, invalid payload, invalid comparison mode, global operand arity and an invalid Float instruction in an unreachable block. Repaired records must verify again.

The Python executor uses ordinary host binary64 Float instructions; this is **not** proof that an arbitrary native target inherits the desired floating environment. The exact-rational oracle is authoritative for these tested input families. The independent verifier and transactional promoter do not perform floating arithmetic themselves.

## Remaining U1a and release requirements

**Not yet done in this slice:** native x86-64/ARM64 execution adapter for the redesigned U1 Float operations, explicit host rounding/exception/denormal controls and verification at foreign call boundaries, complete source provenance chain, direct calls/effects, sparse multiway switches, and completed-batch physical resource measurements. Those are separate prerequisites before calling the *whole U1a profile* finished.

The code-bearing PR needs four-platform ordinary CI and full completed-batch `qualification` on its exact final head before a merge. The experimental owned compiler B→C/C→D full self-build remains separate, unqualified and skipped by default.
