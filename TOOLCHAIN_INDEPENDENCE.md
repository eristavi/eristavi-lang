# Toolchain independence audit and execution plan

Status: dependency audit completed against main `7792cb426866627f8b211c0ff2e5771291e22452`.
This is an implementation plan, not an implemented C-free runtime or a language
specification amendment. The governing philosophy and frozen semantics remain intact.

## What independence means

Normal offline application builds already need neither Python nor a C compiler.
Complete project-owned toolchain independence means a previous Eristavi binary can
rebuild the compiler, runtime, build driver, instruction encoder and linker from
Eristavi source without Python, C compilation, C-generated runtime sources or GNU
assembler/linker binaries. A trusted seed compiler remains necessary; bootstrap
independence does not mean creating an executable from no executable tools.

The strict target also removes libc, libm and CRT startup objects from our runtime
and build chain. Calling an OS API through its documented binary ABI is permitted;
that does not require writing or compiling C. OS kernels and platform services are
outside the project-owned source boundary. Any remaining system-library dependency
must be declared explicitly rather than described as full independence.

An optional Python reference implementation can remain for differential testing.
It must not participate in the claimed independent rebuild. External validation
may inspect evidence, but cannot secretly generate required build products.

## Current dependency inventory

| Component | Evidence in repository | Dependency and replacement |
| --- | --- | --- |
| Frontend and native consumers | `src/frontend.eri`, `src/compiler/` | Eristavi source already exists; preserve its contracts and reproducibility. |
| Bootstrap/reference compiler | `compiler/erist/`, `pyproject.toml` | Python, regex and unicodedata2; retain as optional oracle after replacing required bootstrap operations. |
| Native value runtime | `runtime/value_runtime.c` | C allocation, Text, numeric, file/process and checked-failure helpers; replace by independently bootstrappable Eristavi runtime modules. |
| Native heap collector | `runtime/native_gc_runtime.c` | C registry, typed traversal, weak indexes and sweep; port after the allocator and root ABI are independently expressible. |
| Runtime-source accessor | `src/compiler/value_runtime.eri` | Reads the C asset; it is not an Eristavi implementation of that asset. |
| Earlier scalar runtime | `src/compiler/scalar_runtime.eri` | Returns C source as Text; emitting C from Eristavi does not remove the dependency. |
| Build and package driver | `tools/build_offline.py` | Python plus C compilation, dependency discovery and package assembly; replace required release operations with an Eristavi driver. |
| Application command wrapper | shell wrapper in `tools/build_offline.py` | POSIX shell/utilities and bundled `as`/`ld`; replace with native Eristavi command dispatch and process/platform services. |
| Startup and numeric/system services | includes and calls in `runtime/value_runtime.c`; startup/library inventory in `tools/build_offline.py` | CRT, libc/libm, loader ABI, stdio, strtod, fenv, malloc/free, setjmp/longjmp and paths; each needs an explicit implementation or declared OS boundary. |
| Unicode data generation | `compiler/erist/unicode_*`, pinned Python dependencies | Existing runtime tables are embedded; remove Python from required regeneration with a pinned input/table-generator workflow written in Eristavi. |
| Machine-code/object/link stage | emitted assembly and GNU tools in offline bundle | Implement encoding, ELF/COFF objects, relocations, symbol resolution and executable layout in Eristavi. |
| Windows execution | not a qualified native target | Implement Windows x64 ABI, PE/COFF, imports, runtime adapter and native offline packaging. |

## Blocking dependency cycle

Ordinary Eristavi values currently depend on runtime allocation, representation and
helper calls. Rewriting malloc or the collector using those same values would call
back into the runtime being replaced. Existing `identity` is explicitly not a raw
pointer and cannot be repurposed as one. Checked signed Int must not silently become
an unchecked machine address or wrapping word.

The audited built-in surface (`compiler/erist/stdlib.py`) exposes files, Unicode
and process operations, not a freestanding memory/platform implementation API.
Simply translating C functions into ordinary Eristavi source cannot close this cycle.

Before runtime translation, specify a compiler-internal runtime implementation
profile in Universal IR. Proposed needs, not new public source syntax:

- explicit machine-word operations, widths and overflow behavior, separate from Int;
- opaque address/region operations with bounds, alignment and valid access contracts;
- unboxed scalar/layout operations that do not allocate ordinary managed values;
- stable internal symbols and platform-call conventions for runtime helper entries;
- platform memory reserve/commit/release and file/process boundary operations;
- verified root/safe-point registration that cannot collect unfinished values;
- a checked-failure transport mechanism without libc jump buffers;
- startup and Float behavior preserving the locked binary64 contract.

Each primitive needs a verifier rule and lowering for both native consumers. Do not
smuggle raw pointers, ownership annotations, unchecked Int or arbitrary foreign calls
into ordinary source programs. If the existing language cannot express the runtime
through restricted internal facilities, record a separate design decision before
changing source syntax. No spelling is approved by this audit.

## Ordered implementation milestones

| Stage | Concrete deliverable | Completion gate |
| --- | --- | --- |
| I0: baseline | Pin known-working compiler/runtime seed, source inventory, ABI calls and required tools. Keep unrelated feature drafts separate. | Exact seed/source hashes and reproducible current bundle evidence. |
| I1: freestanding foundation | Specify and implement private IR/runtime profile, unboxed layouts, allocator and a minimal Linux x86-64 startup/platform adapter. | Inspect emitted code/imports: no recursive managed allocation or old runtime dependency; focused allocation/alignment/failure cases pass. |
| I2: value runtime | Port checked numerics, Text/Unicode, values/identity, failures, resources and typed GC in dependency order. | Existing saved outputs, root/interior-reference/cycle cases, cleanup order, Float and Unicode conformance remain equal. No C source emitted or runtime C object linked. |
| I3: owned release driver | Eristavi command-line build/package driver, provenance, file protection and required Unicode-generation tooling. | Rebuild compiler/runtime/package from seed with Python/C compiler unavailable. GNU tools may remain temporarily, explicitly recorded. |
| I4: owned encoding/linking | x86-64 instruction encoding, ELF object writing, symbols/relocations and executable linking; then ARM64 equivalents. | Compare instruction/object behavior with established tools during development, then build/rebuild without those tools available. |
| I5: Windows x64 | Windows calling convention, unwind/error strategy, platform adapter, PE/COFF writer/linker/imports and native driver. | Cross-produced executables run on Windows; Windows-hosted offline compiler rebuilds itself. Cross-compilation alone is insufficient. |
| I6: independent release | Repeated compiler/runtime/driver/tool rebuilds on each claimed platform from a pinned previous Eristavi seed. | Isolated process/dependency audit proves no Python, C compiler/runtime objects, libc/libm/CRT or GNU tools enter the declared chain. Document remaining OS requirements. |

I1 is the next implementation milestone. It can begin against stable main while
Map/Bytes remains draft; new collection families need explicit runtime layouts and
tracing before joining the independent-runtime baseline. They must not force an
unqualified compiler into the seed chain.

Windows ABI/format design can proceed once the internal contracts are stable. The
first minimal proof should stay scoped to Linux x86-64, followed by ARM64 and the
Windows target. Do not add public language features to accelerate platform work.

## Runtime port order and invariants

1. Bootstrap-independent word/layout/platform primitives and allocation.
2. Checked scalar operations and required Float conversion/rounding behavior.
3. Text storage, UTF-8, pinned Unicode operations and formatting.
4. Ordinary values, Lists, explicit identity and any subsequently qualified collections.
5. Explicit checked-failure propagation and deterministic resource cleanup.
6. Typed roots, safe points, weak prefix metadata and managed reclamation.
7. Driver, startup, packaging and owned code/object/link tools.

Intermediate stages may use the previous qualified runtime as a comparison oracle,
but must list which helpers remain external. Ordinary value snapshots, explicit
shared identity, checked errors, transitive fixed, Unicode pinning and reverse-order
exactly-once resource cleanup are acceptance requirements, not migration options.

## Validation only after a coherent stage is implemented

Review contracts and dependency closure first, batch changes locally, and run focused
checks at the end of the stage. Run full repeated self-build/platform qualification
only after those checks pass. Do not repeat full builds for each runtime function.
Reuse successful evidence for unchanged source snapshots and retry infrastructure
failures individually. Never skip final semantic or platform validation to claim
independence. A renamed C object, C text embedded in an .eri file, generated C, or a
bundled Python interpreter fails the ownership/dependency gate.

For this audit-only change, final validation is limited to source-reference integrity,
review of dependency claims, unchanged frozen specifications and a clean diff. No
compiler implementation changed, so no compiler self-build is warranted.

## Scheduling

Do not assign a reliable completion date or effort percentage before the I1
freestanding proof. That proof determines whether the runtime can be expressed
without circular dependencies and provides a defensible basis for estimating I2-I6.
