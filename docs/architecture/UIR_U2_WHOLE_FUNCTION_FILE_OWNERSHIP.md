# Whole-Function File ownership and native roots — U2 development gate

Status: **partial, unqualified**; 7 November 2026. Implements an optional
owner-verified root emitter on [draft PR #121](https://github.com/eristavi/eristavi-lang/pull/121)
based on the active U2 draft PR #111. **Not the finished whole-Function File
lowering**. Do not merge this gate on architectural claims or mark #74 complete.

## Frozen meaning

The language-level `with` owner acquires exactly one noncopyable File, nested
resources close in reverse lexical order and a consumed handle is unavailable
on **both** checked outcomes. An ordinary return or checked failure cannot
silently bypass cleanup. An existing primary error remains primary; new close
failures form ordered secondary context. If cleanup fails on a pending success,
that success is cancelled. Terminal defects do not perform ordinary checked
unwinding. No resource handles may escape, become identities or be copied.

Canonical opcode 46/47 and the original frozen Function SSA and exact
fallible metadata remain the sole executable semantics. The existing
`u2_scoped_owners.verify` checks *every* original block, including dead blocks:
acquisition/consumption, single lexical owner, successor signature, source LocId,
unavailable result, and zero-owner normal/checked returns. Never infer resource
lifetime from ordinary SSA use-liveness; an owner with no subsequent read still
requires a strong GC root until its deterministic close.

## Selected bounded representation

The new private `u2_function_file_roots_x86_64.emit` first reruns the entire
canonical independent owner proof. It snapshots original owner signatures and
File.consume terminator operands before emitting assembly. It then generates:

- A class-1 File-root vector of `maxDepth` words to be bound to the caller's
  existing managed-runtime scope; all words initialized to zero first.
- A publication helper for **each original canonical block** (including dead
  blocks). The helper reads exactly the block's original lexical owner ValueId
  words from the Function SSA frame into its registered root slots and clears
  unused slots, refusing missing owner objects.
- A consumption helper for each verified checked File.close terminator. The
  helper checks the original consumed SSA word and its lexical root slot,
  clears both and never turns checked-failure into success. A caller may call
  it **only after** the real runtime cleanup has consumed that resource.

These are *helpers*, not an alternative CFG, special source syntax, another
collector or a new 32-byte ABI. The existing native compiler must still
ensure there is no allocating/collecting call between a successful File.open
result and publication of its owner root, or between edge phi moves and the
destination block's publication. The runtime cleanup adapter itself must
keep the File rooted throughout a potentially collecting close.

Initial admission caps are 64 blocks, 256 SSA values and 8 simultaneous
File owners (bounded by the existing owner verifier and request budgets).
The emitted root vector occupies at most 64 bytes. Preparation visits
O(blocks * maxDepth + instructions) original words with charged work and
bounded arrays, followed by O(blocks * maxDepth + closes) pure assembler
emission. Preflight precedes the first output byte; the emitted helpers do
not authorize machine execution merely because metadata verified.

## Missing integration and acceptance

A later coherent code batch must connect these verified root facts to the
existing whole-Function emitter, with original File acquisition and error
transport; real File.close through the already verified reverse cleanup
adapters; caller-owned class-5 `FailureContext` publication and ordered
secondary attachment; pending normal results, checked handlers and recursive
frames; and **all** exits. Include live/foreign/stale/dead/duplicated owner
negatives, forced GC across acquisition/cleanup, deterministic failure
injection, full physical and independent outcome evidence before marking
this work as integrated. The current emitter still refuses arbitrary File
opcodes; no default compiler code path changed.

The focused test checks original Function ownership metadata, generated
root/helper signatures, consumption labels and object-file assembly. It is
not an actual end-to-end File.open/close application or CI qualification.
The test must pass before this partial foundation is considered verified.

Final four-platform CI and completed-batch qualification remain reserved
for the completed U2 implementation. Keep #111/#121 draft and #74 open.
