# Eristavi Compilation Targets

> **Status: Broad C backend; substantial direct x86-64; expanded ARM64 assembly path; first JavaScript and WebAssembly consumers**

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
    ├─→ x86-64 Linux direct backend → assembly → native
    ├─→ ARM64 Linux backend → assembly/native on matching host
    ├─→ ES2020 JavaScript
    └─→ WebAssembly text
```

## Native: x86-64 Linux

The direct System V backend executes a broad pre-0.1 slice without generated C:

- Int, Bool, Float and length-aware Text;
- `.bytes`, `.scalars`, and Unicode-17 `.characters` Text views;
- functions, recursion, register and stack arguments;
- checked Int arithmetic/division/remainder faults;
- conditions, loops and short-circuit Boolean control flow;
- ordinary nominal values with deep value semantics;
- Lists, stable iteration, checked indexing and structural equality;
- maybe/none;
- managed identity and identity equality;
- inferred generic specialization, including reusable module-object templates;
- checked failures, typed/catch-all handlers and propagation;
- deterministic `std.files` resources and cleanup;
- exact-length UTF-8 file I/O plus checked `exists/remove`;
- serialized module object linkage without dependency source for supported implementations;
- compiler-rooted non-moving mark-and-sweep bootstrap reclamation.

The current GC precisely identifies compiler root slots (heap locals and Universal-IR temporaries) but still discovers child references inside tracked heap payloads by exact pointer matching rather than typed heap descriptors. Production typed heap maps remain runtime-hardening work.

## Native: ARM64 Linux

The AArch64/AAPCS64 backend consumes the same Universal IR. Assembly-generation coverage now includes:

- Int/Bool/Float;
- functions/calls/recursion;
- register/stack argument placement;
- checked Int arithmetic/division/remainder;
- comparisons and control flow;
- Text and aggregate runtime representation operations;
- nominal values, Lists, maybe and identity operations;
- checked-error runtime state/dispatch operations;
- deterministic `std.files` runtime operations and cleanup state.

CI cross-assembles emitted ARM64 code. Native Linux execution remains host-gated, so current evidence for the expanded runtime layers is cross-assembly/structural rather than full behavioral parity with x86-64.

## C

C remains the broad bootstrap portability/interoperability target:

```text
Eristavi typed IR → C11 → C toolchain → native executable
```

The generated-C backend covers the principal implemented pre-0.1 surface, including all three Unicode Text views with pinned grapheme segmentation.

## JavaScript

An ES2020 backend now consumes Universal IR for the current scalar/function/control-flow slice.

Key semantic rule: Eristavi `Int` maps to checked JavaScript `BigInt`, never silently to `Number`. Tests execute functions, Float/Text behavior, control flow and overflow protection with an available JavaScript runtime.

Aggregate values, checked errors, deterministic resources and the full Unicode runtime are not yet JavaScript-parity complete.

## WebAssembly

A WebAssembly-text backend now consumes Universal IR for the current scalar/function/control-flow slice. It emits direct WAT contracts for checked Int operations, functions/calls and control-flow dispatch.

Text and higher runtime families are currently rejected explicitly rather than approximated. Binary execution/runtime integration remains later work.

## Semantic rule

> **Target platforms implement Eristavi semantics; they do not redefine them.**

A program must not change its defined meaning merely because it is compiled to direct x86-64, ARM64, generated C, WebAssembly or JavaScript.

## Next target work

The priority is now:

1. typed heap descriptors and stronger direct-GC precision/reclamation policy;
2. native ARM64 Linux CI and behavioral parity for the expanded assembly layers;
3. broaden JavaScript/WebAssembly through aggregates, errors, Text views and runtime services;
4. additional OS/ABI targets, especially Windows and macOS direct-native work;
5. RISC-V as a later third native architecture once the runtime ABI is stable.
