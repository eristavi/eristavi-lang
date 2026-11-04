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
