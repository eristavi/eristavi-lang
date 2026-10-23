# Eristavi

Eristavi is an experimental general-purpose programming language focused on **readability, strong typing, native performance, universal portability, and controlled simplicity**.

> **Complexity belongs in the compiler and runtime, not in the programmer's code.**

## Project identity

- **Language:** Eristavi
- **Source files:** `.eri`
- **Reserved extension:** `.erist`
- **CLI/toolchain:** `erist`
- **Official website:** https://eristavi.org
- **Repository:** `eristavi/eristavi-lang`

## Status

The **pre-0.1 source-language/frontend contract is frozen for implementation**. The Python bootstrap now implements the principal frozen language slices through collections, user-defined values, maybe/identity, checked errors, deterministic resources, modules/imports, and compiler-inferred generic relationships.

The project also has its first typed Eristavi IR and working compiled path:

```text
Eristavi source → frontend → typed Eristavi IR → C → system C compiler → native executable
```

The AST bootstrap runtime currently has broader feature coverage than the typed IR/C backend. See [`IMPLEMENTATION_AUDIT.md`](IMPLEMENTATION_AUDIT.md) for the exact implementation boundary and remaining gaps.

## Design direction

Eristavi aims for:

- a small, stable core vocabulary;
- one obvious way to express fundamental concepts;
- strong static typing with aggressive type inference;
- a rich standard library instead of keyword bloat;
- automatic memory management;
- deterministic cleanup for files, sockets, and other external resources;
- a machine-neutral Eristavi intermediate representation;
- native compilation for supported CPU architectures;
- C, JavaScript, and WebAssembly as strategic additional targets;
- clear compiler diagnostics that explain how to fix problems;
- performance transparency without forcing low-level complexity into ordinary code.

See [`DESIGN_PHILOSOPHY.md`](DESIGN_PHILOSOPHY.md).

## Syntax examples

```eri
let x be 40;
let y be 2;
output(x + y);
```

Functions may infer non-circular result contracts:

```eri
function double(value Int) {
    return value * 2;
}

output(double(21));
```

User-defined values use named fields:

```eri
type Customer {
    fixed id Int;
    name Text;
}

let customer be Customer {
    id = 1;
    name = "Anna";
};
```

Collections are ordinary values with inferred element relationships:

```eri
let customers be [];
customers.add(customer);
output(customers.count);
```

Generic relationships are inferred rather than written with generic syntax:

```eri
function identity(value) {
    return value;
}

output(identity(10));
output(identity("Hello"));
```

Checked failures remain explicit:

```eri
error LoadError {
    message Text;
}
```

and deterministic resources use `with` rather than manual lifetime management.

## Toolchain

Interpreter/runtime path:

```text
python -m compiler.erist run examples/hello.eri
python -m compiler.erist check examples/hello.eri
```

First compiled backend path:

```text
python -m compiler.erist build-c examples/hello.eri -o hello.c
python -m compiler.erist build examples/hello.eri -o hello
```

When installed via `pyproject.toml`, use the `erist` command directly.

## Tests

```text
python -m unittest discover -s tests -v
```

At the current audit point the suite contains **80 passing tests** covering frontend/runtime behavior, project modules, and the first C/native backend.

## Documentation

- [`PRE_0_1_FREEZE.md`](PRE_0_1_FREEZE.md) — frozen source-language/frontend boundary
- [`IMPLEMENTATION_AUDIT.md`](IMPLEMENTATION_AUDIT.md) — current implementation coverage, backend status, and audited gaps
- [`DESIGN_PHILOSOPHY.md`](DESIGN_PHILOSOPHY.md) — governing design charter
- [`LANGUAGE_SEMANTICS.md`](LANGUAGE_SEMANTICS.md) — consolidated semantics
- [`GRAMMAR.md`](GRAMMAR.md) — consolidated surface grammar
- [`LEXICAL_RULES.md`](LEXICAL_RULES.md) — lexical rules
- [`PRECEDENCE.md`](PRECEDENCE.md) — expression ordering
- [`FUNCTION_RETURNS.md`](FUNCTION_RETURNS.md) — function completion/result semantics
- [`COLLECTIONS.md`](COLLECTIONS.md) — `List`
- [`CONSTRUCTION.md`](CONSTRUCTION.md) — named-field construction
- [`FIXED_IMMUTABILITY.md`](FIXED_IMMUTABILITY.md) — transitive `fixed`
- [`VALUE_EQUALITY.md`](VALUE_EQUALITY.md) — ordinary structural equality
- [`IDENTITY_EQUALITY.md`](IDENTITY_EQUALITY.md) — identity equality
- [`ERRORS.md`](ERRORS.md) — checked failures
- [`RESOURCE_CLEANUP.md`](RESOURCE_CLEANUP.md) — deterministic cleanup and dual-failure composition
- [`GENERICS.md`](GENERICS.md) — inferred generic relationships
- [`TARGETS.md`](TARGETS.md) — target strategy

## License

Eristavi is released under the MIT License.
