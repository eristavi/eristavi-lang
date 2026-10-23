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

No compiler code is intentionally committed yet. The first implementation milestone is to parse and evaluate/compile the bootstrap example in `examples/hello.eri`.
