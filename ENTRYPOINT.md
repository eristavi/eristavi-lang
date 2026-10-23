# Eristavi Entrypoint and Top-Level Execution

> **Status: Locked for pre-0.1**

This document defines how an Eristavi program begins execution, which files may contain top-level executable statements, and how entry execution is separated from reusable module declarations.

The governing principle is:

> The toolchain selects the entry file explicitly; the language does not require a magic `main` function, a magic filename, or hidden module initialization.

## 1. The entry file is selected externally

An executable Eristavi program has exactly one **entry source file** for a given run/build operation.

The toolchain is given that source file explicitly. Conceptually:

```text
erist run app.eri
erist build app.eri
```

The exact command-line surface may evolve, but the semantic rule is fixed: the selected source file is the program's entry module.

There is no required `main` function and no required `main.eri` filename.

`main` is an ordinary identifier and is not reserved by the language.

A project may therefore expose different executables by selecting different entry source files in different toolchain invocations.

## 2. Top-level executable statements belong only to the selected entry file

The selected entry file may contain executable statements at file scope.

Example:

```eri
let x be 40;
let y be 2;

output(x + y);
```

These statements form the program's implicit entry execution body and run in source order.

The programmer does not write a wrapper function merely to start a program.

## 3. Imported modules are declaration-only

A module that is imported by another module must not contain top-level executable statements.

An importable module may contain imports and module declarations such as functions, types, and errors:

```eri
import models.user;

public function add(a Int, b Int) returns Int {
    return a + b;
}
```

It may not contain executable file-scope statements such as:

```eri
let value be load();   // invalid in an imported module
output(value);         // invalid in an imported module
```

This rule applies transitively throughout the imported module graph.

Importing a module therefore does not execute arbitrary initialization code or create hidden runtime side effects.

A file containing top-level executable statements may be selected as an entry file, but it cannot simultaneously be used as an imported reusable module in that program.

## 4. Entry-file ordering

The pre-0.1 entry file has three conceptual regions in this order:

```text
imports
module declarations
entry executable statements
```

Imports come first.

Module declarations such as functions, types, and errors come before the entry executable body.

Once the first top-level executable statement appears, a later module declaration is a compile-time error.

Example:

```eri
import services.math;

function double(value Int) returns Int {
    return value * 2;
}

let answer be double(21);
output(answer);
```

This ordering keeps the module graph, reusable declarations, and runtime execution visually distinct.

## 5. Module declarations remain order-independent within their region

The existing module-resolution rule remains in force: module declarations are collected and resolved across the declaration region rather than becoming execution-order dependent.

For example, one function may refer to another function declared later in the declaration region.

Entry executable statements, by contrast, execute in source order and their local bindings follow ordinary declaration-before-use rules.

## 6. Entry bindings are execution-local, not module members

A top-level executable binding in the entry file belongs to the implicit entry execution body:

```eri
let price be 50;
output(price);
```

Such a binding is not a public module declaration, cannot be imported by another module, and is not implicitly visible inside module-level function/type/error declarations.

Conceptually, module declarations exist outside the implicit entry execution body, while executable statements execute inside it.

Therefore this is invalid:

```eri
let price be 50;

function showPrice() {
    output(price);  // error: entry-local binding is not a module declaration
}
```

Pass required values explicitly instead:

```eri
function showPrice(price Int) {
    output(price);
}

let price be 50;
showPrice(price);
```

This avoids introducing hidden global mutable state merely because Eristavi permits concise top-level execution.

## 7. Entry execution uses ordinary statement semantics

Within the entry execution body, ordinary statement rules continue to apply.

The entry body may use constructs such as:

```text
let / fixed bindings
assignment
expression statements
if / else
for / in
while
with
```

Entry-local scopes, redeclaration rules, no-shadowing rules, Bool-only conditions, checked-error handling, and resource cleanup behave exactly as they do inside an ordinary function body unless this document says otherwise.

## 8. No top-level `return`

`return` belongs to function completion and is not valid at file scope.

This is invalid:

```eri
return;
```

and so is:

```eri
return 1;
```

Normal completion of the entry execution body means normal completion of the program.

Pre-0.1 does not introduce a special entry-return syntax merely to communicate a process exit code.

## 9. Checked failures may not escape the entry boundary

The implicit entry execution body has no `fails` contract.

Therefore a checked failure must be handled before it reaches the entry boundary.

A `try` expression cannot propagate a checked failure out of top-level entry execution.

Use an exhaustive `else error` handler at the boundary when needed:

```eri
let user be loadUser(1)
else error DatabaseError {
    output(error.message);
};
```

A top-level `fail` statement is invalid because there is no surrounding function `fails` contract to satisfy.

Runtime defects remain separate from checked failures and follow their own runtime behavior.

## 10. Normal program completion

When the final reachable entry statement completes, the Eristavi program completes successfully from the language's point of view.

How a target maps normal completion to a host-specific process status is a backend/runtime concern and must not redefine source-language semantics.

A future standard-library API may expose explicit host/process termination where appropriate without adding entrypoint syntax to the core language.

## 11. No hidden module initialization

Pre-0.1 does not define:

- import-time executable code;
- static initializer blocks;
- module constructors;
- a reserved `main` symbol;
- a required `main.eri` filename;
- automatic discovery of an entry function by name.

All runtime execution begins from the explicitly selected entry source file.

## 12. Library/module checking does not require an entry file

The compiler may parse, type-check, or compile reusable declaration-only modules without selecting a program entry file.

An entry source file is required only when the toolchain operation needs an executable program start.

This distinction lets the same language support reusable modules and executable programs without introducing a second source-file syntax.

## Governing rule

> An Eristavi executable starts from one explicitly selected source file. That file may contain a declaration region followed by an implicit top-level execution body. Imported modules remain declaration-only, imports never execute hidden initialization, and no magic `main` name or filename is part of the language.
