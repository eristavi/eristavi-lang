# Eristavi Draft Grammar

> **Status: Consolidated draft for pre-0.1**
>
> This file records the current surface grammar after the pre-0.1 specification audit. Productions marked by already-locked language decisions are authoritative for pre-0.1. Expression precedence, assignment placement, condition typing, function completion, and the entry-module model are now locked; only a small number of parser/semantic details remain before parser freeze.

## Goals

The grammar should remain:

- small;
- deterministic;
- readable;
- easy to parse;
- free of redundant equivalent forms;
- independent of line breaks for statement termination.

## 1. Statement termination — locked

Simple statements end with `;`.

```eri
let price be 50;
price = 60;
print price;
return price;
```

Structural blocks end with `}` and do not require an additional semicolon merely because the block ended:

```eri
if ready {
    start();
}
```

Newlines are formatting only. Eristavi has no automatic semicolon insertion and does not infer statement boundaries from indentation.

The rule is:

> Simple statements end with `;`. Structural blocks end with `}`. Newlines are formatting, not syntax.

## 2. Names and type expressions

Conceptual forms:

```text
qualified-name := identifier { "." identifier }
type-name      := qualified-name

type-expression := [ "maybe" ] [ "identity" ] type-name
```

Canonical examples:

```text
Int
Text
User
models.User
maybe User
identity Counter
maybe identity Counter
```

`identity maybe Counter` is not an alternate spelling.

Where a type annotates a named value, the name comes first:

```text
identifier type-expression
```

There is no colon-based named type annotation.

## 3. Variable declarations — locked

```eri
let name be expression;
let name Type be expression;
let fixed name be expression;
let fixed name Type be expression;
```

Grammar:

```text
variable-declaration :=
    "let" [ "fixed" ] identifier [ type-expression ] "be" value-expression ";"
```

A `fixed` binding whose inferred or explicit type is `identity ...` is invalid in pre-0.1.

## 4. Literals

Initial literal forms include:

```text
integer
float
text
true
false
none
list literal
```

List literal:

```text
list-literal :=
    "[" [ expression { "," expression } ] "]"
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

`none` is valid only where the expected or inferred type is `maybe ...`.

## 5. Operators and expression precedence — locked

Arithmetic operators:

```text
+  -  *  /  %
```

Comparison operators:

```text
==  !=  <  <=  >  >=
```

Boolean operators:

```text
not
and
or
```

The symbolic aliases `!`, `&&`, and `||` are not Eristavi Boolean operators.

Pre-0.1 precedence from highest to lowest is:

| Level | Forms / operators | Associativity |
|---|---|---|
| 1 | call `()`, index `[]`, member access `.` | left / postfix |
| 2 | unary `-`, `try`, `identity` | prefix |
| 3 | `*`, `/`, `%` | left |
| 4 | `+`, `-` | left |
| 5 | `==`, `!=`, `<`, `<=`, `>`, `>=` | non-associative |
| 6 | `not` | prefix |
| 7 | `and` | left |
| 8 | `or` | left |

Assignment `=` is not an expression operator and has no precedence level.

Conceptually, the parser may express the hierarchy as:

```text
expression :=
    or-expression

or-expression :=
    and-expression { "or" and-expression }

and-expression :=
    not-expression { "and" not-expression }

not-expression :=
    "not" not-expression
    | comparison-expression

comparison-expression :=
    additive-expression
    [ comparison-operator additive-expression ]

comparison-operator :=
    "==" | "!=" | "<" | "<=" | ">" | ">="

additive-expression :=
    multiplicative-expression
    { ( "+" | "-" ) multiplicative-expression }

multiplicative-expression :=
    prefix-expression
    { ( "*" | "/" | "%" ) prefix-expression }

prefix-expression :=
    ( "-" | "try" | "identity" ) prefix-expression
    | postfix-expression
```

The non-repeating optional comparison production is intentional: comparison chaining is not part of pre-0.1.

Therefore:

```eri
a + b * c
```

means:

```eri
a + (b * c)
```

and:

```eri
not a == b
```

means:

```eri
not (a == b)
```

while:

```eri
a or b and c
```

means:

```eri
a or (b and c)
```

These are invalid comparison chains:

```text
10 < age < 65
a == b == c
```

Write the intended relationship explicitly:

```eri
age > 10 and age < 65
a == b and b == c
```

For `identity T`, `==` and `!=` use logical identity semantics as defined in `IDENTITY_EQUALITY.md`.

See `PRECEDENCE.md` and `OPERATORS.md` for the locked detailed model.

## 6. Blocks

```text
block :=
    "{" { statement } "}"
```

Example:

```eri
{
    let x be 10;
    print x;
}
```

## 7. Conditionals — locked condition typing

```eri
if condition {
    ...
} else {
    ...
}
```

Grammar:

```text
if-statement :=
    "if" expression block [ "else" block ]
```

The condition expression must have static type `Bool`. Eristavi does not apply implicit truthiness to numbers, text, collections, optional values, identities, or other values.

Comparisons with `none` participate in semantic narrowing for `maybe` values.

See `CONDITIONS.md`.

## 8. Loops

For/in:

```eri
for item in items {
    print item;
}
```

```text
for-statement :=
    "for" identifier "in" expression block
```

While:

```eri
while condition {
    ...
}
```

```text
while-statement :=
    "while" expression block
```

A `while` condition must have static type `Bool`, under the same rule as `if`.

## 9. Functions and result inference — locked

Examples with an explicit result contract:

```eri
function add(a Int, b Int) returns Int {
    return a + b;
}
```

A result may instead be inferred when it is statically clear:

```eri
function add(a Int, b Int) {
    return a + b;
}
```

The second function is inferred to produce `Int`.

A function with no explicit `returns T` and no `return expression;` statements is a no-value function:

```eri
function logMessage(message Text) {
    print message;
}
```

Conceptual grammar:

```text
function-declaration :=
    [ "public" ] "function" identifier
    "(" [ parameters ] ")"
    [ "returns" type-expression ]
    [ fails-clause ]
    block

parameters :=
    parameter { "," parameter }

parameter :=
    identifier [ type-expression ]

fails-clause :=
    "fails" error-type { "," error-type }

error-type :=
    type-name
```

Parameters without written types may participate in compiler-inferred static generic relationships as defined in `GENERICS.md`.

Ordinary parameters use value semantics. Pre-0.1 defines no separate `ref`, `mut`, `inout`, or equivalent parameter syntax.

Pre-0.1 defines no programmer-visible `Void`, `void`, `Unit`, or equivalent result type merely to represent a no-value function.

When a value-producing function's result inference depends directly or indirectly on its own result type, `returns T` is required explicitly. This includes recursive or mutually recursive result inference that would otherwise be circular.

See `FUNCTION_RETURNS.md` for the locked result/completion model.

## 10. Return and function completion — locked

Surface grammar remains:

```text
return-statement :=
    "return" [ expression ] ";"
```

The two forms have different semantic roles.

A value return:

```eri
return value;
```

produces the function's successful result. If `returns T` is omitted, compatible `return expression;` sites may establish the inferred result type.

A bare return:

```eri
return;
```

is valid only in a no-value function and performs an early exit.

A function cannot mix `return expression;` and bare `return;` completion.

For a value-producing function, every reachable path that can complete successfully must return a compatible value. Reaching the closing `}` on such a path is a compile-time error rather than an implicit missing value.

Checked `fail` terminates its path and therefore does not require a `return` on that path.

`return none;` returns an actual absent `maybe T` value. It is not equivalent to `return;` and `none` is never used as Eristavi's substitute for a void result.

Multiple inferred return expressions must establish one compatible static result type; pre-0.1 does not create a dynamic or union result type to reconcile incompatible returns.

A no-value function call cannot be used where a value is required.

See `FUNCTION_RETURNS.md`.

## 11. User-defined types — locked core form

```eri
type User {
    fixed id Int;
    name Text;
    middleName maybe Text;
}
```

Public type:

```eri
public type User {
    id Int;
}
```

Conceptual grammar:

```text
type-declaration :=
    [ "public" ] "type" identifier
    "{" { field-declaration } "}"

field-declaration :=
    [ "fixed" ] identifier type-expression ";"
```

Type blocks end with `}`, not `};`.

## 12. Named-field construction — locked

Eristavi has one direct construction form:

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

The `=` token here belongs to the construction grammar; it is not an assignment expression.

Every declared field is required exactly once in direct pre-0.1 construction.

The language does not use positional construction such as `User(1, "Anna")` or colon-based construction such as `User(id: 1)`.

## 13. Identity expressions — locked

```eri
let counter be identity Counter {
    value = 0;
};
```

Conceptual grammar:

```text
identity-expression :=
    "identity" expression
```

For precedence purposes `identity` is a prefix form. The expression grammar factors it at prefix precedence; semantic analysis requires the resulting operand to be an eligible ordinary non-resource value.

Identity is semantic shared identity, not a raw pointer.

## 14. Checked error declarations — locked

```eri
error DatabaseError {
    message Text;
    code Int;
}
```

Public error:

```eri
public error DatabaseError {
    message Text;
    code Int;
}
```

Conceptual grammar:

```text
error-declaration :=
    [ "public" ] "error" identifier
    "{" error-field { error-field } "}"

error-field :=
    identifier type-expression ";"
```

A pre-0.1 checked error declaration must contain exactly one field named `message` of type `Text`.

Error values use the ordinary named-field construction form.

## 15. Producing checked failure — locked

```eri
fail DatabaseError {
    message = "Database unavailable";
    code = 503;
};
```

Grammar:

```text
fail-statement :=
    "fail" expression ";"
```

Semantic analysis requires the produced error type to be permitted by the current function's `fails` contract.

## 16. Checked error handling — locked

Catch-all:

```eri
let user be loadUser(1) else error {
    print error.message;
    return;
};
```

Typed handlers:

```eri
let user be loadUser(1)
else error DatabaseError {
    return;
}
else error DecodeError {
    return;
};
```

Conceptual grammar:

```text
handled-expression :=
    expression error-handler { error-handler }

error-handler :=
    "else" "error" [ error-type ] block
```

An untyped handler is catch-all and must be final when combined with typed handlers. Semantic analysis requires the handler sequence to be exhaustive.

For grammar references in declarations, `value-expression` means either an ordinary expression or a valid handled expression:

```text
value-expression :=
    expression | handled-expression
```

The parser implementation may factor this production differently to avoid recursive ambiguity; the semantic surface above is the locked behavior.

## 17. Checked error propagation — locked

```eri
let user be try loadUser(1);
```

Conceptual grammar:

```text
try-expression :=
    "try" expression
```

For precedence purposes `try` is a prefix form. Semantic analysis verifies compatibility with the surrounding function's `fails` contract.

## 18. Resource management — locked

```eri
with file be try files.open("data.txt") {
    let text be try file.readText();
    print text;
}
```

Optional explicit resource type:

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

The resource identifier is scoped to the block. Resource copy/escape restrictions are semantic checks rather than additional surface syntax.

## 19. Modules and imports — locked

One `.eri` file is one module. The module path is derived from its source-root-relative file path; no module declaration is written in source.

Imports:

```eri
import models.user;
import services.auth;
import models.user as customer;
```

Grammar:

```text
import-declaration :=
    "import" module-path [ "as" identifier ] ";"

module-path :=
    identifier { "." identifier }
```

In pre-0.1, imports must appear before module declarations or top-level entry executable statements. Imports are static module-graph declarations rather than runtime execution points.

Wildcard imports, selective unqualified imports, quoted project paths, and relative traversal strings are not part of pre-0.1.

## 20. Calls, member access, and indexing — locked precedence

Conceptual postfix grammar:

```text
postfix-expression :=
    primary { call | member-access | index-access }

call :=
    "(" [ arguments ] ")"

member-access :=
    "." identifier

index-access :=
    "[" expression "]"

arguments :=
    expression { "," expression }
```

Postfix call, member access, and indexing have the highest expression precedence and chain left to right.

Examples:

```eri
add(10, 20)
customer.name
customers.add(customer)
auth.login(account)
users[0].name
```

Direct integer indexing of `Text` is invalid. An explicit Unicode view must be selected first:

```eri
text.characters[0]
text.scalars[0]
text.bytes[0]
```

## 21. Generic source syntax — locked absent in pre-0.1

Pre-0.1 defines no explicit source grammar for generic type variables, bounds, or arguments.

These are not Eristavi source forms:

```text
List<Text>
List[Text]
List.Text
List:Text
function first<T>(items)
where T: Comparable
```

Generic relationships may still exist internally through static inference as defined in `GENERICS.md`.

## 22. Statement categories and assignment — locked

Conceptually:

```text
statement :=
      variable-declaration
    | assignment-statement
    | expression-statement
    | return-statement
    | fail-statement
    | if-statement
    | for-statement
    | while-statement
    | with-statement
    | function-declaration
    | type-declaration
    | error-declaration
```

Simple assignment and expression statements end with `;`:

```text
assignment-statement :=
    assignment-target "=" value-expression ";"

assignment-target :=
    identifier { "." identifier }

expression-statement :=
    value-expression ";"
```

Assignment is statement-level syntax. It is not part of `expression` or `value-expression`, does not produce a value, and cannot be chained.

Valid:

```eri
price = 50;
user.name = "Maria";
```

Invalid:

```text
a = b = c;
let value be (a = b);
```

Semantic analysis determines whether the assignment target is mutable and whether the right-hand value is type-compatible.

## 23. Top-level execution and entry module — locked

A run/build operation that needs an executable program start selects exactly one source file as the entry module. The language does not reserve a `main` function name and does not require a `main.eri` filename.

Pre-0.1 distinguishes an importable declaration-only module from a selected entry module:

```text
module-declaration :=
      function-declaration
    | type-declaration
    | error-declaration

importable-module :=
    { import-declaration }
    { module-declaration }

entry-module :=
    { import-declaration }
    { module-declaration }
    { entry-statement }

entry-statement :=
      variable-declaration
    | assignment-statement
    | expression-statement
    | if-statement
    | for-statement
    | while-statement
    | with-statement
```

The ordering is intentional:

```text
imports
module declarations
entry executable statements
```

Once the first entry executable statement appears, a later module declaration is invalid.

Entry executable statements form an implicit no-value execution body and run in source order. Their `let` / `fixed` bindings are entry-local rather than module declarations: they cannot be imported and are not implicitly visible inside module-level functions, types, or errors.

Module declarations remain order-independent within the declaration region, while entry-local executable bindings follow the ordinary declaration-before-use and no-shadowing rules.

Imported modules must match `importable-module`; they cannot contain top-level executable statements. Imports therefore do not trigger arbitrary hidden initialization code.

`return` is invalid at file scope because return semantics belong to functions. A top-level checked `fail` is also invalid because the entry body has no `fails` contract, and `try` cannot propagate a checked failure beyond the entry boundary. Checked failures reaching the entry boundary must instead be handled exhaustively.

Normal fallthrough from the final reachable entry statement completes the program normally.

See `ENTRYPOINT.md` for the locked detailed model.

## 24. Output bootstrap status

Early programs use:

```eri
print "Hello";
```

The behavior is part of the bootstrap examples, but whether `print` ultimately lives as a keyword, compiler intrinsic, or standard-library function is not yet frozen.

## 25. Bootstrap subset

The first compiler milestone may implement only a subset of the already-defined pre-0.1 grammar.

The smallest example remains a valid entry module:

```eri
let x be 40;
let fixed y Int be 2;

print x + y;
```

Implementation should add already-defined features incrementally rather than inventing new syntax during compiler construction.

## 26. Remaining grammar work before parser freeze

The remaining grammar-level work is intentionally narrow:

- settle any parser factoring required for `else error` without changing its surface syntax;
- classify bootstrap `print` if the first compiler requires that distinction;
- finalize any primary-expression factoring needed by the implementation without changing the locked surface syntax.

Lexical rules, symbolic vocabulary, expression precedence, associativity, assignment placement, Bool-only condition typing, function result/completion semantics, and the entry-module/top-level execution model are now locked.

These remaining items are parser/specification details, not reasons to reopen already-locked language semantics.
