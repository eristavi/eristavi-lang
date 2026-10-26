# First freestanding foundation slice

Implemented: `src/runtime/linux_x86_64.eri` emits private Linux x86-64 assembly
helpers for anonymous read/write page reservation, release and process termination.
`src/freestanding_probe.eri` is an Eristavi generator for an executable proof.
There is no public pointer API, new keyword, unchecked Int behavior or change to
ordinary value/resource semantics.

This is a first I1 platform-boundary slice, not the complete freestanding IR
profile, general allocator, runtime port or independent compiler. The generator
still runs on the existing bootstrap runtime. The generated probe uses no C
runtime, libc, libm, CRT startup objects or dynamic loader. Its final assembly and
link steps still use GNU tools. Assembly is emitted from Eristavi source; higher
level allocator and value-runtime logic has not been ported to Eristavi yet.

## Private machine ABI

- `erist_rt_reserve`: requested positive signed byte count in `rdi`; returns base
  in `rax` and mapped length in `rdx`. Invalid input or an OS error returns both
  zero. Requests round up to 4096-byte Linux x86-64 base pages. Overflow is rejected
  before addition; the largest accepted request is 2^63 - 4096. The mapping is
  private, anonymous, zero-filled and read/write without execute permission.
- `erist_rt_release`: base in `rdi`, exact mapped length in `rsi`; returns zero or
  the negative Linux error result in `rax`. This private boundary requires a
  matching live reservation; it is not a checked arbitrary-pointer interface.
- `erist_rt_exit`: process status in `rdi`, no return. The proof is single-threaded;
  this is not a language-level immediate-exit facility or a resource-unwind path.

Helpers preserve SysV AMD64 callee-saved registers. Syscalls clobber `rcx`, `r11`
and flags. These conventions are target-specific implementation data; they must
not be used to reinterpret ordinary Eristavi Int/identity values as addresses.

The probe exercises zero/negative/overflow requests, OS failure for an impossible
mapping, one-byte and multi-page requests, page rounding/alignment, zero-fill,
writable last-byte boundaries and successful release. It has a non-executable
stack and no unresolved imports or ELF interpreter.

## Use with the qualified offline toolchain

```sh
/path/to/bundle/bin/erist build src/freestanding_probe.eri --source-root src -o /tmp/erist-memory-generator
/tmp/erist-memory-generator > /tmp/erist-memory.s
as --64 /tmp/erist-memory.s -o /tmp/erist-memory.o
ld -nostdlib -static -e _start /tmp/erist-memory.o -o /tmp/erist-memory-probe
/tmp/erist-memory-probe
```

Success is exit status zero without output. A failed probe exits with status one.
Development validation may build the generator through Stage-0, but this does not
make the generated executable dependent on Python or a C runtime. The isolated
test inspects ELF headers/imports and executes the probe with an unavailable PATH.

## Next boundaries

Specify verified private word/region/layout operations, then use them to implement
an allocator with live-region bookkeeping, alignment, reuse and stable failure
behavior. Avoid implementing that allocator using managed values that recursively
call the allocator being replaced. Integrate startup and helper exports with
runtime-profile compilation before attempting the value runtime or collector.
ARM64 and Windows require separate platform adapters and execution qualification;
this proof does not claim their support. See the toolchain independence audit on
the `planning/toolchain-independence` branch for the complete dependency plan.
