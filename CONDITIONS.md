# Eristavi Condition Typing

> **Status: Locked for pre-0.1**

Eristavi conditions are explicitly typed. `if` and `while` require an expression whose static type is `Bool`.

There is no general truthiness model in pre-0.1.

## 1. Bool-only conditions

Valid:

```eri
let ready Bool be true;

if ready {
    output("Ready");
}
```

Valid comparisons naturally produce `Bool`:

```eri
if age >= 18 {
    output("Adult");
}

while count < 10 {
    count = count + 1;
}
```

Boolean operators also produce and consume `Bool` values:

```eri
if active and verified {
    start();
}

if not connected {
    reconnect();
}
```

## 2. No numeric truthiness

Numbers are not conditions merely because they are zero or non-zero.

Invalid:

```text
if count {
    ...
}
```

Use an explicit comparison:

```eri
if count != 0 {
    ...
}
```

The same rule applies to `Float`.

## 3. No Text truthiness

`Text` values do not become false when empty or true when non-empty.

Invalid:

```text
if name {
    ...
}
```

Use an explicit property or comparison provided by the type/library model, for example conceptually:

```eri
if name.characters.count > 0 {
    ...
}
```

## 4. No collection truthiness

Collections are not implicitly false when empty or true when non-empty.

Invalid:

```text
if users {
    ...
}
```

The programmer asks the intended question explicitly, for example:

```eri
if users.count > 0 {
    ...
}
```

The exact collection API may evolve, but the condition itself must still evaluate to `Bool`.

## 5. No optional-value truthiness

A `maybe T` value is not itself a condition.

Invalid:

```text
if user {
    ...
}
```

Use an explicit absence check:

```eri
if user != none {
    output(user.name);
}
```

Existing flow-sensitive narrowing for `maybe` values applies after explicit `none` checks.

## 6. No identity truthiness

An `identity T` value is not implicitly true merely because an identity handle exists.

Invalid:

```text
if counter {
    ...
}
```

If absence is meaningful, use `maybe identity T` and compare explicitly with `none`.

## 7. No implicit conversion to Bool

Eristavi does not define implicit conversions such as:

```text
Int   -> Bool
Float -> Bool
Text  -> Bool
T     -> Bool
```

A type may expose ordinary APIs that explicitly answer a Boolean question, but such APIs return `Bool`; they do not create a language-wide truthiness protocol.

## 8. `if` and `while`

The semantic rule is identical for both constructs:

```text
condition-expression static type == Bool
```

The grammar continues to accept an ordinary expression syntactically:

```text
if-statement :=
    "if" expression block [ "else" block ]

while-statement :=
    "while" expression block
```

The type checker rejects the construct when the expression does not have static type `Bool`.

## 9. Diagnostics

The compiler should explain the intended explicit test instead of merely reporting a generic mismatch.

For example:

```text
Condition must have type Bool; found Int.
Eristavi does not use numeric truthiness.
Compare the value explicitly, for example: count != 0
```

Diagnostics may suggest a type-appropriate explicit test when one is obvious.

## Governing rule

> Eristavi conditions express Boolean questions explicitly. `if` and `while` accept only `Bool`; values of other types never acquire truthiness implicitly.
