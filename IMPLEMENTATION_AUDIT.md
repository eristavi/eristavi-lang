# Eristavi pre-0.1 Implementation Audit

> **Audit date: 2026-10-24**
>
> **Scope:** frozen pre-0.1 source contract versus the Python bootstrap/reference runtime, serialized module artifacts, typed IR, generated-C backend, Universal IR, direct x86-64 backend, ARM64 backend, Unicode/runtime behavior and multi-toolchain CI.

## 1. Executive result

Eristavi is now a **broad working pre-0.1 bootstrap compiler with an independent direct-native architecture**, not merely a parser/interpreter or a C transpilation experiment.

At this audit point:

- the source-language/frontend contract remains frozen;
- no fundamental language semantic had to be reopened during this implementation phase;
- the Python bootstrap/reference runtime covers the principal frozen pre-0.1 language surface;
- the generated-C backend remains the broad portable compiled baseline;
- Universal IR now represents functions, Float/Text, aggregates, Lists, maybe, identity, checked failures and deterministic resources in addition to primitive control flow;
- the direct x86-64 Linux backend executes a substantial pre-0.1 subset without generated C;
- versioned module **interfaces and concrete implementation objects** permit source-independent type checking and direct executable linkage for supported concrete implementations;
- an ARM64/AAPCS64 backend consumes the same Universal IR and cross-assembles successfully;
- the verified suite contains **216 tests** and passes in all three CI jobs: GCC/Ubuntu, Clang/Ubuntu and Clang/macOS at `-O2`;
- direct ARM64 native execution remains skipped unless an ARM64 Linux host is available; AArch64 assembly is nevertheless validated by cross-assembly in CI.

The governing target rule remains intact:

> **Target platforms implement Eristavi semantics; they do not redefine them.**

## 2. Current architecture

```text
Eristavi source
    ↓
lexer / parser / AST
    ↓
name resolution + semantic analysis + type inference
    ↓                         ↘
bootstrap/reference runtime   typed/source-close Eristavi IR
                                  ├─→ C11 backend → C compiler → native executable
                                  ↓
                               Universal IR
                                  ├─→ x86-64 Linux backend → assembly → native executable
                                  └─→ ARM64 Linux backend → assembly
```

Module compilation now also has a source-independent artifact boundary:

```text
module.eri
  ├─→ module.eri-interface.json   public semantic contract
  └─→ module.eri-object.json      concrete Universal-IR implementation
```

This is an important architectural change: generated C is no longer the only executable proof, and live Python analyzer objects are no longer the only reusable module boundary.

## 3. Frozen frontend/reference implementation

The frontend/reference runtime continues to cover the principal frozen language surface, including:

- the exact lexical/keyword contract;
- Unicode 17 XID identifiers and NFC identity;
- checked signed-64-bit Int;
- IEEE binary64-oriented Float;
- length-aware Unicode Text;
- explicit Text character/scalar/byte views;
- `let`, transitive `fixed`, annotations and lexical no-shadowing;
- Bool-only conditions, `if / else`, `while`, stable `for`;
- functions, recursion and return inference;
- compiler-inferred generic relationships;
- Lists with ordinary value semantics;
- named-field user-defined values and structural equality;
- maybe/none and flow narrowing;
- explicit managed identity;
- checked errors and propagation;
- deterministic `with` resources;
- modules/imports/aliases/visibility.

This phase did not add source keywords, generic syntax, borrowing syntax, exception syntax or manual memory-management syntax.

## 4. Unicode and Text

### Pinned semantics

Identifier normalization/classification and grapheme behavior remain pinned to Unicode **17.0.0** rather than the host Python or OS Unicode database.

### Generated-C path

The broad generated-C runtime executes all frozen explicit Text views:

```eri
text.bytes
text.scalars
text.characters
```

The character view uses generated Unicode-property tables and a pinned extended-grapheme implementation rather than libc locale APIs or code-point approximation.

Compiled Text remains explicit UTF-8 bytes plus length. Embedded NUL therefore survives output, equality, concatenation and file round trips, and invalid UTF-8 read from a file remains a checked `FileError`.

### Direct x86-64 path

The direct backend now implements length-aware Text values, concatenation, exact equality, function transfer, output and UTF-8 file boundaries. It also preserves mixed scalar/Text output order despite using both stdio and exact-length raw writes.

The explicit direct Text-view operations `.bytes`, `.scalars`, and `.characters` are **not yet implemented through Universal IR/direct x86-64**. This is a direct-backend parity gap, not a source-semantic gap.

### Unicode test boundary

The compiled grapheme implementation has representative/corpus parity tests against the pinned bootstrap segmentation, but this audit does not claim exhaustive execution of the complete official Unicode GraphemeBreakTest corpus. Adding the complete pinned official vectors remains desirable production conformance work.

## 5. Universal IR

Universal IR has grown from a scalar experiment into a meaningful machine-independent execution representation.

It now makes explicit:

- typed virtual values and local slots;
- basic blocks and branch/jump/return terminators;
- functions, parameters, calls, returns and recursion;
- Int, Bool, Float and Text;
- checked Int arithmetic;
- Float arithmetic/comparisons;
- Text concatenation/equality/output;
- short-circuit Boolean CFG;
- nominal type layouts and field access/mutation;
- List construction/count/index/set/add and stable iteration;
- maybe values;
- identity handles;
- explicit ordinary-value cloning;
- structural equality versus identity equality;
- checked-error state, matching, handler dispatch and propagation;
- deterministic resource cleanup;
- std.files open/read/write/exists/remove runtime operations.

### Value/identity semantics below the frontend

Ordinary composite transfers emit explicit clone operations. This includes assignment, parameter passing, return transfer and stable iteration where required. The direct backend therefore receives the fact that ordinary values are logically independent.

Identity handles are not deep-cloned on transfer and preserve shared logical identity.

Tests directly exercise nested value copies, Lists of values, parameter isolation and identity aliasing. This is stronger evidence than relying only on frontend interpretation.

## 6. Direct x86-64 Linux backend

The x86-64 System V backend now executes the following without generated C:

### Functions and ABI

- module-level functions;
- recursion;
- no-value and value-returning functions;
- integer/pointer arguments in System V general registers;
- Float arguments/returns in XMM registers;
- stack-passed arguments beyond register capacity;
- nested checked arithmetic faults that terminate rather than becoming ordinary return values.

Tests include recursive factorial and an eight-argument function.

### Scalars and Text

- Int/Bool/Float;
- checked Int arithmetic/division/remainder;
- IEEE-oriented Float arithmetic/comparison behavior for the tested subset;
- length-aware Text constants, equality, concatenation and output;
- embedded NUL Text.

### Aggregates and identity

- ordinary nominal values;
- nested field mutation;
- recursive deep copying where required;
- structural equality;
- Lists, mutation, checked indexing, `.count`, `.add`, equality and stable iteration;
- maybe/none;
- identity aliasing and identity equality.

### Inferred generics

Source builds monomorphize inferred generic relationships through the direct backend. Tests cover:

- one-value identity-style relationship across Int/Text/Float;
- same-type multi-parameter relationships;
- inferred List element relationships.

### Checked errors

Checked failures are represented below the frontend using explicit Universal-IR state/CFG operations rather than target exceptions.

Direct tests cover:

- catch-all handler message access;
- typed error fields;
- typed handler selection;
- `try` propagation through multiple functions;
- success bypassing handlers;
- cleared failure state not leaking into subsequent calls;
- a handler producing and propagating a new failure.

### Deterministic resources

The direct runtime now implements the current `std.files` surface:

- `files.open`;
- `File.readText()`;
- `File.writeText()`;
- `files.exists()`;
- `files.remove()`;
- deterministic cleanup from `with`.

Direct tests cover:

- cleanup on return;
- nested resource cleanup;
- exact Text I/O including embedded NUL;
- invalid UTF-8 as checked `FileError`;
- missing paths;
- embedded-NUL paths;
- `exists/remove` behavior;
- body failure remaining primary through cleanup.

The direct runtime retains cleanup failures that occur during active checked-failure unwinding as secondary runtime failure context instead of replacing the primary failure. Source-visible programmatic inspection of that secondary context remains intentionally outside pre-0.1.

## 7. Direct-memory-management audit

The direct heap representation is currently **correctness-first bootstrap infrastructure**, not the final automatic-memory-management implementation.

Lists, nominal values, maybe wrappers, identities, Text concatenation and some runtime records allocate heap storage. Ordinary value semantics are implemented through explicit deep-clone helpers where required.

However, the direct runtime currently does **not reclaim all ordinary heap allocations with a production precise GC**. Many allocations are process-lifetime bootstrap allocations.

This is now one of the most important remaining runtime tasks because automatic memory management is a language-level design commitment. Before a production pre-0.1 direct runtime is considered complete, the direct backend/runtime must introduce precise root metadata and collection/reclamation while preserving identity and deterministic non-memory resources.

This limitation does not affect the language's source semantics, but it does affect long-running direct-runtime production readiness.

## 8. Module interfaces and objects

### Interface artifact

The public contract remains:

```text
schema  = eristavi.module-interface
version = 1
```

It preserves public types/errors/functions, dependency identities, pinned Unicode version, checked `fails` contracts and inferred generic relationships.

Importers can type-check from the interface after dependency source removal.

### Implementation artifact

Concrete implementations now use:

```text
schema  = eristavi.module-object
version = 2
IR      = universal-ir-v2
```

The object serializes concrete Universal-IR functions and relevant nominal/error layouts and embeds the exact interface digest against which it was compiled.

The linker rejects interface/object digest mismatches.

### Source-independent executable linkage

Direct tests now compile a module interface/object pair, delete the dependency `.eri` source, and successfully build/run the importing application.

Coverage includes:

- scalar function linkage;
- nominal parameters/returns;
- List returns;
- checked-error contracts and typed handlers;
- imported nominal field-layout consistency.

### Remaining generic object boundary

The interface can describe inferred generic contracts and source builds can monomorphize inferred generics. A precompiled object does **not yet carry a reusable generic implementation template** that can be specialized for arbitrary future call-site types after source removal.

This is a concrete object-format/link-time specialization task, not a reason to add explicit generic syntax.

## 9. ARM64 backend

A second CPU backend now consumes the same Universal IR for the current scalar/function slice.

The AArch64/AAPCS64 implementation covers:

- Int/Bool/Float values;
- functions/calls/recursion;
- register and stack argument placement;
- checked Int arithmetic/division/remainder;
- comparisons and control flow;
- scalar output.

CI cross-assembles generated AArch64 assembly with Clang's AArch64 target. This provides concrete evidence that the lower IR is not structurally coupled to x86-64.

A native ARM64 execution test exists but is skipped on the current non-ARM hosted runners.

ARM64 does **not** yet have parity for Text runtime values, Lists/nominal values, maybe/identity, checked-error runtime state or deterministic resources.

## 10. Generated-C backend

The generated-C route remains the broad portable backend. It covers the principal implemented pre-0.1 surface, including:

- scalar types and checked Int behavior;
- length-aware Text and all explicit Unicode Text views;
- functions/recursion/control flow;
- Lists and ordinary values;
- maybe and identity;
- checked errors;
- inferred generic specializations;
- source modules;
- deterministic resources;
- exact Text file I/O;
- checked file existence/removal.

The C backend remains important for portability and semantic cross-checking even as direct backends mature.

Generated-C executable linkage still relies on implementation source rather than the new Universal-IR object linker. That is an implementation-path difference, not a semantic difference.

## 11. Float conformance

The generated-C conformance suite continues to exercise:

- NaN equality behavior;
- positive/negative infinity;
- signed zero;
- smallest subnormal preservation;
- overflow to infinity.

The direct x86-64 path now also executes Float functions/arithmetic/comparisons, including a NaN-equality case used in direct tests.

The current matrix does not constitute exhaustive proof across all CPUs, compiler optimization modes and floating-point environments. Native ARM64 Float execution, Windows/MSVC and future RISC-V remain additional conformance work.

## 12. Test and CI result

The verified suite contains:

```text
216 tests
```

The final tested code boundary passes in all three GitHub Actions jobs:

- GCC on Ubuntu, `-O2`;
- Clang on Ubuntu, `-O2`;
- Clang on macOS, `-O2`.

The Ubuntu run reports:

```text
Ran 216 tests
OK (skipped=1)
```

The skipped test is native ARM64 execution on a non-ARM host. Direct x86-64 executable tests run on Linux. ARM64 assembly generation is cross-assembled in CI.

Coverage now includes:

- frontend/reference semantics;
- generated-C native execution;
- pinned Unicode and grapheme behavior;
- interface serialization and source-independent type checking;
- object serialization, digest integrity and source-independent direct linking;
- direct x86-64 function ABI/recursion;
- Float/Text direct execution;
- deep values, Lists, maybe and identity;
- inferred generic direct specializations;
- checked-error direct execution;
- deterministic direct resources and UTF-8 file boundaries;
- ARM64 shared-IR emission/cross-assembly.

## 13. Quality findings from this phase

Implementation exposed several issues that were corrected rather than documented away:

- arithmetic faults inside nested direct functions originally risked behaving like ordinary function returns; they now terminate through the runtime fault path;
- interface analyzer proxies initially lost whether a parameter was explicitly declared, which affected object symbol selection; declared-parameter metadata is now preserved;
- early object linkage used fake source stubs; concrete object contracts/layouts are now injected directly into Universal lowering;
- catch-all error handlers initially cleared the active failure before preserving the handler-visible error view; captured error views are now stable;
- fully terminating handled-return CFGs initially left an artificial merge block that appeared to fall through; unreachable merge blocks are removed;
- resource-return lowering initially inserted cleanup checks even with no active resources and could double-clean during propagation; both cases were corrected;
- mixed scalar/Text direct output could reorder because stdio buffering was mixed with raw writes; buffered output is flushed before exact-length Text writes;
- an apparent imported two-field layout corruption was traced to that output-ordering issue; dedicated IR-layout tests confirm serialized field ordering and access indices are consistent;
- direct tests explicitly catch shallow-copy mistakes in nested values and Lists of values.

Earlier fixes remain in force: length-aware Text, content equality, UTF-8 validation, Unicode identifier mangling, Int-only `%`, deep `fixed`, value semantics, pinned Unicode and multi-compiler CI.

## 14. Remaining implementation gaps

The major gaps are now engineering/runtime boundaries rather than unresolved source-language design.

### A. Direct automatic memory management

Implement precise root/type metadata and a production collector/reclamation strategy for direct heap values. Deterministic external resources remain separate from GC.

### B. Direct Unicode Text views

Lower and execute `.bytes`, `.scalars`, and `.characters` through Universal IR/direct backends using the same pinned Unicode semantics as the generated-C path.

### C. Precompiled inferred-generic implementation templates

Allow interface-only object dependencies to carry generic implementation templates or another validated specialization representation so arbitrary downstream concrete instantiations do not require source.

### D. ARM64 parity and native CI

Extend the second backend through Text, aggregates, checked errors and resources; add a native ARM64 Linux runner/test environment.

### E. Broader platform/ABI conformance

Windows/MSVC, additional Linux architectures, macOS direct ABI work and future RISC-V remain unimplemented or unautomated.

### F. WebAssembly and JavaScript

Both remain strategic targets but have not been implemented.

### G. Unicode official conformance corpus

Add the complete official pinned Unicode grapheme test vectors as an automated fixture.

### H. Optimization and production object format

The direct backend intentionally favors correctness and stack spilling. Register allocation, optimization, binary/compact object formats, incremental build caching and mature linker metadata remain future compiler work.

### I. Standard library breadth

Paths as a richer abstraction, time, JSON, networking, process/environment APIs and other domains remain library work.

## 15. Deliberately postponed — not defects

The following remain deliberately outside the current pre-0.1 implementation scope unless real programs force an earlier decision:

- explicit generic syntax/constraints;
- traits/interfaces;
- pattern matching;
- async/await and advanced concurrency;
- reflection/macros;
- identity-to-value snapshot API;
- advanced resource transfer/borrowing/lifetime syntax;
- package registry/version/lockfile design;
- advanced GC generations/concurrent collectors;
- stable portable bytecode/JIT;
- self-hosting;
- multiple feature-complete direct CPU backends.

## 16. Audit conclusion

The requested implementation sequence is complete at a meaningful bootstrap milestone.

Eristavi now demonstrates three mutually useful execution layers:

```text
Python bootstrap/reference runtime
```

```text
typed Eristavi IR → C11 → native
```

and, for a substantial language subset:

```text
typed Eristavi IR → Universal IR → direct x86-64 → native
```

A second ARM64 backend already consumes the same Universal IR, and serialized interface/object pairs prove that reusable Eristavi modules no longer require live Python analyzer state or dependency source for supported direct linkage.

The frozen source model survived this work without redesign.

> **Audit verdict:** Eristavi is now a broad pre-0.1 bootstrap compiler with a frozen source language, a mature reference/generated-C path, versioned source-independent module contracts and concrete Universal-IR objects, a substantially capable direct x86-64 backend, an independent ARM64 consumer of the same lower IR, and a 216-test multi-toolchain conformance suite. The next phase should prioritize production direct-runtime memory management, direct Unicode Text-view parity, reusable generic object templates, ARM64 parity/native CI and broader target/platform conformance—not new source syntax.
