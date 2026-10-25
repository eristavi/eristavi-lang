# Eristavi Punctuation and Operators

> **Status: Pre-0.1 punctuation contract; collection extension qualification pending**

This document defines Eristavi's symbolic punctuation and operator vocabulary.

The design goal is deliberately small: use symbols where their structural meaning is immediately readable, use words where symbols reduce readability, and avoid redundant shorthand.

## 1. Complete pre-0.1 symbolic vocabulary

```text
Punctuation:
; , : . ( ) { } [ ]

Assignment:
=

Arithmetic:
+ - * / %

Comparison:
== != < <= > >=
```

Boolean operators remain words:

```text
and
or
not
```

`:` is punctuation, not a keyword and not a general-purpose operator.

## 2. Structural punctuation

### Semicolon

`;` terminates simple statements, field declarations, named-field initializers, and Map entries according to grammar context.

```eri
let price be 50;
price = 60;

let ages be [
    "Anna" : 32;
    "John" : 41;
];
```

### Comma

`,` separates items in grammar contexts such as function parameters, arguments, error contracts, and List elements.

```eri
function add(a Int, b Int) returns Int {
    return a + b;
}

let names be ["Anna", "Maria", "John"];
```

A Map deliberately does not reuse comma as its entry terminator; `:` expresses the key/value relationship and `;` closes that relationship.

### Colon

`:` has one pre-0.1 source meaning: it separates a Map key from its value inside a Map literal.

```eri
let ages be [
    "Anna" : 32;
    "John" : 41;
];
```

The empty Map spelling is:

```eri
let values be [:];
```

`:` is not used for type annotations, return types, namespace qualification, slicing, or a ternary operator.

Therefore forms such as these remain invalid:

```text
let age: Int be 32;
condition ? first : second
module::name
```

### Dot

`.` is used for qualified/member access and module paths where grammar context permits it.

```eri
user.name
customer.address.city
text.characters.count
models.user
```

### Parentheses

`(` and `)` are used for grouping, function calls, and parameter lists.

### Braces

`{` and `}` delimit blocks and named-field construction bodies.

```eri
if ready {
    output("Ready");
}

let user be User {
    id = 1;
    name = "Anna";
};
```

Braces are not Map literal punctuation.

### Square brackets

`[` and `]` are the visual family for collection literals and supported indexing.

```eri
let names be ["Anna", "Maria"];
let ages be ["Anna" : 32; "John" : 41;];
let data Bytes be [72, 101, 108];

let first be names[0];
let age be ages["Anna"];
let byte be data[0];
```

The contained punctuation/type context determines whether the literal denotes List, Map or Bytes. Square brackets do not make arbitrary types indexable; direct `Text` integer indexing remains invalid.

## 3. Assignment

Pre-0.1 defines one assignment symbol:

```text
=
```

Examples:

```eri
price = 50;
user.name = "Maria";
numbers[0] = 10;
ages["Anna"] = 33;
```

The grammar determines whether `=` is ordinary assignment or a named-field initializer. It remains a statement/construction form, not an expression operator.

Compound-assignment operators such as `+=`, `-=`, `*=`, `/=` and `%=` are not defined.

## 4. Arithmetic operators

Pre-0.1 defines:

```text
+ - * / %
```

`-` also serves as unary numeric negation. The lexer does not include the minus sign inside numeric literal tokens.

No symbolic exponentiation, increment or decrement syntax is defined.

## 5. Comparison operators

Pre-0.1 defines:

```text
==
!=
<
<=
>
>=
```

The semantic meaning of equality follows the operand types. `identity T == identity T` compares logical identity under the existing identity contract.

Standalone `!` is not an Eristavi operator; Boolean negation is `not`. `!=` remains one complete comparison token.

## 6. Boolean operators remain words

```text
and
or
not
```

There are no symbolic aliases `&&`, `||` or standalone `!`.

## 7. Longest-token recognition

When one valid symbolic token is a prefix of another, the lexer recognizes the longest valid token. This applies to:

```text
==
!=
<=
>=
```

The rule is lexical and does not define operator precedence.

## 8. Slash and comments

`/` participates in three lexical possibilities:

```text
/     division
//    line comment
/*    block comment
```

Comment opener recognition takes priority over treating the first slash as division.

## 9. Deliberately absent symbolic syntax

Pre-0.1 does not define:

```text
+= -= *= /= %=
++ --
**
&& || !
& | ^ ~ << >>
?
-> =>
::
@
#
`
```

The colon itself is no longer absent; its meaning is narrowly fixed to Map entry punctuation. There is still no punctuation-based ternary operator or colon-based type annotation.

## 10. Whitespace

Whitespace is not required around punctuation/operators where token boundaries are unambiguous.

These are lexically valid:

```eri
add(a,b);
a+b;
user.name;
["a":1;]
```

Canonical spacing remains a formatter/style concern. Documentation prefers spaces around `:` in Map entries for readability.

## Governing rule

> Eristavi keeps its symbolic vocabulary small. `:` exists because an associative key/value relationship needs a clear visual separator; it has no unrelated secondary meaning. Boolean logic remains `and`, `or`, and `not`, and redundant shorthand stays excluded.
