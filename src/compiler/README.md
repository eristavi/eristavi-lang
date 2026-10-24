# Eristavi-written compiler

This directory is the staged self-hosted implementation of the Eristavi compiler.

The existing Python implementation in `compiler/erist/` remains Stage-0 until this tree can compile itself and pass the shared conformance suite.

The initial layout is intentionally small:

```text
source.eri       source positions and scalar helpers
span.eri         half-open source spans
token.eri        stable token-kind codes and token values
diagnostic.eri   checked frontend diagnostic values
lexer.eri        Stage-1 lexer
```

Later stages add the flat AST/parser, semantic analysis, IR, verifier/optimizer and native lowerings.

Compiler code must stay inside the frozen pre-0.1 language. When the compiler needs a data structure not yet present in the standard library, prefer a simple List/arena implementation first; do not add source syntax merely because another implementation language offers a convenient feature.
