# Eristavi Ordinary Value Equality

> **Status: Locked for pre-0.1**

This document defines equality for ordinary Eristavi values and how `==` / `!=` compose across nested value structure.

The governing rule is:

> Two ordinary values of the same static type are equal when every corresponding stored component is equal according to that component type's own equality semantics.

## 1. Equality is structural for ordinary user-defined values

Ordinary user-defined `type` values compare by their stored fields.

```eri
type User {
    id Int;
    name Text;
}

let first be User {
    id = 1;
    name = "Anna";
};

let second be User {
    id = 1;
    name = "Anna";
};

output(first == second); // true
```

Conceptually, the comparison is equivalent to asking whether every corresponding field is equal:

```eri
first.id == second.id
and first.name == second.name
```

The compiler performs this composition automatically; programmers do not write generated field-by-field equality code.

Field declaration order does not create positional construction semantics, but corresponding declared fields define the stored structure being compared.

## 2. Equality composes recursively

Nested ordinary values use the same rule recursively.

```eri
type Address {
    city Text;
}

type User {
    name Text;
    address Address;
}
```

For two `User` values, `address` is compared using `Address` equality, and `Address` compares its own stored fields.

The rule is therefore compositional rather than special-cased by nesting depth.

## 3. Component types keep their own equality semantics

Structural equality never changes the meaning of equality for a field merely because that field appears inside another value.

Core examples:

- `Int` uses integer value equality;
- `Bool` compares `true` / `false` values;
- `Text` compares the actual Unicode scalar sequence under the locked Text model;
- `Float` uses the already-locked IEEE 754 equality semantics;
- `identity T` uses logical identity equality, not current field-state equality;
- `maybe T` uses optional-value equality as defined below.

This means an ordinary value containing an `identity T` field compares that field by logical identity.

```eri
type Session {
    name Text;
    counter identity Counter;
}
```

Two `Session` values with equal `name` fields and the same `Counter` logical identity compare equal. Two otherwise identical `Session` values whose counters are independently created identities compare unequal.

No hidden state comparison is performed for identity fields.

## 4. `maybe T` equality

`maybe T` is equality-comparable when `T` is equality-comparable.

The rules are:

- `none == none` is true;
- `none` compared with a present value is false;
- two present values compare their contained values using `T` equality;
- `!=` is the logical inverse of `==`.

Existing contextual typing permits ordinary checks such as:

```eri
if user == none {
    ...
}
```

`none` does not become a separate universal null type.

## 5. Ordered collection equality

For ordered collection values, equality is structural and order-sensitive when the element type is equality-comparable.

Two ordered collections are equal when:

1. they have the same number of elements; and
2. each corresponding element compares equal using the element type's equality semantics.

Conceptually:

```eri
[1, 2, 3] == [1, 2, 3] // true
[1, 2, 3] == [3, 2, 1] // false
```

This rule does not choose the final concrete pre-0.1 collection type name (`Array`, `List`, or another name). It locks only the equality semantics of ordered collection values once that collection abstraction is finalized.

A collection whose element type is not equality-comparable does not automatically support equality.

## 6. Equality-comparable types are derived structurally

Equality availability is a static property determined by the complete type structure.

An ordinary user-defined value type supports `==` and `!=` only when every stored field type supports equality.

For example:

```eri
type Point {
    x Float;
    y Float;
}
```

is equality-comparable because both fields are equality-comparable.

If a future stored field type has no equality semantics, then an ordinary type containing that field is not automatically equality-comparable either.

The compiler should identify the specific field or nested type path that prevents structural equality.

This derived property is an internal type-system fact. Pre-0.1 introduces no `Equatable` keyword, trait, annotation, or protocol syntax.

## 7. Same static type is required

Ordinary structural equality is type-preserving.

The operands of ordinary value equality must have the same compatible static semantic type under the language's existing optional-context rules.

Eristavi does not compare unrelated user-defined types merely because their fields happen to have the same shape.

There is no implicit numeric coercion for equality either. In particular, the locked no-implicit-conversion rule remains in force:

```eri
10 == 10.0 // compile-time type error
```

The programmer must perform an explicit conversion when a deliberate cross-numeric-type comparison is required.

Likewise, `T` and `identity T` do not compare implicitly.

## 8. Float and NaN remain IEEE-compositional

Structural equality does not special-case `Float` to restore reflexivity.

The locked Float rule remains:

```text
NaN == NaN    false
NaN != NaN    true
```

Therefore an ordinary value containing a NaN field may compare unequal to itself.

```eri
type Measurement {
    value Float;
}
```

If `measurement.value` is NaN, then:

```eri
measurement == measurement // false
```

This is intentional. Nesting a Float inside another value must not silently change Float equality semantics.

## 9. `!=` is the inverse of `==`

For every equality-comparable type, `!=` is the Boolean inverse of that type's `==` result.

Eristavi does not provide a separately overloadable inequality operation.

## 10. No user-defined equality overloading in pre-0.1

Pre-0.1 does not define:

```text
operator ==
operator !=
Equatable
custom equality hooks
```

Ordinary value equality has one language-defined structural meaning.

Domain-specific notions of equivalence should use clearly named ordinary functions when needed, for example conceptually:

```eri
sameCustomer(first, second)
equivalentDocument(first, second)
matchesIgnoringCase(first, second)
```

Such functions do not redefine `==`.

## 11. Resources and non-value entities do not gain equality accidentally

Deterministically managed resource handles governed by `with` do not automatically acquire structural equality merely because `==` exists for ordinary values.

Any future non-value-like entity must receive equality semantics through an explicit language or library design decision rather than through a representation accident such as address comparison.

## 12. Diagnostics

When equality is invalid, diagnostics should explain the semantic reason.

Examples include:

```text
Cannot compare User and Customer with ==.
Equality requires compatible static types.
```

or:

```text
Cannot compare Job with ==.
Field `callback` has a type that does not define equality.
```

For nested structural failures, the diagnostic should identify the relevant field path when practical.

## Governing principle

> Ordinary Eristavi equality is structural, recursive, type-preserving, and compositional. Each component retains its own equality semantics; identities compare by identity, Float retains IEEE behavior, optional and ordered collection values compose element equality, and no custom equality overloading or implicit cross-type coercion is introduced in pre-0.1.
