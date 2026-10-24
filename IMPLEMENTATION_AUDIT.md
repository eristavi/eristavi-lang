# Eristavi pre-0.1 Implementation Audit

> **Audit date: 2026-10-24**
>
> **Scope:** frozen pre-0.1 source contract, bootstrap/reference runtime, generated-C path, verified Universal IR, direct x86-64 runtime/GC, ARM64 assembly backend, module artifacts/caching, JavaScript/WebAssembly consumers, Unicode behavior and multi-toolchain CI.

## 1. Executive result

Eristavi is now a **broad working pre-0.1 compiler/toolchain with an independent direct-native runtime architecture and multiple Universal-IR consumers**.

At this audit point:

- the source-language/frontend contract remains frozen;
- this implementation phase required no new source keywords or fundamental semantic redesign;
- the Python bootstrap/reference runtime covers the principal frozen pre-0.1 language surface;
- the generated-C backend remains the broad portability/conformance baseline;
- Universal IR is verified and bootstrap-optimized before direct/object consumption;
- direct x86-64 Linux executes a broad language/runtime slice without generated C;
- all three explicit Text views execute directly on x86-64, including pinned Unicode-17 grapheme segmentation;
- the direct x86-64 runtime now includes automatic non-moving mark-and-sweep reclamation with compiler-described roots;
- module interface/object artifacts support source-independent concrete linkage and reusable downstream inferred-generic specialization;
- incremental module artifact caching uses source content plus dependency public-contract identities;
- ARM64 consumes the same Universal IR and now has expanded Text/aggregate/error/resource assembly-generation layers;
- ES2020 JavaScript and WebAssembly-text backends consume the current scalar/function/control Universal-IR slice;
- the verified suite contains **245 tests** and passes in all three hosted CI jobs: GCC/Ubuntu, Clang/Ubuntu and Clang/macOS at `-O2`.

The governing target rule remains:

> **Target platforms implement Eristavi semantics; they do not redefine them.**

## 2. Current compiler architecture

```text
Eristavi source
    ↓
lexer / parser / AST
    ↓
name resolution + semantic analysis + type inference
    ↓                         ↘
bootstrap/reference runtime   typed/source-close Eristavi IR
                                  ├─→ C11 backend → C compiler → native
                                  ↓
                         verified + optimized Universal IR
                                  ├─→ x86-64 Linux → assembly → native
                                  ├─→ ARM64 Linux → assembly/native on matching host
                                  ├─→ ES2020 JavaScript
                                  └─→ WebAssembly text
```

Reusable module compilation has a separate semantic/implementation boundary:

```text
module.eri
  ├─→ module.eri-interface.json   public semantic contract
  └─→ module.eri-object.json      Universal-IR implementation + optional generic template
```

This means generated C is no longer the only compiled proof, and live Python analyzer state is no longer required as the only reusable module boundary.

## 3. Frozen frontend/reference implementation

The frontend/reference runtime continues to implement the principal frozen surface:

- exact lexical/keyword rules;
- Unicode 17 XID identifiers and NFC identity;
- checked signed-64-bit `Int`;
- IEEE binary64-oriented `Float`;
- length-aware Unicode `Text`;
- explicit `.characters`, `.scalars`, `.bytes` Text views;
- `let`, transitive `fixed`, annotations and lexical no-shadowing;
- Bool-only conditions, `if / else`, `while`, stable `for`;
- functions, recursion and return inference;
- compiler-inferred generic relationships without source generic variables;
- growable ordered `List` values;
- named-field ordinary values and structural equality;
- `maybe` / `none` and flow narrowing;
- explicit managed `identity`;
- checked errors, propagation and handlers;
- deterministic `with` resources;
- modules/imports/aliases/visibility.

This phase did not add borrowing syntax, manual memory syntax, exception syntax, traits, explicit generic syntax, reflection or async syntax.

## 4. Unicode and Text audit

### Pinned semantics

Identifier normalization/classification and grapheme behavior remain pinned to Unicode **17.0.0** rather than host Python/OS Unicode versions.

### Generated-C path

Generated C supports:

```eri
text.bytes
text.scalars
text.characters
```

The character view uses generated Unicode-property tables and a pinned extended-grapheme implementation rather than libc locale behavior or code-point approximation.

Compiled Text remains UTF-8 bytes plus explicit length. Embedded NUL survives output, equality, concatenation and file round trips. Invalid UTF-8 read from a file remains a checked `FileError`.

### Direct x86-64 path

The direct backend now executes all three explicit views without generated C:

- byte count/index;
- Unicode scalar count/index;
- extended grapheme cluster count/index.

Pinned Unicode property tables are emitted for the assembly runtime. Direct tests cover combining sequences, emoji ZWJ sequences, regional-indicator pairing, Indic conjunct behavior and bounds faults.

### Remaining conformance boundary

Representative/corpus parity is tested, but this audit does **not** claim automated execution of every vector from the complete official Unicode `GraphemeBreakTest.txt`. Adding the full pinned official corpus remains desirable production conformance work.

## 5. Universal IR audit

Universal IR now represents a meaningful machine-independent execution contract rather than a scalar experiment.

It includes:

- typed virtual values and locals;
- basic blocks and jump/branch/return terminators;
- functions, parameters, calls, returns and recursion;
- `i64`, `f64`, `bool`, length-aware `text`, and `void`;
- Text-view operations;
- nominal layouts and fields;
- Lists, maybe and identity handles;
- checked Int arithmetic;
- Float arithmetic/comparison operations;
- Text concatenation/equality/output;
- short-circuit Boolean CFG;
- construction, field access and mutation;
- List construction/count/get/set/add and stable iteration;
- explicit ordinary-value cloning at transfer boundaries;
- structural equality versus identity equality;
- checked-error state/matching/dispatch/propagation;
- deterministic resource cleanup;
- `std.files` open/read/write/exists/remove operations.

Ordinary values and shared identity are therefore distinguished *before* target-specific code generation.

### Verification

Universal-IR verification checks, among other things:

- unique function/type/block symbols;
- entry-function presence;
- dense valid local/value ids;
- valid CFG targets;
- Bool branch conditions;
- function-call target/arity/type contracts;
- return contracts;
- presence and validity of terminators.

Verification runs before and after the current optimization pipeline.

### Bootstrap optimization

Implemented semantics-preserving passes include:

- supported Int/Bool/Float constant folding;
- checked-Int folding only when Eristavi overflow/division rules remain valid;
- unreachable-block elimination;
- post-pass verification.

Target-neutral analysis also computes:

- deterministic value live ranges;
- stack-slot planning/coalescing groundwork;
- escape classification for calls/returns;
- short-lived scalar register candidates.

These analyses are currently groundwork rather than a production register allocator.

## 6. Direct x86-64 Linux backend

The System V backend executes a broad pre-0.1 slice without generated C.

### Functions and ABI

Implemented and tested:

- functions and recursion;
- value/no-value returns;
- general-register arguments;
- XMM Float arguments/returns;
- stack arguments after register capacity;
- nested checked arithmetic faults that terminate through the runtime fault path.

Tests include recursive factorial and an eight-argument function.

### Scalars, Text and aggregates

Implemented and tested:

- Int/Bool/Float;
- checked Int arithmetic/division/remainder;
- Float functions/arithmetic/comparison cases;
- length-aware Text and embedded NUL;
- all Text views;
- ordinary nominal values;
- nested mutation;
- deep logical copying;
- structural equality;
- Lists, checked indexing, `.count`, `.add`, mutation, equality and stable iteration;
- maybe/none;
- identity aliasing and logical identity equality.

### Inferred generics

Source builds specialize inferred relationships directly. Tests cover:

- preserve/identity-style relationships across multiple concrete scalar types;
- same-type multi-parameter relationships;
- inferred List element relationships;
- generic ordinary value use.

### Checked failures

Checked failures are represented as Universal-IR state/CFG operations, not target exceptions.

Direct tests cover:

- catch-all error message access;
- typed error fields;
- typed handler selection;
- `try` propagation through functions;
- success bypassing handlers;
- cleared failure state not leaking into later calls;
- handler-produced secondary/new checked failures.

### Deterministic resources

The direct runtime implements the current `std.files` surface:

- `files.open`;
- `File.readText()`;
- `File.writeText()`;
- `files.exists()`;
- `files.remove()`;
- deterministic `with` cleanup.

Tests cover return cleanup, nested cleanup, UTF-8 validation, embedded NUL data/path handling, missing paths, `exists/remove`, and body-failure priority over cleanup failure.

Deterministic external resources remain separate from GC memory ownership.

## 7. Direct automatic-memory-management audit

Automatic memory management now exists in the direct x86-64 path.

### Current collector

The runtime uses a tracked **non-moving mark-and-sweep** collector.

Compiler-generated root frames contain addresses of:

- heap-typed declared local slots;
- heap-typed Universal-IR temporary spill slots.

Checked-error runtime globals are also marked as roots.

The temporary-slot addition is important: a composite temporary can remain live between construction and a later use even when it has not yet become an ordinary source binding.

### Correctness bugs found and fixed

During collector integration:

1. GC-frame unlink initially used `%rax`, overwriting ordinary function return values after the return value had already been placed there. Root-frame unlink now uses `%r11`.
2. Rooting only declared locals allowed heap-valued IR temporaries to be reclaimed prematurely. Heap-typed temporary spill slots are now roots as well.
3. The collector sweep loop needed to preserve its list cursor across libc `free`, since caller-saved `%rcx` cannot be assumed stable.
4. Two near-identical GC root-frame implementations were consolidated so future root-contract fixes cannot diverge.

After these fixes, direct aggregate/error/resource/object/generic tests and dedicated GC graph/stress tests pass.

### Precision boundary

This audit deliberately does **not** call the current collector a finished production precise GC.

Root discovery is compiler-described at known slots. However, child discovery inside a tracked heap allocation currently scans payload machine words and treats exact tracked allocation pointers as references.

This is safe for the present bootstrap representation but can conservatively retain allocations whose data word happens to equal a tracked pointer. A production collector should use typed heap descriptors/pointer masks and tighter liveness-derived root ranges.

## 8. Module interfaces, objects and inferred-generic templates

### Interface artifact

Current public contract:

```text
schema  = eristavi.module-interface
version = 1
```

It preserves public types/errors/functions, dependency identities, Unicode version, checked `fails` contracts and inferred generic relationships.

Importers can type-check from the interface after dependency source removal.

### Implementation artifact

Current implementation artifact:

```text
schema  = eristavi.module-object
version = 3
IR      = universal-ir-v3
```

It serializes concrete verified/optimized Universal-IR implementations and required type layouts, tied to the exact interface digest.

The linker rejects interface/object digest mismatch.

### Reusable inferred-generic specialization

For a module exporting public inferred-generic functions, object v3 can carry a bootstrap reusable implementation template:

```text
generic_template.kind = eristavi-source-v1
```

A downstream importer can request a concrete specialization after the original dependency `.eri` source has been deleted. The template is re-analyzed against serialized module/dependency contracts, concretized for the downstream argument types, lowered to Universal IR and linked.

Tests cover post-source-removal specialization of:

- preserve-style `(T) -> T` relationships;
- same-type multi-parameter relationships;
- List element relationships.

This does **not** introduce user-visible generic syntax. A future compact generic IR/template representation should replace the bootstrap internal source-template payload.

## 9. Incremental module/build cache

`erist compile-module` now supports reusable artifact caching keyed by source content and dependency public-contract identities.

Verified behavior:

- identical second compile is a cache hit;
- own source changes invalidate the module;
- dependency public-interface changes invalidate importers;
- dependency private implementation changes do not invalidate an importer when the public interface digest is unchanged.

This is a sound bootstrap incremental-compilation boundary. It is not yet a complete package manager/build graph or production artifact store.

## 10. ARM64 backend

ARM64/AAPCS64 consumes the same Universal IR rather than a parallel semantic pipeline.

Current assembly-generation coverage includes:

- Int/Bool/Float;
- functions/calls/recursion;
- register/stack argument placement;
- checked integer arithmetic/division/remainder;
- comparisons/control flow;
- Text runtime operations;
- ordinary values and List operations;
- maybe and identity operations;
- checked-error state/handler operations;
- deterministic file-resource runtime operations and secondary-failure state.

CI cross-assembles the expanded AArch64 output successfully.

A native ARM64 execution test exists for matching ARM64 Linux hosts. The current hosted matrix does not provide broad ARM64 **Linux** native execution, so cross-assembly proves code-generation validity but does not yet establish full runtime behavioral parity with x86-64.

## 11. JavaScript backend

An ES2020 backend now consumes the current scalar/function/control Universal-IR slice.

Most important semantic choice:

> Eristavi `Int` uses checked JavaScript `BigInt`; ordinary `Number` is not allowed to silently redefine 64-bit integer semantics.

Tests execute:

- functions;
- Float/Text cases in the supported slice;
- control flow;
- checked Int overflow behavior.

Lists, ordinary aggregates, maybe/identity, checked errors, deterministic resources and complete Unicode Text runtime parity remain future JavaScript work.

## 12. WebAssembly backend

A WebAssembly-text backend now consumes the current scalar/function/control Universal-IR slice.

It emits direct WAT contracts for:

- functions/calls;
- checked Int operations;
- control-flow dispatch.

Unsupported runtime families such as Text are currently rejected explicitly rather than approximated.

The current tests validate emitted WAT structure/contracts. This audit does not claim a complete WebAssembly runtime, full heap semantics or broad `.wasm` executable conformance yet.

## 13. Generated-C backend

Generated C remains the broad portable baseline and important semantic cross-check.

It covers the principal implemented pre-0.1 surface, including:

- scalar types and checked Int behavior;
- length-aware Text and all explicit Unicode Text views;
- functions/recursion/control flow;
- Lists and ordinary values;
- maybe and identity;
- checked errors;
- inferred generic specializations;
- modules;
- deterministic resources;
- exact Text file I/O and checked path operations.

Generated-C executable linkage still follows its own implementation-source route rather than using the Universal-IR direct object linker.

## 14. Float conformance

The suite continues to exercise important IEEE behavior, including:

- NaN equality behavior;
- infinities;
- signed zero;
- smallest subnormal preservation;
- overflow to infinity;
- direct x86-64 Float function/arithmetic/comparison behavior.

This is meaningful conformance evidence but not exhaustive proof across every CPU, optimization mode and floating-point environment. Native ARM64 Linux Float execution and Windows toolchains remain future matrix additions.

## 15. Test and CI result

The verified suite contains:

```text
245 tests
```

The tested implementation boundary passes all three GitHub Actions jobs:

- GCC / Ubuntu / `-O2`;
- Clang / Ubuntu / `-O2`;
- Clang / macOS / `-O2`.

Coverage includes:

- frozen frontend/reference semantics;
- generated-C native execution;
- pinned Unicode/grapheme behavior;
- module interfaces and source-independent type checking;
- v3 objects, digest integrity and source-independent linkage;
- inferred-generic object specialization after source removal;
- incremental artifact caching;
- verified/optimized Universal IR and analysis groundwork;
- direct x86-64 function ABI/recursion;
- Float/Text/Text-view direct execution;
- deep values, Lists, maybe and identity;
- checked-error direct execution;
- deterministic resources/UTF-8 boundaries;
- GC root-frame and nested-graph/replacement stress behavior;
- ARM64 expanded runtime emission and cross-assembly;
- JavaScript scalar/function execution;
- WebAssembly-text scalar/function contracts.

Platform-specific tests skip when a matching execution ABI/runtime is unavailable rather than pretending another host proves native behavior.

## 16. Quality findings from this implementation phase

The phase exposed concrete engineering defects and resolved them rather than weakening semantics:

- direct Text views were implemented natively instead of approximating graphemes as code points;
- return-register corruption from GC-frame unlinking was fixed;
- heap-valued IR temporary roots were added after stress tests exposed premature reclamation;
- the GC sweep cursor is preserved across external allocator calls;
- duplicate GC root-frame implementations were consolidated;
- ARM64 resource tests exposed an invalid test fixture attempting an unsupported member access in that handler context; the fixture was corrected to the valid catch-all error view;
- prior direct-runtime fixes remain in force: exact-length Text, output ordering, deep value copies, checked-error lifetime, deterministic cleanup and object layout consistency.

The source-language design survived these issues unchanged.

## 17. Remaining production gaps

The largest remaining gaps are now implementation maturity boundaries.

### A. Typed heap descriptors and GC liveness

Replace payload-word child scanning with typed pointer descriptors/masks, integrate liveness so dead temporary roots do not remain for an entire function, and tune collection policy/performance.

### B. Backend allocation quality

Apply the existing live-range/stack-slot/register-candidate analysis to real stack-slot reuse and register allocation. The current direct backend remains correctness-first and spill-heavy.

### C. Native ARM64 Linux CI

Run the expanded ARM64 runtime behavior on actual ARM64 Linux, not only cross-assemble it. Resolve any ABI/runtime parity issues discovered there.

### D. JavaScript/WebAssembly parity

Extend both targets through aggregates, maybe/identity, checked failures, deterministic resources, Text views and automatic-memory/runtime services while preserving Eristavi semantics.

### E. Production artifacts/linker

Replace or complement bootstrap JSON/source-template objects with compact validated binary/template artifacts, stronger dependency metadata and mature separate compile/link behavior.

### F. Broader OS/ABI matrix

Windows, macOS direct-native ABI work, more Linux architectures and later RISC-V remain future target work.

### G. Full Unicode official test corpus

Automate the complete pinned official grapheme-break vector set rather than relying only on representative/corpus parity cases.

### H. Standard-library breadth

Paths, time, JSON, networking, process/environment APIs and other domains remain library work.

## 18. Deliberately postponed — not defects

Still outside current pre-0.1 scope unless real use forces reconsideration:

- explicit generic syntax/constraints;
- traits/interfaces;
- pattern matching;
- async/await and advanced concurrency;
- reflection;
- macros;
- operator overloading;
- package registry;
- self-hosting.

## 19. Final audit verdict

The current repository is best described as:

> **A broad pre-0.1 Eristavi compiler/toolchain with a frozen source-language contract, a mature bootstrap/reference and generated-C baseline, verified target-neutral Universal IR, a broad direct x86-64 runtime including Unicode views and automatic reclamation, reusable module objects with inferred-generic specialization, an expanded ARM64 backend, and first JavaScript/WebAssembly consumers.**

It is **not yet a production 0.1 release**. The next work is mainly runtime precision, code-generation quality, second-backend native conformance, portable-target parity and production artifact/tooling maturity.

Most importantly, the implementation continues to support the governing design decision:

> **Small language. Rich libraries. Powerful compiler. Predictable runtime. Universal architecture.**
