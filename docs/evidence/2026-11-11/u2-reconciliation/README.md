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

Pending the branch-only focused job. Record the run ID, exact tested commit,
pass/fail/skip counts and any remaining refusals after completion; do not
promote historical results to new-source acceptance.

## Still open

Mixed owning/non-owning group bindings with a producing sibling;
active primary across an owning defined call; remaining managed field
and identity composition; carrier overlap; hostile roots and physical/
sanitizer/fault/independent comparison evidence; final four-platform and
completed-batch qualification. #74 stays open; #111/#121 stay draft.
No full owned compiler self-build or broad CI.
