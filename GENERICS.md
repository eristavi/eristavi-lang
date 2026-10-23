# Eristavi Inferred Generic Abstraction

> **Status: Locked for pre-0.1**

This document defines the pre-0.1 generic abstraction model.

## 1. Generic relationships are inferred

Eristavi pre-0.1 does not require programmers to declare generic type variables explicitly.

A function may become implicitly generic when the compiler can infer a consistent relationship between its parameter types, operations, and result type.

Example:

```eri
function identity(value) {
    return value;
}
```

The source code does not declare a type variable such as `T`. Internally, the compiler may understand the function as accepting a value of some type and returning that same type.

The programmer writes the relationship through ordinary code; the compiler derives the generic type relationship.

The design rule is:

> Generic type variables are compiler concepts in pre-0.1, not programmer vocabulary.

## 2. Type relationships must remain consistent

The compiler must unify inferred parameter and result relationships statically.

```eri
function choose(first, second, useFirst Bool) {
    if useFirst {
        return first;
    }

    return second;
}
```

The compiler infers that `first`, `second`, and the returned value must share one compatible type.

Valid uses include:

```eri
let number be choose(10, 20, true);
let name be choose("Anna", "Maria", false);
```

An inconsistent use is rejected at compile time:

```eri
let value be choose(10, "Anna", true);  // compile-time error
```

Eristavi must not silently widen such a call to an untyped or dynamically typed value.

## 3. Collections participate in inference

Generic relationships may be inferred through collection operations when the compiler knows the collection's element relationship.

```eri
function first(items) {
    return items.first;
}
```

When called with a collection of `User`, the result is inferred as `User`. When called with a collection of `Text`, the result is inferred as `Text`.

The programmer does not write forms such as:

```text
List<User>
List[User]
List.User
List:User
```

No such generic container syntax is part of pre-0.1.

## 4. No dynamic fallback

Implicit generic inference is still static typing.

If the compiler cannot determine a safe and consistent type relationship, compilation fails with a diagnostic explaining the conflicting requirements.

The compiler must not resolve failed inference by converting the value to a hidden dynamic type, universal object type, or unchecked runtime representation.

## 5. No explicit generic parameter syntax in pre-0.1

The initial language intentionally has no user-written equivalents of:

```text
<T>
[T]
T where Comparable
where T: Comparable
function name<T>(...)
```

There are also no explicit generic constraint declarations, trait bounds, generic specialization annotations, or variance syntax in pre-0.1.

If an abstraction cannot be expressed safely through inference, the programmer must use a concrete implementation for now.

An explicit abstraction system may be designed later only when real programs demonstrate requirements that inference alone cannot express.

## 6. Operations constrain inferred types

The body of a function contributes type requirements.

For example:

```eri
function double(value) {
    return value + value;
}
```

This function is valid only for types for which the selected `+` operation is statically valid under Eristavi's type rules.

The compiler must infer from actual operations rather than assume that every type supports every operation.

Pre-0.1 does not expose those requirements through user-written constraint syntax.

## 7. Calls specialize the inferred relationship

At each valid call site, the compiler resolves the inferred generic relationship to concrete types.

```eri
let number be identity(10);
let text be identity("Hello");
```

The first call produces `Int`; the second produces `Text`.

The language semantics do not require a particular implementation strategy. The compiler may monomorphize, share generated code, use internal type metadata, or choose another representation as long as observable behavior remains statically typed and equivalent.

## 8. Public and module-visible behavior

An implicitly generic function may participate in a module API only when the compiler can derive a stable checked contract from its declaration and body.

The compiler must record enough type information in compiled module metadata for importing modules to type-check calls without reparsing implementation details as an unchecked dynamic API.

Tooling should be able to display the inferred contract in a readable form even though source code does not expose generic variables.

For example, tooling may explain:

```text
identity(value) -> same type as value
```

or, as an internal diagnostic notation:

```text
(T) -> T
```

The internal notation is explanatory tooling, not Eristavi source syntax.

## 9. Diagnostics and explainability

When inference fails, diagnostics should describe the relationship in programmer terms.

For example:

```text
choose requires `first` and `second` to have the same type.
`first` is Int.
`second` is Text.
```

The compiler should avoid exposing implementation-specific type-variable identifiers unless they materially help explain the problem.

Future tooling such as `erist explain` may show inferred parameter, return, collection-element, and operation requirements.

## 10. What pre-0.1 deliberately postpones

The initial generic model does not attempt to solve:

- explicit generic type declarations;
- traits or interfaces used as generic constraints;
- associated types;
- higher-kinded types;
- specialization syntax;
- variance annotations;
- explicit generic argument application;
- generic metaprogramming.

These are postponed until concrete Eristavi programs demonstrate a requirement for them.

## 11. Governing rule

The pre-0.1 rule is:

> Functions may be implicitly generic when the compiler can infer consistent static type relationships. If it cannot, compilation fails rather than requiring generic syntax or falling back to dynamic typing.
