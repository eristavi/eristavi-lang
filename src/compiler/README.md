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
semantic_model.eri   explicit identity semantic state
semantic_types.eri   unification and inferred relationships
semantic.eri         name/type/safety analysis
semantic_project.eri source module graph and root validation
semantic_report.eri  inferred contract inspection
typed_ir.eri         source-close typed IR records
ir_lower.eri         semantic facts and inferred scalar specializations to typed IR
ir_verify.eri        independent structural/type/scope verification
ir_report.eri        deterministic IR JSON inspection
ir_c.eri             verified IR to C11
scalar_runtime.eri   bootstrap C runtime with checked Int, binary64 and Text
```

Experimental semantic analysis, scalar typed IR, verification and C emission are available through the executable. Later stages extend typed lowering, Universal IR, optimization and native backends. See SCALAR_COMPILATION.md at the repository root. The lexer/parser execute under Stage-0 and as generated-C executables; they do not yet form a self-hosted compiler. `std.unicode` currently requires the reference or C route.

Compiler code must stay inside the frozen pre-0.1 language. When the compiler needs a data structure not yet present in the standard library, prefer a simple List/arena implementation first; do not add source syntax merely because another implementation language offers a convenient feature.

The executable entry is `src/frontend.eri`; see [`FRONTEND_TOOL.md`](../../FRONTEND_TOOL.md).

See [`SEMANTIC_ANALYSIS.md`](../../SEMANTIC_ANALYSIS.md) for the candidate boundary.
