# Eristavi

**A readable, strongly typed programming language with its own compiler architecture, machine-neutral IR, and native code generators.**

> **Complexity belongs in the compiler and runtime, not in the programmer's code.**

Eristavi is a general-purpose programming language designed around a simple idea:

> Programmers should describe the computation clearly; the compiler should handle the machinery required to execute it.

```eri
let price be 120;
let quantity be 3;
let total be price * quantity;

if total > 300 {
    output("Large order");
}

output(total);
```

Eristavi combines a deliberately small and readable source language with strong static semantics, type inference, automatic memory management, deterministic resource handling, and an architecture designed for direct native compilation.

The language is currently **pre-0.1** and under active development.

[About Eristavi](#why-the-project-exists) · [Design Philosophy](DESIGN_PHILOSOPHY.md) · [Language Semantics](LANGUAGE_SEMANTICS.md) · [Compiler Architecture](#compiler-architecture) · [Documentation](#documentation)

---

## Eristavi in a minute

Variables are intentionally simple:

```eri
let age be 44;
let name be "Anna";
```

Types are inferred when the compiler already knows them.

Important contracts remain explicit:

```eri
function double(value Int) returns Int {
    return value * 2;
}
```

Ordinary values can define their structure directly:

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

Failures form part of a function's contract:

```eri
function read(path Text) returns Text fails files.FileError {
    ...
}
```

External resources have deterministic lifetime:

```eri
with file be try files.open(path) {
    return try file.readText();
}
```

Generic relationships can be inferred without introducing separate generic syntax:

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

output(text.characters.count);
output(text.scalars.count);
output(text.bytes.count);
```

Eristavi distinguishes what the programmer means instead of silently guessing.

---

## Why Eristavi?

Programming languages have accumulated decades of useful ideas.

They have also accumulated complexity.

Eristavi asks a different question:

> **Which complexities should still belong to the programmer, and which can reasonably be handled by the compiler?**

The language is designed around several principles.

### Readable, but precise

Eristavi aims to be immediately understandable without trying to imitate unrestricted natural language.

```eri
let total be price * quantity;

if total > 100 {
    output(total);
}
```

Readable syntax must still have deterministic grammar and predictable semantics.

### Strong types without excessive ceremony

The compiler should infer what is obvious.

The programmer should state what is important.

```eri
let quantity be 5;
```

The compiler knows this is an `Int`.

But public contracts can remain explicit:

```eri
function calculate(price Float, quantity Int) returns Float {
    ...
}
```

### One obvious way

Eristavi deliberately avoids accumulating multiple equivalent syntaxes for fundamental concepts.

The goal is not to provide every familiar spelling from every other language.

The goal is to reduce the number of concepts that programmers need to remember.

### Small language, capable libraries

Language syntax should describe program structure and semantics.

Functionality such as files, networking, JSON, databases, time, encoding, and processes generally belongs in types and libraries rather than becoming additional language keywords.

### Automatic memory management

Ordinary application code should not need to manually allocate and release general-purpose memory.

The compiler and runtime should manage memory lifetime while remaining free to optimize values into registers, stacks, or other representations where appropriate.

### Deterministic resources

Memory and external resources are different problems.

Files, sockets, locks, transactions, and operating-system handles require predictable cleanup.

Eristavi therefore makes resource lifetime explicit through scoped constructs such as `with`.

### Native execution matters

Readable source code should not require giving up native execution.

Eristavi is being designed with its own target-independent compiler pipeline and target-specific native code generators.

---

## Compiler architecture

Eristavi is not designed around C as its native execution model.

Its compiler architecture separates source-language semantics from the machine that eventually executes the program.

```text
Eristavi source (.eri)
        │
        ▼
Lexer / Parser
        │
        ▼
Semantic analysis
        │
        ▼
Type and effect inference
        │
        ▼
Typed Eristavi representation
        │
        ▼
Universal IR
        │
        ▼
Verification + optimization
        │
        ├───────────────┬────────────────┐
        ▼               ▼                ▼
   x86-64 backend   ARM64 backend   WebAssembly
        │               │
        ▼               ▼
 native instructions  native instructions
        │               │
        └─────── machine execution ──────┘
```

The source language describes computation.

The target backend describes the machine.

This separation allows new architectures to be added underneath the same Eristavi language model without introducing architecture-specific concepts into ordinary `.eri` source code.

---

## Eristavi owns the compilation model

The long-term Eristavi toolchain is intended to own the path from source semantics to native instructions.

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
machine instructions
```

This is an important part of the project.

Eristavi is not intended to become merely a syntax layer that permanently translates programs into C before another compiler performs the real native compilation.

During the pre-0.1 bootstrap phase, some external infrastructure remains involved in building and packaging the toolchain. Those dependencies are implementation boundaries being progressively reduced rather than part of the language's long-term execution model.

The current x86-64 and ARM64 native backends lower verified Universal IR into target assembly. Direct instruction encoding and deeper ownership of object and executable generation are later steps in the same architecture.

---

## Native targets

### x86-64

The x86-64 backend consumes verified Universal IR and lowers supported Eristavi operations into architecture-specific native instructions.

Current work includes:

- integer and boolean operations;
- floating-point operations;
- functions and recursion;
- control flow;
- ordinary values;
- Lists;
- maybe and identity values;
- checked failures;
- deterministic resources;
- Text support in the existing hosted runtime;
- native memory and runtime independence work.

### ARM64

ARM64 consumes the same Universal IR.

The language semantics are therefore not defined in terms of x86-64 behavior.

Supported language concepts are progressively implemented behind the ARM64 backend while preserving the same source-level contracts.

### Future architectures

The compiler architecture is intended to allow additional native targets without changing the Eristavi source language.

Potential future targets include architectures such as RISC-V.

No target architecture should define Eristavi semantics.

---

## WebAssembly

WebAssembly is a portable execution target rather than a substitute for Eristavi's native compiler architecture.

```text
Eristavi source
      ↓
Universal IR
      ↓
WebAssembly backend
      ↓
WebAssembly
```

This allows Eristavi programs to target environments where portable sandboxed execution is more appropriate than native binaries.

---

## Other output targets

Eristavi may support additional translation or interoperability backends where they are useful.

Those targets are secondary to the core architecture.

The defining compilation model remains:

```text
Eristavi source → Eristavi compiler → Eristavi IR → target backend
```

---

## Current status

Eristavi is currently **pre-0.1** and is not yet recommended for production software.

The source-language/frontend contract has reached a stable implementation phase while the compiler, runtime, and native toolchain continue to mature.

Already implemented or substantially implemented areas include:

- lexer and parser;
- semantic analysis;
- static relationship inference;
- type and effect information;
- typed intermediate representation;
- Universal IR;
- IR verification;
- optimization passes;
- x86-64 backend work;
- ARM64 backend work;
- WebAssembly generation;
- module interfaces and compiled artifacts;
- checked failures;
- deterministic resource handling;
- Unicode Text semantics;
- managed heap and runtime work;
- incremental compilation infrastructure.

The compiler itself increasingly contains components written in Eristavi.

---

## Runtime independence

A major project goal is to remove historical bootstrap dependencies from the normal Eristavi compilation and execution path.

An important milestone has already been reached on Linux x86-64:

> An ordinary `.eri` scalar program can travel through the Eristavi-written frontend and native backend and execute using the new freestanding Eristavi runtime path without linking the previous C application runtime, libc, CRT startup objects, or a dynamic loader.

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

through the freestanding scalar path.

This milestone should be stated precisely:

> **Eristavi has demonstrated a C-free application runtime path for the supported scalar subset.**

It does not yet mean that every part of the compiler toolchain is completely independent of bootstrap infrastructure.

The remaining dependencies are being removed incrementally without changing the public language model simply to make implementation work easier.

See [FREESTANDING_SCALAR_APPLICATION.md](FREESTANDING_SCALAR_APPLICATION.md) and [OFFLINE_TOOLCHAIN.md](OFFLINE_TOOLCHAIN.md).

---

## Building Eristavi with Eristavi

Self-hosting is not being treated as a marketing checkbox.

It is part of the architecture.

Increasing portions of the compiler are implemented in Eristavi, including work covering:

```text
Eristavi source
      ↓
parsing
      ↓
semantic analysis
      ↓
typed IR
      ↓
Universal IR
      ↓
verification
      ↓
optimization
      ↓
native target generation
```

The goal is progressively to reach a toolchain where Eristavi can build Eristavi through machinery owned by the project itself.

The language design is not being changed merely to make self-hosting easier.

Implementation complexity belongs underneath the language.

See [SELF_HOSTING.md](SELF_HOSTING.md).

---

## Language design

### Variables

```eri
let total be 42;
```

### Functions

```eri
function double(value Int) {
    return value * 2;
}

output(double(21));
```

### Values

```eri
type Coordinate {
    x Float;
    y Float;
}

let point be Coordinate {
    x = 10.5;
    y = 20.0;
};
```

### Fixed values

```eri
type Customer {
    fixed id Int;
    name Text;
}
```

`fixed` expresses immutability as part of the value contract.

### Inferred generic relationships

```eri
function first(value) {
    return value;
}

let number be first(10);
let text be first("Hello");
```

The compiler can infer the relationship rather than requiring a separate generic syntax for the common case.

### Checked failures

```eri
function load(path Text) returns Text fails files.FileError {
    ...
}
```

A function that can fail states that contract explicitly.

### Deterministic resources

```eri
import std.files;

function load(path Text) returns Text fails files.FileError {
    with file be try files.open(path) {
        return try file.readText();
    }
}
```

### Unicode Text

```eri
let text be "A\u{301}";

output(text.characters.count); // grapheme clusters
output(text.scalars.count);    // Unicode scalar values
output(text.bytes.count);      // UTF-8 bytes
```

Eristavi does not pretend these concepts are interchangeable.

---

## Quick start

The current developer toolchain still includes bootstrap infrastructure while the independent native toolchain is being completed.

```sh
git clone https://github.com/eristavi/eristavi-lang.git
cd eristavi-lang
python -m pip install -e .
```

Run an Eristavi program:

```sh
erist run examples/hello.eri
```

Example:

```eri
let x be 40;
let y be 2;
output(x + y);
```

Output:

```text
42
```

Check a program without running it:

```sh
erist check examples/hello.eri
```

Generate Universal IR:

```sh
erist uir examples/hello.eri
```

Generate native assembly for a supported target:

```sh
erist build-asm examples/hello.eri -o hello.s --target x86_64-linux
```

Build through the direct native backend:

```sh
erist build-direct examples/hello.eri -o hello --target x86_64-linux
```

---

## Project direction

The project is currently moving toward increasingly complete compiler and runtime independence.

A simplified roadmap is:

```text
Language model
      ✓
Parser / semantic analysis
      ✓
Typed IR / Universal IR
      ✓
Native x86-64 backend
      ✓ / expanding
Native ARM64 backend
      ✓ / expanding
Freestanding memory foundation
      ✓
Freestanding scalar runtime
      ✓
Freestanding Text / managed values
      →
Remaining runtime families
      →
Independent native toolchain
      →
Direct machine-code / executable ownership
      →
0.1
```

The roadmap is intentionally incremental.

A milestone is considered meaningful only when the implementation can preserve the existing language semantics rather than requiring shortcuts in the source language.

---

## Design principles

Eristavi follows a small set of governing ideas.

### Complexity belongs underneath the language

Ordinary programs should not expose compiler or runtime implementation details unnecessarily.

### One obvious way

Fundamental concepts should normally have one preferred representation.

### Infer what is obvious

The compiler should not require programmers to repeat information it can safely prove.

### Require what is important

Public contracts, failures, resource lifetime, and ambiguous operations should remain explicit.

### Libraries before keywords

Capability should normally grow through types and libraries before expanding the language grammar.

### Safe behavior should look ordinary

Potentially dangerous low-level operations should eventually remain available, but they must be visibly explicit.

### Machines do not define the language

x86-64, ARM64, WebAssembly, and future architectures are backend concerns.

Eristavi semantics remain machine-independent.

Read the full charter in [DESIGN_PHILOSOPHY.md](DESIGN_PHILOSOPHY.md).

---

## Why the project exists

Eristavi is also a personal exploration of how programming languages could be designed differently after decades of experience with modern software, compilers, and computer architecture.

The longer story behind the project, its origins, and the thinking that led to its design will be documented separately as **About Eristavi**.

---

## Documentation

### Language

- [Design Philosophy](DESIGN_PHILOSOPHY.md)
- [Language Semantics](LANGUAGE_SEMANTICS.md)
- [Grammar](GRAMMAR.md)
- [Lexical Rules](LEXICAL_RULES.md)
- [Unicode Text Views](TEXT_VIEWS.md)
- [Collections](COLLECTIONS.md)
- [Fixed / Immutability](FIXED_IMMUTABILITY.md)
- [Value Equality](VALUE_EQUALITY.md)
- [Identity Equality](IDENTITY_EQUALITY.md)
- [Checked Failures](ERRORS.md)
- [Resource Cleanup](RESOURCE_CLEANUP.md)
- [Inferred Generic Relationships](GENERICS.md)

### Compiler

- [Semantic Analysis](SEMANTIC_ANALYSIS.md)
- [Frontend Tool](FRONTEND_TOOL.md)
- [Universal IR](UNIVERSAL_IR.md)
- [Module Interfaces](MODULE_INTERFACES.md)
- [Direct Backends](DIRECT_BACKENDS.md)
- [Targets](TARGETS.md)

### Runtime and implementation

- [Self Hosting](SELF_HOSTING.md)
- [Implementation Audit](IMPLEMENTATION_AUDIT.md)
- [Production Hardening](PRODUCTION_HARDENING.md)
- [Native Heap GC](NATIVE_HEAP_GC.md)
- [Heap Diagnostics](HEAP_DIAGNOSTICS.md)
- [Freestanding Scalar Application](FREESTANDING_SCALAR_APPLICATION.md)
- [Offline Toolchain](OFFLINE_TOOLCHAIN.md)

---

## Project identity

- **Language:** Eristavi
- **Source extension:** `.eri`
- **CLI / compiler:** `erist`
- **Official website:** [eristavi.org](https://eristavi.org)
- **Repository:** `eristavi/eristavi-lang`
- **License:** MIT

The `.erist` extension is reserved for a possible distinct future purpose and is not an alternative ordinary source-file extension.

---

## License

Eristavi is released under the **MIT License**.
