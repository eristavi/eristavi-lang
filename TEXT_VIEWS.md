# Eristavi Unicode Text Views — pre-0.1 clarification

This document makes the already-frozen explicit Text-view model precise without adding new source-level types or syntax.

## 1. Text is not directly indexed

Direct integer indexing remains invalid:

```eri
text[0] // compile-time error
```

A program must first select the semantic unit it intends to observe:

```eri
text.characters
text.scalars
text.bytes
```

## 2. `characters`

`text.characters` is a read-only view of Unicode extended grapheme clusters using the Unicode version pinned by the Eristavi toolchain.

```eri
text.characters.count
text.characters[0]
```

Indexing returns `Text` containing exactly one extended grapheme cluster. Eristavi does not introduce a separate programmer-visible `Character` type in pre-0.1.

## 3. `scalars`

`text.scalars` is a read-only view of Unicode scalar values.

```eri
text.scalars.count
text.scalars[0]
```

Indexing returns `Text` containing exactly one Unicode scalar value. Eristavi does not introduce a separate programmer-visible `Scalar` type in pre-0.1.

## 4. `bytes`

`text.bytes` is a read-only view of the canonical UTF-8 encoding of the Text value.

```eri
text.bytes.count
text.bytes[0]
```

Indexing returns `Int` in the range `0..255`. Eristavi does not introduce a separate programmer-visible `Byte` type in pre-0.1.

## 5. Indexing and bounds

All three views use zero-based `Int` indexes.

A valid index satisfies:

```text
0 <= index < view.count
```

A runtime-dependent invalid index produces a defined bounds fault. Negative indexes are out of bounds rather than from-end shorthand.

## 6. Views are read-only

The views expose observation, not mutation:

```eri
text.characters[0] = "A"; // compile-time error
text.bytes[0] = 65;        // compile-time error
```

A view may be stored in an ordinary or `fixed` local binding, but it cannot be used to mutate the underlying Text.

## 7. Unicode version

The pre-0.1 bootstrap toolchain pins Unicode **17.0.0** for identifier normalization/classification and extended grapheme-cluster behavior. A future toolchain version may deliberately advance the pinned Unicode version, but semantics must not silently depend on the host language or operating system Unicode tables.

## Governing rule

> Text indexing is explicit about the unit being observed: grapheme clusters and scalar values yield Text, UTF-8 bytes yield Int, and the views are read-only.
