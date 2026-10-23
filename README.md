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

Eristavi is currently in the **language-design and compiler-bootstrap stage**. Syntax and semantics that are not explicitly marked as settled may change while the first specification is being developed.

## Design direction

Eristavi aims for:

- a small, stable core vocabulary;
- one obvious way to express fundamental concepts;
- strong static typing with aggressive type inference;
- a rich standard library instead of keyword bloat;
- automatic memory management;
- deterministic cleanup for files, sockets, and other external resources;
- a machine-neutral intermediate representation;
- native compilation for supported CPU architectures;
- a portable execution format for broader compatibility;
- clear compiler diagnostics that explain how to fix problems;
- performance transparency without forcing low-level complexity into ordinary code.

See [`DESIGN_PHILOSOPHY.md`](DESIGN_PHILOSOPHY.md) for the governing design charter.

## Early syntax example

```eri
let x be 40;
let y be 2;

print x + y;
```

The intended result is:

```text
42
```

Collection types are intended to be inferred whenever the compiler has enough information:

```eri
let names be ["Anna", "Maria", "John"];
let customers be [];

customers.add(Customer("Anna"));
customers.add(Customer("John"));
```

The compiler should infer the element types rather than requiring generic type syntax in ordinary code.

## Documentation

- [`DESIGN_PHILOSOPHY.md`](DESIGN_PHILOSOPHY.md) — governing principles
- [`LANGUAGE_SEMANTICS.md`](LANGUAGE_SEMANTICS.md) — current semantic decisions and open questions
- [`GRAMMAR.md`](GRAMMAR.md) — draft surface grammar

## License

Eristavi is released under the MIT License.
