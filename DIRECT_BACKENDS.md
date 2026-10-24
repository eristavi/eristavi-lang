# Eristavi Direct Backends

> **Status: x86-64 substantially implemented; ARM64 architecture slice implemented**

Direct backends consume Eristavi Universal IR and emit CPU assembly without generated C.

## x86-64 Linux / System V

The x86-64 backend currently supports a broad pre-0.1 execution slice:

- Int, Bool, Float and length-aware UTF-8 Text;
- functions, recursion, register arguments and stack spill arguments;
- checked signed-64-bit arithmetic and defined division/remainder faults;
- conditions, loops and short-circuit Boolean control flow;
- deep ordinary value semantics for nominal values and Lists;
- structural equality;
- maybe/none;
- shared identity semantics;
- inferred source generic specializations;
- checked errors and handler dispatch;
- deterministic `std.files` resources, UTF-8 validation and path operations;
- source-independent linking from `.eri-interface.json` + `.eri-object.json` for supported concrete implementations.

The backend currently uses libc/system runtime services for bootstrap allocation, formatted scalar output, file operations and process termination. CPU assembly generation itself is direct.

### Heap representation

Heap-backed direct values use explicit Universal-IR type information and runtime helpers. Ordinary value transfers invoke deep cloning where required; identity transfers preserve the shared handle.

This is intentionally correctness-first. Current direct allocations are not yet reclaimed by a production GC. Automatic memory management remains a language guarantee that the production direct runtime must implement before the direct backend is considered release-complete.

### Output ordering

Text output uses exact-length raw writes so embedded NUL remains valid. Scalar output currently uses stdio. The composed direct backend flushes buffered stdio before raw Text writes so mixed `output(...)` calls preserve source-program order.

### Checked failures

Checked errors are represented as explicit Universal-IR state and branches. The backend provides runtime storage for the current error and handler-visible captured views. Resource cleanup failures encountered while another failure is active are retained as secondary runtime context rather than replacing the primary failure.

## ARM64 Linux / AAPCS64

The ARM64 backend is deliberately based on the same Universal IR rather than a parallel semantic lowering.

Current coverage includes:

- Int, Bool and Float;
- functions/calls/recursion;
- AAPCS64 register and stack argument placement;
- checked Int arithmetic/division/remainder;
- comparisons and control flow;
- scalar output.

CI validates generated AArch64 assembly by cross-assembling it. A native ARM64 execution test exists and runs automatically when an ARM64 Linux runner is available.

The ARM64 backend does not yet implement the x86-64 heap-value, checked-error and resource runtime layers.

## Commands

```text
erist uir app.eri -o app.uir

erist build-asm app.eri -o app.s --target x86_64-linux
erist build-direct app.eri -o app --target x86_64-linux

erist build-asm app.eri -o app-aarch64.s --target arm64-linux
```

`build-direct` currently links only on a host matching the requested Linux architecture. Cross-assembly emission is available independently through `build-asm`.

## Current direct-backend boundary

The most important remaining work is:

- direct `.bytes`, `.scalars`, and `.characters` Text views;
- production automatic memory reclamation/GC;
- ARM64 parity for Text, aggregates, errors and resources;
- native ARM64 CI;
- additional OS/ABI targets;
- optimization/register allocation beyond the correctness-first stack-slot strategy;
- reusable precompiled inferred-generic implementation templates.

These are compiler/runtime engineering tasks. They do not require new source-language syntax.
