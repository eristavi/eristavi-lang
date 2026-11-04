# U2 bounded native checked-cleanup adapter — development checkpoint

Status: experimental; **not** complete U2 checked-invoke or FailureContext
acceptance. Governing documents: DESIGN_PHILOSOPHY.md,
LANGUAGE_SEMANTICS.md, RESOURCE_CLEANUP.md, CI_QUALIFICATION.md,
UIR_U2_MULTI_CLOSE_LOWERING.md and HANDOVER.md.

## Connection to canonical information

`src/compiler/u2_cleanup_native_x86_64.eri` consumes the **existing private**
`u2_cleanup_plan.Plan`, and independently verifies every plan row, owner,
exit origin, reverse lexical order, normal and failure successors before
emitting any native code. This does not create a new executable IR or invent
another source-language cleanup model. The emitted x86-64 function is a
bounded lower-level execution of those verified close obligations.

Closed development profile: one to eight scoped owners, zero surviving owners,
File resource boxed owned values, and a caller-owned saved-failure record.
Root words for resources are supplied in lexical acquisition order; generated
code executes the verified plan starting at `plan.entry`. The function
registers a private native root scope (resource boxed slots plus one class-5
saved-failure pointer) and preserves it through all allocating close helpers.
Every consumed resource is zeroed in both the local root and caller's owner
word on either checked outcome. No pending successful-return payload is
modified. Failure outcome returns -1, successful exit returns zero.

The existing real `evn_cleanup_accumulate` and
`erist_rt_failure_append` are used unchanged: a new close failure becomes the
primary if no failure was pending, or is appended as an ordered secondary
otherwise. A pending primary remains primary, and a clean close does not
invent a secondary. An already closed resource is not re-closed.

## Independent integration testing

The code generator fixture derives both success-entry and already-failed
native entries from independently verified cleanup plans. The native Linux
integration test uses actual owned file resources and the existing runtime,
and injects a *real checked close failure* through the test-only close-error
interposition already used in freestanding resource tests. It tests successful
and failing exits in both normal and failing close modes, forced GC with
registered roots, closed resource counts, physical live saved-failure counts,
and exact reverse-ordered payload contents.

## What this does NOT establish

The emitted helper does not yet lower canonical opcode-46 instructions from a
complete Function or emit checked continuation dispatch from a verified
source-level owner profile. It consumes an independently verified private
plan and a pre-existing caller-managed frame. General FileError construction
for arbitrary source calls, pending-return transport through all CFG exits,
mixed resources and surviving outer prefixes, recursive checked unwinds,
precise SSA publication/release, structural corruption and allocator-refusal
oracles, and final four-platform qualification remain required.

No default production compiler path, source syntax, Unicode 17 tables,
32-byte value ABI, GC, File runtime contract, ownership policy or external
dependency is changed. Keep PR #111 draft and #74 open.

## Exact November 4 qualification evidence

- Tested code revision: `3f36fa48e473ef554f003b0c0edcdc36c44f3a73`.
- [Focused native cleanup CI #41812694413](https://github.com/eristavi/eristavi-lang/actions/runs/41812694413):
  **PASS**, all four actual File resource scenarios in one test method.
- [Full focused Linux U2 smoke #41812694324](https://github.com/eristavi/eristavi-lang/actions/runs/41812694324):
  **PASS**, 99 run / 96 passed / 0 failed / 3 intentional skips.
- The four-platform final matrix was not run; no production merge and no
  formal U2 acceptance. Next connect canonical checked invoke CFG and
  typed FailureContext root publication to this adapter rather than
  broadening a separate executable plan interpreter.

## 4 November 2026 — opt-in canonical single-owner ingress

`src/compiler/u2_cleanup_canonical_x86_64.eri` is a separate admission
boundary for an existing canonical opcode-46 checked `File.close`. It rechecks
the published canonical function and independent scoped-owner profile, the
current continuation pair, complete checked-invoke root map, selected source
instruction, both destinations, class-5 failure slot, and the original private
cleanup plan before forwarding to the established native adapter.

The admission profile is deliberately closed: exactly one File owner, no
surviving outer prefix, one consumed close operand, zero normal results, one
failure edge payload, a current source LocId and a freshly verified root map.
A mismatched location/owner/edge/root must fail closed before emitting any
assembly; the native adapter re-verifies the private cleanup plan itself.

This is an **integration gate**, not full machine lowering: it does not yet
transport arbitrary checked-call return SSA values, publish the selected
canonical machine-slot root itself, handle arbitrary multi-owner paths,
recursive checked unwind or mixed resource types. Its private class-5 native
root behavior remains the already-tested adapter's behavior. Keep U2 draft,
production and public ABI unchanged. Do not cite the earlier native File tests
as qualification of this new bridge; exact-head focused results must be
recorded separately once available.

## 4 November 2026 — three-part native U2 integration candidate

Status: **code committed; exact-revision CI pending**, not U2 acceptance.
This is a bounded continuation of the existing frozen semantics and canonical
UIR contracts. Source syntax, semantic operation IDs, production compiler,
owned runtime, GC collector, public 32-byte value ABI and external imports
remain unchanged.

### 1. Checked edge -> live class-5 root

`src/compiler/u2_checked_rooted_x86_64.eri` consumes the exact canonical
`Function`, independent scoped-owner proof, canonical opcode-46 root map,
native machine-slot placement, checked destination descriptor and private
verified cleanup plan. It **verifies the complete placement first**, then
invokes the canonical File close ingress and existing native root publisher.

The generated private `erist_u2_checked_LABEL` entry takes RDI (caller File
owner words), RSI (caller-owned 96-byte saved-failure record) and RDX (caller
root words, already bound with `erist_u2_bind_LABEL` in a live scope). It
requires the selected root to be empty, publishes RSI in the verified class-5
slot **before any allocating close helper**, performs the checked native close,
releases that root only on successful completion and retains it on failure.
Status in RAX is 0 or -1, and the caller must retain the bound scope through
error propagation/handling and explicitly release the slot afterward. A
failure without a populated typed saved context is a terminal internal defect.
This is a private backend adapter, **not** a general canonical CFG executor.

### 2. Physical GC and rejection regression

`tests/test_u2_checked_rooted.py` builds the canonical owner/checked-invoke
fixture, derives the machine slot through the existing independently verified
root-map/placement contracts, and executes the emitted File close + root
publisher on the actual owned Linux x86-64 runtime. It covers normal and
injected checked File-close failures, forced collection while the typed
failure record is live, root release on normal completion, owner consumption,
open-resource counts and final GC/allocator shutdown.

Existing independent `test_u2_native_root_publish.py` checks wrong-class,
overlapping, misaligned, stale, foreign and closed slot plans. Full
end-to-end malformed-root and allocator-refusal coverage is still open;
do not extend the meaning of one bounded positive native regression.

### 3. Surviving prefixes and pending scalar completion

`u2_cleanup_native_x86_64.emit` now accepts 1–8 original File owners with
a verified `survive` prefix, while consuming *only* the exited suffix.
Both normal and already-failing private plans retain surviving caller roots.
`emitPendingScalar` adds a closed x86-64 private adapter whose RDX input is a
pending i64 return value. After cleanup success it returns that value in RAX
with RDX=0; after checked cleanup failure RAX carries no success result and
RDX=-1. The caller must branch on the status before observing the return.

`test_u2_native_cleanup.py` adds a three-owner/two-inner-scope exit
with one surviving File owner, a pending scalar return, normal/failing closes
and a subsequent outer File close. The tests do **not** establish a canonical
SSA pending-return transport or all-handler control-flow lowering.

### Remaining non-negotiable gates

- Qualified exact-head focused CI for this candidate, then independent
  broader tests; any red check remains a blocker.
- Verify stale, foreign, deleted and wrong-class canonical roots at the
  **combined** ingress, including forced-GC and allocator-refusal outcomes.
- Bind pending success results from actual canonical SSA continuation
  parameters rather than the caller-provided private scalar ABI.
- Lower multiple owner prefixes and all checked/failure/handler CFG paths
  from the canonical Function (not solely private plan rows).
- Confirm recursion across checked frame failures, managed Text/List/identity
  roots, physical retained capacity/RSS, independent Stage-0/native parity
  and final four-platform completed-batch qualification.

Keep PR #111 draft and U2 issue #74 open; do not merge or promote.
