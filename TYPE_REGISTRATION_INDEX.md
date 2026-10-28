# Typed IR type-registration index

Status: review candidate. This change optimizes compiler-private typed-IR lowering only. It does not change Eristavi source semantics, public typed-IR layout, type numbering rules, verifier requirements, runtime behavior, or the public 32-byte value ABI.

## Motivation

A full-source lower-IR counter investigation on merged main after PR #52 measured the remaining typed-lowering lookup work while compiling `src/frontend.eri`:

- 51,139 type-registration calls;
- 3,521,042 linked `Program.types` node visits inside registrations;
- 31,785 existing-type hits;
- only 171 distinct non-builtin types;
- an average 110.18 linked nodes for each registration that had to search the table.

The same diagnostic measured 750,946 specialization/source-list visits and 30,282 local-binding visits. Type registration was therefore selected as the next bounded target. The counts are algorithmic evidence, not a compiler speedup claim.

## Implementation

`Program.types` remains the canonical public linked representation. The lowerer now owns a private reusable `ir_types.Registry` used only to locate an already-registered `(kind, name, inner)` key quickly.

The registry has 257 hash buckets. Bucket lookup uses a balanced integer tree; each bucket retains a short collision chain. Hash collisions are always resolved by exact equality of `kind`, `name`, and `inner`. No hash match is accepted as type identity.

The registry is seeded from an existing `Program.types` chain in tail-to-head order so that a duplicate legacy table, if present, keeps the same newest-first lookup priority as the previous linear scan. Its `nextIndex` is still derived by counting existing non-builtin type records from the legacy base index 6. New types are still prepended to `Program.types`, so public type IDs and list insertion order are unchanged.

Nominal types are inserted into the private registry immediately after the corresponding public `ir.Type` record is created and before recursive field lowering. This preserves the previous recursive/self-referential nominal-layout behavior. Field order, `checked` state, `std.files.FileError` handling, error payload layout, unresolved-type diagnostics, and recursive wrapper registration remain unchanged.

The existing `register()` and `failures()` entry points retain the legacy scan path for callers outside the lowering builder. The source lowerer alone carries one registry and calls `registerIndexed()` / `failuresIndexed()`.

## Correctness evidence

The candidate was first compared against unmodified merged main on the bootstrap runtime.

For `src/compiler/typed_ir.eri`:

- typed IR was byte-identical, SHA-256 `e66cae026247b7d05694cc12972490803782ec25e9eb68c7a799bdfe72f52afc`;
- x86-64 assembly was byte-identical, SHA-256 `172769263e830e6bb555926612972f8b807b8a6f9261e0ca88087165f135cfb7`.

For the full `src/frontend.eri` compiler source under the bootstrap runtime, baseline and candidate x86-64 assembly were byte-identical, SHA-256 `2a3c06c8e73aa7fd0bcff5ca4a20aa355f69047c7addb48f9ad7d2a0b1888dc0`.

Existing deterministic typed-IR and specialization-cache regression tests passed. A dedicated type-index regression additionally forces two nominal keys into the same private hash bucket and verifies exact collision handling, parity with the legacy lookup path, unchanged count-based next type index, unchanged public list-head insertion, and repeated cache hits.

## Bounded performance evidence

Bootstrap full-source timings were effectively flat (8.00 s baseline versus 7.92 s candidate in one pair). This is not treated as a speedup.

A serial owned-runtime ABBA measurement on `src/compiler/typed_ir.eri` also showed only a small movement:

- baseline wall median: 5.380 s;
- candidate wall median: 5.270 s;
- baseline user-CPU median: 4.035 s;
- candidate user-CPU median: 4.020 s.

All four typed-IR outputs were byte-identical. This small module does not exercise the full-source registration volume, so no general speedup is claimed from it.

The scale-sensitive check used one 300-second candidate-only full-source trajectory because the preserved baseline compiler hash already matched the exact post-PR-#52 baseline. Both runs consumed the same merged-main source and the same command shape.

At the 300-second cap:

- baseline: 104 `lower-function` begins, 103 completed functions;
- candidate: 122 begins, 121 completed functions;
- the candidate's first 104 lowering subjects exactly matched the baseline prefix;
- candidate therefore completed 18 additional functions before the same cap;
- the candidate still remained inside typed-IR lowering and did not reach typed-IR verification or Universal IR lowering.

This establishes a materially better full-source lowering trajectory for the owned runtime. It is **not** a 17.5% compiler or wall-time speedup claim: both observations are censored at 300 seconds and individual function costs are not uniform.

## Qualification boundary

This is compiler/common-source work, not a runtime-only change. Before merge it requires the normal four-platform CI gate and full qualification. The evidence does not yet justify a 900-second owned self-build: full-source lowering still fails to complete inside the 300-second trajectory probe, so the next lowering bottleneck should be addressed first.
