# U2 checked Function — publication producer performance checkpoint

6 November 2026, branch `compiler/u2-cleanup-foundation-20261102`.
Draft PR #111 / open issue #74. This is an incremental engineering
candidate, not final acceptance or release.

## Observed evidence prior to change

- [Focused #42259784644](https://github.com/eristavi/eristavi-lang/actions/runs/42259784644): 18 methods run, 17 pass, 1 120-second owned generator timeout; five test-source phase markers prove the stall is within `native.emitChecked`.
- [Focused #42260926729](https://github.com/eristavi/eristavi-lang/actions/runs/42260926729): 18 methods run, 17 pass, 1 120-second owned generator timeout. Temporary isolated compiler source markers establish `ssa.verify`, signature checks and canonical table snapshots complete. The last observed marker precedes building per-instruction root publication bits. No `publication-verify` marker is observed.
- These are incomplete runs. No whole-compiler or owned-runtime speedup is yet established.

## Semantics-preserving change

The original slow emitter performed two complete linked-block-tail liveness
searches for **each** instruction / tracked ValueId pair to construct its
per-instruction publication bitmaps, and repeated those queries again in an
independent verifier. With N instructions, R tracked managed SSA values and
per-block chain length L, producer cost was proportional to O(R*N*L), in
addition to operand rescans and the unchanged independent verifier.

The new producer allocates the exact global `N*R` before/after buffers and
walks each original canonical block chain once to collect instruction IDs
(including unreachable blocks, and in original linked order). For each
tracked ValueId it makes a reverse sweep recording uses at/after and strictly
after each instruction, then a forward sweep recording whether an ordinary
SSA definition has occurred. It uses the original frozen output liveness bit
and writes by **global InstId**, because instruction IDs can interleave
across blocks. Block-entry bits still come from the existing SSA API.

The optimized construction has bounded O(R*(N + total operands)) work after
canonical verification, without per-query suffix rescans; it uses one bounded
block instruction-order vector and reuses the output vectors as scratch.
`budget.work` still charges all scans. No new public ABI, source syntax,
trusted verification flag, collector, root class, GC policy or checked
error contract is introduced.

## Critical safety proof boundary

`ssa.verifyPublications` is deliberately **unchanged**. It independently
rederives the canonical liveness Plan and recomputes every entry/before/after
bit from original SSA queries, including unreachable code. If the optimized
producer differs in any one bit, the emitter refuses before emitting native
assembly. Existing negative tests for missing/foreign/dead publications,
forged backing and refusal cleanup remain required.

## Verifier bottleneck and independent last-use candidate

- [`ac475bb` focused #42262947027](https://github.com/eristavi/eristavi-lang/actions/runs/42262947027):
  18 methods executed, **17 passed / 1 unchanged 120-second owned
  generator timeout**. The owned run emitted `U2_NATIVE_TRACE:publication-verify`,
  confirming producer construction completed. It emitted no
  `U2_NATIVE_TRACE:publication-done`. The next bottleneck is verifier
  execution, not the original producer.
- In the same `ssa.verifyPublications` function, fresh `ssa.verify`
  reconstruction is preserved, as is exact selected-ID, entry-bit,
  before/after-bit comparison across reachable and unreachable blocks.
  Point-query `ssa.liveBefore` and `ssa.liveAfter` remain unmodified
  independent references. The new checker traverses the ORIGINAL canonical
  linked instruction records, finds each ValueId's last-use position and
  local definition position, and compares both exact root bits at every
  global InstId. That last-use algorithm is distinct from the producer's
  reverse suffix bitmap. A mismatched or missing bit still rejects.
- Separate deterministic Python model check of original point-query truth
  versus the last-use formula: **3,093,668 randomized
  before/after/instruction/definition/use combinations, zero mismatches**.
  This is a *model check only*, not a compiler, runtime, sanitizer, or CI pass.
  No test skip, watchdog extension, or accepted memory budget change.

## First new verifier validation and syntax correction

- [`e5bdcc9` List/SSA focused #42263997707](https://github.com/eristavi/eristavi-lang/actions/runs/42263997707) failed to compile the changed module due to Eristavi's existing no-shadowing rule: `u2_ssa_liveness.eri:516:9: name 'i' is already visible`. The many dependent test failures all reflect this single module compile error. This does not qualify or refute runtime/root semantics.
- Corrected by assigning `i=0` to the function's existing mutable local rather than redeclaring `let i be 0`. No source semantics, frozen contracts or verifier criteria were changed. Hosted corrected-source results pending.

## Post-correction exact-source evidence / next diagnostic

- [`c63f2a6` SSA/List #42264207607](https://github.com/eristavi/eristavi-lang/actions/runs/42264207607): 8/8 passed, including adversarial SSA liveness, List snapshots and CFG loops.
- [`c63f2a6` identity-root #42264207644](https://github.com/eristavi/eristavi-lang/actions/runs/42264207644): 15/15 passed.
- [`c63f2a6` managed Function #42264207710](https://github.com/eristavi/eristavi-lang/actions/runs/42264207710): 18 methods, 17 pass, 1 unchanged 120-second owned generator timeout. Last marker `publication-build`, not `publication-verify`. Exact performance bottleneck is not yet conclusively explained; this stage position can change across hosted runs.
- The next revision adds **test-only monotonic timestamps** from stdout lines during the owned binary execution and finer block-level markers in a temporary compiler copy. It retains the absolute watchdog, bytes, status, and independent C comparison. No source-language, verifier, API or production compiler change; validation pending.

## Source-stage timing and refined diagnosis

Hosted [#42266043455](https://github.com/eristavi/eristavi-lang/actions/runs/42266043455)
failed only the existing owned-generator watchdog (17 other focused
methods passed). Timestamped phases from generator start:
0.000 begin; 0.832 metadata; 4.003 Function construction;
4.111 native emitter entry; 57.436 at `ssa.verify` call entry;
113.668 after its return and checked-root admission;
113.821 snapshot; 119.584 publication builder entry;
120.000 deadline. The original interpretation that root publication
itself dominated was unsupported: **~110 seconds elapsed in the
earlier two verification/plan phases**. No performance pass or
regression claim follows from this incomplete run.

Next isolated source tracing marks canonical verification,
plan construction, independent plan comparison and checked-root
verification. Instrumentation changes no production compiler,
public point-queries, owned-runtime behavior, or timeout.

## Verification vs plan construction — measured breakdown

Exact-head [run #42267466631](https://github.com/eristavi/eristavi-lang/actions/runs/42267466631)
at `8d94a439`: 18 checked+managed focused tests, 17 pass, 1 owned
source-generator watchdog timeout at unchanged 120 seconds. Host-monotonic
timestamps around two independent liveness proofs:

| Phase | Start | End | Observed elapsed |
| --- | ---: | ---: | ---: |
| First canonical verification | 9.895 s | 40.990 s | **31.095 s** |
| First SSA plan construction | 40.998 s | 57.633 s | **16.635 s** |
| Second canonical verification | 57.653 s | 91.442 s | **33.789 s** |
| Second SSA plan construction | 91.451 s | 109.300 s | **17.849 s** |
| Comparison and admission | 109.300 s | 114.198 s | ~4.898 s |

No independent owned/C generator parity result or wall-clock speedup.
Next narrow diagnostic instruments `u1_verify.inspect` stages (bounds,
metadata, contracts, structure, dominance/SSA) and the SSA plan's
select/uses/flow, **only inside the temporary test compiler source**. No
production compiler, ABI, watchdog, root verifier or owner semantics change.

## Validation status

- Exact `e40a64b` [Text/List integration #42262075150](https://github.com/eristavi/eristavi-lang/actions/runs/42262075150): **12/12 passed**.
- Exact `e40a64b` [managed focused #42262075162](https://github.com/eristavi/eristavi-lang/actions/runs/42262075162): **18 run, 17 pass, 1 diagnostic-fixture failure**. The fixture asserted its obsolete `// Independently prove EACH publication obligation` marker was present. The optimization removed that comment; execution never reached the owned generator. **No owned-generator time/success/120s result on this head**. The next patch corrects only that marker.

Pending exact-head focused owned-generation and whole-Function managed,
Text/List integration, saved primary/secondary, root/owner negative tests.
The old 120-second watchdog remains unchanged. Full four-platform and
completed-batch qualification are NOT claimed; #74 stays OPEN and #111 DRAFT.
