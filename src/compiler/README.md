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

The Eristavi-written compiler implements parsing, semantic analysis, structural
lowering, verified Universal IR and native x86-64/ARM64 assembly emission. Linux
bundles pass repeated native self-build gates with the bootstrap runtime. The
`--runtime owned` Linux x86-64 build/startup path is being qualified separately;
see `OWNED_BUILD_INTEGRATION.md`. The Python implementation remains the independent
reference/bootstrap, and GNU as/ld remain required native build tools.

Compiler code must stay inside the frozen pre-0.1 language. When the compiler needs a data structure not yet present in the standard library, prefer a simple List/arena implementation first; do not add source syntax merely because another implementation language offers a convenient feature.

The executable entry is `src/frontend.eri`; see [`FRONTEND_TOOL.md`](../../FRONTEND_TOOL.md).

See [`SEMANTIC_ANALYSIS.md`](../../SEMANTIC_ANALYSIS.md) for the candidate boundary.

The structural/native implementation adds ir_types.eri, universal_model.eri,
universal_lower.eri, universal_verify.eri, universal_optimize.eri,
universal_report.eri, ir_x86.eri and ir_arm64.eri. ir_c.eri remains a verified C
consumer, using the pinned runtime/value_runtime.c bootstrap asset through
value_runtime.eri. The offline bundle is built/audited by tools/build_offline.py;
see OFFLINE_TOOLCHAIN.md at the repository root.
