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

The first slice currently supports enough frozen semantics to execute `examples/hello.eri`:

- the complete 28-keyword lexer vocabulary;
- SPACE/TAB/LF/CR source whitespace rules;
- line comments and nested block comments;
- Unicode/NFC identifier handling;
- decimal, binary, and hexadecimal Int literals;
- decimal Float literals;
- Text literals with the locked escape set;
- `let` and `let fixed` bindings with inferred basic types;
- simple mutable reassignment;
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

The initial suite covers the hello program, `fixed` reassignment rejection, Int/Float type separation, Float `%` rejection, signed Int remainder, nested block comments, and Boolean precedence.

## Next implementation slices

The compiler should continue vertically through already-frozen behavior. A sensible near-term order is:

1. explicit basic type annotations;
2. blocks and lexical scopes;
3. `if` / `else` and `while`;
4. functions and return analysis;
5. `List` literals, indexing, `.count`, `.add`, and indexed assignment;
6. user-defined value types and named-field construction;
7. `maybe` / `none` flow narrowing;
8. checked errors;
9. identity;
10. `with` resources and cleanup semantics;
11. modules/imports;
12. typed Eristavi IR and the first real compilation backend.

Implementation should follow the root specifications rather than inventing semantics for convenience.
