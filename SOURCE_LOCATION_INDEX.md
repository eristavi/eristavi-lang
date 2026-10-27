# Indexed compiler source locations

PR #39 passed CI #383 and owned integration before merging. This batch targets
frontend work, preserving the frozen language, diagnostic coordinates and public
value ABI.

`semantic_model.at` previously restarted a linked-list walk for every AST token.
Instrumentation of the owned native compiler's analysis of 100 declarations
recorded 100 lookups and 24,850 linked-node visits. This is quadratic diagnostic
bookkeeping as a module grows, even when the program has no errors.

Each module now builds a balanced lookup tree in linear time, reusing its existing
Location records. A token ordinal selects its exact original record in logarithmic
time. The source-order chain remains intact; the owned tracer already handles the
resulting shared/cyclic identity graph. Index construction recurses only to tree
height. Unknown token indices retain the existing path/line-1/column-1 fallback.
Synthetic IR locations and malformed-IR fixtures initialize the extra private
fields explicitly. No syntax, inference rules or diagnostic policies change.

Validation covers the frozen semantic acceptance/contract/diagnostic corpus,
module behavior, typed IR execution/verifier checks and Universal IR. A new test
checks late error coordinates after 0, 63, 256 and 1,023 declarations with Unicode
preceding the error. The focused owned-native probe checks every ordinal in a
257-record tree in permuted order and negative/past-end fallback behavior.

The earlier 900-second owned self-build timeout remains unresolved. Local attempts
to emit a fresh full native compiler through the generated-C bootstrap exceeded a
separate 120-second profiling limit, including with -O2. They do not establish a
new native whole-compiler speedup or repeatability. No additional 900-second owned
rebuild was launched. The next full-completed-batch qualification must use the new
source head; earlier cached compiler assembly is invalid after these changes.

Ordinary four-platform CI and full bootstrap/owned-integration qualification are
required for this compiler change. The bootstrap runtime remains default. Further
profiling should examine semantic-fact lookup during IR lowering, which currently
also searches linked records, before scheduling another long owned rebuild.
