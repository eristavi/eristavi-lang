# Owned-runtime allocation-failure qualification

Status: thirteen Text failure probes qualified in PR #33 across all four CI jobs
(with target-native probes on x86-64 Linux) and merged.
This is a bounded prerequisite for roadmap step 7, not complete collector integration.
The supported target is Linux/System-V x86-64 and the supported value heap is Text.

`tests/test_owned_runtime_allocation_failures.py` compiles the existing Text-runtime
generator once and instruments only the emitted test assembly. Production helpers,
allocator policy, source semantics and CI configuration are unchanged. Thirteen
independent static executable probes inject failures at these boundaries:

| Boundary | Required behavior |
| --- | --- |
| Text reservation fails | OOM fault, no record/value publication, no release of nonexistent storage |
| Text record allocation fails | Release unpublished mapping using its original exact pair; OOM fault |
| Allocator region reservation fails | Unwind unpublished Text mapping; OOM fault |
| Text slot allocation fails | Terminal OOM; published record remains internally consistent until process exit |
| Text copy fails after one store | Release unpublished mapping; internal fault |
| Empty Text slot allocation fails | OOM without creating a Text backing record |
| Invalid UTF-8 input | Reject before any allocation or reservation |
| Shared-capacity result slot fails | Keep shared mapping and old snapshot; terminal OOM |
| Shared-capacity copy fails after one store | Keep shared mapping, old bytes and published length; internal fault |
| Growth reservation fails | Keep both input snapshots and existing records; OOM |
| Growth record allocation fails | Release only the newly reserved output; OOM |
| Growth slot allocation fails | Preserve old snapshots and consistent new record/index; terminal OOM |
| Growth copy fails after one store | Release only unpublished output; internal fault |

The injected release ledger validates the exact original base/length for every
release during the failing operation. It rejects duplicate release, unknown pairs,
and release of either preexisting input. Exit checks also validate expected helper
call counts, registry membership/counts, old snapshot lengths and the append
high-water mark. An operation that unexpectedly returns, or violates ownership,
exits with a distinct failure status instead of passing as an expected runtime fault.
The existing harness still checks static ELF linkage, no imports/dynamic loader,
nonexecutable stack and execution without helper programs in PATH.

OOM and internal defects are terminal runtime faults, not checked `fails` values.
The tests do not require resumable execution after OOM or explicit teardown of an
already published heap on fatal process exit. They do require unpublished mappings
to be released on the existing cleanup paths and shared live storage never to be
released as if it were a failed private output.

PR #32 passed all four CI jobs and was merged before this follow-up batch. This
coverage joins the exact Float-formatting helper in one owned-runtime qualification
batch. No workflow dispatch, rerun, CI skip or workflow change
is part of this work. The focused command was
`python -m unittest discover -s tests -p test_owned_runtime_allocation_failures.py -v`
with the pinned project dependencies available. It passed one test containing all
thirteen subcases in 1.871 seconds. Python syntax and whitespace inspection also
passed. The full suite and self-build gate were not initiated for this branch.

The rest of step 7 requires typed aggregate backing, cycle-safe transitive tracing,
interior roots, handlers, current/saved/secondary failures and resource state. Those
families must be implemented and qualified before step 8's C-runtime-free compiler
self-build. Steps 9–12 remain subsequent milestones; this work does not implement
native packaging, instruction encoding, object output, a linker or additional OSes.
