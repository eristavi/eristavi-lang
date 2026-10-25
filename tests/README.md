# Compiler Tests

Run the full suite from the repository root:

```text
python -m unittest discover -s tests -v
```

The current suite contains **359 tests**.

The scalar compiler corpus freezes 60 executable projects, with 10 additional
runtime-fault comparisons under undefined-behavior sanitization and 28 malformed
IR checks against both verifier and C emitter. Specialization cache and Float
rounding/non-contraction/fast-math checks are described in SCALAR_SPECIALIZATION.md.

The semantic corpus freezes 175 projects (67 accepted, 108 rejected). Acceptance
and inferred contracts are compared independently with Stage-0; 10 documented
diagnostic-location differences have explicit expectations. The candidate also
checks its own frontend module graph offline.

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
- x86-64 lowering-contract tests for conservative unknown operations, call clobbers and GC-safe operand consumption;
- x86-64 physical-register-allocation regressions covering interference, the `r10`/`r11` GP pool, `xmm8`/`xmm9` Float allocation, call/GC boundaries, scalar extraction and emitted register-resident chains;
- spill-frame compaction tests proving register-resident scalars omit stack slots while pinned values retain stable storage;
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

The structural/native milestone expands the executable corpus to 88 projects,
checks all 67 accepted semantic projects for lowering, and tests cleanup-failure
composition. Universal-IR tests cover CFG reachability, class/call validity and
initialization across branches. Native execution runs on matching Linux x86-64/
ARM64 hosts; cross-assembly uses Clang where available. The Linux packaging CI step
separately enforces fixed-snapshot self-build and offline executable audits. See
OFFLINE_TOOLCHAIN.md for the reference-C limitations explicitly recorded by three
projects and for bootstrap/runtime boundaries.

Native runtime lifetime tests count administrative allocations across 10,000
normal exits and checked unwinds, including nested scopes/resources, and repeat
under address/undefined sanitizers. Generated-program tests retain caller state
and typed error payloads across repeated catches. Cleanup-failure injection runs
through both the candidate C and native consumers.

Native temporary-slot tests check bounded storage at 1,000/100,000 loop iterations,
forced collection with snapshots/calls/failures/resources under address/undefined
sanitizers, and emitted root-map coverage against independently reported IR for
both ELF targets. The runtime fixture also checks scope marks and non-value words.

Heap-accounting tests validate aligned/zero-size allocations, resize bookkeeping,
category totals, retained object/Text/failure stress, overflow rejection, and a
zero test-teardown balance under sanitizers. Native integration preserves stdout
and verifies diagnostic counters alongside frequent slot collection.
