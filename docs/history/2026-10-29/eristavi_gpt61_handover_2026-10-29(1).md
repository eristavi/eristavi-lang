# Eristavi Compiler Project — Engineering Handover

**Handover date:** 29 October 2026  
**Repository:** `eristavi/eristavi-lang`  
**Language:** Eristavi  
**Primary source extension:** `.eri`  
**CLI/compiler command:** `erist`  
**Official domain:** `eristavi.org`

This handover concerns the **Eristavi programming language/compiler project only**. Do not mix it with RevaOS or RevaSM / the Universal Semantic Machine project.

---

## 1. Core project goal

Eristavi is a new general-purpose programming language and compiler built around one central principle:

> Complexity belongs in the compiler and runtime, not in the programmer's code.

The source language should remain readable, strongly typed, predictable and relatively small while the implementation is allowed to become sophisticated underneath.

The long-term intention is **not** to remain a transpiler permanently dependent on C, C++, LLVM, Python or another high-level compiler stack.

The intended architecture is:

```text
Eristavi source (.eri)
        ↓
Lexer / Parser
        ↓
Semantic analysis
        ↓
Type and effect inference
        ↓
Typed Eristavi IR
        ↓
Eristavi Universal IR
        ↓
Verification / optimization
        ↓
Target-specific backend
        ↓
x86-64 / ARM64 / WebAssembly / future targets
        ↓
Machine execution
```

Long term, Eristavi should own its compiler frontend, semantic model, intermediate representations, verifier, optimizer, runtime, target backends, machine-code encoders, object generation and eventually its linker/toolchain.

Do **not** redesign the language philosophy or architecture from first principles. Continue from the implementation that exists.

---

## 2. Architectural rules that must remain preserved

Source semantics are not to be weakened for performance.

Important preserved contracts include strong static typing, automatic memory safety, deterministic resource handling, mandatory verification, explicit failure semantics, predictable source behavior and the existing public **32-byte value ABI**.

Private compiler indexes, caches and accelerators are acceptable when they preserve the canonical public representation and observable behavior.

A hash table must never make hash equality authoritative. Hashes may select buckets, but exact semantic/identity comparison remains authoritative.

Optimization must never silently change diagnostics, source semantics, verification behavior, IR ordering or public ABI.

Whenever possible, require byte-identical generated IR/assembly when optimizing an internal lookup or algorithm that should not change output.

---

## 3. Engineering preferences

Use evidence-driven engineering and realistic claims.

Do not inflate microbenchmark improvements into whole-compiler claims.

Do not run expensive tests after every change.

Preferred pattern:

```text
cheap static inspection
→ bounded counter/profile
→ focused benchmark
→ exact-output correctness gate
→ normal CI
→ qualification
→ expensive owned self-build only when justified
```

Expensive tests should be performed at meaningful milestones rather than continuously.

When a performance candidate does not improve the measured target, discard it rather than carrying unnecessary complexity.

Temporary diagnostic GitHub workflows and helper scripts must not remain in the final production PR.

Squash merges are preferred to keep `main` clean.

When the user says **"continue", "proceed", "go ahead", or similar**, actually continue repository work rather than merely describing what should be done.

Use the GitHub connector for repository work.

Keep the user updated during long tool sequences.

---

## 4. Current compiler/runtime status

The compiler is already substantially beyond a toy implementation.

It has an Eristavi-written compiler frontend, Typed IR, Universal IR, verification, optimization and native assembly generation.

Linux x86-64 and ARM64 compilation paths exist.

There is an independent owned Linux x86-64 runtime path intended to eliminate libc/CRT/runtime dependency from generated targets.

The owned runtime is capable of building static compiler/application executables without libc, CRT objects or a dynamic loader.

However, **repeated owned compiler self-build is not yet qualified** because the B→C compiler rebuild still exceeds the existing 900-second limit.

The default/runtime promotion should not occur until repeatable owned self-build succeeds.

The broader long-term roadmap still includes removing required Python bootstrap tooling, removing C runtime/build dependencies, direct machine-code/object generation, an Eristavi-owned linker, and additional platform support.

Those are later stages. The immediate problem is compiler throughput under the owned runtime.

---

## 5. Performance work completed so far

The optimization effort has been deliberately driven by measurement rather than speculative rewriting.

| PR | Main result |
|---|---|
| #44 | Improved owned graph-registry capacity/growth and hash distribution for large heaps. |
| #45 | Fixed collector scheduling that caused excessively frequent full tracing on large heaps. |
| #46 | Added native compiler phase tracing and preserved timeout diagnostics. |
| #47 | Indexed Universal IR verification and reused dataflow masks. Owned verifier benchmark improved roughly 3×. |
| #48 | Reworked typed-IR ownership verification and removed a major quadratic local-identity scan. |
| #49 | Removed quadratic typed-local table construction in `ir_lower.eri`. |
| #50 | Indexed typed verifier locals while preserving scope activation and diagnostics. |
| #52 | Made the owned graph registry grow earlier at its existing load bound. Collision-chain comparisons fell roughly 68% on the measured optimizer workload. |
| #53 | Indexed Typed IR type registration without changing public type IDs or `Program.types`. |
| #54 | Indexed specialization/source lookup without changing routine order or specialization identity. |
| #55 | Indexed Typed IR type queries during lowering. This was the breakthrough that moved the owned self-build fully beyond typed lowering and Universal IR construction. |
| #57 | **Current open PR.** Indexes Universal verifier flow lookups. |

Issue **#51** is the ongoing performance/evidence tracker and contains much of the historical benchmarking evidence.

---

## 6. Important historical bottleneck progression

Earlier, the owned compiler could not complete Typed IR lowering within bounded runs.

The sequence #48 → #49 → #50 → #53 → #54 → #55 progressively removed those bottlenecks.

Examples of progress included a 300-second frozen workload moving from approximately 103 completed lowering functions, to 121, to 144.

PR #55 changed the situation dramatically.

A candidate workload that previously hit the 300-second cap completed the complete frozen compiler workload in approximately:

```text
99.82 s wall
98.71 s user
exit 0
```

It completed all 428 lowering functions, Typed IR verification, Universal IR lowering, Universal optimization and x86 assembly generation on that bounded bootstrap-style workload.

That result justified attempting the real **900-second owned self-build** again.

---

## 7. The 900-second owned self-build after PR #55

Two independent repeatability samples were run.

Both reached the hard 900-second cap.

Crucially, they no longer timed out in Typed IR lowering.

Both completed:

```text
Typed/source lowering:       453 / 453
Typed IR verification:       454 / 454
Universal IR lowering:       454 / 454
```

Both then entered:

```text
universal-optimize
```

and remained there until the 900-second cap.

Sample 1 entered Universal optimization at approximately:

```text
844.09 s
```

Sample 2 entered Universal optimization at approximately:

```text
720.76 s
```

Both then hit the 900-second limit.

Peak memory was approximately 580 MiB and both runs used identical compiler-B hashes.

This is a major architectural checkpoint:

**Typed lowering is no longer the blocking stage.**

The active gating bottleneck is now:

```text
Universal IR optimization
```

---

## 8. PR #55 status

PR #55 was successfully qualified and squash-merged.

Its merge commit on `main` is:

```text
17a39a508728e42465add23c497189684d6318a9
```

PR #57 currently branches from that state.

---

## 9. Investigation of the Universal optimizer

The Universal optimizer is intentionally small.

Its main optimization is unreachable-block removal, surrounded by mandatory Universal IR verifier passes.

Conceptually:

```text
verify before optimization
        ↓
reachability / remove unreachable blocks
        ↓
verify after optimization
```

Therefore the measured cost called `universal-optimize` is not necessarily sophisticated optimization logic. Much of it is verifier work.

A bounded profile on merged `main` separated the costs.

For one optimizer pass over the full compiler workload:

```text
Pre-optimization verifier:
12,404 flowAt calls
402,965 linked Flow-node visits

Post-optimization verifier:
12,401 flowAt calls
402,956 linked Flow-node visits

Reachability:
6,871 blockAt calls
229,120 linked block-node visits
```

The verifier fixed-point process itself was **not** excessively iterative.

It required only approximately:

```text
773 iterations across 454 routines per verifier pass
```

Therefore repeatedly rescanning due to convergence was not the correct immediate target.

The major obvious target was the repeated linear `flowAt()` lookup.

---

## 10. Current open PR #57

Current PR:

```text
#57 — Index Universal verifier flow lookups
```

Current PR head:

```text
8af0ffe3350c737550c3ab0e6c3fa89f60f6f091
```

Base:

```text
main @ 17a39a508728e42465add23c497189684d6318a9
```

PR #57 currently changes exactly two production/review files:

```text
src/compiler/universal_verify.eri
tests/universal_verifier_cases.py
```

No temporary diagnostic workflow/helper remains in the final PR diff.

The implementation introduces a compiler-private exact flow index using **257 buckets**.

The canonical `Flow.next` chain remains untouched.

This preserves validation order, propagation order, fixed-point behavior and existing semantics.

Bucket selection is based on block index, but a lookup hit still requires exact block-index equality.

Sparse block IDs remain supported.

The optimizer's separate reachability `u.blockAt()` lookup was deliberately **not** optimized in this PR so that the verifier-flow change could be measured independently.

---

## 11. PR #57 correctness evidence

The existing wide/sparse/cyclic public verifier oracle passes with exact diagnostics.

Native verifier execution passes.

A deliberate hash-collision regression was added.

The test uses valid block IDs:

```text
0
257
```

which intentionally select the same private 257-bucket index.

The collision case passes on both bootstrap and native verifier paths.

This permanently verifies the intended contract:

```text
hash/bucket selection ≠ identity
exact block index = identity
```

Full `src/frontend.eri` baseline/candidate generated x86-64 assembly is byte-identical.

Recorded assembly SHA-256:

```text
1dd930ac741a994d3d337684df7fa3f7fd574e7e515212a876cee6d3354c40f2
```

No source-language semantics, public Universal IR representation, public ABI, diagnostic ordering, sparse-ID behavior or optimizer pass ordering changed.

---

## 12. PR #57 performance evidence

Bootstrap-runtime full-source paired comparison:

```text
Baseline:
120.60 s wall
119.68 s user

Candidate:
123.39 s wall
122.38 s user
```

Therefore:

**Do not claim a bootstrap or whole-compiler speedup from PR #57.**

The relevant target is the owned runtime.

A focused owned-runtime ABBA verifier benchmark used:

```text
64 registers
300 CFG chain blocks
6 verification rounds
```

All outputs were identical.

Results:

```text
A1 baseline:
5.24 s wall
4.55 s user
4,672 KiB RSS

B1 candidate:
3.02 s wall
2.73 s user
5,184 KiB RSS

B2 candidate:
2.91 s wall
2.63 s user
5,184 KiB RSS

A2 baseline:
5.08 s wall
4.41 s user
4,672 KiB RSS
```

Medians:

```text
wall:     5.16 s → 2.965 s
user CPU: 4.48 s → 2.68 s
RSS:      +512 KiB
```

That is approximately:

```text
42.5% lower wall time
40.2% lower user CPU
```

on the focused owned-verifier workload.

This is legitimate evidence for the targeted owned-runtime verifier operation.

It is **not** evidence of a 42.5% whole-compiler improvement.

---

## 13. PR #57 CI state — CURRENT CHECKPOINT

Normal CI run:

```text
CI #426
```

has completed successfully.

All four jobs are green:

```text
Linux x86-64 GCC       PASS
Linux x86-64 Clang     PASS
Linux ARM64 Clang      PASS
macOS Clang            PASS
```

PR #57 remains **open**.

The next required gate is full qualification on the **exact PR #57 head**:

```text
8af0ffe3350c737550c3ab0e6c3fa89f60f6f091
```

The 900-second owned self-build has **not yet been rerun for PR #57**.

Do not merge PR #57 yet.

Do not start the 900-second owned self-build before qualification is clean.

---

## 14. Immediate continuation instructions for GPT-6.1

Continue directly from this exact checkpoint.

1. Run/verify the repository's full qualification workflow on PR #57 head `8af0ffe3350c737550c3ab0e6c3fa89f60f6f091`.
2. Qualification should include owned integration plus the existing bootstrap self-build/offline Linux GCC, x86-64 Clang and ARM64 Clang gates.
3. Inspect successful logs, not only green status. Check for hash mismatches, skipped validations, fallback paths or audit warnings.
4. If qualification is clean on the exact head, run **one** 900-second owned B→C self-build/repeatability probe.
5. Preserve phase trace, wall/user/system time, RSS, compiler-B identity and completion/timeout phase.
6. Compare against the post-#55 baseline:
   - all Typed IR and Universal lowering completed,
   - timeout occurred in `universal-optimize`,
   - sample 1 entered optimization ~844.09 s,
   - sample 2 entered optimization ~720.76 s.
7. If the #57 run completes inside 900 seconds, verify complete self-build evidence and repeatability hashes before claiming success.
8. If it still times out in `universal-optimize`, **do not** immediately run another 900-second sample. Re-profile the optimizer after #57.
9. The previously measured reachability `u.blockAt()` path had ~6,871 calls / 229,120 linked block visits, but re-measure before targeting it.
10. Record meaningful evidence in PR #57 and issue #51.
11. If #57 proves worthwhile and all gates pass, squash-merge with an exact-head guard and verify `main`.

---

## 15. What GPT-6.1 must NOT do

- Do not redesign Eristavi's source language or compiler architecture.
- Do not remove verification to gain speed.
- Do not reduce validation passes merely because they are expensive without an equivalent architectural justification and explicit approval.
- Do not replace exact identity with hashes.
- Do not change public block IDs, type IDs, routine order, public IR order or ABI just to make indexing easier.
- Do not claim a whole-compiler percentage by extrapolating a microbenchmark.
- Do not repeatedly run the 900-second test hoping for a different result.
- Do not increase the timeout beyond 900 seconds merely to make the test pass.
- Do not leave temporary diagnostic workflows in production PRs.
- Do not merge if normal CI or qualification is not clean.
- Do not silently use C/LLVM/Python as permanent architecture to solve performance.
- Do not assume the next hotspot from old measurements after a major optimization; remeasure.

---

## 16. GitHub/repository hygiene

Diagnostic branches are preferred for temporary instrumentation.

Production PRs should contain only intentional source/tests/documentation.

Always inspect the final branch comparison before opening or merging a PR.

Prefer squash merge for performance batches.

Use expected-head verification before merging.

After merging, verify both PR merged state and `main`.

Meaningful benchmark conclusions should be recorded in GitHub, especially issue #51.

---

## 17. Current performance model

The owned runtime dramatically magnifies algorithms that repeatedly traverse linked identity structures.

Common pattern:

```text
small apparently harmless linked lookup
        ↓
called thousands/millions of times
        ↓
owned runtime makes pointer/object lookup expensive
        ↓
whole compiler becomes extremely slow
```

Successful improvements have often replaced repeated linear scans with private indexes while keeping the canonical public linked representation unchanged.

Examples include typed local indexes, type registration, type-ID lookup, specialization lookup, graph-registry indexing and Universal verifier flow lookup.

This pattern is useful but must not become dogma.

Measure each hotspot independently.

---

## 18. Why PR #57 remains technically reasonable

The bootstrap-runtime full-source result is slightly worse:

```text
120.60 s → 123.39 s
```

So PR #57 should not be justified by bootstrap performance.

The problem being solved is the **owned-runtime** B→C self-build.

The focused owned verifier benchmark shows approximately 40–42% lower CPU/wall time on the exact algorithm being replaced.

The implementation preserves canonical verifier ordering and produces identical compiler assembly.

Therefore PR #57 is reasonable to take through qualification and exactly one owned self-build integration test.

Its value must ultimately be judged by the owned trajectory.

---

## 19. Expected decision after the next 900-second run

Three meaningful outcomes:

### A. Owned self-build completes below 900 seconds

Treat this as a major milestone.

Verify:

- exit success,
- B/C assembly identity where required,
- B/C executable repeatability,
- offline audit,
- static executable properties,
- exact source identity,
- repeatability metadata.

Do not stop at "exit 0".

### B. Still times out later in `universal-optimize`

PR #57 may help but be insufficient.

Re-profile remaining optimizer work.

The reachability `blockAt()` path is a known candidate, but only target it if it is still dominant after #57.

### C. Little/no trajectory improvement

Reconsider whether PR #57 is worthwhile despite the focused benchmark.

Do not merge complexity just because a microbenchmark improved.

---

## 20. Broader roadmap after owned self-build succeeds

Once repeated owned compiler self-build is genuinely qualified:

1. Complete remaining collector/runtime integration.
2. Make compiler operation fully owned-runtime based.
3. Remove required Python build/bootstrap tooling.
4. Implement direct machine-code/object output.
5. Implement relocations and ELF generation.
6. Replace GNU assembler/linker dependencies with owned tooling.
7. Extend independent toolchain support:
   - Linux ARM64,
   - Windows,
   - macOS.
8. Continue toward a fully offline native compiler/toolchain.

Do not jump ahead to these merely to avoid finishing owned self-hosting.

The current milestone is still:

```text
Reliable, repeatable Eristavi compiler self-build
on the owned runtime
within the existing 900-second qualification boundary.
```

---

## 21. Project philosophy reminder

The aim is not simply to make Eristavi compile itself once.

The aim is to build a compiler/runtime/toolchain architecture that remains readable, deterministic, verifiable, independent and eventually capable of reaching the machine without relying permanently on another language ecosystem.

Performance work should remove accidental implementation complexity rather than compromise the language's semantics.

The philosophy remains:

> Complexity belongs in the compiler and runtime, not in the programmer's code.

**Continue from PR #57. Do not restart the project.**
