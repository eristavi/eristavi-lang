# Eristavi Expression Precedence

> **Status: Locked for pre-0.1**

This document defines the pre-0.1 expression precedence and associativity model. Eristavi deliberately keeps the table small, rejects comparison chaining, and keeps assignment outside the expression hierarchy.

## 1. Precedence table — highest to lowest

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

Assignment `=` is not an expression operator and therefore has no precedence level.

## 2. Postfix forms bind strongest

Calls, indexing, and member access bind more tightly than prefix and infix operators and may chain from left to right.

```eri
users[0].name
loadUser(1).name
customer.address.city
```

Conceptually:

```text
((users[0]).name)
((loadUser(1)).name)
((customer.address).city)
```

Semantic validation still determines whether a particular call, index, or member access is valid for the operand type.

## 3. Prefix forms

Unary numeric negation, checked-error propagation, and explicit identity creation are prefix forms.

```eri
-value
-(a + b)
try loadUser(id)
identity Counter {
    value = 0;
}
```

They bind more tightly than multiplicative and additive arithmetic.

For example:

```eri
-a * b
```

means:

```eri
(-a) * b
```

and:

```eri
try loadPrice() + tax
```

means:

```eri
(try loadPrice()) + tax
```

There is no unary `+` in pre-0.1.

## 4. Multiplicative arithmetic

The operators:

```text
*  /  %
```

have equal precedence and associate left to right.

```eri
a * b / c
```

means:

```eri
(a * b) / c
```

## 5. Additive arithmetic

The operators:

```text
+  -
```

have equal precedence and associate left to right.

Multiplicative arithmetic binds more strongly:

```eri
a + b * c
```

means:

```eri
a + (b * c)
```

## 6. Comparisons are non-associative

The comparison operators are:

```text
==  !=  <  <=  >  >=
```

They have one shared precedence level and do not associate with one another.

Valid:

```eri
age >= 18
user == none
first != second
```

Invalid without explicit Boolean composition:

```text
10 < age < 65
a == b == c
a < b == c
```

Write the intended relationship explicitly:

```eri
age > 10 and age < 65
a == b and b == c
```

Eristavi therefore does not inherit C-style accidental Boolean/numeric comparison chains and does not introduce special comparison-chain semantics in pre-0.1.

## 7. `not` binds below comparisons

`not` applies to the result of a comparison before `and` or `or` are considered.

```eri
not a == b
```

means:

```eri
not (a == b)
```

Likewise:

```eri
not age >= 18
```

means:

```eri
not (age >= 18)
```

Parentheses may always make the intended grouping explicit.

This ordering is intentional because Eristavi uses the readable word operator `not` rather than symbolic `!`.

## 8. `and` binds above `or`

```eri
a or b and c
```

means:

```eri
a or (b and c)
```

Complex Boolean expressions may still use parentheses whenever they improve readability.

## 9. Assignment is not an expression

The token `=` is used by assignment statements and grammar-defined initialization contexts, but it does not produce a value and cannot appear as a general subexpression.

Valid:

```eri
price = 50;
user.name = "Maria";
```

Also valid in named-field construction:

```eri
let user be User {
    id = 1;
    name = "Anna";
};
```

Invalid:

```text
a = b = c;
if x = 10 {
    ...
}
let value be (x = 20);
```

This removes assignment from the precedence table and prevents accidental assignment in conditions or other value expressions.

## 10. Parentheses override precedence

Parentheses explicitly group an expression wherever the grammar permits an expression.

```eri
let result be (a + b) * c;
```

Programmers should use grouping when it improves clarity even when the precedence rule already produces the same meaning.

## Governing rule

> Postfix access binds strongest; prefix operations follow; multiplication precedes addition; comparisons are non-associative; `not` applies after comparisons; `and` precedes `or`; and assignment is a statement-level operation rather than a value-producing expression.
