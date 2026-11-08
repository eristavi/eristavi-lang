# U2 multi-owner active-primary prefixes — 8 November 2026

Verified implementation/test checkpoint: `c25498fc715b6d954747644f36447dc414e08d44`.
This documentation successor leaves compiler/test inputs unchanged.


Base branch head: `97630a1227dec9846f258716d35e023cd8cb6b7a`.
Issue #74 remains OPEN; drafts #121/#111 unmerged. This is development evidence.

Implemented up to eight explicit primary-bound closes over the original canonical
Function, with lexical prefixes of up to eight owners. `verifyPrimary` checks
all source owners, failed-mode one-close Plan with surviving depth minus one,
unchanged primary/pending and every surviving owner on both outcomes. Multiple
bindings cannot duplicate instructions or substitute the innermost obligation.
No new executable IR, resource adapter, collector or public ABI.

Efficiency: privately build at most eight request nodes and a dense table only
for bound Functions. Instruction emission uses O(1) primary lookup; ordinary
Functions allocate neither structure. Each binding still pays fresh full owner,
root, continuation and cleanup-plan verification. No cached proof or widened
watchdog. No timing speedup, physical memory or paired-benchmark claim.

## Observed verification

| Log | Outcome |
| --- | --- |
| focused.log | 10 methods / 9 passes / 1 ERROR / 0 skips, 63.885 s. Error was a shared test generator directory name causing FileExistsError before generation of the second fixture. |
| final-additional.log | Corrected new primary-chain method plus closed/mixed-group execution and nine malformed group metadata probes: 3/3 PASS, 47.275 s. Existing pointer-qualifier warnings retained. |
| combined-final.log | Corrected original + two-owner primary cases in the same test class: 2/2 PASS, 11.262 s. Confirms directory collision resolved. |

Together the successful method outcomes cover twelve distinct methods; this is
not a single 12-test green suite run. The code is the same across these runs;
only the test temporary directory name was corrected between them. No tests,
assertions or timeouts were weakened. Python compilation and full patch check
pass. inputs.sha256 pins changed code/test inputs.

The new canonical fixture acquires two real Files with an existing primary,
closes the inner while retaining the outer, then closes the outer on both
outcomes. Four executions cover clean/failing closes and absent/existing prior
secondary. Test-only runtime instrumentation records actual resource objects
at acquisition and checks exact reverse record order at each close and exactly
two closes. Forced GC, primary identity, ordered linked secondary count and
complete resource/failure/graph/Text/handler reclamation are asserted. Duplicate
binding, missing bound site and wrong surviving prefix refuse before output.
Original one-owner, nested-primary/recovering handler, prefix/dispatch,
checked-recursion and group metadata/execution checks remain passing.

Earlier development attempts encountered restored-environment missing Python
dependencies, the bootstrap's generic empty-list specialization restriction,
a local no-shadowing name collision, and incorrectly ordered owner-signature
fixture registration. These were corrected before retained final verification.
The bounded private linked request representation avoids the generic-list issue.

## Remaining / exact next work

Finish primary-bound propagation across File-owning checked recursive/group
calls; non-i64/nested List/aggregate and typed failure constructors; broader
hostile-root/allocator/sanitizer/physical and independent source-origin evidence.
Latest owned/C generator parity and four-platform/full completed-batch gates
are pending. Prior hosted smoke #42410196267 had three 120 s generator timeouts;
no fix or green latest owned evidence is claimed here. No broad/full/self-build
CI or paused #51 work manually initiated. Any automatic hosted run after publish
must be checked independently. Keep #74 OPEN and PRs draft.
