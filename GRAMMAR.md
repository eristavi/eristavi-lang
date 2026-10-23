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
list literal
```

Examples:

```eri
42
19.95
"Hello"
true
false
[1, 2, 3]
[]
```

Draft grammar:

```text
list-literal := "[" [ expression { "," expression } ] "]"
```

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

The semantic model for inference of parameter/return types is still under discussion, so the grammar below is provisional.

```text
function-declaration :=
    "function" identifier "(" [ parameters ] ")"
    [ "returns" type-name ] block

parameters := parameter { "," parameter }
parameter  := identifier [ type-name ]
```

Ordinary parameter passing follows value semantics. Syntax for explicit in-place mutation of caller-owned values is not defined yet.

## 8. Return

```eri
return value;
```

Draft grammar:

```text
return-statement := "return" [ expression ] ";"
```

## 9. Calls and member access

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

## 10. User-defined types

Ordinary user-defined `type` declarations have value semantics by default.

```eri
type User {
    fixed id Int;
    name Text;
}
```

A field without `fixed` is mutable. A `fixed` field is initialized once and cannot be reassigned afterward.

The field declaration shape is:

```text
field-declaration := [ "fixed" ] identifier type-name ";"
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

## 11. Output

Early examples use:

```eri
print "Hello";
```

Whether `print` is a language keyword, compiler intrinsic, or standard-library function is not yet locked. The preference is to keep capabilities in the standard library when practical.

## 12. Generic syntax

Eristavi currently defines **no explicit generic type syntax**.

The following are not part of the grammar:

```text
List<Text>
List[Text]
List.Text
List:Text
```

Collection and generic relationships should be inferred by the compiler where possible. A future explicit abstraction syntax should only be added when real use cases show that inference is insufficient.

## 13. Semicolon status

Current examples use semicolons to terminate simple statements. This is the working parser assumption for the bootstrap compiler, not yet a permanent language commitment.

## 14. Bootstrap subset

The first parser only needs enough grammar to accept programs such as:

```eri
let x be 40;
let fixed y be 2;

print x + y;
```

Features should be added to the grammar only after their semantics are understood.
