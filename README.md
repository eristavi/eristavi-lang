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

Eristavi is currently in the **pre-0.1 specification and compiler-bootstrap stage**. Core semantics are largely settled; the remaining specification work is being narrowed before frontend implementation begins.

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

- [`DESIGN_PHILOSOPHY.md`](DESIGN_PHILOSOPHY.md) — governing design charter
- [`LANGUAGE_SEMANTICS.md`](LANGUAGE_SEMANTICS.md) — consolidated pre-0.1 semantics
- [`GRAMMAR.md`](GRAMMAR.md) — consolidated pre-0.1 surface grammar
- [`OUTPUT.md`](OUTPUT.md) — standard textual output
- [`CONSTRUCTION.md`](CONSTRUCTION.md) — named-field construction and initialization
- [`IDENTITY_EQUALITY.md`](IDENTITY_EQUALITY.md) — explicit identity equality semantics
- [`VALUE_PARAMETER_MUTATION.md`](VALUE_PARAMETER_MUTATION.md) — ordinary value-parameter behavior
- [`ERRORS.md`](ERRORS.md) — typed checked errors and propagation
- [`GENERICS.md`](GENERICS.md) — compiler-inferred generic abstraction
- [`TARGETS.md`](TARGETS.md) — native, C, JavaScript, and WebAssembly target strategy

## Compiler bootstrap

The first compiler implementation will live under [`compiler/`](compiler/) and grow from the settled bootstrap subset rather than attempting to implement every future language feature at once.

The initial example is [`examples/hello.eri`](examples/hello.eri).

## License

Eristavi is released under the MIT License.
