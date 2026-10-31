# Eristavi Lang — Remaining UIR acceptance and optimization plan

**Date:** 31 October 2026. **Latest status:** PR #105 qualified/merged; scoped U1a physical acceptance complete, #77 closure follows. U1b aggregates/U2/U3/U4 remain open. Section A below records the original plan and is superseded by this disposition. **Scope:** verified `main` after the runtime optimization, controlled benchmark, narrow interpreter, C-heap measurement and U2/U3 parity baseline batches. This document is a dependency and verification plan, **not a claim that U1a/U1b/U2/U3/U4 are complete**. Read the newest [HANDOVER.md](../../HANDOVER.md) checkpoint first.

## Verified work already delivered

| Area | Exact accepted evidence | Interpretation |
| --- | --- | --- |
| Production runtime optimization | [PR #99](https://github.com/eristavi/eristavi-lang/pull/99), exact-head full CI and owned integration | GC scheduling, exact roots and bounded scratch merged; existing ABI/semantics unchanged |
| Same-host production runtime benchmarking | [PR #100](https://github.com/eristavi/eristavi-lang/pull/100), [five-pair AB/BA result](https://github.com/eristavi/eristavi-lang/actions/runs/41198570405) | worker0 median **21.869176 → 4.019040 s (5.4414×)**; not whole compiler |
| New UIR scalar U1a | [PR #98](https://github.com/eristavi/eristavi-lang/pull/98), qualified closed #71/#72/#76 | scalar/SSA/Float/calls/effects/switches, safe provenance and bounded simplifier; physical owner gate still open |
| U1b narrow reference execution | [PR #101](https://github.com/eristavi/eristavi-lang/pull/101), [full CI](https://github.com/eristavi/eristavi-lang/actions/runs/41199325649), [qualification](https://github.com/eristavi/eristavi-lang/actions/runs/41199325706) | 210 independent i8/i16/i32 oracle cases, isolated owner-scoped requests; immutable aggregates NOT implemented |
| Native C managed heap observations | [PR #103](https://github.com/eristavi/eristavi-lang/pull/103), [20 raw samples](../evidence/2026-10-31/u1a-c-physical-heap-samples.json), [explicit opt-in CI](https://github.com/eristavi/eristavi-lang/actions/runs/41200109602) | actual whole C collector heap/GC/RSS, but NOT per-UIR-owner backing |
| U2/U3 frozen behavior A/B baseline | [PR #104](https://github.com/eristavi/eristavi-lang/pull/104), [focused CI](https://github.com/eristavi/eristavi-lang/actions/runs/41199824619) | Stage-0 and **old** native parity over 15 successful corpus cases; NO new UIR managed semantics or source pipeline |

## A. U1a #77 — physical attribution ACCEPTED through qualified PR #105

Final full CI 41222506854 and qualification 41222506873 passed; tested/merged tree 0d8bf1f4a58f66a15bb9a89bd42f596091ed9c36. The adversarial 65,536-word case passed unchanged peak/traffic gates with actual semantic backing and complete reclamation. HANDOVER section 44 and the final investigation define scope and retained deferrals. Issue #77 is CLOSED/completed.

### Original acceptance plan (now evidenced)

- Add a **reviewed private instrumentation gate** linking allocation-site tags to the exact `budget.Owner` for UIR metadata, per-function body, construction/promoter/verifier scratch and retained publication. Track allocated backing capacity **and** collector block/header bytes, retained/live/peak bytes, reclamation and cumulative traffic, without altering the frozen 32-byte ABI.
- Verify actual native C and owned-runtime allocation/GC sources independently. Existing [C collector observations](../evidence/2026-10-31/u1a-c-physical-heap-samples.json) show C-managed peak 8,423,198 / 8,476,364 / 9,172,962 B at dense8/32/128 while modeled function peaks are 162,368 / 274,528 / 720,704 B; these measures cover different ownership scopes. **Do not divide them and call it a memory multiplier.** The empty control's zero C-managed allocation with nearly equal full-process RSS underscores the distinction.
- Extend 8/32/128 to larger, independent graph/local/nesting/IR-owner scaling and mixed producers; preserve malformed dead-code, cancellation, precise source/origin and transactional rollback. Attribute overhead on each release, no negative owners or stale verified revisions. Keep original 8MiB function qualification and 64MiB traffic policy without post-hoc weakening.
- Only close [#77](https://github.com/eristavi/eristavi-lang/issues/77) when actual per-owner physical backing, source fault consistency, resource scale, independent oracle and exact-head CI/qualification are demonstrated. **Actual durable serialized artifacts belong to U3**, and fully managed Text/List GC to U2.

## B. U1b #73 — immutable aggregate completion, still OPEN

**Already qualified:** i8/i16/i32 registry/build/verifier and U1b narrow independent reference execution. **Still implement:**

1. Choose module-metadata-owned immutable aggregate type identities independent of source AST/old `typed.Program`. Extend the present six primitive UIR TypeIds via a checked, owner-bound aggregate table; reject foreign-owner IDs, missing type entries, by-value cycles and out-of-budget nesting. Don't silently substitute List or identity for core aggregates.
2. Store compact, deterministic field-type/offset metadata in bounded shared UIR pools. Implement **`aggregate.make`**, **`aggregate.get`**, **`aggregate.set`** as typed pure SSA operations with immutable result-value copies: set returns a new aggregate; the old value remains unchanged. Static field ordinal/type/arity and nested structural ownership are mandatory.
3. Extend the authoritative registry, construction, independent dead-code/type verifier, promotion copying, reference execution and optimization invalidation together—never merely reserve opcode numbers or bypass a failing verifier. Treat aggregate values as private UIR data, not the existing public Eristavi boxed ABI.
4. Independent Python oracle and 3-size nested/projection/update corpus; negative foreign owner, wrong field, type mismatch, malformed unreachable aggregate, by-value cycle, overflow, cancellation/alloc-refusal and exact cleanup/traffic. Full four-platform CI and completed-batch qualification on the final exact head, original tests intact.
5. Close [#73](https://github.com/eristavi/eristavi-lang/issues/73) only after aggregate make/get/set and narrow all-width acceptance, not because the 210-case scalar interpreter alone passed.

## C. U2 #74 — managed values, checked continuations, deterministic resource ownership

**NOT IMPLEMENTED in redesigned UIR.** Implement a **versioned optional UIR semantic extension**, using current runtime/ABI adapters rather than replacing the collector:

- Typed Text/Text views (pinned Unicode17), List values with ordinary by-value copies, shared identity with pointer/reference distinction, checked value availability and a closed operation/effect registry.
- Explicit checked-failure success/error continuation edges and terminal trap distinction; deterministic exactly-once **reverse-order** resource cleanup on return or checked failure, preserving primary/secondary cleanup-failure order. Process-terminal defects promise no cleanup.
- Independent owner and root-safe-point maps on all paths (calls, block edges, unwinding/cleanup, promoted private temporaries). Reject missing roots, consumed values, malformed unreachable typed operations, invalid failure edges, double cleanup and illegal owner crossing.
- Deep nested loops/resources, identity cycles, Text/List alias/copy, negative OOM/refusal/GC stress and Stage-0 vs old-native vs isolated new-U2 reference output/trace parities, real memory and pause/throughput.
- Do not begin production frontend migration until [#74](https://github.com/eristavi/eristavi-lang/issues/74) passes its independent semantic/resource gates.

## D. U3 #75 — actual frozen frontend→new typed UIR and one native target

**NOT IMPLEMENTED end-to-end.** Build opt-in **shadow path** from frozen AST and analyzed semantic facts into owned typed UIR, without reintroducing the mandatory source-close executable Typed IR. Adapt scopes, modules, inferred generics, Unicode17 Text/views, checked failures/resources. Reverify after construction, promotion, transforms and artifact ingress. Use exact source digest/LocId with proper synthetic parent chains; version source/IR/runtime/ABI import identities and artifact/cache manifest; reject stale/forged "verified" stamps.

Lower one complete Linux x86-64 UIR profile to the actual native target, preserving calls, strict f64, sparse CFG, aggregates, managed roots, checked cleanup, source fault anchors and old public ABI through private adapters. Compare against frozen Stage-0 and existing compiler for the entire accepted corpus (the [PR #104 baseline](https://github.com/eristavi/eristavi-lang/pull/104) is only an initial 15-case sample). Record A/B output/fault/source and physical performance on identical complete compiler inputs. Retain a rollback and old production backend until independently qualified. Close [#75](https://github.com/eristavi/eristavi-lang/issues/75) only after that end-to-end integration and full qualification.

## E. U4 #102 — target legalization, machines and artifacts

**NOT IMPLEMENTED for redesigned UIR.** Complete checked semantic→legal→machine profiles, one authoritative op registry/legality checker and exact-revision verification after each transform. Implement x86-64 machine lowering with instruction selection, call ABI, root-aware liveness/register allocation, exact checked failures and LocId trap mapping, deterministic object/relocation/linking. Then prove ARM64 parity and explicitly document unsupported target gaps. RevaSM stays a *peer* machine, requiring measured live-in/block-parameter threading—not a mandatory pass-through. Artifact/caching/dependency/source digest, migration and repeatable packaging need separate verified release profiles. See [#102](https://github.com/eristavi/eristavi-lang/issues/102).

## Cross-cutting performance and CI rules

- **Optimization-first after correctness, safety and frozen semantics**: measured algorithmic work, memory/budget, construction/verifier/GC/compilation phase times and predictable tests are default design criteria. Refer to the controlled [5.4414× fixed worker result](../evidence/2026-10-31/owned-runtime-production-paired.md) but never extrapolate to all compilation.
- Current [#51](https://github.com/eristavi/eristavi-lang/issues/51) hash-table hypothesis must be recalibrated: the source already grows the 8,192-bucket table above **16,384 live graph objects**, not its old 65,536 threshold. Measure current registry depth, index rebuilds and compiler source phase outliers before new optimizations.
- Focused tests and change-specific independent oracle while developing. **One** final exact-head full matrix/qualification when compiler/IR/runtime code changes; docs-only changes need patch check. Do not automatically run experimental owned full compiler self-build.
- Keep HANDOVER.md recovery/table/latest sections consistent after every qualified implementation, issue state change or merge. Never report U2/U3/U4 completion from isolated reference tests or older Stage-0/Universal IR native routes.

**Dependency truth:** U1a physical acceptance is qualified and merged through #105, and #77 is CLOSED/completed. U1b #73 remains partially implemented; U2 #74, U3 #75 and U4 #102 remain open. No safe shortcut can substitute a functioning, verified implementation for a milestone checkbox.
