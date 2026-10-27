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
  `full` or `owned-integration`, for an explicitly selected branch/ref.

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
