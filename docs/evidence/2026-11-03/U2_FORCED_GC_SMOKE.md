# U2 forced-GC validation run

This is a validation-only PR derived from U2 development head `3f01869b50f1fba02ad02af823fb162a02cc3157`. It must never merge to `main`. The source-backed test adds explicit collector calls and asserts a rooted saved typed failure is retained, then reclaimed after release. Existing canonical UIR root-map publication is not yet established. Retain PASS/FAIL evidence by exact CI head before promoting any claim.
