# Eristavi Compilation Targets

> **Status: Architectural direction with first direct native slice implemented**

Eristavi is designed around machine-independent compiler IRs. Target backends must preserve Eristavi semantics rather than inherit target-language or CPU behavior accidentally.

## Core target set

The long-term target strategy remains:

- native machine code;
- C source;
- JavaScript;
- WebAssembly.

Rust, Go, and PHP source-generation backends are not planned targets.

## Current backend architecture

Eristavi now has two relevant IR levels:

```text
Eristavi source
    ↓
typed/source-close Eristavi IR
    ├─→ C11 portability backend
    ↓
Universal IR
    └─→ direct CPU backend
```

The typed IR retains rich source semantics. Universal IR exposes lower target-neutral basic blocks and primitive checked operations for direct backends.

## Native

Native compilation remains the primary long-term goal.

### First direct backend

The first executable direct CPU slice targets **x86-64 Linux / System V**:

```text
Eristavi source
    ↓
frontend
    ↓
typed IR
    ↓
Universal IR
    ↓
x86-64 assembly
    ↓
system assembler/linker
    ↓
native executable
```

No generated C source is used in this path.

The first slice covers Int/Bool locals, checked integer arithmetic, comparisons, `if / else`, `while`, and Int/Bool output. It is deliberately smaller than the mature C backend.

x86-64 was selected first because the current CI can execute it directly. This is an implementation sequencing decision, not a language preference. ARM64 and later architectures must consume the same machine-independent semantics.

## C

C remains the broad bootstrap portability/interoperability target:

```text
Eristavi typed IR → C source → C toolchain → native executable/library
```

The generated-C path currently implements substantially more of pre-0.1 than the first direct backend, including Text/Unicode, Lists, values, optionals, identity, checked failures, resources, modules and inferred generic specializations.

Generated C is an implementation target, not the definition of Eristavi semantics.

## JavaScript

JavaScript remains a strategic target for browser and JavaScript-hosted environments.

```text
Eristavi IR → JavaScript
```

The backend must preserve Eristavi semantics. In particular, checked signed 64-bit `Int` cannot silently become ordinary JavaScript `Number` where precision would be lost; `BigInt` and/or runtime helpers may be required.

## WebAssembly

WebAssembly remains a strategic direct target for portable sandboxed execution, browsers, servers, edge environments and embedding.

Its runtime integration must preserve Eristavi semantics for memory management, checked failures, Text/Unicode, resources and other guarantees.

## Semantic rule

> Target platforms implement Eristavi semantics; they do not redefine them.

A program must not change its defined meaning merely because it is compiled to direct x86-64, generated C, JavaScript, WebAssembly, or a future architecture.

## Next target work

The recommended implementation order from the current state is:

1. extend Universal IR with function calls and additional runtime/value concepts;
2. grow the x86-64 backend through those capabilities;
3. add ARM64 against the same Universal-IR boundary;
4. add a direct WebAssembly backend when the runtime boundary is sufficiently stable;
5. add JavaScript when browser/JS-hosted execution becomes a priority.
