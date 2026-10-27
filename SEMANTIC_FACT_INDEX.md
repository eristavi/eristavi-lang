# Indexed expression facts

This follow-up builds on PR #40's source-location tree. PR #40's normal CI passed;
its full qualification was still running when this branch was prepared.

Typed-IR lowering previously searched the module-wide newest-first fact chain
twice for every expression: once for its type and once for its effects. Instrumented
small `ir` runs recorded 420, 1,640 and 6,480 visited fact records for 20, 40 and
80 declarations. These counts expose quadratic scanning independently of timing.

Semantic analysis now retains a newest-first fact bucket on each indexed token
location. Facts keep both their global link and a separate token-bucket link.
Lookup still compares AST-node identity, so distinct nodes sharing a token do not
merge, and repeated analysis returns the latest matching fact. Synthetic invalid
ordinals use the original global-chain search. IR lowering retrieves the matching
fact once and uses that same record for both type and checked effects.

The corresponding indexed runs visit 20, 40 and 80 fact records. Location-tree
navigation remains logarithmic and is not included in these fact-visit counts.
This is an algorithmic measurement, not a whole-compiler speedup claim. No full
native compiler rebuild or additional expensive CI qualification was started.

Validation: semantic, typed-IR and Universal IR regressions passed (30 passed,
one cross-assembler skipped), plus an independent identity-collision/reanalysis/
synthetic-fallback test. The suite contains 407 test methods. Private Location
and Fact constructors/fixtures initialize the added fields. Frozen language,
diagnostics, type/effect relationships and public value ABI remain unchanged.

This branch must be qualified on its final source head after PR #40 is settled.
The bootstrap profile remains default; owned self-build repeatability remains
unqualified. Cached compiler assembly from earlier sources must not be reused.
