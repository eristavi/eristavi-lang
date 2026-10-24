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

The **pre-0.1 source-language/frontend contract is frozen for implementation**. The Python bootstrap frontend/runtime covers the principal frozen surface: functions, collections, ordinary values, maybe/identity, checked errors, deterministic resources, modules/imports, inferred generic relationships and explicit Unicode Text views.

Unicode identifier, normalization and grapheme behavior is pinned to Unicode **17.0.0**. The broad generated-C path supports all three explicit Text views. The direct x86-64 path now does too, including pinned grapheme segmentation without generated C.

## Compiler architecture

```text
Eristavi source
    ↓
lexer / parser / semantic analysis + inference
    ↓
typed/source-close Eristavi IR
    ├─→ C11 backend → C toolchain → native executable
    ↓
verified + optimized Universal IR
    ├─→ x86-64 Linux → native executable
    ├─→ ARM64 Linux → assembly/native on matching host
    ├─→ ES2020 JavaScript
    └─→ WebAssembly text (current scalar/function slice)
```

Universal IR is verified before/after bootstrap optimization. Current passes include constant folding and unreachable-block elimination, with liveness, stack-slot, escape-analysis and register-candidate analysis available for later backend use.

The direct x86-64 route executes a broad pre-0.1 implementation without generated C: functions/recursion, Int/Bool/Float/Text, all explicit Text views, Lists, ordinary values, maybe, identity, checked failures, inferred generic specializations, deterministic file resources and module-object linkage.

The x86-64 runtime also has a non-moving mark-and-sweep bootstrap collector. Compiler-described root frames include heap-typed locals and Universal-IR temporaries. Heap child traversal still uses exact tracked-pointer discovery across allocation payload words; typed heap descriptors remain a production-hardening step.

ARM64 consumes the same Universal IR and now has assembly-generation layers for Text, aggregates, maybe/identity, checked failures and deterministic file resources in addition to scalar/functions. CI cross-assembles the generated AArch64 code; broad native ARM64 Linux execution still requires an ARM64 Linux runner.

## Module artifacts and incremental compilation

```text
module.eri
  ├─→ module.eri-interface.json
  └─→ module.eri-object.json
```

`erist interface` emits a deterministic public contract. `erist object` emits a versioned Universal-IR implementation bound to that interface digest.

Object format v3 can also carry a bootstrap reusable implementation template for public inferred-generic functions. Downstream compilation can specialize those functions after the original dependency `.eri` file has been removed, without adding explicit generic syntax to Eristavi.

`erist compile-module` provides content/interface-digest keyed reusable artifact caching. Public dependency changes invalidate importers; private implementation-only dependency changes do not invalidate an unchanged public contract key.

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
- C, JavaScript and WebAssembly targets preserving Eristavi semantics;
- clear compiler diagnostics;
- performance transparency without forcing low-level complexity into ordinary code.

See [`DESIGN_PHILOSOPHY.md`](DESIGN_PHILOSOPHY.md).

## Syntax examples

```eri
let x be 40;
let y be 2;
output(x + y);
```

```eri
function double(value Int) {
    return value * 2;
}

output(double(21));
```

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

```text
erist run examples/hello.eri
erist check examples/hello.eri

erist interface models/user.eri
erist object models/user.eri
erist compile-module models/user.eri

erist build-c examples/hello.eri -o hello.c
erist build examples/hello.eri -o hello

erist uir examples/hello.eri -o hello.uir
erist build-asm examples/hello.eri -o hello.s --target x86_64-linux
erist build-direct examples/hello.eri -o hello --target x86_64-linux
erist link-direct examples/hello.eri -o hello --target x86_64-linux

erist build-asm examples/hello.eri -o hello-aarch64.s --target arm64-linux

erist build-js examples/hello.eri -o hello.mjs
erist build-wat examples/hello.eri -o hello.wat
```

## Tests

```text
python -m unittest discover -s tests -v
```

The current suite contains **245 tests** and passes in all three CI jobs:

- GCC on Ubuntu at `-O2`;
- Clang on Ubuntu at `-O2`;
- Clang on macOS at `-O2`.

Direct x86-64 executable tests run on Linux. ARM64 assembly is cross-assembled in CI; native ARM64 Linux execution remains host-gated. JavaScript tests execute with an available JS runtime, while the current WebAssembly target is validated at the emitted WAT contract level.

See [`IMPLEMENTATION_AUDIT.md`](IMPLEMENTATION_AUDIT.md) for the audited boundary and remaining production work.

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
- [`DIRECT_BACKENDS.md`](DIRECT_BACKENDS.md) — direct backend status
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
