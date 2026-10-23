# Eristavi Standard Textual Output

> **Status: Locked for pre-0.1**

This document defines Eristavi's simple default textual-output operation.

The governing rule is:

> Use one ordinary standard-library function, `output(...)`, for simple textual output. Do not add a special output statement or duplicate alias.

## 1. Canonical form

Simple output uses an ordinary function call:

```eri
output("Hello, world!");
```

`output` is not a keyword and does not introduce special grammar.

This is intentionally different from statement-like forms such as:

```text
print value;
echo value;
```

Eristavi keeps output inside the existing function-call model.

## 2. Standard environment

`output` is part of the pre-0.1 standard environment and is available without an explicit import in ordinary programs.

Conceptually, it is a standard-library/prelude function rather than compiler-only syntax.

The bootstrap compiler may implement it internally at first, but that implementation detail does not change its source-language classification.

## 3. Pre-0.1 behavior

The canonical pre-0.1 form takes one value:

```eri
output(value);
```

It writes a human-readable textual representation of that value to the program's standard textual output and terminates the output with a line break.

The bootstrap implementation must support the core value types needed by early programs, including `Text`, `Int`, `Float`, and `Bool`.

Exact richer formatting rules for arbitrary user-defined values are standard-library design work and are not part of the core grammar freeze.

## 4. No alias

Pre-0.1 does not define `print`, `echo`, `say`, or `out` as aliases for `output`.

This follows Eristavi's one-obvious-way principle.

The short name `out` remains available for a future stream abstraction if such an API is eventually justified; it is not reserved by the language.

## 5. Examples

```eri
let x be 40;
let y be 2;

output(x + y);
```

Expected textual output:

```text
42
```

Text output:

```eri
output("Ready");
```

Boolean output:

```eri
output(true);
```

## 6. Vocabulary status

`output` is an ordinary predeclared name, not a reserved lexical keyword.

A lexer tokenizes it as an identifier. Name resolution supplies the standard `output` function when it has not been replaced by an invalid conflicting declaration under the language's predeclared-name rules.

The detailed policy for collisions with predeclared standard names may be specified with the broader standard-library namespace model; no additional keyword is introduced here.

## Governing principle

> Output should be obvious to read, ordinary to call, and cheap in language vocabulary: `output(value);`.
