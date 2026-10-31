# U1a native Float, production import trust and source publication batch

Status: **qualified and merged through PR #96** on 31 October 2026.
Merge commit: `f5c3904e72009bf2c20051cb002772f75e20b98c`.
Exact tested head: `eec1dfee100be8c0f9b88a71a98b4866f36fab66`.
Tested/merged tree: `10fb3c388bea0f9f9bc6e6a5d26cc72867b475ce`.
[Four-platform CI](https://github.com/eristavi/eristavi-lang/actions/runs/41187461690)
and [completed-batch qualification](https://github.com/eristavi/eristavi-lang/actions/runs/41187461738)
passed at that exact head. The merge reused the passed evidence and triggered
zero workflows; no full tests were repeated for merging. Full owned compiler
self-build remains deliberately skipped/unqualified. The limitations below remain.

## Execution boundary

`src/compiler/u1_native.eri` accepts a session-local publication created from a
sealed linked UIR program and selected import policy. It freshly verifies all
bodies, effects and imports and compares exact owned table contents and binding
revisions before emitting a **private bootstrap C execution image**. The image
is not a public serialized UIR format or a replacement for the production
frontend. No source syntax, existing native ABI or default compiler path changes.
Mandatory scalar promotion remains required before canonical publication.

`runtime/u1_native.h` is the closed native execution adapter for that image.
It executes linked pred/i64/f64 instructions using bounded private native frames,
ordered zero/multiple returns and snapshot-before-assignment CFG arguments.
It preserves terminal-fault codes and the actual callee LocId, and supports
recursion, sparse switches, integer overflow pairs and unused-result faults.
Unsupported opcodes produce kind 3 at the instruction location; invalid native
entry/environment requests produce kind 4. It does not execute U1b/U2 operations.
There are no optimizer-supplied native callback pointers or guessed helper names.

This is a native **executor**, not a new machine-code generator/JIT or U3 frontend
integration. C is a bootstrap adapter in the existing bootstrap model. The UIR
builder, independent verifier, publication and simplifier are written in Eristavi.
The existing Eristavi reference evaluator keeps explicit unsupported Float results;
it is not silently replaced with native host arithmetic.

## Strict binary64

The x86-64 adapter establishes masked, round-to-nearest-ties-even MXCSR with
FTZ/DAZ clear, and performs separate SSE2 `addsd/subsd/mulsd/divsd` instructions.
AArch64 establishes FPCR/FPSR and uses separate scalar `fadd/fsub/fmul/fdiv`.
Every operation has one binary64 result. Inline machine instructions prevent
compiler contraction, reassociation or excess intermediates; fast-math compilation
is rejected. Negation flips the sign bit. Integer bit classification implements
all unordered NaN comparison results without signaling exceptions; arithmetic
NaNs are canonicalized because payloads/flags are not core observations.

The caller's control/status is saved and restored on normal, trap, cancellation,
fuel/depth and quota exits. Native execution and closed imported-call boundaries
check the required controls. Exception-status flags are not U1 observations.
No callback/foreign code can be introduced by a serialized import/effect hint.
The adapter currently supports x86-64 and AArch64; other architectures are refused.

## Production import catalog, version 1

| Adapter | Exact symbol | Signature | Effect mask | Native behavior |
| --- | --- | --- | --- | --- |
| 3 | `erist.u1.i64.identity` | `(i64) -> (i64)` | 0 | Return the exact incoming word |
| 4 | `erist.u1.i64.write` | `(i64) -> ()` | 20 | Write signed decimal plus newline to the selected FILE stream; a write refusal/error terminates with code 4 at the call site |

Mask 20 means external (4) plus terminal fault (16). The write adapter does not
promise flush/durability. Its FILE is provided by the embedding host; untrusted UIR
cannot inject a pointer. The selection checker requires the real imported
FunctionId, exact symbol bytes, signature, kind, version and effects. The emitted
image asserts the native runtime contract version. The two historical test-only
adapters are rejected by the native production emitter. This small catalog is
production trust for **these implementations**, not arbitrary dynamic FFI support.
The reference evaluator can execute adapter 3; adapter 4 is explicitly unsupported
there, rather than fabricating OS output or recording a fake test trace.

## Revisions, sources and diagnostics

`u1_publication.eri` holds an exact owned copy of every relevant metadata and
function table plus binding/signature/revision entries. Body copies are charged
to their function owner; shared metadata is charged to its metadata owner.
Publication never trusts a hash collision, old successful Report, unchanged
revision integer, builder state or serialized ready flag. Before emission it
re-runs independent verification/effect/import validation and exact comparisons.
A well-formed same-revision edit, source digest change, changed import version,
changed declaration/signature, table replacement or stale binding invalidates it.
Failed snapshot construction releases registered copies and retains request work
and allocation traffic. This is single-session ownership, not a cryptographic
capability against arbitrary memory writes by native C code.

Metadata now includes bounded ordered supplemental `(child,parent,role)` origin
links: shared value, call site, resource declaration and resource exit. Parents
must be earlier LocIds; duplicate links and cycles/forward links are rejected,
including unused origins. Supplemental sources may differ; the primary original
diagnostic anchor remains unchanged. Roles reserve future attribution without
implementing U2 cleanup or an inliner.

`native.sourceMap` emits a **private diagnostic-only map**. The bootstrap
`compiler/erist/u1_source_map.py` decoder checks schema/native contract, bounded
integer tables, exact logical name/digest/length against selected source revisions,
byte ranges and origin graphs. It remaps source IDs by complete logical identity,
with sparse external IDs stored in dictionaries, and retains compact byte span,
anchor, line/column and parent sets. Source SHA-256 is the content revision;
local source IDs and checkout paths are not persistent identity. Excerpts require
matching actual content bytes and SHA-256. No stale text is displayed.
Native trap locations and source/origin tables are ordinary required program data
and remain available after `strip`. Public UIR serialization, generic artifacts,
full symbolic debugging and universal memory/address provenance remain separate.

## Bounded canonical simplification

The simplifier validates the entire input, including dead CFG, then uses a private
promoted clone. It folds exact predicate logic/comparisons and wrapping i64
arithmetic when operands are known constants. It chooses only proven constant
branch/switch edges, rebuilds all edge/argument/case pools, then re-promotes and
reverifies to remove newly dead blocks and trivial parameters. The input is never
edited. Every changed output has a new revision; it must be rebound/published.

No call, guard, division/remainder, checked-overflow pair, Float arithmetic or
known runtime trap is folded/moved. In particular an earlier write cannot move
after a known zero-divisor trap, and distinct diagnostic sites are retained.
There is no inlining, speculative deletion of unused calls or unapproved rewrite.
All scans/constant arithmetic/pool allocations use existing work, capacity,
traffic and cancellation accounting; no quota is raised for this batch.

## Evidence and limits

`tests/test_u1_native.py` builds the actual Eristavi emitter and executes its
resulting native image. Its nine acceptance tests include:

- 525 input pairs / 6,300 Float observations against the independent existing
  integer/Fraction IEEE oracle, including random bit patterns, both signed zeros,
  signaling/quiet NaNs, infinities, subnormals, halfway ties and overflow;
- explicit non-FMA counterexample and hostile caller rounding/FTZ/DAZ state;
- 209 integer pairs with all six overflow pairs, wraps/div/rem and ten comparisons
  (6,061 integer/predicate observations) against unbounded mathematics;
- recursion and bounded negative recursion, zero-result local/imported calls,
  twelve-result native calls, sparse full-word switches, parallel-copy loops;
- exact first-write/fault ordering and callee origin, debug stripping, work,
  cancellation and native frame-capacity refusal; active frames release exactly;
- original/simplified output comparison over 45 independent inputs; same-revision,
  source/import revision rejection; cyclic unused origins; malformed dead CFG;
  cancelled simplification; publication quota cleanup and monotonic charges;
- diagnostic-map ingress/remap and stale-excerpt rejection; explicit rejection
  of fast-math and attempts to use test imports as production trust;
- deliberate host stdio FP-control corruption is rejected after the import,
  with caller state and native frame ownership still restored.

The focused integration smoke profile passes 20 tests locally, including all new
acceptance plus existing verifier, promotion, integer execution, runtime cleanup
and production frontend baseline checks. Full CI/qualification is a separate gate.

`docs/evidence/2026-10-31/u1-native-physical.json` records five fresh-process,
serialized original/simplified pairs with identical outputs, native frame bytes,
traffic, process peak RSS and timing. This is a matched direct-UIR native recipe,
not a whole-compiler speedup or complete physical Eristavi heap/GC qualification.
Local native ASan/UBSan checks cover frames, recursion and traps; local LSan task
inspection is disabled only for the container's `/proc` limitation. Hosted defaults
are unchanged. Full owned compiler self-build remains deliberately unselected.

Do not close all of #71/#77 based on a green scalar batch: broader matched UIR
stress/full physical heap/GC accounting and production frontend/artifact migration
retain their independent acceptance gates. Do not infer U1b/U2/U3 completion.
