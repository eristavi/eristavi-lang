# First real freestanding scalar Eristavi application

> **Status: stacked runtime-independence review candidate; Linux x86-64 only**

This slice proves that the compiler/runtime work is no longer limited to synthetic
assembly probes. An ordinary `.eri` source file is compiled through Eristavi's own
frontend, semantic analysis, typed/Universal IR and x86-64 emitter, then linked
against only the Eristavi-emitted freestanding scalar runtime.

No public Eristavi syntax, grammar, type-system rule, ownership model or design
philosophy is changed.

## Application

`examples/freestanding_scalar_application.eri` is ordinary Eristavi source:

```eri
let first be 40;
let second be 2;
output(first + second);
output(first < second);
```

Its required output is:

```text
42
false
```

## Compiler path exercised

The focused test builds `src/frontend.eri` and invokes its existing `emit-asm`
command on the real example file. The application therefore passes through the
Eristavi-source compiler modules rather than a handwritten test emitter:

```text
.eri source
  -> Eristavi lexer
  -> Eristavi parser
  -> Eristavi semantic analysis
  -> typed IR
  -> verified/optimized Universal IR
  -> Eristavi x86-64 emitter
  -> application assembly
```

The emitted application uses the existing native helper ABI, including scopes,
root binding, scalar values/operators and output.

## Freestanding runtime path

The application assembly is combined with Eristavi-emitted runtime source only:

```text
Linux syscall boundary
  -> verified allocator / reservation-aware free list
  -> checked Int/Bool engine
  -> libc-free runtime faults
  -> 32-byte scalar ev_value ABI
  -> slot/scope lifetime ABI
  -> Int/Bool output
  -> syscall-only _start / exit
```

The scalar `evn_output` subset preserves the current visible formatting contract:

- Int: signed decimal plus one newline;
- Bool: `true` or `false` plus one newline.

Int formatting handles the full signed 64-bit range without C formatting helpers.
Writes use the project-owned Linux `write` syscall loop.

## Validation

The final focused Ubuntu x86-64 run executed ten cumulative runtime-independence
tests successfully, including the real application proof.

For the final application binary the test verifies:

- `ld -nostdlib -static` linking succeeds;
- no ELF interpreter;
- no dynamic section;
- non-executable stack;
- no unresolved symbols;
- no libc `write`/`exit` runtime dependency;
- execution with an unusable `PATH` succeeds;
- stdout is exactly `42\nfalse\n`;
- stderr is empty;
- exit status is zero.

## Dependency boundary

This milestone is deliberately stated narrowly.

The **generated application target** does not link `runtime/value_runtime.c`,
`runtime/native_gc_runtime.c`, libc, libm, CRT startup objects or a dynamic loader.

However, during this transition the `frontend.eri` compiler executable and the
small runtime-source emitter are still built using the previously qualified
bootstrap toolchain. GNU `as` and `ld` are also still the explicit assembly/link
boundary.

Therefore this is the first C-free **application runtime path**, not yet a fully
independent compiler rebuild.

## Next boundary

The scalar path is now coherent enough to stop expanding it horizontally. The next
value-runtime work should migrate Text storage/UTF-8 behavior and its managed
allocation rules, because Text is the first major heap-backed ordinary value family
needed by realistic programs and by the compiler itself. The existing Unicode
contract and pinned tables must be preserved exactly; no public language shortcut
should be introduced for the runtime port.
