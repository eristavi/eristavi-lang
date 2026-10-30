# U1a synthetic source-origin chain — bounded first slice

Checkpoint: 2026-10-30. Scope: private in-memory metadata/independent verification only. Governing contract: `docs/architecture/Eristavi-UIR-U1-Contract-2026-10-29.md` §§9–10, plus the agreed source-location policy and `CI_QUALIFICATION.md`.

The metadata location record already has seven physical fields; its seventh previously required zero. This change gives it a checked *private* encoding for a **single parent** and transformation reason without enlarging metadata tables or changing U1 budget reservations:

- `0`: direct/original source location.
- `reason * 1048577 + parent.index`: derived origin; reason is 1 frontend lowering, 2 scalar promotion, 3 exact folding, or 4 machine legalization. Parent is a nonzero, **earlier** LocId.
- `meta.synthetic(metadata,phase,parent,reason)` copies the parent's source identity, byte span, diagnostic anchor and line/column into a new owned, immutable-on-freeze LocId, with an explicit typed parent and reason.
- The independent verifier checks nonnegative encoding, reason membership and strictly backward parent indices for **every location record**, including unused/dead locations. This enforces acyclic chains without recursive depth or a scan proportional to arbitrary external IDs.
- The raw source module ID and its SHA-256 digest stay in the existing owned source table. No reading of current source bytes or path guessing is introduced.
- Verifier regression constructs a two-step chain, checks valid diagnostics, corrupts a parent into a self-cycle, changes the reason, mutates a negative encoding, and restores the valid record. Reverification runs each time; no cached success flag is trusted.

**Explicit limits:** This initial encoding has one parent per derived LocId and four closed reason classes. It is **not** a frozen public artifact encoding, does not yet implement core-only synthetic roots without a parent, multi-parent origin sets, inlined call-site chains, U2 resource-exit origins, remapping during artifact serialization, or a native trap-report adapter. The current promoter preserves existing LocIds because it retains the original immutable metadata. These future obligations are described in `docs/architecture/ERISTAVI_U1_TO_U3_EXECUTION_PLAN.md`.

No frozen source syntax/semantics, production compiler, runtime ABI, target generator or module/artifact cache was changed. The code-bearing PR requires four-platform CI and completed-batch qualification on its final head before merge.
