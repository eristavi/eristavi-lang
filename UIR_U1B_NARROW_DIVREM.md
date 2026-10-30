# U1b signed and unsigned narrow-width division and remainder

Checkpoint 2026-10-30. This is an **isolated draft** stacked on U1b narrow arithmetic PR #86, which depends on narrow type/constants PR #84 and U1a call/switch integration PR #83. No production source language or runtime pipeline change.

## Operations

- Private op41: `narrow.div`, op42: `narrow.rem`; exactly two operands and one result, each with identical TypeId 4 (i8), 5 (i16) or 6 (i32).
- Required payload 1 signed or 2 unsigned; extra field is width TypeId. Invalid width, mode, result/operand type, missing location and unreachable malformed operations are independently rejected.
- Exact signed quotient truncates toward zero, remainder has dividend sign, and both satisfy `a=q*b+r`. Unsigned interprets input bit patterns as 0..2^W-1 and returns the same W-bit word.
- Zero divisor terminates with `integer_zero_divisor` (trap 2). Signed MIN/-1 terminates with `integer_overflow` (trap 1) for **both div and rem**. No fake result or recoverable checked failure. The instruction's original LocId is preserved on the fault. Trap-enabled operations are tagged `ops.mayTrap`, **not** CFG terminators on successful execution.
- No implicit widening, host UB or floating-point division. No unapproved public Eristavi narrow integer types.

## Differential and negative evidence protocol

Reference execution uses exact unbounded Python integer quotient/remainder; a separate mathematical expectation uses magnitudes and `divmod()` for signed operations. 12 direct fixtures (each of 3 widths × signed/unsigned × quotient/remainder) cover the signed minimum, near-min, -1, 0, maximum, other signs and high-bit unsigned patterns. A thirteenth i8 scalar-cell diamond validates first-fault order, original locations and cell-free before/after SSA promotion, requiring precisely one inserted block parameter and two edge arguments.

`tests/test_u1_verifier.py` adds valid, wrong signedness/width/operand/result type, missing source location, restoration and dead malformed instruction tests. Original U1a and U1b tests remain mandatory. Promotion suite now expects **52 snapshots**.

## Release boundaries

At creation these claims describe **source code and tests, not execution results**. Four-platform CI and completed-batch bootstrap/offline + owned integration qualification are mandatory on the **final integrated head** after the parent PRs qualify and merge. The separate owned full compiler self-build remains unqualified and skipped.

Still missing from U1b: immutable aggregates make/get/set and by-value cycle rejection, core-only aggregate oracle/physical memory evidence. U2 managed Text/List/identity, checked continuations, cleanup/roots, and U3 frontend→typed UIR/native integration remain separate major milestones.
