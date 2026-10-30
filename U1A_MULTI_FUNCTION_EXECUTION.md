# U1a multi-function reference execution and trusted imports

Status: **isolated U1a reference profile, qualified and merged as PR #92**. The existing
Eristavi frontend → Typed IR → native compiler paths are **not replaced**.
The governing approved design is
[the U1 contract](docs/architecture/Eristavi-UIR-U1-Contract-2026-10-29.md)
sections 2, 4, 6–9, 13 and [issue #71](https://github.com/eristavi/eristavi-lang/issues/71).

## Implemented in this slice

- `u1_module.eri`: immutable-metadata FunctionId → independently verified
  completed/cell-free function-body registry. Forward declarations and mutual
  recursion bind by a declaration-table FunctionId, **not** a source name or
  guessed `fN` helper string. A sealed registry must have exactly one matching
  local body per defined declaration; imported functions cannot masquerade as
  local functions. Stale revisions and malformed dead blocks are rejected.
- `u1_execute.eri`: bounded independent interpreter of linked hand-built UIR.
  Every direct-call frame has private SSA value slots, simultaneous CFG-edge
  argument assignment, exact argument and ordered result counts, and distinct
  normal / terminal trap / budget-depth / unsupported-op outcomes. Calls can
  nest, recur and return zero or multiple values. An observable trace emitted
  before a callee's trap is preserved, while the actual trapping LocId remains
  the callee's original LocId. Fuel is bounded (1–1,048,576) and call depth
  is bounded (1–1,024), independent of the Python test timeout.
- `u1_effects.eri`: metadata/body revalidation at analysis time; direct
  terminal-fault bits for guards and integer division/remainder; conservative
  possible-divergence on CFG backward edges; DFS call-cycle detection; and a
  reverse caller worklist propagating all six effect categories (read, write,
  external, allocation, trap, divergence). Every local declaration's declared
  effect mask must cover the derived mask. Bodies are scanned including
  unreachable instructions; conservative over-approximation is intentional.
- `u1_imports.eri`: explicitly selected **version 1 test adapters only**:
  `u1.test.trace`, one i64 parameter, zero results, external effect mask 4;
  and `u1.test.identity`, one i64 parameter/result, mask 0. The selected
  module, real imported FunctionId, exact symbol bytes, signature,
  declared mask and version are independently validated. Missing/duplicate,
  changed, forged or incomplete imported contracts fail closed. Arbitrary
  optimizer-supplied effect claims or native callbacks are never trusted.

The executable scalar subset currently covers pred/i64 literals, pred.not,
pred.and/pred.or, wrapping i64 add/sub/mul, signed/unsigned i64 comparisons, signed i64
division/remainder with first-fault codes, guards, jump/branch/sparse-switch,
direct calls and returns. Unsupported instructions have a distinct explicit
outcome (kind 3), **never** guessed host semantics. In particular, strict
binary64 (including native rounding environment), unsigned division,
checked-overflow multiresult primitives, U1b narrow integer execution,
managed U2 values, fallible-call continuations and resource cleanup semantics
are **not implemented** by this reference evaluator.

## Outcomes and validation

`execute.run(program,policy,functionId,inputList,fuel,depthLimit)` returns
an `Outcome`: kind 0 normal with `count` ordered results; kind 1 a terminal
trap with `code` and original `location`; kind 2 fuel/depth exhaustion;
kind 3 explicitly unsupported opcode. `trace` records selected test-import
events in execution order. It is not an operating-system I/O transaction log.
`execute.value` rejects nonnormal/out-of-range results.

Before evaluation a new, independently verified effect snapshot validates
**every** linked UIR body and selected import version, checks effect upper
bounds, and is released after execution or error. No stale verifier report,
`verified=true` serialization or cached mutation revision is executable
authority. Exact local call signatures and all dead instructions are checked
by the already-independent U1 verifier. Budgeted word stores for frame SSA
slots are released in normal/early fault/fuel/call returns.

The `tests/fixtures/u1_execution.eri` acceptance fixture is **hand-built UIR**
rather than Eristavi source lowered by the production compiler. It checks
mutually recursive even/odd, first-fault order across nested direct calls,
zero/multiple returns, simultaneous edge arguments, conservative effect SCC
closure, trusted import trace, foreign/stale/wrong import rejection,
understated-effect rejection, bounded negative-input recursion and explicit
strict-f64 refusal. Python `tests/test_u1_execution.py` compiles and runs
this Eristavi fixture and asserts exact outcomes. `tests/test_u1_module.py`
continues to reject malformed unreachable calls and invalid body bindings.

## Remaining issue #71 gates

Do not declare all U1a or all imported effects ready merely because this
independent reference profile passes. Extend independent execution/oracles
to every admitted U1a scalar operation including strict f64, full trap origin
and mixed control-flow stress. Version-bound **production** import trust
requires a reviewed native runtime/FFI adapter; these two exact test adapters
cannot authorize arbitrary foreign functions. Verify physical-resource work
at scale, monotonic release contracts, cancellation, SSA promotion after
callgraph mutation and direct UIR native lowering separately.

Release policy: incremental updates run **one Linux smoke** via the revised
CI workflow; **one** final four-platform CI and the required completed-batch
qualification on the exact final source revision are mandatory before merging
compiler-code changes. Experimental `owned-self-build` is still separately
selected and not implied by this release.


## Qualified merge evidence — 2026-10-31

- Merged PR: [#92](https://github.com/eristavi/eristavi-lang/pull/92), main commit `e59ef7e6401990da5498b24f357077cc46e41e51`.
- Tested head `65b8109c9248162e63b4f1cedf91e5a25e4835df` passed the [complete four-platform CI](https://github.com/eristavi/eristavi-lang/actions/runs/41138028053) and [required completed-batch qualification](https://github.com/eristavi/eristavi-lang/actions/runs/41138028110). The merged implementation Git tree is identical to tested head: `0d85a50abbf1390e741ec7ff0705254ec5fc2c1a`.
- The experiment-only owned compiler self-build remains skipped, not qualified. Production/native UIR integration and the limitations documented above remain future work.
