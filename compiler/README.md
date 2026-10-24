# Eristavi Compiler

This directory contains the Python bootstrap implementation of the `erist` toolchain.

The source-language contract is frozen in `PRE_0_1_FREEZE.md`. The bootstrap implements that contract vertically so supported features can be parsed, type-checked, executed, lowered to typed Eristavi IR, compiled, and tested without inventing alternate syntax.

## Current pipeline

```text
.eri source
    ↓
lexer
    ↓
parser / AST
    ↓
name resolution + semantic analysis + type inference
    ↓                         ↘
bootstrap execution runtime    typed Eristavi IR
                                   ↓
                                C backend
                                   ↓
                              system C compiler
                                   ↓
                              native executable
```

## Frontend/runtime surface

The bootstrap frontend and execution runtime now cover the principal frozen pre-0.1 language surface:

- exact 28-keyword lexical vocabulary, nested comments, numeric/Text literals and locked whitespace rules;
- Unicode 17.0.0-pinned XID identifiers and NFC normalization;
- explicit `Text` views: `.characters`, `.scalars`, `.bytes`, `.count`, checked indexing and read-only behavior;
- `let`, transitive `fixed`, name-first annotations, assignment and lexical no-shadowing;
- checked signed-64-bit `Int`, binary64-oriented `Float`, `Bool`, and `Text` behavior;
- frozen operator precedence, Bool-only conditions, `if` / `else`, `while`, and stable `for` iteration;
- module-level functions, typed/inferred result contracts, no-value functions, recursion and completion analysis;
- compiler-inferred generic parameter relationships with concrete specialization;
- growable homogeneous `List` values, empty-list inference, checked indexing, `.count`, `.add`, mutation, equality and value semantics;
- ordinary user-defined values, fixed fields, named-field construction, nested mutation, structural equality and copying;
- `maybe T` / `none` and flow-sensitive presence narrowing;
- managed `identity T`, aliasing, identity equality and shared mutation;
- checked errors, `fails`, `fail`, typed/catch-all `else error`, exhaustiveness and `try` propagation;
- deterministic `with` ownership for `std.files`, including cleanup-failure composition;
- modules/imports, aliases, public/private declarations, circular-import diagnostics and source-root loading.

The Unicode Text-view implementation deliberately uses compiler-internal view types. In pre-0.1, character/scalar indexing yields `Text`, byte indexing yields `Int`, and no public `Character`, `Scalar`, or `Byte` type has been invented.

## Typed IR and C/native backend

`ir.py` defines the first machine-independent typed Eristavi IR. The C/native path has grown well beyond the original scalar slice and currently has executable tests for:

- `Int`, `Float`, `Bool`, and `Text`;
- checked signed-64-bit arithmetic and Int division/remainder faults;
- Text concatenation and content equality;
- `if` / `else`, `while`, functions, recursion and output;
- Lists, checked indexing, mutation, equality, value copying and stable iteration;
- ordinary user-defined values, nested fields, structural equality and value semantics;
- `maybe` / `none` and narrowed optional values;
- identities, aliasing and identity equality;
- checked errors, typed/catch-all handlers and propagation;
- inferred-generic concrete specializations;
- imported public functions/types and aliases;
- deterministic `std.files` resources, read/write operations and cleanup unwinding.

`c_backend.py` emits C11 and `erist build` invokes a system C compiler. This is a real native compilation route, but it remains a bootstrap portability backend rather than Eristavi's eventual direct CPU backend.

Explicit Unicode Text views are currently implemented in the frontend/bootstrap runtime but are not yet lowered through the C backend. A compiled grapheme-cluster implementation requires a pinned Unicode runtime strategy rather than delegating silently to platform character APIs.

## Commands

```text
python -m compiler.erist run examples/hello.eri
python -m compiler.erist check examples/hello.eri
python -m compiler.erist build-c examples/hello.eri -o hello.c
python -m compiler.erist build examples/hello.eri -o hello
```

When installed through `pyproject.toml`, the same commands are available through `erist`.

For multi-file programs, pass `--source-root` when the entry file's parent is not the intended project source root.

The native builder honors `CC`, allowing the conformance suite to exercise more than one host C compiler.

## Tests

Run:

```text
python -m unittest discover -s tests -v
```

The verified suite currently contains **144 passing tests**. It covers frontend/runtime semantics, project loading, generated C/native execution, Lists, values, maybe, identity, errors, resources, generics, modules, Unicode 17 identifiers/graphemes/Text views, and focused binary64 edge cases including NaN, infinities, signed zero and subnormals.

CI is configured to exercise the native path with GCC and Clang on Ubuntu and Clang on macOS, increasing the chance of catching host-toolchain leakage.

## Remaining engineering boundary

The source language is no longer waiting on broad semantic design. Remaining implementation work is concentrated in:

- compiled/native parity for the explicit Unicode Text views;
- stronger cross-platform Float conformance evidence and optimization-mode testing;
- stable serialized module/interface metadata instead of live Python analyzer sharing;
- broader standard-library/runtime facilities;
- the eventual lower-level universal IR and first direct CPU backend.

Implementation should continue to follow the frozen specifications rather than changing Eristavi semantics for backend convenience.
