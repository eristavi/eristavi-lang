# Eristavi Draft Grammar

> **Status: Draft / pre-0.1**
>
> This file describes the smallest surface grammar needed to bootstrap the first compiler. It is intentionally incomplete. Syntax that has not been explicitly settled should not be treated as permanent.

## Goals

The first grammar should be:

- small;
- deterministic;
- easy to parse;
- readable;
- free of redundant forms;
- easy to extend without breaking existing meaning.

## 1. Variable declaration

Locked binding forms:

```eri
let name be expression;
let name Type be expression;
let fixed name be expression;
let fixed name Type be expression;
```

`let` introduces a mutable binding by default. `fixed` makes that binding immutable after initialization.

Examples:

```eri
let age be 44;
let age Int be 44;
let name Text be "Anna";
let values be [10, 20, 30];
let user maybe User be none;

let fixed taxRate Float be 0.19;
```

Identity handles use the same annotation position when written explicitly:

```eri
let counter identity Counter be identity Counter {
    value = 0;
};
```

Grammar:

```text
variable-declaration :=
    "let" [ "fixed" ] identifier [ type-expression ] "be" expression ";"
```

Explicit annotations use the same name-first form used by parameters and fields: `name Type`. Colon-based annotation syntax is not part of this grammar.

A `fixed` binding whose inferred or explicit type is `identity ...` is invalid in the initial language because `fixed` promises deep immutability rather than merely preventing handle rebinding.

## 2. Literals

Initial literal forms:

```text
integer
float
text
true
false
none
list literal
```

Examples:

```eri
42
19.95
"Hello"
true
false
none
[1, 2, 3]
[]
```

Draft grammar:

```text
list-literal := "[" [ expression { "," expression } ] "]"
```

`none` represents absence only in an expected `maybe` context. It does not make ordinary types nullable.

Text literals are Unicode text and source files use UTF-8. Invalid UTF-8 is not valid source text.

### Integer literal semantics

`Int` is a signed 64-bit integer on every supported target:

```text
-9223372036854775808 .. 9223372036854775807
```

An integer literal is inferred as `Int` when it fits that range and no other explicit numeric type is required by context.

A compile-time constant expression whose `Int` result is outside that range is rejected:

```eri
let x Int be 9223372036854775807 + 1;  // compile-time error
```

Normal runtime integer arithmetic is checked and does not silently wrap. Runtime overflow and division by zero produce defined arithmetic faults. Explicit wrapping or saturating arithmetic, if added, will be opt-in rather than the behavior of ordinary operators.

## 3. Operators

Initial arithmetic operators:

```text
+  -  *  /
```

Initial comparison operators:

```text
==  !=  <  <=  >  >=
```

Boolean operators are locked as readable words:

```text
and
or
not
```

Examples:

```eri
ready and connected
failed or expired
not connected
```

The symbolic forms `&&`, `||`, and `!` are not Boolean operators in Eristavi.

A working precedence direction is:

```text
not
comparison
and
or
```

Exact precedence for all operators will be formalized before the parser is considered stable.

## 4. Blocks

```text
block := "{" { statement } "}"
```

Example:

```eri
{
    let x be 10;
    print x;
}
```

A structural block closes with `}` and does not require a semicolon merely because the block ended.

## 5. Conditional

Current draft:

```eri
if condition {
    ...
} else {
    ...
}
```

Draft grammar:

```text
if-statement := "if" expression block [ "else" block ]
```

Comparisons with `none` participate in type narrowing for `maybe` values:

```eri
if user == none {
    return;
}

print user.name;
```

and:

```eri
if user != none {
    print user.name;
}
```

## 6. Loops

### For/in

```eri
for item in items {
    print item;
}
```

Draft grammar:

```text
for-statement := "for" identifier "in" expression block
```

### While

```eri
while condition {
    ...
}
```

Draft grammar:

```text
while-statement := "while" expression block
```

## 7. Functions

Current draft form:

```eri
function add(a Int, b Int) returns Int {
    return a + b;
}
```

Optional return values use `maybe`:

```eri
function findUser(id Int) returns maybe User {
    ...
}
```

Recoverable checked failures use `fails`:

```eri
function loadUser(id Int) returns User fails DatabaseError {
    ...
}
```

A function may combine an optional result and a checked error contract:

```eri
function findUser(id Int) returns maybe User fails DatabaseError {
    ...
}
```

A function that intentionally accepts shared identity state makes that visible in the parameter type:

```eri
function increment(counter identity Counter) {
    counter.value = counter.value + 1;
}
```

The function grammar remains provisional beyond the already locked name-first annotation form, `maybe`, `identity`, and `fails` directions.

```text
function-declaration :=
    [ "public" ] "function" identifier "(" [ parameters ] ")"
    [ "returns" type-expression ]
    [ "fails" type-expression ] block

parameters := parameter { "," parameter }
parameter  := identifier [ type-expression ]
```

When a parameter type is written, it follows the parameter name directly, for example `id Int`, `user maybe User`, or `counter identity Counter`.

Ordinary value parameters follow value semantics. An `identity T` parameter preserves shared identity and may therefore observe or mutate the same logical identity as the caller.

Syntax for explicit in-place mutation of an ordinary caller-owned value remains undefined and separate from identity semantics.

## 8. Return

```eri
return value;
return none;
```

Draft grammar:

```text
return-statement := "return" [ expression ] ";"
```

Returning `none` is valid only when the function's result type is `maybe ...` or when surrounding inference establishes an optional result type.

## 9. Checked error handling

A caller of a function with a checked `fails` contract must either handle or propagate that failure.

### Local handling

Current locked direction:

```eri
let user be loadUser(1) else error {
    print error.message;
    return;
}
```

Conceptual grammar:

```text
handled-expression := expression "else" "error" block
```

The `error` name refers to the typed checked error produced by the preceding operation.

The compiler must reject control-flow paths where the success value would be used even though the error-handling block did not establish a valid replacement value or exit that path.

### Propagation

Current locked direction:

```eri
let user be try loadUser(1);
```

Conceptual grammar:

```text
try-expression := "try" expression
```

`try` is valid only when the surrounding function declares a compatible checked failure with `fails`.

The exact syntax for declaring custom error types and composing multiple possible checked error types remains open.

## 10. Resource management

The locked scoped-resource form is:

```eri
with file be try files.open("data.txt") {
    let text be try file.readText();
    print text;
}
```

A resource binding may use the ordinary name-first explicit type form when needed:

```eri
with file File be try files.open("data.txt") {
    ...
}
```

Grammar:

```text
with-statement :=
    "with" identifier [ type-expression ] "be" expression block
```

The expression must produce a resource value recognized by the type system as requiring deterministic cleanup.

The resource identifier is scoped to the `with` block and is released when control leaves that block.

Cleanup applies to normal fallthrough, `return`, checked-error propagation, and any future language-level control flow that exits the block.

Resource handles are single-owner values while managed by `with`. Implicit copying is invalid:

```eri
with file be try files.open("data.txt") {
    let another be file;   // compile-time error: implicit resource copy
}
```

A resource owned by a `with` block also cannot silently escape the scope by being returned, stored elsewhere, or captured in a way that outlives the block.

A deterministic resource type cannot be wrapped in `identity` to bypass these ownership rules.

Multiple resources use ordinary nesting in the initial grammar:

```eri
with connection be try database.connect() {
    with transaction be try connection.transaction() {
        ...
    }
}
```

The inner resource is cleaned up before the outer resource.

The initial grammar deliberately does not introduce borrow/lifetime syntax or a multi-resource `with` header. Advanced ownership transfer and cleanup-failure composition remain semantic design questions for later work.

## 11. Identity handles

Ordinary user-defined values remain value types. Shared identity is introduced explicitly with `identity`.

Example value type:

```eri
type Counter {
    value Int;
}
```

An identity is created from a value expression with the prefix form:

```eri
let first be identity Counter {
    value = 0;
};
let second be first;

second.value = 10;
print first.value;       // 10
```

Conceptual grammar:

```text
identity-expression := "identity" expression
```

`identity expression` must produce an eligible non-resource value. It creates a managed identity handle whose inferred type is `identity T`, where `T` is the value type of the expression.

There is no implicit conversion from `T` to `identity T` or from `identity T` back to `T`.

Identity may be written explicitly in fields and parameters:

```eri
type ViewModel {
    counter identity Counter;
}

function increment(counter identity Counter) {
    counter.value = counter.value + 1;
}
```

The initial language does not allow `fixed` bindings of identity types:

```eri
let fixed counter be identity Counter {
    value = 0;
};  // compile-time error
```

This preserves the locked deep-immutability meaning of `fixed`.

`identity` does not mean raw pointer, manual allocation, thread safety, atomicity, or deterministic resource ownership. Identity storage is automatically memory-managed.

Optional identity handles use the single canonical modifier order:

```eri
maybe identity Counter
```

`identity maybe Counter` is not an alternative spelling.

## 12. Modules and imports

Each `.eri` file is one module. The module path is derived from the file path under the project source root.

Example source tree:

```text
src/
    main.eri
    models/
        user.eri
    services/
        auth.eri
```

produces:

```text
main
models.user
services.auth
```

Source files do not repeat this path with a separate `module` declaration.

### Imports

The locked import form is:

```eri
import models.user;
import services.auth;
```

An optional alias may rename the local module namespace:

```eri
import models.user as customer;
```

Grammar:

```text
import-declaration := "import" module-path [ "as" identifier ] ";"
module-path        := identifier { "." identifier }
```

Imports are file-scope declarations and should appear before ordinary declarations and executable statements.

Without an alias, the imported namespace is the final identifier in the module path:

```eri
import services.auth;

auth.login(user);
```

An import does not place the imported module's declarations directly into local scope.

Wildcard imports and selective unqualified imports are not part of the initial grammar:

```text
import *
from x import y
```

Quoted filesystem paths and relative traversal strings are also not project-module syntax:

```text
import "../models/user.eri"
```

Project module paths are logical dotted names resolved from the configured source root.

The top-level namespace `std` is reserved for standard-library modules:

```eri
import std.files;
import std.json;
```

Circular module dependencies are compile-time errors in the initial language.

### Public declarations

Top-level declarations are module-private by default. `public` exposes a declaration through the module namespace.

Examples:

```eri
public type User {
    fixed id Int;
    name Text;
}

public function find(id Int) returns maybe User {
    ...
}
```

`public` applies to the declaration it prefixes. Eristavi does not use a separate ordinary export list.

## 13. Calls and member access

Function call:

```eri
add(10, 20)
```

Member access:

```eri
customer.name
text.words.count
```

Method call:

```eri
customers.add(customer)
```

Imported module access uses the same member syntax:

```eri
user.User
user.find(10)
auth.login(account)
```

Draft grammar:

```text
postfix-expression := primary { call | member-access | index-access }
call               := "(" [ arguments ] ")"
member-access      := "." identifier
index-access       := "[" expression "]"
arguments          := expression { "," expression }
```

A `maybe` value cannot use member access until control-flow analysis has established that it is not `none`.

Although index access is a general postfix form, direct integer indexing is not defined for `Text` because it would be ambiguous:

```eri
text[0]                 // compile-time error
```

Text must first select an explicit Unicode view:

```eri
text.characters[0]      // Unicode extended grapheme cluster
text.scalars[0]         // Unicode scalar value
text.bytes[0]           // UTF-8 byte
```

The corresponding counts are likewise explicit:

```eri
text.characters.count
text.scalars.count
text.bytes.count
```

A bare `text.length` is not defined by the core Text semantics.

## 14. User-defined types and construction

Ordinary user-defined `type` declarations have value semantics by default.

```eri
type User {
    fixed id Int;
    name Text;
    middleName maybe Text;
}
```

Public types use the same declaration with the `public` visibility modifier:

```eri
public type User {
    fixed id Int;
    name Text;
}
```

A field without `fixed` is mutable. A `fixed` field is initialized once and cannot be reassigned afterward.

Field declarations use the same name-first type annotation form:

```text
field-declaration := [ "fixed" ] identifier type-expression ";"
```

An identity field is explicit in the same position:

```eri
type ViewModel {
    counter identity Counter;
}
```

Assignment of an ordinary user-defined value creates an independent logical value:

```eri
let a be user;
let b be a;

b.name = "Maria";
```

Changing `b` must not change `a`.

If a value contains an explicitly declared `identity T` field, copying the outer value preserves that identity handle by design. This is not hidden aliasing because the field type explicitly states `identity`.

A `fixed` binding of an ordinary value is deeply immutable from the programmer's point of view, including nested ordinary fields that are part of the value.

Construction uses the locked named-field brace form defined in `CONSTRUCTION.md`:

```eri
let user be User {
    id = 1;
    name = "Anna";
    middleName = none;
};
```

Conceptual grammar:

```text
construction-expression :=
    type-name "{" field-initializer { field-initializer } "}"

field-initializer :=
    identifier "=" expression ";"
```

Every declared field is required during direct construction in pre-0.1 and must be initialized exactly once.

## 15. Type expressions and optional values

The initial type modifiers have a single canonical order:

```text
type-expression := [ "maybe" ] [ "identity" ] type-name
```

Examples:

```eri
Text
User
maybe Text
maybe User
identity Counter
maybe identity Counter
```

Where a type annotates a name, the form remains consistently:

```text
identifier type-expression
```

Examples:

```eri
age Int
name Text
user maybe User
counter identity Counter
selected maybe identity Counter
```

`identity` is currently defined for eligible user-defined non-resource value types. It is not an alias for a raw pointer or resource handle.

The canonical optional-identity form is `maybe identity T`; alternative modifier orders such as `identity maybe T` are not part of the grammar.

`none` is the absence literal for a `maybe` value, including `maybe identity T`.

Ordinary non-`maybe` types cannot contain `none`.

The language does not define `null` as an ordinary value or as an alias for `none`.

## 16. Output

Early examples use:

```eri
print "Hello";
```

Whether `print` is a language keyword, compiler intrinsic, or standard-library function is not yet locked. The preference is to keep capabilities in the standard library when practical.

## 17. Generic syntax

Eristavi currently defines **no explicit generic type syntax**.

The following are not part of the grammar:

```text
List<Text>
List[Text]
List.Text
List:Text
```

Collection and generic relationships should be inferred by the compiler where possible. A future explicit abstraction syntax should only be added when real use cases show that inference is insufficient.

## 18. Statement termination — locked

Eristavi uses explicit semicolons to terminate simple statements.

```eri
let price be 50;
price = 60;
print price;
return price;
```

A newline does not terminate a statement and carries no statement-boundary meaning. Formatting may therefore place an expression across multiple lines without requiring a continuation marker:

```eri
let total be
    price
    + tax
    + delivery;
```

The semicolon is the syntactic terminator.

Structural constructs that end with a block do not require an additional semicolon after the closing `}`:

```eri
if ready {
    start();
}

while running {
    tick();
}

function add(a Int, b Int) returns Int {
    return a + b;
}
```

Likewise, `type`, `for`, and `with` blocks end structurally with `}` rather than `};`.

Semicolons remain required inside structures where the grammar defines simple terminated entries, including field declarations and construction field initializers:

```eri
type User {
    fixed id Int;
    name Text;
}

let user be User {
    id = 1;
    name = "Anna";
};
```

The final semicolon above terminates the surrounding variable declaration; the inner semicolons terminate the field initializers.

Eristavi does not use automatic semicolon insertion and does not infer statement termination from indentation or line breaks.

The design rule is:

> Simple statements end with `;`. Structural blocks end with `}`. Newlines are formatting, not syntax.

## 19. Bootstrap subset

The first parser should grow toward accepting multi-file and scoped-resource programs such as:

```eri
import std.files;

with file be try files.open("data.txt") {
    let text be try file.readText();
    print text;
}
```

Identity syntax is specified but does not need to be part of the earliest executable bootstrap milestone. A later frontend milestone can add programs such as:

```eri
type Counter {
    value Int;
}

let counter be identity Counter {
    value = 0;
};
```

while keeping the single-file bootstrap case valid:

```eri
let x be 40;
let fixed y Int be 2;

print x + y;
```

Features should be added to the grammar only after their semantics are understood.
