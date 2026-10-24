# Eristavi Compiler

This directory contains the Python bootstrap implementation of the `erist` toolchain.

The source-language contract is frozen in `PRE_0_1_FREEZE.md`. Backend work follows that contract without weakening source semantics for implementation convenience.

## Current pipeline

```text
.eri source
    ↓
lexer / parser / AST
    ↓
name resolution + semantic analysis + type inference
    ↓                         ↘
bootstrap execution runtime    typed/source-close Eristavi IR
                                   ├─→ C11 backend → C toolchain → native
                                   ↓
                         verified + optimized Universal IR
                                   ├─→ x86-64 Linux → native
                                   ├─→ ARM64 Linux → assembly/native on matching host
                                   ├─→ ES2020 JavaScript
                                   └─→ WebAssembly text
```

## Frontend/runtime surface

The bootstrap frontend/reference runtime covers the principal frozen pre-0.1 language surface:

- Unicode 17.0.0-pinned identifiers/NFC;
- Int, Float, Bool and length-aware Unicode Text;
- `.characters`, `.scalars`, and `.bytes` Text views;
- `let`, transitive `fixed`, annotations, lexical scopes and no-shadowing;
- `if / else`, `while`, stable `for`;
- functions, recursion, inferred/explicit results;
- inferred generic relationships and concrete specialization;
- growable `List` values;
- ordinary named-field values and deep value semantics;
- `maybe` / `none` and narrowing;
- managed `identity` and identity equality;
- checked failures;
- deterministic `with` resources;
- modules/imports, visibility and aliases.

## Universal IR

Universal IR now has verifier and bootstrap optimization stages.

Verification checks functions/types/blocks, local/value ids, CFG targets, branch types, call contracts and returns. Optimization currently folds supported constants and eliminates unreachable blocks, then verifies again.

Additional target-neutral analyses provide live ranges, stack-slot planning, escape classification and short-lived scalar register candidates. These analyses are groundwork for later code-generation quality improvements; the current direct backends still favor correctness over aggressive register allocation.

## Direct x86-64 Linux

The direct System V backend executes:

- functions, recursion and register/stack ABI arguments;
- Int/Bool/Float/length-aware Text;
- all explicit Text views, including pinned Unicode-17 grapheme segmentation;
- checked integer faults;
- control flow and short-circuit Boolean behavior;
- Lists and stable iteration;
- deep nominal values and structural equality;
- maybe and identity;
- source-specialized inferred generics;
- reusable inferred-generic object specialization after dependency source removal;
- checked failures and handlers;
- deterministic `std.files` resources;
- UTF-8 validation, exact Text file I/O, `exists` and `remove`;
- concrete module-object linkage without dependency source.

### Direct GC

The x86-64 runtime now includes a non-moving mark-and-sweep bootstrap collector. Compiler root frames cover heap-typed locals and Universal-IR temporary spill slots; checked-error globals are also roots.

Heap child traversal still identifies references by scanning tracked payload words for exact allocation pointers. That is safe for the current bootstrap representation but is not yet the final typed-descriptor collector.

## ARM64 Linux

The AArch64/AAPCS64 backend shares Universal IR and now has assembly-generation support for:

- Int/Bool/Float and functions/calls;
- Text runtime operations;
- nominal values, Lists, maybe and identity operations;
- checked-error state/dispatch operations;
- deterministic file-resource operations and cleanup state.

CI cross-assembles these layers. Broad native ARM64 Linux behavior is still host-gated.

## JavaScript and WebAssembly

`build-js` emits ES2020 JavaScript for the current scalar/function/control slice. Eristavi Int uses checked BigInt helpers.

`build-wat` emits WebAssembly text for the current scalar/function/control slice. Unsupported Text/higher runtime families are rejected explicitly.

## Module artifacts and caching

```text
erist interface module.eri     → module.eri-interface.json
erist object module.eri        → module.eri-object.json
erist compile-module module.eri
```

Object format v3 (`universal-ir-v3`) serializes concrete Universal IR and can carry a bootstrap `eristavi-source-v1` generic template for public inferred-generic functions. Downstream object-only builds can produce concrete specializations after the original `.eri` source is removed.

The module cache is keyed by source content plus dependency public-interface digests, so public contract changes invalidate dependents while private-only dependency changes do not.

## Commands

```text
erist run examples/hello.eri
erist check examples/hello.eri

erist interface models/user.eri
erist object models/user.eri
erist compile-module models/user.eri

erist build-c examples/hello.eri -o hello.c
erist build examples/hello.eri -o hello

erist uir examples/hello.eri -o hello.uir
erist build-asm examples/hello.eri -o hello.s --target x86_64-linux
erist build-direct examples/hello.eri -o hello --target x86_64-linux
erist link-direct examples/hello.eri -o hello --target x86_64-linux
erist build-asm examples/hello.eri -o hello-aarch64.s --target arm64-linux
erist build-js examples/hello.eri -o hello.mjs
erist build-wat examples/hello.eri -o hello.wat
```

## Tests

```text
python -m unittest discover -s tests -v
```

The current suite contains **245 tests** and passes under:

- GCC / Ubuntu / `-O2`;
- Clang / Ubuntu / `-O2`;
- Clang / macOS / `-O2`.

Direct x86-64 executable tests run on Linux. ARM64 expanded runtime output is cross-assembled, with native Linux execution host-gated.

## Remaining engineering boundary

The principal work is now production hardening:

- typed heap descriptors and better GC liveness/precision;
- native ARM64 Linux CI and runtime conformance;
- applying stack-slot/register analyses to real allocation;
- broader JavaScript/WebAssembly runtime parity;
- compact production artifact/linker formats;
- broader OS/ABI support and later RISC-V;
- wider standard library.
