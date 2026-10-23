# Eristavi Compiler

This directory contains the Python bootstrap implementation of the `erist` compiler/toolchain.

The pre-0.1 frontend semantics are frozen in `PRE_0_1_FREEZE.md`; compiler work should implement those rules incrementally rather than inventing alternate syntax during bootstrap development.

## Bootstrap language

The first compiler prototype is written in Python so the language grammar, semantics, diagnostics, and IR can evolve quickly while remaining easy to inspect and test.

The intended long-term goal remains self-hosting: once Eristavi is capable enough, a later compiler may be implemented in Eristavi itself.

## Current frontend pipeline

```text
.eri source
    ↓
lexer
    ↓
parser
    ↓
AST
    ↓
semantic analysis / type inference
    ↓
bootstrap execution backend
```

The execution backend is intentionally temporary. It gives the project a complete working vertical slice before the Eristavi IR and native/backend layers are implemented.

## Implemented bootstrap subset

The bootstrap currently supports:

- the complete 28-keyword lexer vocabulary;
- SPACE/TAB/LF/CR source whitespace rules;
- line comments and nested block comments;
- Unicode/NFC identifier handling;
- decimal, binary, and hexadecimal Int literals;
- decimal Float literals;
- Text literals with the locked escape set;
- `let` and `let fixed` bindings with inferred basic types;
- explicit basic annotations such as `let count Int be 3;`;
- `Int`, `Float`, `Bool`, and `Text` annotation checking with no implicit conversion;
- mutable reassignment to visible non-fixed bindings;
- lexical block scopes created by control-flow blocks;
- declaration-before-use and no local shadowing across visible scopes;
- branch-local bindings that do not leak after their block;
- `if` / `else` with statically required `Bool` conditions;
- `while` with statically required `Bool` conditions;
- mutation of visible outer bindings from nested blocks;
- module-level function declarations before entry execution;
- order-independent function resolution across the module declaration region;
- typed function parameters for the currently implemented basic types;
- mutable local parameter values that do not mutate caller-owned bindings;
- ordinary named function calls with static arity and argument-type checking;
- explicit `returns T` contracts for the implemented basic types;
- inferred result types when return expressions establish one non-circular type;
- no-value functions with normal fallthrough and bare `return;`;
- rejection of no-value calls in value contexts;
- return-path completion checking for value-producing functions;
- rejection of mixed bare/value return completion;
- direct and mutual circular result-inference detection;
- recursive value-producing functions when an explicit result contract breaks the inference cycle;
- recursive no-value functions without a result contract;
- `Int`, `Float`, `Bool`, and `Text` literals;
- unary `-` and `not`;
- arithmetic, comparison, `and`, and `or` precedence;
- non-associative comparisons;
- no implicit `Int` / `Float` mixing;
- signed 64-bit checked Int arithmetic;
- truncation-toward-zero Int division and Int-only `%`;
- IEEE-style Float division-by-zero special values;
- the predeclared `output(value)` call for the initial scalar types;
- source-location diagnostics;
- `run` and `check` CLI commands.

The parser and analyzer deliberately reject frozen features that are not implemented yet rather than guessing provisional behavior.

One deliberate bootstrap limitation remains in this function slice: parameters currently require explicit basic types. The frozen language permits omitted parameter types when compiler-inferred generic relationships are statically provable, but that generic inference machinery is not implemented yet.

## Running the bootstrap

From the repository root:

```text
python -m compiler.erist run examples/hello.eri
```

Expected output:

```text
42
```

Frontend-only checking:

```text
python -m compiler.erist check examples/hello.eri
```

The repository also defines an installable command through `pyproject.toml`:

```text
erist run examples/hello.eri
```

once the package is installed in the active Python environment.

## Tests

Run the current bootstrap tests from the repository root:

```text
python -m unittest discover -s tests -v
```

The current suite contains 37 tests. In addition to the arithmetic, annotation, scope, and control-flow coverage, it now exercises explicit and inferred function results, no-value functions, bare returns, full successful-path return checking, forward function resolution, argument checking, mutable local parameters, explicit recursive functions, recursive no-value functions, and rejection of circular inferred result contracts.

## Next implementation slices

The compiler should continue vertically through already-frozen behavior. The next sensible order is:

1. `List` literals, indexing, `.count`, `.add`, and indexed assignment;
2. user-defined value types and named-field construction;
3. `maybe` / `none` flow narrowing;
4. checked errors;
5. identity;
6. `with` resources and cleanup semantics;
7. modules/imports;
8. compiler-inferred generic parameter relationships beyond the current typed-parameter bootstrap;
9. typed Eristavi IR and the first real compilation backend.

Implementation should follow the root specifications rather than inventing semantics for convenience.
