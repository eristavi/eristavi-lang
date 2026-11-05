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

- one to eight currently live lexical File owners, exactly one exiting
  innermost File owner, and zero to seven surviving outer File owners;
  no already-failing entry in this selected checked SSA profile;
- one source block containing exactly the active File parameter set in any
  verified lexical/SSA order, followed by one predecessor `i64`;
- one checked `File.close` opcode-46 operand and exact source `LocId`;
- normal edge carries the **exact** positive predecessor ValueIds of all
  surviving outer Files in lexical order and the source `i64`;
- failure edge contains the **negative typed failure marker -1** followed
  by those same surviving File ValueIds and the same predecessor `i64`;
- normal destination contains surviving File parameters plus `i64`;
  failure destination contains structural typed error payload **first**,
  then surviving File parameters plus `i64`;
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

The wrapper additionally kills the consumed innermost File's old source
SSA ValueId after native close on BOTH checked outcomes, complementing
the exact runtime File-owner word clearing. Each surviving File ValueId
moves into its chosen successor parameter and its original SSA source slot
is zeroed, while the caller-owned lexical root words remain live through
the surviving outer scope. File ownership is not implemented as an
implicit value copy; a stale consumed File must never be usable.

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

## 4 November 2026 — bounded nested-owner SSA extension

`src/compiler/u2_checked_ssa_bind.eri` and
`src/compiler/u2_checked_ssa_x86_64.eri` now admit/emit a normal-entry,
one-close checked edge with up to eight total File owners and the complete
exact surviving owner prefix moved through version-two normal/failure
successor parameters. The portable binding verifies canonical Function
SSA dominance, owner-depth correspondence, original `Plan`/LocId, exact
surviving positive edge transfers, typed failure marker, selected class-5
root identity and each destination parameter. The machine profile derives
all offsets from the freshly verified canonical ValueIds; the selected
consumed File's source SSA slot is zeroed on **both** outcomes. The
existing caller-owned File root vector remains responsible for the
surviving outer handle through the next lexical exit.

A canonical nested two-File acquire/inner-close/outer-close fixture also
builds complete checked handler paths; on a selected inner checked edge
it independently verifies one carried outer owner plus pending i64,
tests that a forged consumed File cannot be transferred to the successor,
and emits no rejected label. The generated Linux x86-64 test executes
three pending i64 values under both real File-close outcomes, forces the
actual collector, checks the outer resource remains live, closes it once,
and checks the saved failure context survives until root release.
Both the one-owner and two-owner probes explicitly populate the consumed
source SSA File parameter and require it be **zero on completion**;
this prevents use-after-consumption through an abandoned SSA slot.

### Exact evidence and qualification boundary

- Source revision `2099c6243b95679d8683207163f50023136f37b0`
  (before the consumed-source-slot poison hardening):
  [dedicated U2 run #41881371026](https://github.com/eristavi/eristavi-lang/actions/runs/41881371026)
  **SUCCESS: 6 focused methods / 0 failures** and
  [Linux smoke #41881370999](https://github.com/eristavi/eristavi-lang/actions/runs/41881370999)
  **SUCCESS: 104 run / 101 passed / 0 failed / 3 opt-in skips**,
  417.632 seconds. Four-platform CI skipped by incremental policy.
- Native source hardening `a1d3cb8f24c6b4432733e703e05c0948e10be97a`
  plus single-owner regression `8e9cadc0891a93e47abfc32bba46c2b84454e1da`:
  [focused run #41882834794](https://github.com/eristavi/eristavi-lang/actions/runs/41882834794)
  **SUCCESS: 6/6 tests**, proving native consumed-slot poisoning under the
  original and nested runtime cases.
- Latest consumed-source-SSA hardening *and* nested-owner assertion code
  revision `200c7037d8db56e05fecadb4251e4d4a12dcff86` is now
  [focused-verified in #41883433364](https://github.com/eristavi/eristavi-lang/actions/runs/41883433364):
  **SUCCESS, 6/6 native methods, no failures**. The regression explicitly
  publishes both canonical File source parameters, checks the inner consumed
  SSA slot becomes zero on normal/failure, confirms the surviving outer File
  moves correctly, forces collector passes and closes the outer resource
  exactly once. This focused evidence is NOT a completed-batch full matrix;
  the last completed broad Linux smoke remains #41881370999 on the
  *pre-poisoning* `2099c624` revision.
- Initial two-owner [candidate #41879954423](https://github.com/eristavi/eristavi-lang/actions/runs/41879954423)
  failed three *clean test assertions* because the caller deliberately
  class-5 pinned an empty saved FailureContext which the test had expected
  to have been collected; this was corrected to one live record. A
  following [#41880916713](https://github.com/eristavi/eristavi-lang/actions/runs/41880916713)
  failed Python test collection on a `//` comment typo; repaired to `#`.
  These harness failures are superseded by the verified `2099c624`
  implementation smoke and `8e9cadc0` hardened-source focused run.

**Still not full U2:** this is a private Linux x86-64 one-close entry from
a pre-populated SSA frame, not complete code generation for all canonical
CFG blocks/producers and all typed results; it is not recursive checked
failure propagation/ordered secondary composition from native UIR,
managed Text/List/identity root lifetime across loops, allocator-refusal
physical/RSS evidence, Stage-0 vs native independent A/B, or four-platform
completed-batch qualification. Keep PR #111 draft and issue #74 open.
