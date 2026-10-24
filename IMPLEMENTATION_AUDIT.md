# Eristavi pre-0.1 Implementation Audit

> **Audit date: 2026-10-24**
>
> **Scope:** frozen pre-0.1 language contract versus the current Python bootstrap compiler, execution runtime, project loader, typed Eristavi IR, C/native backend, Unicode support and cross-toolchain CI.

## 1. Executive result

Eristavi is now a broad working pre-0.1 bootstrap compiler rather than a parser/interpreter prototype.

At this audit point:

- the source-language/frontend contract remains frozen; no fundamental language decision had to be reopened;
- the frontend/bootstrap runtime covers the principal pre-0.1 language surface;
- the typed IR/C backend compiles Lists, values, optionals, identities, checked errors, deterministic resources, modules and inferred-generic specializations in addition to scalar/control features;
- compiled `Text` no longer inherits C-string semantics: it is represented as explicit UTF-8 bytes plus length;
- embedded NUL is preserved through compiled Text output, concatenation, equality and `std.files` round trips;
- invalid UTF-8 from `readText()` is a checked `FileError` in both bootstrap and compiled execution;
- Unicode behavior in the Python bootstrap is pinned to Unicode **17.0.0**;
- explicit `text.bytes` and `text.scalars` views now compile natively;
- `text.characters` remains fully implemented in the bootstrap runtime but is deliberately rejected by the C backend until a pinned Unicode 17 grapheme-segmentation runtime is embedded;
- the verified suite contains **155 tests**;
- all 155 tests pass with GCC and Clang on Ubuntu and Clang on macOS, with native compilation at `-O2`;
- the current native route remains Eristavi IR → C11 → system C compiler, not a direct machine-code backend.

The governing architecture rule continues to hold:

> Target platforms implement Eristavi semantics; they do not redefine them.

## 2. Frontend and bootstrap runtime

Implemented frontend/runtime behavior includes:

- the frozen 28-keyword lexical vocabulary;
- SPACE/TAB/LF/CR whitespace rules, BOM handling, line comments and nested block comments;
- decimal/binary/hex Int literals and decimal binary64 Float literals;
- Text literals and the frozen escape vocabulary;
- Unicode 17 XID identifiers with NFC normalization;
- `let`, transitive `fixed`, annotations, assignment and lexical no-shadowing;
- signed checked 64-bit `Int`, binary64-oriented `Float`, `Bool`, `Text`, `maybe`, Lists, ordinary values and managed identities;
- `if`, `else`, `while`, stable `for`, functions, recursion and completion analysis;
- compiler-inferred generic relationships and concrete specialization;
- structural value equality and identity equality;
- checked errors, typed/catch-all handling and `try` propagation;
- deterministic `with` resource ownership and cleanup-failure composition;
- source-root modules/imports, aliases, public/private declarations and circular-import diagnostics.

### Explicit Unicode Text views

The bootstrap frontend/runtime implements:

```eri
text.characters
text.scalars
text.bytes
```

The public source model remains intentionally small:

- `text.characters[i]` returns `Text` containing one Unicode extended grapheme cluster;
- `text.scalars[i]` returns `Text` containing one Unicode scalar;
- `text.bytes[i]` returns `Int` in `0..255`;
- all three expose `.count`;
- indexes are zero-based `Int` values with checked bounds;
- views are read-only;
- direct `text[i]` remains invalid.

No programmer-visible `Character`, `Scalar`, or `Byte` type was invented. Compiler-internal view types preserve the distinction without expanding the source type vocabulary.

The rules are recorded in `TEXT_VIEWS.md`.

## 3. Unicode reproducibility

The Python bootstrap no longer inherits identifier/grapheme behavior from whichever Unicode database happens to ship with the host Python runtime.

It pins Unicode **17.0.0** using pinned Unicode data/support dependencies for:

- XID identifier classification;
- NFC normalization;
- extended grapheme-cluster segmentation.

Tests cover combining sequences, ZWJ emoji, scalar/byte distinctions, XID identifiers and NFC identifier identity.

A future non-Python backend/runtime must carry equivalent pinned data or generated tables. Locale APIs, `wchar_t`, platform “character” functions or an arbitrary host Unicode release are not acceptable substitutes.

## 4. Compiled Text representation

A major implementation leak was found during this phase: the original C bootstrap backend represented Eristavi `Text` as `const char *` and therefore used `strlen`, `strcmp` and C-string output semantics.

That was incompatible with the frozen language because valid Eristavi Text can contain `\0` and Text is defined by Unicode/UTF-8 semantics, not C-string termination.

The active C backend now uses a length-aware representation conceptually equivalent to:

```c
typedef struct {
    size_t len;
    unsigned char *data;
} eri_text;
```

Consequences now verified by native tests:

- `"A\0B"` outputs all three content bytes plus the line ending;
- equality compares complete Text content rather than stopping at NUL;
- concatenation preserves embedded NUL;
- Lists and identities containing Text use the length-aware representation;
- error messages and relevant runtime Text fields use the same representation;
- `writeText()` writes exact Text length;
- `readText()` validates UTF-8 rather than accepting arbitrary bytes as Text;
- invalid UTF-8 becomes checked `std.files.FileError`;
- file paths containing NUL fail as checked file errors rather than being silently truncated by C APIs.

This closes an important target-semantic leak rather than merely hiding it behind tests.

## 5. Typed IR and C/native backend

The typed IR remains source-close but now represents substantially more than the original scalar/control subset.

Native executable tests cover:

- `Int`, `Float`, `Bool`, and length-aware `Text`;
- checked Int arithmetic and division/remainder faults;
- Text concatenation, equality and embedded-NUL behavior;
- functions, recursion, conditions and loops;
- Lists, checked indexing, mutation, equality, value copying and stable iteration;
- ordinary user-defined values, nested fields, copying and structural equality;
- `maybe` / `none` and narrowed optional values;
- managed identities, aliasing and identity equality;
- checked errors, typed/catch-all handlers and propagation;
- inferred-generic concrete specializations;
- imported public functions/types and aliases;
- deterministic `std.files` read/write resources and cleanup unwinding;
- `text.bytes.count`, byte indexing, stored byte views;
- `text.scalars.count`, scalar indexing, stored scalar views.

### Remaining Text-view backend gap

`text.characters` is not approximated in compiled code.

The C backend explicitly rejects it with a diagnostic explaining that a pinned Unicode 17 grapheme runtime is required. This is intentional: implementing “characters” as code points, bytes, locale characters, or host-library graphemes would violate the frozen semantics.

This leaves one sharply-defined Text-view parity gap rather than silently inconsistent behavior.

## 6. Resource and UTF-8 semantics

Both bootstrap and compiled execution now test deterministic resource behavior.

Confirmed behavior includes:

- `with` owns a resource and cleanup occurs on normal exit and return;
- nested resources unwind in reverse order;
- file open/read/write failures remain checked failures;
- invalid UTF-8 decoding remains in the checked `FileError` channel;
- body failure remains primary if cleanup also fails;
- cleanup failure is not silently discarded;
- exact Text bytes, including embedded NUL, survive write/read round trips.

No manual lifetime/free syntax was introduced.

## 7. Float conformance status

Compiled tests cover:

- NaN equality behavior;
- positive/negative infinity from IEEE division;
- signed zero preservation;
- smallest subnormal survival rather than flush-to-zero;
- overflow to infinity.

The native builder honors `CC` and `CFLAGS`, and CI currently runs the full suite under:

- GCC on Ubuntu;
- Clang on Ubuntu;
- Clang on macOS;

with `-O2` enabled.

All three configurations pass.

This is strong bootstrap evidence against obvious compiler/host leakage, though it is not a mathematical proof across every CPU, floating-point environment and compiler version. ARM64, RISC-V, Windows/MSVC and additional optimization configurations remain future conformance work.

## 8. Test status

The verified suite contains:

```text
155 tests
```

The suite combines:

- positive execution tests;
- negative semantic diagnostics;
- interpreter/bootstrap runtime tests;
- project/module tests;
- real generated-C/native executable tests;
- Unicode 17 identifier/grapheme tests;
- length-aware native Text tests;
- compiled byte/scalar Text-view tests;
- focused Float edge-case tests.

All 155 tests pass in each of the three current CI configurations, representing **465 successful test executions per full matrix run**.

## 9. Remaining implementation gaps

The remaining gaps are principally architecture/runtime engineering rather than source-language design questions.

### A. Compiled grapheme-cluster view

`text.characters` requires a generated/pinned Unicode 17 extended-grapheme segmentation runtime in compiled targets.

The implementation must carry the relevant Unicode property data/algorithm itself or generate it as part of the runtime. It must not depend on locale-specific C facilities or an arbitrary platform Unicode library version.

### B. Stable compiled module interfaces

The Python bootstrap project compiler still shares live analyzer/module objects between imported modules.

A production compiler needs serialized interface metadata for public types, function contracts, checked errors and inferred generic relationships. Generic interface design needs to preserve enough inferred constraints for callers without requiring a live Python analyzer/body.

### C. Lower-level universal IR and direct native backend

There is still no direct ARM64, x86-64 or RISC-V machine-code backend. Generated C is intentionally a bootstrap portability backend, not the language's permanent execution model.

The next IR layer should make ownership/runtime operations, checked failures, aggregate layout and target-neutral control flow explicit enough for direct backends.

### D. Runtime/standard-library breadth

The implemented standard surface remains intentionally small, principally `output` and `std.files` plus intrinsic language/runtime operations.

JSON, networking, time, process control and broader library domains are future library work, not missing grammar.

### E. Broader platform conformance

Current automated native coverage is Linux/macOS on GCC/Clang. Windows/MSVC, ARM64 and RISC-V environments are not yet in the matrix.

## 10. Deliberately postponed — not defects

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

## 11. Quality findings

Implementation has now exposed and corrected several host-language leakage risks:

- parameters are mutable local values rather than implicitly fixed;
- generated Text output uses real line endings;
- Text equality is content-based, not pointer-based;
- compiled Text is length-aware rather than C-NUL-terminated;
- invalid UTF-8 cannot silently become Text through `readText()`;
- file paths with embedded NUL cannot silently truncate at the C boundary;
- Unicode identifiers are mangled to portable C names;
- Text ordering remains rejected because it is outside the frozen contract;
- `%` remains Int-only;
- Unicode identifier/grapheme semantics are pinned rather than host-dependent;
- native tests run across multiple C compilers and an optimized build;
- compiled `text.characters` is rejected rather than approximated incorrectly.

The multi-compiler matrix has already caught a real portability bug: a zero initializer accepted by GCC became invalid after the Text representation changed and was rejected by Clang. The initializer was corrected rather than special-cased per compiler.

## 12. Audit conclusion

Most of the implementation gaps identified in earlier audits are now closed.

The C/native backend is no longer a scalar prototype. It executes substantial Eristavi programs using Lists, values, optionals, identities, checked errors, resources, modules, generic specializations and length-aware Text.

The Python bootstrap is Unicode-version-pinned and implements the complete explicit Text-view source model. The compiled backend now implements UTF-8 byte and scalar views as well; only extended grapheme-cluster segmentation remains pending because it requires a real pinned Unicode runtime, not an approximation.

The next engineering priorities are:

1. embed/generate the Unicode 17 grapheme-property tables and compile `text.characters` correctly;
2. define serialized module/interface metadata that preserves inferred generic contracts;
3. define the lower-level universal IR needed by a direct CPU backend;
4. expand architecture/platform conformance;
5. implement the first direct native backend after those boundaries are stable.

> **Audit verdict:** Eristavi is a functioning pre-0.1 bootstrap compiler with a frozen source language, broad frontend/runtime coverage, a substantially capable native compilation path, length-aware UTF-8 Text semantics, pinned Unicode behavior, partial compiled Text-view parity, deterministic checked resource behavior, and multi-toolchain conformance testing. The remaining work is concentrated in Unicode grapheme runtime data, production module artifacts and direct-backend architecture—not in redesigning the language.
