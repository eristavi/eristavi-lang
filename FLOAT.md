# Eristavi Float Semantics

> **Status: Locked for pre-0.1**

This document defines the semantic meaning of Eristavi `Float` values and floating-point arithmetic.

## 1. Representation

`Float` is IEEE 754 binary64 on every supported Eristavi target.

This means `Float` has one language-defined representation model regardless of whether code is compiled to native machine code, C, JavaScript, or WebAssembly.

The target implements Eristavi floating-point semantics; the target does not redefine them.

## 2. Rounding

Ordinary floating-point operations use IEEE 754 round-to-nearest, ties-to-even semantics.

Decimal floating-point source literals are converted to the nearest representable binary64 value using the same rounding rule.

The compiler must not allow a target's extended intermediate precision to change observable Eristavi results.

## 3. Arithmetic

The ordinary arithmetic operations on `Float` are:

```eri
a + b
a - b
a * b
a / b
-a
```

Each ordinary operation has binary64 semantics.

An implementation may optimize or reorder only when it can prove that the observable Eristavi result is unchanged.

In particular, an expression such as:

```eri
a * b + c
```

must not silently become a fused multiply-add operation when contraction would change the binary64 result. A future explicit fused operation may be provided separately if justified.

## 4. Infinity and NaN

`Float` retains the IEEE 754 special values:

- positive infinity;
- negative infinity;
- NaN.

Floating-point division by zero follows IEEE 754 behavior rather than producing the integer arithmetic fault used by `Int`.

Examples conceptually include:

```eri
1.0 / 0.0   // positive infinity
-1.0 / 0.0  // negative infinity
0.0 / 0.0   // NaN
```

These values are part of floating-point semantics, not ordinary checked `fails` values.

The language does not require special source literal spellings for NaN or infinity in pre-0.1. APIs for inspecting or constructing special values belong to the type or standard library rather than lexer vocabulary.

## 5. NaN payloads are not ordinary language semantics

IEEE 754 hardware may carry implementation-specific NaN payload bits.

Ordinary Eristavi programs do not observe NaN payload identity as part of normal `Float` semantics.

The compiler or runtime may canonicalize NaN representations when required for deterministic cross-target behavior.

## 6. Comparisons

`Float` comparisons follow IEEE 754 comparison behavior.

Examples:

```eri
1.0 == 1.0     // true
0.0 == -0.0    // true
```

NaN is unordered:

```text
NaN == NaN     false
NaN != NaN     true
NaN < x        false
NaN <= x       false
NaN > x        false
NaN >= x       false
```

for any ordinary `Float` value `x`, including another NaN where applicable.

This behavior is part of `Float` semantics and should be documented clearly by tooling and standard-library APIs.

## 7. Signed zero

IEEE 754 positive and negative zero are preserved:

```text
+0.0
-0.0
```

They compare equal with `==`, but operations permitted by IEEE 754 may distinguish their sign.

Eristavi does not erase signed zero merely to simplify equality.

## 8. Overflow and underflow

Floating-point overflow follows IEEE 754 and produces positive or negative infinity as appropriate.

Underflow uses gradual underflow with subnormal values. Implementations must not silently enable flush-to-zero or denormals-are-zero behavior when that would alter Eristavi results.

## 9. No implicit `Int` to `Float` conversion

`Int` is a signed 64-bit integer, while binary64 cannot represent every signed 64-bit integer exactly.

Therefore Eristavi does not silently convert `Int` to `Float` in mixed arithmetic.

For example:

```eri
let result be 10 + 2.5;
```

is a type error unless the programmer explicitly converts one operand through the appropriate numeric API.

This prevents silent precision loss for values such as:

```text
9007199254740993
```

which cannot be represented exactly as binary64.

## 10. No implicit `Float` to `Int` conversion

A `Float` is never silently converted to `Int`.

For example:

```eri
let count Int be 19.95;
```

is invalid.

Explicit conversion must make the intended behavior clear, such as truncation, rounding, flooring, or another chosen policy. The exact conversion API belongs to the numeric type or standard library rather than the core grammar.

## 11. Cross-target determinism

Eristavi's floating-point semantics are source-language semantics.

A backend must not inherit target-specific behavior that changes an Eristavi program's defined meaning.

This includes avoiding observable differences caused by:

- excess intermediate precision;
- unsafe contraction into fused operations;
- flush-to-zero modes;
- non-Eristavi rounding modes;
- target-specific NaN payload behavior when exposed accidentally.

Optimizations remain allowed when they preserve Eristavi's observable `Float` semantics.

## 12. Relationship to lexical syntax

`LEXICAL_RULES.md` defines how floating-point literals are written.

The lexical syntax and the semantic type are separate concerns:

- the lexer recognizes a decimal floating-point literal;
- semantic analysis assigns or infers `Float`;
- constant evaluation converts the literal to the correctly rounded binary64 value.

## 13. Governing rule

> `Float` is deterministic IEEE 754 binary64 with round-to-nearest, ties-to-even behavior, IEEE special values and signed zero, gradual underflow, and no implicit lossy conversion to or from `Int`.
