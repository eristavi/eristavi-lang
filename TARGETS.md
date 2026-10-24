# Eristavi Compilation Targets

> **Status: broad C and x86-64 paths with initial x86 physical allocation; native-tested ARM64; active JavaScript and WebAssembly consumers**

Eristavi is designed around machine-independent compiler IRs. Target backends preserve Eristavi semantics rather than inheriting target-language, operating-system, or CPU behavior accidentally.

## Core target set

The target strategy is:

- native machine code;
- C source;
- JavaScript;
- WebAssembly.

Rust, Go, and PHP source-generation backends are not planned targets.

## Current architecture

```text
Eristavi source
    ↓
typed/source-close Eristavi IR
    ├─→ C11 portability backend → C toolchain → native
    ↓
verified + optimized Universal IR
    ├─→ x86-64 Linux direct backend → allocation/lowering → assembly → native
    ├─→ ARM64 Linux direct backend → assembly → native
    ├─→ ES2020 JavaScript
    └─→ WebAssembly text
```

## Native: x86-64 Linux

The direct System V backend executes a broad pre-0.1 slice without generated C, including scalars, all explicit Text views, functions, ordinary values, Lists, maybe, identity, inferred generics, checked failures, deterministic resources and source-independent module-object linkage.

Its non-moving mark-and-sweep runtime combines CFG-liveness-aware compiler roots with static heap descriptors for Text leaves, nominal fields, Lists, maybe/identity wrappers and current file-resource records. Scalar spill slots are interference-colored and reused where safe. Dynamic error state still has a conservative exact-tracked-pointer fallback.

The backend also has an initial conservative physical-register allocator. Short-lived scalar virtual values in known call-free lowering regions may remain in GP/XMM registers, with CFG interference preventing conflicting assignments. Complex lowerings are treated as machine clobber regions, so their operands and values that must survive them remain stack-backed. This preserves the existing System V ABI and precise-GC contract while giving x86 a genuine register-resident path. Broader register pools, explicit per-lowering use/clobber metadata and spill-frame compaction remain maturation work.

## Native: ARM64 Linux

The AArch64/AAPCS64 backend consumes the same Universal IR and executes natively in hosted CI.

Current tested/runtime coverage includes:

- Int/Bool/Float;
- functions/calls/recursion;
- register/stack argument placement;
- checked Int arithmetic/division/remainder;
- comparisons and control flow;
- length-aware Text;
- nominal values, Lists, maybe and identity;
- checked-error runtime state and handlers;
- deterministic `std.files` operations and cleanup.

A native ARM64 Ubuntu CI job executes aggregate/error/resource programs, while cross-assembly tests remain as an independent structural check.

Remaining ARM64 parity work includes automatic memory reclamation and the explicit `.bytes`, `.scalars`, and `.characters` direct runtime views.

## C

C remains the broad bootstrap portability/interoperability target:

```text
Eristavi typed IR → C11 → C toolchain → native executable
```

The generated-C backend covers the principal implemented pre-0.1 surface, including all three Unicode Text views with pinned grapheme segmentation.

## JavaScript

The ES2020 backend preserves Eristavi checked signed-64-bit `Int` with `BigInt`, never ordinary JavaScript `Number`.

It executes:

- functions and control flow;
- Int/Bool/Float/Text;
- nominal values and field mutation;
- Lists and checked indexing;
- maybe/none;
- identity handles;
- deep ordinary-value cloning;
- structural equality.

Checked errors, deterministic resources and explicit Text views remain JavaScript parity work.

## WebAssembly

The WAT backend consumes the scalar/function/control slice and supports Text through an explicit semantic host ABI.

Text constants are emitted as UTF-8 data segments and materialized as `externref`; concatenation, equality and output are imports rather than pointer/integer approximations. Checked Int arithmetic also remains explicit runtime imports.

Aggregate values, checked errors, resources, Text views and binary/runtime execution integration remain future WebAssembly work.

## Unicode target conformance

Unicode behavior is pinned to Unicode 17.0.0. CI fetches an immutable-revision copy of the official `GraphemeBreakTest-17.0.0.txt` vectors and runs every non-comment case against the pinned reference grapheme implementation.

## Semantic rule

> **Target platforms implement Eristavi semantics; they do not redefine them.**

A program must not change its defined meaning merely because it is compiled to direct x86-64, ARM64, generated C, WebAssembly or JavaScript.

## Next target work

Priority is now:

1. ARM64 GC and explicit Text-view parity;
2. x86 register-allocation maturation and tighter GC lifetime metadata;
3. broader JavaScript/WebAssembly checked-error/resource/Text-view support;
4. additional OS/ABI targets, especially Windows and macOS direct-native paths;
5. RISC-V as a later third native architecture once the runtime ABI is mature.
