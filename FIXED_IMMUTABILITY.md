# Eristavi Deep `fixed` Immutability

> **Status: Locked for pre-0.1**

This document defines how Eristavi's deep `fixed` guarantee interacts with explicit shared `identity` values.

The governing rule is:

> A `fixed` guarantee is transitive across ordinary value structure. If a value's static type contains `identity` at any reachable stored position, that value is not eligible for `fixed`.

## 1. `fixed` is a real deep guarantee

`fixed` means that the complete ordinary value reachable through that binding or field cannot observably change after initialization.

```eri
type Address {
    city Text;
}

type User {
    name Text;
    address Address;
}

let fixed user be User {
    name = "Anna";
    address = Address {
        city = "Paphos";
    };
};
```

After initialization, neither the binding nor its nested ordinary value state may be changed through `user`.

```eri
user.name = "Maria";           // error
user.address.city = "Limassol"; // error
user = anotherUser;              // error
```

## 2. Identity-bearing values are not deep-fixable

An `identity T` represents explicitly shared logical identity whose state may be changed through another handle.

Therefore this ordinary value type is valid by itself:

```eri
type ViewModel {
    counter identity Counter;
}
```

and an ordinary mutable value of that type is valid:

```eri
let model be ViewModel {
    counter = sharedCounter;
};
```

But the type is not eligible for a deep `fixed` binding:

```eri
let fixed model be ViewModel {
    counter = sharedCounter;
}; // compile-time error
```

Otherwise another alias could mutate `sharedCounter`, changing state observable through `model` while `model` claims to be deeply immutable.

## 3. The rule is transitive

The compiler checks the complete static value structure, not only direct fields.

```eri
type Session {
    counter identity Counter;
}

type Account {
    session Session;
}
```

`Account` is not deep-fixable because the path:

```text
Account -> Session -> identity Counter
```

reaches shared mutable identity.

Therefore:

```eri
let fixed account be Account {
    session = session;
}; // compile-time error
```

The same rule applies through any ordinary stored-value composition supported by the language, including nested user-defined values, optional values, and collection element/value positions.

For example, `maybe identity User` is not deep-fixable even when a particular runtime value currently contains `none`. Eligibility is determined from the static type's possible value structure, not from the current runtime contents.

## 4. `fixed` fields use the same rule

A field declared `fixed` receives the same deep immutability guarantee as a `fixed` binding.

Therefore a fixed field whose type is identity-bearing is invalid:

```eri
type Model {
    fixed counter identity Counter; // compile-time error
}
```

The restriction is also transitive:

```eri
type Session {
    counter identity Counter;
}

type Model {
    fixed session Session; // compile-time error
}
```

This prevents `fixed` from acquiring a second shallow meaning such as "the handle cannot be replaced, but the referenced object may change."

## 5. Direct `fixed identity` remains invalid

The already-established direct case remains invalid:

```eri
let fixed counter be identity Counter {
    value = 0;
}; // compile-time error
```

`identity Counter` is itself identity-bearing and therefore not deep-fixable.

## 6. No implicit freezing of aliases

Applying `fixed` to an ordinary value must never change the mutation capability of independent identity handles elsewhere in the program.

The compiler does not silently freeze a shared identity object merely because one containing value is requested as `fixed`.

Such behavior would make the meaning of one alias unexpectedly depend on another alias.

## 7. No implicit snapshot or copy

The compiler also does not make an implicit ordinary-value snapshot of an identity in order to satisfy `fixed`.

This is rejected rather than silently changing identity semantics:

```eri
let fixed model be ViewModel {
    counter = sharedCounter;
};
```

If a future explicit identity-to-value snapshot operation is introduced, the programmer may use that operation deliberately. No such conversion is implied by `fixed`.

## 8. Deep-fixable is a compiler property, not source syntax

The compiler may internally classify a static type as **deep-fixable** when its reachable ordinary stored-value structure contains no `identity` position.

This is not a programmer-written trait, annotation, keyword, or generic constraint in pre-0.1.

Conceptually:

```text
Int                         deep-fixable
Text                        deep-fixable
Address                     deep-fixable if all stored fields are deep-fixable
maybe Address               deep-fixable if Address is deep-fixable
identity Counter            not deep-fixable
maybe identity Counter      not deep-fixable
ViewModel                   not deep-fixable if it contains identity Counter
```

A `fixed` binding or `fixed` field requires a deep-fixable static type.

## 9. Diagnostics

The compiler should identify the identity-bearing path that prevents a deep `fixed` guarantee.

For example:

```text
Cannot make `account` fixed: Account is not deeply immutable.

Account.session -> Session.counter -> identity Counter

`fixed` requires that no reachable stored value can change through shared identity.
```

This is preferable to a generic type mismatch because the programmer should understand exactly which nested field violates the guarantee.

## Governing principle

> Values are independent data. `identity` is explicit shared mutable identity. `fixed` means nothing reachable through the fixed ordinary value can observably change. Eristavi rejects combinations that would make any of those promises dishonest.
