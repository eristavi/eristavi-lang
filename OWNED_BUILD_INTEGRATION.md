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

CI #379 passed the four-platform suite, all three Linux bootstrap self-build/
offline gates and owned integration for PR #37. Expensive gates now live in the
explicit completed-batch qualification workflow; ordinary CI keeps the full
four-platform test suite. See `CI_QUALIFICATION.md` for selection and final-revision
requirements. Owned integration still records `repeatable: false`.

Temporary-slot pruning now builds a nonowning, open-addressed set of exact
class-1 root keys and scope boundaries before scanning the slot chain. Duplicate,
null and stale keys are safe: keys are compared without dereferencing them. Pending
results and active handler boundaries retain their existing pins; unbound scopes
still suppress pruning. Maps are rebuilt at each pass so overwritten roots do not
remain live. Scratch uses a separate zero-filled reservation and is released at
the end of the pass; reservation failure falls back to the original linear search.
Using the value allocator for this scratch regressed the compiler probe and was
rejected because it polluted the reusable-block chain.

The previous probe counted roughly 643 million root-membership comparisons.
Qualification now checks a 1,024-entry mixed-class map with duplicates and invalid
keys, changed roots, nested scope marks, bounded membership probes and matched
scratch reservations/releases. The same survivor expectations run with scratch
reservation forced to fail. Existing graph/resource checks also cross-check the
slot counter against the independent slot chain.

A before/after token-report probe used identical compiler-B assembly and input
files, changing only the linked owned runtime. Three alternating runs per size on
this Linux x86-64 host produced these wall-time medians; output bytes matched in
every run. This includes token-report formatting and is not a pure lexer or full
compiler benchmark.

| Declarations | Before | Indexed roots | Reduction |
| --- | --- | --- | --- |
| 200 | 1.898 s | 1.143 s | 40% |
| 400 | 4.445 s | 2.715 s | 39% |
| 800 | 11.756 s | 7.173 s | 39% |

The local completed-batch run passed 25 Text/Unicode/Float/graph/resource/root/
allocation-failure tests. The tightened root probe additionally verifies that
successful scratch reservations occur and have matching releases. Hosted results
belong to the final PR revision, not to these local timings.

Small Text buffers remain unpooled and are the next allocation cost to profile.
Another full owned compiler rebuild remains deferred until compiler throughput
justifies its cost; this batch does not change the 900-second qualification limit
or claim repeated owned self-build success.

Bootstrap creation still requires Python and a C toolchain. GNU as/ld and the shell
wrapper remain external tools with their own host dependencies. C export keeps its
bootstrap runtime asset. Native machine-code encoding, ELF object writing, an owned
linker and independent ARM64/Windows/macOS runtime ports remain future work.
Canonical paths currently require Linux procfs. Structural equality remains recursive.
