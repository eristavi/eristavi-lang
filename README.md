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

The **pre-0.1 source-language/frontend contract is frozen for implementation**.

The Python bootstrap implements the principal frozen language surface through collections, user-defined values, maybe/identity, checked errors, deterministic resources, modules/imports, inferred generic relationships, and explicit Unicode Text views.

Unicode identifier, normalization and grapheme behavior is pinned to Unicode **17.0.0**. All three explicit Text views now execute through the compiled C path:

```eri
text.characters
text.scalars
text.bytes
```

Compiled `Text` uses explicit UTF-8 bytes plus length rather than C-string semantics, preserving embedded NUL and validating UTF-8 at file boundaries.

### Compiler layers

Eristavi now has both a broad portability backend and the beginning of a direct native architecture:

```text
Eristavi source
    ↓
frontend / semantic analysis
    ↓
typed Eristavi IR
    ├──────────────→ C11 → system C compiler → native executable
    ↓
Universal IR
    ↓
direct x86-64 backend → assembly → system assembler/linker → native executable
```

The generated-C backend covers the broad pre-0.1 implementation surface. The first direct x86-64 Linux slice is intentionally narrower and currently proves Int/Bool locals, checked integer arithmetic, comparisons, `if / else`, `while`, and output without generated C.

### Module artifacts

The compiler can emit deterministic, versioned `.eri-interface.json` module artifacts. Importers can type-check public types, checked-error contracts and inferred generic function relationships from the interface even when the imported `.eri` implementation source is unavailable.

Executable linkage still requires implementation source until compiled object/module artifacts are added.

See [`IMPLEMENTATION_AUDIT.md`](IMPLEMENTATION_AUDIT.md) for the current audited boundary.

## Design direction

Eristavi aims for:

- a small, stable core vocabulary;
- one obvious way to express fundamental concepts;
- strong static typing with aggressive type inference;
- a rich standard library instead of keyword bloat;
- automatic memory management;
- deterministic cleanup for files, sockets, and other external resources;
- machine-neutral compiler IRs;
- direct native compilation for supported CPU architectures;
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
function preserve(value) {
    return value;
}

output(preserve(10));
output(preserve("Hello"));
```

Text indexing makes the intended Unicode unit explicit:

```eri
let text be "A\u{301}";
output(text.characters.count); // 1 grapheme cluster
output(text.scalars.count);    // 2 Unicode scalars
output(text.bytes.count);      // 3 UTF-8 bytes
```

Standard-library capability grows without keyword growth. For example:

```eri
import std.files;

function exists(path Text) returns Bool fails files.FileError {
    return try files.exists(path);
}
```

Checked failures remain explicit, and deterministic resources use `with` rather than manual lifetime management.

## Toolchain

Bootstrap execution/checking:

```text
erist run examples/hello.eri
erist check examples/hello.eri
```

Versioned module interface:

```text
erist interface models/user.eri
```

Broad generated-C backend:

```text
erist build-c examples/hello.eri -o hello.c
erist build examples/hello.eri -o hello
```

First Universal-IR/direct backend commands:

```text
erist uir examples/hello.eri -o hello.uir
erist build-asm examples/hello.eri -o hello.s --target x86_64-linux
erist build-direct examples/hello.eri -o hello --target x86_64-linux
```

The direct route emits CPU assembly from Eristavi Universal IR; it does not generate C source. The system compiler driver is currently used only as assembler/linker for `build-direct`.

## Tests

```text
python -m unittest discover -s tests -v
```

The suite now contains **174 tests**. CI runs the full suite with GCC and Clang on Ubuntu and Clang on macOS at `-O2`. Direct x86-64 executable tests run on the Linux jobs; macOS validates the rest of the portable compiler/runtime surface.

Coverage now includes versioned source-independent module interfaces, pinned compiled Unicode grapheme segmentation, generated-C execution, Universal IR, real direct x86-64 execution, checked direct arithmetic faults, and expanded `std.files` path operations.

## Documentation

- [`PRE_0_1_FREEZE.md`](PRE_0_1_FREEZE.md) — frozen source-language/frontend boundary
- [`IMPLEMENTATION_AUDIT.md`](IMPLEMENTATION_AUDIT.md) — current implementation coverage, backend status, and audited gaps
- [`DESIGN_PHILOSOPHY.md`](DESIGN_PHILOSOPHY.md) — governing design charter
- [`LANGUAGE_SEMANTICS.md`](LANGUAGE_SEMANTICS.md) — consolidated semantics
- [`GRAMMAR.md`](GRAMMAR.md) — consolidated surface grammar
- [`LEXICAL_RULES.md`](LEXICAL_RULES.md) — lexical rules
- [`TEXT_VIEWS.md`](TEXT_VIEWS.md) — Unicode character/scalar/UTF-8 views
- [`MODULE_INTERFACES.md`](MODULE_INTERFACES.md) — serialized public module contracts
- [`UNIVERSAL_IR.md`](UNIVERSAL_IR.md) — lower target-neutral IR and direct backend boundary
- [`STANDARD_LIBRARY.md`](STANDARD_LIBRARY.md) — current bootstrap standard-library surface
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
- [`TARGETS.md`](TARGETS.md) — target strategy and direct backend status

## License

Eristavi is released under the MIT License.
