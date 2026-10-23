# Eristavi pre-0.1 Specification Audit

> **Initial audit date: 2026-10-23**
>
> **Final freeze verification: 2026-10-23**
>
> **Status: Pre-0.1 frontend semantics frozen; implementation may proceed**

This document records the consolidation audit performed before implementation of the Eristavi compiler frontend and the resolution of the freeze items identified by that audit.

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
- `VALUE_EQUALITY.md`
- `COLLECTIONS.md`
- `INTEGER_REMAINDER.md`
- `RESOURCE_CLEANUP.md`
- `PRE_0_1_FREEZE.md`

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

## 3. Resolved pre-0.1 freeze decisions

Every frontend P0 item and every semantic edge case required for the initial pre-0.1 implementation now has an explicit decision.

### Lexical rules — resolved

`LEXICAL_RULES.md` defines comments, Unicode identifiers, the exact 28-keyword set, text escapes, integer and floating-point literal forms, and source whitespace behavior.

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

`FLOAT.md` defines `Float` as deterministic IEEE 754 binary64, including rounding, special values, signed zero, gradual underflow, and cross-target behavior. There is no implicit `Int`/`Float` conversion in either direction.

### Deep `fixed` with contained identity — resolved

`FIXED_IMMUTABILITY.md` defines a transitive deep-fixable rule.

A `fixed` binding or `fixed` field is valid only when its static type contains no `identity` at any reachable stored type position. The rule is recursive through nested ordinary values and applies through optional and collection positions.

Eristavi rejects the combination rather than weakening `fixed` into shallow handle immutability, implicitly freezing other aliases, or silently snapshotting identity state.

### Ordinary value equality — resolved

`VALUE_EQUALITY.md` defines ordinary user-defined value equality as structural, recursive, type-preserving, and compositional.

Two ordinary values of the same compatible static type compare equal when every corresponding stored component compares equal under that component type's own equality semantics.

This preserves existing component rules rather than replacing them: `identity T` fields compare by logical identity, `Float` retains IEEE behavior including NaN, `maybe T` composes contained equality, and ordered collections compare by length and corresponding elements when their element type is equality-comparable.

Pre-0.1 introduces no equality-overloading syntax, `Equatable` protocol, or implicit cross-type coercion.

### Collections — resolved

`COLLECTIONS.md` defines the first concrete pre-0.1 collection family as `List`.

A List is ordered, growable, homogeneous in its statically inferred element relationship, and an ordinary value by default. List literals use `[...]`; indexing is zero-based and requires `Int`; bounds are checked; `.count` is the single element-count property; `.add(value)` is the canonical append operation; and mutable Lists support indexed assignment.

Empty List literals require enough static context to infer one element type. Mixed incompatible elements, unresolved empty Lists, and implicit `Int`/`Float` mixing are compile-time errors rather than dynamic fallback.

List assignment and parameter passing preserve ordinary value semantics. `fixed` Lists are deeply immutable and must satisfy the existing deep-fixable rule. Ordered structural equality uses the already-locked value-equality model.

Pre-0.1 does not expose user-written `List<Text>` generic syntax. `List` is a predeclared type-family name rather than a keyword, while the element relation remains compiler-inferred.

### Integer remainder and Float `%` — resolved

`INTEGER_REMAINDER.md` defines `%` as an `Int`-only operator in pre-0.1.

Signed integer division truncates toward zero, and `%` computes the corresponding signed remainder. A nonzero remainder follows the sign of the dividend. Division or remainder by zero is an integer arithmetic fault, and the signed-minimum / `-1` exceptional pair is treated as overflow rather than inheriting target-specific behavior.

`Float` does not support `%`. Floating-point remainder/modulo, if real programs require it later, belongs to explicitly named numeric library operations with separately defined contracts.

### Resource cleanup and dual failure — resolved

`RESOURCE_CLEANUP.md` defines deterministic cleanup-failure composition without adding new surface syntax.

A cleanup failure prevents an otherwise successful fallthrough or return and becomes the primary checked failure when no failure is already active.

If the body is already propagating a checked failure, that original failure remains primary. Cleanup failures are preserved as secondary cleanup failure context rather than replacing or silently discarding the original cause.

Nested resources clean up in reverse order. If no failure was active, the first cleanup failure encountered becomes primary and later cleanup failures become secondary context. If a body failure was already active, all cleanup failures are secondary to that body failure.

Resource cleanup failure sets are statically known and participate in ordinary checked-failure analysis. Secondary context is runtime/compiler failure metadata rather than a new source-level union, wrapper error, keyword, or exception hierarchy.

## 4. Deliberately postponed — not pre-0.1 blockers

The following areas are intentionally outside the pre-0.1 semantic freeze. Their absence is a design decision, not an unresolved contradiction.

### Identity-to-value snapshot

Pre-0.1 defines no operation for extracting an independent ordinary `T` snapshot from `identity T`.

This capability should be added only if real programs demonstrate a need and its copying/snapshot semantics can be named clearly.

### Advanced resource transfer and borrowing

Pre-0.1 keeps the existing scoped single-owner `with` model.

It does not add ownership transfer, general borrowing, lifetime annotations, manual release, or move syntax. Those features remain postponed until concrete use cases justify the additional vocabulary and complexity.

### Third-party package roots and package management

Project-local source-root modules and the reserved `std` root are sufficient for pre-0.1.

Third-party package root naming, dependency resolution, versioning, registry behavior, lockfiles, and related package-manager policy are postponed beyond the initial compiler.

## 5. Architectural decisions that do not block the frontend

The following remain open until the frontend and typed representation are sufficiently real to inform them:

- exact Eristavi IR instruction set and representation;
- first native CPU backend;
- exact backend implementation order;
- stable portable bytecode/runtime format, if one is eventually needed in addition to native, C, JavaScript, and WebAssembly.

These do not delay lexer/parser/type-checker work.

## 6. Features deliberately postponed

There is no reason to pull the following into pre-0.1 implementation work:

- explicit generic syntax;
- traits/interfaces for generic constraints;
- pattern matching;
- async/await;
- advanced concurrency;
- reflection;
- macros;
- advanced garbage collection;
- package registry infrastructure;
- identity snapshots;
- advanced resource transfer/borrowing;
- multiple native CPU backends;
- self-hosting.

## 7. Final freeze verification

The final cross-document verification confirmed that the current source-language/front-end contract is coherent enough to implement.

In particular:

- the master semantics no longer lists `%`, cleanup dual failure, identity snapshots, resource transfer, or package roots as accidental unresolved blockers;
- `%` is consistently Int-only while Float arithmetic excludes `%`;
- `output(...)` remains an ordinary standard function and the exact keyword count remains 28;
- the `List` collection surface matches the grammar's indexing and assignment-target model;
- deep `fixed`, ordinary value equality, and identity equality compose without contradictory aliasing rules;
- checked cleanup failures compose with the checked-error system without new source syntax;
- entry execution remains selected by file rather than magic `main` syntax;
- parser factoring for `else error` and primary/postfix parsing is implementation-internal and does not reopen source syntax.

`PRE_0_1_FREEZE.md` records the implementation handoff boundary.

## 8. Audit conclusion

The pre-0.1 semantic/frontend specification is frozen for implementation.

The language now has explicit rules for:

- lexical structure;
- symbolic vocabulary;
- precedence and assignment;
- lexical scope and name resolution;
- Bool-only conditions;
- function results and completion;
- entry execution;
- standard textual output;
- deterministic `Float` semantics;
- transitive deep `fixed` eligibility;
- structural ordinary value equality;
- ordered growable `List` collections with inferred element relationships and checked zero-based indexing;
- truncation-toward-zero signed `Int` division and Int-only `%` remainder;
- deterministic resource cleanup and dual checked-failure composition.

Frontend/compiler implementation should now proceed from the frozen subset. New language features should require evidence from implementation or real Eristavi programs rather than speculative expansion before the compiler exists.

The governing design order remains:

> **Philosophy → Semantics → Architecture → Implementation**
