# U1a scalar-cell promotion

This isolated slice depends on verifier PR #59, including its C-bootstrap
checked-failure recovery fix at `c2989f169f6c470f95c11cec2ec5368bd333a485`.
It implements the agreed initialized-cell, pruned dominance-frontier and SSA
renaming algorithm. The production frontend/driver still uses the old pipeline.

## Construction and verification

`u1_builder.eri` now owns a separate cell table: scalar TypeId plus the unique
initializer InstId. `CellId` is nominal and function-owned, distinct from
ValueId. Cells contain only pred/i64/f64; they have no address, identity visible
to a generated program, managed reference, resource or escape operation.

| Private operation | Meaning |
| --- | --- |
| 10: cell.init | One exact-type operand, one declared initializer, no result |
| 11: cell.read | No ordinary operand; one fresh SSA result of the cell type |
| 12: cell.write | One exact-type operand, no result |

These are internal operation IDs, not a frozen public format. All three carry
the existing location ID and a checked CellId attribute. There is no uninitialized
value, fake Void result, memory address or implicit mutable-register fallback.

`verify.construction` independently checks the complete construction form,
including every dead block and every initializer declaration. In the reachable
CFG, initialization must dominate every read/write and precede accesses in the
same block. The initializer's SSA operand must itself be available. Loop-local
initialization retains its execution point and resets the cell each iteration.

`verify.verify` is the canonical gate: the same structural/SSA checks plus
rejection of every remaining cell. Neither builder completion nor an earlier
report authorizes bypassing verification. No executable publication path or
trusted serialized stamp is introduced.

## Promotion transaction

1. Independently verify input construction before dropping any dead component.
2. Compute iterative simple Lengauer–Tarjan dominators and one dominance-frontier
   index. Index cell accesses once in block/instruction order.
3. For each cell, identify local definitions and upward-exposed reads. Propagate
   live-in states through predecessor edges, stopping at definitions. Generation
   marks admit each cell/block state only once.
4. Place parameters at the pruned iterated frontier. Process cells in ID order;
   preserve existing parameter order and append new cell parameters in that
   deterministic order. Separate edge records retain parallel-edge distinctions.
5. Walk the dominator tree with explicit enter/exit stacks and undo bindings.
   Replace reads with their current SSA values, capture incoming values at each
   source terminator, and restore bindings before traversing sibling subtrees.
6. Use substitutions and a dependency worklist to remove singleton trivial
   parameters, ignoring self-inputs. Simplification also handles pre-existing
   non-entry block parameters; entry parameters retain the function signature.
   This is not a general equivalence/SCC optimization for all redundant phis.
7. Compact the surviving substitution/parameter/edge plan; release obsolete
   liveness, frontier, undo and dependency data before building the output.
8. Rebuild a separate function with new owner-scoped IDs. Remove cell operations,
   remap every surviving definition/use, and preserve instruction order and
   locations. Release analysis scratch before independent canonical verification.
9. Return the cell-free output only after verification succeeds. Failure or
   cancellation discards private output/scratch and returns no ready result.

Input records remain unchanged on success or failure. The input and output share
only frozen metadata; each function has its own key and tables. No initializer,
arithmetic computation, guard, fault or effect is moved. Ordinary computations
remain even when the destination cell becomes unused. All edge arguments are
collected as simultaneous transfers, including loop swaps.

The promotion phase uses the existing 33,554,432-work quota; pre/post verification
use their own 16,777,216-work phases. Request work/traffic are cumulative across
attempts. Resource errors identify the promotion stage. The accounting still
models the safe page adapter; it is not a complete physical heap/GC accounting.

## Bounded analysis and storage lifetime

Cell accesses are indexed once. Per-cell analysis walks those indexed accesses
and marked CFG/frontier states, rather than repeatedly scanning all instructions.
Live-in/placement generation arrays are reused between cells; no dense C-by-B
table is allocated. Storage includes actual frontier/parameter/argument entries,
which can grow with graph structure. Global work/capacity/count guards remain
mandatory; total promotion is not claimed universally linear.

The verifier derives value coverage/uniqueness from checked definition ranges
and back-references. Instruction positions also serve as claim markers; edge
source slots mark claimed edges. Orphan instructions are rejected before their
unchecked result ranges can be followed. This avoids separate value, instruction
and edge claim arrays while retaining independent validation.

The dominator workspace has eleven physical words per block. Disjoint phases
reuse storage; this does not pack or narrow public IDs:

| Slot | DFS/LT | Later tree/promotion use |
| --- | --- | --- |
| 0/1/2 | Successor head / predecessor head / DFS number | Retained |
| 3 | DFS parent | Cleared, then tree child head |
| 4 | Semidominator | Promotion undo marker after dominance is complete |
| 5 | Ancestor | Tree sibling |
| 6 | Label | Tree entry interval |
| 7 | Immediate dominator | Retained |
| 8 | Bucket head | Tree exit interval |
| 9 | DFS cursor, then bucket link | Tree/rename cursor after LT |
| 10 | DFS-number-to-vertex map | Retained through immediate-dominator correction |

All LT uses finish before tree storage reuse. Dominance intervals are complete
before any promotion traversal reuses the remaining temporary slots. CFG and
dominator traversal remain iterative.

## Focused evidence

```sh
python3 -m unittest discover -s tests -p 'test_u1*.py' -v
python3 -m unittest discover -s tests -p 'test_c_failure_recovery.py' -v
```

The U1 batch passed ten tests locally, including both native runtime profiles.
Promotion captures 18 before/after IR pairs and independently evaluates 88 input
cases, comparing mathematical expected results and complete guard/fault/location
traces. Cases cover diamonds, loop-carried state, sequential joins, redundant
parameters, simultaneous swaps, repeated loop-local initialization, irreducible
loops, dead components, unused destinations with observable faults, i64 bounds
and exact f64 bit values. Float arithmetic execution is not claimed here.

Eight negative cases cover read-before-init, non-dominating/missing init, malformed
dead code, canonical rejection of cells, early quota exhaustion, deterministic
late-rebuild failure, and pre-admission cancellation. Late failure tests ensure
partial outputs are discarded without changing the input or resetting consumed
traffic. The expanded verifier protocol adds orphan/cycle regressions.

Bootstrap fixtures use eight additional independent verifications per result.
The selected modeled 8 MiB peak/64 MiB allocation-traffic gates remain unchanged.
All three scale points pass their exact inserted-parameter/edge counts:

| Family | N | Inserted parameters | Inserted arguments |
| --- | --- | --- | --- |
| Diamond | 8 / 32 / 128 | N | 2N |
| Bounded loop with extra local | 8 / 32 / 128 | N+1 | 2(N+1) |
| Sequential diamonds | 8 / 32 / 128 | N | 2N |

The 128-local sequential fixture initially exhausted modeled capacity. Retiring
dead scratch, compacting the rebuild plan, eliminating redundant claim arrays
and reusing dominator temporaries reduced its lifecycle peak to 8,206,560 bytes.
Its successful allocation traffic, including eight additional verifications,
is 19,524,768 bytes; promotion records 3,367,442 charged work units. No limit
was increased. Per-fixture values/source hashes are in
`UIR_U1A_PROMOTION_EVIDENCE.json`.

The fixtures are direct IR tests, not the original source-to-assembly U0 workloads
or a matched legacy/candidate timing experiment. Their modeled gates do not prove
physical-memory qualification. Native smoke tests run small diamonds/loops,
swaps and repeated initialization through Eristavi-emitted assembly linked with
bootstrap and owned runtimes, with one extra verification. They compare complete
snapshots and independent behavior; the owned ELF remains static/import-free
with a non-executable stack and runs with an unusable PATH.

Remaining: complete U1a operations/calls/switches/strict Float execution, source
maps/origin chains, publication/revision capabilities, full physical accounting,
matched large-stress/performance qualification, and frontend/native integration.
The earlier large owned-runtime timeout remains open. No new self-build,
900-second run, full compiler qualification, workflow or language/ABI/filesystem
change is part of this slice.
