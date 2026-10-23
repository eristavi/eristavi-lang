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
let fixed name be expression;
```

`let` introduces a mutable binding by default. `fixed` makes that binding immutable after initialization.

Examples:

```eri
let age be 44;
let name be "Anna";
let values be [10, 20, 30];

let fixed taxRate be 0.19;
```

Grammar:

```text
variable-declaration := "let" [ "fixed" ] identifier "be" expression ";"
```

Explicit type annotation is intentionally left out of this first grammar until its final form is decided.

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

The semantic model for inference of parameter/return types is still under discussion, so the grammar below remains provisional apart from the locked `fails` direction.

```text
function-declaration :=
    "function" identifier "(" [ parameters ] ")"
    [ "returns" type-expression ]
    [ "fails" type-expression ] block

parameters := parameter { "," parameter }
parameter  := identifier [ type-expression ]
```

Ordinary parameter passing follows value semantics. Syntax for explicit in-place mutation of caller-owned values is not defined yet.

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

## 10. Calls and member access

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

Draft grammar:

```text
postfix-expression := primary { call | member-access | index-access }
call               := "(" [ arguments ] ")"
member-access      := "." identifier
index-access       := "[" expression "]"
arguments          := expression { "," expression }
```

A `maybe` value cannot use member access until control-flow analysis has established that it is not `none`.

## 11. User-defined types

Ordinary user-defined `type` declarations have value semantics by default.

```eri
type User {
    fixed id Int;
    name Text;
    middleName maybe Text;
}
```

A field without `fixed` is mutable. A `fixed` field is initialized once and cannot be reassigned afterward.

Field declarations use a type expression:

```text
field-declaration := [ "fixed" ] identifier type-expression ";"
```

Assignment of a user-defined value creates an independent logical value:

```eri
let a be user;
let b be a;

b.name = "Maria";
```

Changing `b` must not change `a`.

A `fixed` binding is deeply immutable from the programmer's point of view, including nested fields that are part of the value.

Explicit shared/reference semantics are not part of ordinary `type` syntax. A future explicit identity/reference mechanism may be added separately when needed.

The exact constructor/initialization syntax remains provisional.

## 12. Type expressions and optional values

The initial optional type modifier is locked as `maybe`:

```text
type-expression := [ "maybe" ] type-name
```

Examples:

```eri
maybe Text
maybe User
maybe Int
```

`none` is the absence literal for a `maybe` value.

Ordinary non-`maybe` types cannot contain `none`.

The language does not define `null` as an ordinary value or as an alias for `none`.

## 13. Output

Early examples use:

```eri
print "Hello";
```

Whether `print` is a language keyword, compiler intrinsic, or standard-library function is not yet locked. The preference is to keep capabilities in the standard library when practical.

## 14. Generic syntax

Eristavi currently defines **no explicit generic type syntax**.

The following are not part of the grammar:

```text
List<Text>
List[Text]
List.Text
List:Text
```

Collection and generic relationships should be inferred by the compiler where possible. A future explicit abstraction syntax should only be added when real use cases show that inference is insufficient.

## 15. Semicolon status

Current examples use semicolons to terminate simple statements. This is the working parser assumption for the bootstrap compiler, not yet a permanent language commitment.

## 16. Bootstrap subset

The first parser only needs enough grammar to accept programs such as:

```eri
let x be 40;
let fixed y be 2;

print x + y;
```

Features should be added to the grammar only after their semantics are understood.
