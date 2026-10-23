# Eristavi Checked Errors

> **Status: Locked for pre-0.1**

This document defines custom checked error declarations, failure production, multiple checked error contracts, local handling, and propagation.

## 1. Errors are typed data

Recoverable failures are represented by explicit error types.

```eri
error DatabaseError {
    message Text;
    code Int;
}
```

An error declaration is data-oriented. It does not create an exception class hierarchy and does not imply inheritance.

Every checked error type must declare a `message Text` field. This guarantees that a general checked-error handler can always inspect and report a human-readable message.

Additional fields are ordinary typed fields:

```eri
error FileError {
    message Text;
    path Text;
}

error DecodeError {
    message Text;
    position Int;
}
```

Error fields use the same name-first type form as ordinary type fields.

Conceptual grammar:

```text
error-declaration :=
    [ "public" ] "error" identifier "{" error-field { error-field } "}"

error-field :=
    identifier type-expression ";"
```

For pre-0.1, a checked error declaration must contain exactly one field named `message` whose type is `Text`.

## 2. Error construction

Checked error values use the same named-field brace construction model as ordinary user-defined values:

```eri
DatabaseError {
    message = "Database connection failed";
    code = 503;
}
```

All declared fields are required during direct construction and must be initialized exactly once, following the ordinary pre-0.1 construction rules.

There is no separate exception constructor syntax.

## 3. Producing a checked failure

A recoverable checked failure is produced with `fail`:

```eri
fail DatabaseError {
    message = "Database connection failed";
    code = 503;
};
```

`fail` transfers control out of the current function with the supplied checked error value.

Conceptual grammar:

```text
fail-statement :=
    "fail" expression ";"
```

The expression supplied to `fail` must have an error type that is present in the current function's declared `fails` contract.

Example:

```eri
function loadUser(id Int) returns User fails DatabaseError {
    if not connected {
        fail DatabaseError {
            message = "Database connection failed";
            code = 503;
        };
    }

    ...
}
```

`return` and `fail` therefore have distinct meanings:

```eri
return user;   // successful result
fail error;    // recoverable checked failure
```

Unchecked exceptions are not the ordinary recoverable failure mechanism in Eristavi.

## 4. Multiple checked error types

A function may declare more than one checked failure type with a comma-separated `fails` list:

```eri
function loadUser(id Int)
    returns User
    fails DatabaseError, DecodeError
{
    ...
}
```

Conceptual grammar:

```text
fails-clause :=
    "fails" error-type { "," error-type }
```

A `fails` list is a contract, not a user-visible union type expression. The comma-separated form does not introduce general-purpose union syntax into Eristavi.

Duplicate error types in the same `fails` clause are invalid.

A function that declares no `fails` clause cannot produce or propagate an ordinary checked failure.

## 5. Catch-all local handling

A caller may handle every checked error produced by an expression with the existing catch-all form:

```eri
let user be loadUser(1) else error {
    output(error.message);
    return;
};
```

Inside the block, `error` refers to the checked error value produced by the preceding expression.

Because all checked error types expose `message Text`, `error.message` is always available in a catch-all handler.

A catch-all handler covers every checked error type that may be produced by the handled expression.

## 6. Typed local handling

When different checked error types require different behavior, handlers may narrow by error type:

```eri
let user be loadUser(1)
else error DatabaseError {
    output("Database problem: " + error.message);
    return;
}
else error DecodeError {
    output("Invalid data: " + error.message);
    return;
};
```

The handler uses Eristavi's ordinary name-first type order:

```text
error DatabaseError
```

Within that block, `error` is statically narrowed to `DatabaseError`.

Conceptual grammar:

```text
handled-expression :=
    expression error-handler { error-handler }

error-handler :=
    "else" "error" [ error-type ] block
```

An untyped `else error` is the catch-all form and must be the final handler when combined with typed handlers.

The same error type cannot be handled twice in one handler sequence.

## 7. Exhaustiveness

Local handling must cover every checked error type produced by the handled expression unless an unhandled error is propagated through a separate valid mechanism.

For the pre-0.1 local handler form, a handler sequence attached to an expression is exhaustive when either:

- every possible checked error type has a typed handler; or
- a final catch-all `else error` is present.

Example of an incomplete handler sequence:

```eri
function load() returns Data fails FileError, DecodeError {
    ...
}

function run() {
    let data be load()
    else error FileError {
        output(error.message);
        return;
    };
}
```

This is a compile-time error because `DecodeError` is not handled and `run` does not declare a compatible propagation path for that handled expression.

A final catch-all makes the handler sequence exhaustive:

```eri
let data be load()
else error FileError {
    output("Cannot read file.");
    return;
}
else error {
    output(error.message);
    return;
};
```

The compiler must report missing checked-error cases clearly.

## 8. Propagation with `try`

`try` propagates checked failures to the current function:

```eri
function run() fails FileError, DecodeError {
    let data be try load();
}
```

Conceptual grammar remains:

```text
try-expression :=
    "try" expression
```

Every checked error type that may be propagated by the `try` expression must be representable by the current function's own `fails` contract.

Example:

```eri
function load() returns Data fails FileError, DecodeError {
    ...
}

function run() fails FileError {
    let data be try load();
}
```

This is a compile-time error because `DecodeError` cannot be propagated through `run`'s declared contract.

The compiler checks this statically.

## 9. Combining `maybe` and `fails`

Legitimate absence and operational failure remain separate concepts.

```eri
function findUser(id Int)
    returns maybe User
    fails DatabaseError, DecodeError
{
    ...
}
```

This function can have three semantic outcomes:

- success with `User`;
- success with `none`;
- failure with one of the declared checked error types.

`none` is not an error, and an error is not absence.

## 10. Visibility and modules

Checked error declarations follow ordinary top-level visibility rules.

Private by default:

```eri
error InternalError {
    message Text;
}
```

Public when intentionally part of a module API:

```eri
public error DatabaseError {
    message Text;
    code Int;
}
```

Imported public error types remain qualified through the module namespace under the ordinary module rules.

## 11. Runtime defects remain separate

Arithmetic faults, violated runtime invariants, compiler/runtime defects, and unrecoverable process failures are not ordinary checked errors merely because `error` declarations exist.

The `fails` contract is for recoverable failures that application code is expected to handle or deliberately propagate.

## 12. No exception hierarchy in pre-0.1

The initial language intentionally has no:

- `throw` keyword;
- `catch` keyword;
- exception inheritance;
- base exception class;
- implicit unchecked application exceptions;
- general-purpose union syntax merely to express several errors.

The checked-error vocabulary is deliberately small:

```text
error   declares failure data
fails   declares a function's checked failure contract
fail    produces a checked failure
else error handles a checked failure
try     propagates a checked failure
```

The design rule is:

> Checked failures are explicit typed data, explicit contracts, explicit handling, and explicit propagation.
