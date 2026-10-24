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

The **pre-0.1 source-language/frontend contract is frozen for implementation**. The Python bootstrap frontend/runtime covers the principal frozen language surface: functions, collections, ordinary values, maybe/identity, checked errors, deterministic resources, modules/imports, inferred generic relationships and explicit Unicode Text views.

Unicode identifier, normalization and grapheme behavior is pinned to Unicode **17.0.0**. The broad generated-C backend supports all three explicit Text views, including compiled grapheme segmentation. Compiled Text is length-aware UTF-8 rather than C-string data, so embedded NUL and UTF-8 validation preserve Eristavi semantics.

## Compiler architecture

Eristavi now has three useful execution/compiler layers:

```text
Eristavi source
    ↓
lexer / parser / semantic analysis + inference
    ↓
typed/source-close Eristavi IR
    ├─→ C11 backend → C toolchain → native executable
    ↓
Universal IR
    ├─→ x86-64 Linux direct backend → assembly → native executable
    └─→ ARM64 Linux backend → assembly
```

The direct x86-64 path no longer depends on generated C and now executes a substantial pre-0.1 subset: functions/recursion, Int/Bool/Float/Text, Lists, ordinary values, maybe, identity, checked failures, inferred source-generic specializations, deterministic file resources and module-object linkage.

The ARM64 backend consumes the **same Universal IR** for the current scalar/function slice. CI cross-assembles its AArch64 output; native ARM64 execution activates when an ARM64 Linux runner is available.

## Module artifacts

Eristavi separates public contracts from concrete implementation artifacts:

```text
module.eri
  ├─→ module.eri-interface.json
  └─→ module.eri-object.json
```

`erist interface` emits a deterministic versioned public contract. `erist object` emits a versioned concrete Universal-IR implementation bound to the interface digest.

For supported concrete functions and types, the direct compiler can type-check and link a dependency from the interface + object pair **after its `.eri` implementation source has been removed**.

## Design direction

Eristavi aims for:

- a small, stable core vocabulary;
- one obvious way to express fundamental concepts;
- strong static typing with aggressive type inference;
- a rich standard library instead of keyword bloat;
- automatic memory management;
- deterministic cleanup for files, sockets and other external resources;
- machine-neutral compiler IRs;
- direct native compilation for supported CPU architectures;
- C, JavaScript and WebAssembly as strategic additional targets;
- clear compiler diagnostics;
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

Ordinary user-defined types are values:

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

Generic relationships are inferred rather than written with generic syntax:

```eri
function preserve(value) {
    return value;
}

output(preserve(10));
output(preserve("Hello"));
```

Unicode units are explicit:

```eri
let text be "A\u{301}";
output(text.characters.count); // 1 grapheme cluster
output(text.scalars.count);    // 2 Unicode scalars
output(text.bytes.count);      // 3 UTF-8 bytes
```

Checked failures and deterministic resources remain explicit:

```eri
import std.files;

function read(path Text) returns Text fails files.FileError {
    with file be try files.open(path) {
        return try file.readText();
    }
}
```

## Toolchain

Bootstrap/reference execution:

```text
erist run examples/hello.eri
erist check examples/hello.eri
```

Module artifacts:

```text
erist interface models/user.eri
erist object models/user.eri
```

Broad generated-C path:

```text
erist build-c examples/hello.eri -o hello.c
erist build examples/hello.eri -o hello
```

Universal IR / direct CPU paths:

```text
erist uir examples/hello.eri -o hello.uir

erist build-asm examples/hello.eri -o hello.s --target x86_64-linux
erist build-direct examples/hello.eri -o hello --target x86_64-linux

erist build-asm examples/hello.eri -o hello-aarch64.s --target arm64-linux
```

The direct route emits CPU assembly from Eristavi Universal IR; generated C is not involved.

## Tests

```text
python -m unittest discover -s tests -v
```

The current suite contains **216 tests** and passes in all three CI jobs:

- GCC on Ubuntu at `-O2`;
- Clang on Ubuntu at `-O2`;
- Clang on macOS at `-O2`.

Direct x86-64 executable tests run on Linux. ARM64 assembly is cross-assembled in CI; native ARM64 execution is skipped unless the runner itself is ARM64 Linux.

Coverage includes frontend semantics, generated-C execution, pinned Unicode, serialized interfaces/objects, source-independent object linkage, direct functions/ABI, Float/Text, deep values, Lists, maybe, identity, checked errors, deterministic resources and inferred generic specializations.

See [`IMPLEMENTATION_AUDIT.md`](IMPLEMENTATION_AUDIT.md) for the audited boundary and remaining work.

## Documentation

- [`PRE_0_1_FREEZE.md`](PRE_0_1_FREEZE.md) — frozen source-language/frontend boundary
- [`IMPLEMENTATION_AUDIT.md`](IMPLEMENTATION_AUDIT.md) — current audited implementation status
- [`DESIGN_PHILOSOPHY.md`](DESIGN_PHILOSOPHY.md) — governing design charter
- [`LANGUAGE_SEMANTICS.md`](LANGUAGE_SEMANTICS.md) — consolidated semantics
- [`GRAMMAR.md`](GRAMMAR.md) — consolidated surface grammar
- [`LEXICAL_RULES.md`](LEXICAL_RULES.md) — lexical rules
- [`TEXT_VIEWS.md`](TEXT_VIEWS.md) — Unicode character/scalar/UTF-8 views
- [`MODULE_INTERFACES.md`](MODULE_INTERFACES.md) — versioned contract and implementation artifacts
- [`UNIVERSAL_IR.md`](UNIVERSAL_IR.md) — target-neutral lower IR
- [`DIRECT_BACKENDS.md`](DIRECT_BACKENDS.md) — x86-64 and ARM64 direct backend status
- [`STANDARD_LIBRARY.md`](STANDARD_LIBRARY.md) — current standard-library surface
- [`COLLECTIONS.md`](COLLECTIONS.md) — `List`
- [`FIXED_IMMUTABILITY.md`](FIXED_IMMUTABILITY.md) — transitive `fixed`
- [`VALUE_EQUALITY.md`](VALUE_EQUALITY.md) — ordinary structural equality
- [`IDENTITY_EQUALITY.md`](IDENTITY_EQUALITY.md) — identity equality
- [`ERRORS.md`](ERRORS.md) — checked failures
- [`RESOURCE_CLEANUP.md`](RESOURCE_CLEANUP.md) — deterministic cleanup and dual-failure composition
- [`GENERICS.md`](GENERICS.md) — inferred generic relationships
- [`TARGETS.md`](TARGETS.md) — target strategy and implementation status

## License

Eristavi is released under the MIT License.
