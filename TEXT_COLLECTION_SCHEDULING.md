# Schedule Text tracing after reference-graph changes

Status: Linux x86-64 review candidate; automatic CI qualification pending.

Protected allocation safe points and the existing bounded slot threshold remain.
They now run the full Text heap trace only after a relevant graph change: removal
of slots during root-map pruning, scope restoration, or replacement of an existing
Text/view value through `evn_store`. Scalar-only stores and insertion of a fully
constructed result do not make a previously reachable Text buffer unreachable.

A private dirty word records these changes. Collection clears it only after a
successful full trace/sweep. Explicit `erist_rt_text_collect` calls still force a
trace. Every existing pending-result/root/mark guarantee remains in force; scalar
runtime composition remains unchanged. View and NFC compositions share the same
scheduler, so their backing and scratch lifetime regressions also cover it.

The hosted deterministic regression checks 10,000 scalar allocations plus stores
with a retained Text value: bounded slots and no more than 100 heap traces. It also
replaces the last reference to a Text buffer below the pruning threshold and checks
that the next scalar safe point releases the orphan; scope exit returns tracked
Text storage to zero. Collection counts are private probe data, not a public API or
a wall-clock performance claim. No tests were manually run; automatic CI qualifies.

This removes redundant tracing work. Registry lookup, page-per-buffer allocation,
and broader collector/value-family optimization remain future performance work.
No public syntax, semantics, ownership behavior or Unicode rules change.
