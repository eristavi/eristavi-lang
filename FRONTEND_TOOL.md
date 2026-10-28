# Eristavi-written frontend executable

The repository now contains a usable **syntax frontend written in Eristavi** at
`src/frontend.eri`. It reads a source file, runs the Eristavi-written lexer/parser,
and checks syntax or writes a machine-readable token/AST report.

The syntax commands do not resolve imports or check types. Experimental semantic
commands now do; `ir` and `emit-c` add an experimental scalar compilation path.
`erist check` remains the Stage-0 semantic checker; `erist-frontend check` checks
syntax only. An unknown function name can therefore pass the frontend and still
be rejected by Stage-0 semantic analysis.

## Build

From the repository root, with the bootstrap dependencies and a C compiler installed:

```sh
python -m pip install -e .
erist build src/frontend.eri --source-root src -o erist-frontend
```

The build uses Python Stage-0 and the portable C backend. Once built, the executable
runs locally without Python, a C compiler, installed Eristavi source modules or
network access. It still uses the host's normal system libraries. This is an
offline frontend executable, not yet a self-building standalone compiler.

## Use

```sh
./erist-frontend check examples/hello.eri
./erist-frontend ast examples/hello.eri
./erist-frontend ast examples/hello.eri --output hello.ast.json
./erist-frontend tokens examples/hello.eri --output hello.tokens.json
./erist-frontend --help
```

Paths may be absolute or relative to the process working directory. Spaces and
Unicode names are passed as ordinary arguments; use normal shell quoting when
needed. Syntax commands pass paths directly to the file boundary. Semantic
commands add canonical root validation and a source module loader.

Successful `check` is silent. Reports go to stdout unless `--output` is specified.
Diagnostics go to stderr. Exit status is **0** for success, **1** for source/I/O
failure, and **2** for incorrect command usage.

The complete source is read and analyzed before a report file is created.
`--output` exclusively creates a new file. Existing files, symlinks and the input
itself are never truncated. Choose a new report name or remove an old report
explicitly before reusing its name. A failed write can leave a partial newly
created report; output is not an atomic-replacement API.

The reference runner can execute the same entry program:

```sh
erist run src/frontend.eri --source-root src -- ast examples/hello.eri
```

Arguments after `--` are forwarded to the Eristavi program unchanged.

## Experimental semantic commands

```sh
./erist-frontend analyze project/src/application.eri --source-root project/src
./erist-frontend analyze-report project/src/application.eri --source-root project/src
```

These commands run the Eristavi-written name/type/safety analyzer and source module
loader. They do not execute the application. The source root defaults to the entry
file's parent. Successful analysis is silent; `analyze-report` emits inferred
function contracts. Semantic commands use `--source-root`, not `--output`.
Stage-0 remains the reference while differential coverage and later IR work continue.
See [`SEMANTIC_ANALYSIS.md`](SEMANTIC_ANALYSIS.md).

## Reports

AST output is an object with `format: "eristavi-ast-v1"`, `syntaxOnly: true`, and
`tree`. Each tree node is an array:

```text
[kind, text, extra, flag, line, column, firstChildren, secondChildren, thirdChildren]
```

Kinds and the contextual `extra`/`flag` fields follow `src/compiler/ast.eri` and
`src/compiler/parser.eri`. Each child group is an ordered array; internal identity
handles and sibling links do not leak into the report. The program node uses the
EOF location. Numeric literals retain validated spelling, Text contains decoded
scalars, and identifiers use pinned Unicode-17 NFC identity.

Token output has `format: "eristavi-tokens-v1"` and `tokens`. Each token is:

```text
[kind, rawLexeme, valueText, line, column]
```

Numeric `valueText` remains validated source spelling for the later typed literal
stage. The report includes EOF. JSON escaping preserves control scalars and
embedded NUL. Report versions are bootstrap inspection contracts, not a frozen
public compiler IR or object ABI.

## Conformance and boundaries

`tests/fixtures/frontend_cases.json` is shared by the Stage-0 parser and the compiled
Eristavi frontend. Tests compare complete AST shapes and source locations for
valid cases, and phase/location for invalid cases. The compiled frontend also
parses every repository `.eri` file under `src/` and compares its AST to Stage-0.
Additional tests cover token payloads, exact UTF-8 I/O, error status, relative and
Unicode paths, report preservation and execution with an empty `PATH`.

The lexer/parser/report formatter and command flow are Eristavi source. The small
`std.process`, `std.unicode`, `files.openRead` and `files.create` runtime boundaries
currently execute in the reference runtime and generated-C route. Direct native,
JavaScript and Wasm support for these new library operations is pending and their
use is rejected explicitly. No language syntax or implicit ownership rules were
added for this phase.

Experimental semantic analysis, source-close typed IR, verification and scalar C
emission are now implemented in Eristavi. See SCALAR_COMPILATION.md for `ir` and
`emit-c`, supported source coverage and build dependencies. Float and inferred scalar specialization are documented in
SCALAR_SPECIALIZATION.md. Broader lowering, Universal IR and native backends remain later stages. Full self-building requires
repeatable compiler builds and equivalent
semantic/conformance results. The final offline native toolchain must also bundle
or implement its assembler/linker functionality before external build tools can
be removed from normal native compilation.

## Native/offline extension

The compiler now also provides `uir` and `emit-asm`, with `--target x86_64-linux`
or `--target arm64-linux` for assembly. Semantic/IR commands accept source-root
flags; native assembly may combine root and target flags. `emit-c` reads the pinned
`runtime/value_runtime.c` bootstrap asset. The packaged wrapper supplies the native
build/check CLI and bundled assembler/linker/runtime. See OFFLINE_TOOLCHAIN.md for
full structural coverage, self-build evidence, commands and limitations. Earlier
sections above describe the original frontend/scalar milestones.

## Opt-in phase tracing

Add `--trace-phases` after the command and source path to write structured progress
to stderr. AST, IR, generated C/assembly and normal stdout remain unchanged.
For example: `erist-frontend emit-asm src/frontend.eri --source-root src --target x86_64-linux --trace-phases`.

Records begin with `[erist-phase] ` followed by JSON containing `event`, `phase`,
and `subject`. Subjects are JSON-quoted, including paths with Unicode or newlines.
Tracing covers input read/lex/parse, module location indexing and analysis,
function analysis and lowering, Universal IR conversion/optimization, native
function/descriptors emission and output. Lowered function subjects include the
`f` index used by the native emitter, allowing the last emitter record to be
matched to its source function. An error preserves the original diagnostic and
exit status; an unmatched `begin` identifies work that did not finish.

The offline `erist` wrapper also forwards `--trace-phases`. Qualification enables
it explicitly and retains raw stderr plus timestamped events. Trace I/O can affect
timings; tracing is diagnostic evidence rather than a performance benchmark.

Typed-IR validation and Universal IR construction have separate nested phase
records; see [TYPED_IR_VERIFICATION.md](TYPED_IR_VERIFICATION.md) for phase names
and the local-table ownership optimization.
