# Current six-step runtime migration

This checklist describes the remaining C value-runtime migration after PR #30.
It records implementation boundaries; adding a primitive or test is not completion
of the corresponding language-value subsystem. All target work currently concerns
Linux/System-V x86-64. The bootstrap generator still uses the existing C runtime.

| Step | Current batch | Remaining acceptance boundary |
| --- | --- | --- |
| 1. Text performance | Indexed backing lookup; snapshot-safe append capacity; geometric growth | Automatic qualification of this batch; independent small-buffer allocation remains unpooled |
| 2. Float | Strict binary64 arithmetic, comparisons and sign negation primitives | Correct decimal input/output; value ABI dispatch and lifetime integration; end-to-end fixtures |
| 3. Objects and Lists | Existing C ABI and operations inventoried | Typed backing ownership; construction and initialization; copy/detach; member/index/ref; append; equality; transitive tracing |
| 4. `maybe` and identity | Existing wrapper/alias ABI inventoried | None/present operations; optional detach; shared identity updates; alias equality; cyclic graph marking |
| 5. Checked failures | Existing native helper contracts inventoried | Handler frames and context transfer; saved payload ownership; typed matches; unwind roots; primary/secondary propagation |
| 6. Resources and OS services | Existing cleanup and file contracts inventoried | File/process syscall boundary; exactly-once reverse cleanup; failure composition; compiler-required services |

Steps 3 and 4 require a common nonmoving typed heap tracer before constructors can
safely publish nested values. The existing Text collector follows slots to backing
buffers only. Enabling aggregates in its tag dispatch without tracing every nested
edge would prematurely free live Text. Root maps can also contain interior values,
failures and resources; the present Text profile intentionally does not enable them.

The existing `ev_value` layout is 32 bytes. Objects hold a count and a pointer to
32-byte cells. Value updates detach aggregate backing. Identity uses a shared wrapper
cell; updates detach the contained value while preserving the wrapper alias.
`maybe` uses absent null backing or a one-cell wrapper. Ordinary identity equality
compares wrapper identity; aggregate equality follows values. These contracts must
be carried over, with all cycles marked before descent and no recursive sweep.

Checked failures and resources cannot be enabled by implementing only `evn_fail` or
Linux `close`. Native handler frames preserve slot/scope boundaries. Active and saved
failures own typed payloads and secondary contexts; all remain collector roots.
Cleanup preserves the original primary failure, attaches secondary failures in
reverse acquisition order, cancels a successful return on cleanup failure, and runs
exactly once. `RESOURCE_CLEANUP.md` remains authoritative.

Publish related implementation in one coherent batch. Keep automatic GitHub CI and
all platform/self-build gates enabled. Do not dispatch or rerun expensive workflows
for each helper. Qualification claims require completed results for the exact source
head, followed by a merge with that head as the expected revision.
