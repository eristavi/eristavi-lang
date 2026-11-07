# Whole-Function File ownership and native roots — U2 development gate

## 7 November continuation: integrated nested owners and checked self-recursion

**Current development state supersedes the one-owner limits below.** Original
whole-Function emission now supports independently verified owner stacks of
depth 1–8. Root vectors reserve exactly the verified maximum depth, emit matching
class-1 entries, publish every surviving lexical owner at each original block
entry and poison just the consumed inner handle/root after real close. The same
emitter supports an exact checked self-call while the caller frame owns a File:
owner proof prohibits passing a handle into the child; the caller retains its
class-1 roots while the child acquires/closes its own resources. Dead incoming
checked errors can be recovered and then cleaned up, while live unbound primary
failure propagation stays refused.

Native targeted 3/3 pass:
[CI #42404765081](https://github.com/eristavi/eristavi-lang/actions/runs/42404765081),
exact code/test tree `8e5c8bd8de09d46586934b28dad2f7ac6f1729c1`.
Tests cover nested normal/failed paths, outer-prefix root refusal, forced GC,
reverse exactly-once cleanup and owning self-recursion through depth 16 with
injected close failures. They do not certify arbitrary File-owning checked
groups, live-primary composition across arbitrary nested chains, managed generic
constructors, broad physical/independent evidence or final four-platform CI.
Existing single-owner explicitly bound primary composition still operates in
its own bounded profile. No frozen ABI or default production behavior changed.


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

## First whole-Function integration — 7 November 2026

`u2_function_managed_x86_64.emitFileChecked` now admits one lexical File
owner, using the original canonical Function and fresh scoped-owner proof.
It extends the existing SSA selection with the distinct File carrier, reuses
full publication verification, and calls this foundation's per-block publish
and close-poison helpers from the actual Function CFG. A separate lexical
class-1 word is appended to the existing registered root vector; its lifetime
is independent of ordinary use-liveness. Existing class-5 outcome roots remain.
The additional lexical word costs eight bytes before stack alignment.

Exact version-one imported symbols `u2.file.openRead.v1` and
`u2.file.close.v1` require imported kind 2, effects 63 and version 1.
Acquisition takes the exact Text carrier and returns the owner carrier; close
takes that carrier and has no successful result. The failure carrier must be
exactly two Text fields (FileError message and path), with the existing checked
root verifier proving the same failure type at every original invoke.
The private entry also receives the linked runtime File descriptor index;
the existing runtime checks its resource kind. This is not a public ABI.

Acquisition reuses `erist_rt_file_open` with read-only flags and the existing
`evn_frame`/`setjmp`/`evn_pop` runtime boundary. Its result is immediately stored
in a registered temporary before any further runtime call. A caught checked
failure is saved and class-5 rooted after handler retirement, then transported
through the original failed edge. Terminal defects never become checked edges.
Close reuses `evn_empty_failure` and `evn_cleanup_accumulate`, then poisons the
original SSA handle and lexical root on both outcomes. Original simultaneous
edge moves publish destination roots before GC. Pending scalar values travel
through canonical carried arguments; a failing close selects the failed edge
and therefore cancels the otherwise successful return.

This first slice refuses nested depth, defined checked calls in the File
profile, failure parameters in owning blocks, and live primary contexts across
File operations. It does NOT yet implement nested surviving prefixes,
primary/secondary composition, recursive owned frames, all source exit shapes,
or additional File services. Earlier standalone nested cleanup evidence does
not qualify these unintegrated combinations. Existing checked group APIs and
production defaults are unchanged. The initial managed plan and File-selected
plan are closed on success and refusal; focused tests check retained accounting.

## Remaining acceptance

First connect an original active FailureContext to verified suffix cleanup,
retaining the primary and attaching secondary close failures in order. Then
admit nested owner prefixes and checked recursive/group calls with private
frames. Add combined foreign/stale roots, deeper allocator/physical/sanitizer
and independent-origin evidence. No new executable IR or resource runtime is
needed. Full four-platform and completed-batch qualification remain deferred;
keep #111/#121 draft and #74 open.

## Primary-composition integration constraint

The existing `UIR_U2_CHECKED_CHAIN_AND_RECURSIVE_FAILURE.md` contract keeps
an original carried primary distinct from the new close-failure outcome.
Consequently `ssa.liveBefore` alone must never authorize treating a live
FailureContext as the active propagation: a handler may retain an error as
ordinary data. The next integration must reuse the original checked-chain
binding and independently verified failed-entry cleanup Plan (including exact
primary ValueId transport on both outcomes), then invoke the existing cleanup
adapter for that bound route. Do not remove the current live-primary refusal
and infer active propagation merely from a matching failure type. Native
accumulator mutation cannot silently redefine original immutable SSA results.

`u2_checked_chain_verify.verifyPrimary` now exposes that existing failed-route
proof independently of the closed first/normal two-stage path. It freshly checks
canonical ownership, continuation, failed-entry cleanup Plan and root map, then
exact `[primary, File, pending i64]` source and both successor transports.
The chain verifier delegates its failed-route suffix proof to this entry.
Reports carry revision and instruction facts for immediate use, not cached
verification authority. General Function emission does not yet consume it.

## Whole-Function primary composition

`emitFileCheckedPrimary` adds one explicit PrimaryBinding (continuation,
instruction, original failed-entry Plan, lexical Scope and exit LocId).
Fresh verification precedes any assembly; a report is never cached authority.
The exact Function failure carrier must back the primary's class-5 root.
The independent proof is in `u2_primary_cleanup_bind`, shared with the chain.

File.close still accumulates its own outcome into a new rooted empty context.
On actual close failure, the new context is appended to the original primary
using the existing runtime operation, with both contexts rooted. The original
close outcome selects the original typed CFG edge; the incoming primary is
carried on both edges. A successful close cannot turn propagation into success.
Previously attached secondaries remain ahead of the newly appended close error.
No additional resource adapter, executable IR, public ABI or runtime semantics.

Admission remains one lexical owner and one explicitly bound failing close;
File-owning defined calls and arbitrary nested prefixes remain excluded.
Only the bound primary may be live across that close. Acquisition may carry
rooted failure ingress without mutating it. Ordinary handlers with retained
errors must not opt into failed-entry composition without the explicit binding.
