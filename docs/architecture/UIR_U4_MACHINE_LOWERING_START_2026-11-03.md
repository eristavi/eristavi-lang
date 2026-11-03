# U4 machine lowering — implementation boundary

Status: development plan, not implemented or qualified. Issue #102.

## Existing decisions

Typed canonical UIR is source-neutral and independently verified. Legalization selects a target profile and lowers per function into a target-specific machine representation. RevaSM is a peer target, not a mandatory intermediate. Preserve frozen 32-byte public ABI through private adapters and keep existing production backends intact.

## First independent implementation slice

1. Inventory U1 operation registry, existing x86-64 emitter, ABI helpers and machine code paths; do not fork a second semantic registry.
2. Define private target-legal machine operations for U1 scalar Int64/Bool/strict binary64, calls, returns, conditional branches and SSA block-parameter parallel moves. Reject unsupported operations with explicit target-legality diagnostics.
3. Implement deterministic instruction selection and register/stack placement with bounded liveness/work accounting; preserve callee/caller-save conventions, stack alignment, source LocId and overflow/fault behavior. Parallel-move cycles require correct resolution.
4. Exercise native execution against the independent canonical UIR interpreter and existing compiler for scalar CFG/loops/recursion. Measure compilation time, allocator traffic, owner peak and process RSS on identical inputs.
5. Keep checked failures, managed root maps and scoped resource lowering behind U2-accepted contracts. Never fake roots or suppress failure edges to claim a working backend.

## Integration gate

U2 root-safe-point/liveness and cleanup acceptance precede full managed machine execution; U3 source provenance and artifact manifests precede default pipeline migration. Do not close #102 or merge implementation without exact-head full CI and qualification. No experimental owned full self-build without explicit permission.

## Three-step development checkpoint

1. **Inspected:** `u1_ops.eri`, `u1_native.eri`, and the existing Python `x86_64_lowering_contracts.py`; the old Python x86 backend and U1 native C table adapter are not a qualified new-U1 machine backend.
2. **Implemented (isolated):** `compiler/erist/u4_parallel_moves.py` adds a private simultaneous block-parameter copy scheduler, including cycles using a nonaliasing scratch location. It is not wired into native instruction selection.
3. **Tests added (not yet independently confirmed):** `tests/test_u4_parallel_moves.py` includes chain/cycle, exhaustive small graph oracle and invalid input rejection. Await exact-head focused CI before claiming green.

Next: connect verified canonical U1 edge arguments to target machine locations and select a target-legal scalar instruction subset; U2 managed roots remain gated.
