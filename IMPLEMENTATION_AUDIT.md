# Eristavi pre-0.1 Implementation Audit

> **Audit date: 2026-10-24**
>
> **Scope:** frozen pre-0.1 language contract versus the current Python bootstrap compiler, AST execution runtime, project loader, typed Eristavi IR, C/native backend, Unicode support and cross-toolchain CI.

## 1. Executive result

Eristavi has moved beyond an interpreter/bootstrap experiment into a broad executable compiler implementation.

At this audit point:

- the source-language/frontend contract remains frozen and no major semantic decision had to be reopened;
- the frontend and bootstrap runtime cover the principal pre-0.1 language surface;
- the typed IR/C backend now compiles the major value, collection, optional, identity, checked-error, resource, module and inferred-generic slices that were previously frontend-only;
- Unicode behavior is pinned to Unicode **17.0.0** rather than inherited from the host Python Unicode database;
- explicit Text views are implemented in the frontend/bootstrap runtime;
- the verified suite contains **144 tests**;
- the native suite passes under GCC and Clang on Ubuntu and Clang on macOS, with `-O2` enabled;
- the current native route remains Eristavi IR → C11 → system C compiler, not a direct machine-code backend.

The implementation continues to support the central architecture rule:

> Target platforms implement Eristavi semantics; they do not redefine them.

## 2. Frontend and bootstrap runtime

The implemented frontend/runtime surface includes:

- the frozen 28-keyword lexical vocabulary;
- SPACE/TAB/LF/CR whitespace rules, BOM handling, line comments and nested block comments;
- decimal/binary/hex Int literals and decimal binary64 Float literals;
- Text literals and the frozen escape vocabulary;
- Unicode 17 XID identifiers with NFC normalization;
- `let`, transitive `fixed`, annotations, assignment and lexical no-shadowing;
- signed checked 64-bit `Int`, `Float`, `Bool`, `Text`, `maybe`, Lists, ordinary user-defined values and managed identities;
- `if`, `else`, `while`, stable `for`, functions, recursion and completion analysis;
- compiler-inferred generic relationships and concrete specialization;
- structural value equality and identity equality;
- checked errors, typed/catch-all handling and `try` propagation;
- deterministic `with` resource ownership and cleanup-failure composition;
- source-root modules/imports, aliases, public/private declarations and circular-import diagnostics.

### Unicode Text views

The previously audited Text-view gap is now closed in the frontend/bootstrap runtime:

```eri
text.characters
text.scalars
text.bytes
```

The compiler uses internal semantic view types rather than inventing public `Character`, `Scalar`, or `Byte` source types.

The pre-0.1 clarification is:

- `text.characters[i]` returns `Text` containing one Unicode extended grapheme cluster;
- `text.scalars[i]` returns `Text` containing one Unicode scalar;
- `text.bytes[i]` returns `Int` in `0..255`;
- all three views expose `.count`;
- indexes are zero-based `Int` values with checked bounds;
- views are read-only;
- direct `text[i]` remains invalid.

These rules are recorded in `TEXT_VIEWS.md`.

## 3. Unicode reproducibility

The previous host-Unicode dependency has been removed from the bootstrap lexical/text-view path.

The toolchain now pins Unicode **17.0.0** using pinned `unicodedata2` data and a pinned Unicode-aware regex implementation for XID and extended grapheme clusters.

Tests cover:

- Unicode version pinning;
- XID identifier behavior;
- NFC identifier identity;
- extended grapheme clusters, including combining sequences and ZWJ emoji;
- scalar versus UTF-8 byte views.

This closes the original Unicode-version audit gap for the Python bootstrap. A future non-Python runtime/backend must carry equivalent pinned tables/logic rather than delegating to platform-specific character APIs.

## 4. Typed IR and C/native backend

The typed IR remains source-close but now represents substantially more than the original scalar/control subset.

Native executable tests cover:

- `Int`, `Float`, `Bool`, and `Text`;
- checked Int arithmetic and division/remainder faults;
- Text concatenation and content equality;
- functions, recursion, conditions and loops;
- Lists, checked indexing, mutation, equality, value copying and stable iteration;
- ordinary user-defined values, nested fields, copying and structural equality;
- `maybe` / `none` and narrowed optional values;
- managed identities, aliasing and identity equality;
- checked errors, typed/catch-all handlers and propagation;
- inferred-generic concrete specializations;
- imported public functions/types and aliases;
- deterministic `std.files` read/write resources and cleanup unwinding.

This means the old audit statement that Lists, values, maybe, errors, identity, resources, modules and generic specializations were still backend gaps is no longer correct.

## 5. Resource semantics

Both bootstrap execution and compiled execution now test deterministic resource behavior.

Confirmed behavior includes:

- `with` owns a resource and cleanup occurs on normal exit and return;
- nested resources unwind in reverse order;
- file open/read/write failures remain checked failures;
- if a body failure is already propagating, it remains primary when cleanup also fails;
- cleanup failure is not silently discarded.

No manual lifetime/free syntax was introduced.

## 6. Float conformance status

Float conformance has materially improved.

Compiled tests now cover:

- NaN equality behavior;
- positive/negative infinity from IEEE division;
- signed zero preservation;
- smallest subnormal survival rather than flush-to-zero;
- overflow to infinity.

CI now runs the full 144-test suite under:

- GCC on Ubuntu;
- Clang on Ubuntu;
- Clang on macOS;

with native compilation at `-O2`.

All three configurations pass.

This is strong bootstrap evidence against obvious host/compiler leakage, but it is not yet a proof across all CPUs, compiler versions and floating-point environments. ARM/RISC-V and additional optimization/toolchain configurations remain future conformance work.

## 7. Test status

The verified suite contains:

```text
144 tests
```

The suite includes positive execution, negative semantic diagnostics, interpreter/runtime behavior and real generated-C/native execution.

The CI matrix executes that suite on three host/compiler configurations, so the current matrix represents **432 successful test executions per full run**.

The current automated commands include:

```text
python -m compileall -q compiler tests
python -m unittest discover -s tests -v
```

The native builder honors both `CC` and `CFLAGS`, allowing conformance runs to vary host compiler and optimization mode without changing Eristavi source.

## 8. Remaining implementation gaps

The remaining gaps are now narrower and principally architectural/engineering rather than source-language design questions.

### A. Compiled Unicode Text views

`characters`, `scalars`, and `bytes` are implemented in the frontend/bootstrap runtime, but are not yet lowered through the C/native backend.

`bytes` and scalar traversal are straightforward runtime engineering. Extended grapheme clusters require a pinned Unicode segmentation implementation in the compiled runtime; Eristavi must not silently substitute locale/platform character APIs.

### B. Direct native backend

There is still no direct ARM64, x86-64 or RISC-V machine-code backend. The current native path deliberately uses generated C.

The eventual first direct backend should consume a lower-level form of Eristavi's own IR rather than making C semantics part of the language contract.

### C. Stable compiled module interfaces

The Python bootstrap project compiler still shares live analyzer/module objects between imported modules.

A production compiler needs serialized interface metadata containing public types, function contracts, checked errors and generic specialization information so importers can type-check without another source module's live Python analyzer state.

### D. Runtime/standard-library breadth

The implemented standard surface is intentionally small, principally `output` and `std.files` plus intrinsic language/runtime operations.

JSON, networking, time, process control and broader library domains remain future library work, not missing grammar.

### E. Broader platform conformance

The C path is now exercised on Linux/macOS and GCC/Clang, but Windows/MSVC, ARM64 and RISC-V environments are not yet part of the automated matrix.

## 9. Deliberately postponed — not defects

The audit does not classify these as pre-0.1 implementation defects:

- explicit generic syntax/constraints;
- traits/interfaces;
- pattern matching;
- async/await and advanced concurrency;
- reflection/macros;
- identity-to-value snapshot API;
- advanced resource transfer/borrowing/lifetime syntax;
- package registry/version/lockfile design;
- advanced garbage collectors;
- stable portable bytecode/JIT;
- self-hosting;
- multiple direct native CPU backends.

## 10. Quality findings

The implementation process has caught several host-language leakage risks and corrected them:

- function parameters are mutable local values rather than implicitly fixed;
- generated Text output uses real newlines;
- compiled Text equality is content-based rather than pointer-based;
- Unicode source identifiers are mangled to portable ASCII C identifiers;
- Text ordering is rejected because it is not part of the frozen contract;
- `%` remains Int-only;
- Unicode identifier/grapheme behavior is pinned rather than host-dependent;
- native tests now run with multiple host compilers and optimization enabled.

The new Text-view implementation also avoided introducing public one-character/byte types that were not present in the frozen language.

## 11. Audit conclusion

The implementation has now closed most of the gaps identified by the previous audit.

The most important change in project status is that the C/native backend is no longer merely a scalar prototype: it executes tests across Lists, values, optionals, identities, checked errors, resources, modules and inferred-generic specializations.

The frontend/bootstrap runtime is now also Unicode-version-pinned and implements the explicit Text-view model.

The next engineering priorities are therefore:

1. implement compiled Unicode Text views with a pinned runtime segmentation strategy;
2. introduce stable compiled module/interface metadata;
3. continue cross-platform/backend conformance work;
4. define the lower-level universal IR needed by the first direct CPU backend;
5. implement the first direct native backend only after those boundaries are stable.

> **Audit verdict:** Eristavi is a functioning pre-0.1 bootstrap compiler with a frozen language surface, broad frontend/runtime coverage, a substantially capable typed IR/C native path, pinned Unicode semantics, and multi-toolchain conformance testing. The remaining work is concentrated in runtime portability, compiled Text-view parity, module artifacts and the eventual direct native backend—not in redesigning the language.
