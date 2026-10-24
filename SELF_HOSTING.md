# Eristavi Self-Hosting

> **Status: active staged migration; Stage-0 remains the trusted bootstrap**

Eristavi is now developed with an explicit self-hosting plan. The existing Python implementation under `compiler/erist/` is the **Stage-0 bootstrap compiler**. It is deliberately retained until an Eristavi-written compiler can reproduce the frozen language semantics and compile itself.

## Invariants

Self-hosting must not reopen the frozen pre-0.1 source contract merely to make compiler implementation easier.

The migration therefore follows these rules:

- no new source syntax is introduced for compiler convenience;
- the Stage-0 compiler remains the semantic reference during migration;
- Eristavi compiler modules live under `src/compiler/`;
- compiler data structures use ordinary values and Lists, with explicit `identity` handles for shared AST/cursor state;
- no hidden pointer/reference model is introduced;
- every migrated stage receives differential or structural tests against Stage-0;
- a stage is not promoted merely because it parses its own source; semantic equivalence matters;
- Python is removed from the normal compiler path only after a repeatable self-build exists.

## Repository roles

```text
compiler/erist/       Python Stage-0 bootstrap implementation
src/compiler/         Eristavi Stage-1+ compiler implementation
tests/                shared semantic, backend and self-hosting tests
examples/             user-facing Eristavi examples
```

The Python package is intentionally not moved during early self-hosting because its import path is part of the existing test/build infrastructure. Renaming it before the Eristavi frontend reaches parity would add repository churn without reducing bootstrap dependence.

## Self-hosting minimum profile

The first Eristavi-written compiler is intentionally implemented with the already-frozen language surface:

- `Int`, `Bool`, `Float`, `Text`;
- explicit Text scalar/byte views;
- ordinary user-defined values;
- Lists with value semantics;
- functions and inferred relationships;
- checked failures;
- modules/imports;
- deterministic file resources.

Compiler structures use integer kind tags and Lists. Recursive AST links use the existing `maybe identity Node` model explicitly, and parser cursor state uses `identity ParserState`. There are no hidden references, compiler-only pointer rules or new generic syntax. These are implementation choices within the frozen language.

## Stages

### Stage 0 — trusted bootstrap

Python parses, analyses and lowers Eristavi. It already produces native x86-64/ARM64 code through Universal IR and also supports C, JavaScript and WebAssembly consumers.

### Stage 1 — compiler foundations in Eristavi

`src/compiler/` gains source locations, spans, tokens, diagnostics and a lexer. Stage-0 compiles/checks these modules and tests compare their behavior with the frozen lexical contract.

### Stage 2 — parser and explicit identity AST

The parser is written in Eristavi using `maybe identity Node` child/sibling links and explicit identity cursor state. Recursive helpers declare their result contracts. Optional child handles are copied into local bindings before presence checks, using the existing narrowing rules instead of adding mutable-field narrowing for compiler convenience.

### Stage 3 — semantic analysis

Name resolution, type relationships, scope checking, fixed/value/identity semantics and checked failures move to Eristavi. Differential tests compare accepted/rejected programs and diagnostics with Stage-0.

### Stage 4 — IR and verification

Typed IR and Universal IR construction, verification and basic optimization move to Eristavi.

### Stage 5 — native lowering

The x86-64 backend, register allocation/lowering contracts and then ARM64 are moved behind Eristavi-owned IR. Stage-0 remains capable of rebuilding the Stage-1 compiler while this work is in progress.

### Stage 6 — first repeatable self-build

The promotion gate is:

```text
Stage-0 Python compiler
        ↓
Eristavi compiler A
        ↓
Eristavi compiler B
        ↓
Eristavi compiler C
```

B and C must agree under the documented reproducibility policy and pass the same semantic/conformance suites. Only then can the Eristavi-written compiler become the default `erist` implementation.

## Current bootstrap gaps

The current language is sufficient to begin the port, but a production self-hosted compiler will eventually need library/runtime depth in areas such as paths, process arguments/environment and efficient builders. Those are standard-library/runtime tasks; they should not be solved by adding redundant language syntax.

## Verified frontend boundary

The lexer covers Unicode-17 XID identifiers/NFC, scalar escapes, numeric separators,
leading-zero/Float rules, nested comments, BOM placement and source locations.
Numeric token values retain their validated source spelling until the later typed
literal stage; Text values contain decoded scalars. Stage-0 now preserves the raw
Text lexeme as diagnostic metadata too.

Tests compare token kinds, raw lexemes, identifier/Text values and locations, and
compare rejected cases and diagnostic locations. The parser has acceptance,
rejection and expression-tree precedence checks. Both components execute as
compiled C programs as well as under the reference interpreter.

`std.unicode` is a small library boundary, not language syntax. Its C implementation
embeds tables generated from the pinned Unicode 17 dependencies. It does not use
locale, host OS normalization, ICU or a Python process at executable runtime.
Canonical decomposition, canonical ordering, blocked composition and algorithmic
Hangul normalization are checked against the reference Unicode-17 database.

For this migration, use `erist build` for compiler components requiring
`std.unicode`. The direct/JS/Wasm routes do not yet implement this new library and
report that limitation explicitly. This C bootstrap path is an implementation
bridge; Stage-0 is still required to build it, and it is not full self-hosting.

## Executable frontend milestone

`src/frontend.eri` composes the lexer/parser into a command-line program. It reads
UTF-8 through a deterministic read-only resource, checks syntax, and emits
versioned JSON token/AST reports. New report files use exclusive creation so a
source or existing report is not overwritten. Process arguments, stderr and exit
status are standard-library operations; no magic entry function or keywords were
introduced. Relative paths are handled by the existing file boundary; this stage
does not yet resolve imports and does not need speculative path APIs.

The compiled C executable is tested with an empty `PATH`; it needs no Python or
C compiler at runtime. Build-time Python/C requirements remain until later
self-hosting stages. The reference and compiled frontends share a corpus covering
accepted syntax, rejected syntax, complete AST structure and locations. Every
repository `.eri` source is also parsed and compared to Stage-0.

Semantic analysis remains Stage-0. See [`FRONTEND_TOOL.md`](FRONTEND_TOOL.md).
The final standalone offline compiler also needs bundled or Eristavi-owned
assembler/linker functionality; a self-hosted frontend alone does not satisfy that
native-toolchain goal.

## Promotion rule

> **Self-hosting is an implementation milestone, not permission to change Eristavi semantics.**
