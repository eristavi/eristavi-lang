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

The **pre-0.1 source-language/frontend contract is frozen for implementation**. The bootstrap/reference runtime covers the principal frozen surface: functions, collections, ordinary values, maybe/identity, checked errors, deterministic resources, modules/imports, inferred generic relationships and explicit Unicode Text views.

Unicode identifier, normalization and grapheme behavior is pinned to Unicode **17.0.0**. CI now executes the complete official Unicode-17 `GraphemeBreakTest` fixture against the pinned reference segmenter in addition to compiled/direct grapheme tests.

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
    ├─→ ARM64 Linux → native executable
    ├─→ ES2020 JavaScript
    └─→ WebAssembly text
```

Universal IR is verified before/after bootstrap optimization. Current passes include constant folding and unreachable-block elimination. CFG-aware liveness, interference, spill-slot coloring, escape analysis and register-candidate analysis are also available to direct backends.

## Direct native backends

### x86-64 Linux

The direct x86-64 route executes a broad pre-0.1 implementation without generated C: functions/recursion, Int/Bool/Float/Text, all explicit Text views, Lists, ordinary values, maybe, identity, checked failures, inferred generic specializations, deterministic file resources and module-object linkage.

The runtime includes a non-moving mark-and-sweep collector. Compiler root frames are now **liveness-aware** and pair stable heap root addresses with static type descriptors. Typed traversal handles Text leaves, nominal fields, Lists, maybe/identity wrappers and file-resource records; conservative exact-pointer scanning remains only as a fallback for dynamic runtime state. Scalar Universal-IR temporaries also reuse CFG-noninterfering spill slots.

### ARM64 Linux

ARM64 consumes the same Universal IR and covers Int/Bool/Float, functions, Text, ordinary values, Lists, maybe, identity, checked failures and deterministic file resources. The hosted CI matrix now includes a native ARM64 Linux runner, so aggregate/error/resource behavior is executed rather than only cross-assembled. Mixed scalar/Text output also preserves source order through the composed ARM64 direct backend.

## Module artifacts and incremental compilation

```text
module.eri
  ├─→ module.eri-interface.json
  └─→ module.eri-object.json
```

`erist interface` emits a deterministic public contract. `erist object` emits a versioned Universal-IR implementation bound to that interface digest.

Object format v3 can carry a reusable bootstrap implementation template for public inferred-generic functions. Downstream compilation can specialize those functions after the original dependency `.eri` file has been removed, without adding explicit generic syntax to Eristavi.

`erist compile-module` provides content/interface-digest keyed artifact caching. Public dependency changes invalidate importers; private implementation-only changes do not invalidate an unchanged public-contract key.

## JavaScript and WebAssembly

The ES2020 backend preserves checked Eristavi `Int` through `BigInt` and now executes ordinary nominal values, Lists, maybe, identity, deep value cloning and structural equality in addition to scalar/function/control-flow behavior.

The WebAssembly-text backend supports the current scalar/function/control slice plus Text through an explicit `externref` host ABI. UTF-8 constants are emitted as data segments; Text construction, concatenation, equality and output are explicit host contracts rather than numeric approximations.

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
erist build-direct examples/hello.eri -o hello-aarch64 --target arm64-linux

erist build-js examples/hello.eri -o hello.mjs
erist build-wat examples/hello.eri -o hello.wat
```

## Tests

```text
python -m unittest discover -s tests -v
```

The current suite contains **255 tests** and passes in all four hosted CI jobs:

- GCC / x86-64 Ubuntu / `-O2`;
- Clang / x86-64 Ubuntu / `-O2`;
- Clang / ARM64 Ubuntu / `-O2`;
- Clang / ARM64 macOS / `-O2`.

The matrix also downloads an immutable-revision copy of the official Unicode 17 `GraphemeBreakTest` fixture and executes all of its vectors. Platform-specific direct-native cases run on their matching Linux architecture.

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
