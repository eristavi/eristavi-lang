# Eristavi Function Return and Completion Semantics

> **Status: Locked for pre-0.1**

This document defines function result inference, no-value functions, `return;`, `return value;`, successful-path completion, checked-failure termination, and recursive return inference for Eristavi pre-0.1.

The governing principle is:

> Infer a function result when the contract is statically clear; require explicit intent when inference is circular or ambiguous.

## 1. `returns T` is optional when the result can be inferred

An explicit result contract is valid:

```eri
function add(a Int, b Int) returns Int {
    return a + b;
}
```

The same result may be inferred when the body establishes it clearly:

```eri
function add(a Int, b Int) {
    return a + b;
}
```

The second function is statically inferred to produce `Int`.

Omitting `returns T` does not mean dynamic typing and does not automatically mean a no-value function.

## 2. No-value functions

A function with no explicit `returns T` contract and no `return expression;` statements is a no-value function.

```eri
function logMessage(message Text) {
    output(message);
}
```

A no-value function may complete by reaching its closing `}`.

Pre-0.1 introduces no `Void`, `void`, `Unit`, or equivalent programmer-visible result type merely to represent this case.

A no-value call may be used as a statement:

```eri
logMessage("Started");
```

It cannot be used where a value is required:

```eri
let result be logMessage("Started"); // error
```

## 3. Bare `return;`

`return;` is an early exit from a no-value function.

```eri
function process(active Bool) {
    if not active {
        return;
    }

    performWork();
}
```

A bare return is invalid in a value-producing function:

```eri
function calculate() returns Int {
    return; // error
}
```

The same restriction applies when the function's result is inferred from other `return expression;` statements.

## 4. `return expression;`

A `return expression;` produces the function's successful result value.

```eri
function double(value Int) {
    return value * 2;
}
```

The compiler infers the result as `Int`.

If `returns T` is written, each returned expression must be compatible with `T`.

## 5. One coherent completion contract

A function cannot mix value-returning and bare-return completion.

Invalid:

```eri
function calculate(active Bool) {
    if active {
        return 10;
    }

    return; // error
}
```

A function is either value-producing or no-value from the programmer's point of view.

## 6. Every reachable successful path of a value-producing function must produce a value

If a function produces a value, every reachable path that can complete successfully must return a compatible value.

Invalid:

```eri
function calculate(active Bool) {
    if active {
        return 10;
    }

    // error: successful fallthrough without a value
}
```

Valid:

```eri
function calculate(active Bool) {
    if active {
        return 10;
    }

    return 0;
}
```

The same rule applies whether the result type is explicit or inferred.

The compiler performs static control-flow analysis. It need not invent a missing value when a path can reach the end of a value-producing function.

## 7. Multiple returned values must establish one static result type

Valid:

```eri
function choose(first Bool) {
    if first {
        return 10;
    }

    return 20;
}
```

The result type is `Int`.

Invalid:

```eri
function choose(first Bool) {
    if first {
        return 10;
    }

    return "ten"; // error
}
```

Pre-0.1 does not silently create a dynamic or union result type to reconcile incompatible returns.

## 8. `fail` terminates a path

A checked `fail` terminates the current execution path and therefore satisfies path-completion analysis without requiring a `return` on that path.

```eri
function load(id Int)
    returns User
    fails DatabaseError
{
    if id < 0 {
        fail DatabaseError {
            message = "Invalid id";
            code = 400;
        };
    }

    return findUser(id);
}
```

The same principle applies to a function whose result type is inferred.

`fail` does not itself produce the successful result value; it terminates the path through the function's checked-failure contract.

## 9. `none` is not no-value completion

`return;` and `return none;` are fundamentally different.

```eri
return;
```

means that a no-value function completes without producing a value.

```eri
return none;
```

returns the actual absence value of a `maybe T` result.

Example:

```eri
function findUser(id Int) returns maybe User {
    if id < 0 {
        return none;
    }

    return lookupUser(id);
}
```

Eristavi never uses `none` as a substitute for `void` or missing function results.

## 10. Recursive and circular result inference

Pre-0.1 does not require the compiler to solve circular result-type equations.

When a value-producing function's result inference depends directly or indirectly on its own result type, the function must declare `returns T` explicitly.

Direct recursion therefore uses an explicit result contract when the recursive call participates in the returned value:

```eri
function factorial(n Int) returns Int {
    if n <= 1 {
        return 1;
    }

    return n * factorial(n - 1);
}
```

A corresponding function without the explicit result contract is rejected when inference would be circular:

```eri
function factorial(n Int) {
    if n <= 1 {
        return 1;
    }

    return n * factorial(n - 1); // error: circular result inference
}
```

The same rule applies to mutually recursive value-producing functions when their inferred result types depend on one another.

This is not a ban on recursion. It is a requirement to state the result contract where inference ceases to be locally provable.

## 11. Explicit result contracts remain useful

Even where inference could succeed, programmers may write `returns T` to make an API contract visible and compiler-checked.

```eri
public function calculatePrice(order Order) returns Float {
    return computePrice(order);
}
```

Pre-0.1 does not force explicit result annotations on all public functions; that may be a style or lint recommendation rather than a grammar rule.

## 12. Explicit `returns T` with no successful return value

A function with an explicit `returns T` contract may have paths that only terminate through `fail` or another statically non-completing path.

For example, an implementation whose only reachable path fails may still state the intended result contract explicitly:

```eri
function unavailable() returns User fails DatabaseError {
    fail DatabaseError {
        message = "Unavailable";
        code = 503;
    };
}
```

Without an explicit `returns T`, a function containing no `return expression;` is classified as no-value rather than causing the compiler to invent a hidden bottom/never result type.

## 13. Diagnostics

The compiler should diagnose at least:

- bare `return;` inside a value-producing function;
- `return expression;` incompatible with an explicit result type;
- incompatible inferred return-expression types;
- reachable successful fallthrough from a value-producing function;
- use of a no-value call in a value context;
- circular result inference that requires an explicit `returns T` contract.

Diagnostics should identify the conflicting return sites or the uncovered fallthrough path where practical.

## Governing rule

> A function either produces a value or does not. `returns T` states the value contract explicitly; otherwise Eristavi infers it when statically clear. No-value functions may fall through or use `return;`; value-producing functions must return a compatible value on every reachable successful path. `fail` terminates a path, `none` remains optional absence, and circular result inference requires an explicit result contract.
