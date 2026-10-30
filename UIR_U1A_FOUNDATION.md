# U1a construction and accounting foundation

This review slice starts the agreed typed Universal IR in Eristavi source. It is
isolated: the working compiler continues using its existing pipeline. No grammar,
language semantics, public value ABI, target selection, or file extension changes.

## Included

- `compiler.u1_budget`: request/shared/function owners, pending reservations,
  commit/cancel, live and reserved peaks, cumulative allocation traffic, same-kind
  sibling transfer, split handles, bounded prepaid work, cancellation, closure,
  and failed-attempt abandonment. Failed admission checks precede counter mutation.
- `compiler.u1_words`: append-only dense indices over 16-word pages and a radix-16
  directory. At most six directory levels cover the bounded word index space.
  Reads/writes do not copy a whole ordinary List. The current source frontend does
  not support parameterized List field declarations, so this adapter also avoids
  introducing new collection syntax or modifying language rules.
- `compiler.u1_meta`: primitive `pred`/`i64`/`f64` TypeIds, canonical signatures
  using an exact 64-bucket index, owned parameter/result pools, source revision
  identities and byte spans, program-scoped IDs, and immutable table APIs. Hash
  collisions still compare complete parameter/result sequences.
- `compiler.u1_ops` and `compiler.u1_builder`: a first fixed operation subset,
  function-scoped BlockId/ValueId/InstId APIs, independently owned indexed records,
  explicit operands/results, typed edges and simultaneous edge-argument ordering,
  zero-result operations without fake void values, and complete-construction freeze.

No module retains an AST, semantic Analyzer, mutable TypeVar, or old `typed.Program`.
Identity keys distinguish owner scopes without a global mutable ID allocator.
`complete()` means **construction complete**, not verified, executable, or ready
for production publication. There is deliberately no trusted `verified` bit.

## Representation in this slice

| Record | Word fields |
|---|---|
| Block (5) | first parameter, parameter count, first instruction, last instruction, terminator |
| Value (4) | TypeId, definition kind, defining block/instruction, result ordinal |
| Instruction (10) | op, block, operand start/count, first result/count, LocId, two attributes, next instruction index |
| Edge (3) | target block, argument start/count |
| Signature (6) | full hash, next collision index, parameter start/count, result start/count |
| Source (4) | logical-name byte start/count, digest-byte start, source byte length |
| Location (7) | SourceId, start/end/anchor, line/column, reserved origin index |

Indices are dense and checked; zero is absence. Typed handles carry owner identity
and an index restricted by the applicable profile ceiling. The Eristavi `Int`
implementation/32-byte value ABI still determines physical storage in this
bootstrap adapter. These word rows are **not** a frozen encoding or a claim of
packed 32-bit physical IDs. Per-block instruction ordering uses integer next
indices in the dense instruction table, not an allocated node per operand.

The first operation subset is: i64/pred constants, raw binary64 constant bits,
signed add-with-overflow results, predicate negation, guard, jump, branch, and
return. Add-with-overflow describes a wrapped result plus predicate; the explicit
guard remains separate. Direct calls, switches, the rest of arithmetic/Float, and
their independent semantic/reference verification are subsequent U1a slices.

## Budget boundary

`UIR_U1A_BUDGETS.json` records selected numeric policies. Factory defaults are
checked against it by executing Eristavi code, including qualification versus
development function capacities and construction/verification/promotion quotas.

The ledger enforces charges supplied by adapters. The word adapter declares
conservative model charges of 512 bytes per store, 800 per directory node, and
768 per page, including an allowance for its allocation descriptor. It is not an
automatic heap tracer. Budget control/temporary objects, real allocator headers,
GC retention, and every physical backing allocation are not exhaustively
instrumented in this slice. Therefore passing these checks does **not** establish
the full 8 MiB qualification gate, physical memory bounds, or an optimization
speedup. A packed native storage adapter and complete accounting remain work
before that claim can be made.

`release()` is an accounting operation: its caller must end backing ownership
first. The managed adapter drops its store roots at disposal; runtime garbage can
remain until collection. `abandon()` requires the caller to discard an entire
failed child attempt first; request allocation traffic/work survive retries. It
does not pretend to physically free arbitrary storage or replace the allocator.
Transfer only supports same-kind siblings in one request, so function storage
cannot be transferred into the shared-metadata kind to evade its function gate.

Owner states are active/failed/cancelled/closed (0/1/2/3). Reservation handles are
pending/committed/cancelled; allocations are live/released. These are compiler
data invariants and are not a sandbox against a malicious compiler pass that
directly corrupts public record fields. A future independent verifier must read
the actual records and reject malformed IR rather than trust builder state.

## Validation

Run the focused batch from the repository root:

```sh
python -m unittest discover -s tests -p test_u1_foundation.py -v
```

Four tests cover the Eristavi protocol probe, selected profile factories, nominal
ID rejection, and the Eristavi compiler's emitted probe linked independently with
the bootstrap and owned runtimes. The native owned check requires Linux x86-64
and GNU development tools; it audits no dynamic interpreter/section, no undefined
imports, and non-executable stack, then runs with an unusable PATH.

The probe has 24 expected scenario labels: pending-versus-live capacity, rollback,
parent/traffic admission, transfers and failed transfers, single-use handles,
prepaid work/request retry history, cancellation, abandonment, signed counter
boundary, page boundaries, canonical metadata and hash collisions, invalid source
spans/revisions, construction freeze, loop argument order, foreign ValueIds, edge
validation, and cleanup after partial construction exhausts its budget.

This tests construction and accounting, not execution of the new UIR. The native
code runs the Eristavi builder/test implementation through the existing compiler.
The edge swap test checks the stored parallel argument mapping; it does not yet
qualify a new backend's parallel-copy resolver.

No self-build, new 900-second run, full qualification, or workflow dispatch is part
of this slice. Expensive qualification stays at the later integration gate.

## Next boundary

The subsequent isolated verifier slice is recorded in UIR_U1A_VERIFIER.md. It
adds structural/type/span and reachable SSA checking for this operation subset;
its report grants no publication privilege. UIR_U1A_PROMOTION.md adds initialized
scalar cells and mandatory promotion. Complete operation semantics and
strict Float cases, checked record decoding, source-map/origin-chain validation,
and matched candidate fixtures before qualifying U1a. The construction marker is
not a substitute for those checks. Retain the existing compiler until U2/U3
integration and conformance succeed.
