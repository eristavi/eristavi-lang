# Eristavi Compiler

This directory contains the Python bootstrap implementation of the `erist` toolchain.

The source-language contract is frozen in `PRE_0_1_FREEZE.md`. The bootstrap implements that contract vertically while keeping backend limitations explicit instead of changing source semantics for implementation convenience.

## Current pipeline

```text
.eri source
    ↓
lexer / parser / AST
    ↓
name resolution + semantic analysis + type inference
    ↓                         ↘
bootstrap execution runtime    typed/source-close Eristavi IR
                                   ├─→ C11 backend → C toolchain → native executable
                                   ↓
                                Universal IR
                                   ↓
                                x86-64 backend
                                   ↓
                                assembly → assembler/linker → native executable
```

The C route remains the broad portability backend. The direct route is the first machine-code architecture slice and does not generate C.

## Frontend/runtime surface

The bootstrap frontend and execution runtime cover the principal frozen pre-0.1 surface:

- exact 28-keyword lexical vocabulary, nested comments, numeric/Text literals and locked whitespace rules;
- Unicode 17.0.0-pinned XID identifiers and NFC normalization;
- explicit `Text` views: `.characters`, `.scalars`, `.bytes`, `.count`, checked indexing and read-only behavior;
- `let`, transitive `fixed`, name-first annotations, assignment and lexical no-shadowing;
- checked signed-64-bit `Int`, binary64-oriented `Float`, `Bool`, and `Text` behavior;
- frozen operator precedence, Bool-only conditions, `if / else`, `while`, and stable `for` iteration;
- functions, recursion, result inference and completion analysis;
- compiler-inferred generic relationships with concrete specialization;
- homogeneous growable `List` values with value semantics;
- ordinary user-defined values, fixed fields, named-field construction and structural equality;
- `maybe T` / `none` with flow-sensitive narrowing;
- managed `identity T` and identity equality;
- checked errors and `try`/`else error` handling;
- deterministic `with` ownership and cleanup-failure composition;
- modules/imports, visibility, aliases and circular-import diagnostics.

## Unicode/Text compiled runtime

Compiled `Text` is represented as explicit UTF-8 bytes plus length rather than a C NUL-terminated pointer.

The generated-C backend now executes all three frozen Text views:

```text
text.bytes
text.scalars
text.characters
```

`text.characters` uses generated Unicode grapheme-property tables and an embedded UAX #29-style segmentation runtime derived from the same pinned Unicode-support dependency used by the bootstrap. It does not delegate character boundaries to libc locales or arbitrary platform Unicode APIs.

Tests cover combining sequences, ZWJ emoji, Regional Indicator pairing, Indic conjuncts, Hangul/emoji cases, bounds faults and a multi-rule parity corpus against the pinned bootstrap segmentation.

## Module interfaces

`interface.py` implements versioned deterministic module metadata.

```text
erist interface models/user.eri
```

produces a `.eri-interface.json` artifact containing public type/function/error contracts, dependency identities, Unicode version and inferred generic relationships.

The project compiler can type-check an importer from that interface even if the imported source file is absent. Private functions are not exported as callable symbols.

Interface-only imports are not yet executable object artifacts; runtime/build linkage still requires implementation source.

## Typed IR and generated-C backend

The broad native path has executable coverage for:

- Int, Float, Bool and length-aware UTF-8 Text;
- checked Int arithmetic and division/remainder faults;
- Text concatenation/equality and embedded NUL;
- all explicit Unicode Text views;
- control flow, functions and recursion;
- Lists and stable iteration;
- ordinary values and structural equality;
- maybe/none;
- identities;
- checked errors;
- inferred-generic specializations;
- imported public functions/types;
- deterministic file resources and checked path operations.

`std.files` now includes deterministic file resources plus checked `exists(path)` and `remove(path)` operations.

## Universal IR

`universal_ir.py` defines the first lower machine-independent IR used by direct CPU backends.

The initial executable slice makes these concepts explicit:

- basic blocks;
- virtual typed values;
- local slots;
- jump/branch/return terminators;
- checked Int arithmetic;
- Int/Bool comparisons and primitive output.

The first slice intentionally rejects high-level features not yet represented there. The broader typed IR/C path remains available for them.

## Direct x86-64 backend

`x86_64_backend.py` emits x86-64 System V assembly directly from Universal IR.

Current direct executable coverage includes:

- Int/Bool locals;
- assignment;
- checked Int add/subtract/multiply/divide/remainder/negation;
- comparisons and Boolean negation;
- `if / else` and `while`;
- Int/Bool output;
- overflow and division-by-zero runtime faults.

`build-direct` currently targets x86-64 Linux. The system C compiler driver is used as assembler/linker, but generated C source does not participate.

## Commands

```text
erist run examples/hello.eri
erist check examples/hello.eri
erist interface models/user.eri
erist build-c examples/hello.eri -o hello.c
erist build examples/hello.eri -o hello
erist uir examples/hello.eri -o hello.uir
erist build-asm examples/hello.eri -o hello.s --target x86_64-linux
erist build-direct examples/hello.eri -o hello --target x86_64-linux
```

For multi-file programs, pass `--source-root` when the entry file's parent is not the intended source root.

The C/native builders honor `CC` and `CFLAGS` where applicable.

## Tests

```text
python -m unittest discover -s tests -v
```

The suite contains **174 tests**. CI runs it with GCC and Clang on Ubuntu and Clang on macOS at `-O2`.

Direct x86-64 executable tests run on Linux. Portable frontend/runtime/C-backend tests run across the full matrix. Coverage includes module-interface round trips and source-independent checking, Unicode 17 grapheme compilation, std.files path operations, Universal-IR structure, direct x86-64 execution and direct arithmetic faults.

## Remaining engineering boundary

The language is no longer waiting on broad syntax/semantic design. Main compiler work is now:

- compiled implementation/object artifacts to accompany module interfaces;
- Universal-IR support for functions, Text/Float, aggregates, failures and resources;
- broader direct x86-64 parity;
- an ARM64 backend against the same Universal IR;
- broader OS/architecture CI;
- continued standard-library growth;
- eventually WebAssembly and JavaScript targets.

Implementation should continue to follow the frozen specifications rather than alter Eristavi semantics for backend convenience.
