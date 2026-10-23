# Eristavi pre-0.1 Frontend Freeze

> **Freeze date: 2026-10-23**
>
> **Status: Frozen for frontend implementation**

The Eristavi pre-0.1 source-language surface and the semantic rules required by the initial lexer, parser, name resolver, type checker, and executable bootstrap are frozen.

This freeze does **not** mean that Eristavi is feature-complete. It means the compiler may now be implemented against a stable pre-0.1 contract without continuing to redesign fundamental syntax or semantics during frontend construction.

## 1. Freeze rule

Implementation must follow the locked specifications.

If implementation reveals a genuine contradiction or makes a locked rule impossible to implement correctly, the specification may be amended deliberately. Implementation convenience alone is not a reason to invent alternate syntax or silently change semantics.

The governing development rule is:

> Implement the language that is specified; do not redesign the language accidentally inside the compiler.

## 2. Frozen source-language areas

The pre-0.1 freeze includes:

- `.eri` source files and the explicitly selected entry-file model;
- the exact 28-keyword lexical set;
- Unicode identifier rules and text-literal escapes;
- decimal/binary/hex integer literals and decimal Float literals;
- semicolon statement termination and brace-delimited structural blocks;
- `let` and transitive `fixed` semantics;
- name-first explicit type annotations without colons;
- `Int`, deterministic IEEE 754 binary64 `Float`, `Bool`, and Unicode `Text` semantics;
- `Int`-only `%` with truncation-toward-zero signed division/remainder semantics;
- ordinary value semantics and explicit `identity T` shared identity;
- `maybe T` / `none` optional values;
- structural ordinary value equality and logical identity equality;
- named-field user-defined value construction;
- compiler-inferred generic relationships without user-written generic type variables;
- the ordered growable `List` collection family with inferred element relationships;
- zero-based checked List indexing, `.count`, `.add(value)`, and indexed assignment;
- `if`, `else`, `for`, `in`, `while`, and function return/completion behavior;
- Bool-only condition typing with no general truthiness;
- lexical scope, declaration-before-use, redeclaration, and no-shadowing rules;
- typed checked errors through `error`, `fails`, `fail`, `else error`, and `try`;
- deterministic `with` resource ownership and cleanup;
- cleanup dual-failure composition with one stable primary checked failure and secondary cleanup context;
- declaration-only imported modules and private-by-default visibility;
- the canonical standard textual-output function `output(value)`;
- the existing operator vocabulary, precedence, associativity, and statement-level assignment model.

## 3. Parser factoring is implementation-internal

`GRAMMAR.md` contains conceptual grammar productions whose source-language behavior is frozen.

The parser implementation may refactor productions internally to remove recursion or ambiguity, including:

- factoring `else error` handling;
- choosing the exact internal `primary` / postfix parser structure;
- choosing recursive-descent helper boundaries.

These are implementation choices, not open source-language design questions.

No internal parser factoring may change accepted source syntax, precedence, associativity, or semantic meaning.

## 4. Deliberately postponed beyond pre-0.1

The following are intentionally **not** required to implement the frozen frontend:

- explicit identity-to-value snapshot APIs;
- advanced resource ownership transfer or borrowing;
- lifetime syntax or manual general-purpose memory management;
- third-party package root naming and dependency resolution;
- package registry, versioning, and lockfile policy;
- explicit generic syntax or generic constraints;
- traits/interfaces for generic constraints;
- pattern matching;
- async/await and advanced concurrency;
- reflection and macros;
- advanced garbage collectors;
- multiple native CPU backends;
- self-hosting;
- stable portable bytecode/runtime format.

Their absence must not be treated by the compiler as permission to invent provisional syntax.

## 5. Architecture that remains implementation work

The semantic frontend freeze does not prematurely lock implementation details that should be informed by real compiler work.

Still open at the architecture/implementation level are:

- the exact Eristavi IR instruction set and data representation;
- the first native CPU backend;
- backend implementation order;
- low-level runtime representation choices that preserve observable semantics;
- optimization strategy;
- eventual portable bytecode details, if justified later.

The long-term target direction remains native machine code plus C, JavaScript, and WebAssembly backends.

## 6. Cross-document consistency result

The final freeze verification found the major specification documents aligned on the current pre-0.1 model:

- `LANGUAGE_SEMANTICS.md` is the consolidated semantic authority;
- `GRAMMAR.md` matches the locked surface and may be factored internally by the parser;
- `LEXICAL_RULES.md`, `PRECEDENCE.md`, `OPERATORS.md`, and `PUNCTUATION.md` agree on lexical/operator vocabulary;
- `FLOAT.md` and `INTEGER_REMAINDER.md` separate Float arithmetic from Int-only `%`;
- `FIXED_IMMUTABILITY.md`, `IDENTITY_EQUALITY.md`, and `VALUE_EQUALITY.md` compose without weakening their respective guarantees;
- `COLLECTIONS.md` matches List syntax, value semantics, equality, deep-fixed behavior, and assignment paths;
- `ERRORS.md` and `RESOURCE_CLEANUP.md` preserve checked-failure typing while defining deterministic cleanup composition;
- `ENTRYPOINT.md` and the grammar agree that executable start is selected by file rather than magic `main` syntax;
- `OUTPUT.md` keeps `output` in the ordinary function-call model rather than adding a keyword or statement form.

Older provisional spellings mentioned in historical/audit explanations are not alternate language forms.

## 7. Bootstrap implementation target

The compiler should now begin from the smallest executable vertical slice:

```eri
let x be 40;
let y be 2;

output(x + y);
```

The implementation sequence should grow from working source to execution rather than implementing disconnected subsystems indefinitely:

```text
source
  ↓
lexer
  ↓
parser
  ↓
AST
  ↓
name/type analysis
  ↓
typed representation
  ↓
initial execution/backend path
```

The first milestone is successful execution of `examples/hello.eri` under the frozen lexical, binding, integer-arithmetic, entrypoint, and `output(...)` rules.

## Governing principle

> The pre-0.1 language surface is stable enough to build. New features now require evidence from implementation or real Eristavi programs, not speculative expansion before the compiler exists.
