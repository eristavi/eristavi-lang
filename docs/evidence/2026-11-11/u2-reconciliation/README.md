# U2 PR #111 / #121 reconciliation — 11 November 2026

Source parent: `91feef0981c88032e14fbbf60afb0cb25dc99f44` (#121).
Imported private acquisition bridge originates from
`02e4c52ef00c1cbfda1ade6b2dd555bc62494aae` (#111).
The two original draft branches are intentionally unchanged.

## Change boundary

- Retain the entire whole-Function CFG, owning runtime, lexical File roots,
  aggregate bindings, failure chains and native cleanup implementation from #121.
- Bring over #111's independently verified opt-in File acquisition bridge,
  with its contract aligned to #121 using existing native import inspection:
  kind 2, effects 63, version 1, Text -> File, two-Text-field FileError.
- Extend the original bridge fixture and test with wrong-effects, wrong
  FailureContext shape, stale-revision and foreign root-map refusals.
- Preserve both CI smoke selections, and reconcile HANDOVER/architecture docs.
- Add a single branch-only focused workflow; do not trigger any broad test,
  full matrix or owned compiler self-build.

## Inherited evidence (not combined qualification)

- #111 Linux smoke: https://github.com/eristavi/eristavi-lang/actions/runs/42676542396
  (172 run / 169 passed / 3 intentional skips).
- #121 Linux smoke: https://github.com/eristavi/eristavi-lang/actions/runs/42519706400
  (230 run / 227 passed / 3 intentional skips).
- #121 source/test checkpoint `375c983fd6da7170463d2d726912bb27f59cbe22`;
  5/5 focused primary aggregate tests, existing logs at
  `docs/evidence/2026-11-08/u2-file-primary-values/`.
- #111 original 2/2 acquisition bridge focused tests documented at
  `docs/evidence/2026-11-09/u2-file-acquire/`, under its old, narrower
  effects-8 metadata; not a combined-branch pass.

## Reconciled exact-head evidence

**PASS, 13/13 focused tests, 0 failures, 0 skips (141.098 seconds).**
Verified branch source/test commit:
`0d572e0d885ddbf17afc958025c93358f6e08c48`
on Linux x86-64, with Clang C native backend and pinned Python dependencies.

- Workflow: https://github.com/eristavi/eristavi-lang/actions/runs/43022380412
- Focused job: https://github.com/eristavi/eristavi-lang/actions/runs/43022380412/job/130528483303
- Native test log artifact:
  https://github.com/eristavi/eristavi-lang/actions/runs/43022380412/artifacts/13855667515
- Exact runner summary: `Ran 13 tests in 141.098s` / `OK`.
  The workflow job and run both concluded **success**.

The original bridge acquisition success and absent-path failure retain
registered roots, forced GC, cleanup, and reclamation. Its original unknown
symbol test and new wrong-import-effects, wrong FailureContext field,
stale-revision and foreign root-map negative cases all passed. Whole-Function
focused acquisition and terminal-refusal tests passed, together with existing
File aggregate/primary, nested ordered failures and invalid-binding refusal
tests. The live-primary-across-owning-call *refusal* passed: this does **not**
mean that missing composition case has been implemented.

Generated C produced existing nested-pointer-qualifier Clang warnings in
some Function regressions; these remain unsuppressed and were not counted as
new failure evidence. The full 230-test smoke, four-platform qualification,
self-build and independent physical/sanitizer qualification were not run.
This is **only bounded focused reconciliation verification**.

## Still open

Mixed owning/non-owning group bindings with a producing sibling;
active primary across an owning defined call; remaining managed field
and identity composition; carrier overlap; hostile roots and physical/
sanitizer/fault/independent comparison evidence; final four-platform and
completed-batch qualification. #74 stays open; #111/#121 stay draft.
No full owned compiler self-build or broad CI.
