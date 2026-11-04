# U2 bounded canonical SSA -> native checked File-close continuation

**Checkpoint: 4 November 2026.** Opt-in Linux x86-64 implementation is
**focused-tested**, not general canonical Function code generation, full managed
`FailureContext` implementation, U2 acceptance, or production migration.

Governing order: `DESIGN_PHILOSOPHY.md` -> `LANGUAGE_SEMANTICS.md` ->
`RESOURCE_CLEANUP.md` -> canonical UIR/continuation/owner/root contracts ->
implementation and independent verification. No new source syntax, opcode,
executable shadow IR, collector, or public 32-byte value ABI.

## Necessary semantic contract

For an ordinary pending `Int` return, an actual predecessor SSA value must
survive a checked `File.close` operation **only when cleanup succeeds**. The
successful continuation receives it as a typed block parameter. The checked
failure continuation receives a structural typed failure payload as its *first*
parameter; it may carry the predecessor value for its handler/propagation
context, but it **must not** complete the original successful return.
The close consumes the File owner exactly once on both outcomes. Any managed
failure record stays rooted until handling/propagation ends, including forced
collection during allocating close helpers.

The existing version-two `u2_invoke_transfer` canonical opcode 46 already
expresses both successor result-tuples: negative ordinal markers for
outcome-only values; positive indices for previously available values. This
work uses those existing pools, independently verified SSA dominance and
scoped ownership, rather than inventing a second set of executable edges.

## Step 1 — independently verify canonical carried SSA

`src/compiler/u2_checked_ssa_bind.eri` rechecks the whole canonical Function,
`u2_scoped_owners.Profile`, fallible contracts, version-two continuation
`Pair`, class-5 `u2_root_map.Map`, and fresh original
`u2_cleanup_plan.Plan`. Selected closed profile:

- one active File resource and exactly one exited owner, with no surviving
  outer File owner; normal mode only at entry;
- one source block with exactly `(File, i64)` block parameters;
- one checked `File.close` opcode-46 operand and exact source `LocId`;
- normal edge has one **positive** SSA transfer of that source i64;
- failure edge has the **negative typed failure marker -1** followed by
  exactly the same predecessor SSA i64;
- normal destination has one `i64` block parameter; failure destination
  has one structural typed aggregate failure parameter plus one `i64`;
- class-5 failure-root metadata names that exact checked instruction,
  first failure destination `ValueId`, type, original source location;
- at most 128 canonical SSA values for the selected machine-frame profile.

The independently verified report exposes exact source/normal/failure/carry
`ValueId` indices and selected root index. Existing whole-function canonical
dominance and owner proof also cover unreachable/dead blocks. Wrong-source
carried values are rejected **even when they have matching i64 type**.

The bounded proof scans the canonical pools and map without a separate
executable representation. Its full verifier cost is deliberately explicit;
it is not a claim of optimized general UIR lowering or a production hot path.

## Step 2 — emit the two native outcome paths

`src/compiler/u2_checked_ssa_x86_64.eri` independently verifies the
portable report and `u2_native_slots_x86_64.Plan` before it emits source-
verified native cleanup and class-5 publisher helpers.

Private wrapper `erist_u2_ssa_LABEL` receives:
`RDI` caller-owned File resource word(s), `RSI` caller-owned 96-byte
saved failure record, `RDX` live already bound class-5 root vector,
`RCX` caller-owned flat one-word-per-canonical-SSA-`ValueId` frame.
The caller must initialize the **actual predecessor block-parameter slot**
before entering. The reported native frame contains no source-level or public
Value ABI; its maximum 128 slots require at most 1024 bytes.

The wrapper snapshots the verified source SSA slot, clears newly produced
destination slots, publishes the class-5 saved record before any potentially
allocating File.close, runs the independently verified native cleanup plan,
then dispatches its checked status:

- **Normal (RAX=0):** source i64 moves into verified normal destination slot;
  failure destination slots remain zero and selected class-5 root releases.
- **Checked failure (RAX=-1):** normal destination remains zero; first
  failure destination gets saved-failure pointer, next gets carried i64 solely
  for failure handling; selected class-5 root stays live until caller release.
- Faulted or contradictory state fails terminally, not as an invented
  `fails` value. Existing File cleanup and runtime helpers remain unchanged.

This emits real machine-side branches and SSA destination writes, **not**
general native labels/control flow for all canonical blocks, interprocedural
calls, or a complete `FailureContext` value implementation. In particular,
the acquisition/entry-side predecessor SSA frame population in the executable
test is still caller-owned, not general machine lowering of its producing
instructions. Structural failure payload metadata is not a new public
failure-group type.

## Step 3 — focused and independent negative execution evidence

`tests/fixtures/u2_checked_ssa.eri` constructs a real canonical
version-two acquire/close Function with a carried predecessor i64 and
independently verifies all owner, SSA and root metadata. Its corruption
matrix checks same-type wrong-source normal and failure carries, removed
failure marker, stale `Pair` revision and stale root-map revision, then
restores and independently re-verifies. A forged carried `i64` is also
passed to the native entry: the verifier refuses before any `LABEL=62`
assembler symbol can be emitted.

`tests/test_u2_checked_ssa.py` generates executable owned x86-64 code,
derives machine frame offsets from the emitted helper, and compares positive
and negative checked outcomes for three predecessor i64 values `0`,
`74565`, `-19` against independently written expected slots. It injects
real File-close failure, runs explicit collector passes with the saved
FailureContext still pinned, checks exactly-once File close, root retirement
on success and no final live resources/GC object leaks.

`tests/test_u2_native_cleanup.py` and
`tests/test_u2_checked_rooted.py` continue to cover the earlier bounded
native cleanup and root contracts; both are now included in the standard
Linux focused-smoke list, together with the new SSA test.

### Verified GitHub Actions at exact source revision

- `1b99e065122b903aaa1537a7fc8cd563252f56d5`;
  [dedicated native check #41876779592](https://github.com/eristavi/eristavi-lang/actions/runs/41876779592):
  **SUCCESS**, five focused test methods, no failures.
- The same code revision;
  [Linux Clang smoke #41876779269](https://github.com/eristavi/eristavi-lang/actions/runs/41876779269):
  **SUCCESS**, **103 run / 100 passed / 0 failed / 3 opt-in skips**,
  **349.924 seconds**; the exact-head archive was uploaded.
  Full four-platform matrix intentionally **skipped** under the incremental
  CI policy; this is **not** completed-batch merge qualification.

Initial experimental reds required two test-fixture corrections: instantiate
the concrete U1 builder edge-check specialization with an independently
valid dead block, and rebind the continuation after Function completion
advanced its revision. Those did not modify frozen language semantics or
disable verification. Newer exact-code green checks supersede those attempts.

## Remaining U2 gates

General canonical opcode-46 lowering still needs complete checked path
dispatch and all SSA result transport, surviving owner prefixes and
multi-stage reverse cleanup via actual canonical Functions, recursive
checked-call frame propagation and ordered Unicode17 primary/secondary
failure contexts, live exact Text/List/identity root publication/retirement,
stale/foreign/dead-root and allocator-refusal matrices on the full combined
path, actual owner capacity/RSS/GC/traffic evidence and independent Stage-0
vs native differential behavior.

Complete those acceptance requirements before **one exact-head four-platform
CI and required finished-batch qualification**. Keep draft PR #111 OPEN,
issue #74 OPEN, default production compiler and 32-byte ABI unchanged,
U3/U4 migration separate and optimization #51 paused. No experimental
owned-compiler full self-build is authorized.
