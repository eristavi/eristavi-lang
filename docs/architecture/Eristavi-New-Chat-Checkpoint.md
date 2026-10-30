# Eristavi — current handover

Updated 30 October 2026. The full handover is now maintained on GitHub:

[Read HANDOVER.md](https://github.com/eristavi/eristavi-lang/blob/63297369fb7c41e9f13915f6102490f41ee9626a/HANDOVER.md)

Documentation PR: https://github.com/eristavi/eristavi-lang/pull/61 (open).

PR #59 and #60 are merged. The implementation checkpoint is main commit
`cd421d859e3372796e59ddf236944efc1b6aaddb`, tree
`c6a554e04c12d26c93650956709c5d57f1812ddf`.
Both PR heads passed four-job CI. Completed-batch qualification
[41018345033](https://github.com/eristavi/eristavi-lang/actions/runs/41018345033)
passed three bootstrap repeatability/offline gates plus owned integration.
Full owned-compiler repeatability remains unproven.

This supersedes the 28 October measurement-first checkpoint. Read the GitHub
handover before continuing. Next: remaining U1a operations/calls/switches/strict
Float, first auditing operation classification and CFG successor walkers.
The production frontend still uses its existing pipeline; the new IR is isolated.
