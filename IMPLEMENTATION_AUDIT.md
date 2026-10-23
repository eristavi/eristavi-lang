# Eristavi pre-0.1 Implementation Audit

> **Audit date: 2026-10-23**
>
> **Scope:** frozen pre-0.1 language contract versus the current Python bootstrap compiler, AST execution runtime, project loader, typed Eristavi IR, and first C/native backend.

## 1. Executive result

The project has moved beyond a lexer/parser proof of concept into a broad executable implementation of the frozen language model.

At this audit point:

- the Python sources compile successfully with `compileall`;
- the complete local suite contains **80 passing tests**;
- the canonical hello program runs through the AST bootstrap runtime and produces `42`;
- the same scalar program lowers through typed Eristavi IR, emits C, compiles with the system C compiler, and produces `42` as a native executable;
- the broad bootstrap runtime implements the principal pre-0.1 slices through modules/imports;
- the first typed IR/C backend is intentionally narrower and is not yet feature-parity with the frontend/runtime.

The source-language freeze remains valid. The implementation work completed here did not require adding alternate syntax or reopening the major semantic decisions.

## 2. Frontend and runtime coverage

### Lexer — implemented

Implemented behavior includes:

- exact frozen keyword vocabulary;
- SPACE/TAB/LF/CR whitespace model and BOM handling;
- Unicode identifiers with NFC normalization using the host Unicode tables;
- `//` comments and nested `/* ... */` comments;
- decimal/binary/hex Int literals;
- decimal Float literals and exponent syntax;
- locked Text escapes and Unicode scalar escapes;
- frozen punctuation/operator tokenization and longest-token recognition.

### Parser / AST — broadly implemented

The parser represents and accepts the frozen forms needed for:

- imports and public/module declarations;
- variable declarations and writable assignment paths;
- functions, parameters, returns and `fails` clauses;
- types, errors and named-field construction;
- `if`, `while`, `for`, `with` and blocks;
- Lists, calls, member/index access;
- `identity`, `try`, `fail` and `else error` handlers;
- `maybe`/`none` type/value syntax.

The construction-versus-block ambiguity is resolved using known type/module information without changing source syntax.

### Semantic analysis / inference — broadly implemented

Implemented checks include:

- declaration-before-use, lexical scope, no local shadowing and module declaration ordering;
- primitive and composite type relationships;
- checked Int/Float separation and Int-only `%`;
- Bool-only conditions;
- function arity/argument checks, inferred/explicit results, no-value use rules, recursion and completion analysis;
- compiler-inferred generic parameter relationships with symbolic body constraints and per-call specialization;
- List element inference, unresolved/conflicting empty List diagnostics, checked indexes, fixed mutation rules and equality;
- ordinary user-value construction, field mutability, structural equality and deep-fixable analysis;
- maybe presence requirements and common flow-narrowing cases;
- identity creation/equality and value/identity separation;
- checked error contracts, local exhaustive handling and propagation;
- deterministic resource ownership constraints and cleanup-error contract checking;
- project/module imports, aliases, public/private access, circular dependencies and declaration-only reusable modules.

### AST execution runtime — broadly implemented

The bootstrap runtime executes the corresponding source features, including value-copy semantics, identity alias semantics, stable List iteration, checked failures and handlers, and `std.files` resource cleanup. Checked cleanup failures preserve an already-active body failure as primary and attach cleanup failures as secondary diagnostic context.

## 3. Module and project implementation

`project.py` provides source-root-relative module loading. It:

- maps dotted imports to `.eri` files;
- compiles imports recursively;
- detects circular imports;
- enforces declaration-only imported modules;
- exposes only public declarations to importing modules;
- supports aliases;
- carries imported type/error/function information into semantic analysis and runtime execution.

This is sufficient for bootstrap project work. Serialized module metadata, package resolution, versioning and registry behavior remain intentionally beyond pre-0.1.

## 4. Generic inference implementation

Untyped function parameters are no longer rejected wholesale. The bootstrap now supports useful inferred relationships such as:

```eri
function identity(value) {
    return value;
}
```

and List-element relationships such as a generic first-element function.

The compiler symbolically checks generic bodies, records operation constraints, and specializes relationships at concrete calls. It rejects incompatible specializations rather than falling back to dynamic typing.

This is an implementation of the frozen inferred-generic philosophy, not a complete future constraint/type-system engine. More stress testing is required as the standard library grows.

## 5. Typed Eristavi IR — first implementation

`ir.py` introduces a typed, machine-independent structured IR with:

- typed constants and variables;
- unary/binary expressions;
- named calls;
- bindings and assignment;
- conditional and loop nodes;
- returns;
- function and entry bodies.

This establishes the required source → semantic analysis → Eristavi IR boundary.

The current IR is deliberately source-close. It is not yet the final universal low-level instruction set. Future work may introduce explicit basic blocks, control-flow edges, ownership/value operations, checked-failure edges, runtime intrinsics and backend-oriented lowering passes while keeping the source semantics unchanged.

## 6. C/native backend — working first slice

The first backend emits C11 from typed IR and can produce a native executable through the system C compiler.

The supported compiled subset includes:

- `Int`, `Float`, `Bool`, and literal Text values;
- checked signed-64-bit Int arithmetic;
- Int division/remainder faults and overflow checks;
- scalar comparisons including content-based Text equality;
- Bool logic;
- local variables and direct assignment;
- `if` / `else` and `while`;
- concrete functions, calls, returns and recursion;
- scalar `output`;
- Unicode source identifiers through ASCII-safe C name mangling.

Generated Text literals preserve escapes correctly. Native backend tests compile and execute generated programs rather than checking emitted source only.

`erist build` currently means Eristavi IR → generated C → system C compiler. A direct machine-code backend remains future architecture work.

## 7. Confirmed remaining implementation gaps

The following are **implementation gaps**, not reopened language-design questions.

### A. Explicit Unicode Text views

The frozen language distinguishes:

```eri
text.characters
text.scalars
text.bytes
```

and their indexing/count operations. The current frontend/runtime does not yet implement these views.

Additionally, the specification names the semantic views but does not currently expose dedicated programmer-visible `Character`, `Scalar`, or `Byte` source types. Before implementing indexed results, the existing specifications should be checked for enough type-level precision; implementation must not invent new public type names silently.

### B. Unicode version pinning

The lexical implementation currently uses the host Python Unicode tables for identifier classification/NFC behavior. The language direction requires a toolchain-pinned Unicode version. A reproducible Unicode data strategy is still required.

### C. Full typed-IR/backend parity

The AST frontend/runtime supports substantially more than the first IR/C backend. IR/backend lowering is still required for:

- Lists and stable iteration;
- user-defined values and nested mutation;
- maybe/none;
- checked errors, handlers and propagation;
- identities;
- deterministic resources/cleanup;
- imported modules;
- inferred-generic specializations;
- Text concatenation and richer Text operations.

The C backend correctly rejects unsupported lowering instead of silently changing semantics.

### D. Float conformance hardening

The C runtime sets round-to-nearest and uses explicit helper calls/volatile results to avoid obvious contraction/excess-precision drift, but full cross-platform proof of the frozen binary64 contract still requires conformance testing for:

- subnormal/FTZ behavior;
- NaN behavior/canonicalization expectations;
- signed zero;
- compiler optimization modes;
- target-specific floating-point environment behavior.

The backend must not claim full deterministic Float conformance until these tests exist across target toolchains.

### E. Direct native backend

No direct ARM64/x86-64/RISC-V machine-code backend exists yet. The current native path is intentionally via C. The first direct CPU backend and exact low-level Eristavi IR remain architectural work.

### F. Serialized module interfaces

Imported modules currently share in-memory semantic metadata in the Python bootstrap. A production compiler will need stable compiled module/interface metadata so importers can type-check without relying on another module's live analyzer object.

### G. Standard library breadth

Only the bootstrap pieces required for current tests exist, notably `output` and a small `std.files` model. JSON, networking, time, processes, richer Text operations and similar library domains remain future library implementation work rather than grammar work.

## 8. Deliberately postponed items — not defects

The audit does **not** classify the following as implementation defects because the frozen roadmap deliberately postpones them:

- explicit generic syntax and generic constraints;
- traits/interfaces for generic bounds;
- pattern matching;
- async/await and advanced concurrency;
- reflection/macros;
- identity-to-value snapshot API;
- advanced resource transfer/borrowing/lifetime syntax;
- third-party package registry/version/lockfile design;
- advanced garbage collectors;
- stable portable bytecode/JIT;
- self-hosting;
- multiple direct native CPU backends.

## 9. Quality findings

During this implementation pass, several issues were caught before the audit was closed:

- function parameters were corrected to be mutable local values rather than implicitly fixed;
- generated C newline escaping was corrected so output emits real line breaks rather than literal `\\n` text;
- C Text equality was corrected to content comparison instead of pointer comparison;
- Unicode Eristavi identifiers are mangled to portable ASCII C identifiers;
- ordered comparison on `Text` was removed from the bootstrap semantic checker because the frozen specifications define Text equality but do not define a Text ordering relation.

These corrections reinforce the rule that target behavior must follow Eristavi semantics rather than host-language accidents.

## 10. Test status

Audit command:

```text
python -m compileall -q compiler tests
python -m unittest discover -s tests -v
```

Result at audit close:

```text
80 tests passed
```

The suite includes negative semantic tests as well as executable behavior and native compiled-backend tests.

## 11. Audit conclusion

The planned implementation sequence through Lists, user-defined values, maybe, checked errors, identity, resources, modules, inferred generic relationships, and a first typed-IR/native compilation path has been completed for the bootstrap milestone.

The project is **not yet a feature-complete pre-0.1 native compiler**. The broad source frontend/runtime is substantially implemented, while the typed IR/backend still needs feature parity and the explicit Unicode Text-view gap remains.

The correct next engineering phase is no longer broad language design. It is:

1. close the audited frontend gaps without changing the frozen surface;
2. extend typed IR to represent the remaining already-implemented semantic features;
3. bring the C/native path to frontend parity with cross-backend conformance tests;
4. harden Unicode/Float reproducibility;
5. only then choose and implement the first direct native CPU backend.

> **Audit verdict:** the frozen design survived implementation, the bootstrap frontend/runtime is broadly functional, and the compiler architecture now has a real IR/backend boundary. Remaining work is principally implementation depth and backend parity, not a need to redesign the language.
