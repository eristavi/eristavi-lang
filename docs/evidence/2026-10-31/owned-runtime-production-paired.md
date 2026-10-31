# Production owned-runtime same-host A/B benchmark — 31 October 2026

**Status: measured; opt-in GitHub Actions job PASSED.** This evaluates the
*actual merged source versions*, not the disposable prototype described in
the earlier performance investigation.

- Run: [41198570405](https://github.com/eristavi/eristavi-lang/actions/runs/41198570405)
- Raw machine-readable artifact: [owned-runtime-abba-41198570405](https://github.com/eristavi/eristavi-lang/actions/runs/41198570405/artifacts/13040469945)
  (artifact #13040469945, ZIP digest
  `sha256:94e4035eb8fd5da5ab7a844a737f2d86160b990abd8de86ce483019f4e24ab9e`).
- Harness branch test head: `e846f06d12fcb5d802ce9b34804d1bf7d1906366`.
- Before: qualified exact pre-PR99 main `4f876009c9786d4e47807d42fe91d922f147a2b4`.
- After: qualified PR99 merged runtime `388bfb6da42a6c0c1de307a0aa72ea987b63bbb0`.
- Host: GitHub Actions Ubuntu 24.04 Linux x86-64, Clang 18.1.3.
- Workload: **worker 0** from the original `test_u1_integer_execution`
  fixture, preserving the complete independent Python unbounded-integer
  expected result and original **120s per-execution watchdog**.
- Method: one identical generated application assembly, linked separately
  to baseline and optimized owned runtimes. Five serialized AB/BA
  fresh child-process pairs; no concurrent benchmark children, timeouts,
  instrumented timed sections or page-cache flushing. Raw stdout SHA-256,
  runtime/ELF hashes, CPU, RSS, metadata and matched-output proof are retained
  in the artifact ZIP. No test assertions, language semantics or ABI changed.

| Pair | Order | Before wall s | After wall s | Before user CPU s | After user CPU s |
| --- | --- | ---: | ---: | ---: | ---: |
| 1 | AB | 21.649 | 3.719 | 19.676 | 3.183 |
| 2 | BA | 21.869 | 4.040 | 19.366 | 3.235 |
| 3 | AB | 20.932 | 4.040 | 19.292 | 3.222 |
| 4 | BA | 21.928 | 3.897 | 19.314 | 3.147 |
| 5 | AB | 22.032 | 4.019 | 19.395 | 3.141 |

**Reported exact median values:** baseline 21.869176 seconds, optimized
4.019040 seconds, **5.4414x speedup** (about 81.6% reduction in wall time)
on this *particular*, actual-production runtime worker.

**Memory:** `wait4().ru_maxrss` returned 127,628 KiB in both variants
on every child. This is full process peak RSS, **not an attributed UIR-owned
buffer measurement** and not proof of equal peak allocation or collector
memory costs. The optimized runtime includes two additional bounded
64 KiB BSS buffers. CPU time, wall time and RSS describe this fixed
workload only; no claim of 5.44x faster *whole compiler* or all programs.

**Future optimization/resource gates:** add separately matched compiler-source
benchmarks and GC/mapping event counters; measure U1a private IR owner backing
vs real retained heap/allocator/GC under 8/32/128 and larger stress before
closing [#77](https://github.com/eristavi/eristavi-lang/issues/77).
The historic [#51](https://github.com/eristavi/eristavi-lang/issues/51)
graph-registry hypothesis must be retested against current source: the
initial static 8192-bucket table now grows when live count exceeds **16,384**;
the issue's older 65,536 threshold is no longer current, so blindly
reimplementing its recommended change would be wrong.
