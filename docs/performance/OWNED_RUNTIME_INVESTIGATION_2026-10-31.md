# Owned-runtime slow-test investigation

31 October 2026. Baseline: `0a2caea09ae9bb05a062a986a3412bc045bbf96b` (qualified PR #96 implementation).
Status: **investigation complete; recommendations and disposable prototypes only**.
No production compiler/runtime/test/workflow implementation has been changed.
No full CI or owned compiler self-build was run for this investigation.

## Finding in plain language

The owned runtime is repeatedly cleaning and re-sorting the same memory records,
even when little new graph-object memory has been created. It also re-checks
objects that the collector has already visited. Separate temporary lookup tables
are repeatedly requested from, then returned to, the operating system.

The tests expose a runtime bottleneck. They are doing genuine construction,
verification, arithmetic, recursion, cleanup and malformed-input work. Their
correctness checks should be retained. Ubuntu itself and slow compilation are
not the main cause established by this profile.

**Recommended first optimization batch:** allocation-pressure-aware graph/text GC
scheduling, exact-slot root filtering, and bounded reusable slot-index scratch.
A disposable combination preserved every observed result and greatly reduced
the runtime work. It is not a qualified production patch or a promised CI speedup.

## Reproduction and measured results

The original `test_integer_executor_on_both_native_runtimes` recipes and eight
worker groups were reproduced from `tests/test_u1_integer_execution.py` without
removing cases or assertions. Each worker's output was compared to the original
unbounded-integer oracle, including traces, faults, quota/cancellation and stale
verification checks. All eight workers retained their original 120-second wall
watchdog. The integer application assembly is identical across the C runtime,
owned baseline and disposable owned variants; only runtime assembly is varied.
The scratch source filename/root differs from GitHub's temporary checkout, so
this does not claim byte identity with a GitHub-produced binary.

The independent verifier protocol and 91-graph plus 128-block-chain oracle were
also rebuilt from the original tests and compared to their complete expected
outputs. These are focused existing workloads, not a rerun of the full suite.

| Local workload | C-runtime baseline | Owned baseline | Combined diagnostic prototype | Owned wall reduction |
| --- | ---: | ---: | ---: | ---: |
| All eight integer workers, summed | 17.775 s | 244.901 s | 57.335 s | 76.6% |
| Verifier malformed-IR protocol | 4.421 s | 57.017 s | 11.016 s | 80.7% |
| Dominator oracle, 91 graphs + 128-block chain | 3.318 s | 80.800 s | 11.041 s | 86.3% |

Full eight-worker owned baseline CPU: 230.412 user / 14.465 system seconds.
The combined prototype used 57.183 user / 0.120 system seconds on those workers.
All worker outputs and all verifier/oracle observations matched exactly.
These table rows are one serialized complete pass each; they are not five whole
suite repetitions. The combined prototype is root filtering + conditional index
preparation + a diagnostic 16x graph-GC scheduling budget + scratch reuse.

### Five-pair confirmation

Integer worker 0 was additionally run in **five fresh-process matched pairs**,
alternating baseline/candidate order, on the same host with the same compiled
application, runtime profiles, input, watchdog and environment. Jobs were
serialized. Neither external CI jobs nor other profiling experiments were
launched in parallel with the comparison. Binaries were already built;
filesystem/code caches were not flushed. This measures execution, not builds.

| Pair | Execution order | Baseline wall | Prototype wall |
| --- | --- | ---: | ---: |
| 1 | baseline, prototype | 37.395 s | 6.943 s |
| 2 | prototype, baseline | 38.924 s | 6.796 s |
| 3 | baseline, prototype | 35.996 s | 6.550 s |
| 4 | prototype, baseline | 39.640 s | 7.124 s |
| 5 | baseline, prototype | 37.617 s | 7.841 s |

Median: **37.617 → 6.943 seconds**, 5.42x ratio of medians
(81.5% lower wall time). Baseline range
35.996–39.640 s;
prototype 6.550–7.841 s.
Do not multiply this representative-worker ratio by another measured ratio or
apply it directly to whole compiler builds. CI hardware/load can differ.

## Attribution: where the CPU time goes

External `ptrace` sampling is blocked in this environment; `perf`/Valgrind are
not installed. A diagnostic-only Linux x86-64 `ITIMER_PROF` / `SA_SIGINFO` sampler
was added to a disposable runtime copy. It sampled instruction addresses every
5 ms of process CPU time, used no external process tracing, and retained exact
oracle output. The original production runtime was not edited.

The sampled worker produced 6,659 in-range samples. Addresses were
mapped using retained ELF symbols and local helper call targets, so the local
heapsort helper is not incorrectly charged to the preceding public function.
The 16-byte PC bins and timer interrupts make these approximate proportions.

| Exclusive sampled location | Samples | Approximate share |
| --- | ---: | ---: |
| `erist_rt_graph_owner` | 1,603 | 24.07% |
| `.Lg_index_sift` | 1,365 | 20.50% |
| `erist_rt_graph_mark_roots` | 538 | 8.08% |
| `erist_rt_graph_prepare_index` | 469 | 7.04% |
| `.Lslots_index_insert` | 355 | 5.33% |
| `erist_rt_graph_mark_value` | 292 | 4.39% |
| `erist_rt_graph_mark_object` | 258 | 3.87% |
| `erist_rt_graph_sweep` | 240 | 3.60% |
| `erist_rt_memory_load64` | 191 | 2.87% |
| `erist_rt_graph_kind` | 150 | 2.25% |

Owner lookup, heapsort and interval-index preparation together account for about
**51.6%** of sampled CPU time. Root traversal, value marking and sweeping add
substantial further collection cost. The free-list allocator itself accounts
for about 1.5%; its scan count is only about 1.06 visits per allocation here.
Replacing the allocator's first-fit list is therefore not the best first target.

### Exact event counts, measured separately

Separate flag-preserving assembly counters retained exact outputs. Instrumented
runs have substantial overhead; their duration is **not** used as a speed result.

| Event in integer worker 0 | Owned baseline | Combined prototype |
| --- | ---: | ---: |
| Allocator calls | 72,284,485 | 72,284,482 |
| Value-slot creations | 68,089,958 | 68,089,958 |
| Graph-object creations | 1,784,454 | 1,784,454 |
| Graph/text collections | 150,818 | 9,735 |
| Object-owner lookups | 118,397,346 | 33,116 |
| Interval-index preparations | 150,818 | 7,729 |
| Slot collections | 36,806 | 36,806 |
| OS memory reservations | 36,827 | 65 |
| OS memory releases | 36,806 | 44 |

The identical **68,089,958 value-slot creations** and
**1,784,454 graph-object creations** demonstrate that the gain is not
from deleting arithmetic/test work. Slot-collection count is also unchanged.
The changed scheduling/filtering removes repeated graph tracing and ownership
searches; the scratch cache removes repeated kernel mapping cycles.

The independent C-runtime diagnostic reported **55 managed-heap
collections** for the same worker, versus 150,818 owned graph/text collections.
The collectors have different representations and trigger policies, so these
are not equivalent units of work, but the large scheduling difference is real.
C managed-heap peak was 8,670,142 bytes, excluding its untracked administrative
storage and allocator overhead. That boundary is different from the owned
reserved-mapping metric below; do not equate them or claim a matched memory tier.

## Specific causes in the inspected code

1. **Collections are paced by many scalar safe-point visits.**
   `erist_rt_scalar_value_new` goes through `erist_rt_text_safe_point`.
   `evn_scope_leave` and `evn_pop` set the heap-dirty flag. Once dirty,
   `.Lgraph_safe_since` advances on safe points, while the post-sweep budget is
   approximately half the retained graph/failure/text count, with a minimum 128.
   Consequently ordinary scalar/verification helper work can trigger whole-heap
   tracing/sorting even when few new graph objects were allocated. The measured
   worker averages only about 12 newly created graph objects per collection.
2. **Slot roots are marked twice through different paths.**
   `erist_rt_graph_mark_roots` first visits every value slot, then considers
   class-1 frame roots through `erist_rt_graph_owner`, including addresses that
   are already known value slots. Those addresses often cannot be interior
   object cells, yet still pay a binary search. The C runtime already builds an
   exact slot-address set and skips this duplicate path; the prototype follows
   that safety rule without dereferencing arbitrary root addresses.
3. **The graph interval index is rebuilt and heapsorted at collection entry.**
   It is needed for actual interior roots, but repeatedly processing it at this
   collection frequency is costly. Conditional preparation alone gave little
   additional improvement in the exploratory worker: real/non-slot roots still
   often require it. A more complex incremental index is not the first proposal.
4. **Slot-index scratch is mapped/unmapped repeatedly.**
   `.Lslots_prepare_index` requests zeroed scratch with `erist_rt_reserve`;
   `erist_rt_slots_collect` releases it after each collection. A bounded cache
   can clear/reuse capacity and keep fallback behavior, avoiding kernel calls.
5. **Boxed values amplify all of the above.**
   The legacy source-to-native path creates a runtime value slot for literals,
   copies and expression results. The worker creates 68 million such slots.
   This is an architectural opportunity, but changing private scalar lowering
   or word-buffer storage needs a separate design and acceptance boundary.
   It is not a reason to replace the working compiler prematurely.

Source anchors: [value scope/slots](../../src/runtime/value_scope_x86_64.eri),
[graph heap](../../src/runtime/graph_heap_x86_64.eri),
[graph values](../../src/runtime/graph_values_x86_64.eri),
[scalar value helpers](../../src/runtime/value_scalar_x86_64.eri),
[allocator](../../src/runtime/allocator_x86_64.eri),
[independent C GC](../../runtime/native_gc_runtime.c),
[legacy universal lowering](../../src/compiler/universal_lower.eri),
[U1 word adapter](../../src/compiler/u1_words.eri).

## Optimization options, ranked

| Priority | Proposal | Measured diagnostic evidence | Engineering scope / requirements |
| --- | --- | --- | --- |
| 1 | Pace graph/text GC from fresh managed allocation bytes/count and live-heap pressure, with explicit memory limits and bounded polling | Worker 0: 34.02 s baseline; 14.24 s with 4x scheduling budget; 9.27 s with 16x | Medium risk. Design a pressure policy; **do not blindly ship the diagnostic multiplier**, disable GC or remove forced-collection testing. Track text, graph and failure allocation, backing bytes, cancellation and allocation-failure behavior. |
| 2 | Skip duplicate exact-slot roots before interior-owner lookup | 34.02 → 27.35 s without changing collection cadence | Low/medium scope. Preserve exact-address checks, collision handling, interior roots, protected values, failures and fallback if scratch cannot be reserved. Independent C implementation supplies a concrete precedent. |
| 3 | Reuse bounded slot-index workspace instead of mapping it per collection | In combined verifier graph probe: 18.98 → 11.04 s; kernel time 6.84 → 0.004 s | Low/medium scope. Clear reused keys; validate capacity arithmetic; prevent overlapping/nested ownership; retain no-allocation fallback, explicit release/reset and resource accounting. Alone it barely changed the graph-GC-dominated integer worker. |
| Later | Reduce boxed scalar temporaries and use denser compiler-private word buffers | 68 million temporary slots establish scale; no isolated production speed result | Higher architectural scope. Preserve the existing value ABI at boundaries, checked arithmetic, root maps, value/identity semantics and UIR budgets. Address through reviewed lowering/storage work, not an ad hoc ABI change. |

**Recommended implementation:** the first three as one narrowly scoped runtime
batch, starting with explicit collector accounting and the allocation-pressure
policy. The prototype combination is strong evidence for the mechanisms, not a
substitute for production design, hardening or qualification. Faster compilation
flags, test deletion and OS changes do not address the measured main bottleneck.
Keep all independent mathematical/malformed-IR and first-fault oracles.

## Memory and safety observations

The disposable mapping telemetry counted successful reservations/releases inside
the actual owned native runtime. Worker 0 baseline peak dynamic reservation was
1,458,176 bytes; combined peak 1,409,024 bytes.
Reservation traffic fell from 2,896,707,584 to 2,162,688 bytes.
Traffic is cumulative virtual reservation activity, **not simultaneous RAM use**.
The exact-root prototype additionally reserves 1 MiB of static virtual BSS
workspace and touches only its active hash-table range. These figures exclude
ELF/code, stack, static storage and OS/allocator overhead; they do not qualify
complete physical UIR heap/GC accounting. C managed-byte statistics use a
different boundary and cannot be compared as total process memory.

`wait4` peak RSS appears dominated by inherited pre-exec state. Per-PID `/proc`
reads in this environment did not reliably identify the native child and often
returned no usable RSS samples. Those raw fields are retained in evidence but
**excluded from memory conclusions**. No unsupported RSS/speedup claim is made.

The prototypes preserved all original integer-worker outputs, checked failures,
quota/cancellation behavior and the complete protocol/dominance outputs. This
is not proof of every language lifetime/GC/resource case. A production patch
must additionally cover:

- forced collection at aggressive intervals, tiny heaps and allocation refusal;
- zero/duplicate/colliding/foreign roots, interior roots and protected temporaries;
- checked unwinding, nested scopes, abandoned-slot root clearing and scratch failure;
- shared List snapshots, nominal value copies, identity mutation, Text/views and
  deterministic resource cleanup under real memory pressure;
- complete physical storage/capacity/traffic accounting for retained workspace;
- matched stress and the unchanged full four-platform CI + required completed-batch
  qualification once on the final implementation revision. The separate full
  owned compiler self-build remains unselected unless explicitly requested.

## Evidence and reproduction

Raw observations, input/build hashes, counter/sample data and the diagnostic
harness are retained in [the evidence appendix](../evidence/2026-10-31/owned-runtime-profile-evidence.md).
Run only disposable copies against the pinned baseline. The 16x scheduling
experiment is deliberately not a source/compiler/runtime patch in this repository.
All results are local native execution measurements; no whole-build performance
or future GitHub Actions duration is promised.
