# Eristavi pre-0.1 Implementation Audit

> **Audit date: 2026-10-25**
>
> **Scope:** frozen pre-0.1 source contract, bootstrap/reference runtime, generated-C path, verified Universal IR, direct x86-64 GC/runtime with contract-driven physical register allocation and spill-frame compaction, native ARM64 runtime, module artifacts/caching, JavaScript/WebAssembly consumers, Unicode conformance and hosted CI.

## Structural/native compiler and offline gate update

The first production-hardening patch reclaims completed native handler frames and
restores abandoned call scopes/temporary slots at a checked catch boundary. Stress
and address/undefined sanitizer tests cover these lifetimes; injected cleanup
failures now execute through both candidate C and native paths. See
PRODUCTION_HARDENING.md for the review and remaining P0 allocation work. General
object/Text collection and bounded temporary storage in ordinary loops remain open.

The older audit sections below retain historical Stage-0 capabilities and counts.
In particular, Stage-0's tracing collector/register allocator must not be confused
with the separate offline compiler's boxed bootstrap runtime.

Eristavi now owns structural value/List/maybe/identity/error/resource lowering,
its typed/effect verifier, Universal register/CFG lowering and verifier, a small
unreachable-block pass, and native x86-64/ARM64 ELF consumers. The executable corpus
contains 88 projects; all 67 accepted semantic projects are checked for lowering.
Cleanup-failure injection tests preserve primary/secondary ordering, and malformed
Universal IR tests reject bad classes, calls, successors and initialization.

The offline packaging gate compares fixed-snapshot native assembly/B-C binaries
and audits application builds with unusable Python/C compiler shims. The runtime
remains a prebuilt C bootstrap artifact and GNU assembler/linker tools are packaged;
this is not a production release or a source-compatible Stage-0 artifact ABI port.
The suite contains **353 tests**. Current-commit CI/self-build results belong to the
PR. OFFLINE_TOOLCHAIN.md records the architecture, audit/evidence formats and gates.
Frozen philosophy, grammar and semantic specifications remain unchanged.

## Float and inferred scalar specialization update

The candidate now supports binary64 Float and specialization of inferred functions
for Int/Float/Bool/Text arguments, with per-specialization type substitutions,
implementation reuse and pending-body lowering for nested/recursive/imported calls.
Float IR payloads are independently validated; the C bootstrap runtime converts
literals under nearest rounding, preserves operation boundaries and rejects
fast-math. Source philosophy, grammar and semantics are unchanged.

The executable corpus contains 60 projects; 28 malformed IR projects are rejected
by both verifier and backend. Additional tests inspect specialization reuse,
reject incompatible relationships, reset non-nearest rounding and check separated
operations under optimization/contraction settings. Stage-0 C infinity literal
emission and infinity/signed-zero division were corrected under the locked rules.
The suite now contains **344 tests**. Current-commit hosted results belong to its PR.
See SCALAR_SPECIALIZATION.md for evidence, bootstrap boundaries and remaining gates.

## Eristavi-written executable compiler slice

The candidate now lowers concrete Int/Bool/Text programs into its own source-close
typed IR, independently verifies that IR and emits C11. Functions/recursion,
imports, scopes, branching/loops, checked Int and exact Text are covered by 32
saved-output differential projects, 10 sanitized runtime-fault cases and 22
malformed-IR rejection projects. Stage-0 C binary/call evaluation order was
corrected to agree with the reference interpreter using C11 sequencing.
See SCALAR_COMPILATION.md for commands, evidence and precise boundaries.

The suite contains **340 tests**. The full native compiler, broader lowering,
Universal IR migration, optimization, repeated self-build and independent offline
toolchain packaging remain promotion gates. Source philosophy/specifications are
unchanged. Earlier update sections below record prior milestones.

## Eristavi-written semantic analyzer update

The experimental candidate now implements name/scope/module resolution, type
unification and inferred relationships, ordinary/List/maybe/identity values,
transitive fixed checks, returns, checked failures and deterministic resource rules.
The source module loader checks roots/visibility/cycles; expression type/effect
facts and inferred function contracts are retained for the next IR stage.

A 175-case corpus (67 accepted, 108 rejected) matches Stage-0 acceptance and inferred
contracts. Ten diagnostic-location differences are intentional and recorded.
Compiled and interpreted execution of the same Eristavi analyzer are compared,
and the compiled candidate analyzes its own frontend module graph offline.

Conformance also corrected Stage-0 duplicate parameters, ordinary count-field
assignment, ordinary resource-copy escape paths and no-value List elements.
These enforce existing frozen rules; the philosophy, grammar, lexical and semantic
specifications are unchanged. `analyze` is opt-in; Stage-0 remains the trusted normal
compiler. Source-independent interface artifacts and the Eristavi-written IR/
code-generation/self-build pipeline remain later work. See SEMANTIC_ANALYSIS.md.
The suite now contains **333 tests**; current-commit hosted results belong to its PR.

## Executable frontend update

`src/frontend.eri` now builds through C into an offline syntax-check/token/AST tool.
Its entry flow, lexer, parser and report formatting are written in Eristavi. Process
arguments, diagnostics and exit status are small `std.process` runtime operations;
read-only input and exclusive output use scoped `std.files` resources. Python and
a C toolchain remain build dependencies, but are not required to run the binary.

The shared frontend corpus compares full ASTs and source locations, as well as
rejection phases/locations. Every repository `.eri` source under `src/` is parsed
and compared to Stage-0. These checks exposed and corrected operator/statement
locations and opening-construct EOF diagnostics. Generic C lowering now preserves
checked optional-presence facts. Typed FileError handlers expose their existing
message/path payloads in the reference and C paths.

The suite contains **333 tests**. Current-commit hosted results belong to its PR.
The frontend remains syntax-only; semantic analysis, self-building and a fully
standalone assembler/linker toolchain remain later work. The frozen philosophy,
grammar, lexical specification and language semantics are unchanged.

## Self-hosting frontend update

The current change set repairs the Stage-2 parser recursion failure by identifying
inferred specializations by alpha-equivalent type relationships, not fresh internal
variable ids. Recursive result inference still requires an explicit result contract.
Shared relationships are retained when cloning a signature, and concrete inferred
specializations are emitted only once. Typed call lookup respects declared optional
parameter coercions.

The Eristavi lexer now checks numeric separators, decimal leading zeroes, Float
syntax, Unicode identifiers/NFC, scalar escapes, comments and BOM placement.
`std.unicode` supplies pinned identifier predicates, NFC and scalar construction in
the reference/C paths. Its C data is generated from pinned dependencies and tested
against every canonical decomposition and Hangul syllable, identifier-range
boundaries and ordering/composition edge cases. This library has not yet been
implemented by direct native, JS or Wasm backends; `erist build` is the supported
compiled migration route.

The Eristavi lexer and parser both compile and execute through C. Tests compare
lexical output/rejections/locations and expression precedence against Stage-0.
The suite also covers no-value `try` propagation and correct lowering of ordinary
fields named `count`. Mutable AST links use local optional snapshots and the
existing presence checks; compiler convenience does not introduce new field
narrowing semantics. Python remains Stage-0, and full self-building remains open.

The suite now contains **333 tests**. Hosted results for this revision are tracked
in the pull request; historical baseline results below are not a substitute for
checking the current commit.

## 1. Executive result

Eristavi is now a **broad working pre-0.1 compiler/toolchain with two native CPU backends, a portable C path, JavaScript/WebAssembly consumers, reusable module artifacts, automatic memory reclamation on the primary x86-64 direct runtime and a verified contract-driven physical-register allocation path**.

At this audit point:

- the source-language/frontend contract remains frozen;
- this phase required no new source keywords or fundamental semantic redesign;
- the Python bootstrap/reference runtime covers the principal frozen pre-0.1 surface;
- generated C remains the broad portability/conformance baseline;
- Universal IR is verified before and after bootstrap optimization;
- CFG-aware liveness/interference analysis is used by direct x86-64 root planning, spill coloring and physical register allocation;
- direct x86-64 executes the broad implemented language/runtime slice without generated C;
- audited x86 lowering contracts describe machine-level operand/clobber behavior, with unknown lowerings defaulting conservatively;
- the current x86 allocation pools contain two GP registers (`r10`, `r11`) and two XMM registers (`xmm8`, `xmm9`);
- register-resident scalar values no longer reserve redundant precise-x86 spill slots, while pinned heap/root slots remain stable;
- all three explicit Text views execute directly on x86-64 using pinned Unicode-17 behavior;
- the x86-64 runtime has non-moving mark-and-sweep reclamation with liveness-aware compiler roots and static heap descriptors;
- module interface/object artifacts support source-independent concrete linkage and downstream inferred-generic specialization;
- content/public-interface keyed module caching is implemented;
- ARM64 executes Text, aggregates, maybe/identity, checked errors and deterministic file resources on a native ARM64 Linux CI runner;
- ES2020 JavaScript supports ordinary aggregate/value semantics in addition to scalars/functions;
- WebAssembly text supports the scalar/function/control slice plus Text through an explicit UTF-8/`externref` host ABI;
- CI runs the complete official Unicode-17 `GraphemeBreakTest` fixture against the pinned reference segmenter;
- the repository suite contains **333 tests**; current-commit results are recorded in GitHub Actions.

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

### x86 physical register allocation

The x86-64 backend consumes these analyses through a conservative, machine-contract-driven allocator.

Current verified behavior:

- eligible short-lived Int/Bool values may use `r10` or `r11`;
- eligible short-lived Float values may use `xmm8` or `xmm9`;
- interference coloring prevents overlapping virtual values from sharing a physical register;
- per-lowering contracts describe caller-saved/scratch clobbers and whether operands are consumed before clobber;
- values live across helper/PLT/GC clobbers remain spilled;
- dead-after-use operands may remain register-resident when the lowering explicitly consumes them before its clobber point;
- scalar function-call results may become register-resident after the call returns;
- audited call-free scalar extraction operations may produce register-resident results;
- unknown/unaudited lowerings conservatively clobber the full caller-saved register set and cannot produce register-resident scalar results;
- unaudited physical-register pools are rejected.

### Spill-frame compaction

The stack-slot planner now supports values whose entire lifetime is represented by a physical register. Those values receive no spill slot in the precise x86 frame.

Safety rules are explicit:

- pinned values always win over exclusion;
- heap/rooted values keep stable unique slots when required by GC metadata;
- unallocated values retain stack storage as the correctness fallback;
- register-resident scalar values can be removed from the spill frame without affecting GC root addresses.

This is a meaningful physical allocator, but not yet a production whole-function allocator. Move/coalescing improvements, broader audited register use and richer machine-level cost modeling remain open.

## 5. x86-64 automatic memory management

The direct x86-64 Linux runtime uses a non-moving mark-and-sweep collector.

### Root precision

Compiler root frames contain:

- all heap-typed declared locals;
- only heap-typed Universal-IR temporaries proven live across collection safe points;
- static type descriptors paired with those root addresses.

Heap-valued temporary spill slots remain unique/stable when rooted. Register-resident scalar values are absent from the spill frame; remaining scalar temporaries may reuse noninterfering slots.

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
- contract-driven physical register residency for eligible scalar regions;
- spill-frame omission for values proven fully register-resident.

The allocator is layered below the checked-error/resource/direct/GC composition so higher-level runtime families inherit the same allocation policy without changing source semantics.

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
333 tests
```

The audited matrix is:

- GCC / x86-64 Ubuntu / `-O2`;
- Clang / x86-64 Ubuntu / `-O2`;
- Clang / ARM64 Ubuntu / `-O2`;
- Clang / ARM64 macOS / `-O2`.

The allocator/frame-compaction baseline passed all four jobs. The expanded self-hosting change set must pass the same matrix before promotion.

On x86-64 Linux, ARM-native tests are skipped because the ABI does not match. The ARM64 Linux job executes those same native cases. The matrix also runs the official Unicode-17 grapheme vectors.

Coverage includes frontend/reference semantics, generated-C execution, module artifacts/cache, Universal-IR verification/analysis, x86 typed GC, x86 lowering contracts, physical allocation, spill-frame compaction, direct x86 runtime, native ARM64 runtime, JavaScript aggregate/value semantics, WebAssembly Text contracts and Unicode official conformance.

## 13. Quality findings corrected during this phase

This implementation phase exposed and corrected several concrete issues:

- heap temporaries originally remained rooted too broadly; CFG safe-point liveness now selects the temporary-root set;
- scalar temporaries previously occupied one spill slot each; CFG interference coloring permits safe reuse;
- conservative heap child scanning has been replaced by typed descriptors for the principal runtime value families;
- the first x86 allocator model treated complex lowerings as a single clobber point and protected only values live afterward; full CI exposed eight aggregate/error/object regressions where caller-saved scalar operands were destroyed by helper calls before being consumed;
- the allocator was corrected to reason about complete lowering clobber regions;
- explicit x86 lowering contracts now distinguish values that cross clobbers from operands consumed safely before them;
- unknown future lowerings default to conservative full caller-saved clobber behavior;
- the audited allocation pools were expanded from one GP/XMM register to two GP and two XMM registers;
- register-resident scalar values originally still consumed redundant stack spill slots; the stack planner now supports explicit exclusion while guaranteeing pinned GC/root storage takes precedence;
- ARM64 native CI exposed mixed buffered-scalar/raw-Text output reordering; the composed direct backend now flushes before Text writes;
- one ARM checked-error test fixture violated the existing requirement that a value-producing handled expression cannot continue without a replacement value; the invalid fixture was corrected rather than weakening semantics;
- WebAssembly Bool comparison was corrected to use its i32 representation instead of an i64 comparison;
- the first Unicode-fixture workflow used an invalid runner-temp expression at the job environment level; the fixture path was made explicit and the immutable revision fetch now runs successfully on every job.

## 14. Remaining implementation boundaries

The largest remaining engineering tasks are:

### A. ARM64 automatic memory management and Text-view parity

Bring the x86 collector contract and explicit Text-view runtime to ARM64, or define a shared runtime layer that both native targets consume without changing language semantics.

### B. Register allocation maturation

The x86 compiler now has explicit lowering clobber contracts, two-register GP/XMM allocation pools and spill-frame omission for fully register-resident scalars. Remaining allocator work includes broader audited physical-register use, move/coalescing improvements, better cost heuristics and eventual richer instruction-selection integration.

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
- a complete self-hosted toolchain (the lexer/parser/semantic migration is active);
- advanced low-level/unsafe features.

## 16. Audit verdict

The implementation continues to validate the frozen language design.

Eristavi now has:

- a broad reference/generated-C implementation;
- verified/optimized Universal IR;
- CFG-aware liveness, interference and spill-slot analysis;
- a broad direct x86-64 backend with automatic typed heap reclamation;
- explicit x86 machine-lowering use/clobber contracts;
- audited `r10`/`r11` and `xmm8`/`xmm9` physical allocation pools;
- spill-frame compaction for values proven fully register-resident;
- a native-tested ARM64 backend for major runtime families;
- reusable source-independent module implementations and inferred-generic templates;
- incremental module caching;
- expanded JavaScript ordinary-value semantics;
- an explicit Text-aware WebAssembly host contract;
- full official Unicode-17 grapheme reference conformance;
- a **333-test four-platform CI matrix**.

The project has moved firmly from language-prototype construction into **compiler/runtime maturation and cross-target conformance work**. The remaining gaps are engineering depth and target parity, not evidence that the core source-language contract needs to be reopened.
