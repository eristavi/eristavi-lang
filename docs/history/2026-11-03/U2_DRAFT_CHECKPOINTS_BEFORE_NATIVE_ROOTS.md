# Archived U2 incremental checkpoints — 3 November 2026

These are superseded development checkpoint notes preserved verbatim from HANDOVER.md. The current HANDOVER.md governs the next actions.

## Verified canonical U2 root-map checkpoint — 3 November 2026

**New opt-in metadata implementation accepted at focused-test level:** `src/compiler/u2_root_map.eri` derives one versioned class-5 saved-failure root record for every canonical opcode-46 checked invoke, keyed to the exact Function owner, revision, failure-destination first SSA parameter, structural TypeId and LocId. The independent `verify` scans **all** canonical instructions, including unreachable ones, and rejects missing/extra/reordered/malformed/foreign/stale records; prototype bound is 128 invokes / 768 record words, O(instructions+roots) per scan with owner-accounted storage. This is a machine-neutral root **metadata** stage and is not a new executable IR, collector, ABI or native root-slot publisher.

**Evidence:** [focused Linux Clang run #41598271890](https://github.com/eristavi/eristavi-lang/actions/runs/41598271890) at `7a62ea833b8feed3044e554b280faf2c4218662a` passed **80 tests / 77 passed / 0 failed / 3 skipped**, including all five original canonical invoke roots and corrupt-class/missing/stale-map refusals. [Run #41599088883](https://github.com/eristavi/eristavi-lang/actions/runs/41599088883) at exact code head `24e6b4d1e84ba7fb500bfe609534102d3467ead6` also passed **80 / 77 / 0 / 3**, 208.292 seconds; the regression adds a sixth **unreachable checked invoke** and mutates **every one of six root-record fields**, with restored map accepted. Both include passing [native primary/secondary forced-GC tests](https://github.com/eristavi/eristavi-lang/actions/runs/41597194105) and typed cleanup semantic matrix. The next handover-only commit does not change tested source.

**Unfinished U2 acceptance:** metadata alone cannot keep managed payloads alive. Target lowering must bind every verified canonical SSA root to an *actual live machine slot*, publish/update class tables before allocations/unwind, preserve full primary and ordered secondary checked contexts (including Text, List, identity) across collections and returns, and release only after propagation or handler completion. The existing native runtime was explicitly tested, but end-to-end **UIR-generated root-map publication** is not done. Real resource adapters, physical attribution, allocator fault/loop/dead-code conformance, parity and final four-platform completed-batch qualification are still open. PR #111 remains DRAFT, issue #74 OPEN, `main`/32-byte ABI unchanged, optimization #51 PAUSED.

## Latest U2 native GC and remote CI checkpoint — 3 November 2026

**New verified native GC evidence:** [focused GitHub Actions run #41597194105](https://github.com/eristavi/eristavi-lang/actions/runs/41597194105), exact source head `0831d2af204f6019777fac2c92779ac0b5fe0046`, completed **SUCCESS**: 79 tests run, 76 passed, 0 failed, 3 opt-in skipped, 272.115 seconds. Both newly added `FreestandingGraphValueTests.test_u2_saved_failure_root_survives_explicit_gc_and_releases` and `test_u2_primary_and_secondary_survive_forced_gc_in_order` passed, as did nested canonical cleanup and the typed 16-case failure-semantic matrix. The current successor is handover-only.

The two native Linux x86-64 **direct-runtime** probes use the existing class-5 `evn_bind_roots` failure root, explicitly call slot and Text collectors four times while the failure context is live, check the retained typed primary Text and ordered linked secondary Text, count collector entries, then release the root and demand no live saved failure records. The secondary test builds and links the **actual resource runtime** supplying `erist_rt_failure_append` (source commit `0831d2af204f6019777fac2c92779ac0b5fe0046`). A test-only global counter avoids invalid cross-object local symbol references. This validates the existing native runtime failure root/tracer and cleanup-failure chain under explicit collections; **it does not validate UIR-emitted machine root maps or native execution of new canonical cleanup instructions.**

**Remote execution restored:** branch-scoped `push` smoke in `.github/workflows/ci.yml` at `a3e3cadbc353a66dc10b39060f33d25cd70487ae`. The `scope` job rejects malformed patches, filters documentation-only commits, and runs focused Linux Clang tests for non-doc changes on only `compiler/u2-cleanup-foundation-20261102`. It does not run the full four-platform matrix; four-platform qualification is still explicitly gated. PR #111 is the sole active U2 development PR. Supporting PRs #112–#118 were closed without merging after code/evidence reconciliation.

**Next substantive U2 development:** publish and independently verify canonical SSA failure contexts in actual target machine root slots at every allocating or unwinding safe point, including complete secondary-list/managed Text/List/identity liveness and dead-code/malformed-map rejection. Then integrate real checked resource adapters and physical/forced-failure evidence; qualify complete U2 only after explicit independent native/Stage-0 parity and final four-platform CI. Issue #74 remains OPEN; PR #111 remains DRAFT; default production compiler, frozen ABI, and optimization #51 pause unchanged.

## Latest U2 consolidated and owned-runtime verification — 3 November 2026

Two incremental exact-head focused Linux Clang CI gates now pass:
- [Consolidated U2 validation #41593072164](https://github.com/eristavi/eristavi-lang/actions/runs/41593072164), head `bb338d651faff86005cd50ee184c81bdcea26f62`: **76 executed / 73 passed / 0 failed / 3 opt-in skipped**. Exercises the 16-case typed semantic matrix, canonical two-owner checked cleanup including inner-close failure, and independently rejects forged root type and released root pin.
- [Owned runtime pressure #41593073584](https://github.com/eristavi/eristavi-lang/actions/runs/41593073584), head `faf6b4c9985040df7e565f48fd0222d1c4534941`: **77 executed / 74 passed / 0 failed / 3 opt-in skipped**. Builds, assembles and links a static Eristavi-owned-runtime program; preserves the reference failure-root pin through 384 temporary typed failure contexts, then closes all charged backing. Owned probe itself passed in 18.6 seconds; full focused smoke took 260.797 seconds.

The tested `tests/test_u2_failure_root_binding.py` is promoted to the primary draft branch using the **exact passing Git blob** `c59ff7ca02601833874bf415a5dbf34ec3b9441a`, together with this documentation update. All other implementation/fixture files were already promoted byte-for-byte from passed PR #115 in commit `a841c38fbdc08a915e64f464b09278a372aa527f`. These are **focused branch-content equivalence checks, not exact-head four-platform qualification**. Do not confuse the owned reference pin/automatic allocation pressure with explicit forced GC traversal or a published native UIR safe-point root map. In particular, the three opt-in probes skipped by standard smoke still require separate evidence.

**Remaining U2 acceptance gates:** canonical managed Text/List/identity with Unicode17 and copy/alias semantics; native rooted FailureContext with primary and ordered secondary payload survival under forced collections, allocations, unwinds and loops; real checked resource adapters and verified root-map publication; extensive negative/dead/loop/physical/RSS/failure-injection tests; Stage-0/current-native independent execution parity; four-platform completed-batch CI/qualification and explicit release review. PR #111 stays DRAFT, issue #74 stays OPEN, production main/ABI unchanged, optimization #51 paused.

## Current U2 accepted-development checkpoint — 3 November 2026

**Incremental focused CI is green, not full U2 acceptance.** The three-resource typed checked-failure semantic matrix passed on PR #114 [run 41591696832](https://github.com/eristavi/eristavi-lang/actions/runs/41591696832), head `38875824f4347a50c1d4140f1a42e53f4ab4ed11`: **75 tests, 72 passed, 0 failed, 3 opt-in skipped**, including 16 body-state/close-failure combinations. The canonical failure-edge reference-root binding and pin-release lifecycle passed on PR #115 [run 41591975769](https://github.com/eristavi/eristavi-lang/actions/runs/41591975769), head `90946b8c6031c895395057518e580d7bc39b4f04`: **76 tests, 73 passed, 0 failed, 3 opt-in skipped**. Both runs also passed the tested two-stage nested close and checked inner-failure→outer-close regression.

**Source-integrity promotion:** the 10 changed source/test/architecture files from the passing PR #115 head are copied to the primary U2 draft PR #111 using their exact Git blob IDs (no retyping or manual edits to these 10 files). The current HANDOVER.md is updated in the same atomic tree commit. A separate exact-head focused smoke must still validate this consolidated PR #111 tree; earlier green PRs are not exact-head release qualification. Production `main` remains untouched; optimization #51 stays paused.

**Scope and blockers:** `u2_cleanup_lower.emitAt` implements checked canonical opcode-46 cleanup stages under fresh full-plan verification and independent owner checks. `u2_failure_trace` independently walks bounded private plans with complete typed primary/secondary Text payloads. `u2_failure_root_bind` binds an identity-held typed context to a canonical checked-failure block parameter, and releasing it clears the strong reference. This is a **reference pin and structural canonical binding**, NOT native GC safe-point root-map publication, retained payloads under forced physical GC, an executable real file-resource UIR adapter, U2 managed Text/List/identity values or complete multi-exit/loop conformance. Three opt-in native probes were skipped in focused smoke and require separate evidence. Final gates remain: actual safe-point roots, managed values/Unicode17/identity, physical allocator and GC evidence, exhaustive malformed/exit coverage, Stage-0/native independent parity, full four-platform CI and completed-batch qualification. Keep U2 issue #74 OPEN and PR #111 DRAFT; no merge into `main`, final acceptance, or owned compiler self-build.

## Historical focused checkpoint — 2 November 2026 — 2 November 2026

Remote focused test [run 41517841788](https://github.com/eristavi/eristavi-lang/actions/runs/41517841788) completed SUCCESS on PR #112 head `f7a2d60de7d812adce53bbd3662f15b4e972fa71`: **72 tests run, 69 passed, 3 intentionally skipped, 0 failed, 209.400 seconds**. Exact relevant named regressions passed: `test_verified_cleanup_plan_emits_canonical_close_on_both_exit_modes`, `test_primary_and_ordered_typed_context`, `test_primary_and_ordered_cleanup_failures`. The skipped opt-in owned runtime tests were not qualified by this run. The single-close lowering and typed-context budget fixes were copied byte-for-byte to the existing draft U2 branch, with Git blob equality verified, via implementation commits `92bde58350d3ceaf380c8b478d4bda3b4ac3e8d1`, `3cf136d70f6769b39ca321a8d8c9ce4f84a73408`, and fixture commit `59fe9579ef0cd6862d46926f840aa1d2592f637b`. This is focused cross-branch source equality, **not an exact-head full qualification**. PR #111 remains draft; #74 remains open. Next: multiple-owner canonical cleanup chains with proper primary/secondary FailureContext handling; independently verify every metadata contract and owner/edge/root at all exits, then stress/fault/physical evidence. Do not launch full CI or owned compiler self-build prematurely.

## Historical early U2 development checkpoint — 2 November 2026

The user explicitly resumed implementation. Commit `2b39463e4be6fdb84ec119cddee3fc7b8e2eb165`
adds `src/compiler/u2_failure_order.eri`, a **private, untested** bounded
owner-scoped ordered checked-failure token ledger. It retains an existing primary,
promotes the first cleanup failure when none exists, and appends subsequent
failure tokens in cleanup order. Tokens are **not rooted typed error objects**;
this is not complete managed FailureContext, canonical resource lowering,
Text/List/identity support or U2 acceptance. The implementation has not been
compiled or run through focused tests; its API and allocation-failure behavior
require review before adoption. PR #111 remains draft; #74 remains open.
Follow-up commit `61fa433aa8c21ddd011b18b935759655cd2946c6` fixes an
identified constructor refusal path: the charged control allocation is released
if word-store creation fails. This is a code review correction, **not tested**.
New test fixtures in commits `c1724255540af024cde32e86d044203734a736ac`
and `4ecfb79606e9754d2adf81e53c243db0222a2563` exercise initial
primary/secondary order, already-active body failure, and charged owner
reclamation through a focused native Python unittest. **Not executed:**
this environment cannot access the repository via git/network, and the
connected GitHub actions do not provide a workflow dispatch or remote shell.
Do not claim these tests passed. The ledger is not a rooted FailureContext.
Next: compile and independently test the ledger, prove refusal/cleanup behavior,
then connect verified plans to canonical resource operations and managed roots.
Do not merge or run full qualification until coherent acceptance gates pass.

## 93. U2 cleanup-lowering validation checkpoint — 2 November 2026

**Active, unqualified branch:** `compiler/u2-cleanup-foundation-20261102`, PR #111 draft. The opt-in `src/compiler/u2_cleanup_lower.eri` adapter now emits an actual canonical UIR opcode-46 checked close through `u2_invoke_transfer.emit`, after independently rechecking the current semantic cleanup plan and binding. This initial slice deliberately admits exactly one exiting owner per call; owner-prefix transfers and normal versus already-failing modes are explicit. It does not implement complete multi-close chains, return cancellation/typed FailureContext composition, GC roots or production resource execution. The independent canonical and scoped-owner verifiers remain authoritative; emission is not trusted publication.

**New regression:** `tests/test_u2_scoped_owners.py` now transforms the existing 11-block scoped owner fixture to use the lowering adapter for its outer normal close and its pending-failure close, and then executes the existing positive/mutation/refusal checks. `tools/run_ci_tests.py` explicitly includes the new typed FailureContext and failure-order tests in the focused smoke profile. These additions **have not yet been observed to pass**. A GitHub PR synchronize should start a smoke run; inspect the exact new head and logs before reporting results. Local git clone still fails due to DNS resolution in the working container. Do not claim validation or U2 completion on the basis of file commits alone.

**Engineering review pending:** the adapter's full contract table must receive independent all-entry verification (not just the selected entry); canonical owner proof after emission, failure/payload trace parity, source origin, error and allocator refusal, and profile extension for every exit depth remain acceptance gates. The typed identity-linked FailureContext remains a semantic reference, not a pinned canonical root map. The next action is to inspect the focused smoke run, fix real failures, and continue native rooted cleanup integration; defer full four-platform CI until a coherent completed implementation batch.

## 92. Current U2 checkpoint

**New 2 November continuation (unqualified):** On branch `compiler/u2-cleanup-foundation-20261102`, added `src/compiler/u2_failure_context.eri`, `tests/fixtures/u2_typed_failure_context.eri`, and `tests/test_u2_typed_failure_context.py` (commits `bf330fba3897f0d00e52868b6de4b9acda5b9aee`, `43d3493835dbbc9ecfbf1b938061f12300c5a323`, `c2d8bf3bd588304af257a971418eb35087da4b3c`). These are an **opt-in, typed and identity-linked semantic reference**, not a canonical managed FailureContext or root map. Primary typed failure and ordered secondary failure records carry type ID, Text payload and source location. Existing token-based order ledger remains unchanged. This change has **not been compiled or tested** because the local environment cannot resolve github.com for repository checkout; hosted smoke has not yet been inspected. No passing result, ABI integration, native adapter, allocation-failure/GC evidence, merge or closure is claimed. The newly added test is awaiting execution. Do not promote this implementation until actual compilation and tests confirm it.



This replaces the accumulated development instructions in former §§88–92.
The implementation is in the U2 draft branch, not `main`.

| Implemented and tested foundation | Source / boundary |
| --- | --- |
| Bounded reverse cleanup planning | `src/compiler/u2_cleanup_plan.eri`; private planning data, not executable IR |
| Fresh all-row cleanup verification | `u2_cleanup_verify.eri`; includes dead rows, mutations and checked refusal cleanup |
| Typed destinations and cleanup links | `u2_continuation_bind.eri`, `u2_cleanup_link.eri`; exact owners, revisions, signatures and source origins |
| Canonical fallible calls | `u2_invoke_build.eri`, `u2_invoke_contract.eri`, `u1_verify.eri`, `u1_successors.eri`; real FunctionIds, private opcode 46 and the existing canonical pools |
| Multiple checked contracts | Version-one metadata-owned table; exact normal signature snapshots, one aggregate failure payload, fresh checks of every entry including unused contracts |
| Typed outcome transport | `u2_invoke_transfer.eri`; version-two private descriptors, up to 128 carried values, predecessor availability and exact destination types |
| Bounded reference execution | `u2_invoke_reference.eri`; exact closed structural test adapter, outcome-only results and simultaneous source capture before destination writes |
| Initial scoped-owner verification | `u2_scoped_owners.eri`; explicit lexical owner signatures, success-only acquisition, LIFO consumption before both close outcomes, exact surviving edge prefixes and source origins |

The scoped profile currently admits **one explicit resource contract** with an
opaque aggregate handle interpretation. It checks every block, including dead
blocks; rejects resource construction/copy/escape, return without cleanup,
non-LIFO or consumed-owner use, bad edges and stale/foreign profiles; permits a
nonterminating loop to retain owners when its backedge signature matches.
It uses O(N+V+T+S) local verification and reusable
`2(V+1)+(T+1)+256`-word scratch under existing quotas, not path enumeration,
per-block register masks or an ownership fixed point.

**Do not broaden this result:** the resource fixture is hand-built canonical
UIR, not output of completed Eristavi cleanup-plan lowering or a real file
runtime. A structural aggregate payload is not the complete managed
primary/secondary FailureContext. Owned execution of the verifier is not native
execution of resource adapters. Text/List/identity, managed-local promotion,
root maps and complete runtime/context integration remain unfinished.

### Exact revisions and validation

| Evidence | Verified result |
| --- | --- |
| Latest implementation/evidence commit | `3dbc6add049c70fe6adb34bd954270f08a5ba6e7` |
| Exact implementation/evidence tree | `268d79d646293fb3acded1473ad52bceeae31c63` |
| Hosted-smoke head / tree | `4fea1f66fb6ea63621be419c67b8993b6f6bce07` / `982b4c149fd60ac72738a9677d6defabe1d3fdc8`; changes from the implementation commit are handover-only |
| Hosted smoke | [41492512950](https://github.com/eristavi/eristavi-lang/actions/runs/41492512950) SUCCESS; 69 collected, 66 passed, 3 opt-in skips; 145.442 s; job `125438983489` |
| Opt-in owned execution | All three skipped probes passed locally: invoke outcomes, carried outcomes and execution of the scoped-owner verifier |
| Focused U2 / ownership checks | 13/13 in 80.777 s; strengthened bootstrap owner checks 5/5 in 24.998 s; owned owner-verifier probe 1/1 in 24.458 s |
| Broad local smoke | 68 collected, 66 passed, 2 opt-in skips; 273.396 s; the later added owner-native test was run separately and adds the third hosted skip |
| Prior stop checkpoint | `867252d494d9dee6a7b40284b8ed4dffee88db8f`; handover-only successor of the hosted-smoke head |
| Qualification / merge | No new full four-platform CI, completed-batch qualification, U2 closure or merge selected; PR remains DRAFT |

Supporting coverage includes 150 independent legacy resource baseline cases,
30 cleanup plans / 1,602 semantic paths, frozen/dead-row mutations, typed
same-revision pool mutations, multiple fallible targets, unused contract
corruption, duplicate/foreign/version rejection, exact fuel/LocIds, constructor
work/traffic refusal, cancellation and released backing. Earlier intermediate
fixture failures are historical, not current blockers.

Current-source U1 forced-collision regression: **7,830,976 B actual phase peak /
21,974,768 B actual allocator traffic**, within the unchanged **8,388,608 /
67,108,864 B** gates; all tagged backing reclaimed. This is existing U1 physical
scope, not U2 scratch attribution or process RSS. The independent U1b type/value
backing test also reclaimed all observed metadata and function objects.

Evidence: [summary](https://github.com/eristavi/eristavi-lang/blob/3dbc6add049c70fe6adb34bd954270f08a5ba6e7/docs/evidence/2026-11-02/u2-canonical-summary.json),
[local smoke](https://github.com/eristavi/eristavi-lang/blob/3dbc6add049c70fe6adb34bd954270f08a5ba6e7/docs/evidence/2026-11-02/u2-canonical-smoke.json), and
[lossless archive](https://github.com/eristavi/eristavi-lang/blob/3dbc6add049c70fe6adb34bd954270f08a5ba6e7/docs/evidence/2026-11-02/u2-canonical-evidence.zip).
The archive retains raw logs, three owned result/hash records and 18 input
snapshots. CRC and every input SHA-256 were verified; current inputs still match.
Archive SHA-256: `4bea42f5648c0b2c8a3c69627fd1f612beb440405190e009d15eb673b2c6cda6`.

### Remaining U2 gates — actively authorized to resume

1. Connect semantic cleanup plans to canonical resource operations and prove
   exit origins, pending returns and exact cleanup across the complete profile.
2. Implement complete managed Text/List/identity typing and value-copy/alias
   semantics, pinned Unicode17 and managed-local promotion.
3. Implement rooted primary/ordered-secondary FailureContext, root/safe-point
   contracts and real resource/runtime adapters under the existing ABI.
4. Complete independent depth/exit/loop/identity-cycle/malformed cases,
   sanitizer/allocation-failure/cancellation and actual U2 physical/latency
   evidence under preselected policies. Existing small probes do not close this.
5. Once the coherent implementation meets acceptance, run one final exact-head
   four-platform CI and required full qualification, compare tested/merged trees,
   and only then decide merge/closure. Keep #74 open until its gates pass.
