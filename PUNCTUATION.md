# Eristavi Punctuation and Operators

> **Status: Locked for pre-0.1**

This document defines the symbolic punctuation and operator vocabulary of Eristavi pre-0.1.

The design goal is deliberately small: use symbols where they are universally clear, use words where symbols reduce readability, and do not add shorthand until real programs justify it.

## 1. Complete pre-0.1 symbolic vocabulary

Pre-0.1 defines exactly these symbolic punctuation and operator tokens:

```text
Punctuation:
; , . ( ) { } [ ]

Assignment:
=

Arithmetic:
+ - * / %

Comparison:
== != < <= > >=
```

Boolean operators remain the already-locked word operators:

```text
and
or
not
```

## 2. Structural punctuation

### Semicolon

`;` terminates simple statements, field declarations, and named-field initializers according to grammar context.

```eri
let price be 50;
price = 60;
return price;
```

Structural blocks end with `}` rather than an additional semicolon unless the surrounding construct itself requires a terminating `;`.

### Comma

`,` separates items in grammar contexts such as function parameters, arguments, error contracts, and collection elements.

```eri
function add(a Int, b Int) returns Int {
    return a + b;
}

let names be ["Anna", "Maria", "John"];
```

### Dot

`.` is used for qualified/member access and module paths where grammar context permits it.

```eri
user.name
customer.address.city
text.characters.count
models.user
```

Because pre-0.1 floating-point literals require digits on both sides of a decimal point, forms such as `.5` are invalid and do not create ambiguity with the dot token.

### Parentheses

`(` and `)` are used for grouping, function calls, and parameter lists.

```eri
let result be (a + b) * c;
let total be add(a, b);
```

### Braces

`{` and `}` delimit blocks and named-field construction bodies according to grammar context.

```eri
if ready {
    output("Ready");
}

let user be User {
    id = 1;
    name = "Anna";
};
```

### Square brackets

`[` and `]` are used for collection literals and indexing where the type supports indexing.

```eri
let names be ["Anna", "Maria", "John"];
let first be names[0];
```

Square-bracket syntax does not imply that every type is directly indexable. For example, the locked `Text` model still rejects direct integer indexing:

```eri
text[0]               // compile-time error
text.characters[0]    // valid character-view indexing
```

## 3. Assignment

Pre-0.1 defines one assignment symbol:

```text
=
```

Examples:

```eri
price = 50;
user.name = "Maria";

let user be User {
    id = 1;
    name = "Anna";
};
```

The grammar determines whether `=` is an ordinary assignment or a named-field initializer.

Pre-0.1 does not define compound-assignment operators such as:

```text
+= -= *= /= %=
```

Programs use the explicit form:

```eri
price = price + 10;
```

## 4. Arithmetic operators

Pre-0.1 defines:

```text
+ - * / %
```

Examples:

```eri
let total be price + tax;
let difference be a - b;
let area be width * height;
let average be total / count;
let remainder be value % 10;
```

The `-` token also serves as unary numeric negation:

```eri
let temperature be -5;
let result be -(a + b);
```

The lexer does not include the minus sign inside integer or floating-point literal tokens.

Pre-0.1 does not define symbolic exponentiation, increment, or decrement operators such as:

```text
**
++
--
```

Exponentiation may be provided through ordinary numeric APIs unless later language experience proves dedicated syntax valuable.

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

Examples:

```eri
if age >= 18 {
    ...
}

if user == none {
    ...
}

if first != second {
    ...
}
```

The semantic meaning of equality follows the operand types. In particular, the already-locked `identity T` rule means `==` compares logical identity for identity values.

The standalone symbol `!` is not an Eristavi operator. Boolean negation uses the word operator:

```eri
not ready
```

`!=` remains one complete comparison token.

## 6. Boolean operators remain words

Boolean operations use the already-locked keywords:

```text
and
or
not
```

Examples:

```eri
if active and verified {
    ...
}

if not connected {
    ...
}

if admin or owner {
    ...
}
```

Pre-0.1 does not define symbolic aliases:

```text
&&
||
!
```

## 7. Longest-token recognition

When one valid symbolic token is a prefix of another, the lexer recognizes the longest valid token.

For example:

```eri
a >= b
```

contains the single comparison token `>=`, not separate `>` and `=` tokens.

The same rule applies to:

```text
==
!=
<=
>=
```

This longest-token rule is lexical and does not define operator precedence.

## 8. Slash and comment recognition

The `/` symbol participates in three lexical possibilities:

```text
/     division operator
//    line-comment opener
/*    block-comment opener
```

When the lexer encounters `/`, it checks the following source character:

```text
"//"  -> line comment
"/*"  -> block comment
"/"   -> division operator when neither comment opener matches
```

Comment recognition therefore takes priority over treating the first `/` as division.

## 9. Deliberately absent symbolic syntax

Pre-0.1 does not define the following symbolic forms:

```text
+= -= *= /= %=
++ --
**
&& || !
& | ^ ~ << >>
? :
-> =>
::
@
#
`
```

Their absence is intentional. They must not acquire language meaning without a separate future design decision justified by real Eristavi programs.

This also means pre-0.1 has no punctuation-based ternary operator, arrow-return syntax, annotation prefix, namespace separator, bitwise operator family, or escaped-identifier delimiter.

## 10. Whitespace around punctuation

Whitespace is not required around punctuation or symbolic operators when token boundaries are otherwise unambiguous.

These are lexically valid:

```eri
add(a,b);
a+b;
user.name;
```

Canonical spacing is a formatter/style concern rather than a lexical rule.

## Governing rule

> Eristavi pre-0.1 keeps its symbolic vocabulary small: `; , . ( ) { } [ ]`, `=`, `+ - * / %`, and `== != < <= > >=`. Boolean logic remains `and`, `or`, and `not`; speculative shorthand and redundant symbolic aliases are excluded until real programs justify them.
