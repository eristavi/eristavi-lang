# Compiler Tests

Run the full suite from the repository root:

```text
python -m unittest discover -s tests -v
```

The current suite contains **262 tests**.

Coverage spans frontend/reference semantics and multiple compiler/runtime layers, including:

- lexical/type/scope/control-flow semantics;
- functions, recursion and result inference;
- inferred generic relationships;
- Lists, ordinary values, maybe/none and identity;
- checked failures and deterministic resources;
- project modules/imports/visibility/cycles;
- generated-C native execution;
- Unicode 17 Text views and grapheme behavior;
- the complete official Unicode-17 `GraphemeBreakTest` fixture supplied to CI from an immutable revision;
- serialized interfaces/objects and source-independent linkage;
- reusable inferred-generic object specialization after source removal;
- direct x86-64 functions/ABI, Float/Text/Text views, aggregates, Lists, maybe/identity, checked errors and resources;
- x86-64 typed GC descriptors, liveness-aware roots, spill-slot planning and heap-reachability stress cases;
- x86-64 physical-register-allocation regressions covering interference, GP/XMM register classes, call/GC boundaries, complex clobber-region operands and emitted register-resident scalar chains;
- native ARM64 Text/aggregate/maybe/identity/error/resource execution plus cross-assembly checks;
- content/interface-digest keyed module caching;
- Universal-IR verification, optimization, CFG liveness, interference and escape analysis;
- ES2020 JavaScript execution through ordinary-value/List/maybe/identity semantics;
- WebAssembly-text scalar/function/control contracts and explicit Text `externref` host ABI.

CI currently runs the suite on:

- GCC / x86-64 Ubuntu / `-O2`;
- Clang / x86-64 Ubuntu / `-O2`;
- Clang / ARM64 Ubuntu / `-O2`;
- Clang / ARM64 macOS / `-O2`.

Architecture-specific executable tests run on their matching Linux host. On x86-64 Linux the ARM-native cases are skipped; on ARM64 Linux they execute.

Tests should continue to grow around frozen semantics, cross-backend equivalence, runtime conformance and failure-mode regression rather than speculative source syntax.
