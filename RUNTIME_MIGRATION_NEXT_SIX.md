# Current six-step runtime migration

This checklist records the owned Linux/System-V x86-64 value-runtime migration after
PR #35. Implemented helpers and focused checks do not replace full CI qualification.
The bootstrap compiler/generators still use the broad C runtime.

| Step | Current implementation | Remaining acceptance boundary |
| --- | --- | --- |
| 1. Text performance | Indexed backing lookup, immutable prefix capacity and geometric growth qualified in PR #32 | Independent small-buffer allocation remains unpooled |
| 2. Float | Arithmetic, decimal parsing/output, values and scope integration qualified in PR #34 | Further throughput optimization remains optional performance work |
| 3. Objects and Lists | Owned storage, construction, initialization, copy/detach, member/index/ref, append, equality and transitive tracing implemented; focused checks pass | Qualified in PR #35; prefix-append performance follow-up |
| 4. `maybe` and identity | None/present operations, optional detach, shared aliases, equality and cyclic graph marking implemented; focused checks pass | Qualified in PR #35 |
| 5. Checked failures | Owned handler contexts, stable payload/message snapshots, typed/catch-all matching, propagation and slot/scope unwind implemented; focused checks pass | Ordinary failures qualified in PR #35; resource/secondary contexts implemented in the next batch |
| 6. Resources and OS services | Owned file operations, process arguments/output/status, exactly-once reverse cleanup and primary/secondary composition implemented; focused qualification | Automatic full CI for the combined resource batch; Linux canonical paths currently require mounted procfs |

The common owned graph tracer now marks complete value slots, validated interior
cells, current/saved failures and protected pending results. Active scope/handler
administration remains explicitly owned; handler slot marks are pinned during
pruning. An intrusive work list marks before enqueueing, preserving cycles without
recursive traversal or allocation during marking. The separate resource profile adds explicit open-handle roots and secondary cleanup
contexts. See
`OWNED_GRAPH_RUNTIME.md` for layouts, validation and performance limits.

The next acceptance boundary is full CI qualification of the resource batch,
followed by default build/startup integration and compiler workload performance.
Only then can the compiler rebuild on the owned runtime and proceed to removing
required Python tooling, native instruction/object output, linking and additional independent platforms. The current List append and
interior-owner lookup costs must also be assessed before large compiler workloads.

Batch related implementation before publishing a PR. Keep automatic GitHub CI and
all platform/self-build gates enabled. Do not dispatch or rerun expensive workflows
for each helper. Merge only the exact fully qualified source head.
