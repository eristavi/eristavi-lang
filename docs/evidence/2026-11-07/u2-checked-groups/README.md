# U2 checked Function groups — evidence and limits

7 November 2026. Development batch; #111 remains draft and #74 remains open.
Implementation `5dcc85f69ac458f83730957a9defd4b2fa3d0d7e`; corrected test checkpoint
`43d56f2f526fd57db5d790413217de439858b7a5`. Exact input hashes: [inputs](inputs.md).
Logs are fenced Markdown; terminal trailing whitespace is normalized for patch
hygiene, with diagnostic text/timings preserved.

## What changed

The existing whole-Function emitter admits a closed set of exact metadata-bound
checked bodies. Opcode 46 resolves to that member's label rather than always
calling the current Function. Different normal signatures, mutual recursion,
normal/failure edge transport and existing class-1/class-5 root handoff reuse
original canonical UIR, SSA and owned runtime paths. Native frame ABI is unchanged.

At most 16 members, 1024 total SSA values and 2048 total instructions; existing
per-body limits remain (8 inputs, 2 normal results, 64 roots, 64 blocks, 256
values, 512 instructions). The initial profile still needs the caller's one exact
saved-context failure carrier. These are explicit admission limits, not a general
whole-language acceptance claim.

All members undergo canonical/root/target/native admission before output. Private
immutable SSA Plans remain charged to their function owners during this bounded
transaction. Full independent `ssa.verifyPublications` freshly rederives/compares
each Plan before its body's output. All retained Plans/phases close on completion
or refusal, including failure while preparing a later member. Failed generators'
partial stdout is never an accepted compiler artifact. No cached verified flag,
new IR layer, global call table, default compiler change or public ABI promotion.

## Verification

| Check | Result / scope |
| --- | --- |
| Final exact-source hosted focused suite | **29/29 PASS**, 651.252 s, `43d56f2`, [run #42349932276](https://github.com/eristavi/eristavi-lang/actions/runs/42349932276); word-path prerequisite **1/1 PASS**. [Raw log](hosted-focused-pass.log.md). Legacy owned generator 103.728 s, new group generator 101.624 s, both under unchanged 120 s. |
| Final exact-source hosted Linux smoke | **170 run / 167 pass / 0 fail / 3 intentional opt-in skips**, 850.922 s, `43d56f2`, [run #42349932257](https://github.com/eristavi/eristavi-lang/actions/runs/42349932257). Scope/patch SUCCESS; full matrix SKIPPED. [Raw log](hosted-smoke-pass.log.md). Both generators again pass (legacy 78.363 s, group 74.805 s). |
| Previous hosted checkpoint `6635e8e` | 28/29 methods pass; remaining failure was missing bootstrap `checkEdge` specialization in direct comparison fixture. Owned group generator itself passed in 62.882 s; legacy generator 76.004 s, both under 120 s. [Raw log](hosted-28-pass-fixture-specialization-failure.log.md). |
| Local normal focused suite | 10/11 methods pass; owned generator hits the unchanged 120 s watchdog. The unchanged prior `6fe0024` baseline also times out on this host. [Group](local-group-10-pass-watchdog-open.log.md), [baseline](unchanged-baseline-local-watchdog.log.md). |
| Bootstrap C ASan + UBSan | 4/4 focused methods pass, 84.670 s, `-O0`, `detect_leaks=0`, halt-on-error. [Log](local-bootstrap-asan-ubsan.log.md). |
| Corrected direct C generator ASan + UBSan | Pass; 17,007 emitted bytes. [Log and assembly hash](local-direct-bootstrap-asan-ubsan.log.md). |
| Retained-plan refusal / List execution | 2/2 targeted methods pass. Later-member work/capacity refusal restores all owners' live/pending backing; List snapshot and native reclamation checks pass. [Log](local-retained-plan-and-list-checks.log.md). |

The new 11-method suite executes mutual depths 0/1/5/32/64; checked success/failure,
recovery in a different member, swapped scalar/managed result positions, two
managed results, List snapshot independence, primary plus two ordered secondary
contexts, missing sibling handoffs and 14 malformed/missing/foreign/dead target,
label, type, count and origin variants. A frozen mutual source fixture independently
compares Stage-0 and existing C-native output with new native execution. Actual
native collector calls, post-scope Text/graph/failure reclamation and allocator
release checks remain active.

The direct generator fixture preserves an unreachable scalar `build.jump` edge
needed by the existing bootstrap's concrete specialization. C compilation runs
before the expensive owned generator so fixture analysis failures fail fast. Both
generators must run and emit byte-identical assembly; static ELF/no-loader/no
undefined symbols/non-executable stack and native normal/failure execution remain
required. No timeout was increased, no negative/legacy test removed, no test skipped
to obtain a passing gate.

## Physical scope and performance limits

Test-only native stack watermark observations for the mutual fixture:

| Depth | Generated Function frame bytes at deepest entry |
| --- | ---: |
| 0 | 592 |
| 1 | 1,184 |
| 5 | 3,552 |
| 32 | 19,536 |
| 64 | 38,480 |

The independent admission-cap bound is 2,896 bytes per active Function frame.
These measurements exclude transient runtime/collector helper frames and are not
process RSS, total allocator capacity/traffic or GC-pause measurements. Owner
refusal assertions measure existing charged backing; they do not replace actual
allocator attribution. Native reclamation checks are actual owned-runtime probes.
ASan/UBSan instrument bootstrap C programs, not emitted assembly. No passing LSan
or general owned-assembly sanitizer claim is made.

Early implementations rebuilt full Plans and unused publication products. The
recorded diagnostic identified repeated Plan work, leading to bounded Plan reuse
with unchanged independent emission proof. [Earlier diagnostic](earlier-redundant-plan-diagnostic.log.md),
[retained-plan local diagnostic](retained-plan-local-diagnostic.log.md),
[SSA diagnostic](local-ssa-phase-diagnostic.log.md), [temporary patch](ssa-diagnostic.patch.md).
Diagnostic comments perturb timing; no whole-compiler speedup is established.
Retaining Plans raises temporary peak versus closing each immediately; existing
per-owner/common-request peak, traffic and work budgets remain mandatory.
Optimization investigation #51 stays paused.

## Still required for U2 acceptance

General File acquisition/consumption/owner cleanup on all original Function exits;
remaining call combinations outside this profile; nested managed constructors and
aggregate copies; new typed FailureContext construction; combined bad-root/owner/
allocator-fault and broad independent source-origin evidence; deep physical RSS,
traffic, GC-pause and sanitizer qualification. Reconcile main, then qualify one
coherent final revision on four platforms plus completed-batch gates before merge
or closing #74. No full owned-compiler self-build was performed or authorized here.
