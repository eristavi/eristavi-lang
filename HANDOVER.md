# Eristavi compiler — current handover

Reviewed 5 November 2026 (Asia/Nicosia). This is the current recovery document.
Historical checkpoints are evidence, not instructions to restart old work.

## Resume here

### 5 November 2026 — bounded native managed identity checked-edge transfer VERIFIED (focused)

- **Exact code/test implementation revision:** [57391a4](https://github.com/eristavi/eristavi-lang/commit/57391a4ab7b72862975f38ef1238449521e0f9a2), draft PR #111. New `src/compiler/u2_checked_identity_edge_x86_64.eri` consumes `u2_checked_identity_ssa_bind.verifyManagedIdentity` as a pre-emission admission gate. The verifier independently checks the frozen managed identity descriptor, Function revision, exact canonical checked opcode-46 normal/failure continuation, source ValueId, both destination ValueIds, typed failure root metadata and deterministic owner plan.
- **Private x86-64 edge runtime fragment:** caller supplies canonical SSA ValueId-indexed frame, *already registered and published* class-1 identity root, existing bound class-5 failure root, and checked File.close status (0 or -1). It faults on missing/mismatched class-1 root, absent required class-5 failure root, invalid status, or nonempty failure root on normal return. It moves the exact identity SSA source to **only** the selected normal/failure destination, poisons the dead predecessor source, clears the inactive destination, and preserves class-1 root across the next GC safepoint. It does not allocate or call the GC inside the transfer. The caller remains responsible for selecting/invoking this fragment after actual File.close, binding/unbinding scopes and releasing roots when no longer live.
- **Dedicated focused Linux Clang [#42083946201](https://github.com/eristavi/eristavi-lang/actions/runs/42083946201): SUCCESS, 10/10 test methods / 0 failures** (82.209s). The two new tests compile actual Eristavi-native emitted assembly, execute normal and failure edges with an existing class-1 root, real three-node identity-cycle GC and reclamation, check source poison, inactive destination clearing, surviving branch ValueId and live root, and refuse a wrong managed descriptor before assembly. An initial draft failed due to reversing the Python test's normal/failure destination-offset order (emitter outputs failure first); precise exit-index instrumentation proved the harness mistake, fixed in 57391a4. Earlier binder/identity/cycle/checked File tests remain green.
- **Broader exact-code Linux Clang smoke [#42083946227](https://github.com/eristavi/eristavi-lang/actions/runs/42083946227): SUCCESS, 117 run / 114 passed / 0 failures / 3 intentional skips** (698.767s), including the new real native checked identity transfer. The ordinary patch/scope job passed; the full four-platform matrix was deliberately not selected because U2 acceptance is still incomplete.
- **Scope remains bounded:** no automatically generated whole-Function CFG or producer instructions, no automatic class-1 registration before a native File.close allocating call, no general combined File-close wrapper/typed Unicode failure propagation, no recursive checked handler exit lowering, no 32-slot scaling, no RSS/GC-pause/fault matrix, no final four-platform or completed-batch qualification. U2 #74 OPEN, PR #111 DRAFT/unmerged; the default compiler, frozen semantics and 32-byte Value ABI remain unchanged.

### 5 November 2026 — checked identity SSA carry and managed descriptor admission (bounded, Linux development)

- **Implementation:** new `src/compiler/u2_checked_identity_ssa_bind.eri` is a separate machine-neutral verifier for one canonical opcode-46 checked File.close edge. Its original `u2_checked_ssa_bind.eri` File-only counterpart was restored byte-for-byte after compiler specialization conflicts. The new verifier explicitly requires one structural managed-carrier ValueId between lexical File-owner block parameters and the pending i64. The same **exact source ValueId** must be transferred to both normal and typed failure successors, with canonical type/parameter/edge metadata and source origins independently checked. Incorrect same-type source substitutions, stale maps, wrong failed markers and unrelated i64 substitutions reject.
- **Independent identity gate:** `verifyManagedIdentity` requires an exact frozen managed identity descriptor (shared-handle policy) through `u2_identity_root_gate` and recomputes SSA liveness at the current revision, before returning the verified checked-edge report. The test fixture uses the U1b structural carrier as **metadata only**; it does NOT construct a real native managed identity from an ordinary U1b aggregate or invent an executable identity opcode.
- **Focused Linux Clang [#42078309510](https://github.com/eristavi/eristavi-lang/actions/runs/42078309510): SUCCESS, 7/7 test methods / no failures** at exact implementation revision [b7aaac4](https://github.com/eristavi/eristavi-lang/commit/b7aaac43bfb7538c22e84fd91d45934a43f3cfb6). The new 7th regression covers both canonical checked edge transports and adversarial wrong-source and stale-map cases. New negative frozen-descriptor test and inclusion in standard smoke were added at [a6fa74e](https://github.com/eristavi/eristavi-lang/commit/a6fa74ecfcec455c7d7edda3a367060b883d66e5). The exact-head [focused #42078580294](https://github.com/eristavi/eristavi-lang/actions/runs/42078580294) **SUCCESS: 8/8 methods, 0 failures**, including wrong managed identity descriptor refusal. [Linux smoke #42078580125](https://github.com/eristavi/eristavi-lang/actions/runs/42078580125) did **not** run due to patch-check rejection of a trailing blank test-file line; the line is fixed in this follow-up. New exact-code smoke remains unverified until the next workflow completes.
- **Still open:** actual x86-64 checked branch/value transfer and simultaneous live class-1/class-5 machine-root publication at this combined canonical invoke, real identity-producing instructions, full checked FailureContext propagation, arbitrary closure/recursion, >32 managed SSA values, physical budgets and final four-platform CI. PR #111 DRAFT, issue #74 OPEN, default compiler/ABI unchanged. No full owned self-build.

### 5 November 2026 — canonical identity SSA to native class-1 safepoint roots VERIFIED on Linux (bounded)

- **Exact implementation/test revision:** [c4b6b27](https://github.com/eristavi/eristavi-lang/commit/c4b6b27af41dd16d56cdee1f431c74fb32b90d8c) on draft [PR #111](https://github.com/eristavi/eristavi-lang/pull/111). New opt-in Eristavi-owned module src/compiler/u2_identity_root_x86_64.eri creates actual **class-1 native root bind, before, after and release helpers** for one independently verified canonical SSA instruction and immutable shared-handle identity descriptor. The caller still provides the separate real canonical SSA frame and registered root vector; this does not compile full canonical identity instructions or whole Function CFG/checked edges.
- **Trusted native publication:** reverify frozen managed identity descriptor, canonical UIR and exact SSA plan; require matching complete live before/after ValueId obligations. Emit 8-byte root-vector slots mapped to actual 8*(ValueId-1) canonical SSA-frame offsets; zero roots before binding, republish live slots, clear dead slots after last use, and release all selected slots. Required null handles fault through the existing runtime; unsupported symbol names, stale/foreign metadata and wrong descriptors refuse before assembly. Explicit limit: **at most 32 selected identity SSA values**, no silent truncation or public ABI change.
- **Dedicated exact-code Linux Clang [#42018250948](https://github.com/eristavi/eristavi-lang/actions/runs/42018250948): SUCCESS, 6/6 methods / zero failures** (48.885s). Two new tests run the generated machine helpers around real owned GC of a three-node identity cycle, independently parse canonical ValueIds and physical frame/root offsets, require one dead root be zero and live successor root nonzero, prove GC frees the cycle after root release despite stale pointers in the *unregistered* SSA frame, and require a malformed identity/Text descriptor to refuse before assembly. Existing identity admissions, alias/cycle GC, checked-error parity and real File/identity co-roots remain green.
- **Broader exact-implementation Linux Clang smoke [#42018250883](https://github.com/eristavi/eristavi-lang/actions/runs/42018250883): SUCCESS, 113 run / 110 passed / 0 failures / 3 intentional skips** (492.806s), patch/scope passed, full four-platform matrix intentionally skipped. Prior candidate [#42017937365](https://github.com/eristavi/eristavi-lang/actions/runs/42017937365) was red from a Python metadata unpacking/test dict NameError; these harness-only defects were corrected in c4b6b27, without changing frozen language semantics.
- **Still open:** the new source-neutral identity root helper requires explicit test-caller invocation and does **not** automatically populate roots, lower identity-producing instructions, perform native checked opcode-46 normal/failure/handler dispatch, or join all class-1 and class-5 roots over nested cleanup and recursion. General Text/List/identity value layouts, graph/foreign/corruption and allocator refusal, 32-value scaling, real owner traffic/RSS/GC pause and independent all-exit Stage-0 parity remain incomplete. U2 issue #74 OPEN; PR #111 DRAFT/unmerged. Production/default compiler, source semantics, public 32-byte ABI and pause on optimization #51 unchanged. No full owned-compiler self-build or four-platform final qualification.

### 5 November 2026 — identity SSA negative-publication hardening VERIFIED in focused CI

- **Test-only candidate revision:** [80f82d4](https://github.com/eristavi/eristavi-lang/commit/80f82d410d252ab27e67d509585690451175b2e7), based on the existing bounded identity admission gate and native cycle/checked-File probes (no production compiler or ABI changes). The updated canonical identity SSA test now independently rejects three additional invalid machine-root publication promises: a dead value retained after its last use, two repeated copies of the same ValueId, and a foreign metadata-owned ValueId. The exact set of still-live identity roots remains the accepted control.
- **New focused Linux Clang [#42016585421](https://github.com/eristavi/eristavi-lang/actions/runs/42016585421): SUCCESS: 4 test methods / 4 passed / 0 failed**, 22.159s, including identity descriptor/SSA gate and negative cases, physical identity-cycle collection, checked identity error retained through GC, and two alias class-1 roots coexisting with class-5 checked File failures/real reverse-close cleanup.
- **Previously pending Linux smoke [#41993953329](https://github.com/eristavi/eristavi-lang/actions/runs/41993953329): SUCCESS: 111 run / 108 passed / 0 failed / 3 intentional skips**, 412.130s at earlier code revision `a3d45ab`; this is **NOT** exact-head evidence for test-only commit `80f82d4`. The earlier [#42016585487](https://github.com/eristavi/eristavi-lang/actions/runs/42016585487) smoke was cancelled by a later documentation push; docs-only patch check [#42016754276](https://github.com/eristavi/eristavi-lang/actions/runs/42016754276) passed. The subsequent exact-code Linux smoke [#42018250883](https://github.com/eristavi/eristavi-lang/actions/runs/42018250883) passed with the identity admission and new native publication tests selected.
- **Still not implemented:** full native identity-producing UIR lowering, exact machine publication and cleanup across every canonical opcode-46 normal/failure/recursive exit, owner/GC/RSS/pause physical budgets and general root scaling. The metadata admission gate plus physical private test caller are not a whole-Function backend. Keep U2 issue #74 OPEN, PR #111 DRAFT/unmerged. No four-platform qualification, production promotion or owned compiler self-build.

### 5 November 2026 — identity SSA gate, physical cycle GC and checked File co-roots (focused VERIFIED)

- **Exact focused-test revision:** [1397628](https://github.com/eristavi/eristavi-lang/commit/139762896ff8f71c0d5ab1e019cf76ac737967da) on draft [PR #111](https://github.com/eristavi/eristavi-lang/pull/111). New `src/compiler/u2_identity_root_gate.eri` checks the frozen identity descriptor (kind 3, shared-handle policy 2, exact U1b carrier), graph ownership, and the independently verified canonical SSA plan. It refuses wrong/foreign descriptors and missing publication. This is an admission proof, **not native identity codegen**.
- **Focused Linux Clang [#41993529224](https://github.com/eristavi/eristavi-lang/actions/runs/41993529224): SUCCESS, four methods / four passed / zero failed.** The tests verify the SSA gate and wrong-root refusals; a native two-alias three-node identity cycle surviving GC until its final alias root dies; matching Stage-0/C/owned behavior for a typed checked error retaining an identity cycle across 200 transient cycles; and actual native identity class-1 roots overlapping a class-5 original checked File failure plus three real reverse-order failing File closes, explicit GC, one-by-one alias release and complete resource teardown.
- **Limitations:** the mixed File/identity test chooses an existing independently verified private native cleanup helper from its test caller. Neither it nor the metadata gate lowers the **whole original canonical Function opcode-46** into native identity operations, handlers and cleanup. No general recursive/nested-List identity root map, full failure/cleanup safe-point emission, allocator/RSS/pause evidence, U2 acceptance, full four-platform CI or production/ABI change.
- **Smoke qualification status:** prior Linux smoke [#41992444077](https://github.com/eristavi/eristavi-lang/actions/runs/41992444077) passed **107 run / 104 passed / 0 failures / 3 intentional skips** on preceding `552ef2e`, but its explicit smoke manifest omitted the new identity test classes. This checkpoint adds all four identity tests to `tools/run_ci_tests.py` SMOKE_TESTS for a new exact-revision Linux run. That broader test remains **PENDING** until actual CI result is inspected. Keep #74 OPEN and #111 DRAFT/unmerged.
- **Debugging:** earlier red exploratory runs exposed test-fixture local shadowing, an unbound owned compilation test helper, and a string anchor with incorrect indentation for a generated caller prologue; all fixed without relaxing frozen semantics. The general identity-producing backend, verified physical checked failures and root maps across *all* canonical exits, fault/cancellation/allocator proof and final four-platform acceptance remain next. Optimization #51 stays paused; excluded owned self-build not run.

### 5 November 2026 — bounded Text CFG per-instruction roots VERIFIED on Linux

- **Exact implementation revision:** [ca88c31](https://github.com/eristavi/eristavi-lang/commit/ca88c3120236cad790d3269efa0d308afebffde6), draft [PR #111](https://github.com/eristavi/eristavi-lang/pull/111), unchanged source/32-byte ABI/default compiler. The original candidate f3958d2 failed Python syntax from a malformed test insertion; commit fe60595 restored the original recursive test, and ca88c31 fixed Eristavi `try` propagation syntax in the new Text adapter. Failure evidence remains in Actions history, not a passing claim.
- **Focused Text Linux Clang:** [#41985303525](https://github.com/eristavi/eristavi-lang/actions/runs/41985303525) **SUCCESS: 8 / 8 test methods, 0 failures** (124.807s). Native Unicode 17, exact Text views/NFC/bounds, malformed descriptor/import, recursive parent/root frames and checked typed FailureContext reference retain existing behavior; new test directly reads emitted native frame slots before a real GC safepoint and checks a dead concat input is cleared while a loop-carried snapshot and cross-block accent remain rooted.
- **Broader exact-code Linux Clang smoke:** [#41985303605](https://github.com/eristavi/eristavi-lang/actions/runs/41985303605) **SUCCESS: 107 run / 104 passed / 0 failed / 3 intentional skips** (596.283s), including the new precise Text regression. These are incremental Linux gates, NOT four-platform completed-batch qualification.
- **Scope/algorithm:** the independently reverified canonical `ssa.Plan` for the frozen opaque Text carrier (<=32 tracked Text SSA values) controls after-instruction root-word retirement and successor-edge pruning *after* simultaneous phi copies; only bounded multi-block non-recursive Text uses the plan. Existing single-block cases, local 32-frame recursion and profiles with >32 tracked Text values keep conservative roots. Native temporary Unicode view roots remain separately registered. No general identity, aggregates containing Text, checked opcode-46 managed failure, cross-function recursion or root-map publication in this change. No RSS/GC pause or whole-compiler speedup claim.
- **Still OPEN:** full managed Text/List/identity and failure-context precision across all safe points and exits, native checked FailureContext/cleanup integration, >32-slot scaling, malformed/foreign/dead root and allocation-fault matrix, independent Stage-0/owned differential proof, physical resource data and final four-platform CI/qualification. Keep #74 OPEN, #111 DRAFT/unmerged; optimization #51 remains paused; excluded owned compiler self-build not run.

### 5 November 2026 — selected CFG List root retirement VERIFIED on Linux (bounded)

- **Exact implementation revision:** [78828f4](https://github.com/eristavi/eristavi-lang/commit/78828f4bac0da9675331b05cb3170d320aca8983) on `compiler/u2-cleanup-foundation-20261102`, draft [PR #111](https://github.com/eristavi/eristavi-lang/pull/111). A preceding candidate [6b85eef](https://github.com/eristavi/eristavi-lang/commit/6b85eef3392395b7f8c9eff87e9e4cfe8056a47f) initially failed Python syntax because its generated test insertion was malformed; [1ead8b8](https://github.com/eristavi/eristavi-lang/commit/1ead8b8ada98587e2ac3fdc3fa3307dda12d768b) restored the full original test file with one isolated native regression. Smoke [#41981392040](https://github.com/eristavi/eristavi-lang/actions/runs/41981392040) then found a single Eristavi compiler semantic cause behind 19 test failures: `plan.values` was read from an optional `maybe identity ssa.Plan` in a combined Boolean guard. Commit 78828f4 fixed this by nesting explicit `if plan != none` presence proof without weakening optional-value semantics.
- **Focused Linux Clang gate:** [#41983294418](https://github.com/eristavi/eristavi-lang/actions/runs/41983294418) **SUCCESS: 8 methods / 8 passed / 0 failed**, including U2 List-i64 native snapshot/GC, collector-time dead and live SSA root-word inspection, loop-carried snapshots, parallel edges, terminal faults, malformed refusal, and the after-invoke independently verified liveness adversarial matrix.
- **Broader exact-implementation Linux smoke:** [#41983294307](https://github.com/eristavi/eristavi-lang/actions/runs/41983294307) **SUCCESS: 106 run / 103 passed / 0 failed / 3 intentional skips**, 599.047 seconds, with syntax check and current U2 regression. The subsequent documentation-only commits do not alter that tested implementation.
- **What is verified:** for this closed bounded native List-i64 profile with <=32 selected List carrier values, per-instruction `ssa.liveAfter` clears dead managed List root words after their last nonterminal use, before later collections, while live loop-carried snapshots remain rooted. The same function's simultaneous SSA edge copies still occur before successor-specific cleanup, and the legacy single-block and >32-value conservative fallback remain unchanged. This is actual emitted machine-code behavior checked with collector-time root-word tests; **it is not universal managed-machine-root validation or measured RSS/collector-pause efficiency**.
- **Still OPEN:** general Text/List/identity per-instruction publication, checked-failure/cleanup managed safepoints, root corruption and allocation-pressure matrix, removal of conservative >32 limit, source/Stage-0 differential evidence, memory/performance evidence and exact final four-platform qualification. U2 issue #74 stays OPEN, PR #111 DRAFT/unmerged, production syntax/ABI/toolchain unchanged; owned self-build not run.

### 4 November 2026 — two-stage canonical checked File cleanup + recursive failure roots VERIFIED (bounded)

- **Latest implementation source revision**: `87c244abc912d13f54b2730a69991ded050c36d1` on `compiler/u2-cleanup-foundation-20261102`, draft/unmerged [PR #111](https://github.com/eristavi/eristavi-lang/pull/111), U2 [issue #74](https://github.com/eristavi/eristavi-lang/issues/74) OPEN. Subsequent docs-only commits do not qualify new compiler code or change the public ABI.
- **Focused Linux x86-64 native gate:** [Actions #41886929286](https://github.com/eristavi/eristavi-lang/actions/runs/41886929286) **SUCCESS: 7 test methods passed, 0 failed** on the exact implementation head; earlier [#41886639816](https://github.com/eristavi/eristavi-lang/actions/runs/41886639816) and [#41886845027](https://github.com/eristavi/eristavi-lang/actions/runs/41886845027) passed the same seven test methods on earlier progressively complete code versions. New dedicated regression `test_u2_recursive_native_cleanup.py` executes actual recursive native stack scopes (depths 2 and 5), real File close success/failures, class-5 saved original primary across child scopes, forced collector calls and actual linked ordered secondaries verified against an independent Python reverse-close oracle. This is tested recursive *runtime*, not compiler-generated recursive UIR checked machine frames.
- **Step A — verified two-stage canonical checked route:** new machine-neutral `src/compiler/u2_checked_chain_verify.eri` independently verifies the original frozen canonical opcode-46 Function, version-two normal/failed continuation SSA ValueIds, exact surviving lexical File owner, original pending i64, and two independent successor File closes: normal outer cleanup and already-failing outer cleanup. The latter must retain the first typed failure as its primary while an outer File close may add a new secondary. Exact typed root record, current revision, original resource obligations and `failed=true` verified cleanup plan are required; forged source-primary transfers refuse before promotion. No new executable IR/opcode.
- **Step B — physical second-stage native File close:** expanded `tests/fixtures/u2_checked_ssa_prefix.eri` emits `erist_u2_cleanup_73` (normal outer) and `erist_u2_cleanup_74` (already-failing outer) from the two original independently checked plans after successful path admission, alongside the existing inner checked SSA helper `erist_u2_ssa_71`. `tests/test_u2_checked_ssa_prefix.py` now physically calls both outer stages under success/failure File-close injection, forced GC, original primary record preserved, added secondary in failure mode, no false successful return, consumed SSA File words, and final exact-once close. The test caller still selects the path; general UIR Function instruction/producer/branch machine lowering is NOT established.
- **Step C — recursive original-primary and secondary context proof:** new bounded runtime test described above; original FileError remains primary over nested unwinding and all close failures append in inner-to-outer, reverse-lexical order; scopes' GC roots stay registered as needed.
- **Debugging disposition:** initial chained fixture returned `limit:invalid U1a accounting state` because the fixture invoked mutable builder-only `build.parameter` **after** canonical Function finalization; two parameters were captured correctly before completion, verified metadata/canonical ownership rules were not weakened, and temporary diagnostics were removed. Newer exact-source seven-test focused successes supersede those exploratory red checks.
- **Broader exact-source Linux smoke:** [#41886934726](https://github.com/eristavi/eristavi-lang/actions/runs/41886934726) **SUCCESS: 105 tests run / 102 passed / 0 failed / 3 intentional skips**, 579.788 seconds, on exact implementation `87c244abc912d13f54b2730a69991ded050c36d1`. It includes both canonical two-stage checked cleanup and native recursive failure/GC regression; the run preserved CI evidence and skipped the full four-platform matrix under incremental policy. The same-SHA sibling [#41886929188](https://github.com/eristavi/eristavi-lang/actions/runs/41886929188) subsequently also **SUCCESS: 105 run / 102 pass / 0 fail / 3 skips** in 600.284 seconds. These are **NOT** completed-batch merge qualification or full U2 acceptance; the previous [#41881370999](https://github.com/eristavi/eristavi-lang/actions/runs/41881370999) at 104/101/0/3 is now historical evidence.
- **Still OPEN / NOT U2 accepted:** general canonical Function checked CFG and all SSA producers/interprocedural checked lowering, automatically lowered recursive checked call frames and managed full Unicode17 `FailureContext`, precise Text/List/identity safe-point roots across instructions, loops, recursion and all cleanup exits, stale/foreign/dead roots and deterministic allocator faults in combined paths, physical retained-memory/RSS/GC-pause/resource scale, independent Stage-0 vs new canonical/native differential outcomes, and final exact-revision four-platform plus completed-batch qualification. **Do not merge PR #111 or close #74**. Source syntax, production compiler/runtime, 32-byte ABI, U3/U4 migration and paused #51 optimization remain untouched; excluded owned self-build NOT run. See `docs/architecture/UIR_U2_CHECKED_CHAIN_AND_RECURSIVE_FAILURE.md`.

### 4 November 2026 — nested checked SSA owner-prefix and consumed-slot poisoning VERIFIED (bounded)

- **Latest implementation candidate on draft PR #111:** native source `a1d3cb8f24c6b4432733e703e05c0948e10be97a` adds exact clearing of the *consumed canonical source SSA File word* on BOTH checked outcomes. `8e9cadc0891a93e47abfc32bba46c2b84454e1da` adds direct one-owner regression; `200c7037d8db56e05fecadb4251e4d4a12dcff86` adds the nested two-owner consumed-slot assertion. **Exact-code focused CI is green for this newest two-owner assertion**, [#41883433364](https://github.com/eristavi/eristavi-lang/actions/runs/41883433364): 6/6 native methods, zero failures. Full four-platform/owned qualification remains OPEN. Production compiler and public ABI untouched; issue #74 OPEN, PR #111 draft/unmerged.
- **Nested-prefix implementation and positive execution verified:** `u2_checked_ssa_bind.eri` independently verifies canonical opcode-46 checked File.close (version-two) with 1–8 live lexical File owners, exactly one exiting inner owner and 0–7 surviving prefix owners, exact predecessor `i64` source and normal/failure successor SSA ValueIds, typed failure marker, scoped owner-stack signatures, full Function/dominance, original cleanup obligations and complete class-5 root map. `u2_checked_ssa_x86_64.eri` performs an actual checked File close through the independent original plan, moves surviving owners (does not copy them) into the chosen successor SSA parameter slots and clears their old slots; the checked failure primary remains pinned through collection. No new executable IR/opcode/collector/ABI.
- **Focused exact native two-owner proof:** [#41881371026](https://github.com/eristavi/eristavi-lang/actions/runs/41881371026) **SUCCESS, 6 of 6 test methods / 0 failures** on `2099c6243b95679d8683207163f50023136f37b0`. The two-File canonical fixture checks both normal and checked-failing inner close for three predecessor values, one surviving outer owner, actual native File runtime, explicit forced GC, final outer File close, zero leak, forged consumed-owner edge rejection before assembler emission. Both success and failure cases run physically.
- **Broader code smoke (before consumed SSA slot hardening):** [#41881370999](https://github.com/eristavi/eristavi-lang/actions/runs/41881370999) **SUCCESS: 104 tests executed / 101 passed / 0 failed / 3 opt-in skips** in 417.632 seconds at the same `2099c624` implementation head. Full four-platform matrix **SKIPPED** by incremental policy. Exact native source change `a1d3cb8f` subsequently requires new qualification.
- **Consumed source SSA handle regression:** [#41882834794](https://github.com/eristavi/eristavi-lang/actions/runs/41882834794) **SUCCESS, 6 native test methods / zero failures** on `8e9cadc0891a93e47abfc32bba46c2b84454e1da` (native source already hardened). The source File root word is consumed and its stale canonical SSA handle slot is zeroed; live outer owner moves to the proper edge parameter. The latest test-only extension `200c7037` additionally asserts that the nested consumed inner SSA source slot clears; it has now passed [focused #41883433364](https://github.com/eristavi/eristavi-lang/actions/runs/41883433364), 6/6 methods, zero failures. This is NOT an exact-head broad Linux smoke or four-platform qualification: broad #41881370999 predates native-source hardening.
- **Earlier exploratory failures resolved:** [#41879954423](https://github.com/eristavi/eristavi-lang/actions/runs/41879954423) failed only because the test expected zero live FailureContexts while holding the empty saved context under a caller-owned class-5 root; the correct number is one. [#41880916713](https://github.com/eristavi/eristavi-lang/actions/runs/41880916713) then surfaced a `//` Python comment typo corrected to `#`. Later focused and broad green runs cover the corrected prior fixture.
- **Mandatory next engineering work:** fully lower the *whole* canonical checked Function/SSA producers/handler targets for all typed values and multiple cleanup stages, not only one private checked-close entry; complete primary/ordered-secondary managed `FailureContext` across recursive frames; implement precise checked Text/List/identity safe-point roots across loops, recursion and cleanup; run independent malformed owner/foreign root and deep allocation-refusal/GC/RSS/sanitizer tests, independent Stage-0/native A/B with stable source origins, final exact-revision four-platform CI plus required completed-batch qualification. These issue #74 acceptance requirements are still OPEN and make U2 **NOT complete**.
- **Do NOT merge PR #111, close #74, change default production compiler or its 32-byte ABI, resume paused optimization #51, start unrelated U3/U4 migration or run experimental owned compiler self-build**. Architecture details: `docs/architecture/UIR_U2_CHECKED_SSA_NATIVE.md`.

### 4 November 2026 — canonical carried SSA -> native checked File-close VERIFIED (bounded)

- **Latest exact-tested implementation revision:** `1b99e065122b903aaa1537a7fc8cd563252f56d5` on `compiler/u2-cleanup-foundation-20261102`; **draft/unmerged PR #111**, **U2 issue #74 OPEN**. Subsequent documentation commits do not modify implementation sources or invalidate that code-input evidence. Production/default compiler and public 32-byte value ABI unchanged.
- **Targeted native exact-head CI:** [#41876779592](https://github.com/eristavi/eristavi-lang/actions/runs/41876779592) **SUCCESS: five focused test methods, zero failures**. Tests include earlier real File cleanup and canonical rooted close, plus new canonical SSA pending-i64 success/failure execution, forced GC, root release and invalid SSA rejection-before-emit.
- **Broader exact-head Linux Clang smoke:** [#41876779269](https://github.com/eristavi/eristavi-lang/actions/runs/41876779269) **SUCCESS: 103 run, 100 passed, 0 failed, 3 intentional skips**, 349.924 seconds; focused smoke now includes both previously omitted rooted-cleanup test and new SSA test. Artifact preserved; four-platform CI matrix intentionally SKIPPED by incremental test policy. This is **not U2 merge qualification**.
- **Step 1 — independent portable SSA proof:** new `src/compiler/u2_checked_ssa_bind.eri` re-verifies full canonical opcode-46 Function and scoped owners, version-two carried successor edges and typed destinations, class-5 root-map record, original verified cleanup plan, exact source LocId and Function revision. Admitted profile: ONE File owner, zero surviving owners, one predecessor source `i64` SSA block parameter, normal `i64` destination, failure structural typed context plus carried `i64` for handler context only. Source ValueId and both successor ValueIds must match **exactly**, not merely by type.
- **Step 2 — native checked dispatch:** new `src/compiler/u2_checked_ssa_x86_64.eri` reads the predecessor `i64` from the freshly verified SSA frame slot rather than a free caller-provided return register. A private x86-64 helper publishes canonical class-5 GC root before real File close; successful close writes only the normal SSA block parameter and releases the root. Failed close leaves the normal destination zero, writes typed failure record and carried handler data into the verified failure parameters and retains the root through checked handling. Independent machine-slot metadata is verified. The caller still provides the actual predecessor SSA frame; this is not complete machine lowering of the entire Function/entry.
- **Step 3 — independent execution + refusals:** `tests/test_u2_checked_ssa.py` executes 3 pending `i64` cases × 2 native File-close outcomes, with explicit forced collection, preserved scoped resources and final no-leak checks. The canonical fixture rejects same-type but wrong-source normal/failure transfers, removed typed failure marker and stale Pair/root-map revisions. The full native entry refuses wrong-source SSA **before emitting any attempted `LABEL=62` assembler symbol**. An early red check from generic edge-specialization and a stale construction-time `Pair` were fixed through a valid dead CFG edge and binding to the final Function revision; correctness gates were not weakened.
- **Limitations:** selected single-owner version-two source pattern only. This is NOT general canonical opcode-46 native CFG, compiler-lowered entry/producers, all SSA result types, arbitrary handler continuation execution or recursion. Failure payload metadata is structural, not full managed Unicode17 `FailureContext`; complete live Text/List/identity roots, surviving owner prefixes along canonical SSA edges, recursive checked unwinding, physical retained memory/RSS/allocator-refusal and independent multi-target parity remain to be implemented.
- **Next engineering gate:** expand exact canonical SSA transfers to verified surviving File owner prefixes and multi-exit checked cleanup while the GC-root map remains live, then recursive checked primary/ordered secondary propagation and all-managed-value precise roots; add physical and deterministic-fault evidence. When completed, run exact-head four-platform CI plus appropriate completed-batch qualification. **Do not merge PR #111 or close #74** before all acceptance gates. Do not resume paused #51, unrelated U3/U4 migration, or experimental owned self-build.
- **Architecture decision and evidence:** `docs/architecture/UIR_U2_CHECKED_SSA_NATIVE.md` (new); prior `docs/architecture/UIR_U2_NATIVE_CHECKED_CLEANUP.md` remains predecessor evidence.

### Earlier 4 November 2026 — three-step native checked-root and surviving-prefix batch VERIFIED (bounded)

- **Latest tested implementation/test revision:** `6b803e669531abb72966ca6da8f6d1dbb4c24688` on `compiler/u2-cleanup-foundation-20261102`, [draft PR #111](https://github.com/eristavi/eristavi-lang/pull/111). Three-step implementation source through `275b31ce1cb5020dd6de065f04716de98960be2c`; exact-green source includes a repeated-test fixture fix and additional root-corruption negatives. Subsequent documentation-only commits do not alter tested implementation inputs. #74 remains OPEN; production/default compiler and 32-byte public ABI untouched.
- **Dedicated Linux x86-64 checked cleanup CI:** [run #41870175450](https://github.com/eristavi/eristavi-lang/actions/runs/41870175450) **SUCCESS — 4 methods passed, zero failures**. Validated real native File cleanup with 1–8 bounded owners, verified canonical single-owner opcode-46 ingress, actual class-5 machine-root publication/release under real forced GC, checked File-close failures, a live surviving outer-owner prefix, and a cancelled pending `i64` return on checked cleanup failure. The combined native ingress also rejects wrong-class root slots and stale canonical root-map revisions before emitting an inadmissible assembler symbol.
- **Exact-head broader Linux Clang smoke:** [run #41870175496](https://github.com/eristavi/eristavi-lang/actions/runs/41870175496) **SUCCESS — 101 tests executed / 98 passed / 0 failed / 3 intentional skips**, 397.191 seconds. Scope check passed. Four-platform CI matrix deliberately SKIPPED (this is incremental development, not merge qualification). Smoke artifacts preserved by workflow.
- **Resolved red checks:** earlier [#41865432112](https://github.com/eristavi/eristavi-lang/actions/runs/41865432112) and [#41866025365](https://github.com/eristavi/eristavi-lang/actions/runs/41866025365) failed solely because the test generator called `symlink_to` twice inside the same temporary folder. Reusing and validating the stable compiler-import symlink fixed the fixture at `c81ad04c107df0ed811dfb52b9a2bbdc71ddfe66`. No verified runtime semantic regression resulted; newer exact-source green runs supersede the earlier failures.
- **Bounded behavior now proven:** canonical failure-root metadata and independently verified native slot placement feed an opt-in x86-64 checked File close wrapper that publishes the saved failure record **before potentially collecting cleanup**, retains it through the failure edge and releases on success. The private native File adapter consumes only the verified exiting owner suffix, leaving any declared surviving prefix live. A private pending-scalar helper transports the caller-owned i64 only on normal exit and invalidates it on checked failure.
- **Still NOT accepted:** this adapter is **not whole canonical opcode-46 CFG machine lowering**. It does not extract pending success payloads from actual canonical SSA successor parameters, implement arbitrary checked/handler dispatch or recursively propagate checked failures, provide precise per-instruction liveness for managed Text/List/identity, prove combined foreign/deleted-root or deterministic allocator-refusal paths, or establish physical retained-capacity/RSS/differential oracles. Full four-platform CI and completed-batch qualification remain to be done.
- **Next gate:** bind normal/failed canonical edge SSA payloads (including pending return) directly to emitted native checked outcome dispatch, retaining actual live class-5 roots on failure. Independently test malformed/foreign/dead roots, recursive checked cleanup and all surviving owner prefixes, with forced GC and physical memory/work budgeting. Avoid a second executable IR or new public ABI. Then proceed to one final qualified four-platform gate when the coherent U2 batch is complete.
- **Do not merge** PR #111 or close #74; do not start excluded owned compiler self-build, paused #51 optimization, or unrelated U3/U4 migration. Update `HANDOVER.md` automatically after every material gate. Architecture detail: `docs/architecture/UIR_U2_NATIVE_CHECKED_CLEANUP.md`.

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
| U2 | Bounded native CFG List-i64, Unicode17 Text/indexing/NFC, conservative roots and 32-frame local self-recursion. Native verified-plan File cleanup executes reverse close and ordered saved-failure composition. The canonical checked-close bridge now publishes a bounded live class-5 failure-root word and supports tested File-prefix survival/pending-i64 cancellation. An independently verified version-two canonical SSA File.close path now moves up to seven surviving File owners into exact normal/failure successor block parameters and kills the old owner SSA locations; the native nested-owner tests and earlier Linux smoke are green. Bounded native class-1 identity safepoint helpers now emit from verified canonical SSA plans (caller-driven); still OPEN: whole canonical opcode-46 CFG/producer lowering, automatic complete managed Text/List/identity exact roots, recursive checked failure-context propagation, deep fault/physical tests and full completed-batch acceptance. #74 OPEN, #111 DRAFT/unmerged. |
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
| Checked continuations | Canonical opcode-46 invokes and version-two predecessor SSA carries; bounded native checked File.close now admits 1–8 lexical File owners with verified surviving prefix, exact i64 and typed failure successor ValueIds, pinned GC-root, consumed SSA slot poison; general whole-Function checked CFG and all managed failures remain OPEN. |
| Cleanup and owners | Independently verified reverse-cleanup plans, bounded canonical close construction, lexical owner signatures, success-only acquisition and consumption on both close outcomes. Complete resource adapters remain open. |
| Failure contexts | Typed Unicode17 primary/ordered-secondary reference models, class-5 saved-failure publisher probes, and **real native File close failure composition** from verified private cleanup plans. A bounded one-owner checked-edge admission now verifies canonical metadata before emitting the existing native adapter. Whole canonical opcode-46 native failure dispatch, all SSA/handler exits and complete cleanup integration remain open. |
| Liveness | Independently recomputed CFG/SSA plan and publication obligations; bounded native List-i64 and Text CFG profiles retire selected roots after individual instructions and successor edges for <=32 tracked carrier values. A new x86-64 class-1 identity helper publishes/retire exact SSA before/after safepoint sets with physical native GC proof, but the caller still selects/executes it. Automatic all-Function identity/failure/cleanup roots, >32-slot scaling and all-managed-type verification remain OPEN. |
| Managed types | Owner-scoped Text/List/identity descriptors, independent corruption rejection and Unicode17 copy/view contracts; expanded Stage-0/C/owned parity oracle with predeclared accent/flag/ZWJ/empty/ASCII/copy values. This is not general canonical managed execution. |
| Native Text/Unicode17 | Twelve exact runtime imports support scalar creation, immutable concat/copy/equality, byte/scalar/grapheme counts/indexing, explicit NFC and collection. Bounded non-recursive multi-block CFG now retires selected Text roots per instruction/edge, with focused native GC evidence; 32-frame local self-recursion retains conservative managed roots. No arbitrary opcode-46 Text checked failure, general recursion or full Text integration. |
| Native List-i64 | Eristavi-written optional x86-64 adapter for empty/copy/append/replace/count/get/collection, branches/joins/backedges/cyclic transfers; verified successor-edge root retirement now focused-tested for <=32 selected List values. |
| Native boundaries | Managed-registry entry validation, Int/Bool/List runtime descriptor checks, List bounds source name/line/column, independent fixture frame-layout checks, GC/snapshot/reclamation and fault probes. Selected canonical identity SSA safe-point helpers now emit class-1 physical roots with actual cycle GC/release checks, not an automatically lowered whole-Function root map. |

The native List profile is capped at **64 blocks, 512 edges, 128 SSA values and
256 instructions**, with seven exact version-one runtime imports and an opaque
structural carrier interpreted only by that legal profile. It is not a general
managed-type encoding or frontend integration.

The closed bounded native List-i64 and Text multi-block CFG adapters use
independently reverified canonical SSA liveness to clear selected carrier
root words after their last nonterminal instruction use and on the
appropriate successor after simultaneous edge copies. Both profiles
conservatively retain all selected values when more than 32 are tracked.
The Text profile also keeps the established single-block and local
self-recursion cases conservative; the List single-block path retains its
original last-use logic. Unselected boxed values remain conservatively
rooted. The bounded identity emitter now adds actual machine class-1 publication,
retirement and release for one independently verified SSA safepoint with a
caller-populated canonical frame. This remains NOT a complete automatic
identity/checked-failure machine-root publication system for whole Functions.
Managed-local promotion, arbitrary runtime/descriptor compatibility,
physical RSS/GC pause limits and checked exits are still outstanding.

## Validation and evidence

| Revision / run | Verified result |
| --- | --- |
| `c4b6b27af41dd16d56cdee1f431c74fb32b90d8c` — [identity native focus #42018250948](https://github.com/eristavi/eristavi-lang/actions/runs/42018250948) | **SUCCESS:** 6 methods / 6 passed / 0 failed (48.885s); verified canonical SSA-derived class-1 before/after native root bindings, cycle GC and release, and wrong descriptor refusal before emission. |
| Same implementation — [Linux smoke #42018250883](https://github.com/eristavi/eristavi-lang/actions/runs/42018250883) | **SUCCESS:** 113 run / **110 passed / 0 failed / 3 intentional skips** (492.806s), exact-head smoke; full four-platform CI matrix intentionally skipped. |
| `a3d45abdbfc5e18d862a5cdb0be664ccb70e4004` — [prior identity smoke #41993953329](https://github.com/eristavi/eristavi-lang/actions/runs/41993953329) | **SUCCESS:** 111 run / 108 passed / 0 failed / 3 skips (412.130s); preceding identity admission/cycle/checked File co-root work, before native publication helper. |
| `139762896ff8f71c0d5ab1e019cf76ac737967da` — [identity focus #41993529224](https://github.com/eristavi/eristavi-lang/actions/runs/41993529224) | **SUCCESS:** four methods, four passed, zero failed: identity SSA admission, native cycle alias GC, checked error retention parity and live identity/File cleanup co-roots. Exact-code broader smoke pending after manifest inclusion. |
| `552ef2e041c18788f5a5f7f2502d10dd09527343` — [older smoke #41992444077](https://github.com/eristavi/eristavi-lang/actions/runs/41992444077) | **SUCCESS:** 107 tests, 104 passed, 3 skips; did **not** select the new identity test files. Historical evidence. |
| `ca88c3120236cad790d3269efa0d308afebffde6` — [Text focus #41985303525](https://github.com/eristavi/eristavi-lang/actions/runs/41985303525) | **SUCCESS:** 8/8 focused methods (124.807s), including native collector-time precise Text CFG root probe, recursion and Unicode17 faults. |
| Same implementation — [Linux smoke #41985303605](https://github.com/eristavi/eristavi-lang/actions/runs/41985303605) | **SUCCESS:** 107 run / **104 passed / 0 failed / 3 intentional skips** (596.283s); exact current Text root code, no four-platform matrix. |
| `78828f4bac0da9675331b05cb3170d320aca8983` — [List focus #41983294418](https://github.com/eristavi/eristavi-lang/actions/runs/41983294418) / [smoke #41983294307](https://github.com/eristavi/eristavi-lang/actions/runs/41983294307) | **SUCCESS:** 8/8 focused and 106 run / 103 passed / 0 failed / 3 skips. Earlier bounded List roots. |
| `87c244abc912d13f54b2730a69991ded050c36d1` — [Linux smoke #41886934726](https://github.com/eristavi/eristavi-lang/actions/runs/41886934726) | **SUCCESS:** 105 run / 102 passed / 0 failed / 3 intentional skips, 579.788s, checked two-stage native cleanup and recursive primary/secondary failure+GC; full four-platform matrix skipped. |
| `87c244abc912d13f54b2730a69991ded050c36d1` — [focused native #41886929286](https://github.com/eristavi/eristavi-lang/actions/runs/41886929286) | **SUCCESS:** 7/7 focused tests, 0 failures; verified two-stage checked File cleanup, native second-stage normal/failed entries and original-primary recursive failure ordering; broad smoke pending. |
| `200c7037d8db56e05fecadb4251e4d4a12dcff86` — [native focus #41883433364](https://github.com/eristavi/eristavi-lang/actions/runs/41883433364) | **SUCCESS:** 6/6 focused native methods, 0 failures; explicitly zeroes consumed inner File SSA slot and preserves lexical outer owner on both checked outcomes; general U2 still OPEN. |
| `8e9cadc0891a93e47abfc32bba46c2b84454e1da` — [native focus #41882834794](https://github.com/eristavi/eristavi-lang/actions/runs/41882834794) | **SUCCESS:** 6/6 focused methods, 0 failures; native source clears consumed SSA File word; latest two-owner assertion revision 200c pending separate CI. |
| `2099c6243b95679d8683207163f50023136f37b0` — [Linux smoke #41881370999](https://github.com/eristavi/eristavi-lang/actions/runs/41881370999) | **SUCCESS:** 104 run / **101 passed / 0 failed / 3 intentional skips**, 417.632 s; bounded nested File checked-prefix SSA; predates later consumed-slot hardening. |
| `2099c6243b95679d8683207163f50023136f37b0` — [native focus #41881371026](https://github.com/eristavi/eristavi-lang/actions/runs/41881371026) | **SUCCESS:** 6 methods, tested nested File owner surviving both checked edge outcomes and forced GC. |
| `1b99e065122b903aaa1537a7fc8cd563252f56d5` — [Linux smoke #41876779269](https://github.com/eristavi/eristavi-lang/actions/runs/41876779269) | **SUCCESS:** 103 run / **100 passed / 0 failed / 3 intentional skips**, 349.924 s; carried-SSA native checked outcome and rooted cleanup included, full matrix skipped. |
| `1b99e065122b903aaa1537a7fc8cd563252f56d5` — [native focus #41876779592](https://github.com/eristavi/eristavi-lang/actions/runs/41876779592) | **SUCCESS:** 5 focused native methods; SSA wrong-source refusal before assembly emission and positive normal/failure execution; no merge qualification. |
| `6b803e669531abb72966ca6da8f6d1dbb4c24688` — [Linux smoke #41870175496](https://github.com/eristavi/eristavi-lang/actions/runs/41870175496) | **SUCCESS:** 101 run / **98 passed / 0 failed / 3 intentional skips** in 397.191 s; matrix skipped. |
| `6b803e669531abb72966ca6da8f6d1dbb4c24688` — [native focus #41870175450](https://github.com/eristavi/eristavi-lang/actions/runs/41870175450) | **SUCCESS:** 4 focused native cleanup/root methods; wrong-class and stale canonical-root map refusal; no merge qualification. |
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
2. Expand the now **verified bounded per-instruction List-i64/Text CFG**
   retirement and selected **native class-1 identity before/after safepoint**
   helper to automatic full canonical managed Text/List/identity publication
   across whole-Function CFG and all instruction results, checked failures,
   recursion, terminal faults and cleanup boundaries. Resolve the selected
   32-tracked-carrier-value limit deliberately; retain conservative
   fallback until the scalable proof is independently qualified.
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
