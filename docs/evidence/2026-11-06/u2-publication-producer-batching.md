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

## Detailed last verification trace and scoped reduction candidate

Exact [#42268931408](https://github.com/eristavi/eristavi-lang/actions/runs/42268931408)
on `a51182e`: **18 methods / 17 pass / 1 owned-generator timeout**.
Host-time measured in the same test-only isolated source:

| Step | Start s | End s | Elapsed s |
| --- | ---: | ---: | ---: |
| First canonical fallible verification including bootstrap | 12.141 | 54.962 | 42.821 |
| Nested canonical inspect to structure | 21.734 | 44.922 | 23.188 |
| Locations/dominance/SSA and final canonical checks | 44.922 | 54.961 | 10.039 |
| First liveness selection/use scan | 54.972 | 63.057 | 8.085 |
| First liveness flow fixpoint | 63.057 | 77.871 | 14.814 |
| Second full canonical re-verification | 77.900 | >120 | Not completed |

The enclosing run observes startup/temporary instrumentation overhead,
so these values must not be compared to uninstrumented whole-program speed.

**Next source candidate**: inside *private checked Function emission only*,
remove the redundant middle `ssa.verify` call immediately after
`roots.create`, which already reverified the source and created the Plan.
The independent fresh whole-Function and all-root-bit oracle
`ssa.verifyPublications` continues as the mandatory final gate
**before any output**; it reconstructs original canonical source and
compares the plan (including dead blocks). Nonchecked paths unchanged;
`ssa.verify` and `ssa.requirePublished` public APIs unchanged.
No acceptance or speedup claim until exact-head owned-vs-C and negative tests.

**Explicit rejected shortcut**: do not up-front batch all radix-word
`budget.work` calls; `tests/test_u1_words_path.py` pins exact
failed-read work charges at each missing depth and resource limit.
This project contract must not be weakened to achieve a benchmark win.

## Checked-only deferred verifier: instrumented hosted results

Exact commit `7b17207`:

- [Text/List #42270143006](https://github.com/eristavi/eristavi-lang/actions/runs/42270143006): **12/12 pass**, code changed in private checked path and normal Text/List behavior preserved.
- [Managed Function #42270142869](https://github.com/eristavi/eristavi-lang/actions/runs/42270142869): **18 run / 17 pass / 1 owned-source-generator timeout**. In the instrumented binary, root-plan construction completed at 45.350 s, publication production at 58.339 s, independent `ssa.verifyPublications` entered at 58.339 s, its fresh canonical verifier completed at 101.779 s, and independent liveness reconstruction reached flow at 110.848 s. The unchanged watchdog expired at 120 s; no byte-identical C generator output or depth-32 probe was reached in this method.
- **Important measurement caveat:** this test injects many `output` calls and comments into both compiled source-generator inputs, including canonical verifier hotspots, and those allocations/IO are inside the timed program. The timestamps are phase-local evidence only, **not** a clean production generator performance result.

Next test-only change makes all `output`-based source annotations
**opt-in** via `ERISTAVI_U2_OWNED_GENERATOR_TRACE=1`. The standard
test runs the unchanged original fixture and compiler modules, its
original 120-second watchdog and byte-exact C/owned generator comparison.
The optional trace remains available without contaminating standard
qualification. No production compiler/runtime/ABI change in this patch.
Exact-head qualification pending.

## First hosted fast-read build gate

[Run #42272459327](https://github.com/eristavi/eristavi-lang/actions/runs/42272459327):
the original U1a exact-path test was added as the **first**
test in the focused managed-Function workflow. It correctly blocked
the rest of testing because the fast-path candidate tried to bind a
`maybe identity Node` directly to a nonoptional Node in the loop.
The source compiler refused at `u1_words.eri:101:13`.
This is a candidate compile error, not evidence of a runtime fault
or budget-accounting regression. The corrected code invokes the
existing `needNode` and `needPage` unwrap helpers only after
explicit non-none checks. No production semantics or resource
policies are changed. Corrected exact-source tests pending.

## Candidate: fast successful radix read with original refusal path

After the clean uninstrumented
[run #42271055504](https://github.com/eristavi/eristavi-lang/actions/runs/42271055504)
failed the unchanged 120-second owned/C generator watchdog (17/18 passed),
we traced hot canonical verification to repeated frozen word-store reads.
The accepted `u1_words.get` implementation invokes `budget.work(phase,1)`
at entry and then six additional times at the individual 6-level radix
child reads. Each owner/phase work call validates accounting state and
polls cancellation. For many legitimate SSA/verifier reads this is
substantial repeated work. We did **not** relax the watchdog or skip a proof.

The proposed *source* fast path:
- Reread the **current** complete six-level radix node/page graph on
  every call (no cache / trusted summary / retained pointer).
- Enter fast path only with a fully present page and capacity to charge
  **all seven units** under the phase, owner and parent work limits;
  then call `budget.work(phase,7)` exactly once, returning the original
  page word.
- For any incomplete backing or inadequate work budget, delegate to
  the byte-for-byte original slow per-level `budget.work(1)` path.
  Thus missing root/child/page and limited-budget exact failure
  categories, requested/remaining figures, and `phase.used` advances
  remain unchanged. Every successful read still charges exactly 7 units.
- No changes to `set`, `push`, phase/owner schema, source syntax,
  allocator ownership, emission, root verification or public ABI.

**Acceptance gates:** `test_u1_words_path` on original C and owned
native runtimes; U2 checked generator still at original 120 seconds with
independent byte-for-byte C/owned output and depth-32 forced-GC oracle;
checked/managed, Text/List, SSA/identity roots, malformed/stale/dead/
owner fault matrix and documented physical resource limits. Roll back
candidate if those fail; do not treat structural reasoning as a pass.
No exact-head results or speedup recorded yet.

## Latest exact-source successful qualification of the focused blocker

Source `4b71966deb60da883b325936987b7f558ac7fe23` after
the source-type correction of the optional radix unwrap:

- [U1a complete radix path + exact failure accounting](https://github.com/eristavi/eristavi-lang/actions/runs/42272620378):
  **1/1 PASS** in 12.638 s; C and owned runtimes, malformed/missing
  root/child/page, no stale backing, original 0..6 work-budget
  failures and per-owner charges.
- [Checked/managed Function focused run](https://github.com/eristavi/eristavi-lang/actions/runs/42272620378):
  **18/18 PASS** in 272.861 s, including **98.399118497 s** for the
  uninstrumented individual owned source generator under unchanged
  **120 s** watchdog. Includes exact owned-vs-C assembly comparison,
  static linker/loader/undefined symbol and executable-stack checks,
  checked recursion with parent roots and depth-32 forced GC, as well
  as malformed/dead root/failure/owner refusals.
- [Linux Clang smoke #42272620164](https://github.com/eristavi/eristavi-lang/actions/runs/42272620164):
  **159 run / 156 pass / 3 intentional skips / 0 failures**,
  scoped checks PASS. Explicitly skipped final four-platform matrix.
- [Earlier exact pre-word-reader Text/List #42270143006](https://github.com/eristavi/eristavi-lang/actions/runs/42270143006)
  **12/12 PASS**; newest smoke also includes current unchanged behavior.

This is a **measured, passing focused generator result**, not
general Eristavi compiler speedup or completed U2 acceptance.
Still open: arbitrary/mutual calls, nested generic managed values and
typed new FailureContexts, general whole-Function File/handler cleanup,
comprehensive combined root/owner/fault/physical evidence, independent
cross-compiler comparisons, final 4-platform CI and completed-batch
qualification. No final merge. Subsequent docs-only commits must not
be confused with changes to this passing source tree.

## Validation status

- Exact `e40a64b` [Text/List integration #42262075150](https://github.com/eristavi/eristavi-lang/actions/runs/42262075150): **12/12 passed**.
- Exact `e40a64b` [managed focused #42262075162](https://github.com/eristavi/eristavi-lang/actions/runs/42262075162): **18 run, 17 pass, 1 diagnostic-fixture failure**. The fixture asserted its obsolete `// Independently prove EACH publication obligation` marker was present. The optimization removed that comment; execution never reached the owned generator. **No owned-generator time/success/120s result on this head**. The next patch corrects only that marker.

Owned/C checked generator and focused managed tests now PASS on
`4b71966`, as do radix exact-refusal and broad Linux smoke. Only
the broader U2 functional/physical/fault/oracle gates and final four-platform
and completed-batch qualification remain unaccepted. The unchanged
120-second watchdog is preserved; #74 stays OPEN and #111 DRAFT.
