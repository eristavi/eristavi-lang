# Eristavi-written compiler and offline native toolchain

> Experimental Linux native milestone. The frozen source-language contract and
> governing philosophy are unchanged. The developer/reference `erist` installed
> by pip remains Stage-0; the separately built offline bundle contains the
> Eristavi-written native compiler.

## Build and use

Bootstrap build requirements: Python with the pinned project dependencies, a C
compiler, GNU assembler/linker and matching Linux development/runtime files.
Supported native bundle hosts are x86-64 Linux and ARM64 Linux.

```sh
python -m pip install -e .
CFLAGS=-O2 python tools/build_offline.py --output /tmp/erist-offline
/tmp/erist-offline/bin/erist check examples/scalar_compilation.eri
/tmp/erist-offline/bin/erist build examples/scalar_compilation.eri -o /tmp/application
/tmp/application
```

The default packaging command verifies the repeated native self-build and runs a
build audit whose child PATH contains no usable Python or C compiler. A failed
repeatability or offline audit fails the packaging command. `--skip-self-build`
is a development-only option and records `repeatable: false`; it is not a promotion
or release build.

Normal bundle commands are:

```text
erist check SOURCE.eri [--source-root DIRECTORY]
erist build SOURCE.eri -o PROGRAM [--source-root DIRECTORY]
erist ir SOURCE.eri [-o REPORT.json] [--source-root DIRECTORY]
erist uir SOURCE.eri [-o REPORT.json] [--source-root DIRECTORY]
erist build-asm SOURCE.eri -o PROGRAM.s [--source-root DIRECTORY]
erist build-c SOURCE.eri -o PROGRAM.c [--source-root DIRECTORY]
erist version
```

`check` performs semantic checking in the bundle. The lower-level frontend command
`erist-compiler check` remains syntax-only for its existing inspection contract.
`build` emits native assembly, invokes the bundle's assembler and linker, and links
against its prebuilt runtime/startup objects. It does not emit C for the application
or invoke a C compiler. `build-c` remains an explicitly requested bootstrap/export
route; it requires a C compiler only if the user subsequently compiles that C.

Source roots default to the entry file's parent. Source module loading, aliases,
visibility and cycles use the Eristavi-written semantic loader. Paths with spaces
and Unicode are ordinary arguments. The bundle is relocatable on a compatible
host; it does not need the original repository or Python source tree for application
builds. Its standard process/file/Unicode runtime is part of the package.

The native compiler needs its compatible host dynamic loader/system runtime. The
wrapper uses a POSIX shell and ordinary OS utilities; assembler/linker tools and
necessary startup/runtime files are packaged. A failed compile/link preserves an
existing output executable. The wrapper rejects output that aliases the source
and replaces output symlinks rather than writing through them.

## Ownership and boundaries

The lexer, parser, semantic analyzer, type inference, structural typed IR,
independent typed verifier, Universal IR construction, independent CFG verifier,
unreachable-block pass, and x86-64/ARM64 instruction consumers are Eristavi source
under `src/compiler/`.

The native consumer emits real target instructions and direct function calls;
applications are not run by an AST/bytecode interpreter. This first native consumer
spills virtual registers and uses a boxed value runtime with a simple pointer ABI.
Scalar operation specialization, register allocation, heap optimization and native
runtime optimization remain performance work.

The shared runtime is still a **C bootstrap artifact**, compiled once while building
the bundle. It contains checked arithmetic, immutable Text, structural values,
Unicode-17 tables, process/file boundaries and checked-failure support. It is linked
as machine code during normal native builds. The assembler/linker are bundled GNU
tools, not Eristavi-written assembler/linker implementations. These facts are
explicit bootstrap/tooling boundaries, not source-language changes or hidden
conversions to another source language during normal application compilation.

The source loader consumes source modules. Stage-0's interface/object/cache ABI,
JavaScript/Wasm consumers, native macOS/Windows packaging, and production release
qualification are not promoted by this milestone. No claim of complete formal
semantic equivalence follows from a finite corpus or a successful self-build.
Stage-0 remains available as the independent reference and bootstrap.

## Values, optional state and failures

The executable slice now includes ordinary nominal values, inferred nested Lists,
field/index mutation, count/add/iteration, generic specialization across structural
types, `maybe`, explicit identity, Text views, checked failures/handlers/`try`,
source imports, and deterministic `with` resources. Ordinary values copy logically;
identity handles preserve aliasing. Fixed bindings/fields retain their existing
transitive restrictions. There is no new reference/pointer syntax or ownership
transfer rule.

Ordinary aggregate buffers are persistent: mutation copies the affected ordinary
path, while explicit identity mutates the shared identity payload. List append and
Text concatenation can extend only beyond an existing immutable prefix; older
values keep their original lengths and unchanged visible elements/bytes. Growth
allocates a new buffer, so aliases are not invalidated. Native temporary value slots
have scoped arenas; checked unwinding can reclaim skipped arenas when the enclosing
function exits. Object/Text buffers still use a process-lifetime bootstrap pool,
not a production tracing collector. Long-running allocation-heavy applications
need further memory/runtime qualification.

Native checked handlers release their frames on completion and immediately
restore abandoned call scopes/temporary slots on an exceptional pop. Both native
consumers initialize their spills and bind root maps derived from verified
register classes. Periodic slot collection preserves active value spills,
parameters and scope/handler boundaries, bounding temporary storage in ordinary
loops. General value/failure buffers remain process-owned. The explicit C export
retains its existing arena behavior; see PRODUCTION_HARDENING.md.

Optional extraction is a distinct IR operation requiring a proven local presence
fact. Presence comparisons inspect optional storage itself, including repeated loop
conditions after a cursor can become `none`. Stage-0 lowering was repaired to obey
that existing rule too. The compiler does not require source workarounds or weaken
the optional model to build itself.

Checked failures retain their declared nominal payload. Catch-all handlers expose
the guaranteed message. Cleanup runs once, in reverse nesting order, on successful
return and checked unwinding. A body failure stays primary; cleanup failures are
attached in order as secondary context. Without a body failure, the first reverse-
order cleanup failure becomes primary. Tests inject cleanup failures to check both
paths. Runtime defects remain separate from ordinary checked errors.

## Structural and Universal IR

The source-close typed IR retains type/effect facts, locations, field/local/function
IDs, explicit value/identity/maybe operations, mutation paths and cleanup scopes.
Structural types live in a separate type table; scalar IDs remain Int 1, Float 2,
Bool 3, Text 4 and no-value 5. Later IDs identify nominal/collection/optional/
identity/resource/view types. Nominal fields retain fixed flags and error types
retain their checked-error identity.

The typed verifier checks tree ownership/cycles, finite tables, types, scopes,
fixed stores, optional extraction, argument/result contracts, effect annotations,
handler coverage, resource ownership and cleanup failure contracts. Temporary cycle
marks are cleared on success and rejection. Both C and native paths verify first.

`universal_model.eri` and `universal_lower.eri` then produce explicit basic blocks,
virtual registers, instructions and terminators. Branches, loops, short-circuiting,
checked boundaries and cleanup are no longer source control statements. Register
classes describe values, integers, bytes, handler/failure state and arena scope;
they do not describe CPU registers. Portable runtime operations retain value,
arithmetic, failure and cleanup meaning behind the bootstrap runtime ABI.

The Universal verifier checks register classes, helper/program call signatures,
block successors, parameters and definite initialization on every reachable path.
Its must-analysis intersects predecessor masks and handles loops/catch edges.
Unreachable-block removal is independently verified before and after optimization.
The native consumers inspect Universal instructions/type metadata, not source ASTs.
`uir` emits `eristavi-universal-ir-v1` inspection JSON. This experimental internal
schema is not a frozen public bytecode/object ABI and is distinct from Stage-0's
existing serialized artifact format.

The initial consumers use System V x86-64 ELF and AArch64 ELF ABIs. Both save
incoming parameters before helper calls, preserve evaluation order, align calls,
support stack arguments and implement checked boundaries with the native jump
buffer ABI. Runtime layout is behind pointer-based helper calls; source values do
not gain address identity from this implementation choice.

## Self-build evidence

The packaging gate performs:

```text
Stage-0 C bootstrap executable
    -> Eristavi-emitted native compiler B
    -> Eristavi-emitted native compiler C
    -> next Eristavi-emitted native assembly
```

It requires identical native assembly across these emissions and identical B/C
binaries under the same assembler/linker/runtime recipe. It records a fixed source
manifest before the run and rejects changes during the gate. Generated assembly
is preserved under `evidence/` for diagnosis.

A qualified bundle records:

- `self-build.json`: assembly/binary hashes and the repeatability result;
- `source-manifest.json`: exact Eristavi/runtime source hashes;
- `build-toolchain.json`: bootstrap C compiler/flags and native target;
- `inventory.json`, `licenses/`: packaged tool/runtime provenance and notices;
- `offline-tests.json`: native execution with forbidden Python/C compiler shims,
  Unicode paths, source preservation and failed-build output preservation.

This is a private experimental host bundle, not a public redistribution/release
qualification of the bundled third-party tools.

## Regression evidence

The executable corpus contains 88 projects. It compares saved outputs with the
Eristavi-written C/native paths and the Stage-0 interpreter. Stage-0 C also runs
where its existing nested-mutation/identity-List lowering is available; three
projects explicitly record that reference-C limitation rather than silently
changing acceptance or skipping the interpreter comparison.

The semantic corpus independently freezes 175 accepted/rejected projects, and all
67 accepted projects are checked for executable lowering. Additional tests cover
sanitized arithmetic faults, malformed typed IR, malformed Universal calls/CFG/
classes/initialization, deterministic reports, cross-assembly for both ELF targets,
Float rounding/non-contraction, fixed/value/identity behavior, and checked cleanup
failure composition. The full suite contains 356 tests; hosted results and native
self-build audits are recorded on the change's CI run.
