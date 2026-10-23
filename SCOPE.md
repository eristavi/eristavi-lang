# Eristavi Scope and Declaration Rules

> **Status: Locked for pre-0.1**

This document defines lexical scope, declaration visibility, redeclaration, shadowing, parameter names, and module-level declaration resolution for Eristavi pre-0.1.

The governing goal is simple name resolution with no hidden rebinding behavior.

## 1. Lexical block scope

Every `{ ... }` block creates a lexical scope.

Names declared in an outer scope are visible in an inner scope unless another language rule makes them unavailable.

```eri
let price be 50;

if ready {
    let tax be 10;
    output(price);
    output(tax);
}

output(price);
```

A name declared inside the block does not escape that block:

```eri
if ready {
    let tax be 10;
}

output(tax);  // error: tax is out of scope
```

The same rule applies to blocks introduced by functions, conditionals, loops, resources, error handlers, and other block-bearing constructs.

## 2. Local declarations are visible only after declaration

A local binding becomes visible only after its declaration has completed.

Valid:

```eri
let price be 50;
let total be price + 10;
```

Invalid:

```eri
let total be price + 10;  // error: price is not declared yet
let price be 50;
```

Eristavi does not hoist local bindings.

## 3. No self-reference during initialization

The name being declared is not visible inside its own initializer.

Invalid:

```eri
let count be count + 1;
```

This prevents partially initialized or recursively self-referential local bindings from arising implicitly.

Recursive behavior, if introduced for functions or other declarations, is governed by the rules for those declaration categories rather than by local-variable self-reference.

## 4. Same-scope redeclaration is invalid

A scope may not contain two local declarations with the same name.

Invalid:

```eri
let price be 50;
let price be 60;
```

To change a mutable binding, assign to it:

```eri
let price be 50;
price = 60;
```

Declaration and assignment remain distinct operations.

## 5. Local shadowing is not allowed

Pre-0.1 does not allow an inner local declaration to reuse a local name that is already visible from an enclosing local scope.

Invalid:

```eri
let price be 50;

if special {
    let price be 20;  // error: shadows outer price
}
```

Use a distinct name instead:

```eri
let price be 50;

if special {
    let specialPrice be 20;
}
```

This rule is intentional. Reading a name should not require the programmer to determine whether a nearer declaration silently replaced the meaning of an already-visible local name.

## 6. Function parameters belong to the function's local name space

A function parameter is considered declared in the function's local scope before execution of its body.

Valid:

```eri
function calculate(price Float) returns Float {
    let tax be price * 0.19;
    return price + tax;
}
```

A local declaration may not redeclare or shadow a parameter:

```eri
function calculate(price Float) returns Float {
    let price be 100.0;  // error
}
```

Nor may a nested block shadow it:

```eri
function calculate(price Float) returns Float {
    if price > 100.0 {
        let price be 50.0;  // error
    }

    return price;
}
```

Parameter names within one function declaration must also be unique.

## 7. Separate functions have independent local scopes

Different functions may freely reuse ordinary local and parameter names because those declarations do not occupy the same lexical scope.

```eri
function first(value Int) returns Int {
    let result be value + 1;
    return result;
}

function second(value Int) returns Int {
    let result be value * 2;
    return result;
}
```

This is valid.

## 8. Loop variables are scoped to the loop body

A `for` binding belongs to the loop body's lexical scope and follows the same no-shadowing rules as parameters and local declarations.

```eri
for user in users {
    let name be user.name;
    output(name);
}

output(user);  // error
output(name);  // error
```

A loop variable may not reuse an already-visible local or parameter name.

## 9. Resource bindings and handler bindings follow the same model

Names introduced by constructs such as `with` and checked-error handling are lexical bindings in their corresponding blocks.

They exist only within the scope defined by that construct and may not shadow an already-visible local or parameter name.

This keeps one consistent local-name model across the language.

## 10. Module-level declarations are unique

A module may not contain two top-level declarations with the same declared name when both would occupy the ordinary module declaration namespace.

For example, duplicate functions are invalid:

```eri
function load() {
    ...
}

function load() {  // error
    ...
}
```

Duplicate types are likewise invalid:

```eri
type User {
    name Text;
}

type User {  // error
    id Int;
}
```

Pre-0.1 does not use duplicate top-level function names as an overloading mechanism.

A duplicate declaration produces a compile-time error that should identify both the new declaration and the earlier conflicting declaration.

## 11. Module-level declarations are order-independent

Unlike local bindings, top-level declarations are resolved across the complete module rather than only from earlier source positions.

This is valid:

```eri
function main() {
    greet();
}

function greet() {
    output("Hello");
}
```

A function may also refer to a type declared later in the same module:

```eri
function createUser() returns User {
    ...
}

type User {
    name Text;
}
```

The compiler therefore collects module declarations before resolving references among those declarations.

This order independence applies to declaration resolution; it does not make local executable bindings order-independent.

## 12. Imports and module aliases

Imported module names and explicit import aliases participate in module name resolution and must not create an ambiguous duplicate name in the importing module.

For example, two imports that would expose the same module qualifier without distinct aliases must be diagnosed rather than silently choosing one.

Exact third-party package-root naming remains a separate unresolved package-system question.

## 13. Diagnostics

Scope diagnostics should explain the actual naming conflict or visibility problem rather than reporting only an undefined identifier.

Useful diagnostic categories include:

- use before declaration;
- name not visible outside its block;
- same-scope redeclaration;
- forbidden shadowing of an outer local;
- forbidden shadowing of a parameter;
- duplicate parameter;
- duplicate top-level declaration;
- duplicate or ambiguous imported qualifier.

Where practical, diagnostics should point to both the invalid occurrence and the earlier declaration that caused the conflict.

## Governing rule

> Eristavi uses lexical block scope with declaration-before-use for locals, forbids local redeclaration and shadowing, treats parameters and other block bindings consistently, and resolves unique module-level declarations across the whole module independent of source order.
