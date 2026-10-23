# Eristavi Compilation Targets

> **Status: Architectural direction for pre-0.1 and beyond**

Eristavi is designed around a machine-independent Eristavi IR. Target backends consume that IR while preserving Eristavi language semantics.

## Core direction

The long-term target strategy is deliberately narrow:

- native machine code;
- C source;
- JavaScript;
- WebAssembly.

Rust, Go, and PHP source-generation backends are not planned targets. They add maintenance cost without providing a strategic capability that justifies expanding the compiler surface.

## Native

Native compilation remains the primary long-term goal.

```text
Eristavi source
    ↓
frontend
    ↓
Eristavi IR
    ↓
native backend
    ↓
machine code
```

Individual CPU backends may be added incrementally. Eristavi semantics must remain independent of the selected CPU architecture or operating system.

## C

C is a useful portability and interoperability target.

```text
Eristavi IR → C source → C toolchain → native executable/library
```

The generated C is an implementation target, not the definition of Eristavi semantics. Runtime helpers may be emitted or linked where C alone does not directly provide an Eristavi guarantee.

## JavaScript

JavaScript is a strategic target for browser and JavaScript-hosted environments.

```text
Eristavi IR → JavaScript
```

The backend must preserve Eristavi semantics rather than inherit JavaScript semantics accidentally. For example, Eristavi `Int` is a checked signed 64-bit integer, so ordinary JavaScript `Number` cannot be used where doing so would lose integer precision. The backend may use `BigInt` and/or runtime helpers as required.

## WebAssembly

WebAssembly is a strategic target for portable sandboxed execution, browsers, servers, edge environments, and embedding.

```text
Eristavi IR → WebAssembly
```

WebAssembly should be treated as a direct compilation target rather than as a source-language transpilation target.

Its runtime integration layer must still preserve Eristavi semantics for memory management, checked failures, Text/Unicode, resources, and other language guarantees.

## Semantic rule

> Target platforms implement Eristavi semantics; they do not redefine them.

A program must not change its defined meaning merely because it is compiled to native code, C, JavaScript, or WebAssembly.

## Priority

The initial compiler does not need all four targets.

The recommended implementation order is:

1. first executable backend sufficient to prove the compiler architecture;
2. native compilation path;
3. WebAssembly and/or C as additional portable targets;
4. JavaScript when browser/JavaScript-hosted execution becomes an implementation priority.

Exact backend order may change based on implementation needs without changing this architectural target set.
