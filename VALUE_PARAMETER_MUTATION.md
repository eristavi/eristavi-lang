# Eristavi Value Parameter Mutation

> **Status: Locked for pre-0.1**

This document defines how ordinary value parameters behave with respect to caller-owned state.

## 1. Ordinary parameters use value semantics

An ordinary parameter of type `T` receives an independent logical value.

```eri
type User {
    name Text;
}

function rename(user User, name Text) returns User {
    user.name = name;
    return user;
}
```

Mutating `user` inside the function does not directly mutate the caller's value.

The caller receives changes only through an explicit returned value:

```eri
let user be User {
    name = "Anna";
};

user = rename(user, "Maria");
```

The semantic rule is:

> Ordinary parameters are values. Functions return changes rather than mutating caller-owned values.

## 2. No pre-0.1 in-place value parameter feature

Pre-0.1 does not define a special mechanism such as:

```text
ref user
mut user
inout user
change user
&user
```

for mutating an ordinary caller-owned value in place.

Such a feature may be reconsidered only if real Eristavi programs demonstrate a clear need that cannot be served cleanly by value returns or explicit identity semantics.

## 3. Identity remains the explicit shared-mutation mechanism

Shared observable mutation is represented by the already-locked `identity T` model:

```eri
function rename(user identity User, name Text) {
    user.name = name;
}
```

An `identity User` parameter refers to shared logical identity, so mutation through that parameter is observable through other handles to the same identity.

This is intentionally different from an ordinary `User` parameter.

## 4. Compiler optimization is allowed

The value-semantic rule does not require the compiler to physically copy every argument.

The compiler may use copy elision, destructive update, reuse of storage, escape analysis, reference counting internally, copy-on-write, or other optimizations when it can prove that observable value semantics remain unchanged.

For example:

```eri
user = rename(user, "Maria");
```

may be optimized to reuse the existing storage when no other observable value requires the previous state.

The optimization must remain invisible to the program.

## 5. Rationale

This rule keeps the language model simple:

- ordinary values stay independent;
- function calls do not hide aliasing;
- caller-visible mutation remains explicit through returned values;
- shared mutable state remains explicit through `identity T`;
- the compiler retains freedom to optimize away unnecessary physical copies.

The design rule is:

> Value semantics define behavior; implementation strategy remains the compiler's responsibility.
