# Eristavi Compilation Targets

> **Status: Broad C backend, substantial direct x86-64 backend, ARM64 proof backend**

Eristavi is designed around machine-independent compiler IRs. Target backends preserve Eristavi semantics rather than inheriting target-language, operating-system, or CPU behavior accidentally.

## Core target set

The long-term target strategy remains:

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
Universal IR
    ├─→ x86-64 Linux direct backend → assembly → native
    └─→ ARM64 Linux backend → assembly
```

The C path remains the broad portability baseline. The x86-64 route is a genuine direct compiler path and no longer only a scalar proof. ARM64 is the second CPU consumer of the same Universal IR and currently validates the scalar/function architecture.

## Native: x86-64 Linux

The direct x86-64 System V backend currently executes:

- Int, Bool, Float and length-aware Text;
- functions, recursion, register and stack arguments;
- checked Int arithmetic/division/remainder faults;
- conditions, loops and short-circuit Boolean control flow;
- ordinary nominal values with deep value semantics;
- Lists, stable iteration, checked indexing and structural equality;
- maybe/none;
- managed identity and identity equality;
- source-monomorphized inferred generics;
- checked failures, typed/catch-all handlers and propagation;
- deterministic `std.files` resources and cleanup;
- exact-length UTF-8 file I/O plus checked `exists/remove`;
- serialized module object linkage without dependency source for supported concrete functions/types.

Generated C does not participate in this route. The system compiler driver is currently used as assembler/linker.

Remaining direct x86-64 work includes Unicode Text views, production memory reclamation/GC, reusable precompiled generic templates, broader runtime/stdlib coverage and additional conformance/performance work.

## Native: ARM64 Linux

An AArch64/AAPCS64 backend now consumes the same Universal IR for the scalar/function slice, including:

- Int/Bool/Float;
- functions, calls and recursion;
- register/stack argument placement;
- checked Int arithmetic/division/remainder;
- comparisons and control flow;
- scalar output.

CI cross-assembles emitted ARM64 assembly with Clang's AArch64 target. A native execution test is present and activates only on an ARM64 Linux host.

ARM64 aggregate, checked-error, resource and Text-runtime parity is not yet implemented. This backend currently proves the shared lower-IR architecture rather than claiming feature parity with x86-64.

## C

C remains the broad bootstrap portability/interoperability target:

```text
Eristavi typed IR → C11 → C toolchain → native executable
```

The generated-C backend covers the broad pre-0.1 implementation, including all three Unicode Text views with pinned grapheme segmentation. Generated C is an implementation target, not the definition of Eristavi semantics.

## JavaScript

JavaScript remains a strategic target for browser and JavaScript-hosted environments.

The backend must preserve checked signed 64-bit `Int`; ordinary JavaScript `Number` cannot silently stand in where integer precision would be lost. `BigInt` and runtime helpers may be required.

No JavaScript backend is implemented yet.

## WebAssembly

WebAssembly remains a strategic direct target for portable sandboxed execution, browsers, servers, edge environments and embedding.

Its runtime integration must preserve Eristavi semantics for memory management, checked failures, Unicode Text, resources and other guarantees.

No WebAssembly backend is implemented yet.

## Semantic rule

> **Target platforms implement Eristavi semantics; they do not redefine them.**

A program must not change its defined meaning merely because it is compiled to direct x86-64, ARM64, generated C, WebAssembly or JavaScript.

## Next target work

From the current state, the priority is:

1. production memory/GC support for direct heap-backed values;
2. direct Unicode Text views and broader runtime parity;
3. ARM64 parity against the same Universal IR plus native ARM CI;
4. reusable inferred-generic module-object templates;
5. WebAssembly once the direct runtime ABI is stable;
6. JavaScript when browser/JS-hosted execution becomes a priority.
