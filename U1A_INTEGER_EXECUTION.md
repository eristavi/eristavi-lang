# U1a integer reference execution coverage

Status: implementation candidate, **not yet qualified or merged**. Baseline:
main `007aa4ac897a4d618b00955b7808db19792b2404`, following qualified PR #92.
Governing contracts: U1 operation contract §§4, 6–10, 13–15,
`INTEGER_REMAINDER.md`, `CI_QUALIFICATION.md`, `HANDOVER.md` §§25, 28–29.

## Implementation

`src/compiler/u1_execute.eri` now executes every admitted U1a i64/pred
operation: constants; eager predicates; wrap add/sub/mul; six signed/unsigned
overflow pairs; ten comparisons; signed/unsigned div/rem. Overflow operations
produce defined wrapped bits and a separate predicate, without trapping.
The ordinary checked-source recipe still uses `pred.not` and a located guard.
Div/rem report code 2 for zero; both signed MIN/-1 operations report code 1.
No output value is exposed on terminal fault.

Unsigned words retain their complete bits in signed Int containers. Division
uses at most 64 restoring rounds with safe modular arithmetic, plus safe
positive-divisor and high-bit-divisor shortcuts. Signed multiplication overflow
uses checked range thresholds; unsigned multiplication uses the exact unsigned
quotient ceiling. Multiplication and division loops charge work and poll through
the existing budget API. No floating point, unchecked signed host overflow,
new opcode, source syntax, budget increase or production pipeline switch is used.

Boundary tests found two existing wrapping-helper defects: `MIN+MIN` and
`MAX-MIN` could form an unrepresentable positive intermediate. Both helpers
now subtract one before taking the distance. Execution also closes partially
initialized frame storage and its phase when initialization fails; previously
only failures after entering the instruction walker had that cleanup.

The native quota test also exposed an existing checked-unwind/GC defect.
Surviving register root maps retained addresses of abandoned value slots;
after allocator reuse, a slot address could name Text bytes such as
`cancelled`, which the native-C collector then interpreted as a typed value.
Both `runtime/value_runtime.c` and the owned `graph_failure_x86_64` /
`slot_index_x86_64` implementation now clear exact abandoned-slot roots
before freeing them. A scratch hash index gives linear scans with exact-key
membership; the owned path has a no-allocation linear fallback on scratch
reservation refusal. Normal-call results, pre-boundary caller cells, interior
member references and non-value register classes are preserved. Native root
register arrays are writable; the ABI record layout and source semantics are
unchanged. This runtime correction is part of this batch's qualification.

## Independent evidence

`tests/test_u1_integer_execution.py` compiles the hand-built fixture
`tests/fixtures/u1_integer_execution.eri`, then compares actual Eristavi-written
evaluator output with independent unbounded Python mathematics. The oracle
does not copy the evaluator's wrapping/threshold/division algorithms.

- 315 operand pairs: a 15×15 boundary grid, 48 seeded full-word random pairs
  and 42 independently computed near-multiplication-boundary pairs. All 26
  arithmetic, comparison and predicate recipes yield **8,190 observations**.
- 600 combined cases: recursive zero/multiple-value propagation, trace before
  and after the call, sparse switches spanning the full word, loop-carried
  values, direct SSA versus mandatory cell promotion, every overflow pair,
  checked guards and unused trapping div/rem. Complete result/trap code,
  first-fault location and ordered trace are independently checked.
- Exact derived effect assertions: overflow pairs stay pure; div/rem and
  guards add terminal fault; loops/recursion add conservative divergence;
  callers inherit selected trace effects.
- Fuel/depth exhaustion, cancelled request rejection, a measured first-page
  quota failure during frame initialization, a nested late work failure,
  and malformed overflow-result rejection without a revision increment.
  Successful/faulting runs restore live/pending charges; cumulative traffic
  and work remain monotonic. These are modeled ownership counters, **not**
  complete physical heap/allocator/GC accounting.
- Focused native parity compiles the evaluator implementation through the
  existing Eristavi x86-64 backend and executes 44 numeric observations plus
  the failure checks on both native-C and static owned runtimes. It checks
  import-free/static ELF, non-executable stack and execution with an unusable
  PATH. Eight independent workers retain all cases with the unchanged 120s
  per-worker watchdog. An initial single-worker 42-observation owned attempt
  timed out and is not a completed performance/qualification sample. The full
  8,190-case grid uses the C-bootstrap path on each CI platform.
- Deterministic C and owned-assembly regressions assert duplicate abandoned
  roots are cleared, caller cells and normal results survive, integer-class
  bits remain unchanged, and the owned scratch-refusal fallback behaves the
  same. Existing allocation-lifetime and heap-GC sanitizer tests remain intact.

The integer tests are independent of the existing Python UIR promotion
evaluator; that evaluator's existing before/after fixtures remain unchanged.
Fast smoke adds the combined-flow and native allocation-lifetime tests. Full discovery includes all three new
tests, with the usual explicit Linux x86-64 restriction on owned native parity.

## Acceptance and limits

Before accepting the batch, require focused tests, final four-platform full CI
and completed-batch bootstrap/offline plus owned-integration qualification on
the exact final revision. Record their links in the PR; never substitute PR
#92's green results. The separate experimental 900-second owned compiler
self-build remains unselected. Do not merge based on smoke alone.

This completes the integer/predicate portion of the **reference evaluator**,
subject to those gates. It does not complete U1a or issue #71: native strict
f64, production selected import trust, source-origin/publication guarantees,
bounded simplification and wider physical-resource qualification remain.
U1b narrow execution/aggregates, U2 managed failures/resources and U3 production
frontend/native integration are separate. No whole-compiler speedup or physical
memory qualification is claimed.

Local sanitizer evidence uses `ASAN_OPTIONS=detect_leaks=0` only because this
container cannot inspect `/proc/.../task` for LeakSanitizer. The allocation
counter assertions, AddressSanitizer and UBSan still run. Hosted CI retains
its original sanitizer and LeakSanitizer defaults.
