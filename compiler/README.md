# Eristavi Compiler

This directory contains the Python bootstrap implementation of the `erist` toolchain.

The source-language contract is frozen in `PRE_0_1_FREEZE.md`. The implementation follows that contract vertically while keeping backend limitations explicit rather than changing source semantics for compiler convenience.

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
                                Universal IR
                                   ├─→ x86-64 Linux assembly → native
                                   └─→ ARM64 Linux assembly
```

## Frontend/runtime surface

The bootstrap frontend/reference runtime covers the principal frozen pre-0.1 language surface:

- exact lexical/identifier rules with Unicode 17.0.0-pinned XID/NFC behavior;
- Int, Float, Bool and length-aware Unicode Text;
- explicit `.characters`, `.scalars`, and `.bytes` Text views;
- `let`, transitive `fixed`, annotations, lexical scopes and no-shadowing;
- `if / else`, `while`, stable `for`;
- functions, recursion, inferred/explicit results;
- inferred generic relationships and concrete specialization;
- growable `List` values;
- ordinary named-field values and deep value semantics;
- `maybe` / `none` and narrowing;
- managed `identity` and identity equality;
- checked failures with `fails`, `fail`, `try`, and `else error`;
- deterministic `with` resources and cleanup-failure composition;
- modules/imports, visibility and aliases.

## Backend layers

### Generated-C backend

The C backend remains the broad portability baseline. It covers the principal implemented pre-0.1 surface, including all three pinned Unicode Text views, aggregates, checked failures, deterministic resources and modules.

### Universal IR

Universal IR is now substantially broader than its original scalar/control slice. It represents:

- functions/parameters/calls/returns;
- typed basic blocks and local/value slots;
- Int/Bool/Float/Text;
- checked arithmetic and short-circuit Boolean CFG;
- nominal layouts, Lists, maybe and identity;
- explicit ordinary-value cloning and structural equality;
- checked-failure state/dispatch/propagation;
- deterministic resource cleanup;
- `std.files` runtime operations.

The distinction between ordinary value and identity semantics is explicit before a CPU backend sees the program.

### Direct x86-64 Linux

The direct System V backend now executes:

- functions, recursion and register/stack ABI arguments;
- Int/Bool/Float/length-aware Text;
- checked integer faults;
- control flow and short-circuit Boolean behavior;
- Lists and stable iteration;
- deep nominal values and structural equality;
- maybe and identity;
- source-specialized inferred generics;
- checked failures and handlers;
- deterministic `std.files` resources;
- UTF-8 validation, exact Text file I/O, `exists` and `remove`;
- concrete module-object linkage without dependency source.

It remains correctness-first: virtual values are heavily stack-spilled and heap-backed direct values currently use bootstrap allocation without production GC reclamation.

### ARM64 Linux

The AArch64/AAPCS64 backend consumes the same Universal IR for the current scalar/function slice: Int/Bool/Float, calls/recursion, checked integer arithmetic, branches and scalar output.

CI cross-assembles ARM64 output. Native execution activates only on an ARM64 Linux host. Aggregate/error/resource parity is still future work.

## Module artifacts

The compiler emits two versioned artifact families:

```text
erist interface module.eri   → module.eri-interface.json
erist object module.eri      → module.eri-object.json
```

The interface contains the public contract. The object contains concrete Universal-IR functions and layouts and is bound to the interface SHA-256 digest.

The direct compiler can link supported concrete scalar, nominal, List and checked-error implementations from these artifacts after dependency source removal.

Public inferred-generic contracts survive the interface, but reusable precompiled **generic implementation templates** are still a future object-format capability. Source builds already monomorphize inferred generics normally.

## Unicode/Text runtime

Generated-C execution supports `.bytes`, `.scalars` and `.characters`, including pinned Unicode 17 grapheme segmentation.

The direct x86-64 backend currently supports length-aware Text values, concatenation/equality/output and UTF-8 file boundaries, but not the explicit Text-view operations yet. That is a clearly bounded direct-backend parity gap.

## Commands

```text
erist run examples/hello.eri
erist check examples/hello.eri

erist interface models/user.eri
erist object models/user.eri

erist build-c examples/hello.eri -o hello.c
erist build examples/hello.eri -o hello

erist uir examples/hello.eri -o hello.uir
erist build-asm examples/hello.eri -o hello.s --target x86_64-linux
erist build-direct examples/hello.eri -o hello --target x86_64-linux

erist build-asm examples/hello.eri -o hello-aarch64.s --target arm64-linux
```

For multi-file programs, use `--source-root` when the entry file's parent is not the intended project source root.

## Tests

```text
python -m unittest discover -s tests -v
```

The current suite contains **216 tests** and passes under:

- GCC / Ubuntu / `-O2`;
- Clang / Ubuntu / `-O2`;
- Clang / macOS / `-O2`.

Direct x86-64 executable tests run on Linux. ARM64 output is cross-assembled on CI, while the native ARM64 execution test is skipped unless the host is ARM64 Linux.

## Remaining engineering boundary

The principal work is now production compiler/runtime engineering:

- production automatic memory reclamation/GC for direct heap values;
- direct Unicode Text-view parity;
- reusable inferred-generic templates in module objects;
- ARM64 aggregate/error/resource/Text parity and native ARM CI;
- broader OS/ABI conformance, including Windows and future RISC-V work;
- wider standard library;
- eventual WebAssembly and JavaScript targets;
- optimization/register allocation after correctness contracts are stable.

Implementation should continue to follow the frozen specifications rather than alter Eristavi semantics for backend convenience.
