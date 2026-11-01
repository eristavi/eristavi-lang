# Eristavi optimization plan — 1 November 2026

Status: execution in progress; current results and explicit deferrals below supersede the original proposed sequence.
Review baseline: PR #106 head `c2423d5b6211c4999a116e541fb11c67dfa2357d`.
This document records a plan, not completed optimizations or permission to merge.
Follow Philosophy → Semantics → Architecture → Implementation.

## 1. Verified starting point

The complete active-branch HANDOVER.md was read: opening mandates and sections
1–72, 3,046 lines. Main's handover ends at §44 and is not the latest U1b record.
The complete design philosophy, language-semantics summary, U1 contract, typed
UIR proposal and CI qualification policy were read, together with the remaining
acceptance plan, current U1b performance report, relevant value/cleanup/private
memory contracts and current word-store, budget, x86 emitter and scalar-runtime
source. No AGENTS.md is present in the inspected repository tree.

| Item | Verified state |
| --- | --- |
| U1a | Qualified/merged through #105; #77 closed within adopted scope |
| U1b #106 / #73 | Draft/open/unmerged; functional qualification passed at an earlier exact revision |
| Qualified source/test/workflow revision | `0a2ba59472a9571b9f352255c62957594ebacc68` |
| Full CI | [41303717634](https://github.com/eristavi/eristavi-lang/actions/runs/41303717634): all four platform jobs passed |
| Completed-batch qualification | [41303717596](https://github.com/eristavi/eristavi-lang/actions/runs/41303717596): three bootstrap repeatability/offline jobs and owned integration passed; full owned self-build skipped |
| Later current-head CI | [41307434281](https://github.com/eristavi/eristavi-lang/actions/runs/41307434281): smoke passed, new hotspot profiler failed |
| Current versus qualified revision | Only HANDOVER.md, tests/test_u1b_runtime_hotspot.py and .github/workflows/ci.yml differ; compiler/runtime source is unchanged |
| Measured improvement retained | Same-owner redundant poll removal: five paired runs, median 43.954859 → 41.212584 seconds, 6.24% lower on one linked reference fixture |
| Performance #51 | Open: large owned-reference overhead and current real source-compiler profiling remain unfinished |
| U2 / U3 / U4 | Not implemented; default production pipeline unchanged |

The earlier successful full qualification remains evidence for its exact inputs.
It does not certify the later modified diagnostic or workflow. The current PR
cannot be called entirely green.

## 2. What the evidence says

The older accepted diagnostic profile separated these instrumented phases:

| Phase | Wall seconds | Allocator entry calls |
| --- | ---: | ---: |
| Seal / canonical verification | 8.7328 | 179,340,858 |
| Repeated ingress verification across all attempts | 21.8376 | 497,492,849 |
| Aggregate engine and type validation | 1.7184 | 48,182,528 |
| Linked aggregate execution | 1.6492 | 22,200,134 |
| Other setup, refusals and teardown | 9.4284 | 202,028,351 |
| Engine close | 0.0010 | 9,985 |

Observed instrumented process wall: 43.9961 seconds. Verification stages account
for about 69.5% of that observed interval. GC inclusive time was 0.39376 seconds
(about 0.9%, overlapping the phases). Total allocator entries were 964,789,930,
safe-point entries 932,256,371 and graph creations 232,148.

These are instrumented event counts and phase times, not isolated helper CPU
costs or bytes. The accepted profile predates the same-owner poll optimization.
It establishes priority, not a precise current cost breakdown.

Source inspection supplies a plausible mechanism to test: each words.get calls
context, charges work, walks six radix levels in pageAt, and selects one of
sixteen fields. Native scalar helpers allocate a 40-byte slot-node request for
each new boxed scalar; allocator rounding and headers are additional. The current
x86 emitter routes ordinary source operations through boxed helper calls.
Attributing the nearly billion entries to specific callers still requires
measurement; counts alone do not prove allocator free-list search is expensive.

The historical 830× C/owned ratio is a different, cross-runtime comparison.
Do not divide current timings by an older C sample from another runner or promise
that a 6.24% gain closes that gap.

Four private micro-candidates are rejected history: live-slot accessor shortcut,
graph-hash inlining, one-entry positive cache and 64-entry positive cache.
The final cache was 2.65% slower across five pairs. Do not repeat or promote them
without materially new evidence. Raising GC thresholds is not supported here.

## 3. Ordered work and concrete exit criteria

### Step 0 — repair the measurement baseline and CI selection

First fix the demonstrated diagnostic failure, not compiler semantics.

Current decode() removes gc_time_ns from each stage and publishes
gc_seconds_inclusive. A later assertion loops over FIELDS[2:-1], asks each stage
for the removed gc_time_ns key with default zero, and compares that zero sum with
the positive raw cumulative nanoseconds. The latest run fails:
`0 != 545628495: non-reconciling phase event counter: gc_time_ns`.

Retain raw integer per-stage nanoseconds through reconciliation and derive seconds
afterward. Do not remove the reconciliation assertion or compare seconds with
nanoseconds. A tiny synthetic record sequence can check counter telescoping,
phase tags, GC unit conversion and malformed/nonmonotonic rejection without
compiling any Eristavi program.

The current ci.yml also adds an expensive branch-specific profiler on every code
PR synchronize event, including documentation updates on a PR whose net diff
contains code. Restore the established explicit manual profiling selection.
Inspect scope classification before publishing documentation to avoid claiming
that a Markdown edit cannot trigger the current expensive selector.

Exit: fast decoder checks pass; one explicit focused profiler run has exact
C/owned output parity and reconciles every additive counter; raw records plus
summary are retained before temporary files disappear. No full matrix or
experimental owned compiler self-build is needed for this diagnostic repair.

### Step 1 — attribute current verifier costs once

Use the existing full linked fixture including its refusal/cancellation cases.
Pin the current optimized word-store source, compiler/runtime and fixture hashes,
toolchain and limits. Preserve separate uninstrumented control timing.

Add scoped counters for words.get/pageAt/context, budget.work/active/poll,
scalar constructors/copies/arithmetic and erist_rt_value_new. Distinguish true
successful allocation events/bytes and failed requests from allocator entries;
record slot collections, graph finds, actual peak/live/traffic and work ledgers.
Capture call-site or phase attribution rather than instrumenting every operation
with a heavyweight logging call. Check instrumentation register/flag preservation.

Keep instruction/field counts separate from runtime helper counts. Report actual
repeat counts: sealing once, repeated ingress across all fixture attempts, and
execution. The test's many deliberate refusals are valid stress, but its whole
duration is not the cost of one user reservation or one production compile.

Exit: identify the top attributable source/helper path and a count-based savings
hypothesis for ONE candidate. Use a low-overhead timing/sampling cross-check where
available. Stop broad profiling once it answers that question.

### Step 2 — first bounded candidate: cheaper current-record word reads

Preferred first pilot, conditional on Step 1 confirming radix/read amplification:
a bounded record-read helper or short sequential read burst in the verifier that
resolves the authoritative radix path once for words from the same current page.
Start with one hot instruction/value record accessor, not a replacement word
store or an unbounded cache.

Constraints:
- Read current supplied records on every verification invocation, including
  unreachable, same-revision corrupted records. No builder stamp or revision-only
  cache grants trust.
- Keep store/phase owner, lifetime, frozen/write policy, range/overflow and missing
  node/page validation. A read burst must have a proof that no callback, edit,
  safe point or escaped handle can invalidate its resolved page while in use.
- No persistent raw page-pointer cache; no cache across verifier calls.
  Re-resolve at a page boundary and on each new bounded burst.
- Preserve deterministic validation/error order, work admission/refusal behavior,
  cancellation polling and exact ownership accounting. For the first pilot retain
  the existing per-word charge contract; review any later work-model change
  explicitly rather than hiding it as a speed optimization.
- Private helpers return current scalar fields or bounded scratch, not public
  unverified page capabilities. Use the original get path when safety cannot be
  proved. Budget any added scratch, including simultaneous old/new capacities.

Exit: an unchanged logical read set and diagnostic order, fewer measured radix
walk/helper operations, correct pilot output, and meaningful uninstrumented time
improvement. Reject if added scalar boxing or record-copy overhead cancels the
saving. This is a hypothesis, not an implemented API or promised speedup.

### Step 3 — larger candidate only if scalar boxing remains dominant

If Step 2 is ineffective or leaves boxing dominant, prototype backend-private
unboxed Int/Bool intermediates in ONE proved straight-line, nonescaping region.
Keep public function/runtime calls and stored values on the existing 32-byte ABI;
materialize adapters at boundaries.

Require static type, liveness, alias/escape, checked-overflow, fault-location and
root-safety proof. Initially exclude identity/Text/List/maybe/Float, resource
operations, checked-handler boundaries, address escapes and unknown calls; use
the existing boxed path for unsupported cases. This is an incremental current
backend optimization, not U3 promotion or a new source-visible scalar type.

Removing allocations needs an explicit internal representation/exhaustion policy:
preserve defined source faults and terminal OOM behavior for allocations that
remain; do not promise byte-for-byte identical physical OOM injection ordinals
after eliminating a temporary. Root maps and collection boundaries must remain
valid for all managed values surrounding the region. If the existing backend
cannot prove this safely, defer that candidate to reviewed U3/U4 work rather than
weaken the verifier or speculate on a whole-compiler rewrite.

Exit: substantially fewer actual scalar slot allocations on the confirmed path,
independent behavior parity and no unexplained retained memory or root loss.
This is a separately qualified batch, not automatic expansion of Step 2.

### Step 4 — avoid duplicated type work only within one invocation

Lower priority, and only if a fresh profile shows a meaningful share:
independently validate the complete immutable aggregate type graph once per
execution-ingress invocation, then let every body verifier consume that exact
invocation-owned validated context while still checking every body's current
signatures, types, provenance, structure and SSA.

This requires a private verifier API and ownership/mutation-lifetime proof.
Rebuild the context on every later execution; reject altered graphs/declarations
even if revision counters are unchanged. No persistent trusted=true cache and
no omission of dead or uncalled bodies. Preserve budgets and failure cleanup.
Do not implement merely because this is easy: engine/type validation was a much
smaller measured share than sealing and ingress body verification.

### Step 5 — demonstrate improvement and broader relevance

For each promising candidate, stop edits and compare the current optimized owned
baseline with the candidate using five serialized fresh-process
AB/BA/AB/BA/AB pairs on the same host. The baseline includes the qualified
same-owner poll optimization; do not use a slower historical revision to inflate
gains. Use uninstrumented binaries for timing and separate instrumented binaries
for cost attribution.

Record raw wall/user/system CPU, medians, pairwise ratios and spread, peak RSS,
source/runtime/application hashes, exact stdout/stderr/exit and independent
expected results. Source/backend edits may legitimately change application
assembly; runtime-only experiments must retain it. Five samples are limited
evidence: small or inconsistent gains need review, not a categorical speed claim.

Before adoption, apply the unchanged source-compilation workload protocol from
#51 to a completed representative input such as typed_ir.eri; use ir_verify.eri
only within its existing bounded diagnostic cap. Separately record parsing,
semantic analysis, old typed lowering, both existing verifier gates, optimization
and emission where instrumentation permits. Keep cold toolchain build, warm
execution and source-to-assembly time distinct. A timeout remains censored;
do not extend it or substitute the excluded 900-second self-build.

Vary size dimensions independently over three points: word/record count, aggregate
width, nesting depth and function count, rather than increasing width and depth
together. Use focused small cases for development; expensive scale/physical
studies stay explicit opt-in.

Exit: reproducible exact correctness; operation/allocation reduction matching the
hypothesis; a defensible latency improvement rather than a noise-level pilot;
original memory/work/cancellation gates met; and no material unexplained regression
in representative completed compilation. No invented universal speed factor or
post-hoc passing timing threshold.

### Step 6 — correctness, resource and release gate

Run change-specific tests before five-pair qualification when they can cheaply
reject an unsafe candidate. Retain:
- same-revision stale signatures, malformed dead/uncalled bodies, foreign owners,
  corrupted radix paths/fields and restored revalidation;
- branch/switch repeated targets, simultaneous backedge swaps, recursion/fuel,
  narrow arithmetic and original first fault/LocId;
- equal/distinct-owner cancellation and work-credit checks, quota/refusal cleanup,
  monotonic traffic and no partial publication;
- GC/root/unwind, allocator-refusal/fallback, alias/value snapshots and forced
  identity collisions if touched by the implementation;
- actual semantic-owner backing, exclusive frame histories, total allocator
  traffic and process RSS as separately labelled scopes. Preserve the broader
  observer's exactly accounted marked 224-byte process survivor; do not relabel
  it as zero retained process memory or a leak.

Keep original 8 MiB peak / 64 MiB traffic qualification-owner ceilings and
request/work/count/poll limits. Diagnostic event counts are not admission bytes.

Only a final coherent production code batch receives one four-platform full CI
and the qualification selected by CI_QUALIFICATION.md: compiler/codegen/common
changes require full bootstrap repeatability/offline plus owned integration;
owned-runtime-only changes require full CI plus owned integration. Inspect exact
head/job results and compare tested versus merge inputs. Docs-only changes get
patch checks. Keep full experimental owned self-build excluded.

## 4. Merge and milestone recommendation

Keep #106 draft during measurement repair and the first structural pilot. Do not
interpret this planning review as approval to merge or waive performance debt.

Once the diagnostic is green, assess the bounded candidate and record an explicit
reference-only performance disposition. U1b's functional contract does not demand
solving all of #51; conversely, green correctness tests do not prove that the
compiler is optimization-complete. A reference-only U1b merge can be considered
with current measured limitations, a concrete #51 follow-up and the required
qualified unchanged implementation. No production U3 promotion follows.

Continue U2 → U3 → U4 only with their own semantic/resource/performance gates.
Do not accumulate U2 on top of an unexamined high-allocation representation.

## 5. First next action

Repair raw-counter reconciliation and explicit profiler selection, validate the
decoder cheaply, then run ONE corrected current-source attribution profile.
Select the first record-read pilot from that evidence. No optimization
implementation or new expensive workflow was performed during this plan review.

## Execution checkpoint — see HANDOVER §74

- Step 0: raw-unit reconciliation repaired; three cheap decoder/trace tests and
  one corrected current-source native profile passed. Automatic expensive PR
  profiling removed; explicit workflow retains raw records/summary.
- Step 1: current profile attributes 951M successful allocator entries, 920M
  boxed values and 3.23M current radix-child reads; GC inclusive 0.614s.
- Step 2: chose a SMALLER bounded alternative to a record-read burst: explicitly
  unroll the existing fixed six-level noncreating path. It retains every
  current child/page check and all seven per-word work units; creating push
  traversal remains unchanged. No page cache, API/record-layout or ABI change.
  All 12 focused checks pass after correcting one new fixture's optional
  narrowing. Five paired native executions per variant all match the oracle;
  median 61.790446 → 54.983744s (11.0158% lower), all five pairs favorable.
- Step 3: larger scalar unboxing remains deferred under #51. The current
  production Universal IR's generic value class and boxed helper boundary
  do not by themselves prove scalar type/escape/liveness and root-map safety.
  It needs a separately reviewed typed-region/adaptor/exhaustion contract;
  do not expand this safe word-store batch into a speculative backend rewrite.
- Step 4: per-invocation shared type validation remains lower priority. Current
  fresh graph/body/dead-code validation must be retained; no shortcut adopted.
- Step 5: five pairs and expanded candidate allocation profile complete (32.69M fewer boxed temporaries; identical checks/work).
  A separate bounded current compiler-source diagnostic is prepared. Static
  import closure confirms U1 modules are absent from the existing frontend;
  no production compilation-speed gain can be attributed to this change.
- Step 6: physical/scaling and smoke 49/49 PASS; final hosted exact-head qualification pending. No merge,
  U2/U3/U4 implementation or full owned compiler self-build has occurred.

The full paired raw samples, CPU/RSS scope, hashes and independent output oracle
are in ../evidence/2026-11-01/u1b-fixed-path-five-pairs.json. This checkpoint
records a bounded improvement, not completion of all performance work in #51.

Latest execution/acceptance disposition: HANDOVER §75 and U1B_FIXED_DEPTH_WORD_READ_2026-11-01.md. The bounded source profile completed typed_ir with exact parity; ir_verify is censored at 90s. No total compiler-performance completion or owned full self-build is claimed.
