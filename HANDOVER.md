# Eristavi compiler — current handover

Reviewed 4 November 2026 (Asia/Nicosia). This is the current recovery document.
Historical checkpoints are evidence, not instructions to restart old work.

## Resume here

### 4 November 2026 — three-step checked-root/prefix batch committed, awaiting CI

- **New implementation source:** `275b31ce1cb5020dd6de065f04716de98960be2c` on `compiler/u2-cleanup-foundation-20261102`; latest accompanying architecture documentation `c94c5ef7a37e5a3f51a9e372cc57c281afc056ce`. The dedicated focused test [Actions run #41865432112](https://github.com/eristavi/eristavi-lang/actions/runs/41865432112) was **QUEUED** when this checkpoint was written. **No passing test claim is made for this new code**; the previous verified 100-test checkpoint is historical baseline only.
- **Step 1 — canonical typed-failure root -> native scope:** new opt-in `src/compiler/u2_checked_rooted_x86_64.eri` revalidates the exact canonical opcode-46 File-close ingress, whole checked-root map and native slot plan. It emits a private `erist_u2_checked_LABEL` wrapper binding a caller-owned class-5 root before allocating File cleanup, retaining it on checked failure and releasing on success. Requires a caller-bound live root scope; does not introduce another executable IR, collector, public ABI or production compiler edit.
- **Step 2 — actual File/GC regression:** new `tests/test_u2_checked_rooted.py`, run by `.github/workflows/u2-cleanup-smoke.yml`, verifies the generated wrapper with real owned File close (successful and injected error), a canonical root slot, explicit forced collection, retained typed saved failure on the failure edge, cleared success root and no final runtime leaks. The existing `test_u2_native_root_publish.py` retains independent stale/foreign/misaligned/wrong-class root-plan rejection; combined-path negative coverage remains to be added.
- **Step 3 — bounded surviving owners and pending return:** `u2_cleanup_native_x86_64.emit` now roots all incoming File owners but closes only the verified suffix, preserving a live outer prefix. Private `emitPendingScalar` returns the pending i64 in RAX with RDX=0 only if cleanup succeeded; on failure RAX is unavailable (zero) and RDX=-1. New `test_surviving_prefix_and_pending_scalar_return` covers three File owners with an inner-suffix exit, surviving outer File and subsequent close, normal and forced failing closes.
- **Limitations:** this is a **development candidate only**, NOT complete U2 or qualified UIR-to-native machine lowering. The pending scalar is caller-provided, not yet a canonical SSA return continuation; no general recursive checked unwind, all-handler/multi-owner canonical CFG lowering, arbitrary managed Text/List/identity root integration, combined ingress mutations, physical RSS/retained capacity/fault matrix, or final four-platform qualification. Do **not** merge PR #111 or close #74. Do not restart #51, migrate U3/U4, or trigger owned compiler self-build.
- **Next:** inspect exact-run focused CI and fix any failures at the same development boundary; then run independent negative checks and broader focused smoke. Record verified revision and evidence before any acceptance decision. See `docs/architecture/UIR_U2_NATIVE_CHECKED_CLEANUP.md`.

### Earlier 4 November 2026 — canonical checked File-close admission added and focused-tested

- **Current tested implementation revision:** `12bba417a822db605addf66304608d448f246490` on `compiler/u2-cleanup-foundation-20261102`, draft [PR #111](https://github.com/eristavi/eristavi-lang/pull/111). Production/main implementation is untouched. U2 issue #74 remains OPEN.
- **Exact-code focused native cleanup run:** [#41821092507](https://github.com/eristavi/eristavi-lang/actions/runs/41821092507) **SUCCESS**. Both `test_u2_native_cleanup` methods pass: previously proven real File cleanup and new canonical one-owner checked-edge admission/refusal. This is focused Linux x86-64 only, not full U2 acceptance. Subsequent exact-code documentation-head [Eristavi CI #41821258695](https://github.com/eristavi/eristavi-lang/actions/runs/41821258695) **SUCCESS** on `2c2270eeb7b5c95a066de561178827a0fdb172bd`: focused Linux Clang smoke executed 100 tests, 97 passed, 0 failed, 3 intentional skips, 435.467 seconds. The code inputs are unchanged from the tested implementation head; the four-platform matrix was skipped. Separate [#41821251378](https://github.com/eristavi/eristavi-lang/actions/runs/41821251378) succeeded on scope/patch only (focused smoke skipped), and is not the smoke evidence.
- **New private gate:** `src/compiler/u2_cleanup_canonical_x86_64.eri` consumes a frozen canonical Function with opcode 46 and a freshly verified scoped-owner profile, fallible registry, continuation binding, complete class-5 failure-root map and exact original private cleanup plan. Before output it confirms the selected instruction's source, operand, close FunctionId, source LocId, both checked edges and the typed failure destination/root; it then invokes the independently verified existing native cleanup emitter. The malformed-location regression refuses before emitting the forbidden symbol.
- **Closed admitted scope:** exactly one live File owner, no surviving outer owner, no already-failing entry, zero successful close results and one failure payload. It is an **ingress proof and forwarding adapter**, not full canonical CFG machine lowering or an SSA-liveness-aware machine-root publisher. The existing private native adapter performs actual File close execution; the bridge does not yet bind the canonical failure-root slot to that runtime scope, transport pending successful returns, lower arbitrary checked calls, unwind recursive checked frames or support multiple owners/mixed resource families.
- **Next engineering gate:** connect the verified selected failure ValueId/root-map record to an *actual* live native safe-point root word and checked outcome dispatch, with independent forced-GC and malformed/stale/foreign root tests. Extend from one owner to surviving prefixes, pending returns, multi-exit chains and recursive frames only after the bound slice passes. Measure physical retained memory/RSS and allocator refusal, then perform independent Stage-0/native A/B and completed-batch four-platform qualification.
- **Latest status check at 16:54 Cyprus time:** neither PR #111's implementation head nor issue #74 changed after the canonical checked-cleanup integration batch. Focused Linux smoke is now GREEN; U2 acceptance/merge remains blocked by actual canonical machine-root publication, general checked continuation/cleanup coverage, physical/fault oracles and final full qualification.
- **Do not merge** PR #111, close #74, change the production compiler, restart paused #51, or run experimental owned compiler self-build. Do not count the three intentionally skipped tests as passes.

### Earlier 4 November 2026 — real native File cleanup from verified U2 plans

- **Current tested code revision:** `3f36fa48e473ef554f003b0c0edcdc36c44f3a73`
  on `compiler/u2-cleanup-foundation-20261102`, draft
  [PR #111](https://github.com/eristavi/eristavi-lang/pull/111).
  U2 #74 remains OPEN and the compiler production path remains unchanged.
- **Hosted exact-code Linux U2 smoke:**
  [#41812694324](https://github.com/eristavi/eristavi-lang/actions/runs/41812694324)
  **SUCCESS**: patch/scope success, **99 tests executed, 96 passed, 0
  failed, 3 intentional skips**, 306.028 seconds. Four-platform matrix was
  intentionally SKIPPED; final completed-batch acceptance is not met.
- **Dedicated real native checked cleanup run:**
  [#41812694413](https://github.com/eristavi/eristavi-lang/actions/runs/41812694413)
  **SUCCESS**: one test method with four full native resource scenarios:
  (normal/previous failure) x (clean/forced-failing File closes), verifying
  actual reverse close order, exactly-once consumed File handles, pending
  primary preservation, ordered secondary FileError paths, class-5 saved
  failure/root survival through forced GC, and final no-leak shutdown.
- **New bounded native adapter:** `src/compiler/u2_cleanup_native_x86_64.eri`
  emits actual x86-64 close control flow from a *freshly independently
  verified* `u2_cleanup_plan.Plan`. The private closed profile admits
  1-8 File owners, zero surviving outer owners, caller-owned native resource
  slots in lexical acquisition order and a caller-owned saved failure record.
  It uses the existing `evn_cleanup_accumulate`,
  `erist_rt_failure_append`, `evn_bind_roots` and scope-leave runtime.
  It consumes and clears each native owner slot on both outcomes; returns
  0 or -1 checked status. No alternative executable IR, GC, type syntax,
  collector, Unicode17 data, public 32-byte ABI or default compiler edit.
- **Important qualification boundary:** this adapter consumes the private
  verified cleanup plan, **NOT a whole canonical Function opcode-46
  machine-lowering path**. It does not yet translate arbitrary fallible
  invocations, pending successful-return SSA values, surviving outer owners,
  all error/handler CFG paths, recursion-aware checked unwind or mixed
  resource types. The accepted scenarios prove bounded *real* File cleanup
  and ordered failure composition, not complete U2 managed runtime.
- **Next engineering gate:** bind whole-function canonical opcode-46 checked
  continuations and `FailureContext` root maps to this native adapter.
  Verify exact edge-only typed payloads, live/foreign/stale root rejection,
  pending-return transport, reverse close through surviving scopes and
  failure propagation across recursive frames. Then measure physical
  retained-capacity/RSS and finish differential, allocator-refusal and
  exact-head four-platform qualification.
- **Do not merge** PR #111 or close #74; do not restart paused #51,
  U3/U4 migrations or experimental owned compiler self-build.

### Earlier 4 November 2026 checkpoint — bounded native recursive Text roots verified

- **Current tested implementation source** `ec982e1d969b3144b04f5e453100b407c3a8a34b` on
  `compiler/u2-cleanup-foundation-20261102`, [draft PR #111](https://github.com/eristavi/eristavi-lang/pull/111).
  U2 issue #74 remains **OPEN**; no implementation has been merged to main.
- **Current exact-head Linux focused smoke:** [#41797941894](https://github.com/eristavi/eristavi-lang/actions/runs/41797941894)
  **SUCCESS**: patch/scope, **98 tests run, 95 passed, 0 failed, 3 intentional
  skips**; four-platform full matrix intentionally skipped.
- **Recursive native Text dedicated suite:** [#41797941881](https://github.com/eristavi/eristavi-lang/actions/runs/41797941881)
  **SUCCESS: 7 test methods, 0 failures.** Tested depths 0, 1, 3, 8, 31,
  repeated Text allocation/collection in child frames, caller Text retention
  after return, complete frame scope exit, and terminal refusal of depth 33.
- **Exact bounded native profile:** a verified *local self-call* declaration
  `u2.text.recurse` with signature `(Text, i64) -> i64` is admitted as a
  13th declaration beside 12 unchanged Text runtime imports. Every invocation
  roots its own incoming Text and depth words in a newly bound native
  scope/frame; caller frames remain registered while children allocate and
  collect. A private global counter limits this single-thread prototype to
  32 simultaneously active frames. The old zero-argument Text profile
  remains independently tested and unchanged. The source-neutral UIR,
  32-byte value ABI, Unicode17 policy and production compiler are unchanged.
- **Other tested Text behavior:** zero-based explicit byte/scalar/grapheme
  indexes, terminal negative/end bounds, immutable Text equality/copy/concat,
  explicit NFC normalization, conservative CFG loop roots and Unicode17
  typed primary/ordered-secondary *reference* failure-context payloads.
  Arbitrary slicing is intentionally excluded by locked pre-0.1 semantics.
- **Important limitations:** this is **not** arbitrary interprocedural
  recursion, multithreaded recursion, exact SSA root retirement, checked
  opcode-46 execution, rooted native FailureContext, actual file/resource
  adapters or exactly-once deterministic checked cleanup. The native recursive
  path still needs stale/foreign root rejection and physical GC retention
  evidence. The Unicode17 cleanup-context coverage is reference-only.
- **Next action:** implement actual checked invoke/FailureContext native
  publication and scoped reverse cleanup from existing canonical plans,
  including a pending return, a preserved Unicode17 primary Text failure,
  ordered secondary cleanup failures, GC safe points and recursive frames.
  Use independent semantic and native oracles; preserve old-runtime/ABI
  contracts. Then prove physical GC bounds and exact root liveness before
  completed-batch four-platform qualification. Do not promote or merge U2.
- **No work authorized or done on:** production promotion, unrelated U3/U4,
  paused optimization #51, expensive full owned self-build, U2 merge/closure.

### Earlier tested checkpoint — indexed Unicode17 and CFG Text

- Source `75a78d0673274373de6ff6e0651eba7d3db1d670`;
  [focused U2 #41793262699](https://github.com/eristavi/eristavi-lang/actions/runs/41793262699)
  SUCCESS 97 run / 94 passed / 0 failed / 3 intentional skips.
- [Dedicated Text/reference #41793262684](https://github.com/eristavi/eristavi-lang/actions/runs/41793262684)
  SUCCESS 6 test methods. This evidence remains historical, not the latest head.

Read the governing documents below before design or implementation. The user has
authorized continuing U2; historical stop instructions are superseded. A future
work list alone does not authorize unrelated development.

## Milestone status

| Area | Current disposition |
| --- | --- |
| U1a | Accepted within its documented scalar/SSA/call/Float/provenance/physical boundary; #77 closed, qualified PR #105 merged. |
| U1b | Bounded immutable aggregates/reference linked execution accepted; #73 closed, qualified PR #106 merged. |
| U2 | Bounded native CFG List-i64, Unicode17 Text/indexing/NFC, conservative roots and 32-frame local self-recursion. Native verified-plan File cleanup executes reverse close and ordered saved-failure composition. A new single-owner canonical checked-close ingress gate is focused-tested; general opcode-46 CFG lowering, machine root publication, recursive checked unwind and complete managed-root/resource acceptance remain OPEN. #74 OPEN, #111 DRAFT/unmerged. |
| U3 | Initial isolated Python shadow/planning foundation merged in #119; #75 OPEN. Direct production AST-to-owned-UIR integration remains unfinished. |
| U4 | Initial parallel-move foundation in draft #120; #102 OPEN. Full machine migration remains unfinished. |
| Production | Existing frontend/default compiler and 32-byte ABI retained. Latest recorded qualified production optimization is #110. No redesigned-UIR promotion. |
| Optimization #51 | OPEN / PAUSED. Do not restart its benchmarks or rejected pilots. |
| Full owned-compiler self-build | NOT CERTIFIED; excluded from routine work without explicit authorization. |

U2 code is on its draft branch, not main. Publishing this same recovery document
on main does not merge U2 implementation. Fetch current refs before continuing.

## What U2 currently implements

| Component | Implemented scope and boundary |
| --- | --- |
| Checked continuations | Canonical opcode-46 invokes, versioned FunctionId contracts, edge-only results and typed carried values. |
| Cleanup and owners | Independently verified reverse-cleanup plans, bounded canonical close construction, lexical owner signatures, success-only acquisition and consumption on both close outcomes. Complete resource adapters remain open. |
| Failure contexts | Typed Unicode17 primary/ordered-secondary reference models, class-5 saved-failure publisher probes, and **real native File close failure composition** from verified private cleanup plans. A bounded one-owner checked-edge admission now verifies canonical metadata before emitting the existing native adapter. Whole canonical opcode-46 native failure dispatch, all SSA/handler exits and complete cleanup integration remain open. |
| Liveness | Independently recomputed CFG/SSA plan and publication obligations; the native List-i64 profile now applies verified successor live-in facts to retire dead List roots after edge transfers for <=32 tracked List values. Per-instruction/all-managed-root coverage remains open. |
| Managed types | Owner-scoped Text/List/identity descriptors, independent corruption rejection and Unicode17 copy/view contracts; expanded Stage-0/C/owned parity oracle with predeclared accent/flag/ZWJ/empty/ASCII/copy values. This is not general canonical managed execution. |
| Native Text/Unicode17 | Twelve exact runtime imports support scalar creation, immutable concat/copy/equality, byte/scalar/grapheme counts/indexing, explicit NFC and collection. Bounded CFG and 32-frame local self-recursion retain managed roots. A separate native verified-plan File cleanup adapter composes real saved failures; no arbitrary opcode-46 Text checked failure, general recursion, precise root retirement or full Text integration. |
| Native List-i64 | Eristavi-written optional x86-64 adapter for empty/copy/append/replace/count/get/collection, branches/joins/backedges/cyclic transfers; verified successor-edge root retirement now focused-tested for <=32 selected List values. |
| Native boundaries | Managed-registry entry validation, Int/Bool/List runtime descriptor checks, List bounds source name/line/column, independent fixture frame-layout checks, GC/snapshot/reclamation and fault probes. |

The native List profile is capped at **64 blocks, 512 edges, 128 SSA values and
256 instructions**, with seven exact version-one runtime imports and an opaque
structural carrier interpreted only by that legal profile. It is not a general
managed-type encoding or frontend integration.

Single-block roots use last-use clearing. In the closed multi-block List-i64
profile, up to 32 selected List-carrier SSA values now receive independently
verified successor live-in-based dead-root clears **after** simultaneous edge
copies and before the next allocation. Other managed value families are not
classified by this adapter. More than 32 selected List values retain bounded
conservative all-block retention; other boxed values and deaths inside blocks
also remain conservatively rooted. This is not general exact machine root
publication/release. Managed-local promotion, arbitrary runtime/descriptor
compatibility and physical retention bounds are still outstanding.

## Validation and evidence

| Revision / run | Verified result |
| --- | --- |
| `2c2270eeb7b5c95a066de561178827a0fdb172bd` — [Linux smoke #41821258695](https://github.com/eristavi/eristavi-lang/actions/runs/41821258695) | **SUCCESS:** 100 tests run, **97 passed, 0 failed, 3 intentional skips** (435.467 s); source implementation unchanged from `12bba417`. Four-platform matrix skipped. |
| `12bba417a822db605addf66304608d448f246490` — [focused canonical/native #41821092507](https://github.com/eristavi/eristavi-lang/actions/runs/41821092507) | **SUCCESS:** two Linux x86-64 native cleanup test methods; original real File cleanup and canonical single-owner admission with bad-location refusal. Full four-platform U2 acceptance **not** performed. |
| `3f36fa48e473ef554f003b0c0edcdc36c44f3a73` — [CI #41812694324](https://github.com/eristavi/eristavi-lang/actions/runs/41812694324) | **SUCCESS:** exact-code Linux Clang focused smoke 99 run / **96 passed, 0 failed, 3 intentional skips**, 306.028 s; patch check passed; four-platform test matrix intentionally skipped. |
| `3f36fa48e473ef554f003b0c0edcdc36c44f3a73` — [dedicated #41812694413](https://github.com/eristavi/eristavi-lang/actions/runs/41812694413) | **SUCCESS:** one test method, four real native File cleanup scenarios; reverse owner ordering, primary plus secondary error payloads, forced GC, no remaining open resources and consumed slots. |
| `ec982e1d969b3144b04f5e453100b407c3a8a34b` — [CI #41797941894](https://github.com/eristavi/eristavi-lang/actions/runs/41797941894) | **SUCCESS:** exact-head patch/scope and focused Linux Clang U2 smoke; **98 run, 95 passed, 0 failed, 3 intentional skips**. Full four-platform matrix intentionally skipped. |
| `ec982e1d969b3144b04f5e453100b407c3a8a34b` — [Text #41797941881](https://github.com/eristavi/eristavi-lang/actions/runs/41797941881) | **SUCCESS:** seven focused native Text methods, including distinct managed root frames, GC, depth 31 and depth-limit terminal fault. |
| `75a78d0673274373de6ff6e0651eba7d3db1d670` — [hosted #41793262699](https://github.com/eristavi/eristavi-lang/actions/runs/41793262699) | **SUCCESS:** patch/scope and Linux Clang focused U2 smoke, **97 run / 94 passed / 0 failed / 3 skips**, 354.352 s. Indexed Unicode17, native CFG roots and typed Text failure-context reference included. Full matrix skipped. |
| `75a78d0673274373de6ff6e0651eba7d3db1d670` — [dedicated #41793262684](https://github.com/eristavi/eristavi-lang/actions/runs/41793262684) | **SUCCESS:** six focused native Text plus reference FailureContext methods, zero failures. |
| `5377eda39ff18c86a8c8b65d5bf2a9daf9d115e0` — [dedicated #41792856568](https://github.com/eristavi/eristavi-lang/actions/runs/41792856568) | **SUCCESS:** five focused native Text methods, including bound checks and loop-backedge GC roots. |
| `f4c074d5e04cf3bcab987cc635cb2b4667640f22` — [dedicated #41792081080](https://github.com/eristavi/eristavi-lang/actions/runs/41792081080) | **SUCCESS:** four native Unicode17 Text methods, indexed views and explicit NFC. |
| `bce2e9c59b7c997d436f9b74980a31b6c4878aa2` — [hosted U2 #41789413729 attempt 2](https://github.com/eristavi/eristavi-lang/actions/runs/41789413729) | **SUCCESS:** scope/patch and Linux Clang focused smoke, 95 run, **92 passed, 0 failed, 3 intentional skips**, 421.127 s. Exact code tested; full platform matrix skipped. |
| `bce2e9c59b7c997d436f9b74980a31b6c4878aa2` — [dedicated Text #41789413436](https://github.com/eristavi/eristavi-lang/actions/runs/41789413436) | **SUCCESS:** three native Text/Unicode17 test methods, eight value/view cases plus corrupted descriptors/imports and invalid scalar fault. |
| `d2a25a82d9d8216f494118b348878e25176903d1` — [hosted #41718084522](https://github.com/eristavi/eristavi-lang/actions/runs/41718084522) | **SUCCESS:** scope/patch check and Linux Clang focused smoke: 92 run, **89 passed, 0 failed, 3 intentional skips**; 382.990 s. Includes List snapshots, loop/backedge, cyclic swap, GC and added edge-clear assembly assertion. Full platform matrix SKIPPED. |
| `5bcaf8533bedc44f0b4689c3d0cbddc2c1fc9ac3` — [hosted #41711062178](https://github.com/eristavi/eristavi-lang/actions/runs/41711062178) | **SUCCESS:** earlier fixture-only EOF repair; scope and focused Linux smoke passed. |
| `c7149aee5102b67b2a68e888776406ea01a0035e` — local coherent smoke | 92 run, **89 passed, 0 failed, 3 intentional opt-in skips**, 255.341 s. Covers CFG List snapshots/cyclic swaps, registry/runtime rejection, bounds origins and existing regressions. |
| Same revision — hosted #41698723325 | **FAILED scope/patch check**; smoke and full matrix skipped. Local success does not override this failure. |
| `2619885a2ff7043dda4080e722ffe31c8806f495` — hosted #41696878635 | Scope and focused Linux smoke SUCCESS; full platform matrix skipped. Earlier single-block native slice only. |

Original implementation source hashes and raw outcomes/logs (unchanged by fixture-formatting repairs):
[JSON](https://github.com/eristavi/eristavi-lang/blob/c7149aee5102b67b2a68e888776406ea01a0035e/docs/evidence/2026-11-03/u2-list-cfg-smoke.json)
and [raw log](https://github.com/eristavi/eristavi-lang/blob/c7149aee5102b67b2a68e888776406ea01a0035e/docs/evidence/2026-11-03/u2-list-cfg-smoke.log).
Exact native scope, algorithms and exclusions:
[List-i64 contract](docs/architecture/UIR_U2_LIST_I64_NATIVE.md) (branch current); the earlier pinned file remains historical evidence.

Three skipped probes are not passes. No full U2 four-platform CI or
completed-batch qualification has passed. Earlier CI #41698723325 failed
only because three fixtures had surplus EOF blank lines; the corrected
fixture revision and subsequent edge-retirement revision both passed hosted
focused smoke. The successive 382.990, 421.127 and 354.352 s smokes are NOT paired
performance measurements; no whole-compiler speedup or verified physical
retention/RSS improvement is claimed. Intermediate failed
candidate CI runs #41714642589/#41715592713/#41716173164/#41716892840
were corrected before final passing revision, and are historical failure
evidence only.

## Remaining U2 acceptance, in order

1. Extend independently verified List edge-root pruning with corruption
   rejection (missing, prematurely cleared, stale/foreign and dead-published
   roots), explicit collection at the destination, and actual retained-owner,
   collector/traffic/RSS evidence; avoid interpreting assembly pattern checks
   as full physical proof. Measure compile/emit overhead on matched inputs.
2. Move from bounded successor-only List root retirement to exact per-instruction
   managed-value publication/release on verified canonical CFG, preserving
   loop/recursion, checked-failure, terminal fault and cleanup boundaries.
   Resolve the current 32-tracked-List-value profile limit deliberately;
   keep conservative fallback until new proof is qualified.
3. Complete general canonical managed representation and eligible-local
   promotion; the bounded Text/Unicode17 adapter now has view indexes, NFC,
   conservative CFG-loop roots and an exact local self-recursion profile with
   registered native frames. General interprocedural/thread-safe recursion,
   stale/foreign-root rejection, exact managed safe-point retirement,
   Text-containing aggregates, comprehensive API/source behavior, nested
   Lists and identity-cycle integration remain. Arbitrary Text slicing is
   deliberately postponed by frozen pre-0.1 semantics.
4. Connect complete checked FailureContext and resource adapters to **whole
   canonical Function opcode-46** native lowering: the new separately verified
   private-plan File close adapter demonstrates actual reverse-order closure,
   GC-rooted saved primary and ordered secondary FileErrors for bounded
   1-8 owner full exits, but has NOT lowered general checked invokes or typed
   edge payload transport. Finish pending returns, surviving owner prefixes,
   all exits, recursion/handlers, ordered Unicode17 Text failures, and exact
   live machine-root publication/release. Unicode context reference tests
   remain reference-only outside the bounded real File adapter.
5. Complete independent behavior/source-origin comparisons, deep/malformed/dead
   CFG cases, cancellation, sanitizer/allocator-refusal and actual owner/traffic/
   RSS/latency evidence under preselected limits.
6. Once coherent acceptance is met, run one exact-head four-platform CI and
   required completed-batch qualification; compare tested/merged trees before
   any U2 merge/closure. Keep #74 OPEN and #111 DRAFT until then.

## Governing documents and recovery

Read this handover, the complete [design philosophy](DESIGN_PHILOSOPHY.md),
[language semantics](LANGUAGE_SEMANTICS.md), applicable locked rules and
[CI qualification policy](CI_QUALIFICATION.md). Follow **Philosophy → Semantics →
Architecture → Implementation**.

Read the typed UIR architecture/U1 contract through [the records index](docs/README.md).
For current U2 branch contracts, use this
[pinned architecture directory](https://github.com/eristavi/eristavi-lang/tree/c7149aee5102b67b2a68e888776406ea01a0035e/docs/architecture):
remaining UIR acceptance, continuations, fallible registry, scoped owners,
multi-close lowering, managed types, canonical root map, failure-root boundary,
native-root publication and initial budget policy. Also read
[cleanup semantics](RESOURCE_CLEANUP.md) and [owned resource runtime](OWNED_RESOURCE_RUNTIME.md).
Dated contracts retain governing decisions; outdated status paragraphs are
superseded by this handover, not permission to repeat completed work.

## Historical recovery records

The full pre-cleanup handover text is retained (terminal blank lines normalized):
[U2 branch snapshot](docs/history/2026-11-03/HANDOVER_BEFORE_CURRENT_ONLY_CLEANUP_U2.md)
and [main snapshot](docs/history/2026-11-03/HANDOVER_BEFORE_CURRENT_ONLY_CLEANUP_MAIN.md).
Exact original bytes remain at U2 revision `c7149aee5102b67b2a68e888776406ea01a0035e`
and main revision `0f7cd0af57777c73686f02b61b7991f68dcc8757`.
Older archives and raw evidence remain in Git. Consult them only for a specific
decision or measurement; old commands, stops, pending notes and “next” sections
are historical, not active instructions.

## Architecture and working boundaries

- Follow **Philosophy → Semantics → Architecture → Implementation**. Complexity
  belongs in the compiler/runtime; preserve a small, readable source language.
- Approved AST plus frozen semantic facts eventually build one source-neutral
  typed UIR directly. No extra mandatory source-close executable Typed IR.
  Preserve old paths and independent oracles until U2/U3/U4 gates pass.
- Independent owned metadata, immutable SSA, explicit effects, fresh all-block
  verification and mandatory eligible-cell promotion remain required. No fake
  Void value, stale verified flag or unchanged revision substitutes for proof.
- Checked signed Int64, strict binary64, value vs identity semantics and
  deterministic scoped resources stay frozen. Normal/checked exits require
  exactly-once reverse cleanup. Standalone terminal defects do not unwind;
  process termination promises no flush/durability or persistent-lock release.
- RevaSM is a peer target, not a compulsory intermediary. Preserve existing
  32-byte ABI boundaries, private-memory and generic compatibility adapters.
  Moving GC, a new address/provenance design, generic-template replacement,
  public UIR serialization/new artifact extensions and FS-001 remain separate
  decisions; do not introduce them as prerequisites or settled policy.
- Use `.eri` for source/implementation and `erist` for the toolchain; `.erist`
  remains reserved. C/Python are bootstrap tools, not intended permanent target
  dependencies. Major layer redesigns require the recorded technical review.
- Work autonomously within authorization, give concise progress updates and
  do not request repeated routine GitHub permission. Do not spawn sub-agents
  without an explicit applicable user/AGENTS.md/skill instruction.

## Standing GitHub authorization — explicit user instruction, 2026-11-01

The repository owner has **explicitly authorized ChatGPT to act on their behalf using the connected GitHub account**, without repeatedly asking permission for routine project work. Treat this as standing authorization for investigating repositories, reading files and issues, creating/editing commits and branches, updating PRs/issues/documentation, running available tests and workflows, and merging/closing completed milestones **when their documented acceptance gates actually pass**. Execute the requested work directly, provide results and evidence, and do not interrupt progress with redundant permission questions. This instruction applies to future Eristavi handovers and working sessions. Connected tool capabilities and service authorization remain binding; do not claim an action succeeded unless verified. Preserve philosophy, frozen semantics, CI/qualification rules, release safety and careful irreversible-action checks. **The standing authorization does not waive acceptance criteria or authorize previously excluded experimental full owned-compiler self-build tests.**

### Standing publication authorization — explicit user confirmation

The user explicitly approved publishing the updated full handover and raw evidence archive to the public `eristavi/eristavi-lang` GitHub repository and instructed: **“yes sure, you always have to do it.”** Treat routine publication of this project's handovers, performance reports, source patches, diagnostic logs, measurement summaries and evidence archives to that same repository as authorized project work. Keep these records current automatically, without repeatedly asking for routine publication permission. This does not authorize unrelated data disclosure, bypass service restrictions or waive correctness, qualification and merge gates.

## Mandatory philosophy-first engineering discipline — standing user instruction

**At the beginning of every new Eristavi chat, and before any material design, implementation, optimization or milestone decision, read and FOLLOW the actual governing project documents. Do not rely on the handover summary, old conversation memory or a milestone checklist as a substitute. This is a permanent user requirement; the user must not need to repeat it.**

1. **Read current sources first:** current `HANDOVER.md` (latest authoritative checkpoint and historical supersession), the **complete `DESIGN_PHILOSOPHY.md`**, `LANGUAGE_SEMANTICS.md`, applicable locked semantics and the relevant current architecture/IR contracts, then `CI_QUALIFICATION.md`. For a status-only request, verify current GitHub/CI/issue facts and describe the extent of the documents actually reviewed; never claim to have read something that was not inspected.
2. **Use the non-negotiable design order:** **Philosophy → Semantics → Architecture → Implementation**. Specify the intended meaning and review architectural consequences *before* choosing an implementation. Implementation convenience cannot weaken or silently redefine frozen semantics.
3. **Preserve the design constitution:** small stable language vocabulary; one obvious, readable, precise way to express fundamental concepts; strong static guarantees with sensible inference; rich libraries instead of unnecessary syntax; automatic safe memory and deterministic scoped cleanup for external resources; explicit low-level danger; excellent diagnostics; and universal portability. **Complexity belongs in the compiler/runtime, not in the programmer's code.** A feature must justify its permanent conceptual cost.
4. **Optimization-first, but never correctness-last:** correctness, safety and locked semantics are absolute gates. After them, execution and compilation speed, bounded physical memory, allocation/GC pressure, predictable work/cancellation and efficient CI are the **highest engineering priorities from initial design onward**. Define representation, algorithmic complexity, ownership/peak/traffic budgets and before/after measurements. Distinguish per-owner physical backing, total allocator traffic and process RSS. Never advertise a microbenchmark or rejected prototype as whole-compiler speedup.
5. **Keep the architecture and compatibility intact:** source-neutral typed Universal IR and independently verified publication; no extra mandatory source-close executable Typed IR; machine- and OS-independent semantics; C/Python as bootstrap tools rather than permanent target dependencies. Preserve the frozen Eristavi source behavior, the existing 32-byte public ABI, fault/source-location and exactly-once cleanup semantics, independent reference oracles, rollback and the default production compiler until the redesigned path passes its own U2/U3/U4 acceptance gates. Avoid speculative whole-compiler rewrites or unapproved new syntax/ABI/artifact formats.
6. **Qualify proportionately:** focused tests, independent positive/negative/oracle checks and resource/fault probes while developing; full four-platform CI and required completed-batch qualification **once per coherent final implementation batch**, never after every helper. Documentation-only changes require a lightweight patch check; never initiate experimental owned full compiler self-build without explicit user authorization. Report `planned`, `implemented`, `tested`, `qualified`, `merged` and `deferred` distinctly.
7. **Carry the rule into every future handover automatically:** each work session must reconcile current decisions and evidence in this document; keep opening instructions, current status and newest recovery checkpoint consistent, including philosophy, locked semantics, performance/CI rules and next actions. If a future handover is edited, **retain this section and propagate its requirements**. Do not make the user remind us to follow the project's philosophy.

## Mandatory handover maintenance — standing user instruction

**HANDOVER.md must stay current at all times. Updating it is part of every
project task, not a separate task that waits for the user to request it.**

- Read the current handover before continuing work. Update it immediately after
  each material implementation change, architectural decision, validation result,
  PR status change, merge, blocker or change to the next step.
- While work is in progress, record the active branch and what is pending.
  Distinguish implemented, tested, qualified and merged states. Never leave
  merged work labelled as a candidate or completed checks labelled pending.
- Keep the opening recovery instructions, current-status table and latest
  checkpoint consistent, with exact relevant commits, test evidence, limitations
  and next actions. Preserve older evidence as clearly superseded history.
- Include the handover update in the working batch and reconcile its final
  merge/qualification status promptly afterward. Before every final user reply
  about project work or session handoff, verify the checkpoint reflects the
  actual state; do not declare the task complete with a stale handover.
- Status-only documentation updates need a lightweight patch check. Reuse valid
  qualification evidence for unchanged implementation; do not rerun expensive
  compiler/runtime tests merely to keep this file current.

## Optimization-first engineering policy — standing user priority

**From this checkpoint onward, treat runtime and compiler performance,
memory/resource efficiency, and predictable compilation times as the
HIGHEST development priorities, after correctness, safety and frozen
language semantics.** Every newly designed or revised compiler/runtime
component must budget algorithmic cost, hot-path allocations, retained
memory, work/GC pressure, cancellation and determinism before adoption.
Do not accumulate avoidable temporary boxes, repeated full-heap passes,
redundant indexing, unbounded caches or unnecessarily expensive CI.

- Preserve the existing frontend, ABI, fault and cleanup order, independent
  acceptance oracles and observable language behavior. Never trade safety
  or correctness for benchmark gains; never skip/delete tests to look faster.
- Establish and retain **before/after** targeted wall/CPU,
  allocation/collection counts, modeled owner capacity/traffic and actual
  physical resource samples, stating attribution and platform limits.
- For incremental changes run the narrowest useful focused tests and
  differential/fault/forced-memory probes; run the complete four-platform
  CI plus required qualification **once per coherent final code batch**.
  Never enable experimental owned compiler full self-build without permission.
- Give priority to existing measured runtime bottlenecks before introducing
  competing optimizations. Prefer bounded, reversible production edits with
  explicit allocation-failure and no-allocation fallback. Resist public
  ABI churn, speculative whole-compiler rewrites and benchmark overclaiming.
- Maintain a ranked optimization backlog and update this handover after
  implementation, qualification, merge or a discovered performance regression.
  An unqualified prototype is not production-ready or a future CI time guarantee.
The separate optimization investigation #51 is currently **PAUSED** by the user.
The policy above continues to govern future design; it does not authorize
restarting paused benchmarks, rejected pilots or the capped compiler workload.

Keep this file current-only: replace superseded status rather than appending
contradictory recovery checkpoints. Move dated history to `docs/history/`,
retain raw evidence and link it. Preserve all standing instructions above.
