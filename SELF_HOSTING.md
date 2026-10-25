# Eristavi Self-Hosting

> **Status: experimental native self-build/offline bundle gate; Stage-0 retained as reference/bootstrap**

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

### Stage 3 — experimental semantic analysis

Name resolution, source module loading/visibility, type relationships, scopes,
fixed/value/identity semantics, checked failures and resource checks are written in
Eristavi. `analyze` and `analyze-report` expose the candidate without replacing
Stage-0. The shared 175-case corpus compares acceptance and inferred contracts;
location differences are recorded explicitly. The candidate analyzes the frontend's
own module graph offline. Expression type/effect facts are retained for Stage 4.
See [`SEMANTIC_ANALYSIS.md`](SEMANTIC_ANALYSIS.md). Complete equivalence and promotion
require continued differential coverage; this is not full self-building.

### Stage 4 — structural and Universal IR

The Eristavi-written candidate lowers scalars, ordinary values/Lists, maybe/identity,
checked failures, Text views, standard-library boundaries and deterministic cleanup
into independently verified structural IR. It then builds target-independent
register operations/basic blocks, verifies CFG/classes/definite initialization,
and removes unreachable blocks with pre/post verification. See OFFLINE_TOOLCHAIN.md.

### Stage 5 — native consumers

Eristavi-written x86-64 and ARM64 ELF consumers emit instructions from Universal IR.
They currently spill virtual registers and call a prebuilt C bootstrap runtime
through a pointer ABI. Native runtime optimization/register allocation remain
performance work; source semantics do not change to simplify backend code.

### Stage 6 — repeated native self-build and offline packaging

`tools/build_offline.py` builds native compiler B, uses B to build C and uses C to
reproduce the next assembly. It requires identical assembly and B/C binaries for
a fixed source/runtime snapshot. Its default gate also builds/runs applications
with unusable Python/C compiler shims in child PATH. Assemblers/linkers, runtime
objects, startup files, provenance and evidence are packaged for a compatible Linux
host. x86-64 and ARM64 are supported native bundle targets.

The gate is experimental and does not replace the independent Stage-0 reference,
its artifact ABI or its existing JS/Wasm consumers. The runtime remains a C bootstrap
artifact and the bundled assembler/linker are GNU tools. This is not an Eristavi-
written operating-system/runtime/assembler stack or a production release claim.

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
keeps syntax commands independent of import resolution. The semantic commands
now add a source loader and use the required canonical-path library operation.

The compiled C executable is tested with an empty `PATH`; it needs no Python or
C compiler at runtime. Build-time Python/C requirements remain until later
self-hosting stages. The reference and compiled frontends share a corpus covering
accepted syntax, rejected syntax, complete AST structure and locations. Every
repository `.eri` source is also parsed and compared to Stage-0.

The normal compiler still uses Stage-0; experimental Eristavi analysis is available
through the separate semantic commands. See [`FRONTEND_TOOL.md`](FRONTEND_TOOL.md).
The native bundle now includes assembler/linker tooling and a prebuilt bootstrap
runtime. See OFFLINE_TOOLCHAIN.md for the repeatability/offline audit, supported
Linux hosts and remaining production/runtime/portability gates.

## Promotion rule

> **Self-hosting is an implementation milestone, not permission to change Eristavi semantics.**
