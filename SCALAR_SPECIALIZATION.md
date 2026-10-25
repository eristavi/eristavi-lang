# Scalar specialization and Float compilation

> Historical scalar-specialization milestone, extended by OFFLINE_TOOLCHAIN.md.

The candidate now compiles concrete `Float` alongside `Int`, `Bool` and `Text`,
and specializes inferred functions for scalar argument types. No generic syntax,
keywords, implicit conversions, ownership rules or source semantics were added.
The locked philosophy and language specifications remain unchanged.

## Use

```sh
erist build src/frontend.eri --source-root src -o erist-frontend
./erist-frontend ir examples/scalar_specialization.eri
./erist-frontend emit-c examples/scalar_specialization.eri > application.c
cc -std=c11 -O2 application.c -lm -o application
./application
```

The example prints `42`, `2.5`, `Eristavi`, and `true`, each on its own line.
`--source-root` and offline execution have the same behavior described in
[SCALAR_COMPILATION.md](SCALAR_COMPILATION.md). Link the generated runtime with
`-lm`, including for programs that do not themselves use Float.

## Inferred relationships become concrete implementations

```eri
function twice(value) { return value + value; }

output(twice(21));
output(twice(1.25));
output(twice("Eri"));
```

The semantic analyzer still determines the inferred relationships and validates
source calls. The lowerer now clones each function's type relationships into a
specialization-local substitution map. It binds the scalar argument kinds,
resolves result/local/expression types and emits an independent concrete IR
function. The original semantic type graph is not rewritten with one caller's
chosen types.

The cache key is the source declaration identity plus the ordered parameter kinds.
Different import aliases for the same source function share its implementations.
Repeated Int calls reuse one implementation; an additional Text call gets another.
Internal report names append numeric type tags such as `app.twice$1` for Int and
`app.twice$2` for Float. These are compiler inspection names, not source syntax.

A pending-work list lowers newly discovered specializations until none remain.
Calls can reuse an already registered function before its body is lowered, allowing
ordinary recursive/mutually recursive calls without recursive expansion in the
compiler. Calls inside generic bodies can discover further specializations.
Concrete non-generic declarations retain eager lowering; unused inferred generic
functions receive no machine implementation until called. Their source bodies are
still analyzed by the semantic phase. Checked-failure declarations remain outside
this executable slice, even when unused.

Every specialization passes the existing independent IR verifier, which checks
concrete local/argument/result types, fixed stores, scopes and complete returns.
A mixed Int/Float call is not silently converted; incompatible relationships fail
semantic checking. Generic syntax and semantics remain those of GENERICS.md.
Collections, nominal values, maybe/identity and resource/error lowering remain
future work. The generic forms accepted are those already accepted by the semantic
analyzer; this phase does not broaden its inference rules.

## Float boundary

`Float` is binary64, using the existing semantic type tag `2`. The candidate now
lowers Float literals, variables, parameters/results, unary negation, arithmetic,
comparison, equality and output. `%` continues to require Int.

The IR stores a Float literal's validated source spelling in its Text payload;
its integer payload is unused. The verifier independently requires exactly one
Float token with no surrounding whitespace/comments or additional tokens. The
emitter removes validated numeric separators and emits a quoted numeric string.
The C bootstrap runtime converts that string with `strtod` under the C locale and
`FE_TONEAREST`. Generated programs do not call `setlocale`; C programs start in
the C locale. Overflow yields infinity; underflow preserves gradual subnormal
behavior. Runtime literal conversion is an explicit bootstrap implementation
boundary, not an Eristavi parsing API or a self-hosted binary64 constant evaluator.

The generated runtime requires a binary64 `double`, radix two, gradual underflow
and no excess expression precision. Startup establishes round-to-nearest. Each
arithmetic helper stores its result through a volatile binary64 object, preserving
operation boundaries and preventing contraction into fused multiply-add. Signed
zero, IEEE infinity and unordered NaN comparisons follow FLOAT.md. Unsafe
`-ffast-math` builds are rejected explicitly instead of changing source behavior.
Float output uses the existing Stage-0 C route's 17-significant-digit formatting;
this phase does not unify that route with the interpreter's Python formatting.

The emitted backend retains the previous simple Text allocation registry. Full
runtime memory management, Universal IR construction/optimization, native lowering,
repeatable compiler self-build and independent offline packaging are still pending.

## Evidence and bootstrap corrections

The saved executable corpus now contains 60 projects: the original 32 plus 14
inferred-function and 14 Float projects. They compare saved outputs with the
Eristavi-written compiler, reference interpreter and Stage-0 C compiler. Cases
cover scalar type combinations, nested/imported/recursive generic calls, cached
implementations, signed zero, NaN, literal and arithmetic overflow/underflow,
subnormals, decimal ties-to-even and separated multiply/add operations.

Additional tests inspect specialization IDs/types and deterministic output, reject
incompatible generic relationships and mixed numeric operations, compare interpreted
and compiled execution of the lowerer/emitter, reject fast-math, and establish
rounding even when the launcher first selects a different rounding mode. The
non-contraction/rounding test runs emitted code at `-O0` and at `-O3` with
`-ffp-contract=fast`. The independent verifier and emitter now reject 28 malformed
IR projects, including Float payload injection and Float remainder.

The corpus exposed two existing Stage-0 C defects under the locked Float rules:
positive/negative infinity literals now emit valid C macros, and infinity divided
by signed zero obtains its result sign from operand signs without multiplying
infinity by zero. Both corrections are implementation fixes, not source changes.
The ten sanitized Int-fault comparisons and the broader regression suite continue
to run unchanged.
