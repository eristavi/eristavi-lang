# Eristavi Construction and Initialization

> **Status: Locked for pre-0.1**

This document defines the construction and initialization semantics for ordinary user-defined values and explicit identity values.

## 1. One construction form

Eristavi uses one named-field construction form:

```eri
TypeName {
    field = expression;
    field = expression;
}
```

Example:

```eri
type User {
    fixed id Int;
    name Text;
}

let user be User {
    id = 1;
    name = "Anna";
};
```

Construction is field-named rather than positional. Field order in the type declaration therefore does not become part of the call-site contract.

The following positional form is not part of the initial language:

```text
User(1, "Anna")
```

Colon-based named initialization is also not part of the construction syntax:

```text
User(id: 1, name: "Anna")
```

The design rule is:

> Values are constructed by naming the fields being initialized.

## 2. Required initialization

For pre-0.1, every declared field is required during direct construction and must be initialized exactly once.

```eri
type User {
    fixed id Int;
    name Text;
}

let user be User {
    id = 1;
    name = "Anna";
};
```

Omitting a required field is a compile-time error:

```eri
let user be User {
    id = 1;
};
```

Initializing the same field more than once is a compile-time error:

```eri
let user be User {
    id = 1;
    id = 2;
    name = "Anna";
};
```

Supplying a field that does not exist on the type is a compile-time error.

Default field values and optional omission rules are deliberately not part of this decision and may be considered separately later.

## 3. Fixed fields

A `fixed` field is initialized through the same construction syntax as every other field:

```eri
type User {
    fixed id Int;
    name Text;
}

let user be User {
    id = 1;
    name = "Anna";
};
```

After construction, a `fixed` field cannot be reassigned:

```eri
user.name = "Maria";  // valid
user.id = 2;           // compile-time error
```

This preserves the existing rule that `fixed` means initialized once, then immutable.

## 4. Identity construction

Identity uses the same value construction form and adds the already-locked explicit `identity` prefix:

```eri
type Counter {
    value Int;
}

let counter be identity Counter {
    value = 0;
};
```

The brace expression first describes a valid `Counter` value. `identity` then creates managed shared identity from that value.

There is no separate constructor syntax for identity values.

## 5. Construction through ordinary functions

Eristavi does not need constructor overloading or special constructor methods in pre-0.1.

When initialization requires validation, calculation, checked errors, or other behavior, an ordinary function can return the constructed value:

```eri
function createUser(id Int, name Text) returns User {
    return User {
        id = id;
        name = name;
    };
}
```

This keeps construction syntax data-oriented while ordinary functions handle behavior.

## 6. Grammar

Conceptual grammar:

```text
construction-expression :=
    type-name "{" field-initializer { field-initializer } "}"

field-initializer :=
    identifier "=" expression ";"
```

An identity construction uses the existing identity expression rule:

```text
identity-expression := "identity" expression
```

where the expression may be a construction expression:

```eri
identity Counter {
    value = 0;
}
```

## 7. Initial restrictions

The initial language intentionally has no:

- positional field construction;
- overloaded constructors;
- implicit constructors;
- colon-based field initialization;
- constructor-specific methods or keywords;
- automatic field omission;
- default-field-value semantics.

These should only be added later if real programs demonstrate a clear need.

## 8. Rationale

This design follows Eristavi's core principles:

- one obvious construction form;
- readable field names at the use site;
- no dependency on declaration order;
- simple deterministic parsing;
- straightforward compile-time validation;
- no special constructor subsystem when ordinary functions already express behavior.

The design rule is:

> Construction states the data explicitly; functions provide behavior when construction needs logic.
