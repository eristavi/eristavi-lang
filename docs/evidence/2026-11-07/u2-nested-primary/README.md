# Nested File primary propagation — verified development checkpoint

Date: 7 November 2026 (Asia/Nicosia). Branch
`compiler/u2-nested-primary-20261107`, intended for
`compiler/u2-whole-function-file-roots-20261107` (draft PR #121),
which targets draft #111. U2 issue #74 stays OPEN.

## Exact source and validation

- Implementation/tests commit:
  `1f1b44b3f74d11d5e95e0d85f0c0ac9277ef9e8b`.
- [Focused GitHub CI #42412553696](https://github.com/eristavi/eristavi-lang/actions/runs/42412553696):
  **4/4 PASS, zero failures and zero skips, 51.138 seconds**;
  hosted Linux x86-64 Clang.
- [Earlier three-method focused CI #42412420675](https://github.com/eristavi/eristavi-lang/actions/runs/42412420675):
  **3/3 PASS, 48.622 seconds** on precursor `c20efa9c`.
- Workflow: `.github/workflows/u2-nested-primary-focused.yml`.
  It runs only bounded native execution and binding-refusal probes,
  not full owned-generator self-builds or four-platform qualification.

## What the new executable probe proves

`tests/fixtures/u2_function_file_nested_primary.eri` builds one
*original canonical Function*, not a separately interpreted cleanup
program. It acquires an outer File followed by an inner File. Both
owners have independent lexical scopes and live class-1 roots. Inner
File.close normal/failure edges consume and poison the inner owner
while carrying the original outer owner into its next block.

The inner-close-failed edge carries its original class-5 context
as the primary to an exact three-parameter source
`[FailureContext, outer File, pending i64]`. Only the outer File is
still owned at that point. An independently checked `PrimaryBinding`
authorizes the one remaining File.close in already-failing mode.
The existing native runtime appends a newly failed outer close as a
secondary, retaining the original primary object and its typed edge
semantics. No additional executable IR, cleanup runtime, or public
32-byte ABI change was introduced.

The primary execution method checks:
- Both acquisitions and both closes succeed, returning pending 42
  with zero live File resources.
- Failed *inner acquisition* recovers after closing the surviving
  outer File and returns 7.
- Failed *outer acquisition* propagates a typed checked error without
  a resource close.
- Failed inner and outer closes produce an original FileError plus
  one secondary after two closes, with final zero open resources.
  The generated code runs with forced GC at original block safepoints.

The negative method mutates the failed-entry Plan mode and the
continuation revision; each must refuse before any assembly is
emitted, with no retained-plan leak. The preexisting single-owner
primary composition and nested recovering-handler native regression
remain green.

## Limits

The general Function has a maximum verified lexical depth of two,
but the *bound primary* close still has exactly one surviving
File owner. The proof explicitly refuses arbitrary unbound failure
propagation or simultaneous multiple owning closers with an active
primary. Multiple chained, currently failing lexical owners still
require their own source-bound proof/implementation. Broad managed
aggregate/List and new failure construction, cross-platform/owned
parity, independent source origin, allocator/physical/sanitizer
evidence, main reconciliation and final release qualification
are separate unfulfilled U2 gates. Do not merge or close #74
based on this focused result.
