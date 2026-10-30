# U1b narrow type and constant integration candidate

2026-10-30. This branch stacks i8/i16/i32 type identity and exact bit-pattern constants from original PR #81 at `ab3d9fda0a1f713a8eb2e2533c85de999dca6cfa` and PR #82 at `e842f3b1ee75800a74c4f25726e8b35146974247` **on top of** combined call/switch candidate PR #83 `ef441fe6dc6d0a8d0f05fdf45efdb9290771b240`.

## Reconciliation
- All original U1a call/switch operations 34/35 and U1b narrow constant op 36 are recognized. The narrow constant has a required type attribute i8/i16/i32 and exact unsigned-width bound, with a single result of that width.
- Owned type registry includes primitive i8/i16/i32 along with existing pred/i64/f64 and FunctionId declarations.
- The builder's op36 payload/attribute validation is performed before dynamic call result reservation; verifier keeps both signature-derived call result types and exact typed narrow constants. The switch's shared successor schema remains unchanged.
- The independent oracle/differential suites include all call/switch and narrow fixtures: 35 promotion snapshots total, with the original before/after SSA expectations and malformed-IR checks preserved. Narrow signed high-bit views, narrow type mismatch, narrow constant overflow/type/width and unreachable malformed instruction tests remain mandatory.
- Conflicting test expectations and fixture registration were combined, not silently overwritten.
- The original PR #82 commit is recorded as an additional Git parent; it includes the entire PR #81 history.

## Qualification gates
This is **not yet a qualified integrated U1b release**. PR #81 and #82 each have normal four-platform CI but **not** completed-batch qualification on this combined tree. The combined U1a base PR #83 must pass regular CI and full qualification independently; then this branch must be retargeted to the resulting tested main, rebuilt/requalified on the final revision if the Git tree differs. Merge only after four-platform CI and completed-batch bootstrap/offline + owned integration qualification on exact final head.

Not covered: width-specific arithmetic/overflow/div/rem, immutable aggregates, managed Text/List/identity, checked failures, deterministic resources, or U3 frontend/native integration. They require independent verified slices and compatibility gates. No production compiler or frozen Eristavi source language modified.
