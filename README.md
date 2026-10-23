# Eristavi

Eristavi is an experimental general-purpose programming language focused on **readability, strong typing, native performance, universal portability, and controlled simplicity**.

The guiding principle is simple:

> **Complexity belongs in the compiler and runtime, not in the programmer's code.**

## Project identity

- **Language:** Eristavi
- **Source files:** `.eri`
- **Reserved extension:** `.erist`
- **CLI/toolchain:** `erist`
- **Official website:** https://eristavi.org
- **Repository:** `eristavi/eristavi-lang`

## Status

The **pre-0.1 frontend semantics are frozen for implementation**. The Python bootstrap compiler is now under active development in `compiler/` and already runs the canonical hello program through a lexer, parser, AST, semantic analyzer, and temporary execution backend.

See [`PRE_0_1_FREEZE.md`](PRE_0_1_FREEZE.md) for the freeze boundary and deliberately postponed features.

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

See [`DESIGN_PHILOSOPHY.md`](DESIGN_PHILOSOPHY.md) for the governing design charter.

## Early syntax example

```eri
let x be 40;
let y be 2;

output(x + y);
```

The intended result is:

```text
42
```

`output(...)` is Eristavi's ordinary standard textual-output function. It is part of the standard environment rather than a language keyword.

User-defined values use named-field construction:

```eri
type Customer {
    name Text;
}

let anna be Customer {
    name = "Anna";
};
```

Collection element types and generic relationships are inferred when the compiler has enough static information:

```eri
let customers be [];

customers.add(Customer {
    name = "Anna";
});

customers.add(Customer {
    name = "John";
});
```

The compiler infers the element relationship rather than requiring explicit generic type syntax in ordinary pre-0.1 code.

## Documentation

- [`PRE_0_1_FREEZE.md`](PRE_0_1_FREEZE.md) — frozen frontend boundary and implementation handoff
- [`DESIGN_PHILOSOPHY.md`](DESIGN_PHILOSOPHY.md) — governing design charter
- [`LANGUAGE_SEMANTICS.md`](LANGUAGE_SEMANTICS.md) — consolidated pre-0.1 semantics
- [`GRAMMAR.md`](GRAMMAR.md) — consolidated pre-0.1 surface grammar
- [`LEXICAL_RULES.md`](LEXICAL_RULES.md) — lexical structure and literal rules
- [`PRECEDENCE.md`](PRECEDENCE.md) — expression precedence and associativity
- [`OUTPUT.md`](OUTPUT.md) — standard textual output
- [`FLOAT.md`](FLOAT.md) — deterministic Float semantics
- [`INTEGER_REMAINDER.md`](INTEGER_REMAINDER.md) — signed Int division and Int-only `%`
- [`COLLECTIONS.md`](COLLECTIONS.md) — pre-0.1 `List` model
- [`CONSTRUCTION.md`](CONSTRUCTION.md) — named-field construction and initialization
- [`FIXED_IMMUTABILITY.md`](FIXED_IMMUTABILITY.md) — transitive `fixed` eligibility
- [`IDENTITY_EQUALITY.md`](IDENTITY_EQUALITY.md) — explicit identity equality semantics
- [`VALUE_EQUALITY.md`](VALUE_EQUALITY.md) — structural ordinary value equality
- [`VALUE_PARAMETER_MUTATION.md`](VALUE_PARAMETER_MUTATION.md) — ordinary value-parameter behavior
- [`ERRORS.md`](ERRORS.md) — typed checked errors and propagation
- [`RESOURCE_CLEANUP.md`](RESOURCE_CLEANUP.md) — deterministic cleanup and dual-failure composition
- [`GENERICS.md`](GENERICS.md) — compiler-inferred generic abstraction
- [`TARGETS.md`](TARGETS.md) — native, C, JavaScript, and WebAssembly target strategy

## Compiler bootstrap

The active bootstrap implementation lives under [`compiler/`](compiler/).

From the repository root, the current vertical slice can run:

```text
python -m compiler.erist run examples/hello.eri
```

Expected output:

```text
42
```

The package also defines the `erist` console command through `pyproject.toml` when installed in a Python environment.

Current tests can be run with:

```text
python -m unittest discover -s tests -v
```

The compiler will grow incrementally from the frozen subset rather than trying to implement every language feature at once.

## License

Eristavi is released under the MIT License.
