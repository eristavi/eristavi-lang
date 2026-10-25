# Eristavi-written typed IR and C compilation

> Experimental Stage-4 executable milestone. Stage-0 remains the default compiler.

The Eristavi-written frontend can now analyze a source project, lower its checked
expressions into Eristavi-owned typed IR, independently verify that IR, and emit a
C11 translation unit. The C compiler then produces the application executable.
Application parsing, analysis, IR construction, verification and C emission run
inside the compiled Eristavi program; they do not invoke Python or Stage-0.

This is the first executable slice of the migration, not full source coverage,
Universal IR parity, native backend ownership or self-compilation. The governing
philosophy, grammar and frozen source semantics have not changed.

## Build and use

From the repository root:

```sh
python -m pip install -e .
erist build src/frontend.eri --source-root src -o erist-frontend
./erist-frontend ir examples/scalar_compilation.eri
./erist-frontend emit-c examples/scalar_compilation.eri > application.c
cc -std=c11 -O2 application.c -lm -o application
./application
```

The example prints:

```text
Eristavi compiler milestone
153
true
```

For source imports, provide `--source-root project/src` after the entry filename.
The default root is the entry file's parent. Paths have the same hosted POSIX
boundary as the semantic analyzer. `ir` and `emit-c` write to stdout only;
diagnostics go to stderr and a failed compilation emits no partial report or C.
Shell redirection is performed by the shell before compilation, so a failed command
can still create an empty redirected destination. Choose destinations accordingly.
Neither command runs the application or invokes a system compiler.

Once the frontend is built, `ir` and `emit-c` operate offline with an empty `PATH`.
Compiling the emitted C still requires an external C compiler and linker. Building
the frontend still requires the Python/C Stage-0 bootstrap. A fully independent
offline `erist` compiler remains the end goal, including owned or bundled native
assembler/linker functionality and repeatable self-builds.

## Implemented slice

- Concrete `Int`, `Float`, `Bool`, `Text` and no-value function results.
- Decimal/binary/hexadecimal Int literals and Unicode-17 identifiers.
- Scalar locals, fixed bindings, assignment and lexical block scope.
- Checked signed 64-bit arithmetic, comparisons and Boolean short-circuit logic.
- Text constants, concatenation and exact length-aware equality, including NUL.
- Named functions with inferred scalar specialization, concrete parameter/result
  relationships, recursion, mutual recursion, inferred results and bare/value returns.
- `if`/`else`, `while` and predeclared scalar `output`.
- Source module imports/aliases, shared dependency graphs and public function calls.

Collections, nominal values, maybe/identity, Text views, checked failures, deterministic resources and standard-library calls
are explicitly rejected by lowering when they require code generation. They remain
available in Stage-0 and in the broader semantic analyzer. The compiler does not
silently change their meaning or fall back to Python. Concrete declarations in
reachable source modules must fit the current lowering slice. Inferred generic functions specialize on demand, while unused type/error
declarations do not themselves generate code. Checked-failure declarations still
require a later lowering stage. See SCALAR_SPECIALIZATION.md for the extension.

## Architecture and verification

| Module | Responsibility |
| --- | --- |
| `src/compiler/typed_ir.eri` | Explicit typed expression, statement, local, function and program records |
| `src/compiler/ir_lower.eri` | Consume semantic facts and source-function relationships; assign numeric local/function IDs |
| `src/compiler/ir_verify.eri` | Independent structural, type, scope, fixed, call and return verification |
| `src/compiler/ir_report.eri` | Deterministic `eristavi-typed-ir-v1` JSON inspection |
| `src/compiler/ir_c.eri` | Emit C from verified IR without consulting the source AST |
| `src/compiler/scalar_runtime.eri` | C bootstrap runtime for checked Int and immutable UTF-8 Text |

This is the source-close typed IR layer described by UNIVERSAL_IR.md. Structured
branches/loops preserve evaluation boundaries; lowering into explicit Universal IR
basic blocks remains a separate next stage. There is no optimization pass in this
milestone. The internal numeric tags/report schema are experimental compiler
contracts, not language syntax or a frozen public bytecode/object format.

Node opcodes are block `0`, constant `1`, local read `2`, unary `3`, binary `4`,
call `5`, output `6`, declaration `10`, store `11`, discard `12`, branch `13`,
loop `14`, return `15`. Types reuse semantic tags: Int `1`, Float `2`, Bool `3`, Text `4`,
no-value `5`. Nodes retain source path/line/column. Numeric local and function IDs
are independent of CPU registers and source identifier spellings.

Both report and C emission verify the IR first. The verifier checks owned acyclic
node trees, finite distinct function/local tables, contiguous IDs, parameter
layout, local declaration/use and lexical scope, fixed stores, opcode/type/operand
compatibility, function argument/result contracts, Boolean conditions, unreachable
instructions and complete value-return paths. Invalid IR reports `ir-verify` with
its source location. It does not trust the lowerer merely because analysis passed.

Every emitted operand and argument is materialized in source order; conditional
right operands remain inside short-circuit branches and loop conditions are
reevaluated on each iteration. Generated identifiers use numeric IDs, and every
Text byte uses a three-digit C octal escape. Source names or Text cannot inject C
syntax; UTF-8 and embedded NUL do not depend on the C execution character set.

The bootstrap Text runtime retains concatenation allocations until process exit,
where its registered cleanup releases them, including on runtime faults. Text is
immutable and byte-length-aware. This simple allocation registry is not a tracing
collector or bounded-memory solution for long-running Text-heavy applications.
Production memory management and optimization remain promotion gates; users gain
no allocation/free syntax or manual memory obligations.

## Evidence

`tests/fixtures/scalar_ir_cases.json` freezes 60 executable projects. Generated-C
results match their saved outputs, the Stage-0 interpreter and the Stage-0 C
compiler. Coverage includes recursion, module diamonds, lexical scopes, Unicode,
NUL, evaluation order, short-circuiting and loop-condition side effects.

Ten runtime-fault programs compare exit status/stdout/stderr against Stage-0 while
the new emitted C runs with undefined-behavior sanitization. Twenty-eight malformed
IR programs must be rejected by both the verifier and the C-emission entry point.
Tests also compare interpreted versus compiled execution of the Eristavi-written
lowerer/emitter, deterministic IR/C output, unsupported-feature diagnostics and
semantic rejection without application execution. Existing syntax/semantic suites
continue checking the expanded compiler's own module graph.

The execution-order corpus exposed Stage-0 C operand/argument ordering dependence
on the host compiler. Its binary and multi-argument call emission now uses C11
comma expressions and separately declared temporaries to match the reference
interpreter's evaluation order. Evaluations stay inside their original loop,
short-circuit and checked-handler boundaries. This repairs implementation behavior;
it does not change the language grammar or source contract.

## Next promotion gates

Extend typed lowering beyond the scalar specialization milestone to values/collections,
maybe/identity, checked failures and explicit deterministic cleanup. Lower that IR
to Eristavi-owned Universal IR with independent verification and semantics-preserving
optimization. Then port native consumers, establish repeated compiler A/B/C builds,
and package the offline `erist` toolchain. Stage-0 stays trusted until those gates
are met.
