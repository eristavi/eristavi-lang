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

### Deep-fixable types — locked

A `fixed` guarantee is transitive across the complete ordinary stored-value structure. A binding or field may be `fixed` only when its static type is **deep-fixable**: no reachable stored type position may contain `identity`.

This is valid because `Address` contains only ordinary value state:

```eri
type Address {
    city Text;
}

let fixed address be Address {
    city = "Paphos";
};
```

A type containing shared identity remains valid as an ordinary mutable value type:

```eri
type ViewModel {
    counter identity Counter;
}
```

but it cannot receive a deep `fixed` guarantee:

```eri
let fixed model be ViewModel {
    counter = sharedCounter;
}; // compile-time error
```

The rule is recursive. If `Account` contains `Session`, and `Session` contains `identity Counter`, then `Account` is also not deep-fixable. The same rule applies through optional and collection value positions; for example `maybe identity Counter` is not deep-fixable even when a particular runtime value is currently `none`.

A `fixed` field follows the same rule, so forms such as this are invalid:

```eri
type Model {
    fixed counter identity Counter; // compile-time error
}
```

Eristavi does not weaken `fixed` into shallow handle immutability, does not implicitly freeze other identity aliases, and does not silently snapshot or copy identity state. The compiler rejects the combination instead.

Deep-fixable is an internal compiler property, not additional source syntax.

See `FIXED_IMMUTABILITY.md` for the locked detailed model.

## 5. Fundamental values — locked where specified

The early fundamental set includes:

- `Int`
- `Float`
- `Bool`
- `Text`

### Int — locked

`Int` is a signed 64-bit integer on every target:

```text
-9223372036854775808 .. 9223372036854775807
```

Normal integer arithmetic is checked. Compile-time-known overflow is a compile-time error; runtime-dependent overflow and division by zero produce defined arithmetic faults. Ordinary `Int` arithmetic never silently wraps.

Signed integer division truncates toward zero. `%` is defined only for `Int` and computes the corresponding signed remainder, whose nonzero sign follows the dividend. Division or remainder by zero is an arithmetic fault. The signed-minimum / `-1` exceptional pair is treated as overflow for both `/` and `%` rather than inheriting target-specific behavior.

Arithmetic faults are runtime defects, not ordinary checked `fails` values.

See `INTEGER_REMAINDER.md` for the locked signed division and `%` model.

### Float — locked

`Float` is IEEE 754 binary64 on every supported target.

Ordinary floating-point operations and decimal-literal conversion use round-to-nearest, ties-to-even semantics.

`Float` preserves IEEE 754 positive and negative infinity, NaN, signed zero, and gradual underflow with subnormal values.

Floating-point division by zero follows IEEE behavior rather than producing the integer arithmetic fault used by `Int`.

Float comparisons follow IEEE rules. In particular:

```text
0.0 == -0.0    true
NaN == NaN     false
NaN != NaN     true
```

NaN payload bits are not part of ordinary Eristavi language semantics and may be canonicalized when needed for deterministic cross-target behavior.

Backends must not expose target-specific excess precision, unsafe fused-operation contraction, flush-to-zero modes, alternate rounding behavior, or other implementation details that would change an observable Eristavi result.

There is no implicit potentially lossy conversion between `Int` and `Float` in either direction.

`%` is not defined for `Float` in pre-0.1. Future floating-point remainder or modulo operations, if needed, belong to explicitly named numeric APIs with separately stated semantics.

See `FLOAT.md` for the locked detailed model and `LEXICAL_RULES.md` for floating-point literal syntax.

### Bool — locked core value

`Bool` has the two literal values:

```text
true
false
```

Boolean operators are `and`, `or`, and `not`.

`if` and `while` conditions must have static type `Bool`. Pre-0.1 defines no implicit truthiness for numbers, text, collections, optional values, identities, or other types.

See `CONDITIONS.md` for the locked condition-typing model.

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

The first concrete collection family is `List`.

A List is ordered, growable, homogeneous in its static element relationship, and an ordinary Eristavi value by default.

List literals use brackets:

```eri
let names be ["Anna", "Maria", "John"];
```

The compiler infers one coherent element type. Mixed incompatible elements do not silently widen to a dynamic type or implicit union, and the existing no-implicit-conversion rule means `Int` and `Float` do not silently mix inside one List.

An empty List literal may acquire its element relationship from statically analyzable use:

```eri
let customers be [];

customers.add(Customer {
    name = "Anna";
});
```

If the compiler cannot establish one element type, or if constraints conflict, compilation fails rather than creating an untyped List.

`List` is a predeclared type-family name, not a keyword. Pre-0.1 still exposes no user-written generic argument syntax such as `List<Text>`; the element relationship remains compiler-inferred.

List indexing is zero-based and requires an `Int` index:

```eri
output(names[0]);
```

Valid indexes satisfy `0 <= index < list.count`. Bounds are checked. A statically provable out-of-range index is a compile-time error; otherwise an invalid access produces a defined runtime bounds fault rather than `none`, wrapping, clamping, or a checked `fails` value. Negative indexes are out of bounds rather than from-end shorthand.

Every List exposes a read-only `.count` property of type `Int` and a canonical no-value `.add(value)` append operation:

```eri
names.add("John");
output(names.count);
```

Mutable Lists support indexed assignment and nested writable indexed paths:

```eri
numbers[1] = 25;
users[0].name = "Maria";
```

Assignment remains statement-level and does not become an expression.

Lists preserve ordinary value semantics. If one List is assigned to another ordinary binding, later mutation of one must not mutate the other. The implementation may use copy-on-write or other optimizations as long as this logical independence is preserved. Ordinary function parameters follow the same value rule.

A `fixed` List is deeply immutable and must satisfy the existing deep-fixable rule. A List whose element type contains reachable `identity` is therefore not eligible for `fixed`.

List equality is ordered structural equality when the element type is equality-comparable: equal Lists have equal counts and pairwise-equal corresponding elements.

`for` iteration traverses a List from index `0` upward in stored order and observes the logical List value present when iteration begins. Implementations need not eagerly copy the List if they can preserve that stable observable sequence.

Pre-0.1 deliberately postpones slicing, negative indexing, additional collection families, maps, sets, queues, linked lists, comprehensions, and similar facilities until real programs justify them.

Pre-0.1 also has no user-written generic parameter syntax such as `<T>`, `[T]`, `where`, trait bounds, or explicit generic arguments.

Functions may be implicitly generic when the compiler can infer consistent static relationships:

```eri
function identity(value) {
    return value;
}
```

The compiler may internally understand this as a same-type input/output relationship, but the internal type variable is not Eristavi source syntax.

If safe inference is impossible, compilation fails. Pre-0.1 requires a concrete implementation rather than an explicit generic escape hatch.

See `COLLECTIONS.md` and `GENERICS.md` for the locked detailed models.

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

### Ordinary value equality — locked

Ordinary user-defined values use structural, recursive, type-preserving equality.

Two ordinary values of the same compatible static type compare equal when every corresponding stored component compares equal under that component type's own equality semantics.

```eri
type User {
    id Int;
    name Text;
}

let first be User {
    id = 1;
    name = "Anna";
};

let second be User {
    id = 1;
    name = "Anna";
};

output(first == second); // true
```

Equality composes rather than reinterpreting component types. Nested ordinary values compare recursively; `identity T` fields compare by logical identity; `Float` retains IEEE equality including NaN behavior; `maybe T` compares absence/presence and then contained values; ordered collections compare by length and corresponding elements.

A type supports `==` / `!=` only when its complete stored value structure is equality-comparable. If a nested field type has no equality semantics, the containing ordinary value type does not automatically gain equality either.

Ordinary equality requires compatible static types. Unrelated user-defined types do not compare merely because they have the same field shape, and Eristavi performs no implicit numeric coercion such as `Int` to `Float` for equality.

Pre-0.1 defines no user-written equality overloading, `Equatable` protocol, or custom equality hook. Domain-specific equivalence uses ordinary clearly named functions instead of redefining `==`.

Because Float semantics are preserved compositionally, an ordinary value containing NaN may compare unequal to itself. Nesting does not silently change Float equality.

See `VALUE_EQUALITY.md` and `IDENTITY_EQUALITY.md` for the locked detailed models.

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
output(first.value);  // 10
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

No explicit identity-to-value snapshot operation is part of pre-0.1. Such an operation is deliberately postponed until a real use case justifies its semantics and API.

See `IDENTITY_EQUALITY.md`.

## 9. Optional values — locked

Eristavi has no ordinary `null` value.

Optional values use `maybe T`; absence uses `none`:

```eri
let user maybe User be none;
```

`none` is valid only where the expected or inferred type is `maybe ...`.

A `maybe` value must be proven present before member access. Ordinary checks participate in flow-sensitive narrowing:

```eri
if user == none {
    return;
}

output(user.name);
```

When `T` is equality-comparable, `maybe T` is equality-comparable: two absent values are equal, absent and present values are unequal, and two present values compare their contained `T` values.

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
    output(error.message);
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
    output(user.name);
}
```

`maybe` and `fails` remain distinct: absence is not failure.

Eristavi pre-0.1 has no exception inheritance, `throw`, or `catch` model for ordinary recoverable failures.

See `ERRORS.md`.

## 11. Modules, visibility, and entry execution — locked

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

Third-party package root naming, dependency resolution, versioning, and package-registry behavior are deliberately postponed beyond pre-0.1. Project-local source-root modules and the reserved `std` root are sufficient for the initial compiler.

### Entrypoint and top-level execution — locked

An executable run/build operation selects exactly one `.eri` source file explicitly as the entry module. Eristavi does not require a magic `main` function, a reserved `main` identifier, or a required `main.eri` filename.

The selected entry module has the conceptual order:

```text
imports
module declarations
entry executable statements
```

Imports must come first. Module declarations such as functions, types, and errors come before entry executable statements. Once top-level execution begins, a later module declaration is invalid.

The entry executable statements form an implicit no-value execution body and execute in source order. Top-level executable `let` / `fixed` bindings are local to that entry execution body: they are not module members, cannot be imported, and are not implicitly visible inside module-level functions or types.

Imported modules are declaration-only. A module used through `import` may contain imports and module declarations but may not contain top-level executable statements. Importing a module therefore does not run arbitrary initialization code or create hidden runtime side effects.

A file that contains top-level executable statements may serve as an explicitly selected entry file, but it cannot simultaneously be imported as a reusable module in that program.

Module declarations remain order-independent within their declaration region. Entry-local executable bindings use ordinary declaration-before-use, lexical-scope, redeclaration, and no-shadowing rules.

`return` is invalid at file scope. The implicit entry body has no `fails` contract, so a top-level checked `fail` is invalid and `try` cannot propagate a checked failure beyond the entry boundary. Checked failures at that boundary must be handled exhaustively.

Normal fallthrough from the final reachable entry statement means normal program completion. Host-specific process exit status mapping is a backend/runtime concern rather than entrypoint syntax.

Reusable declaration-only modules may be parsed, type-checked, or compiled without selecting an entry source file. An entry is required only for a toolchain operation that needs executable program start.

See `ENTRYPOINT.md` and `GRAMMAR.md` for the locked detailed model.

### Standard textual output — locked

Simple program output uses the ordinary call:

```eri
output("Hello");
```

`output` is a predeclared standard-library/prelude function available without an explicit import. It is not a keyword and introduces no output-specific grammar.

Pre-0.1 defines `output` as the single canonical simple textual-output name; `print`, `echo`, `say`, and `out` are not aliases.

The canonical pre-0.1 form takes one value, writes its human-readable textual representation to standard textual output, and terminates the output with a line break. The bootstrap must support the core value types needed by early programs.

See `OUTPUT.md` for the locked detailed model.

## 12. Function behavior — locked for pre-0.1

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

### Function result and completion — locked

`returns T` is optional when the compiler can infer a single static result type from the function body.

```eri
function double(value Int) {
    return value * 2;
}
```

is inferred to produce `Int`.

A function with no explicit `returns T` and no `return expression;` statements is a no-value function. Pre-0.1 defines no programmer-visible `Void`, `void`, `Unit`, or equivalent type merely for this case.

A no-value function may reach its closing `}` normally or exit early with `return;`. A bare `return;` is invalid in a value-producing function.

A function cannot mix bare `return;` and `return expression;` completion.

Every reachable path that can complete successfully in a value-producing function must return a compatible value. Eristavi does not invent an implicit missing/undefined result when such a path reaches the closing `}`.

Multiple inferred return expressions must establish one compatible static result type. The compiler does not silently create a dynamic or union result type to reconcile incompatible returns.

A checked `fail` terminates its path and therefore does not require a successful return on that path.

`return none;` returns the actual absence value of a `maybe T` result and is not equivalent to bare `return;`.

When value-result inference is directly or indirectly circular, including recursive or mutually recursive result inference, an explicit `returns T` contract is required. Recursion itself remains fully allowed.

A no-value function call cannot be used in a value context.

See `FUNCTION_RETURNS.md` for the locked detailed result/completion model and `VALUE_PARAMETER_MUTATION.md` for ordinary parameter behavior.

## 13. Control flow and expression ordering — locked core

The initial language uses:

- `if` / `else`
- `for` / `in`
- `while`
- `return`

Boolean operators are:

```text
and
or
not
```

The symbolic Boolean aliases `&&`, `||`, and `!` are not part of Eristavi.

Expression precedence is locked from highest to lowest as:

```text
call / index / member access
unary - / try / identity
* / / / %
+ / -
comparisons
not
and
or
```

Comparisons are non-associative, so chained forms such as `10 < age < 65` are invalid. `not a == b` means `not (a == b)`. `and` binds more strongly than `or`.

Assignment `=` is not an expression operator. Assignment is statement-level syntax and does not produce a value, so forms such as `a = b = c` or `let value be (a = b);` are invalid. Writable assignment paths may include member and List-index segments, such as `users[0].name = "Maria";`, subject to mutability, type, and bounds checks.

### Condition typing — locked

`if` and `while` require conditions of static type `Bool`.

Eristavi does not define general truthiness. `Int`, `Float`, `Text`, collections, `maybe T`, `identity T`, and arbitrary user-defined values do not implicitly become Boolean conditions.

The programmer asks the intended Boolean question explicitly:

```eri
if count != 0 {
    ...
}

if user != none {
    ...
}
```

See `CONDITIONS.md` for the locked detailed model.

### Scope and declaration resolution — locked

Every `{ ... }` block creates a lexical scope. Local bindings are visible only after their declaration has completed and are not visible inside their own initializer.

Same-scope redeclaration is a compile-time error. Pre-0.1 also forbids local shadowing: an inner local, loop binding, resource binding, or handler binding may not reuse an already-visible local or parameter name.

Function parameters belong to the function's local namespace and must be unique. Separate functions may freely reuse local and parameter names because they have independent scopes.

Module-level functions, types, errors, and other ordinary declarations must have unique names in their module; duplicate names are compile-time errors rather than overloads. Module-level declarations are resolved across the complete declaration region and are therefore order-independent, unlike local bindings.

Entry-local executable bindings are not module declarations and do not become hidden globals merely because they appear at file scope in the selected entry file.

See `SCOPE.md` for the locked detailed model.

See `PRECEDENCE.md`, `OPERATORS.md`, `GRAMMAR.md`, and `COLLECTIONS.md` for expression ordering, assignment, and List indexing semantics.

## 14. Resource management — locked

Memory management and external-resource lifetime are separate concerns.

Deterministic resources use `with`:

```eri
with file be try files.open("data.txt") {
    let text be try file.readText();
    output(text);
}
```

A resource owned by a `with` block is released exactly once when that block is left through ordinary language-level control flow, including normal fallthrough, `return`, and checked-error propagation.

Resource handles are single-owner while governed by `with`. They cannot be implicitly copied or silently escape their owning scope.

Nested resources clean up in reverse nesting order.

A deterministic resource cannot be wrapped in `identity` to bypass resource ownership rules.

A deterministic resource type has a statically known cleanup-failure contract, which may be empty. Cleanup error types participate in ordinary checked-failure analysis for the enclosing function.

If cleanup fails while no checked failure is already active, the cleanup failure becomes the primary checked failure and prevents otherwise successful fallthrough or return.

If a checked failure is already propagating from the body, that original failure remains primary. Any cleanup failure is preserved as secondary cleanup failure context rather than replacing or silently discarding the primary failure. With nested resources, cleanup remains reverse-order; the first cleanup failure becomes primary only when no prior failure was active, and later cleanup failures become secondary context.

Secondary cleanup context does not introduce a new source-level union or wrapper error type. The ordinary `error` binding continues to denote the primary typed error. Pre-0.1 does not expose a programmatic API for enumerating secondary cleanup failures, but compiler/runtime implementations must preserve them for diagnostics and failure reporting while the propagation context is active.

The selected entry execution body has no `fails` contract, so a top-level `with` whose cleanup may produce an unhandled checked failure is invalid at that boundary under the same checked-error rules as any other failure source.

Pre-0.1 does not expose lifetime annotations, manual reference counting, manual `free`, general borrowing syntax, ownership-transfer syntax, or a multi-resource `with` header. Advanced transfer and borrowing are deliberately postponed until real programs justify them.

See `RESOURCE_CLEANUP.md` for the locked cleanup and dual-failure model.

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

The bootstrap should begin with a small executable subset containing basic literals, bindings, arithmetic, names, functions, returns, output, and diagnostics, then grow toward the frozen pre-0.1 surface.

A minimal early program is an entry source file such as:

```eri
let x be 40;
let y be 2;

output(x + y);
```

The project deliberately postpones advanced concurrency, async/await, reflection, macros, pattern matching, explicit generic syntax, advanced GC, package registry work, identity snapshots, advanced resource transfer/borrowing, self-hosting, and multiple native CPU backends until the core compiler is proven or real programs demonstrate the need.

## 18. Deliberately postponed and architectural decisions

The following are not part of the pre-0.1 semantic freeze and do not block frontend implementation:

- explicit extraction of an independent `T` snapshot from `identity T`;
- third-party package root naming, dependency resolution, versioning, and registry behavior;
- advanced resource ownership transfer / borrowing;
- first native CPU backend;
- exact Eristavi IR instruction set and representation;
- stable portable bytecode/runtime format, if one is later needed in addition to the defined target set.

These questions must be decided later from real implementation or program needs and Eristavi's design philosophy rather than copied automatically from another language.
