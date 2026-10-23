# Eristavi Language Semantics

> **Status: Draft / pre-0.1**
>
> This document records current semantic decisions and deliberately separates them from unresolved syntax. Nothing here should be treated as stable language specification until explicitly marked as locked.

## 1. Project identity — locked

- Language name: **Eristavi**
- Primary source extension: **`.eri`**
- Reserved extension: **`.erist`**
- Toolchain / CLI command: **`erist`**
- Official website: **eristavi.org**
- Repository: **eristavi/eristavi-lang**

## 2. Core philosophy — locked

Eristavi is intended to be:

- general-purpose;
- readable without becoming pseudo-English;
- strongly and statically typed;
- aggressively type-inferred;
- native-capable;
- portable across architectures;
- automatically memory-managed for ordinary code;
- small in language vocabulary and rich in libraries.

The compiler and runtime should absorb mechanical complexity wherever they can do so reliably.

## 3. Type inference — direction accepted

Ordinary values should not require redundant type annotations.

```eri
let age be 44;
let name be "Anna";
let numbers be [10, 20, 30];
```

The compiler should infer the corresponding internal types.

Explicit type annotations remain valuable where inference is impossible or where an API contract should deliberately constrain a value.

## 4. Collections — direction accepted

Collection element types should be inferred whenever possible.

```eri
let names be ["Anna", "Maria", "John"];
```

The compiler can infer a list whose elements are `Text`.

An initially empty collection may acquire its element type from later uses within the relevant inference context:

```eri
let customers be [];

customers.add(Customer("Anna"));
customers.add(Customer("John"));
```

The compiler should infer that `customers` contains `Customer` values.

If incompatible values are added, compilation should fail with a useful diagnostic rather than silently degrading to an untyped collection.

```eri
let values be [];
values.add(10);
values.add("hello");
```

This should produce a type-conflict error unless the programmer has explicitly chosen a type model that permits both values.

### Explicit generic syntax

No user-facing generic/container type notation is currently locked.

Previous experiments using angle brackets, square brackets, dots, and colons are **not part of the language specification**.

The design goal is to avoid exposing generic syntax where reliable inference makes it unnecessary.

## 5. Variables and immutability — locked

Ordinary `let` bindings are mutable by default:

```eri
let price be 50;
price = 60;
```

A binding that must not be reassigned after initialization is declared with `fixed`:

```eri
let fixed price be 50;
```

Attempting to reassign a fixed binding is a compile-time error:

```eri
let fixed price be 50;
price = 60;
```

The compiler should report that `price` is fixed and cannot be changed.

The same `fixed` rule applies to fields inside user-defined types:

```eri
type User {
    fixed id Int;
    name Text;
}
```

A `fixed` field is assigned as part of initialization and cannot be reassigned afterward. A field without `fixed` remains mutable according to the surrounding value/reference semantics.

The exact constructor or initialization syntax is not locked yet; this rule defines the immutability guarantee independently of that syntax.

The semantic rule is:

> `fixed` means initialized once, then immutable.

Eristavi should not introduce a second immutability keyword for fields. The same concept uses the same word everywhere.

## 6. Fundamental types — working set

The early language should remain small. The working fundamental type set is:

- `Int`
- `Float`
- `Bool`
- `Text`

Additional numeric widths, `Byte`, decimal arithmetic, optionals, maps, sets, and other types should be added only when the implementation or real programs require them.

## 7. Functions — working direction

Functions should have a single primary declaration form.

Current draft examples use:

```eri
function add(a Int, b Int) returns Int {
    return a + b;
}
```

Parameter and return types may eventually be inferred where doing so remains clear and safe, but public API contracts may reasonably stay explicit.

## 8. Control flow — working set

The initial language should focus on a minimal set:

- `if` / `else`
- `for` / `in`
- `while`
- `return`

The project should not add overlapping control-flow constructs until real use cases justify them.

### Boolean operators — locked

Eristavi uses readable word operators for Boolean logic:

```eri
and
or
not
```

Examples:

```eri
if ready and connected {
    start();
}

if failed or expired {
    stop();
}

if not connected {
    reconnect();
}
```

The symbolic aliases `&&`, `||`, and `!` are not part of Eristavi Boolean syntax. This keeps one obvious form for logical operations and preserves symbolic operators for other purposes where needed.

## 9. Memory management — architectural direction

Ordinary Eristavi code should not manually allocate and free general-purpose memory.

The compiler/runtime should be free to use:

- registers;
- stack allocation;
- escape analysis;
- object elimination;
- managed heap allocation;
- garbage collection.

The first collector should favor correctness and implementation clarity over advanced optimization.

External resources such as files and sockets should eventually use deterministic scoped cleanup rather than waiting for garbage collection.

## 10. Standard library boundary

Capabilities such as text operations, sorting, JSON, networking, files, dates, and databases should normally be libraries rather than language keywords.

For example, operations such as:

```eri
text.words.count
text.reverse
items.sort
```

should be type/library behavior, not special grammar.

## 11. Compilation architecture — locked principle, implementation pending

The language should compile through an Eristavi-owned machine-neutral intermediate representation.

```text
Eristavi source
    ↓
frontend
    ↓
typed representation
    ↓
Eristavi IR
    ↓
target backend
```

The source language must not be designed around a specific CPU architecture.

The long-term architecture may support both native target backends and a stable portable execution format.

## 12. Initial implementation scope

The first implementation should prove the language with a deliberately small feature set:

```eri
let x be 40;
let y be 2;

print x + y;
```

The first compiler milestone does not require generics, async/await, macros, reflection, multiple native backends, a package registry, or an advanced garbage collector.

## 13. Open decisions

The following must be decided deliberately before being treated as stable:

- explicit type-annotation syntax in all positions;
- optional / absent-value model;
- value vs identity/reference type semantics;
- error model;
- exact integer and overflow semantics;
- Unicode indexing semantics;
- generic abstraction model when inference alone is insufficient;
- module/import syntax;
- resource-management syntax;
- first native target backend;
- exact IR specification.

These open questions should be resolved from the design philosophy rather than by copying another language's syntax.
