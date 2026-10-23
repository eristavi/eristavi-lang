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

### Explicit type annotations — locked

When an explicit type is written for a named value, Eristavi uses the readable form:

```text
name Type
```

No colon separates the name from its type.

Variable declarations may therefore rely on inference:

```eri
let age be 44;
let name be "Anna";
```

or state the type explicitly:

```eri
let age Int be 44;
let name Text be "Anna";
let user maybe User be none;
```

The same order is used consistently for parameters and fields:

```eri
function greet(name Text) {
    ...
}

type User {
    fixed id Int;
    name Text;
    middleName maybe Text;
}
```

`fixed` remains a modifier on the binding or field, not part of the type itself:

```eri
let fixed taxRate Float be 0.19;
```

The design rule is:

> A name comes first; its explicit type follows it.

Type inference remains the default for local values, so explicit annotations should be used where they clarify intent, establish a contract, or are required for inference.

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

### Integer semantics — locked

`Int` is a signed 64-bit integer on every supported target. Its semantic range is:

```text
-9223372036854775808 .. 9223372036854775807
```

The width of `Int` is therefore independent of CPU architecture and operating system. Eristavi code must not observe `Int` becoming 32-bit on one target and 64-bit on another.

An integer literal is inferred as `Int` when its value is within the `Int` range and no other explicit numeric type is required by context.

Normal integer arithmetic is checked. Operations such as addition, subtraction, multiplication, negation, and division must not silently wrap when the mathematical result is outside the `Int` range.

For expressions whose result is known at compile time, overflow is a compile-time error:

```eri
let x Int be 9223372036854775807 + 1;  // compile-time error
```

For overflow that depends on runtime values, normal arithmetic produces a defined runtime arithmetic fault rather than wrapping or producing architecture-dependent behavior.

Division by zero is likewise rejected at compile time when provable, and otherwise produces a defined runtime arithmetic fault.

The signed division overflow case `-9223372036854775808 / -1` follows the same checked-overflow rule.

Arithmetic faults are runtime defects rather than ordinary recoverable `fails` values, because making every basic arithmetic operator participate in checked-error propagation would make ordinary numerical code unnecessarily noisy.

Programs that intentionally need wrapping, saturating, or explicitly checked arithmetic may use dedicated opt-in operations in the standard library or a future numeric API. The exact names and surface syntax for those operations are not yet locked.

Additional fixed-width signed or unsigned integer types may be added later when real systems-programming, binary-format, FFI, or performance use cases require them. They do not change the portable semantics of `Int`.

### Text and Unicode semantics — locked

`Text` represents valid Unicode text. Eristavi source files and the canonical byte representation of `Text` use UTF-8.

A `Text` value is not treated as an array of bytes. Human-visible characters, Unicode scalar values, and UTF-8 bytes are distinct views and must be requested explicitly.

Eristavi therefore does **not** allow ambiguous direct integer indexing of `Text`:

```eri
let text be "Hello";
let first be text[0];       // compile-time error
```

Instead, the programmer chooses the intended view:

```eri
let firstCharacter be text.characters[0];
let firstScalar be text.scalars[0];
let firstByte be text.bytes[0];
```

`text.characters` is segmented into Unicode extended grapheme clusters and is the default human-facing character view. This means an emoji sequence or a letter plus combining marks can behave as one visible character where Unicode defines it as one grapheme cluster.

`text.scalars` exposes Unicode scalar values for code-point-level processing.

`text.bytes` exposes the UTF-8 encoded bytes for binary protocols, hashing, FFI, storage formats, and other byte-oriented work.

Counts are equally explicit:

```eri
text.characters.count
text.scalars.count
text.bytes.count
```

Eristavi should not define a bare `text.length` whose meaning could be mistaken for any of these three counts.

Character-oriented standard-library operations should operate on grapheme clusters unless their API explicitly says otherwise. Byte-oriented and scalar-oriented operations must remain explicit.

Text equality compares the actual Unicode scalar sequence. Eristavi does not silently normalize Unicode during assignment, comparison, hashing, or storage. Canonically equivalent spellings therefore remain distinct unless the programmer explicitly normalizes them through the standard library.

Invalid UTF-8 received from files, networks, FFI, or other byte sources must not silently become `Text`. Decoding invalid bytes must fail through the checked error model unless the programmer deliberately chooses an explicit replacement/lossy decoding operation.

The compiler/runtime should pin a Unicode data version for each Eristavi toolchain release so grapheme segmentation and Unicode properties are deterministic for that release.

The implementation may cache boundaries or use other optimizations, but the language does not promise constant-time random indexing into grapheme clusters or Unicode scalars. Performance-sensitive code should be able to iterate these views without accidental repeated rescanning.

The design rule is:

> Text is Unicode. Characters, scalars, and bytes are different things, and Eristavi makes that difference visible.

## 10. Modules and imports — locked

Eristavi uses a file-and-folder based module system.

Each `.eri` source file is one module. Its logical module path is derived from its path under the project's source root, so source files do not repeat their own module name with a separate declaration.

For example:

```text
src/
    main.eri
    models/
        user.eri
    services/
        auth.eri
```

corresponds to the module paths:

```text
main
models.user
services.auth
```

### Import form

Modules are imported explicitly with `import`:

```eri
import models.user;
import services.auth;
```

An import creates a module namespace using the final segment of the module path:

```eri
let account be user.User(...);
let session be auth.login(account);
```

Imported declarations are therefore qualified by default. Importing a module does not inject all of its names into the current module's local scope.

This keeps dependencies visible at the use site and avoids accidental name collisions.

### Aliases

When the default namespace would collide or be unclear, an import may use an explicit alias:

```eri
import models.user as customer;

let account be customer.User(...);
```

An alias changes only the local namespace name. It does not rename the module itself.

### Visibility

Top-level declarations are private to their defining module by default.

A declaration intended to be part of the module's external API is marked `public`:

```eri
public type User {
    fixed id Int;
    name Text;
}

public function find(id Int) returns maybe User {
    ...
}
```

Only public declarations are accessible through an imported module namespace.

Eristavi does not use a separate `export` list for the ordinary module model. Visibility is attached directly to the declaration it describes.

### One obvious import model

The initial language deliberately does not provide wildcard imports or selective unqualified imports such as `import *`, `from x import y`, or equivalent forms.

The normal model is:

```eri
import services.auth;

auth.login(user);
```

This preserves one clear relationship between an import and the names it introduces.

### Module paths

Module paths use identifiers separated by dots. They are logical source paths, not quoted filesystem paths.

Eristavi source therefore does not import project modules using strings such as `"../models/user.eri"`.

The compiler resolves project modules relative to the configured project source root. This keeps source imports portable across operating systems and directory separators.

The `std` top-level namespace is reserved for Eristavi standard-library modules, for example:

```eri
import std.files;
import std.json;
```

Fundamental language types and syntax do not require an import merely to exist. Additional library capabilities should normally live behind explicit standard-library modules.

### Cycles

Circular module dependencies are compile-time errors in the initial language.

This keeps initialization and dependency ordering deterministic while the module system remains small. A future need for more advanced cyclic type relationships should be solved deliberately rather than by allowing arbitrary import cycles.

### Dependency packages

The module semantics above are independent of a future package manager. The exact naming and resolution rules for third-party package roots are not yet locked.

The design rule is:

> One file is one module. Imports are explicit. Imported names stay qualified. Public API is explicit.

## 11. Functions — working direction

Functions should have a single primary declaration form.

Current draft examples use:

```eri
function add(a Int, b Int) returns Int {
    return a + b;
}
```

Functions that can recoverably fail declare that contract with `fails`.

Parameter and return types may eventually be inferred where doing so remains clear and safe, but public API contracts may reasonably stay explicit.

## 12. Control flow — working set

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

## 13. Memory management — architectural direction

Ordinary Eristavi code should not manually allocate and free general-purpose memory.

The compiler/runtime should be free to use:

- registers;
- stack allocation;
- escape analysis;
- object elimination;
- managed heap allocation;
- garbage collection.

The first collector should favor correctness and implementation clarity over advanced optimization.

Memory management and external-resource management are deliberately separate concerns. Garbage collection may manage memory, but files, sockets, database connections, locks, transactions, and similar resources require deterministic release.

## 14. Resource management — locked

Eristavi uses deterministic scoped cleanup for resources whose lifetime must not depend on garbage collection.

The primary construct is `with`:

```eri
with file be try files.open("users.txt") {
    let text be try file.readText();
    print text;
}
```

The expression after `be` must produce a resource value. The binding introduced by `with` exists only inside the block.

The semantic rule is:

> A resource acquired by `with` is owned by that block and is released exactly once when the block is left.

### Cleanup on every ordinary exit path

Cleanup must run when control leaves the block normally and when it leaves through language-level control flow such as `return` or checked-error propagation.

```eri
with file be try files.open("users.txt") {
    if file.empty {
        return;
    }

    process(file);
}
```

The resource is released before the `return` completes.

Likewise:

```eri
function load() returns Text fails FileError {
    with file be try files.open("data.txt") {
        return try file.readText();
    }
}
```

The resource is released before the value or propagated checked error leaves the scope.

If future control-flow constructs such as `break` or `continue` leave a resource scope, the same deterministic cleanup rule applies.

A process-level abort, operating-system termination, power loss, or other event that prevents language-level cleanup from executing is outside this guarantee.

### Resource ownership

Resource handles are not ordinary freely copyable values.

A resource acquired by `with` has one compiler-tracked owner for the duration of that scope. Eristavi must prevent accidental duplication that could create multiple independent owners of the same underlying resource.

For example, this must not silently create a second owner:

```eri
with file be try files.open("data.txt") {
    let another be file;   // invalid as an implicit resource copy
}
```

The compiler should diagnose an attempted implicit resource copy rather than allow double cleanup or unclear ownership.

Resource ownership is a semantic property distinct from ordinary value semantics. Ordinary user-defined values remain value-based; only values whose type represents a deterministically managed resource receive this single-owner behavior.

### No lifetime annotations in ordinary code

The compiler is responsible for tracking the scoped lifetime created by `with`. Ordinary programmers should not need borrow annotations, explicit lifetime parameters, manual reference counts, or `free` operations to use files, sockets, database connections, locks, or similar resources safely.

Advanced ownership transfer or borrowing may be added later if real programs require it, but it must be explicit and must not complicate the basic `with` model.

### Nested resources

Multiple resources may be represented by nested `with` blocks:

```eri
with connection be try database.connect() {
    with transaction be try connection.transaction() {
        ...
    }
}
```

Resources are released in reverse nesting order: the inner resource is released before the outer resource.

The initial language does not need separate syntax for acquiring several resources in one `with` statement.

### Resource escape

A resource owned by a `with` block cannot silently escape that block through assignment, return, collection storage, or capture if doing so would outlive the owning scope.

The compiler must reject such escapes unless a future explicit ownership-transfer mechanism makes the new owner unambiguous.

This keeps basic resource safety enforceable without exposing lifetime syntax.

### Cleanup failures

Cleanup is part of the resource contract and must not be silently ignored. The exact surface semantics for composing a cleanup failure with an already-active checked failure remain open so the initial language does not prematurely add a complex dual-error model.

Whatever representation is chosen later must preserve deterministic cleanup and must never silently discard a recoverable cleanup failure.

### Garbage collection is not resource cleanup

Garbage collection may reclaim memory associated with a resource object, but it is not the semantic mechanism for releasing the external resource itself.

A program must not depend on an eventual garbage-collection cycle to close a file, release a lock, end a transaction, or close a network connection.

The design rule is:

> Memory is managed automatically. External resources are managed deterministically by scope.

## 15. Standard library boundary

Capabilities such as text operations, sorting, JSON, networking, files, dates, and databases should normally be libraries rather than language keywords.

For example, operations such as:

```eri
text.words.count
text.reverse
items.sort
```

should be type/library behavior, not special grammar.

Resource-producing library APIs should integrate with the `with` model rather than requiring ad-hoc manual cleanup patterns.

## 16. Compilation architecture — locked principle, implementation pending

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

## 17. Initial implementation scope

The first implementation should prove the language with a deliberately small feature set:

```eri
let x be 40;
let y be 2;

print x + y;
```

The first compiler milestone does not require generics, async/await, macros, reflection, multiple native backends, a package registry, or an advanced garbage collector.

Resource semantics may be implemented after the smallest expression/function subset works, but their language-level behavior is already defined by the `with` model above.

## 18. Open decisions

The following must be decided deliberately before being treated as stable:

- explicit reference/identity syntax;
- explicit in-place parameter mutation syntax, if needed;
- custom error-type declaration syntax;
- composition of multiple possible checked error types;
- generic abstraction model when inference alone is insufficient;
- third-party package root naming and dependency resolution;
- advanced resource ownership transfer / borrowing semantics, if needed;
- cleanup-failure composition when another checked failure is already active;
- first native target backend;
- exact IR specification.

These open questions should be resolved from the design philosophy rather than by copying another language's syntax.
