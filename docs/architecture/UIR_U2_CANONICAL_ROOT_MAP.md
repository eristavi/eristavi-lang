# U2 canonical checked-failure root-map metadata — bounded v1

Status: **opt-in design/implementation candidate**, 3 November 2026.
Governed by DESIGN_PHILOSOPHY.md, LANGUAGE_SEMANTICS.md,
RESOURCE_CLEANUP.md, UIR_U2_CONTINUATION_CONTRACT.md, and HANDOVER.md.

## Necessity and meaning

Existing canonical opcode-46 `invoke.direct.v1` contains two checked
outcome edges. Failure destination block parameter zero is a typed
aggregate failure payload. At native garbage-collector safe points, the
machine representation of a retained failure context must have an exact
root. The owned Linux x86-64 runtime already supports a scope-bound
root/key/class table with **class 5** for saved failure records, and
traces ordered secondary links. The compiler needs a trustworthy
machine-neutral source of *which* canonical values require that root.

A new private optional `u2_root_map.eri` artifact describes that
information; it is **NOT** a new executable IR, new source keyword,
new GC or new public ABI. Do not conflate this metadata with native
root publication or successful whole-program managed values.

## Record and verifier contract

For each canonical opcode 46, in instruction-index order, the map
contains exactly one six-word entry:

1. canonical instruction ID;
2. failure edge's destination block ID;
3. the destination's first canonical SSA parameter ValueId;
4. structural failure-payload TypeId;
5. exact instruction LocId;
6. runtime root class (=5).

The map is versioned, function-owned, immutable after construction,
and bound to an exact Function key, type-graph key and Function revision.
Creation and independent verification read existing Function instruction,
edge, block and value pools, including **dead/unreachable** instructions.
The verifier rejects missing, duplicate, extra or reordered entries;
wrong/nonstructural type; wrong failure edge, value origin, location,
root class, owner, version, or revision; closed/foreign/malformed
backing and quota failures. It does not trust construction output as
proof of correctness. Full canonical and scoped-owner UIR verification
remain mandatory separately.

The selected opt-in profile caps at 128 checked invokes, 768 record
words, and scans all canonical instructions once, O(instructions +
root records) per independent verification. It adds no new dynamic
dispatch or per-safe-point full graph scan to production. Overflow
refuses explicitly, never silently drops a root.

## Subsequent target integration and acceptance

A machine backend must map the verified SSA root entry to a **live
actual slot** and a scope-bound class-5 entry, then emit/execute the
existing `evn_bind_roots` contract before allocating calls or checked
cleanup/unwind. It must update the table on block transitions and
retain all root classes for Text, List and identity values. A failure
context remains live until propagation or handling has completed; a
secondary chain is traced without changing the typed primary. Root
release must occur before reclamation, not before the last access.

Reject any published target root map not derived from and reverified
against the exact current canonical revision. Negative tests must
mutate every record field and delete a record, including dead code.
Native acceptance additionally requires forced collections with
**compiler-produced** maps, independently instrumented collector
counts, deterministic allocator refusal, physical capacity/RSS
samples and Stage-0/current-native behavior parity.

The existing [run 41597194105](https://github.com/eristavi/eristavi-lang/actions/runs/41597194105)
passes **79 focused tests (76 passed, 3 skipped)** for native class-5
saved failure retention and ordered secondary managed Text under
explicit collector calls. This is the existing runtime's direct root
ABI, not the canonical root-map emitter. U2 #74 remains OPEN and draft
PR #111 must not merge until full acceptance.
