# Eristavi Integer Division and Remainder

> **Status: Locked for pre-0.1**

This document defines the signed `Int` division/remainder relationship and the applicability of the `%` operator.

The governing rule is:

> In pre-0.1, `%` is an `Int`-only remainder operator. Integer division truncates toward zero, remainder follows that division rule, and floating-point remainder/modulo is not expressed with `%`.

## 1. `%` applies only to `Int`

Both operands of `%` must have static type `Int`, and the result has type `Int`.

```eri
let remainder be 10 % 3; // 1
```

This is invalid:

```eri
let remainder be 10.5 % 3.0; // compile-time error
```

Mixed numeric operands remain invalid as well; Eristavi does not implicitly convert between `Int` and `Float`.

## 2. Signed integer division truncates toward zero

For `Int`, `/` discards any fractional mathematical part by truncating the quotient toward zero.

Conceptually:

```text
 10 / 3   =  3
-10 / 3   = -3
 10 / -3  = -3
-10 / -3  =  3
```

This is source-language behavior and must not depend on the target CPU, C compiler, JavaScript runtime, WebAssembly backend, or another implementation environment.

## 3. Remainder follows integer division

For valid nonzero divisor `b`, the remainder `r` is defined by the truncating integer quotient `q`:

```text
q = trunc_toward_zero(a / b)
r = a - q * b
```

Therefore:

```text
 10 % 3   =  1
-10 % 3   = -1
 10 % -3  =  1
-10 % -3  = -1
```

A nonzero remainder has the same sign as the dividend `a`.

Its magnitude is always smaller than the magnitude of the divisor:

```text
abs(r) < abs(b)
```

when the operation is valid.

This is remainder semantics, not a separate always-nonnegative mathematical modulo operation.

## 4. Division or remainder by zero

`Int` division or remainder by zero is invalid.

When the zero divisor is provable at compile time, the compiler rejects the program:

```eri
let value be 10 % 0; // compile-time error
```

When it depends on runtime data, execution produces the defined integer arithmetic fault used by Eristavi checked arithmetic.

The fault is a runtime defect, not an ordinary checked `fails` value.

## 5. Signed minimum divided by `-1`

The mathematical quotient of:

```text
-9223372036854775808 / -1
```

cannot be represented by Eristavi `Int`.

Therefore the operation is an integer overflow fault. If the invalid pair is known at compile time, it is rejected there; otherwise it produces the defined runtime arithmetic fault.

For consistency, the corresponding remainder operation with the same exceptional operand pair is also treated as an arithmetic overflow fault in pre-0.1 rather than exposing target-specific behavior:

```text
-9223372036854775808 % -1
```

## 6. No Float `%`

`Float` arithmetic remains the locked IEEE 754 operation set:

```eri
a + b
a - b
a * b
a / b
-a
```

`%` is not added to that set.

Floating-point ecosystems distinguish several reasonable concepts such as truncated remainder, mathematical modulo, and IEEE remainder. Eristavi does not assign one of those meanings to `%` merely for familiarity.

If real programs require floating-point remainder or modulo, explicitly named numeric/standard-library operations may be designed later with their exact semantics stated in their names and contracts.

No such future API changes the meaning of `%`.

## 7. Diagnostics

A compiler should distinguish at least:

- `%` applied to `Float` or another unsupported type;
- mixed `Int` / `Float` operands;
- compile-time-known zero divisor;
- runtime-dependent zero divisor;
- the signed-minimum / `-1` overflow pair.

For a Float use, a useful diagnostic is conceptually:

```text
Operator `%` is defined only for Int in Eristavi pre-0.1.
Floating-point remainder/modulo requires an explicitly defined numeric operation.
```

## Governing principle

> `%` has one precise pre-0.1 meaning: signed `Int` remainder associated with truncation-toward-zero integer division. It is not a generic numeric modulo operator.
