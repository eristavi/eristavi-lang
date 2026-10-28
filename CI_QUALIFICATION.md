# CI and completed-batch qualification

The frozen language design and runtime contracts are unchanged. Ordinary CI runs
Python compilation and the complete test suite on Linux x86-64 GCC/Clang, Linux
ARM64 Clang and macOS Clang. Native runtime/application tests remain in that suite.
Repeated compiler self-builds and offline packaging are separate, explicit gates.

## Select the required evidence

| Change | Qualification before merge |
| --- | --- |
| Owned x86-64 runtime implementation only | Normal CI plus owned integration |
| Compiler, code generation, bootstrap C runtime, common packaging or startup | Normal CI plus full qualification |
| Release or promotion of a runtime profile | Full qualification and that profile's explicit repeatability evidence |
| Documentation without implementation changes | Normal CI |

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

Ordinary CI uses the standard unittest suite with a JSON outcome report and retains
its raw test log. Platform-specific skips remain visible. See
[BUILD_DIAGNOSTICS.md](BUILD_DIAGNOSTICS.md) for artifact interpretation and limits.
