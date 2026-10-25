# Preflight and qualification

Draft pull requests run `python tools/preflight.py` in one Linux job. This checks
reference behavior, inferred contracts, interfaces, collection IR, evaluation
order and focused C runtime accounting/collection cases. It does not rebuild the
compiler through B/C or claim cross-platform qualification.

Marking a pull request ready triggers `ready_for_review`. Ready PRs and main pushes
first run `python tools/preflight.py --qualify`; only a successful preflight may
start the four-platform full regression matrix and Linux repeated native
self-build/offline gates. Converting back to draft triggers cancellation of a
superseded run, as does pushing another revision to the same branch.

Changes should be reviewed and batched locally before publishing one revision.
Dependency installation retries transient download failures before abandoning a
job. Infrastructure failures should be retried individually once the run ends;
successful native self-build jobs do not need to be repeated.

## Collection integration status

The collection candidate includes the native collector from PR #17. Its new
Map/Bytes reference execution and typed-IR tests are not evidence that those
values are supported by the offline code generators.

The review found and fixes duplicate evaluation in index/member/reference
fallbacks, missing Map interface serialization, and missing Bytes parameter
context across imported interfaces. Unimplemented collection backends now return
source diagnostics instead of internal Python errors.

Full qualification remains blocked by unfinished Map/Bytes C emission, Universal
IR operations, native consumers, runtime representations and corresponding GC
layouts. The qualification preflight intentionally fails on small Map/Bytes
programs until those boundaries are implemented. It never starts a self-build to
rediscover these known gaps. Default draft preflight can pass while these
capabilities remain explicitly experimental.

Before making this feature ready, finish those layers, add forced-collection
tests for Map keys/values and Bytes storage, exercise both families through the
Eristavi-written compiler, and extend the offline execution audit. Reconcile
GRAMMAR.md, LANGUAGE_SEMANTICS.md, OUTPUT.md, interfaces and editor metadata with
the collection decision. The agreed literal forms and frozen resource, identity,
checked-error and mutability rules must not be redesigned during integration.
