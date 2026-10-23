# Eristavi Compiler

This directory contains the Python bootstrap implementation of the `erist` toolchain.

The source-language contract is frozen in `PRE_0_1_FREEZE.md`. The bootstrap implements that contract vertically so each supported feature can be parsed, type-checked, executed, tested, and eventually lowered to Eristavi IR without inventing alternate syntax.

## Current pipeline

```text
.eri source
    ↓
lexer
    ↓
parser / AST
    ↓
name resolution + semantic analysis + type inference
    ↓                         ↘
bootstrap execution runtime    typed Eristavi IR
                                   ↓
                                C backend
                                   ↓
                              system C compiler
                                   ↓
                              native executable
```

The AST execution runtime is still the broadest implementation path. The typed IR and C/native path intentionally cover a smaller scalar/control subset while the IR stabilizes.

## Implemented frontend/runtime surface

The bootstrap now implements the main frozen pre-0.1 vertical slices:

- exact 28-keyword lexical vocabulary, Unicode/NFC identifiers, nested comments, numeric/Text literals and locked whitespace rules;
- `let`, transitive `fixed`, name-first annotations, assignment and lexical no-shadowing;
- checked signed-64-bit `Int`, deterministic binary64-oriented `Float`, `Bool`, and `Text` scalar behavior;
- operator precedence, Bool-only conditions, `if` / `else`, `while`, and ordered stable `for` iteration;
- module-level functions, typed and inferred result contracts, no-value functions, recursion, completion analysis, and ordinary value parameters;
- compiler-inferred generic parameter relationships with per-call specialization and body constraints for the implemented type operations;
- ordered growable `List` values with homogeneous inference, deferred empty-list inference, zero-based checked indexing, `.count`, `.add`, indexed mutation, equality, `fixed` interaction, value semantics, and stable iteration;
- user-defined ordinary value types, fixed fields, named-field construction, nested mutation, structural equality, and value copying;
- `maybe T` / `none`, presence checks and basic flow-sensitive narrowing;
- explicit managed `identity T`, identity equality, aliasing, field mutation, and deep-`fixed` rejection of identity-bearing values;
- checked error declarations, `fails`, `fail`, typed/catch-all `else error`, exhaustiveness, and `try` propagation;
- deterministic `with` ownership for the bootstrap `std.files` resource API, including checked cleanup-failure analysis and runtime primary/secondary failure preservation;
- user modules/imports, aliases, public/private declarations, declaration-only imported modules, circular-import diagnostics, and source-root project loading;
- `run` and `check` commands for the broad bootstrap runtime.

The implementation deliberately rejects unsupported frozen features instead of assigning them provisional behavior.

## Typed IR and compilation backend

`ir.py` defines the first machine-independent typed Eristavi IR. It currently lowers a concrete scalar/control subset:

- `Int`, `Float`, `Bool`, and literal `Text` values;
- local bindings and direct-name assignment;
- scalar expressions and comparisons;
- `if` / `else` and `while`;
- concrete non-generic functions, calls, returns, and recursion;
- `output(value)` for scalar values.

`c_backend.py` consumes that IR and emits C11 plus small runtime helpers for checked `Int` operations, binary64-oriented Float operations, Text equality, and output. `erist build` then invokes the configured system C compiler. This is the first native compilation path, but it is **not** yet a direct CPU backend and does not yet have full frontend feature parity.

Commands:

```text
python -m compiler.erist run examples/hello.eri
python -m compiler.erist check examples/hello.eri
python -m compiler.erist build-c examples/hello.eri -o hello.c
python -m compiler.erist build examples/hello.eri -o hello
```

When installed through `pyproject.toml`, the same commands are available through `erist`.

For multi-file programs, pass `--source-root` when the entry file's parent is not the intended project source root.

## Tests

Run:

```text
python -m unittest discover -s tests -v
```

The current suite contains **80 tests** spanning the frontend/runtime, module loader, and first compiled backend. It includes interpreter and compiled execution checks, checked arithmetic faults, recursion, collections, values, maybe/identity/error/resource behavior, generic relationships, module boundaries, Unicode identifiers in generated C, and Text escaping/equality in the native path.

## Known implementation boundary

The broad bootstrap frontend/runtime is substantially ahead of the typed IR backend. Full pre-0.1 compiled-backend parity still requires lowering/runtime support for Lists, user values, maybe, checked errors, identities, resources, modules, and generic specializations. Explicit Unicode Text views (`characters`, `scalars`, `bytes`) also remain a frontend/runtime gap and are recorded in `IMPLEMENTATION_AUDIT.md`.

Implementation should continue to follow the frozen specifications rather than changing language semantics for backend convenience.
