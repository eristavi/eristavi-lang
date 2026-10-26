# Eristavi

**A readable, strongly typed general-purpose programming language with its own compiler architecture, machine-neutral IR, and native backends.**

> **Complexity belongs in the compiler and runtime, not in the programmer's code.**

Eristavi is designed around a simple idea: programmers should describe computation clearly, while the compiler handles the machinery required to execute it.

```eri
let price be 120;
let quantity be 3;

let total be price * quantity;

if total > 300 {
    output("Large order");
}

output(total);
```

The language combines readable source code, strong static semantics, type inference, automatic memory management, deterministic resource handling, explicit Unicode behavior, and an architecture intended to reach native machine execution without making ordinary source code look low-level.

Eristavi is currently **pre-0.1** and under active development.

[Design Philosophy](DESIGN_PHILOSOPHY.md) · [Language Semantics](LANGUAGE_SEMANTICS.md) · [Universal IR](UNIVERSAL_IR.md) · [Direct Backends](DIRECT_BACKENDS.md) · [Targets](TARGETS.md)

---

## Why Eristavi?

Programming languages have accumulated decades of powerful ideas. They have also accumulated complexity.

Eristavi asks a simple question:

> **Which complexities should still belong to the programmer, and which can reasonably be handled by the compiler?**

The project follows a few governing principles:

- **Readable, but precise.** Source code should be easy to understand without becoming ambiguous.
- **Strong types without unnecessary ceremony.** Infer what is obvious; require what is important.
- **One obvious way.** Fundamental concepts should not accumulate multiple equivalent forms without a strong reason.
- **Libraries before keywords.** New capability should normally come from types, libraries, runtimes, or backends rather than permanent grammar growth.
- **Automatic memory management.** Ordinary code should not need manual general-purpose memory ownership.
- **Deterministic resources.** Files, sockets, locks, and similar external resources need predictable lifetime.
- **Machine-independent language semantics.** CPU architecture belongs below the source language.
- **Explicit low-level power.** Systems programming should remain possible without forcing low-level complexity into ordinary programs.

The language should remain small enough to understand while the compiler becomes capable enough to carry more of the difficult work underneath it.

---

## Eristavi at a glance

### Variables

```eri
let age be 44;
let name be "Anna";
```

Types are inferred when the compiler already knows them.

### Functions

```eri
function double(value Int) returns Int {
    return value * 2;
}

output(double(21));
```

### Ordinary values

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

### Inferred generic relationships

```eri
function preserve(value) {
    return value;
}

output(preserve(10));
output(preserve("Hello"));
```

The common case does not require separate generic syntax when the relationship can be inferred safely.

### Checked failures

```eri
function read(path Text) returns Text fails files.FileError {
    ...
}
```

Failures remain part of a function's contract.

### Deterministic resources

```eri
import std.files;

function read(path Text) returns Text fails files.FileError {
    with file be try files.open(path) {
        return try file.readText();
    }
}
```

### Explicit Unicode views

```eri
let text be "A\u{301}";

output(text.characters.count); // grapheme clusters
output(text.scalars.count);    // Unicode scalar values
output(text.bytes.count);      // UTF-8 bytes
```

Eristavi does not treat characters, Unicode scalars, and UTF-8 bytes as interchangeable concepts.

---

## Compiler architecture

Eristavi is not designed around C as its native execution model.

The core architecture is:

```text
Eristavi source (.eri)
        ↓
Lexer / Parser
        ↓
Semantic analysis
        ↓
Type and effect inference
        ↓
Typed Eristavi IR
        ↓
Universal IR
        ↓
Verification + optimization
        ↓
Target-specific backend
        ├─→ x86-64
        ├─→ ARM64
        └─→ WebAssembly
```

The source language describes the computation.

The target backend describes the machine.

This separation is intentional: adding a new architecture should not require changing ordinary Eristavi source semantics.

---

## Eristavi Universal IR

Eristavi uses its own machine-neutral lower intermediate representation.

The Universal IR is a target-independent register/control-flow representation with explicit basic blocks, virtual values, terminators, checked-failure state, deterministic cleanup behavior, and enough type information for backends to preserve Eristavi semantics rather than reinterpret them.

Conceptually:

```text
Eristavi source
    ↓
source-close typed IR
    ↓
Universal IR
    ↓
verified target lowering
```

The design uses established compiler techniques such as control-flow graphs, liveness analysis, interference analysis, optimization passes, and register allocation, while the actual Eristavi IR model and semantics are implemented specifically for this project.

See [UNIVERSAL_IR.md](UNIVERSAL_IR.md).

---

## Native compilation

Eristavi owns the language-to-backend compilation model.

The long-term native path is intended to become:

```text
.eri source
    ↓
Eristavi compiler
    ↓
Eristavi IR
    ↓
Universal IR
    ↓
Eristavi target backend
    ↓
Eristavi instruction encoder
    ↓
machine-code bytes
    ↓
object / executable generation
```

Today, the native x86-64 and ARM64 backends already lower verified Universal IR into target assembly. External assembler/linker infrastructure remains a current toolchain boundary while direct instruction encoding and deeper executable ownership remain future steps.

Assembly is therefore an implementation/output layer, not the definition of Eristavi's native architecture.

Historical and bootstrap C paths remain in the repository for reference, qualification, and transition work, but C is **not** the intended long-term native execution model of the language.

---

## Native targets

### x86-64 Linux

The direct x86-64 backend consumes verified Universal IR and supports a broad pre-0.1 language slice including functions, control flow, scalar values, Text, collections, ordinary values, maybe/identity values, checked failures, resources, and module artifacts.

The backend also contains compiler analysis work for liveness, interference, spill-slot management, and physical register allocation.

### ARM64 Linux

ARM64 consumes the same Universal IR rather than a separate language representation.

The backend covers the principal scalar and structured language families and is being brought toward parity with the x86-64 implementation while preserving the same source-level semantics.

### WebAssembly

WebAssembly is treated as a portable execution target, not as a replacement for the native compiler architecture.

```text
Eristavi source
      ↓
Universal IR
      ↓
WebAssembly backend
      ↓
WebAssembly
```

Additional translation or interoperability backends may exist where useful, but they are secondary to the core Eristavi compiler and native backend architecture.

---

## Runtime independence

Compiler and runtime independence are major project goals.

An important Linux x86-64 milestone has already been reached: an ordinary scalar `.eri` application can travel through the Eristavi-written frontend and native lowering path and execute through the freestanding runtime without linking the previous C application runtime, libc, CRT startup objects, or a dynamic loader.

For example:

```eri
let first be 40;
let second be 2;

output(first + second);
output(first < second);
```

produces:

```text
42
false
```

through the current freestanding scalar application path.

This does **not** yet mean that the complete compiler toolchain is fully independent. Bootstrap pieces and external assembler/linker infrastructure still remain at defined boundaries.

Freestanding Text storage, Unicode behavior, managed values, and the remaining runtime families are being migrated incrementally so that implementation work does not weaken the public language contract.

See [FREESTANDING_SCALAR_APPLICATION.md](FREESTANDING_SCALAR_APPLICATION.md), [FREESTANDING_TEXT_STORAGE.md](FREESTANDING_TEXT_STORAGE.md), and [OFFLINE_TOOLCHAIN.md](OFFLINE_TOOLCHAIN.md).

---

## General-purpose by design

Eristavi is intended to remain a general-purpose language rather than a language tied to one application domain.

Its architecture should naturally support work ranging from ordinary applications to systems software as the implementation matures:

- command-line tools;
- servers and networking;
- databases;
- scientific computing;
- graphics and audio;
- AI and machine learning libraries;
- embedded and real-time systems;
- compilers and language tooling;
- operating-system components;
- bare-metal software;
- drivers and hardware-facing code;
- WebAssembly and portable execution environments.

These areas should not require Eristavi to become a different language each time. New domains should normally be enabled through libraries, runtimes, explicit low-level capabilities, and target backends rather than domain-specific keyword growth.

---

## Self-hosting

Eristavi is progressively replacing bootstrap compiler/runtime dependencies with Eristavi-written and native machinery.

`src/compiler/` contains Eristavi-written work covering parsing, semantic analysis, typed IR, Universal IR construction, verification, optimization, and native x86-64 / ARM64 consumers.

The goal is not merely to label the compiler "self-hosted." The goal is to understand and increasingly own the complete path from Eristavi source semantics to native execution.

The public language design is not changed simply to make self-hosting easier.

See [SELF_HOSTING.md](SELF_HOSTING.md) and [OFFLINE_TOOLCHAIN.md](OFFLINE_TOOLCHAIN.md).

---

## Quick start

The current developer CLI still includes Stage-0 bootstrap infrastructure while the independent native toolchain is being completed.

```sh
git clone https://github.com/eristavi/eristavi-lang.git
cd eristavi-lang
python -m pip install -e .
```

Run an Eristavi program:

```sh
erist run examples/hello.eri
```

Check a program without running it:

```sh
erist check examples/hello.eri
```

Inspect Universal IR:

```sh
erist uir examples/hello.eri
```

Generate native target assembly:

```sh
erist build-asm examples/hello.eri -o hello.s --target x86_64-linux
```

Build through the direct native backend:

```sh
erist build-direct examples/hello.eri -o hello --target x86_64-linux
```

Generate WebAssembly text:

```sh
erist build-wat examples/hello.eri -o hello.wat
```

---

## Current status

> **Eristavi is pre-0.1 and is not yet recommended for production software.**

The source-language/frontend contract is frozen for implementation while the compiler, runtime, native backends, and independent toolchain continue to mature.

Current project areas include:

- Eristavi-written lexer, parser, and semantic analysis;
- strong typing and inferred static relationships;
- source-close typed IR;
- Eristavi Universal IR;
- IR verification and optimization;
- x86-64 and ARM64 native backend work;
- checked failures and deterministic resources;
- Unicode Text semantics and explicit Text views;
- managed-memory/runtime work;
- module interfaces and reusable compiled artifacts;
- incremental compilation infrastructure;
- freestanding runtime migration;
- WebAssembly generation.

The repository contains both the current broad bootstrap/reference implementation and the newer Eristavi-written/native migration work. Documentation distinguishes those boundaries explicitly.

---

## Roadmap

A simplified direction toward 0.1 is:

```text
Source-language contract
        ✓

Parser / semantic analysis
        ✓

Typed IR / Universal IR
        ✓

x86-64 native backend
        ✓ / expanding

ARM64 native backend
        ✓ / expanding

Freestanding memory foundation
        ✓

Freestanding scalar application runtime
        ✓

Freestanding Text / Unicode runtime
        →

Remaining managed values and resources
        →

Compiler/runtime bootstrap removal
        →

Direct instruction encoding
        →

Object / executable ownership
        →

Developer tooling and packaging
        →

0.1
```

The roadmap is intentionally incremental. A milestone should preserve the language model rather than require shortcuts in the source language simply to simplify implementation.

---

## Design philosophy

The project is governed by a few durable rules:

> **Infer what is obvious; require what is important.**

> **Do not add a keyword when a type, library, operator, or existing construct can express the concept clearly.**

> **New syntax must reduce complexity, not merely move it.**

> **Complexity belongs in the compiler and runtime, not in the programmer's code.**

Read the full design charter in [DESIGN_PHILOSOPHY.md](DESIGN_PHILOSOPHY.md).

---

## Project identity

- **Language:** Eristavi
- **Primary source extension:** `.eri`
- **Reserved extension:** `.erist`
- **CLI / compiler:** `erist`
- **Official website:** https://eristavi.org
- **Repository:** `eristavi/eristavi-lang`
- **License:** MIT

`.erist` is reserved for a possible distinct future purpose and is not an alternative ordinary source-file extension.

---

## Documentation

### Language

- [DESIGN_PHILOSOPHY.md](DESIGN_PHILOSOPHY.md) — governing design charter
- [LANGUAGE_SEMANTICS.md](LANGUAGE_SEMANTICS.md) — consolidated language semantics
- [GRAMMAR.md](GRAMMAR.md) — surface grammar
- [LEXICAL_RULES.md](LEXICAL_RULES.md) — lexical rules
- [TEXT_VIEWS.md](TEXT_VIEWS.md) — Unicode character/scalar/UTF-8 views
- [COLLECTIONS.md](COLLECTIONS.md) — collections
- [FIXED_IMMUTABILITY.md](FIXED_IMMUTABILITY.md) — `fixed` semantics
- [VALUE_EQUALITY.md](VALUE_EQUALITY.md) — ordinary structural equality
- [IDENTITY_EQUALITY.md](IDENTITY_EQUALITY.md) — identity equality
- [ERRORS.md](ERRORS.md) — checked failures
- [RESOURCE_CLEANUP.md](RESOURCE_CLEANUP.md) — deterministic cleanup
- [GENERICS.md](GENERICS.md) — inferred generic relationships

### Compiler

- [SEMANTIC_ANALYSIS.md](SEMANTIC_ANALYSIS.md) — Eristavi-written semantic analysis
- [FRONTEND_TOOL.md](FRONTEND_TOOL.md) — frontend tool
- [UNIVERSAL_IR.md](UNIVERSAL_IR.md) — target-independent lower IR
- [MODULE_INTERFACES.md](MODULE_INTERFACES.md) — compiled interfaces and objects
- [DIRECT_BACKENDS.md](DIRECT_BACKENDS.md) — native backend status
- [TARGETS.md](TARGETS.md) — target strategy
- [SELF_HOSTING.md](SELF_HOSTING.md) — self-hosting migration

### Runtime and qualification

- [OFFLINE_TOOLCHAIN.md](OFFLINE_TOOLCHAIN.md) — offline/native toolchain boundary
- [FREESTANDING_SCALAR_APPLICATION.md](FREESTANDING_SCALAR_APPLICATION.md) — first freestanding scalar application path
- [FREESTANDING_TEXT_STORAGE.md](FREESTANDING_TEXT_STORAGE.md) — freestanding Text storage work
- [NATIVE_HEAP_GC.md](NATIVE_HEAP_GC.md) — native heap tracing contract
- [PRODUCTION_HARDENING.md](PRODUCTION_HARDENING.md) — hardening and qualification work
- [IMPLEMENTATION_AUDIT.md](IMPLEMENTATION_AUDIT.md) — audited implementation boundary

---

## Testing

The repository uses automated CI across supported host/compiler combinations, including x86-64 and ARM64 Linux and macOS coverage where applicable. Unicode conformance and platform-specific native cases are included in the qualification matrix.

The exact test count changes as the implementation grows, so the CI result is the authoritative current signal rather than a hard-coded README number.

Local reference-suite execution remains available with:

```sh
python -m unittest discover -s tests -v
```

---

## License

Eristavi is released under the **MIT License**.
