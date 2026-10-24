# Eristavi Direct Backends

> **Status: broad x86-64 bootstrap backend with initial physical register allocation; native-tested ARM64 runtime backend**

Direct backends consume Eristavi Universal IR and emit CPU assembly without generated C.

## x86-64 Linux / System V

The direct x86-64 backend executes a broad pre-0.1 surface:

- Int, Bool, Float and length-aware UTF-8 Text;
- `.bytes`, `.scalars`, and pinned Unicode-17 `.characters` views;
- functions, recursion, register and stack-passed arguments;
- checked signed-64-bit arithmetic/division/remainder faults;
- conditions, loops and short-circuit Boolean control flow;
- deep ordinary value semantics for nominal values and Lists;
- structural equality;
- maybe/none;
- shared identity semantics;
- source and object-template inferred-generic specialization;
- checked errors and handler dispatch;
- deterministic `std.files` resources, UTF-8 validation and path operations;
- source-independent linking from `.eri-interface.json` + `.eri-object.json`.

Generated C is not involved. The system compiler driver is currently used as assembler/linker.

### Automatic memory management

The current x86-64 runtime uses a non-moving mark-and-sweep bootstrap collector.

Compiler root frames contain heap-typed declared locals plus only those heap-typed Universal-IR temporary values whose CFG liveness proves that they cross a GC safe point. Each root entry pairs a stable stack address with a static type descriptor.

Typed heap traversal currently understands:

- Text and Text-view leaves;
- nominal fields using their declared layouts;
- List backing storage and typed elements;
- maybe and identity wrappers;
- current deterministic file-resource records.

Dynamic checked-error state retains a conservative fallback that follows only exact tracked-allocation pointers. This is safer than scanning arbitrary addresses but remains bootstrap infrastructure rather than a final concurrent/generational collector.

Scalar Universal-IR temporaries use CFG-aware interference-based spill-slot coloring, so non-overlapping values may reuse stack storage. Heap temporary slots remain pinned and unique whenever they participate in GC root metadata.

Deterministic non-memory resources remain outside GC ownership.

### Physical register allocation

The x86-64 backend now has an initial verified physical-register allocation path layered beneath the checked-error/resource/direct/GC composition.

The first allocator slice is deliberately conservative:

- eligible short-lived Int/Bool values may remain in a caller-saved GP register;
- eligible short-lived Float values may remain in a caller-saved XMM register;
- CFG interference prevents simultaneously live virtual values from sharing the same physical register;
- only scalar lowering operations explicitly known to be call-free currently produce register-resident values;
- values that must survive helper, PLT or GC clobbers remain stack-backed;
- operands of complex lowerings also remain stack-backed because those lowerings may call helpers before every source operand has been consumed;
- scalar values extracted through higher-level aggregate/List/error operations remain spilled until those machine lowerings have explicit use/clobber contracts;
- stack slots remain the correctness fallback.

This establishes a real register-resident execution path without weakening the System V ABI or precise-GC rooting contract. It is not yet a mature whole-function allocator. The next work is explicit machine-level use/clobber metadata, a broader safe register pool, better move/coalescing decisions and compaction of spill slots that are no longer necessary.

### Unicode Text views

Direct Text views do not fall back to generated C. Native runtime assembly implements byte/scalar access and Unicode-17 extended grapheme segmentation using pinned generated Unicode property data.

CI additionally runs the official Unicode-17 `GraphemeBreakTest` corpus against the pinned reference segmenter.

### Checked failures and resources

Checked errors are explicit Universal-IR state/CFG operations rather than target exceptions. Resource cleanup failures encountered while another failure is active remain secondary runtime context rather than replacing the primary failure.

## ARM64 Linux / AAPCS64

ARM64 consumes the same Universal IR rather than a parallel semantic lowering.

The composed direct backend covers:

- Int, Bool and Float;
- functions/calls/recursion and AAPCS64 register/stack arguments;
- checked Int arithmetic/division/remainder;
- comparisons and control flow;
- length-aware Text operations;
- nominal values, Lists, maybe and identity;
- checked-error state/handler operations;
- deterministic file resources and secondary-failure state.

Hosted CI includes a native ARM64 Ubuntu runner. Native behavioral tests execute Text, ordinary values, Lists, maybe/identity, checked errors and exact UTF-8 file-resource round trips. Cross-assembly tests remain as an additional structural check.

Mixed scalar/Text output uses the same ordering contract as x86-64: stdio is flushed before exact-length raw Text writes.

ARM64 automatic heap reclamation and direct explicit Text-view parity are still incomplete relative to x86-64.

## Commands

```text
erist uir app.eri -o app.uir

erist build-asm app.eri -o app.s --target x86_64-linux
erist build-direct app.eri -o app --target x86_64-linux
erist link-direct app.eri -o app --target x86_64-linux

erist build-asm app.eri -o app-aarch64.s --target arm64-linux
erist build-direct app.eri -o app-aarch64 --target arm64-linux
```

`build-direct`/`link-direct` require a host matching the requested Linux architecture. Cross-assembly emission remains available independently through `build-asm`.

## Remaining direct-backend boundary

The next work is production hardening rather than source-language redesign:

- ARM64 automatic memory management and explicit Text-view parity;
- tighter dynamic-error descriptor coverage and shorter x86 GC root lifetimes;
- x86 register-allocation maturation: explicit lowering clobber contracts, broader register pools and dead-spill/frame compaction;
- additional OS/ABI targets;
- broader standard-library runtime support.

These are compiler/runtime engineering tasks and do not require new Eristavi syntax.
