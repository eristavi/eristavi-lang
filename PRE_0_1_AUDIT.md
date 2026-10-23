# Eristavi pre-0.1 Specification Audit

> **Initial audit date: 2026-10-23**
>
> **Status: Original frontend P0 decisions resolved; semantic freeze edge cases remain**

This document records the consolidation audit performed before implementation of the Eristavi compiler frontend and tracks the resolution of the freeze items identified by that audit.

The audit did not redesign already-locked language behavior. Its purpose was to identify stale documentation, contradictions, and genuinely unresolved areas that matter before the pre-0.1 specification is frozen.

## 1. Files audited

The original audit covered:

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

Dedicated specifications added or finalized during follow-up resolution include:

- `LEXICAL_RULES.md`
- `PRECEDENCE.md`
- `SCOPE.md`
- `CONDITIONS.md`
- `FUNCTION_RETURNS.md`
- `ENTRYPOINT.md`
- `OUTPUT.md`
- `FLOAT.md`
- `FIXED_IMMUTABILITY.md`

## 2. Documentation drift corrected by the audit

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

The locked pre-0.1 rule is:

> Ordinary parameters are values. Functions return changes rather than mutating caller-owned ordinary values.

### Identity equality

The locked rule is:

> `identity T == identity T` means the same logical identity, not equal current field state and not equal memory address.

### Checked errors

The consolidated grammar includes:

- `error` declarations;
- `fail` statements;
- comma-separated `fails` contracts;
- typed `else error ErrorType` handlers;
- catch-all `else error`;
- `try` propagation.

### Generic abstraction

The locked pre-0.1 model is:

> Generic relationships may be inferred statically by the compiler, but pre-0.1 exposes no user-written generic type-variable or constraint syntax.

### Target strategy

The selected target direction is:

- native machine code;
- C;
- JavaScript;
- WebAssembly.

Rust, Go, and PHP are not planned targets.

## 3. Frontend P0 resolution status

Every P0 item identified by the initial audit has now received an explicit pre-0.1 decision.

### Lexical rules — resolved

`LEXICAL_RULES.md` now defines comments, Unicode identifiers, the exact 28-keyword set, text escapes, integer and floating-point literal forms, and source whitespace behavior.

### Expression precedence and associativity — resolved

`PRECEDENCE.md`, `OPERATORS.md`, and `GRAMMAR.md` define the complete precedence model. Comparisons are non-associative, Boolean ordering is explicit, and assignment is statement-level rather than an expression.

### Scope, declaration, and shadowing — resolved

`SCOPE.md` defines lexical block scope, declaration-before-use, no self-reference during local initialization, no same-scope redeclaration, no local shadowing, unique parameters, and order-independent unique module declarations.

### Condition typing — resolved

`CONDITIONS.md` requires static `Bool` conditions for `if` and `while`. Pre-0.1 has no implicit truthiness.

### Function completion and no-value functions — resolved

`FUNCTION_RETURNS.md` defines inferred versus explicit result contracts, no-value functions, bare `return;`, required successful-path returns, checked-failure termination, and the explicit-return-type requirement for circular result inference.

### Top-level execution and entrypoint — resolved

`ENTRYPOINT.md` defines an explicitly selected entry source file, top-level execution in that entry file, declaration-only imported modules, and no magic `main` function or filename.

### Standard textual output — resolved

The early provisional `print` spelling has been replaced by the locked standard function:

```eri
output("Hello");
```

`OUTPUT.md` defines `output(value)` as an ordinary predeclared standard-library/prelude function. It is not a keyword or special statement, requires no explicit import, and uses ordinary call syntax.

Pre-0.1 defines no built-in `print`, `echo`, `say`, or `out` alias.

### Float semantics — resolved

`FLOAT.md` now defines `Float` as deterministic IEEE 754 binary64, including rounding, special values, signed zero, gradual underflow, and cross-target behavior. There is no implicit `Int`/`Float` conversion in either direction.

### Deep `fixed` with contained identity — resolved

`FIXED_IMMUTABILITY.md` now defines a transitive deep-fixable rule.

A `fixed` binding or `fixed` field is valid only when its static type contains no `identity` at any reachable stored type position. The rule is recursive through nested ordinary values and applies through optional and collection positions.

Eristavi rejects the combination rather than weakening `fixed` into shallow handle immutability, implicitly freezing other aliases, or silently snapshotting identity state.

Deep-fixable is a compiler property rather than new source syntax.

## 4. Semantic edge cases still to resolve before full pre-0.1 freeze

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

### Collection details

The general collection direction and inferred homogeneous element relationships are established, but the exact first concrete collection model, including Array/List naming and formally locked indexing details, still needs a deliberate decision before that API is considered frozen.

### Float remainder

The `%` token is part of the locked arithmetic vocabulary, but whether `%` applies only to `Int` in pre-0.1 or also receives explicitly defined `Float` remainder semantics remains to be settled.

## 5. Architectural decisions that do not block the frontend

The following should remain open until the frontend and typed representation are sufficiently real to inform them:

- exact Eristavi IR instruction set and representation;
- first native CPU backend;
- exact backend implementation order;
- stable portable bytecode/runtime format, if one is eventually needed in addition to native, C, JavaScript, and WebAssembly.

These should not delay lexer/parser/type-checker work.

## 6. Features deliberately postponed

There is still no reason to pull the following into pre-0.1 implementation work:

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

## 7. Current audit conclusion

The original frontend P0 questions and the major deep-immutability/identity edge case are now resolved. The language has explicit rules for:

- lexical structure;
- symbolic vocabulary;
- precedence and assignment;
- lexical scope and name resolution;
- Bool-only conditions;
- function results and completion;
- entry execution;
- standard textual output;
- deterministic `Float` semantics;
- transitive deep `fixed` eligibility.

The next recommended semantic sequence is:

1. define ordinary value equality;
2. settle the first concrete collection details and `%` applicability;
3. review identity snapshot only if a real use case requires it;
4. review the remaining resource/package edge cases that actually block pre-0.1;
5. perform a final cross-document frontend freeze audit;
6. begin lexer/parser/type-checker implementation from the locked subset.

The audit continues to support the governing design order:

> **Philosophy → Semantics → Architecture → Implementation**
