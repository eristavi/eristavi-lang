# Source specialization lookup index

This note records the evidence for replacing the typed-IR lowerer's repeated linked `Source` lookup with a compiler-private exact-key index. It is a bounded optimization result, not a whole-compiler speed claim.

## Measured target

The post-#52/#53 lowering investigation measured the existing specialization/source lookup path before this change:

- 3,195 specialization lookups.
- 750,946 linked `Source` nodes visited.
- 2,767 existing-specialization hits.
- 428 misses/new routines.
- 235.04 linked nodes visited per lookup on average.
- The first 422 source misses alone account for 88,831 triangular construction visits (`0 + ... + 421`).
- The separate pending-lowering sweep was not the target: two sweeps visited only 428 source nodes in total.

This made specialization lookup the next measured linked-scan cost after the type-registration index.

## Candidate

`src/compiler/ir_lower.eri` now keeps a private 257-bucket specialization registry alongside the existing canonical `builder.sources` list.

The bucket hash uses stable declaration-source/token data and the existing specialization key only to select a bucket. Identity is never defined by the hash. A hit still requires exact equality of both:

- declaration identity; and
- specialization key text.

Collision-chain entries use a separate private `bucketNext` link. The existing `Source.next` list is preserved for lowering order and the existing pending sweep.

The change does not alter:

- public typed IR;
- function indices or names;
- source-list insertion order;
- specialization key construction;
- generic type assignment/concretization;
- diagnostics;
- verifier behavior;
- runtime or collector semantics; or
- the public 32-byte value ABI.

## Exactness checks

A bounded probe built both the merged-main baseline and the indexed candidate, then deliberately created two modules with identical generic function source shape and specialization keys so that bucket selection could collide while declaration identity differed.

Baseline and candidate remained byte-identical:

- collision-project typed IR SHA-256: `33f4556ef4142d10a4214684797fe68a3f88e9d005611698460907fb98c22af9`;
- collision-project x86-64 assembly SHA-256: `35551017246ab0eb600d7c3e87c40eed2b0efb0891d5ec235ea9018094e787bb`.

The repository's existing deterministic specialization regression remains in place as the permanent functional coverage; no expensive diagnostic workflow is retained by this change.

## Bounded bootstrap-runtime comparison

On the full current compiler source (`src/frontend.eri`) with identical command/environment and serial A/B/B/A execution:

| Run | Compiler | Wall | User | System | Max RSS |
| --- | --- | ---: | ---: | ---: | ---: |
| A1 | baseline | 6.53 s | 6.23 s | 0.29 s | 544,960 KiB |
| B1 | candidate | 6.08 s | 5.81 s | 0.27 s | 545,040 KiB |
| B2 | candidate | 6.25 s | 5.94 s | 0.31 s | 545,108 KiB |
| A2 | baseline | 6.37 s | 6.07 s | 0.30 s | 545,100 KiB |

All four emitted assemblies were byte-identical with SHA-256 `7a08e608f097eb6e0c79e78650f17adcb52fb553d89f40a5ad37734548dc9efb7`.

Median wall time was 6.45 s for the baseline and 6.165 s for the candidate (about 4.4% lower on this bounded workload). Median user CPU was 6.15 s versus 5.875 s (also about 4.5% lower). RSS was effectively unchanged. These numbers establish a useful local/full-source signal in this environment only; they are not a general compiler-speed claim.

## Owned-runtime 300-second trajectory

The candidate was then measured once with the owned runtime against the same frozen compiler workload used for the post-#53 trajectory:

- frozen workload commit: `ab3a60674b0e862f5a237b5ede84f2dfa94953fe`;
- time cap: 300 seconds;
- candidate owned compiler B SHA-256: `b8b1b583020fd6f909ee99b49a435aa75bf9e102a8a8539e34cfb35aaf486096`;
- candidate compiler-B assembly SHA-256: `920b00d7ce55b146902b5b3e23d20a4d91bd287bc27075504f2bcd3fc0705022`;
- owned runtime object SHA-256: `f1f384cb6b2dd407f3f73474772ae38f85bd54f548d596429f3edbbdd2bb0103`.

At the same cap:

- post-#53 trajectory: 122 `lower-function` begins / 121 completions;
- indexed specialization candidate: 145 begins / 144 completions;
- difference: 23 additional completed lowering functions;
- equivalently, about 19% more function completions at the same censored 300-second point.

The approximately 19% figure is **not** a 19% wall-time or compiler-speed claim: function costs are nonuniform and both measurements are censored.

The candidate still timed out during typed-IR lowering. It did not reach `typed-ir-verify`, `universal-lower`, or `universal-optimize`. Therefore this optimization does not justify a 900-second owned self-build by itself. Full owned compiler repeatability remains unproven.

## Qualification policy

Because this modifies compiler/common source, the production candidate should pass:

1. the normal four-job CI matrix;
2. full bootstrap/offline qualification and owned integration on the final head;
3. no 900-second owned compiler self-build unless a later bounded trajectory reaches materially later compiler phases.
