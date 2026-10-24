# Eristavi Direct Backends

> **Status: x86-64 broad bootstrap backend; ARM64 expanded assembly backend**

Direct backends consume Eristavi Universal IR and emit CPU assembly without generated C.

## x86-64 Linux / System V

The direct x86-64 backend currently supports a broad pre-0.1 execution slice:

- Int, Bool, Float and length-aware UTF-8 Text;
- `.bytes`, `.scalars`, and pinned Unicode-17 `.characters` views;
- functions, recursion, register arguments and stack-passed arguments;
- checked signed-64-bit arithmetic and defined division/remainder faults;
- conditions, loops and short-circuit Boolean control flow;
- deep ordinary value semantics for nominal values and Lists;
- structural equality;
- maybe/none;
- shared identity semantics;
- inferred source generic specializations;
- source-independent inferred-generic specialization from module-object templates;
- checked errors and handler dispatch;
- deterministic `std.files` resources, UTF-8 validation and path operations;
- source-independent linking from `.eri-interface.json` + `.eri-object.json`.

The system compiler driver is currently used as assembler/linker. Generated C is not involved.

### Automatic memory management

The current direct runtime now has a non-moving mark-and-sweep bootstrap collector.

Compiler-emitted root frames contain addresses of:

- heap-typed declared locals;
- heap-typed Universal-IR temporary spill slots;
- checked-error globals maintained outside ordinary local scope.

This fixed the main correctness risk of collecting a temporary aggregate between construction and its next use. GC stress tests exercise repeated heap replacement and nested List/value graphs.

The collector is **not yet the final production precise collector**. Root slots are compiler-described, but heap child discovery still scans tracked payload words and treats only exact tracked allocation pointers as references. Typed heap descriptor masks and shorter liveness-based root ranges remain future hardening work.

Deterministic non-memory resources remain outside GC ownership.

### Unicode Text views

Direct Text views no longer fall back to generated C. Native runtime assembly implements byte/scalar access and Unicode-17 extended grapheme segmentation using generated property tables derived from the pinned toolchain data.

### Output ordering

Text output uses exact-length raw writes so embedded NUL remains valid. Scalar output currently uses stdio. The composed direct backend flushes buffered stdio before raw Text writes so mixed `output(...)` calls preserve source order.

### Checked failures and resources

Checked errors are explicit Universal-IR state/CFG operations rather than target exceptions. Resource cleanup failures encountered while another failure is active remain secondary runtime context instead of replacing the primary failure.

## ARM64 Linux / AAPCS64

ARM64 uses the same Universal IR rather than a separate semantic lowering.

Current assembly-generation coverage includes:

- Int, Bool and Float;
- functions/calls/recursion;
- AAPCS64 register and stack argument placement;
- checked Int arithmetic/division/remainder;
- comparisons and control flow;
- Text runtime operations;
- nominal values, Lists, maybe and identity operations;
- checked-error state/handler operations;
- deterministic file-resource runtime operations and secondary-failure state.

CI cross-assembles the expanded runtime output. A native ARM64 execution test exists for matching ARM64 Linux hosts, but current hosted CI does not provide broad native ARM64 Linux behavioral coverage. Cross-assembly therefore proves code-generation validity, not complete runtime parity.

## Commands

```text
erist uir app.eri -o app.uir

erist build-asm app.eri -o app.s --target x86_64-linux
erist build-direct app.eri -o app --target x86_64-linux
erist link-direct app.eri -o app --target x86_64-linux

erist build-asm app.eri -o app-aarch64.s --target arm64-linux
```

`build-direct`/`link-direct` link only on a host matching the requested Linux architecture. Cross-assembly emission is available independently through `build-asm`.

## Current direct-backend boundary

The next direct-backend work is principally production hardening:

- typed heap descriptors and improved GC precision/liveness;
- native ARM64 Linux CI and behavioral parity verification;
- better stack-slot reuse and real register allocation;
- broader OS/ABI targets;
- wider standard-library runtime support.

These are compiler/runtime engineering tasks and do not require new source-language syntax.
