# Eristavi U1 → U3 execution and acceptance plan
Checkpoint: 2026-10-30. Status: engineering execution plan, not a revised language specification.

## Governing architecture and safety boundaries

- Freeze `DESIGN_PHILOSOPHY.md`, `LANGUAGE_SEMANTICS.md` and `PRE_0_1_FREEZE.md`.
- Source language, old compiler, Stage-0 Python reference, existing 32-byte ABI boundaries and current working module formats remain intact until independently proven compatible migrations.
- Approved design: AST and frozen semantic facts → **one** owned, language-neutral, typed Universal IR → independently verified SSA → canonical verified transformations → target legalization/machine code. Do **not** introduce a new mandatory executable source-close Typed IR.
- Internal UIR opcode numbers, profiles and cache encodings are **not** a public serialized ABI. Runtime memory/GC, generic templates, OS/ABI, RevaSM and artifact schema each need separate review.
- Reject unsupported operations/profiles; never invent semantics or silently fall back to legacy lowering on validation failure.
- No claim of completing U1a/U1b/U2/U3 merely because source code or small native probes compile.

## U1a: core scalar/control-flow slice (first)

### U1a-1: strict binary64

Complete typed `f.add/sub/mul/div/neg`, six IEEE comparison relations and exact 64-bit constants. Require nearest-even binary64 for each arithmetic operation, no excess precision/FMA/FTZ/DAZ or implicit Int conversion. Preserve signed zero, infinities, subnormals, NaN unordered comparisons and no integer-style Float divide-by-zero trap. Establish a controlled floating environment at native execution/foreign ABI boundaries. Tests compare independent IEEE class/bit observations (except permitted NaN payload canonicalization), including non-FMA, ties-to-even and subnormal vectors, before/after SSA promotion; reject invalid modes/operand types/locations and unreachable malformed IR.

### U1a-2: declarations/calls/imported effects

Owned function declaration/signature table; direct `FunctionId` reference with exact ordered parameters/results (including zero and multiple results), forward refs/recursion, and explicit pure/read/write/external/allocation/terminal-trap/divergence summaries. Derive body summaries conservatively across recursive SCCs, reject unsupported checked failures (U2), and validate trusted versioned import contracts. Verify unused effectful calls cannot disappear and first observable fault/side-effect order is unchanged. Differential oracle includes mutually recursive calls, non-returning functions and malformed imports.

### U1a-3: sparse switch + edge schema

Introduce an explicit edge/case table instead of numeric successor count or case-span allocation. Integer selector, unique equal-width case bits, unsigned canonical sort, exactly one default, no fallthrough. Extend *all* CFG walkers (builder, independent structural/SSA verifier, graph/dominance, promotion and reference execution), parallel block argument transfer, same-target-distinct-edge cases and unreachable case records together. Test empty, dense, sparse, max-bit, duplicate, bad default, wrong width, swapped edge arguments, loops and large sparse values. Require bounded memory proportional to case count.

### U1a-4: provenance, publication and versioning

Original `LocId` and source digest are mandatory for source effects/faults, with owned synthetic origin chains, end-to-end original fault anchoring, revision-aware verification, and no stale accepted record after mutation. Any publication/optimization must verify the new revision; verifier reports are observational and do not become bypass capabilities. Test stale digest, changed source, same textual name in different revisions, undo/retry/cancel, malformed dead code and transformations preserving fault origin.

### U1a exit

Complete independent reference evaluation, malformed-IR and generated tests for every admitted scalar/control op; cell-free transactional SSA after mandatory promotion; bounded work/traffic and measured physical allocation under specified budgets. Native U1a behavior is not considered implemented until a **separately checked target adapter** executes representative IR and reports strict Float/terminal traps correctly.

## U1b: extended core types

Add i8/i16/i32 (and any specifically approved remaining widths) as distinct same-width signed/unsigned bit-vector operations. Overflow, constant validation, division/remainder, signed/unsigned comparisons and mixed-width rejection need independent exact oracles. Introduce owned immutable aggregate type graph, make/get/set, structural field arity/type verification, nonrecursive/cyclic-by-value rejection, and proper value-copy semantics. No managed Text/List/identity, extra public Int types, implicit widening or broad address model. Require deep/large aggregate stress and self-contained hand-written UIR without Eristavi runtime assumptions.

## U2: managed values, checked failures and resources

Preserve existing Eristavi semantics while specifying and implementing:
- Typed managed Text/List/identity and existing value-copy vs identity semantics.
- Explicit checked-failure continuations, live result/failure availability and required no-value/typed return behavior. Never confuse terminal traps with recoverable checked errors.
- Scoped resource owners, exactly-once normal and checked-failure cleanup, reverse construction order, nested/multi-exit cleanup chains and primary/secondary-failure ordering; terminal runtime defects end without user cleanup.
- Root maps and native GC safe points, profile-tagged ABI/runtime adapters and allocation-failure behavior. Preserve pinned root stability, Unicode 17, existing runtime ownership and library contracts.
- Independent verifier rejection of use-after-consumption, dropped cleanup, stale roots, invalid failure edges, owner mismatch and invalid managed typing.
- Stress nested resources, deep cleanup, loops, common subpaths, failure during close, identity cycles, GC churn and allocator failure, with real physical memory and duration evidence.

Do not replace the working native compiler with a scalar-only U1/U2 subset. Deferred moving GC, new memory provenance and generic-template artifact redesign remain separately gated.

## U3: AST/semantic facts → UIR and one native target

Implement semantic-to-UIR construction directly using the frozen compiler frontend. No mandatory new source-close executable IR. Preserve modules/imports, generic relationships, diagnostics and source spans; compare Stage-0 and old native outputs for representative legal/illegal programs. Implement a reviewed native legalization/runtime path for one target first (suggest existing Linux x86-64) with exact i64, strict Float, control/calls/switch, managed/checked/resource semantics. Compare observable output, failure order, process behavior, file/resource cleanup, GC/root safety and original source locations, plus non-Eristavi hand-built UIR. Preserve old paths for A/B until gates pass. Do not claim independent native compiler self-hosting without repeated complete B→C/C→D qualification.

## Release and evidence protocol

- Small focused PR per coherent completed slice; CI on Linux x86-64 GCC/Clang, Linux ARM64 Clang and macOS Clang; compiler changes then completed-batch explicit `qualification` workflow on **exact** code revision.
- Keep the optional experimental owned self-build distinct; do not re-run the historical 900-second timeout without explicit scope.
- Record commit/tree equality at merges and current `HANDOVER.md` status, including failures and corrected head IDs.
- Compatibility gate: Stage-0 and old native compiler remain source/runtime references until the new path matches their specified output, diagnostics and edge cases.
- Performance gate: report separately construction, verification, promotion, optimization, native lowering, runtime throughput, GC allocation/pause/peak, and offline package integrity; no extrapolated claims from microprobes.
- U4 backend/legalization/ABI, public artifacts/cache invalidation and broader platform support are follow-on milestones; any 0.1 release plan must choose explicitly whether to ship the current bootstrap compiler or wait for integrated U3.

References: `HANDOVER.md`; `docs/architecture/Eristavi-UIR-U1-Contract-2026-10-29.md`; `docs/architecture/Eristavi-Typed-Universal-IR-Proposal-2026-10-29.md`; `CI_QUALIFICATION.md`; `OFFLINE_TOOLCHAIN.md`; `PRODUCTION_HARDENING.md`.
