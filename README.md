# Eristavi

A readable, strongly typed programming language with its own compiler architecture, machine-neutral IR and native code generators.

Eristavi is currently pre-0.1 and under active development.

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

`src/compiler/` now contains Eristavi-written parsing, semantic analysis, structural
typed IR, verification, Universal IR, unreachable-block removal and native x86-64/
ARM64 instruction consumers. The separate Linux offline bundle uses these components
without Python or a C compiler during normal application builds. Its runtime is
still a prebuilt C bootstrap artifact, now wrapped by a native-only typed
non-moving heap collector; GNU assembler/linker tools are still packaged.

```sh
python -m pip install -e .
CFLAGS=-O2 python tools/build_offline.py --output /tmp/erist-offline
/tmp/erist-offline/bin/erist build examples/scalar_compilation.eri -o /tmp/application
```

Packaging requires a fixed-snapshot repeated native self-build and an offline audit.
See [OFFLINE_TOOLCHAIN.md](OFFLINE_TOOLCHAIN.md) for supported hosts, evidence and
boundaries. The pip-installed developer CLI remains the Python Stage-0 reference,
including its existing artifacts and JS/Wasm routes; the native bundle is opt-in.
The frozen language philosophy and source specifications are unchanged.

[PRODUCTION_HARDENING.md](PRODUCTION_HARDENING.md) records the runtime review,
checked-unwind/temporary-slot fixes, native heap reclamation and remaining
qualification gates. [NATIVE_HEAP_GC.md](NATIVE_HEAP_GC.md) records the collector's
root/traversal contract. Optional allocation profiling remains available through
[HEAP_DIAGNOSTICS.md](HEAP_DIAGNOSTICS.md).

The lower-level frontend still offers syntax/token/AST inspection plus semantic,
typed-IR, Universal-IR, C and native-assembly commands. See
[FRONTEND_TOOL.md](FRONTEND_TOOL.md) and [SELF_HOSTING.md](SELF_HOSTING.md).

The next runtime batch adds opt-in owned Linux x86-64 packaging (`--runtime owned`),
static startup, geometric List prefix storage and indexed interior GC roots. Its
compiler self-build qualification and remaining bootstrap boundaries are recorded
in [OWNED_BUILD_INTEGRATION.md](OWNED_BUILD_INTEGRATION.md).

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

The Stage-0 direct runtime includes a non-moving mark-and-sweep collector. Compiler root frames are **liveness-aware** and pair stable heap root addresses with static type descriptors. Typed traversal handles Text leaves, nominal fields, Lists, maybe/identity wrappers and file-resource records; conservative exact-pointer scanning remains only as a fallback for dynamic runtime state.

Physical register allocation now uses CFG interference together with explicit x86 lowering use/clobber contracts. The audited allocation pools currently include two GP registers (`r10`, `r11`) and two XMM registers (`xmm8`, `xmm9`). Values that cross helper/PLT/GC clobbers remain spilled, while audited call-free scalar operations, safe extraction operations and scalar call results may stay register-resident. Unknown lowerings default to conservative full caller-saved clobbers. Register-resident scalars no longer reserve redundant spill slots in the precise x86 frame; pinned heap/root slots remain stable and take precedence over compaction.

### ARM64 Linux

ARM64 consumes the same Universal IR and covers Int/Bool/Float, functions, Text, ordinary values, Lists, maybe, identity, checked failures and deterministic file resources. The hosted CI matrix includes a native ARM64 Linux runner, so aggregate/error/resource behavior is executed rather than only cross-assembled. Mixed scalar/Text output also preserves source order through the composed ARM64 direct backend.

### Offline native runtime

The Eristavi-written offline compiler's boxed native runtime now uses a separate
non-moving typed tracing layer on both supported Linux architectures. It starts
from active value slots/scopes, verified Universal-IR value/failure roots, handlers
and checked-failure state; it traverses Text/Text views, ordinary values, Lists,
maybe/identity, resources and error payloads. Prefix-append indexes are weak
metadata and do not keep otherwise dead backing buffers alive. Identity cycles are
collectable. Deterministic files remain governed by `with`, not GC finalizers.

Collection occurs only at native pointer-ABI safe points. The collector is a
bootstrap production-hardening implementation: stop-the-world and single-runtime,
not generational/concurrent/compacting. The underlying runtime source is still C
and remains a later toolchain-independence boundary.

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

The current suite contains **406 tests**. The hosted CI matrix runs:

- GCC / x86-64 Ubuntu / `-O2`;
- Clang / x86-64 Ubuntu / `-O2`;
- Clang / ARM64 Ubuntu / `-O2`;
- Clang / ARM64 macOS / `-O2`.

The matrix also downloads an immutable-revision copy of the official Unicode 17 `GraphemeBreakTest` fixture and executes all of its vectors. Platform-specific direct-native cases run on their matching Linux architecture. Completed batches select repeated Linux native self-builds and offline application audits through the separate [qualification workflow](CI_QUALIFICATION.md); ordinary CI keeps all four platform test suites.

See [`IMPLEMENTATION_AUDIT.md`](IMPLEMENTATION_AUDIT.md) for the audited boundary and remaining production work.

## Documentation

- [`SEMANTIC_ANALYSIS.md`](SEMANTIC_ANALYSIS.md) — experimental Eristavi-written semantic analyzer
- [`FRONTEND_TOOL.md`](FRONTEND_TOOL.md) — Eristavi-written frontend executable
- [`PRE_0_1_FREEZE.md`](PRE_0_1_FREEZE.md) — frozen source-language/frontend boundary
- [`IMPLEMENTATION_AUDIT.md`](IMPLEMENTATION_AUDIT.md) — current audited implementation status
- [`PRODUCTION_HARDENING.md`](PRODUCTION_HARDENING.md) — production runtime hardening gates
- [`NATIVE_HEAP_GC.md`](NATIVE_HEAP_GC.md) — offline/native heap tracing contract
- [`HEAP_DIAGNOSTICS.md`](HEAP_DIAGNOSTICS.md) — opt-in allocation accounting baseline
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