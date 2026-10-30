# CI and completed-batch qualification

The frozen language design and runtime contracts are unchanged. Incremental
implementation PRs receive a **focused Linux Clang smoke suite**, not four
complete native builds. Documentation-only PRs receive a Git patch check.
The full CI profile still runs the **unchanged full test suite** on Linux
x86-64 GCC/Clang, Linux ARM64 Clang and macOS Clang, including native
runtime/application tests, but only at explicitly selected final gates.
Repeated compiler self-builds and offline packaging are separate gates.

## Select the required evidence

| Change | Qualification before merge |
| --- | --- |
| Owned x86-64 runtime implementation only | Full four-platform CI plus owned integration |
| Compiler, code generation, bootstrap C runtime, common packaging or startup | Full four-platform CI plus full qualification |
| Release or promotion of a runtime profile | Full four-platform CI, full qualification and that profile's explicit repeatability evidence |
| Documentation without implementation changes | Lightweight PR patch check (no compiler or full matrix) |
| Incremental implementation edits | One-platform smoke CI plus change-specific developer tests; not a merge gate |

Select a profile once the implementation batch is complete. Do not run expensive
qualification after each helper. Existing qualified evidence can be reused only
when the relevant implementation and toolchain inputs are unchanged.

- Add the `owned-qualification` label to a completed PR to run the static owned
  compiler/application bundle and offline audit on Linux x86-64 Clang.
- Add the `qualification` label to run both owned integration and repeated
  bootstrap self-build/offline audits on all three Linux configurations.
- The **Eristavi qualification** workflow also offers **Run workflow**, with
  `full`, `owned-integration` or `owned-self-build`, for an explicitly selected branch/ref.

Qualification does not run on ordinary pushes, PR synchronization or main merges.
A label qualifies the source revision present when it is added. If relevant code
changes afterward, remove and re-add the label when the next batch is ready, or
manually run the workflow on the new ref. Require successful normal CI and the
selected qualification jobs for the final revision before merging. A skipped job
or an earlier green revision is not qualification evidence. These are review
requirements; the workflow does not install repository branch-protection rules.

The `owned` job uses `--runtime owned --skip-self-build`. It runs the static-link,
startup and offline application audit and records `repeatable: false`. It does
**not** qualify repeated owned compiler self-builds or promote the owned runtime
to default. Full qualification retains the three Linux bootstrap gates that passed
CI #379; those gates are selected explicitly instead of repeating during each
edit or on the resulting main merge.

## Diagnostic evidence and the explicit owned self-build gate

All qualification commands use `--trace-phases` and retain per-command stdout,
stderr, phase events, partial emissions, input hashes and qualification status.
Build stdout/stderr is also tee'd with shell pipe-failure propagation. Evidence is
uploaded with `if: always()` and 14-day retention even if a build step fails. The
job summary states repeatability and offline-audit status separately. An interrupted
job may retain `running` status; do not treat an incomplete record as a success.

The manually selected `owned-self-build` profile runs the owned compiler's full
B-to-C and C-to-D checks plus offline audit. It is independent of `full`, which
continues to qualify bootstrap self-builds and owned integration. Ordinary pushes
and PR synchronization trigger neither expensive profile. The default command
timeout is still 900 seconds; `--command-timeout` allows short diagnostic probes.

Both smoke and full CI use `tools/run_ci_tests.py`, with explicit
`--profile smoke` / `--profile full` modes and retained JSON outcome reports.
The full profile retains original unittest discovery and every original test;
its JSON report also records the slowest tests and durations. Full CI enables
`ERISTAVI_TEST_TIMING=1` for native U1 phase breakdown. Platform-specific
skips remain visible. See [BUILD_DIAGNOSTICS.md](BUILD_DIAGNOSTICS.md).

## Trigger policy: only test when useful

- **PR code opened, reopened or synchronized:** the patch is checked and
  a single Ubuntu Clang smoke suite runs. The developer should also run
  change-specific tests locally. This is not sufficient to merge a compiler
  implementation change.
- **PR changing only Markdown (.md/.mdx/.rst):** only changed-file
  classification and `git diff --check` run. No system compiler builds,
  platform matrix, or expensive self-builds.
- **Final compiler/runtime implementation revision:** explicitly run the
  complete four-platform CI matrix by marking a draft PR **Ready for review**,
  selecting **Actions > Eristavi CI > Run workflow > full** on the PR branch,
  or applying the `qualification` / `owned-qualification` label when the
  appropriate offline qualification is also needed. A qualification label
  triggers BOTH the explicit full CI matrix and the separate build jobs.
- **After any code changes to a qualified PR:** previous CI and offline
  results do not qualify the new source revision. For a new final run, mark
  draft/ready again or manually dispatch full CI on the new exact head;
  remove/reapply the qualification label, or dispatch that workflow manually
  when build inputs changed. Do not infer a rerun from a label that remained
  attached to the PR.
- **Main merge:** the full CI suite is not automatically run **again**.
  Verify exact tested PR head and resulting merged Git tree equality.
  Manual full CI remains available for regressions, releases and audits.
- **The `owned-self-build` profile is NOT part of ordinary smoke/full CI**
  and must continue to be selected explicitly. Previous 900-second owned
  compiler self-build timeouts are not evidence of a passing release.

## Why the Linux verifier test took so long

The full GitHub CI logs from 2026-10-30 show approximately **148 seconds
(GCC)** and **93 seconds (Clang)** elapsed at
`test_eristavi_emitted_verifier_and_oracle_on_both_runtimes`. These are
completion gaps in timestamped unittest output, not isolated compiler-only
phase measurements. The test builds the Eristavi frontend and owned-runtime
generator, emits two programs as assembly, assembles and links both owned
and native-C runtime paths and executes the independent verifier/oracle.

Previously the same frontend and runtime generator were independently
compiled with `-O2` in each of three U1 test classes (foundation, promotion,
verifier). Their test-only binaries are now cached *within one Python test
process only*, keyed by CC/CFLAGS, without retaining artifacts across jobs,
revisions or execution environments. Each actual test program, native-C and
owned link, source-origin verification, and runtime/output assertion still
executes independently. The full profile records the cold build and per-stage
costs so further optimizations can be based on measured evidence rather than
guessing or lengthening test timeouts.
