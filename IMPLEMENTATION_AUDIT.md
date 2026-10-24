# Eristavi pre-0.1 Implementation Audit

> **Audit date: 2026-10-24**
>
> **Scope:** frozen pre-0.1 source contract, bootstrap/reference runtime, generated-C path, verified Universal IR, direct x86-64 GC/runtime and initial physical register allocation, native ARM64 runtime, module artifacts/caching, JavaScript/WebAssembly consumers, Unicode conformance and hosted CI.

## 1. Executive result

Eristavi is now a **broad working pre-0.1 compiler/toolchain with two native CPU backends, a portable C path, JavaScript/WebAssembly consumers, reusable module artifacts, automatic memory reclamation on the primary x86-64 direct runtime and an initial verified physical-register allocation path**.

At this audit point:

- the source-language/frontend contract remains frozen;
- this phase required no new source keywords or fundamental semantic redesign;
- the Python bootstrap/reference runtime covers the principal frozen pre-0.1 surface;
- generated C remains the broad portability/conformance baseline;
- Universal IR is verified before and after bootstrap optimization;
- CFG-aware liveness/interference analysis is used by direct x86-64 stack/root planning and conservative physical register allocation;
- direct x86-64 executes the broad implemented language/runtime slice without generated C;
- short-lived scalar values in proven call-free x86 regions can execute directly from physical GP/XMM registers while unsafe lowering boundaries retain spill fallback;
- all three explicit Text views execute directly on x86-64 using pinned Unicode-17 behavior;
- the x86-64 runtime has non-moving mark-and-sweep reclamation with liveness-aware compiler roots and static heap descriptors;
- module interface/object artifacts support source-independent concrete linkage and downstream inferred-generic specialization;
- content/public-interface keyed module caching is implemented;
- ARM64 executes Text, aggregates, maybe/identity, checked errors and deterministic file resources on a native ARM64 Linux CI runner;
- ES2020 JavaScript supports ordinary aggregate/value semantics in addition to scalars/functions;
- WebAssembly text supports the scalar/function/control slice plus Text through an explicit UTF-8/`externref` host ABI;
- CI runs the complete official Unicode-17 `GraphemeBreakTest` fixture against the pinned reference segmenter;
- the repository suite contains **262 tests** and passes in all four hosted CI jobs.

The governing target rule remains:

> **Target platforms implement Eristavi semantics; they do not redefine them.**

## 2. Compiler architecture

```text
Eristavi source
    ↓
lexer / parser / AST
    ↓
name resolution + semantic analysis + type inference
    ↓                         ↘
bootstrap/reference runtime   typed/source-close Eristavi IR
                                  ├─→ C11 → C toolchain → native
                                  ↓
                         verified + optimized Universal IR
                                  ├─→ x86-64 Linux → allocation/lowering → assembly → native
                                  ├─→ ARM64 Linux → assembly → native
                                  ├─→ ES2020 JavaScript
                                  └─→ WebAssembly text
```

Reusable module compilation remains separated into public contract and implementation artifacts:

```text
module.eri
  ├─→ module.eri-interface.json
  └─→ module.eri-object.json
```

This architecture no longer relies on generated C or live Python analyzer objects as the only executable/reusable boundaries.

## 3. Frozen frontend/reference surface

The frontend/reference implementation continues to cover the principal frozen language surface:

- Unicode-17 XID identifiers and NFC identifier identity;
- checked signed 64-bit Int;
- IEEE binary64-oriented Float;
- length-aware Unicode Text;
- explicit character/scalar/byte Text views;
- `let`, annotations, transitive `fixed`, lexical scopes and no-shadowing;
- Bool-only conditions, `if/else`, `while`, stable `for`;
- functions, recursion and result inference;
- compiler-inferred generic relationships;
- Lists with ordinary value semantics;
- named-field ordinary values and structural equality;
- maybe/none and flow narrowing;
- explicit identity handles;
- checked failures/propagation/handlers;
- deterministic `with` resources;
- modules/imports/aliases/visibility.

No explicit generic syntax, exception hierarchy, manual memory syntax or additional source keywords were introduced.

## 4. Universal IR maturity

Universal IR represents functions/CFG, typed virtual values/locals, scalar types, Text/Text views, nominal layouts, Lists, maybe, identity, checked arithmetic, Float/Text operations, explicit ordinary-value cloning/equality, checked failure state and deterministic resources.

### Verification

The verifier checks function/type/block symbols, dense local/value ids, CFG targets, Bool branches, call signatures/results and return contracts. Verification occurs before and after optimization.

### Bootstrap optimization

Current semantics-preserving optimization includes:

- constant folding for supported Int/Bool/Float operations;
- checked Int folding only when Eristavi overflow/division rules remain satisfied;
- unreachable-block elimination.

### CFG analyses

The compiler computes:

- block live-in/live-out sets;
- instruction-level liveness;
- value interference graphs;
- spill-slot coloring;
- escape reasons;
- scalar register candidates.

### Initial x86 physical register allocation

The x86-64 backend now consumes those analyses through a deliberately conservative allocator.

Current verified behavior:

- short-lived Int/Bool candidates may use a caller-saved GP register;
- short-lived Float candidates may use a caller-saved XMM register;
- interference coloring prevents overlapping virtual values from sharing the same physical register;
- values that cross a possible helper/PLT/GC clobber remain spilled;
- operands consumed inside complex machine-lowering regions also remain spilled, because those lowerings may call helpers before all operands are consumed;
- scalar values produced by higher-level aggregate/error/List extraction remain stack-backed until those lowerings have explicit machine use/clobber contracts;
- existing stack slots remain available as the correctness fallback.

This is a real register-resident execution path, but it is not yet a mature whole-function register allocator. Broader register pools, explicit target clobber metadata and dead spill-slot/frame compaction remain future work.

## 5. x86-64 automatic memory management

The direct x86-64 Linux runtime uses a non-moving mark-and-sweep collector.

### Root precision

Compiler root frames contain:

- all heap-typed declared locals;
- only heap-typed Universal-IR temporaries proven live across collection safe points;
- static type descriptors paired with those root addresses.

Heap-valued temporary spill slots remain unique/stable when rooted. Noninterfering scalar virtual values may reuse spill slots.

### Typed heap traversal

Descriptors currently distinguish and traverse:

- Text/Text-view leaves;
- nominal objects using declared field layouts;
- Lists, their backing allocation and heap-typed elements;
- maybe wrappers;
- identity wrappers;
- current file-resource records.

Dynamic checked-error globals still use a conservative fallback that follows only exact tracked-allocation pointers. This avoids treating arbitrary addresses as managed references while keeping dynamic state safe.

### GC limitations

This collector is meaningful automatic reclamation, but it is still bootstrap infrastructure rather than a final production collector:

- collection is stop-the-world/single-runtime oriented;
- it is not generational, concurrent or compacting;
- a root slot selected because a value crosses some safe point may retain the value longer than its exact final live interval if that slot is not cleared dynamically;
- dynamic checked-error payload traversal retains a conservative fallback;
- ARM64 does not yet have equivalent automatic reclamation.

Deterministic external resources remain outside GC ownership by design.

## 6. Direct x86-64 execution boundary

The System V backend executes without generated C:

- Int/Bool/Float;
- length-aware Text and all explicit Text views;
- functions, recursion and register/stack arguments;
- checked Int arithmetic/faults;
- control flow and short-circuit Boolean logic;
- nominal values and recursive deep value copying;
- Lists, checked indexing, mutation, equality and stable iteration;
- maybe/none;
- identity aliasing/equality;
- source/object-template inferred generic specialization;
- checked errors and handlers;
- deterministic file resources;
- exact UTF-8 Text file boundaries including embedded NUL;
- source-independent module-object linkage;
- automatic heap reclamation;
- conservative physical register residency for eligible scalar regions.

The physical allocator is intentionally layered below the existing checked-error/resource/direct/GC composition so those higher-level runtime families inherit the same allocation policy without changing source semantics.

## 7. ARM64 backend and native CI

ARM64/AAPCS64 consumes the same Universal IR.

The current direct runtime supports and executes in hosted native ARM64 Linux CI:

- Int/Bool/Float;
- functions/calls/recursion and ABI argument placement;
- checked Int arithmetic;
- control flow;
- length-aware Text;
- nominal values and Lists;
- maybe and identity;
- checked errors/typed handlers;
- deterministic `std.files` operations and cleanup;
- embedded-NUL Text file round trips.

An output-order bug exposed by native ARM testing was fixed by flushing stdio before exact-length Text writes, matching the x86 runtime contract.

Cross-assembly tests remain alongside native behavioral tests.

Remaining ARM64 parity gaps include:

- automatic memory reclamation/GC;
- direct `.bytes`, `.scalars`, `.characters` runtime parity;
- broader long-running memory/runtime stress coverage.

## 8. Unicode/Text conformance

The toolchain pins Unicode **17.0.0**.

CI fetches an immutable-revision copy of `GraphemeBreakTest-17.0.0.txt` and executes every non-comment conformance vector against the pinned reference segmenter. The harness asserts that the fixture is Unicode 17 and contains the expected broad test population.

Additional tests exercise generated-C and direct x86-64 grapheme behavior, including combining sequences, ZWJ emoji, regional indicators and Indic conjuncts.

This closes the prior gap of having only a curated grapheme corpus for the reference implementation. It does **not** yet compile and execute every official vector through every backend.

## 9. Module artifacts, generics and caching

### Interface

The versioned interface artifact preserves public types/errors/functions, Unicode version, dependency identities, checked failure contracts and inferred generic relationships.

### Object

Object format v3 (`universal-ir-v3`) serializes concrete verified/optimized Universal IR and nominal/error layouts tied to the exact interface digest.

For public inferred-generic functions it can also carry a bootstrap implementation template. Downstream object-only compilation can specialize supported inferred-generic functions after original source removal.

This preserves the language's source-level inferred-generic model; no explicit generic syntax was added.

### Incremental cache

Reusable artifact cache keys include source content and dependency public-interface identities. A public dependency contract change invalidates importers; a private implementation-only dependency change does not invalidate an otherwise unchanged importer contract key.

The JSON/bootstrap object form is not a final compact production binary format.

## 10. JavaScript backend

The ES2020 consumer preserves Eristavi Int with checked `BigInt`.

It supports:

- scalar/function/control behavior;
- Text concatenation/equality/output;
- nominal values and field mutation;
- Lists with bounds checks;
- maybe/none;
- identity handles;
- deep ordinary-value cloning;
- structural equality.

Execution tests cover value-copy independence, Lists, maybe, identity aliasing and defined failure on List bounds.

Remaining JavaScript parity includes checked errors, deterministic resources, explicit Text views and broader module/runtime integration.

## 11. WebAssembly backend

The WAT consumer supports current scalar/function/control behavior and checked Int runtime contracts.

Text is represented by an explicit host boundary rather than a numeric approximation:

- UTF-8 constants are emitted in memory data segments;
- `text_from_utf8` creates an `externref` Text value;
- concatenation, equality and output are explicit host imports.

This keeps Text semantics distinct while the full Wasm runtime is still under construction.

Remaining Wasm work includes aggregate values, checked failures, resources, Text views, a concrete host runtime and binary execution/conformance tests.

## 12. Test and CI result

The current suite contains:

```text
262 tests
```

The audited matrix is:

- GCC / x86-64 Ubuntu / `-O2`;
- Clang / x86-64 Ubuntu / `-O2`;
- Clang / ARM64 Ubuntu / `-O2`;
- Clang / ARM64 macOS / `-O2`.

All four jobs pass on the verified register-allocation change set.

On x86-64 Linux, ARM-native tests are skipped because the ABI does not match. The ARM64 Linux job executes those same native cases. The matrix also runs the official Unicode-17 grapheme vectors.

Coverage includes frontend/reference semantics, generated-C execution, module artifacts/cache, Universal-IR verification/analysis, x86 typed GC, direct x86 runtime and register-allocation regressions, native ARM64 runtime, JavaScript aggregate/value semantics, WebAssembly Text contracts and Unicode official conformance.

## 13. Quality findings corrected during this phase

This implementation phase exposed and corrected several concrete issues:

- heap temporaries originally remained rooted too broadly; CFG safe-point liveness now selects the temporary-root set;
- scalar temporaries previously occupied one spill slot each; CFG interference coloring permits safe reuse;
- conservative heap child scanning has been replaced by typed descriptors for the principal runtime value families;
- the first x86 allocator model treated complex lowerings as a single clobber point and protected only values live afterward; full CI exposed eight aggregate/error/object regressions where caller-saved scalar operands were destroyed by helper calls before being consumed;
- the allocator now treats complex lowerings as clobber **regions**, keeping both their operands and surviving values stack-backed unless the lowering is explicitly known call-free;
- higher-level scalar extraction is also conservatively excluded from register residency until machine-level use/clobber contracts exist;
- ARM64 native CI exposed mixed buffered-scalar/raw-Text output reordering; the composed direct backend now flushes before Text writes;
- one ARM checked-error test fixture violated the existing requirement that a value-producing handled expression cannot continue without a replacement value; the invalid fixture was corrected rather than weakening semantics;
- WebAssembly Bool comparison was corrected to use its i32 representation instead of an i64 comparison;
- the first Unicode-fixture workflow used an invalid runner-temp expression at the job environment level; the fixture path was made explicit and the immutable revision fetch now runs successfully on every job.

## 14. Remaining implementation boundaries

The largest remaining engineering tasks are:

### A. ARM64 automatic memory management and Text-view parity

Bring the x86 collector contract and explicit Text-view runtime to ARM64, or define a shared runtime layer that both native targets consume without changing language semantics.

### B. Register allocation maturation

The compiler now has a working conservative x86 physical allocator, but the next steps are explicit machine-level use/clobber contracts, a broader safe physical-register pool, better move/coalescing decisions and removal/compaction of spill slots that are no longer needed.

A mature allocator must continue to preserve the existing System V ABI, checked-failure paths and precise-GC rooting contract rather than optimizing around them implicitly.

### C. JavaScript/WebAssembly parity

Add checked errors, resources and explicit Text views to JavaScript; add aggregate/error/resource/Text-view runtime families and actual executable Wasm integration.

### D. Direct Unicode backend-wide official-vector execution

The reference segmenter passes the complete official fixture. Compiling every official vector through direct/generated targets would provide stronger cross-backend Unicode evidence.

### E. Production artifacts/linking

Replace or supplement JSON bootstrap objects with compact validated binary artifacts and more mature linker metadata/incremental build orchestration.

### F. Additional OS/ABI targets

Direct Windows and macOS ABIs remain unimplemented. RISC-V remains a later third native architecture candidate.

### G. Standard library breadth

Paths, time, JSON, networking, process/environment APIs and other domains remain library work.

## 15. Deliberately postponed — not defects

The following remain outside the frozen pre-0.1 source scope unless real programs force a decision:

- explicit generic syntax/constraints;
- traits/interfaces;
- pattern matching;
- async/await and advanced concurrency;
- reflection/macros;
- package registry;
- stable bytecode/JIT;
- self-hosting;
- advanced low-level/unsafe features.

## 16. Audit verdict

The implementation continues to validate the frozen language design.

Eristavi now has:

- a broad reference/generated-C implementation;
- verified/optimized Universal IR;
- CFG-aware liveness, interference and spill-slot analysis;
- a broad direct x86-64 backend with automatic typed heap reclamation;
- an initial verified x86 physical-register allocation path with conservative clobber-region safety;
- a native-tested ARM64 backend for major runtime families;
- reusable source-independent module implementations and inferred-generic templates;
- incremental module caching;
- expanded JavaScript ordinary-value semantics;
- an explicit Text-aware WebAssembly host contract;
- full official Unicode-17 grapheme reference conformance;
- a **262-test four-platform CI matrix**.

The project has moved firmly from language-prototype construction into **compiler/runtime maturation and cross-target conformance work**. The remaining gaps are engineering depth and target parity, not evidence that the core source-language contract needs to be reopened.
