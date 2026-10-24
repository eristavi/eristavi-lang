# Compiler Tests

Run the full suite from the repository root:

```text
python -m unittest discover -s tests -v
```

The current suite contains **245 tests**.

Coverage is split across frontend/reference semantics and multiple compiler/runtime layers, including:

- lexical, type, scope/no-shadowing and control-flow semantics;
- functions, recursion and result inference;
- compiler-inferred generic relationships;
- Lists, ordinary values, maybe/none and identity;
- checked failures and deterministic resources;
- project modules/imports/visibility/cycles;
- generated-C native execution;
- Unicode 17 Text views and grapheme behavior;
- serialized interfaces/objects and source-independent linkage;
- reusable inferred-generic object specialization after source removal;
- direct x86-64 functions/ABI, Float/Text, aggregates, Lists, maybe/identity, checked errors and resources;
- direct x86-64 Unicode Text views;
- direct GC root-frame and heap-reachability stress cases;
- ARM64 scalar/runtime/checked-error/resource assembly generation and AArch64 cross-assembly;
- content/interface-digest keyed module caching;
- Universal-IR verification/optimization analysis groundwork;
- ES2020 JavaScript backend execution for the current scalar/function slice;
- WebAssembly-text backend contracts for the current scalar/function slice.

CI currently runs the suite on:

- GCC / Ubuntu / `-O2`;
- Clang / Ubuntu / `-O2`;
- Clang / macOS / `-O2`.

Platform-specific execution tests skip where the requested ABI/host is unavailable. Direct x86-64 behavior executes on x86-64 Linux; expanded ARM64 code is cross-assembled in the current hosted matrix.

Tests should continue to grow around frozen semantics, cross-backend equivalence, runtime conformance and failure-mode regression rather than speculative source syntax.
