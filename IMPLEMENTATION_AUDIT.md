# Eristavi pre-0.1 Implementation Audit

> **Audit date: 2026-10-24**
>
> **Scope:** frozen pre-0.1 language contract versus the Python bootstrap frontend/runtime, serialized module interfaces, typed IR, generated-C backend, lower Universal IR, first direct CPU backend, Unicode runtime, standard-library surface and cross-toolchain CI.

## 1. Executive result

Eristavi has crossed another implementation boundary.

The project is no longer only a broad bootstrap compiler that happens to use C for native execution. It now has:

1. **versioned serialized module interfaces** that permit source-independent type checking;
2. **compiled Unicode 17 grapheme segmentation**, closing the previous `text.characters` backend gap;
3. a distinct **lower Universal IR** with explicit blocks, virtual values and checked primitive operations;
4. a real **direct x86-64 Linux backend** that produces executable code without generated C;
5. a slightly broader **standard library**, including checked filesystem existence/removal operations.

The frozen source-language semantics did not need to be reopened to implement any of these changes.

The verified suite now contains **174 tests**. The full suite passes under GCC and Clang on Ubuntu and Clang on macOS at `-O2`. Direct x86-64 executable tests run on Linux and are skipped on the non-x86-64-Linux direct-target configuration.

The central architecture rule remains intact:

> Target platforms implement Eristavi semantics; they do not redefine them.

## 2. Current compiler architecture

The implementation now has a meaningful split between high-level semantic representation and direct-backend representation:

```text
Eristavi source
    ↓
lexer / parser / AST
    ↓
name resolution + semantic analysis + type inference
    ↓                         ↘
bootstrap runtime             typed/source-close Eristavi IR
                                  ├─→ C11 backend → C compiler → executable
                                  ↓
                               Universal IR
                                  ↓
                               x86-64 backend
                                  ↓
                               assembly → assembler/linker → executable
```

This is important because generated C is no longer the only proof of native execution architecture.

The C path remains broader; the direct path is intentionally smaller and is now a correctness/architecture foundation rather than a parity claim.

## 3. Frontend and bootstrap runtime

The frontend/runtime continue to cover the principal frozen pre-0.1 surface:

- exact 28-keyword lexical vocabulary;
- Unicode identifiers with NFC identity;
- Int, Float, Bool and Text;
- explicit Unicode Text views;
- `let` and transitive `fixed`;
- lexical scopes and no-shadowing;
- `if / else`, `while`, stable `for`;
- functions, recursion and result inference;
- inferred generic relationships;
- Lists with value semantics;
- ordinary user-defined values and structural equality;
- `maybe` / `none` and flow narrowing;
- explicit managed identity;
- checked errors and propagation;
- deterministic resources;
- modules/imports and visibility.

No new grammar was introduced for the architecture work in this audit.

## 4. Serialized module interfaces

### Implemented

The compiler now emits deterministic versioned module metadata:

```text
*.eri-interface.json
```

through:

```text
erist interface module.eri
```

The current bootstrap schema is:

```text
schema  = eristavi.module-interface
version = 1
```

The interface records:

- module identity;
- required Unicode version;
- dependency identities;
- type/error field metadata required for static semantics;
- public visibility;
- public function contracts;
- inferred generic relationships and operation constraints;
- return relationships;
- checked `fails` contracts.

The canonical JSON form is deterministic and can be SHA-256-digested.

### Verified source independence

Tests now remove an imported module's `.eri` source after generating its interface and successfully type-check the importer from metadata alone.

This includes:

- construction of imported public value types;
- inferred generic function relationships such as `(T) -> T`;
- checked imported error contracts;
- enforcement that private functions remain unavailable.

### Remaining module-artifact boundary

An interface is a type-checking/contract artifact, **not yet executable object code**.

Generated-C builds and direct builds still require implementation source for linked modules. The next production step is therefore implementation/object artifacts paired with the interface, not more source-language syntax.

## 5. Unicode 17 and compiled `text.characters`

The previous audit's largest Text-view parity gap is closed.

The generated-C runtime now implements:

```eri
text.characters
text.scalars
text.bytes
```

including `.count` and checked indexing.

### Grapheme strategy

The compiled character view does not use C locales, `wchar_t`, OS character APIs, or code-point approximation.

At compiler/runtime-generation time, Eristavi derives compact property ranges from the pinned Unicode-aware dependency and embeds target runtime tables for the properties needed by extended grapheme segmentation, including:

- Grapheme_Cluster_Break categories;
- Indic Conjunct Break categories;
- Extended_Pictographic.

The C runtime implements the relevant Unicode grapheme rules for:

- controls/CR/LF;
- Hangul clusters;
- Extend/ZWJ/SpacingMark/Prepend;
- Indic conjunct sequences;
- Extended_Pictographic ZWJ sequences;
- Regional Indicator pairing.

Tests exercise combining marks, ZWJ emoji, flags, Indic conjuncts, stored character views, bounds faults, Hangul/emoji cases and a corpus whose native counts are cross-checked against the pinned bootstrap segmentation.

### Audit caution

This is strong implementation evidence, not a claim that the current tests exhaust the complete Unicode GraphemeBreakTest corpus. A production conformance phase should ingest the official pinned Unicode test vectors as an automated fixture rather than relying only on selected/corpus tests.

## 6. Text representation and file boundaries

The previous length-aware Text fix remains intact.

Compiled `Text` is represented by explicit UTF-8 bytes plus length, so:

- embedded NUL survives output, equality and concatenation;
- List/identity/error Text fields do not become C-string values;
- file writes use exact Text length;
- `readText()` validates UTF-8;
- invalid UTF-8 remains checked `std.files.FileError`;
- paths containing embedded NUL fail through the checked file-error channel instead of truncating at a C boundary.

The new grapheme implementation operates over this same length-aware representation.

## 7. Universal IR

A lower machine-independent IR is now implemented separately from the source-close typed IR.

The first Universal IR slice has:

- explicit basic blocks;
- typed virtual values;
- local slots;
- explicit jumps, branches and returns;
- checked signed-64-bit arithmetic operations;
- comparison operations;
- Boolean operations;
- primitive Int/Bool output operations.

The current direct slice lowers:

- Int/Bool declarations and assignment;
- checked `+ - * / %` and unary `-` for Int;
- comparisons;
- Boolean negation;
- `if / else`;
- `while`;
- Int/Bool output.

Unsupported high-level operations fail lowering explicitly instead of acquiring target-specific semantics.

### Important maturity boundary

Universal IR is **not yet feature-parity IR**.

It does not yet model the full pre-0.1 implementation surface such as:

- ordinary function calls/ABI;
- Float;
- Text values;
- Lists and aggregates;
- maybe/identity;
- checked-failure control-flow edges;
- resources/cleanup;
- GC/runtime ownership operations.

The existing typed-IR/C route remains the broad backend while Universal IR grows deliberately.

## 8. First direct CPU backend

The first executable direct target is **x86-64 Linux / System V**.

The path is:

```text
Eristavi
  ↓
typed IR
  ↓
Universal IR
  ↓
x86-64 assembly
  ↓
system assembler/linker
  ↓
executable
```

Generated C is not involved.

### Verified direct behavior

Direct executable tests cover:

- hello/arithmetic output;
- Int/Bool locals;
- `if / else` and `while`;
- signed integer division truncating toward zero;
- signed remainder relation;
- checked overflow fault;
- division-by-zero fault.

The backend uses a deliberately simple stack-spill strategy for virtual values and libc calls for bootstrap output. These are backend implementation choices, not source-language semantics.

### Why x86-64 first

The language architecture had intentionally left the first CPU backend unfrozen. x86-64 Linux was selected because the current CI can assemble, link and execute the generated code immediately.

This does not change the portable architecture. ARM64 should be implemented against the same Universal-IR contract rather than through a separate semantic path.

## 9. Standard-library/runtime growth

The standard library remains deliberately small, but `std.files` now goes beyond owned file resources.

In addition to `open`, resource `readText()` and `writeText()`, the compiler/runtime now implement:

```eri
files.exists(path)
files.remove(path)
```

Both operations use checked `files.FileError` contracts for invalid/OS-error paths.

`exists` returns `false` for an ordinary nonexistent target but does not collapse other path/OS errors into `false`.

`remove` reports a missing target as a checked failure rather than silent success.

Both bootstrap execution and generated-C/native execution are tested.

This demonstrates the intended library-first growth model without adding keywords.

## 10. Generated-C backend status

The generated-C route remains the broadest compiled backend and currently has executable coverage across:

- Int, Float, Bool and length-aware UTF-8 Text;
- checked Int arithmetic;
- Text equality/concatenation;
- all three Unicode Text views;
- functions/recursion/control flow;
- Lists and stable iteration;
- ordinary values and structural equality;
- maybe/none;
- identity;
- checked failures;
- inferred generic specializations;
- imported modules;
- deterministic resources;
- exact Text file I/O;
- checked file existence/removal.

C remains a portability backend, not Eristavi's semantic definition.

## 11. Float conformance

The generated-C/native suite continues to test:

- NaN equality behavior;
- IEEE infinities;
- signed zero;
- smallest subnormal preservation;
- overflow to infinity.

The CI matrix uses:

- GCC on Ubuntu;
- Clang on Ubuntu;
- Clang on macOS;

with `-O2`.

This is good bootstrap evidence, but ARM64, Windows/MSVC, RISC-V and broader floating-point environment coverage are still future conformance work.

## 12. Test status

The verified suite contains:

```text
174 tests
```

It includes:

- positive and negative frontend semantics;
- bootstrap runtime behavior;
- project/module loading;
- versioned module-interface round trips;
- source-independent interface type checking;
- generated-C/native execution;
- Unicode 17 identifier and Text-view behavior;
- compiled grapheme segmentation;
- length-aware Text and UTF-8 file behavior;
- deterministic resources;
- inferred generics;
- Float edge cases;
- std.files path operations;
- Universal-IR structural checks;
- real direct x86-64 executable tests.

The full suite passes in all three CI jobs. Direct x86-64 executable tests are active on the Linux jobs and skipped where the target cannot execute natively.

## 13. Audit findings and corrections

This implementation phase exposed or confirmed several useful quality points:

- live analyzer objects are no longer the only module-contract representation;
- inferred generics can cross a serialized interface boundary without adding source generic syntax;
- compiled grapheme behavior can be pinned without delegating to host locale character APIs;
- target-neutral checked arithmetic can be represented below the source-close IR;
- direct x86-64 checked overflow/division faults match Eristavi rather than raw CPU wrapping/trapping accidents;
- standard-library growth does not require keyword growth;
- a stale README example attempted to name a function `identity`, but `identity` is a reserved keyword; the example has been corrected to `preserve`.

Earlier quality fixes remain in force: length-aware Text, content equality, UTF-8 validation, Unicode identifier mangling, Int-only `%`, deep `fixed`, value semantics and multi-compiler CI.

## 14. Remaining implementation gaps

The major remaining work is now narrower and better separated by layer.

### A. Module implementation artifacts

Interfaces are implemented; compiled implementation/object artifacts and dependency linkage are not.

### B. Universal-IR parity

Functions/ABI, Float, Text, aggregates, Lists, optionals, identities, checked failure edges, deterministic cleanup and runtime/GC primitives still need lower-IR representations.

### C. Direct backend parity

The x86-64 backend currently covers the first scalar/control slice. It is not yet a replacement for the C backend.

### D. Additional direct architectures

ARM64 is the logical next CPU backend after Universal IR expands enough to prove a second architecture against the same semantics.

### E. Broader platform CI

Windows/MSVC, native ARM64 and RISC-V are not yet automated.

### F. Standard library

JSON, paths as a richer abstraction, time, networking, process/environment APIs and broader numeric utilities remain future library work.

### G. Unicode conformance corpus

The compiled grapheme runtime should eventually run the complete official test vectors for the pinned Unicode version.

## 15. Deliberately postponed — not defects

The audit still does not classify these as pre-0.1 implementation defects:

- explicit generic syntax/constraints;
- traits/interfaces;
- pattern matching;
- async/await and advanced concurrency;
- reflection/macros;
- identity-to-value snapshot API;
- advanced resource transfer/borrowing/lifetime syntax;
- package registry/version/lockfile design;
- advanced garbage collectors;
- stable portable bytecode/JIT;
- self-hosting;
- multiple feature-complete direct CPU backends.

## 16. Audit conclusion

The five requested engineering areas have all moved from roadmap items to working implementation milestones.

The strongest architectural change is that Eristavi now demonstrates **two independent native routes**:

```text
typed IR → C → native
```

and, for the first bounded scalar/control slice:

```text
typed IR → Universal IR → x86-64 assembly → native
```

At the same time, module contracts can survive serialization independently of implementation source, and Unicode grapheme semantics now survive compiled execution without host-locale approximation.

No language redesign was required.

> **Audit verdict:** Eristavi is now a broad pre-0.1 bootstrap compiler with a frozen source language, serialized module interfaces, complete compiled explicit Text-view support, a target-neutral lower-IR foundation, a tested first direct x86-64 backend, expanding standard-library facilities, and a 174-test multi-toolchain conformance suite. The next phase is primarily about widening Universal-IR/direct-backend parity and producing linkable compiled module artifacts—not inventing more language syntax.
