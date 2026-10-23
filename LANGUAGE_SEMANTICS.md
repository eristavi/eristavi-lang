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

A `fixed` field is assigned as part of initialization and cannot be reassigned afterward.

The exact constructor or initialization syntax is not locked yet; this rule defines the immutability guarantee independently of that syntax.

The semantic rule is:

> `fixed` means initialized once, then immutable.

Eristavi should not introduce a second immutability keyword for fields. The same concept uses the same word everywhere.

### Deep immutability — locked

A `fixed` binding makes the complete bound value immutable from the programmer's point of view, including nested mutable fields that are part of that value.

```eri
let fixed user be User(...);

user.name = "Maria";           // compile-time error
user.address.city = "Paphos";  // compile-time error
user = anotherUser;             // compile-time error
```

This avoids a distinction where the binding is fixed but the value behind it can still be mutated.

## 6. Value semantics — locked

Ordinary Eristavi user-defined types use value semantics by default.

```eri
let a be user;
let b be a;

b.name = "Maria";
```

Changing `b` must not change `a`.

Assignment, ordinary parameter passing, and ordinary collection extraction should therefore behave as logical value copies rather than hidden aliases.

The language semantics do **not** require eager physical copying. The compiler/runtime may use copy elision, shared storage, copy-on-write, escape analysis, stack allocation, or other optimizations as long as observable behavior remains value-based.

### Identity and sharing

Some values genuinely require shared identity, such as connections, actors, graph nodes, or explicitly shared application state.

Eristavi should support such behavior only through an explicit future reference/identity mechanism. Ordinary `type` declarations must not silently become reference types.

The syntax for explicit shared/reference semantics is not yet locked.

### Function mutation

Ordinary function parameters should not silently mutate caller state through hidden aliasing.

If Eristavi later supports in-place mutation of a caller-owned value, that intent should be explicit in the function declaration or call semantics. The syntax for this feature remains open.

## 7. Optional values — locked

Eristavi does not use ordinary `null` values.

Absence is represented explicitly with `none`, and a type that is allowed to be absent is written with `maybe`:

```eri
maybe User
maybe Text
maybe Int
```

For example:

```eri
type User {
    fixed id Int;
    name Text;
    middleName maybe Text;
}
```

A function may explicitly return an optional value:

```eri
function findUser(id Int) returns maybe User {
    if id == 1 {
        return User(...);
    }

    return none;
}
```

A normal `User`, `Text`, `Int`, or other non-`maybe` type cannot contain `none`.

```eri
let name be "Anna";
name = none;            // compile-time error
```

`none` does not implicitly make arbitrary values nullable. It is valid only where the expected type is optional or where type inference can establish a `maybe` type from surrounding context.

### Presence checks and narrowing

A `maybe` value cannot be used as though it definitely contains its underlying value.

```eri
let user be findUser(1);
print user.name;         // compile-time error
```

The programmer must establish that the value is present:

```eri
let user be findUser(1);

if user == none {
    return;
}

print user.name;
```

After the `none` branch exits, the compiler narrows `user` from `maybe User` to `User` in the remaining control-flow path.

The opposite form also narrows inside the branch:

```eri
if user != none {
    print user.name;
}
```

The compiler should perform this narrowing through ordinary control-flow analysis rather than requiring an unsafe unwrap operator.

### No ordinary null

`null` is not a normal Eristavi value and is not an alias for `none`.

The goal is that absence is always visible in the type system and must be handled before the contained value is used.

## 8. Error model — locked

Recoverable failures are typed and checked by the compiler.

A function that can fail declares the error type with `fails`:

```eri
function loadUser(id Int) returns User fails DatabaseError {
    ...
}
```

A caller must either handle the failure locally or propagate a compatible declared failure.

Unchecked exceptions are not the normal mechanism for application control flow in Eristavi.

### Absence and failure are different

`maybe` represents legitimate absence. `fails` represents an operation that did not complete successfully.

```eri
function findUser(id Int) returns maybe User
```

means the operation succeeds but a matching user may not exist.

```eri
function loadUser(id Int) returns User fails DatabaseError
```

means the operation is expected to produce a `User`, but the operation itself may fail.

Both may appear together:

```eri
function findUser(id Int) returns maybe User fails DatabaseError {
    ...
}
```

This means the operation may fail, and if it succeeds, the requested value may still be absent.

### Local handling — locked direction

The readable local handling form is:

```eri
let user be loadUser(1) else error {
    print error.message;
    return;
}
```

Inside the `else error` block, `error` is the typed failure value from the operation.

If the error block completes normally instead of exiting or producing a replacement value, the compiler must reject uses that would assume `user` was successfully initialized.

### Propagation — locked direction

`try` propagates a compatible checked error from the current function:

```eri
function showUser(id Int) fails DatabaseError {
    let user be try loadUser(id);
    print user.name;
}
```

A function may use `try` only when its own declared failure contract can represent the propagated error.

The compiler must verify propagation statically.

### Runtime defects

Programmer defects, violated compiler/runtime invariants, or unrecoverable runtime failures are separate from ordinary checked errors and are not required to appear in a function's `fails` contract.

The exact representation and reporting of fatal runtime defects remains an implementation decision.

### Error declarations

The exact syntax for defining custom error types and composing multiple error types is not yet locked. The checked-error semantics above do not depend on that surface syntax.

## 9. Fundamental types — working set

The early language should remain small. The working fundamental type set is:

- `Int`
- `Float`
- `Bool`
- `Text`

Additional numeric widths, `Byte`, decimal arithmetic, maps, sets, and other types should be added only when the implementation or real programs require them.

`maybe` is a type modifier for explicit absence, not a separate fundamental payload type.

## 10. Functions — working direction

Functions should have a single primary declaration form.

Current draft examples use:

```eri
function add(a Int, b Int) returns Int {
    return a + b;
}
```

Functions that can recoverably fail declare that contract with `fails`.

Parameter and return types may eventually be inferred where doing so remains clear and safe, but public API contracts may reasonably stay explicit.

## 11. Control flow — working set

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

## 12. Memory management — architectural direction

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

## 13. Standard library boundary

Capabilities such as text operations, sorting, JSON, networking, files, dates, and databases should normally be libraries rather than language keywords.

For example, operations such as:

```eri
text.words.count
text.reverse
items.sort
```

should be type/library behavior, not special grammar.

## 14. Compilation architecture — locked principle, implementation pending

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

## 15. Initial implementation scope

The first implementation should prove the language with a deliberately small feature set:

```eri
let x be 40;
let y be 2;

print x + y;
```

The first compiler milestone does not require generics, async/await, macros, reflection, multiple native backends, a package registry, or an advanced garbage collector.

## 16. Open decisions

The following must be decided deliberately before being treated as stable:

- explicit type-annotation syntax in all positions;
- explicit reference/identity syntax;
- explicit in-place parameter mutation syntax, if needed;
- custom error-type declaration syntax;
- composition of multiple possible checked error types;
- exact integer and overflow semantics;
- Unicode indexing semantics;
- generic abstraction model when inference alone is insufficient;
- module/import syntax;
- resource-management syntax;
- first native target backend;
- exact IR specification.

These open questions should be resolved from the design philosophy rather than by copying another language's syntax.
