# Eristavi Universal IR

> **Status: broad executable lower IR with verification, optimization, CFG analysis, initial x86 physical allocation and multiple consumers**

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

Universal IR represents explicit basic blocks/terminators, typed virtual values and locals, functions/calls/returns, scalar types, Text views, nominal values, Lists, maybe, identity, checked arithmetic, Float/Text operations, ordinary-value cloning/equality, checked failures and deterministic `std.files` operations.

Ordinary value semantics are explicit: transfer of a List or nominal value emits clone behavior while `identity<T>` preserves the shared handle.

## Verification and optimization

Every direct/object lowering passes the Universal-IR verifier before and after optimization. Verification covers symbol uniqueness, dense ids, valid CFG targets, Bool branches, call contracts and returns.

Bootstrap optimization currently performs:

- semantics-safe constant folding for supported Int/Bool/Float operations;
- checked-Int folding only when the result remains valid under Eristavi overflow/division rules;
- unreachable-block elimination;
- post-pass verification.

## CFG and allocation analyses

The analysis layer provides:

- block live-in/live-out sets;
- instruction-level liveness;
- virtual-value interference graphs;
- CFG-aware spill-slot coloring;
- escape classification;
- short-lived scalar register candidates.

The x86-64 collector consumes safe-point liveness to root only heap temporaries that must survive collection and uses interference coloring to reuse non-overlapping scalar spill slots. Heap spill slots that participate in root metadata stay pinned and unique.

The x86-64 backend now also consumes these analyses through an initial conservative physical-register allocator. Eligible short-lived Int/Bool and Float values can remain register-resident in lowering regions explicitly known to be call-free. Higher-level lowering instructions are treated as clobber regions: their operands and values that must survive them remain stack-backed, because helper calls may occur before all operands are consumed.

This is intentionally not yet a mature whole-function allocator. Explicit per-lowering machine use/clobber contracts, broader register pools, move/coalescing improvements and dead spill-slot/frame compaction remain open.

## Checked failures

Checked failures remain explicit state/CFG operations (`set_error`, `error_pending`, matching, views and clearing) rather than target exceptions. `try` propagation and `else error` therefore remain target-neutral.

## Deterministic resources

`with` ownership remains explicit below the source language. Lowering inserts reverse-order cleanup on normal exit, return and checked-failure propagation, preserving primary-vs-secondary failure ordering.

## Automatic memory-management boundary

Universal IR exposes heap-backed semantic type information while direct runtimes choose target-specific collection machinery.

The x86-64 runtime has liveness-aware compiler roots plus static descriptors for Text leaves, nominal fields, Lists, maybe/identity wrappers and file resources. Dynamic checked-error state retains a conservative exact-pointer fallback. ARM64 automatic reclamation remains a backend parity gap.

## Module objects

Versioned `.eri-object.json` artifacts serialize verified/optimized Universal-IR implementations tied to exact interface digests. Object v3 can additionally carry a reusable inferred-generic implementation template for downstream specialization after source removal.

## Current consumers

### x86-64 Linux
Broad direct consumer with functions, Float/Text/Text views, aggregates, Lists, maybe, identity, checked errors, resources, module objects, GC and an initial verified scalar physical-register allocation path.

### ARM64 Linux
Consumes the same IR and is native-tested for Text, aggregates, maybe/identity, checked failures and file resources in addition to scalar/functions. Automatic reclamation and explicit Text-view runtime parity remain incomplete.

### JavaScript
The ES2020 consumer supports functions/control/scalars plus nominal values, Lists, maybe, identity, deep cloning and structural equality. Int remains checked `BigInt`.

### WebAssembly
The WAT consumer supports scalar/function/control operations plus Text through an explicit UTF-8/`externref` host ABI. Aggregate/error/resource families remain future work.

## Remaining lower-IR work

The main work is maturation rather than semantic invention:

1. register-allocation maturation and broader optimization;
2. ARM64 GC/Text-view parity;
3. broader JavaScript/WebAssembly failures/resources/Text views;
4. compact production artifact/linker metadata;
5. additional OS/ABI and future native consumers such as RISC-V.

> **Universal IR carries Eristavi semantics downward; target backends do not invent them.**
