# Eristavi Language Semantics

> **Status: Consolidated pre-0.1 semantics**
>
> This document is the master semantic summary for Eristavi pre-0.1. Dedicated locked documents may provide additional detail, but they must not contradict this file.

## 1. Project identity — locked

- Language: **Eristavi**
- Primary source extension: **`.eri`**
- Reserved extension: **`.erist`**
- CLI / toolchain command: **`erist`**
- Official website: **eristavi.org**
- Repository: **eristavi/eristavi-lang**

## 2. Governing philosophy — locked

Eristavi is a general-purpose language centered on:

- readability without pseudo-English verbosity;
- one obvious form for fundamental concepts;
- strong static typing with aggressive inference;
- native performance and machine-independent semantics;
- automatic memory management for ordinary values;
- deterministic scoped cleanup for external resources;
- a small language vocabulary with capability pushed into libraries;
- excellent diagnostics and inspectable compiler behavior.

The governing principle is:

> **Small language. Rich libraries. Powerful compiler. Predictable runtime. Universal architecture.**

Design order remains:

> **Philosophy → Semantics → Architecture → Implementation**

## 3. Type inference and annotations — locked

Eristavi infers types where the relationship is statically clear:

```eri
let age be 44;
let name be "Anna";
```

Explicit named annotations use name-first order with no colon:

```eri
let age Int be 44;
let name Text be "Anna";
let user maybe User be none;
```

The same order is used by parameters and fields:

```eri
function greet(name Text) {
    ...
}

type User {
    fixed id Int;
    name Text;
}
```

The design rule is:

> A name comes first; its explicit type follows it.

## 4. Variables and immutability — locked

`let` introduces a mutable binding:

```eri
let price be 50;
price = 60;
```

`fixed` makes the complete bound ordinary value immutable after initialization:

```eri
let fixed taxRate Float be 0.19;
```

For ordinary values, `fixed` is deep from the programmer's point of view:

```eri
let fixed user be User {
    id = 1;
    name = "Anna";
};

user.name = "Maria";  // compile-time error
user = anotherUser;    // compile-time error
```

Fields use the same modifier:

```eri
type User {
    fixed id Int;
    name Text;
}
```

A `fixed` field is initialized once and cannot be reassigned afterward.

A `fixed` binding whose value has an `identity` type is invalid in pre-0.1 because `fixed` means deep immutability rather than shallow handle immutability.

## 5. Fundamental values — locked where specified

The early working set includes:

- `Int`
- `Float`
- `Bool`
- `Text`

`Float` exists in the working set, but its exact numeric semantics are not yet frozen.

### Int — locked

`Int` is a signed 64-bit integer on every target:

```text
-9223372036854775808 .. 9223372036854775807
```

Normal integer arithmetic is checked. Compile-time-known overflow is a compile-time error; runtime-dependent overflow and division by zero produce defined arithmetic faults. Ordinary `Int` arithmetic never silently wraps.

Arithmetic faults are runtime defects, not ordinary checked `fails` values.

### Text and Unicode — locked

`Text` is valid Unicode with UTF-8 as its canonical byte representation.

Direct integer indexing is intentionally undefined:

```eri
text[0]  // compile-time error
```

The programmer selects the intended view explicitly:

```eri
text.characters[0]
text.scalars[0]
text.bytes[0]
```

`characters` means Unicode extended grapheme clusters, `scalars` means Unicode scalar values, and `bytes` means UTF-8 bytes.

Counts are likewise explicit:

```eri
text.characters.count
text.scalars.count
text.bytes.count
```

There is no ambiguous bare `text.length` in the core Text model.

Text equality compares the actual Unicode scalar sequence. Eristavi does not silently normalize text. Invalid UTF-8 must not silently become `Text`.

## 6. Collections and inferred generic abstraction — locked for pre-0.1

Collection element types are inferred where possible:

```eri
let names be ["Anna", "Maria", "John"];
```

An initially empty collection may acquire its element relationship from statically analyzable use. Conflicting uses are compile-time errors rather than a fallback to dynamic typing.

Pre-0.1 has no user-written generic parameter syntax such as `<T>`, `[T]`, `where`, trait bounds, or explicit generic arguments.

Functions may be implicitly generic when the compiler can infer consistent static relationships:

```eri
function identity(value) {
    return value;
}
```

The compiler may internally understand this as a same-type input/output relationship, but the internal type variable is not Eristavi source syntax.

If safe inference is impossible, compilation fails. Pre-0.1 requires a concrete implementation rather than an explicit generic escape hatch.

See `GENERICS.md` for the locked model.

## 7. User-defined value types and construction — locked

Ordinary user-defined `type` values have value semantics by default:

```eri
type User {
    fixed id Int;
    name Text;
}
```

Assignment creates an independent logical value:

```eri
let a be user;
let b be a;
b.name = "Maria";
```

Changing `b` must not change `a`.

The implementation may use copy elision, shared backing storage, copy-on-write, escape analysis, or destructive optimization as long as observable behavior remains value-based.

### Direct construction — locked

Eristavi uses one named-field construction form:

```eri
let user be User {
    id = 1;
    name = "Anna";
};
```

For direct construction in pre-0.1:

- every declared field is required;
- every field is initialized exactly once;
- unknown fields are compile-time errors;
- duplicate fields are compile-time errors;
- declaration order does not become a positional call contract;
- positional construction and colon-based construction are not supported;
- default field values and automatic omission are not part of pre-0.1.

When construction needs validation, calculation, or checked failure, an ordinary function returns the value.

See `CONSTRUCTION.md`.

## 8. Explicit identity — locked

Shared logical identity is explicit in the type:

```eri
identity Counter
```

An identity is created explicitly from an eligible ordinary non-resource value:

```eri
type Counter {
    value Int;
}

let counter be identity Counter {
    value = 0;
};
```

There is no implicit conversion between `T` and `identity T`.

Assignment of an identity handle preserves the same logical identity:

```eri
let first be counter;
let second be first;
second.value = 10;
print first.value;  // 10
```

Identity is automatically memory-managed. It is not a raw pointer, does not expose an address, and does not imply thread safety, atomicity, or resource ownership.

Optional identity uses the single canonical order:

```eri
maybe identity Counter
```

`identity maybe Counter` is not an alternate spelling.

### Identity equality — locked

For `identity T`, `==` means the same logical identity and `!=` means a different logical identity.

Two independently created identities remain unequal even when all fields currently contain equal data.

Identity equality is not physical-address equality, and `T` does not implicitly compare with `identity T`.

See `IDENTITY_EQUALITY.md`.

## 9. Optional values — locked

Eristavi has no ordinary `null` value.

Optional values use `maybe T`; absence uses `none`:

```eri
let user maybe User be none;
```

`none` is valid only in a `maybe` context or where inference establishes such a context.

A `maybe` value must be proven present before member access. Ordinary checks participate in flow-sensitive narrowing:

```eri
if user == none {
    return;
}

print user.name;
```

No unsafe unwrap operator is required for normal control flow.

`maybe` means legitimate absence, not failure.

## 10. Checked errors — locked

Recoverable failures are typed and checked.

Custom checked errors are data declarations:

```eri
error DatabaseError {
    message Text;
    code Int;
}
```

Every checked error type in pre-0.1 must declare exactly one `message Text` field. Additional typed fields are allowed.

An error is produced with `fail`:

```eri
fail DatabaseError {
    message = "Database unavailable";
    code = 503;
};
```

Functions declare checked failures with `fails`. Multiple error types use a comma-separated contract:

```eri
function loadUser(id Int)
    returns User
    fails DatabaseError, DecodeError
{
    ...
}
```

A caller must handle or propagate all possible checked failures.

Catch-all handling:

```eri
let user be loadUser(1) else error {
    print error.message;
    return;
};
```

Typed exhaustive handling:

```eri
let user be loadUser(1)
else error DatabaseError {
    return;
}
else error DecodeError {
    return;
};
```

Propagation uses `try` and is checked against the surrounding function's own `fails` contract:

```eri
function showUser(id Int) fails DatabaseError, DecodeError {
    let user be try loadUser(id);
    print user.name;
}
```

`maybe` and `fails` remain distinct: absence is not failure.

Eristavi pre-0.1 has no exception inheritance, `throw`, or `catch` model for ordinary recoverable failures.

See `ERRORS.md`.

## 11. Modules and visibility — locked

One `.eri` file is one module. Its logical path is derived from its path under the configured source root.

There is no separate module declaration.

Imports use dotted logical paths:

```eri
import models.user;
import services.auth;
```

The imported namespace is the final path segment unless explicitly aliased:

```eri
import models.user as customer;
```

Imported names stay qualified by default. Wildcard imports, selective unqualified imports, quoted project paths, and `../` traversal imports are not part of pre-0.1.

Top-level declarations are private by default. `public` exposes a declaration through the module namespace:

```eri
public type User {
    id Int;
}
```

The top-level namespace `std` is reserved for the standard library.

Circular module dependencies are compile-time errors in the initial language.

Third-party package root naming and dependency resolution remain open.

## 12. Function parameter behavior — locked for pre-0.1

Ordinary parameters use value semantics. They cannot directly mutate caller-owned ordinary values.

```eri
function rename(user User, name Text) returns User {
    user.name = name;
    return user;
}
```

Caller-visible changes are returned explicitly:

```eri
user = rename(user, "Maria");
```

Pre-0.1 has no `ref`, `mut`, `inout`, `&`, or equivalent in-place ordinary value parameter feature.

Shared observable mutation remains explicit through `identity T` parameters.

The compiler may optimize physical copying away when value semantics remain observationally intact.

See `VALUE_PARAMETER_MUTATION.md`.

## 13. Control flow — initial set

The initial language uses:

- `if` / `else`
- `for` / `in`
- `while`
- `return`

Boolean operators are locked as:

```text
and
or
not
```

The symbolic Boolean aliases `&&`, `||`, and `!` are not part of Eristavi.

## 14. Resource management — locked

Memory management and external-resource lifetime are separate concerns.

Deterministic resources use `with`:

```eri
with file be try files.open("data.txt") {
    let text be try file.readText();
    print text;
}
```

A resource owned by a `with` block is released exactly once when that block is left through ordinary language-level control flow, including normal fallthrough, `return`, and checked-error propagation.

Resource handles are single-owner while governed by `with`. They cannot be implicitly copied or silently escape their owning scope.

Nested resources clean up in reverse nesting order.

A deterministic resource cannot be wrapped in `identity` to bypass resource ownership rules.

Pre-0.1 does not expose lifetime annotations, manual reference counting, manual `free`, general borrowing syntax, or a multi-resource `with` header.

Cleanup-failure composition when another checked failure is already active remains open.

## 15. Memory management — architectural direction

Ordinary Eristavi code does not manually allocate and free general-purpose memory.

The compiler/runtime may use registers, stack allocation, escape analysis, object elimination, managed heap allocation, and garbage collection as appropriate.

The first collector should favor correctness and implementation clarity over advanced optimization.

GC is not the semantic mechanism for releasing external resources.

## 16. Compilation architecture and targets — locked direction

Compilation centers on an Eristavi-owned machine-independent IR:

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

The long-term target set is deliberately narrow:

- native machine code;
- C source;
- JavaScript;
- WebAssembly.

The governing target rule is:

> Target platforms implement Eristavi semantics; they do not redefine them.

Rust, Go, and PHP source-generation backends are not planned targets.

See `TARGETS.md`.

## 17. Pre-0.1 implementation scope

The first compiler does not need to implement every already-defined semantic feature immediately.

The bootstrap should begin with a small executable subset containing basic literals, bindings, arithmetic, names, functions, returns, and diagnostics, then grow toward the frozen pre-0.1 surface.

A minimal early program remains:

```eri
let x be 40;
let y be 2;

print x + y;
```

The project deliberately postpones advanced concurrency, async/await, reflection, macros, pattern matching, explicit generic syntax, advanced GC, package registry work, self-hosting, and multiple native CPU backends until the core compiler is proven.

## 18. Remaining open decisions

The following are still deliberately unresolved and should not block the first frontend bootstrap unless implementation requires them:

- exact `Float` semantics;
- full operator precedence table beyond already-established relationships;
- general equality rules for ordinary user-defined value types;
- explicit extraction of an independent `T` snapshot from `identity T`, if needed;
- third-party package root naming and dependency resolution;
- cleanup-failure composition when another checked failure is already active;
- advanced resource ownership transfer / borrowing, if real programs require it;
- classification of bootstrap `print` as keyword, intrinsic, or standard-library function;
- first native CPU backend;
- exact Eristavi IR instruction set and representation;
- stable portable bytecode/runtime format, if one is later needed in addition to the defined target set.

These questions must be resolved from Eristavi's design philosophy rather than copied automatically from another language.
