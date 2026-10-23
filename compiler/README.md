# Eristavi Compiler

This directory will contain the bootstrap implementation of the `erist` compiler/toolchain.

## Bootstrap language

The first compiler prototype is expected to be written in Python so the language grammar, semantics, diagnostics, and IR can evolve quickly.

The intended long-term goal is self-hosting: once Eristavi is capable enough, a later compiler can be implemented in Eristavi itself.

## Planned frontend pipeline

```text
.eri source
    ↓
lexer
    ↓
parser
    ↓
AST
    ↓
semantic analysis / type inference
    ↓
Eristavi IR
    ↓
target backend
```

Implementation should follow the specifications in the repository root rather than inventing semantics for implementation convenience.

## Bootstrap entry model

An executable run/build selects one `.eri` source file explicitly as the entry module. Eristavi does not require a magic `main` function or `main.eri` filename.

The selected entry file may contain module declarations followed by top-level executable statements. Those executable statements form the implicit entry execution body and run in source order. Imported modules are declaration-only and must not perform hidden top-level initialization.

The first implementation milestone is to parse and evaluate/compile `examples/hello.eri` as an entry source file under the rules in `ENTRYPOINT.md`.
