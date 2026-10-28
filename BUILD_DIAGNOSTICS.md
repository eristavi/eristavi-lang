# Build and CI diagnostic evidence

The audit of PR #45 read all five complete job logs (2,937 lines): CI #395 and
owned integration #8. No recorded compiler/runtime failure was found. Every one
of the 420 discovered cases passed on at least one matching runner. But successful
subprocess output was suppressed, the owned job explicitly skipped compiler
self-build, no qualification artifacts were uploaded, and six inherited tests ran
duplicate coverage. A passing job was not evidence of owned B-to-C repeatability.

## Changes

- Bootstrap/direct compiler helpers forward both diagnostic streams even on
  success. Qualification streams stderr while keeping generated-code stdout
  separate, and saves both raw streams for each command.
- Native `--trace-phases` records identify read, lex, parse, indexing, project and
  module analysis, individual function analysis/lowering, Universal IR conversion
  and optimization, native function/descriptors emission and output. JSON-quoted
  subjects prevent filenames from corrupting event boundaries. See FRONTEND_TOOL.md.
- The qualification runner records timestamped stages/events, active nested compiler
  phases, command arguments/status, partial output, source/tooling input hashes,
  seed identity, comparison results and a final `qualification.json`, including on
  ordinary exceptions/timeouts. A host crash/job kill may leave `status: running`;
  that is incomplete evidence, never a pass. A timeout kills the command's process
  group and preserves captured data. Normal command timeout remains 900 seconds.
  Group termination is idempotent: macOS may reject another signal while the
  first shutdown is still being reaped. The timeout regression forces that race.
- Offline negative cases require their intended exit codes and diagnostics. A
  crash or unrelated nonzero exit can no longer masquerade as controlled rejection.
  The offline audit also exercises phase tracing without Python/C compilers in PATH.
- Ordinary CI retains raw test output and JSON outcomes, including every skip and
  its reason. Qualification retains logs/evidence even on step failure. Artifacts
  have attempt-specific names and 14-day retention; preserve important findings
  separately before that period expires.
- Action runtime versions are updated to Node-24-based v6 releases. Hosted runner
  versions seen in the audited logs meet their requirements. Actual job logs remain
  the authority on any remaining action/dependency deprecation warnings.
- Shared cache fixtures no longer inherit unrelated test methods, removing six
  duplicate executions without deleting their original coverage. CI's discovered
  case count and README now use the same interpretation.

## Reading results

`evidence/qualification.json` reports the runtime, requested self-build mode, current
stage, command, active phases, input snapshot status, comparisons, repeatability
and offline-audit result. `evidence/events.jsonl` retains elapsed times for stage,
command and compiler phase events. Each `evidence/commands/NNNN.json` identifies
its corresponding `.stdout` and `.stderr`. Completed `.s` files are published
only after a successful emission command; `.partial.s` and raw stdout may be
incomplete. Presence of an output file alone proves nothing.

The nested `evidence/offline-audit` journal includes expected-negative stages.
The audit runs in the builder process so each timed command owns and cleans up
its subprocess group directly. Audit commands honor a shorter requested build
timeout; cleanup or evidence-write errors preserve the original failure.
Those command records intentionally show failed commands, while the audit only
succeeds after checking the exact controlled failure and output preservation.
`self-build.json` records compiler reproducibility separately from the overall
qualification result; an offline audit failure still fails the qualification.

Choose the runtime/profile explicitly. The `full` workflow profile retains the
three Linux **bootstrap-runtime** self-build gates and owned integration. It does
not claim owned compiler repeatability. The separate, manually selected
`owned-self-build` profile attempts owned B-to-C/C-to-D comparisons and offline
verification, with phase tracing and artifacts. It is never an ordinary CI gate.
Do not rerun expensive qualification after every helper edit.

## Newly exposed relocation warning

Forwarding successful tool output revealed previously hidden x86-64 direct-backend
linker warnings: absolute GC descriptor pointers were emitted in `.rodata`, so
PIE links created `DT_TEXTREL`. Descriptors now use `.data.rel.ro` with relocation
permissions, then GNU_RELRO protection. The regression builds and executes a PIE
with `-z text` (text relocations forbidden), checks that `TEXTREL` is absent and
RELRO storage is present. The 31-case direct-backend follow-up passed without the
previous warnings. This does not change the owned runtime's public value ABI.

## Newly exposed C control-flow warnings

The first passing ARM64 CI log exposed `-Wreturn-type` warnings in generated C
for checked failures and resource handlers. Those paths terminate through
`longjmp` or process exit, but the C helper declarations did not describe that
contract. The bootstrap emitter now uses C11 `_Noreturn` for its fault, raise,
propagation and generated error helpers. No fallback value or warning suppression
is added. The six checked-error regressions require `-Werror=return-type`;
22 error/resource/text/diagnostic follow-up checks passed with that strict flag.

The passing GCC job also exposed 23 `-Wnonnull` warnings when it specialized
Text equality against empty storage. The existing short-circuit expression
excluded a byte comparison at zero length; an explicit early return when either
operand is empty now makes that condition clear to GCC. Both bootstrap Text
implementations retain the same byte comparison for nonempty equal lengths.
The real generator regression failed before the change with `-Werror=nonnull`
and passes afterward. Six focused checks passed with both warning categories
treated as errors, including empty/empty and empty/nonempty equality.

## Local validation and limits

The initial complete local run executed 422 cases: 410 passed, nine skipped, and
three sanitizer methods produced eight failure records because LeakSanitizer
could not inspect `/proc` in this execution environment. The skips were the four
ARM64-native cases and five cross-assembler checks because Clang is unavailable
locally. CI's sanitizer checks remain enabled and unchanged. A local ASan/UBSan-only
follow-up of those three methods passed with leak detection disabled for that
local probe; it is not LeakSanitizer qualification.

After the fixes, 31 direct-backend checks and nine diagnostic/packaging checks
passed (overlapping the full run), followed by traced/untraced equivalence across
all frontend modes and both native emitter targets, including Unicode separator
and newline filenames. A real two-second timeout probe using a freshly compiled
frontend retained `generate-owned-runtime` plus the active `universal-optimize`
phase, raw output and `status: timeout`, with an unchanged input snapshot. This
intentional timeout is diagnostic validation, not a compiler self-build attempt.
The final suite discovers 424 cases after adding the strict PIE and audit-cleanup
regressions and removing duplicate inherited executions. Normal CI and full bootstrap/owned
integration qualification remain required on the final revision.

## Remaining limits

Owned compiler self-build last exceeded 900 seconds on commit 810d76f, with no
completed compiler C. This batch adds the observability needed to locate its late
phase; it does not fix or explain that timeout by itself. Trace I/O affects timings.
The language philosophy, frozen semantics, automatic memory safety and deterministic
scoped cleanup remain unchanged. This audit covers the build/diagnostic paths and
reported warnings; it is not a proof that the entire repository has no defects.
