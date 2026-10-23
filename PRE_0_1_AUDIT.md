# Eristavi pre-0.1 Specification Audit

> **Audit date: 2026-10-23**
>
> **Status: Core semantic audit complete; narrow freeze items remain**

This document records the first consolidation audit performed before implementation of the Eristavi compiler frontend.

The audit did not redesign already-locked language behavior. Its purpose was to identify stale documentation, contradictions, and genuinely unresolved areas that matter before the pre-0.1 specification is frozen.

## 1. Files audited

The audit covered:

- `DESIGN_PHILOSOPHY.md`
- `LANGUAGE_SEMANTICS.md`
- `GRAMMAR.md`
- `CONSTRUCTION.md`
- `IDENTITY_EQUALITY.md`
- `VALUE_PARAMETER_MUTATION.md`
- `ERRORS.md`
- `GENERICS.md`
- `TARGETS.md`
- `README.md`
- `compiler/README.md`
- `examples/hello.eri`
- `tests/README.md`

## 2. Documentation drift corrected

The audit found several places where older master documentation had not caught up with later locked decisions.

### Construction

Old master examples still used provisional forms such as:

```text
User(...)
Counter(...)
Customer("Anna")
```

The locked named-field form is now used consistently:

```eri
User {
    id = 1;
    name = "Anna";
}
```

### Resource management

The design charter still contained an early conceptual `using` example.

The locked resource construct is now shown consistently as:

```eri
with file be try files.open("data.txt") {
    ...
}
```

### Value parameter mutation

`LANGUAGE_SEMANTICS.md` still described explicit in-place mutation of ordinary caller-owned values as an open syntax question.

The locked pre-0.1 rule is now reflected in the master semantics:

> Ordinary parameters are values. Functions return changes rather than mutating caller-owned ordinary values.

### Identity equality

The master open-decision list still described identity equality as unresolved.

The locked rule is now reflected:

> `identity T == identity T` means the same logical identity, not equal current field state and not equal memory address.

### Checked errors

`GRAMMAR.md` and the master semantics still described custom error declarations and multiple checked error types as unresolved.

The consolidated grammar now includes:

- `error` declarations;
- `fail` statements;
- comma-separated `fails` contracts;
- typed `else error ErrorType` handlers;
- catch-all `else error`;
- `try` propagation.

### Generic abstraction

Older master text treated the generic abstraction model as still open.

The locked pre-0.1 model is now reflected:

> Generic relationships may be inferred statically by the compiler, but pre-0.1 exposes no user-written generic type-variable or constraint syntax.

### Target strategy

The public README now matches the selected target direction:

- native machine code;
- C;
- JavaScript;
- WebAssembly.

Rust, Go, and PHP are not planned targets.

## 3. Documents found consistent

The following dedicated specifications were internally consistent with the decisions they record and required no semantic correction during this audit:

- `CONSTRUCTION.md`
- `IDENTITY_EQUALITY.md`
- `VALUE_PARAMETER_MUTATION.md`
- `ERRORS.md`
- `GENERICS.md`
- `TARGETS.md`

The bootstrap files are also consistent with the current minimal language direction:

- `compiler/README.md`
- `examples/hello.eri`
- `tests/README.md`

## 4. Genuine remaining freeze items

The remaining work should be separated into frontend blockers, semantic edge cases, and later architectural decisions.

### P0 — resolve before freezing the first frontend grammar/type checker

#### Lexical rules

The lexer still needs a precise definition for:

- line and/or block comments;
- valid identifier characters;
- keyword recognition;
- string literal escape rules;
- exact integer and float literal token forms;
- whitespace handling beyond the already-locked rule that newlines do not terminate statements.

These are not major language-philosophy questions, but the lexer cannot be frozen without them.

#### Expression precedence and associativity

The language has operators, but the complete precedence and associativity table is not yet formalized.

The relationship among assignment, arithmetic, comparison, `not`, `and`, and `or` must be deterministic before the parser is frozen.

#### Scope, declaration, and shadowing rules

The frontend needs explicit answers for:

- lexical block scope;
- whether a local name may shadow an outer name;
- whether redeclaration in the same scope is invalid;
- whether use-before-declaration is allowed;
- duplicate top-level declaration behavior.

These rules directly affect name resolution and diagnostics.

#### Condition typing

The specification should explicitly state whether `if` and `while` conditions must be `Bool` rather than relying on truthiness or implicit conversion.

The current philosophy strongly favors explicit predictable typing, but this should be formally locked rather than assumed by the implementation.

#### Function completion and no-value functions

The type checker needs precise rules for:

- functions with no `returns` clause;
- validity of bare `return;`;
- ensuring all reachable paths return a value when a value-returning function requires one.

#### Top-level execution / entrypoint

The bootstrap example uses executable statements at file scope. Before executable compilation, the project should define the initial entry model, for example whether `main.eri` is the conventional program entry module and how top-level executable statements are treated.

#### Bootstrap `print`

The first compiler examples use `print`, but its initial classification remains open:

- language keyword;
- compiler intrinsic;
- standard-library function.

This does not require a large design subsystem, but the bootstrap compiler needs one concrete choice.

## 5. Semantic edge cases to resolve before full pre-0.1 freeze

### Deep `fixed` values containing identity fields

This is the main semantic edge case discovered by the audit.

Consider:

```eri
type ViewModel {
    counter identity Counter;
}

let fixed model be ViewModel {
    counter = sharedCounter;
};
```

The outer value is `fixed`, whose locked meaning is deep immutability from the programmer's point of view. However, the contained `identity Counter` may also be held elsewhere and mutated through another identity handle.

The current specifications clearly forbid:

```eri
let fixed counter be identity Counter {
    value = 0;
};
```

but they do not yet explicitly define whether a deeply fixed ordinary value may contain a mutable identity field.

This must be resolved without weakening the established deep-`fixed` rule.

### Float semantics

`Float` is in the working fundamental set, but its exact representation, arithmetic behavior, special values, and cross-target guarantees are not frozen.

### Ordinary value equality

Identity equality is defined, but the general `==` rules for arbitrary ordinary user-defined value types are not yet frozen.

### Identity-to-value snapshot

No explicit operation for extracting an independent ordinary `T` snapshot from `identity T` is currently defined. It should be added only if real use cases require it.

### Resource cleanup dual failure

If a checked failure is already propagating and deterministic resource cleanup itself fails, composition/reporting remains unresolved. No recoverable cleanup failure may be silently discarded.

### Advanced resource transfer

Ownership transfer or borrowing beyond the basic `with` scope remains deliberately postponed unless real programs require it.

### Third-party package roots

Module semantics are locked, but third-party package naming and dependency resolution are not yet defined.

## 6. Architectural decisions that do not block the frontend

The following should remain open until the frontend and typed representation are sufficiently real to inform them:

- exact Eristavi IR instruction set and representation;
- first native CPU backend;
- exact backend implementation order;
- stable portable bytecode/runtime format, if one is eventually needed in addition to native, C, JavaScript, and WebAssembly.

These should not delay lexer/parser/type-checker work.

## 7. Features deliberately postponed

The audit found no reason to pull the following into pre-0.1 implementation work:

- explicit generic syntax;
- traits/interfaces for generic constraints;
- pattern matching;
- async/await;
- advanced concurrency;
- reflection;
- macros;
- advanced garbage collection;
- package registry infrastructure;
- multiple native CPU backends;
- self-hosting.

## 8. Audit conclusion

The core language model is coherent enough to move toward implementation.

The audit did **not** uncover a need to reopen the major locked decisions around:

- `let` / `fixed`;
- value semantics;
- explicit identity;
- `maybe` / `none`;
- checked errors;
- named-field construction;
- semicolon termination;
- resource scope;
- inferred generic abstraction;
- module qualification;
- the selected compilation-target strategy.

Before calling the pre-0.1 frontend specification frozen, the project should resolve the P0 items in Section 4, then revisit the deep-`fixed` / identity-field edge case in Section 5.

The recommended next design sequence is:

1. lexical rules;
2. scope and shadowing;
3. complete operator precedence / assignment rules;
4. condition and function-completion typing;
5. bootstrap entrypoint and `print`;
6. deep `fixed` + contained identity semantics;
7. freeze the frontend specification;
8. begin lexer/parser implementation.
