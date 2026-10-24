# Eristavi Universal IR

> **Status: Broad executable lower IR with verification, optimization, analysis and multiple consumers**

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
direct/portable target backend
```

The typed IR retains high-level Eristavi concepts useful for semantic checking and portable lowering. Universal IR makes control flow, value-transfer semantics, checked failures, resource cleanup and target runtime operations explicit enough that backends do not reinterpret the language.

## Current model

Universal IR represents:

- explicit basic blocks and jump/branch/return terminators;
- typed virtual values and local slots;
- module-level functions, parameters, calls, returns and recursion;
- `i64`, `f64`, `bool`, length-aware `text`, and `void`;
- explicit Text-view operations for bytes, Unicode scalars and grapheme characters;
- nominal type layouts and fields;
- `list<T>`, `maybe<T>`, and `identity<T>` runtime values;
- checked signed-64-bit arithmetic;
- IEEE-oriented Float operations and comparisons;
- Text concatenation/equality/output operations;
- explicit short-circuit Boolean control flow;
- construction, field access and field mutation;
- List construction/count/get/set/add and stable iteration lowering;
- explicit ordinary-value cloning at transfer boundaries;
- structural value equality and identity equality;
- checked-failure state, matching, handler dispatch and propagation;
- deterministic resource-cleanup operations;
- `std.files` open/read/write/exists/remove operations.

Ordinary value semantics are explicit. Assignment or parameter transfer of a List/nominal value emits clone behavior; `identity<T>` preserves the shared handle. Backends therefore receive the semantic distinction rather than inventing it.

## Verification

Every direct/object lowering passes a Universal-IR verifier that checks structural and type contracts including:

- unique function/type/block symbols;
- dense local/value ids;
- valid CFG targets;
- Bool branch conditions;
- call argument/result contracts;
- function return contracts;
- missing or malformed terminators.

Verification runs before and after bootstrap optimization.

## Bootstrap optimization passes

The current semantics-preserving pass pipeline includes:

- constant folding for supported Int/Bool/Float operations;
- checked-Int folding only when the compile-time result remains valid under Eristavi overflow/division rules;
- unreachable-block elimination;
- post-pass verification.

Separate target-neutral analyses provide:

- deterministic live ranges;
- stack-slot planning/coalescing groundwork;
- escape classification for call/return transfer;
- short-lived scalar register-candidate identification.

The direct backends do not yet use a mature register allocator; these analyses are groundwork, not a claim of production optimization quality.

## Checked failures

Checked failures are not lowered as target-language exceptions. Universal IR uses explicit operations such as:

```text
set_error
error_pending
error_matches
error_value
error_message
error_clear
```

combined with ordinary CFG branches. `try` propagation and `else error` handling remain target-neutral.

## Deterministic resources

`with` ownership is explicit below the source language. Lowering inserts reverse-order cleanup on normal exit, return and checked-failure propagation. Cleanup failure does not silently replace an active primary checked failure.

## Automatic memory-management boundary

Universal IR identifies heap-backed semantic types, while the current x86-64 runtime supplies compiler-rooted non-moving mark-and-sweep reclamation. Heap-typed local and temporary spill slots are rooted explicitly.

The final production collector is not frozen into Universal IR yet. Typed heap descriptors, shorter root liveness and future escape/stack allocation can evolve without changing source semantics.

## Module objects

Versioned `.eri-object.json` artifacts serialize verified/optimized Universal-IR functions and layouts tied to the exact interface digest. Object v3 can additionally carry a bootstrap reusable inferred-generic implementation template for downstream specialization after source removal.

## Current consumers

### x86-64 Linux

Broadest direct consumer: functions, Float/Text/Text views, aggregates, Lists, maybe, identity, checked errors, resources, module objects and GC runtime.

### ARM64 Linux

Consumes the same IR for scalar/functions and now has assembly-generation layers for Text, aggregates, checked failures and file resources. Current CI evidence for the expanded runtime is cross-assembly; broad native Linux ARM64 execution is still host-gated.

### JavaScript

The ES2020 backend consumes the scalar/function/control slice. Eristavi Int is emitted as checked `BigInt`, not JavaScript `Number`.

### WebAssembly

The current WAT backend consumes the scalar/function/control slice with checked Int contracts. Unsupported runtime families are rejected explicitly rather than silently approximated.

## Remaining lower-IR work

The main work is now maturation rather than semantic invention:

1. typed heap descriptors and stronger memory-liveness integration;
2. backend use of stack-slot/register-allocation analyses;
3. broader ARM64 native conformance;
4. broader JavaScript/WebAssembly runtime families;
5. compact production artifact encoding and linker metadata;
6. future additional native consumers such as RISC-V.

> **Universal IR carries Eristavi semantics downward; target backends do not invent them.**
