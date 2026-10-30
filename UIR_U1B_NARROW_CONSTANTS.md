# U1b exact-width narrow integer constants (stacked candidate)

This candidate depends on the i8/i16/i32 identity-and-SSA foundation in PR #81. It is not a claim of complete U1b, and must not be merged independently of its base.

Internal private opcode 36 `const.narrow` has no operands and one result. Its extra attribute is a narrow integer TypeId: 4 for i8, 5 for i16 or 6 for i32. The payload is an **exact unsigned W-bit pattern** in the range 0 through 2^W-1; out-of-range bits are rejected before publication rather than silently truncated. The SSA result's concrete TypeId comes from the declared width. This does not introduce a source-level numeric type, implicit widening, bitcast, or arithmetic operation.

The independent verifier checks the exact bit-width payload, type attribute and result definition in both reachable and unreachable basic blocks. The dedicated verifier fixture mutates a valid i8 payload to 256, corrupts its width to f64, corrupts the result TypeId, then restores and re-verifies. The independent evaluator interprets the signed two's complement view for test outputs, with maximum-bit-pattern constants for i8/i16/i32 all producing -1 and preserving their own types across SSA promotion.

Remaining U1b: width-specific wrap, overflow, comparison, division and remainder semantics, immutable aggregate make/get/set, and complete runtime/backends. Follow `docs/architecture/Eristavi-UIR-U1-Contract-2026-10-29.md`, `CI_QUALIFICATION.md`, and issue #73. No production compiler or source language changes in this candidate.

Four-platform CI and completed-batch qualification on the final *combined* source head are required before any merge. Do not treat a passing test on a stacked, unqualified base as release proof.
