# Eristavi-written compiler

This directory is the staged self-hosted implementation of the Eristavi compiler.

The existing Python implementation in `compiler/erist/` remains Stage-0 until this tree can compile itself and pass the shared conformance suite.

The initial layout is intentionally small:

```text
source.eri       source positions and scalar helpers
span.eri         half-open source spans
token.eri        stable token-kind codes and token values
diagnostic.eri   checked frontend diagnostic values
lexer.eri        Unicode-aware Stage-1 lexer
ast.eri          explicit identity AST and node chains
parser_state.eri explicit identity parser cursor
parser.eri       Stage-2 recursive-descent parser
format.eri       integer/Bool/JSON Text formatting
report.eri       versioned token/AST reports
```

Later stages add semantic analysis, IR, verifier/optimizer and native lowerings. The lexer/parser execute under Stage-0 and as generated-C executables; they do not yet form a self-hosted compiler. `std.unicode` currently requires the reference or C route.

Compiler code must stay inside the frozen pre-0.1 language. When the compiler needs a data structure not yet present in the standard library, prefer a simple List/arena implementation first; do not add source syntax merely because another implementation language offers a convenient feature.

The executable entry is `src/frontend.eri`; see [`FRONTEND_TOOL.md`](../../FRONTEND_TOOL.md).
