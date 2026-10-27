# Owned runtime build/startup integration

The source language, semantic contracts, 32-byte value ABI and governing design
philosophy remain unchanged. PR #36 qualified owned resource/process services.
This batch connects that runtime to the Linux x86-64 offline builder.

```sh
CFLAGS=-O2 python tools/build_offline.py --runtime owned --skip-self-build --output /tmp/erist-owned
/tmp/erist-owned/bin/erist build examples/hello.eri -o /tmp/hello
```

`src/owned_runtime.eri` composes the complete value/resource runtime and `_start`.
Packaging bootstraps its emitter once, assembles the emitted runtime, then links
compiler B and application programs with `-nostdlib -static -e _start`. Neither
libc, the C runtime, CRT objects nor a dynamic loader is linked into those targets.
The ordinary qualified bootstrap runtime remains the default selection until
owned-runtime qualification and performance evidence justify promotion.
The command above creates a development bundle with `repeatable: false`.
Omit `--skip-self-build` only when running full owned repeatability qualification.

The repeated-build gate compares bootstrap/B/C assembly and B/C executable bytes
on a fixed source snapshot. It audits static executable headers, undefined symbols
and a non-executable stack, and runs the existing offline application audit with
Python/C compiler traps in PATH. `self-build.json` records runtime selection,
repeatability, hashes and compiler-emission durations. `--skip-self-build` is a
development option and must never be used as repeatability evidence.

## Compiler workload costs

Owned List append now grows backing geometrically and publishes immutable prefix
headers. Branches and indexed mutations retain existing value-copy semantics.
The collector prepares a sorted nonowning backing index before marking, replacing
full-registry scans at each interior-root lookup with validated binary search.
Tracing itself remains iterative and allocation-free. See `OWNED_GRAPH_RUNTIME.md`
for private layouts, retention behavior and the recursive-equality boundary.

Dirty graph traces are batched using a bounded adaptive safe-point budget; mutation
no longer forces a full collection at the next value helper. Explicit collection
and deterministic file cleanup remain immediate. A collection-count assertion
guards against returning to per-mutation full traces.

The runtime also maintains its exact temporary-slot count across construction,
pruning, scope exit and checked unwind. Safe points read that counter in constant
time. Qualification independently walks the slot chain and cross-checks the count
during graph/resource execution. The allocator caches the last successfully
validated free region to avoid restarting region lookup during grouped frees;
all existing checked metadata validation remains in place and release-all clears
the cache.

The Eristavi-written lexer advances an internal UTF-8 byte cursor, including its
BOM pre-scan, instead of repeatedly indexing scalar views from the start of a file.
Lookahead decodes validated UTF-8 and keeps source locations in Unicode scalars.
The existing valid/invalid Unicode, escape, BOM and numeric conformance corpus
checks the unchanged token and diagnostic contracts.

Qualification includes a 12,000-element growing List, a retained 2,000-element
snapshot, a branched append, indexed mutation and stable snapshot iteration.
Instrumentation bounds initialized/copied storage independently of machine speed;
the original quadratic prefix-copy path exceeds that bound. Existing deep-graph,
interior-root, failure, cleanup/OOM, Unicode and reclamation cases remain enabled.

## Module artifacts

Object-only linking now resolves missing generic specializations to a fixed point
from source calls, imported Universal IR and newly instantiated template bodies.
Private helpers and concrete inferred relationships are retained without duplicate
symbols. Fresh signature instantiation preserves caller relationships across
nested generic calls while keeping independent callers separate.

## Qualification status and remaining boundaries

The static owned compiler B passes the offline application audit: native builds
with Python/C compiler traps in PATH, 100,000 allocation-churn iterations, file
resources, identity values, checked errors, Unicode paths and preservation of
source/prior executable outputs. Static compiler/application headers have no
imports, dynamic loader or executable stack.

The final full compiler B-to-C emission exceeded the existing **900-second**
subprocess budget. Consequently repeated owned compiler self-builds are **not
qualified**, and the owned profile must not become the default. No timeout was
raised to turn an unfinished rebuild into a passing result. A small 200-declaration
token/report probe improved from approximately 10.3 seconds before the workload
optimizations to 1.8 seconds afterward on this host; that does not establish full
compiler throughput or a cross-machine benchmark.

Automatic CI adds one owned **integration-only** development bundle/audit, recording
`repeatable: false`. The original four-platform suite and three Linux bootstrap
self-build/offline gates remain enabled in full. Hosted qualification of the new
source head remains required before merging.

Further compiler-workload profiling should prioritize temporary-root membership
scans and independent small-Text allocations. Counter measurements on the small
probe found roughly 643 million root-membership comparisons; constant-time slot
counting removes a separate 496 million slot-list visits but does not fix that
membership cost. Small Text buffers remain unpooled. These costs need measured
improvement before another expensive owned compiler rebuild.

Bootstrap creation still requires Python and a C toolchain. GNU as/ld and the shell
wrapper remain external tools with their own host dependencies. C export keeps its
bootstrap runtime asset. Native machine-code encoding, ELF object writing, an owned
linker and independent ARM64/Windows/macOS runtime ports remain future work.
Canonical paths currently require Linux procfs. Structural equality remains recursive.
