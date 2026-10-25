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

Unicode identifier, normalization and grapheme behavior is pinned to Unicode **17.0.0**. CI executes the complete official Unicode-17 `GraphemeBreakTest` fixture against the pinned reference segmenter in addition to compiled/direct grapheme tests.

## Self-hosting progress

The trusted Stage-0 toolchain is still written in Python. `src/compiler/` now
contains an Eristavi-written lexer and parser with an explicit identity AST.
Recursive result contracts remain explicit; generic relationships remain inferred.
Differential tests check lexical tokens, locations, rejection behavior and parser
precedence against Stage-0. The Eristavi lexer and parser also compile and execute
through the portable C route.

The new `std.unicode` library exposes pinned Unicode-17 identifier checks, NFC
normalization and scalar construction. It currently executes in the reference
runtime and generated-C backend. Direct native, JavaScript and Wasm support for
this library remains pending; those routes reject its use with guidance to use
`erist build`. Existing direct-native functionality remains available.

`src/frontend.eri` is now a usable syntax frontend: it reads a source file,
checks syntax and emits token/AST JSON reports. The compiled executable runs
offline without Python or a C compiler at runtime. Building it still uses Stage-0
and a C toolchain. Syntax commands retain their existing behavior; experimental
semantic commands are described below. The experimental `ir` and `emit-c` commands now compile a concrete Int/Float/Bool/Text
slice with inferred scalar specialization through an Eristavi-written typed IR and verified C emitter. See
[`SCALAR_COMPILATION.md`](SCALAR_COMPILATION.md) for executable examples and boundaries.
Stage-0 remains the normal compiler.

```text
erist build src/frontend.eri --source-root src -o erist-frontend
./erist-frontend check examples/hello.eri
./erist-frontend ast examples/hello.eri --output hello.ast.json
```

See [`FRONTEND_TOOL.md`](FRONTEND_TOOL.md) for build/use/report contracts and
[`SELF_HOSTING.md`](SELF_HOSTING.md) for the migration. This is not yet a compiler
that can build itself.

### Experimental semantic analysis

The Eristavi-written frontend now also resolves source modules, names and scopes,
infers static relationships, and checks fixed/maybe/identity, checked failures and
resource contracts. It records expression type/effect facts and can explain inferred
function signatures. Stage-0 remains the reference and normal compiler.

```text
./erist-frontend analyze project/src/application.eri --source-root project/src
./erist-frontend analyze-report project/src/application.eri --source-root project/src
```

A shared 175-case corpus checks acceptance/rejection and inferred contracts against
Stage-0. The compiled analyzer also analyzes its own frontend module graph offline.
See [`SEMANTIC_ANALYSIS.md`](SEMANTIC_ANALYSIS.md) for evidence, diagnostic differences
and remaining promotion gates. No frozen syntax or semantic specification changed.

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

Universal IR is verified before/after bootstrap optimization. Current passes include constant folding and unreachable-block elimination. CFG-aware liveness, interference, spill-slot coloring, escape analysis and register-candidate analysis are available to direct backends. The x86-64 backend consumes those analyses through a contract-driven physical-register allocator for short-lived scalar regions.

## Direct native backends

### x86-64 Linux

The direct x86-64 route executes a broad pre-0.1 implementation without generated C: functions/recursion, Int/Bool/Float/Text, all explicit Text views, Lists, ordinary values, maybe, identity, checked failures, inferred generic specializations, deterministic file resources and module-object linkage.

The runtime includes a non-moving mark-and-sweep collector. Compiler root frames are **liveness-aware** and pair stable heap root addresses with static type descriptors. Typed traversal handles Text leaves, nominal fields, Lists, maybe/identity wrappers and file-resource records; conservative exact-pointer scanning remains only as a fallback for dynamic runtime state.

Physical register allocation now uses CFG interference together with explicit x86 lowering use/clobber contracts. The audited allocation pools currently include two GP registers (`r10`, `r11`) and two XMM registers (`xmm8`, `xmm9`). Values that cross helper/PLT/GC clobbers remain spilled, while audited call-free scalar operations, safe extraction operations and scalar call results may stay register-resident. Unknown lowerings default to conservative full caller-saved clobbers. Register-resident scalars no longer reserve redundant spill slots in the precise x86 frame; pinned heap/root slots remain stable and take precedence over compaction.

### ARM64 Linux

ARM64 consumes the same Universal IR and covers Int/Bool/Float, functions, Text, ordinary values, Lists, maybe, identity, checked failures and deterministic file resources. The hosted CI matrix includes a native ARM64 Linux runner, so aggregate/error/resource behavior is executed rather than only cross-assembled. Mixed scalar/Text output also preserves source order through the composed ARM64 direct backend.

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

The ES2020 backend preserves checked Eristavi `Int` through `BigInt` and executes ordinary nominal values, Lists, maybe, identity, deep value cloning and structural equality in addition to scalar/function/control-flow behavior.

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

The current suite contains **344 tests**. The hosted CI matrix runs:

- GCC / x86-64 Ubuntu / `-O2`;
- Clang / x86-64 Ubuntu / `-O2`;
- Clang / ARM64 Ubuntu / `-O2`;
- Clang / ARM64 macOS / `-O2`.

The matrix also downloads an immutable-revision copy of the official Unicode 17 `GraphemeBreakTest` fixture and executes all of its vectors. Platform-specific direct-native cases run on their matching Linux architecture.

See [`IMPLEMENTATION_AUDIT.md`](IMPLEMENTATION_AUDIT.md) for the audited boundary and remaining production work.

## Documentation

- [`SEMANTIC_ANALYSIS.md`](SEMANTIC_ANALYSIS.md) — experimental Eristavi-written semantic analyzer
- [`FRONTEND_TOOL.md`](FRONTEND_TOOL.md) — Eristavi-written frontend executable
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
