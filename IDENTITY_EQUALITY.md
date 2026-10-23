# Eristavi Identity Equality

> **Status: Locked for pre-0.1**

This document defines equality semantics for explicit `identity T` values.

## 1. Equality follows identity semantics

For two values of the same `identity T` type, `==` asks whether both handles refer to the same logical identity.

```eri
type Counter {
    value Int;
}

let first be identity Counter {
    value = 0;
};

let second be first;

output(first == second);   // true
```

Copying an identity handle preserves the same logical identity, so the copied handle compares equal to the original.

The design rule is:

> For `identity T`, equality means same logical identity.

## 2. Equal state does not imply equal identity

Two independently created identities remain different even if all of their fields currently contain equal data.

```eri
let first be identity Counter {
    value = 0;
};

let second be identity Counter {
    value = 0;
};

output(first == second);   // false
```

Changing their state so that the fields become equal does not merge the identities and does not make them equal.

Likewise, changing the state of one handle does not change the identity relationship between aliases of that same object.

## 3. Inequality

`!=` is the logical inverse of identity equality.

```eri
let first be identity Counter {
    value = 0;
};

let second be first;

output(first != second);   // false
```

No additional identity-comparison operator such as `is`, `same`, or pointer-address comparison is introduced.

## 4. No implicit value/identity comparison

`T` and `identity T` are different semantic types and are not implicitly converted.

Therefore this is invalid:

```eri
let value be Counter {
    value = 0;
};

let shared be identity Counter {
    value = 0;
};

output(value == shared);   // compile-time error
```

The programmer must make the intended semantic relationship explicit rather than relying on hidden conversion.

Comparing different identity types is likewise invalid unless a future explicitly defined abstraction provides a common comparable identity type.

## 5. Optional identity

`maybe identity T` follows the existing `none` model.

For equality involving two `maybe identity T` values:

- `none == none` is true;
- `none` compared with a present identity is false;
- two present values compare using identity equality.

Example:

```eri
let selected maybe identity Counter be none;
let counter be identity Counter {
    value = 0;
};

output(selected == none);      // true
selected = counter;
output(selected == counter);   // true after presence is established by the operation
```

This does not introduce null references; `none` remains the only ordinary absence value.

## 6. Identity is not an address

Identity equality is defined in terms of the logical object, not a physical memory address.

The runtime may move, compact, relocate, or otherwise change the physical representation of an identity object without changing its identity relationship.

Programs cannot observe or compare raw addresses through `==`.

## 7. Value-state comparison remains separate

This decision does not define a second automatic comparison mode for the fields inside an identity object.

If a program needs to compare the current state of two identities, it should do so explicitly through their fields or through an ordinary function/library operation designed for that type.

Eristavi does not add a second equality operator merely to compare identity state.

Ordinary user-defined value equality is now separately locked as structural and compositional in `VALUE_EQUALITY.md`. When an ordinary value contains an `identity T` field, that field contributes its existing logical-identity equality semantics to the enclosing structural comparison. The enclosing value does not reinterpret identity as state equality.

## 8. Resources remain separate

This identity-equality rule does not apply to deterministically managed resource handles governed by `with`.

Resource comparison, if ever required, is a separate API/type concern and cannot use `identity` to bypass resource ownership rules.

## 9. Rationale

This design preserves Eristavi's existing principles:

- shared identity is explicit in the type;
- one existing equality operator is reused rather than adding redundant syntax;
- equality remains predictable from the semantic type;
- no raw-pointer or address model leaks into ordinary code;
- identical state does not silently collapse distinct identities;
- the compiler/runtime retain freedom to choose the physical representation.

The design rule is:

> Values describe data. Identities describe the continuing object that owns changing data.
