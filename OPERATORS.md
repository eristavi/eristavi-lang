# Eristavi Punctuation and Operators

> **Status: Symbol vocabulary, precedence, associativity, and `%` applicability locked for pre-0.1.**

This document defines the symbolic punctuation and operator tokens available in Eristavi pre-0.1. The language deliberately keeps this vocabulary small and does not add shorthand merely because it exists in other languages.

## 1. Complete symbolic token set — locked

Pre-0.1 defines exactly 21 symbolic punctuation/operator tokens.

### Structural punctuation

```text
;  ,  .  (  )  {  }  [  ]
```

There are nine structural punctuation tokens.

### Assignment

```text
=
```

### Arithmetic operators

```text
+  -  *  /  %
```

### Comparison operators

```text
==  !=  <  <=  >  >=
```

Boolean operators remain the already-locked word operators:

```text
and  or  not
```

They are reserved keywords rather than symbolic tokens.

## 2. Structural punctuation

### Semicolon `;`

A semicolon terminates simple statements and declaration/initializer entries where the grammar requires one.

```eri
let price be 50;
price = 60;
return price;
```

Fields and named construction initializers also use `;`:

```eri
type User {
    id Int;
    name Text;
}

let user be User {
    id = 1;
    name = "Anna";
};
```

Structural blocks themselves end with `}` rather than an additional semicolon unless the surrounding construct is itself part of a simple statement.

### Comma `,`

A comma separates items in grammatical lists such as function parameters, function arguments, collection elements, and checked-error contracts.

```eri
function add(a Int, b Int) returns Int {
    return a + b;
}

let names be ["Anna", "Maria", "John"];
```

### Dot `.`

A dot is used for qualified/member access and dotted module paths.

```eri
user.name
customer.address.city
text.characters.count
import models.user;
```

Because pre-0.1 rejects shorthand floating-point forms such as `.5` and `5.`, the dot remains lexically unambiguous with numeric literals.

### Parentheses `( )`

Parentheses are used for grouping, function calls, and function parameter lists.

```eri
let result be (a + b) * c;
let value be calculate(first, second);

function add(a Int, b Int) returns Int {
    return a + b;
}
```

### Braces `{ }`

Braces delimit structural blocks and named-field construction bodies.

```eri
if ready {
    output("Ready");
}

let user be User {
    id = 1;
    name = "Anna";
};
```

The parser distinguishes these uses by grammar context; the lexer exposes the same brace tokens.

### Brackets `[ ]`

Square brackets are used for collection literals and indexing syntax.

```eri
let names be ["Anna", "Maria"];
let first be names[0];
```

Whether a value semantically supports indexing is a type-system question rather than a lexical one. For example, the existing `Text` model still rejects direct `text[0]` indexing and requires an explicit view such as `text.characters[0]`.

## 3. Assignment `=`

Pre-0.1 defines one assignment symbol:

```text
=
```

Examples:

```eri
price = 50;
user.name = "Maria";
```

Named construction uses the same token in its grammar-defined initializer context:

```eri
let user be User {
    id = 1;
    name = "Anna";
};
```

`=` is not a general expression operator. Assignment does not produce a value and has no precedence level.

These forms are therefore invalid:

```text
a = b = c;
if x = 10 {
    ...
}
let value be (x = 20);
```

No compound-assignment operators are defined in pre-0.1.

## 4. Arithmetic operators

Pre-0.1 defines the symbolic arithmetic vocabulary:

```text
+  -  *  /  %
```

Examples:

```eri
let total be price + tax;
let difference be a - b;
let area be width * height;
let quotient be total / count;
let remainder be value % 10;
```

The `%` operator is defined only for `Int` in pre-0.1. Both operands and the result are `Int`.

Signed `Int` division truncates toward zero. `%` is the associated signed remainder:

```text
 10 % 3   =  1
-10 % 3   = -1
 10 % -3  =  1
-10 % -3  = -1
```

Division or remainder by zero is a checked integer arithmetic fault. The signed-minimum / `-1` exceptional pair is likewise an overflow fault under the locked integer arithmetic model.

`Float` does not support `%` in pre-0.1. Floating-point remainder or modulo, if later required, belongs to explicitly named numeric library operations rather than receiving an ambiguous `%` meaning.

See `INTEGER_REMAINDER.md` for the full locked rule.

The `-` token is also used by unary negation:

```eri
let temperature be -5;
let result be -(a + b);
```

Negative numeric literals are therefore not separate signed literal tokens.

Pre-0.1 does not define unary `+`, `++`, `--`, or a symbolic exponentiation operator such as `**`.

## 5. Comparison operators

Pre-0.1 defines exactly six symbolic comparison operators:

```text
==  !=  <  <=  >  >=
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

The semantic meaning of equality depends on the operand type. In particular, the already-locked identity rule remains in force: for `identity T`, `==` compares logical identity rather than object contents or physical addresses.

The standalone symbol `!` is not an Eristavi operator. Boolean negation uses the word operator:

```eri
if not connected {
    ...
}
```

`!=` remains one complete comparison token.

Comparison operators are non-associative in pre-0.1. Chained forms such as `10 < age < 65` and `a == b == c` are invalid; the intended relationship must be written explicitly with Boolean operators.

## 6. Boolean operators remain words

Eristavi uses:

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

if admin or owner {
    ...
}

if not connected {
    ...
}
```

The symbolic aliases `&&`, `||`, and standalone `!` are not part of pre-0.1.

## 7. Longest-token recognition

When multiple valid symbolic tokens share a prefix, the lexer recognizes the longest valid token.

For example:

```eri
a >= b
```

contains the single `>=` token rather than separate `>` and `=` tokens.

The same rule applies to:

```text
==
!=
<=
>=
```

This rule concerns tokenization only.

## 8. Slash and comments

The `/` symbol is an arithmetic division token unless it begins one of the already-defined comment forms.

When the lexer encounters `/`:

```text
//  begins a line comment
/*  begins a block comment
/   otherwise denotes division
```

Examples:

```eri
let ratio be a / b;

// line comment

/* block comment */
```

Comment recognition therefore takes lexical priority over emitting a standalone `/` token when the required second character is present.

## 9. Deliberately absent symbolic vocabulary

Pre-0.1 does not define these operator or punctuation forms:

```text
+=  -=  *=  /=  %=
++  --
**
&&  ||  !
&  |  ^  ~  <<  >>
?  :
->  =>
::
@
#
`
```

Their absence is intentional. A future version should add a symbol only when a real language capability requires it and the addition improves Eristavi more than it expands the programmer's vocabulary.

## 10. Expression precedence — locked

From highest to lowest, pre-0.1 uses:

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

Assignment `=` is not part of this hierarchy because assignment is not an expression.

Examples:

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

Parentheses may always express explicit grouping.

See `PRECEDENCE.md` for the full locked rationale and examples.

## Governing rule

> Use symbols where their meaning is compact and universally clear, use words where symbols reduce readability, and do not add shorthand until it demonstrates a real benefit. `%` has one precise pre-0.1 meaning as signed `Int` remainder; Float remainder/modulo remains an explicitly named library concern. Postfix access binds strongest, prefix operations follow, multiplication precedes addition, comparisons are non-associative, `not` applies after comparisons, `and` precedes `or`, and assignment is not a value-producing expression.
