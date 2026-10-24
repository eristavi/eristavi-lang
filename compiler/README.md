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
                                   ├─→ x86-64 Linux → allocation/lowering → native
                                   ├─→ ARM64 Linux → native
                                   ├─→ ES2020 JavaScript
                                   └─→ WebAssembly text
```

## Frontend/runtime surface

The bootstrap frontend/reference runtime covers the principal frozen pre-0.1 surface: Unicode-17 identifiers/NFC, scalar types, explicit Text views, bindings/fixed, scopes, control flow, functions/recursion, inferred generics, Lists, ordinary values, maybe, identity, checked failures, deterministic resources and modules/imports.

## Universal IR and analyses

Universal IR is verified before and after bootstrap optimization.

Verification checks symbols, CFG targets, local/value ids, branch types, call contracts and returns. Optimization currently performs safe constant folding and unreachable-block elimination.

Target-neutral analyses include:

- CFG-aware live-in/live-out sets;
- instruction-level liveness at safe points;
- virtual-value interference graphs;
- spill-slot coloring;
- escape classification;
- scalar register-candidate discovery.

The x86-64 GC backend uses these analyses to root only heap temporaries that cross collection safe points and to reuse noninterfering scalar spill slots.

The x86-64 backend now also has an initial conservative physical-register allocator. Eligible short-lived scalar values in known call-free lowering regions may remain in a GP or XMM register. Complex lowering operations are treated as clobber regions: their operands and values that must survive them remain stack-backed until explicit machine-level use/clobber contracts are available. This preserves the existing ABI and precise-GC guarantees while establishing a real register-resident path.

## Direct x86-64 Linux

The direct System V backend executes a broad pre-0.1 surface, including all Text views, deep ordinary values, Lists, maybe/identity, inferred generics, checked failures, deterministic files and object-only module linkage.

### Direct GC

The non-moving mark-and-sweep runtime combines compiler-described root addresses with static type descriptors.

Typed traversal covers Text leaves, nominal fields, Lists and their backing arrays, maybe/identity wrappers and file-resource records. Dynamic checked-error state retains a conservative exact-tracked-pointer fallback. Heap temporary spill slots remain pinned/stable when rooted; scalar spill slots may be coalesced.

This is substantially more precise than scanning every payload word, while still remaining a correctness-first bootstrap collector rather than a generational/concurrent production GC.

### Physical register allocation

The first allocator slice is deliberately narrow:

- Int/Bool and Float use separate register classes;
- CFG interference prevents overlapping values from sharing a physical register;
- caller-saved residency is allowed only for verified short-lived scalar regions;
- values crossing helper/PLT/GC clobbers remain spilled;
- operands of complex clobbering lowerings remain spilled because a helper may run before every operand is consumed;
- higher-level scalar extraction remains stack-backed until lowering contracts become explicit;
- stack spill slots remain the correctness fallback.

The next allocator work is to formalize per-lowering use/clobber metadata, expand the safe register pool, improve move/coalescing decisions and compact spill slots that become unnecessary.

## ARM64 Linux

The AArch64/AAPCS64 backend shares Universal IR and runs natively in hosted ARM64 Linux CI.

Behavioral coverage includes:

- Int/Bool/Float and functions/calls;
- length-aware Text;
- nominal values and Lists;
- maybe and identity;
- checked errors/handlers;
- deterministic file resources and embedded-NUL UTF-8 I/O.

Cross-assembly tests remain in addition to native execution. ARM64 automatic memory reclamation and explicit Text-view parity remain open.

## JavaScript

`build-js` emits ES2020 JavaScript with checked `BigInt` for Eristavi Int.

The backend supports ordinary nominal values, Lists, maybe, identity, deep cloning and structural equality in addition to functions, scalars and control flow. Checked errors, resources and explicit Text views are not yet parity-complete.

## WebAssembly

`build-wat` emits WebAssembly text for functions/control flow/scalars plus Text through an explicit `externref` host ABI.

UTF-8 Text constants use data segments; construction, concatenation, equality and output are host contracts. Aggregate values, checked errors, resources, explicit Text views and binary execution integration remain future work.

## Module artifacts and caching

```text
erist interface module.eri     → module.eri-interface.json
erist object module.eri        → module.eri-object.json
erist compile-module module.eri
```

Object format v3 (`universal-ir-v3`) serializes concrete Universal IR and can carry a reusable bootstrap template for public inferred-generic functions. Downstream object-only builds can specialize these functions after original source removal.

The module cache is keyed by source content plus dependency public-interface digests, so public contract changes invalidate dependents while private-only dependency changes do not.

## Unicode conformance

The toolchain pins Unicode 17.0.0. CI downloads an immutable-revision copy of the official Unicode-17 `GraphemeBreakTest` fixture and executes every non-comment vector against the pinned reference segmenter. Direct/generated-C Text-view tests provide additional backend coverage.

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
erist build-direct examples/hello.eri -o hello-aarch64 --target arm64-linux
erist build-js examples/hello.eri -o hello.mjs
erist build-wat examples/hello.eri -o hello.wat
```

## Tests

```text
python -m unittest discover -s tests -v
```

The current suite contains **262 tests** and passes under:

- GCC / x86-64 Ubuntu / `-O2`;
- Clang / x86-64 Ubuntu / `-O2`;
- Clang / ARM64 Ubuntu / `-O2`;
- Clang / ARM64 macOS / `-O2`.

Platform-specific native tests execute on their matching Linux architecture. The same matrix runs the official Unicode-17 grapheme vectors.

## Remaining engineering boundary

The principal work is now production hardening:

- ARM64 GC and explicit Text-view parity;
- register-allocation maturation and broader optimization passes;
- broader JavaScript/WebAssembly failure/resource/Text-view parity;
- compact production object/linker formats;
- broader OS/ABI support and later RISC-V;
- wider standard library.
