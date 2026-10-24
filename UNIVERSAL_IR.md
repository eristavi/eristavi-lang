# Eristavi Universal IR

> **Status: Broad executable lower IR implemented for pre-0.1 bootstrap**

Eristavi has two intentionally distinct compiler IR levels:

```text
Eristavi source
    ↓
semantic analysis + type inference
    ↓
typed/source-close Eristavi IR
    ↓
Universal IR
    ↓
direct target backend
```

The typed IR retains high-level Eristavi concepts useful for semantic checking and portable backends. Universal IR makes control flow, value-transfer semantics, checked failures, resource cleanup and target runtime operations explicit enough that CPU backends do not need to reinterpret the language.

## Current model

Universal IR now represents:

- explicit basic blocks and jump/branch/return terminators;
- typed virtual values and local slots;
- module-level functions, parameters, calls, returns and recursion;
- `i64`, `f64`, `bool`, length-aware `text`, and `void`;
- nominal type layouts and fields;
- `list<T>`, `maybe<T>`, and `identity<T>` runtime values;
- checked signed-64-bit arithmetic;
- IEEE-oriented Float operations and comparisons;
- Text concatenation/equality/output operations;
- explicit short-circuit Boolean control flow;
- construction, field access and field mutation;
- List construction/count/get/set/add and stable iteration lowering;
- explicit ordinary-value cloning at value-transfer boundaries;
- structural value equality and identity equality;
- checked-failure state, matching, handler dispatch and propagation;
- deterministic resource-cleanup operations;
- `std.files` open/read/write/exists/remove operations.

Ordinary value semantics are represented explicitly. For example, assignment or parameter transfer of a List or nominal value emits `clone_value`; `identity<T>` does not. A backend therefore receives the difference between value and shared identity from Universal IR rather than deciding it itself.

## Checked failures

Checked failures are not lowered as a target-language exception facility. Universal IR uses explicit operations such as:

```text
set_error
error_pending
error_matches
error_value
error_message
error_clear
```

combined with ordinary CFG branches. `try` propagation and `else error` handling are therefore target-neutral.

## Deterministic resources

`with` ownership is also explicit below the source language. Lowering maintains the active cleanup stack and inserts reverse-order cleanup on:

- normal scope exit;
- `return`;
- checked-failure propagation.

Cleanup failure does not silently replace an active primary checked failure. The direct bootstrap runtime retains later cleanup failures as secondary failure context.

## Module objects

Concrete Universal-IR implementations can be serialized in versioned `.eri-object.json` artifacts. Object files include function bodies and nominal type layouts and are tied to the exact public module-interface digest.

This permits a direct executable to link a dependency from:

```text
module.eri-interface.json
module.eri-object.json
```

without reopening `module.eri`, for supported concrete implementations.

## Direct consumers

### x86-64 Linux

The x86-64 System V backend executes the broadest direct Universal-IR surface today, including functions, Float/Text, Lists, ordinary values, maybe, identity, checked errors and deterministic file resources.

### ARM64 Linux

The AArch64/AAPCS64 backend consumes the same Universal IR for the current scalar/function slice. CI cross-assembles its output with an AArch64 target, proving that Universal IR is not structurally tied to x86-64. Native ARM64 execution remains gated on an ARM64 Linux runner, and aggregate/error/resource parity is future work.

## Remaining lower-IR work

Universal IR is now broad, but important runtime/compiler work remains:

1. direct Text-view operations for `.bytes`, `.scalars`, and `.characters`;
2. explicit memory-management/GC runtime operations and reclamation policy for direct heap values;
3. reusable inferred-generic implementation templates in precompiled module objects;
4. ARM64 parity for heap values, failures and resources;
5. optimization passes after representation and ownership contracts are stable;
6. WebAssembly and JavaScript consumers of the same semantics.

The governing rule remains:

> **Universal IR carries Eristavi semantics downward; target backends do not invent them.**
