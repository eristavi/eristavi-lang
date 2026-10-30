# Eristavi project records and local evidence

Published 30 October 2026. Start with [the handover](../HANDOVER.md), then read the
relevant decision record below. These files make the project recoverable without
the original workspace. This publication adds documentation and archived evidence;
it does not implement the remaining compiler redesign or rerun qualification.

## Architecture and decisions

| Record | Scope |
| --- | --- |
| [Lexer](architecture/Eristavi-Lexer-Architecture-2026-10-29.md) | Agreed lexer design and acceptance criteria |
| [Parser](architecture/Eristavi-Parser-Architecture-Proposal-2026-10-29.md) | Parser architecture and error recovery |
| [Modules and cache](architecture/Eristavi-Module-Architecture-Proposal-2026-10-29.md) | Phased module/cache design; filesystem decision FS-001 remains pending |
| [Semantics](architecture/Eristavi-Semantic-Architecture-Proposal-2026-10-29.md) | Semantic architecture and frozen facts |
| [Typed Universal IR](architecture/Eristavi-Typed-Universal-IR-Proposal-2026-10-29.md) | Agreed architecture and implementation status |
| [U1 contract](architecture/Eristavi-UIR-U1-Contract-2026-10-29.md) | Full U1 operation/verification contract; only the documented subset is implemented |
| [U0 baseline](architecture/Eristavi-UIR-U0-Baseline-2026-10-29.md) | Measurements, limitations, and subsequent decisions |
| [U1a budget policy](architecture/Eristavi-UIR-U1a-Budgets-2026-10-29.json) | Selected development and qualification budgets |
| [Repository audit](architecture/Eristavi-Repository-Audit-2026-10-29.md) | Historical inspected source baseline, not a new audit of current main |
| [Continuation pointer](architecture/Eristavi-New-Chat-Checkpoint.md) | Saved checkpoint pointing to the handover |

These are the local decision records as captured at publication. A filename's
date does not imply that every section was implemented on that date. Read each
record's status and the current handover. Older pending-review wording remains
historical context; the current handover and later explicit decisions identify
the approved UIR direction. Private document links in the readable records were
changed to relative repository links; their decision text was retained.

## Evidence available in Git

All evidence is under [evidence/2026-10-30](evidence/2026-10-30):

| File | Contents |
| --- | --- |
| [Original U0 evidence](evidence/2026-10-30/Eristavi-UIR-U0-Evidence-2026-10-29.zip) | Unchanged original archive, including its original report, measurements, scripts, fixtures, and generated products |
| [Local U0 work](evidence/2026-10-30/u0-local-work.zip) | Complete captured U0 work directory, excluding installed dependencies and Python bytecode |
| [Local U1 work](evidence/2026-10-30/u1-local-work.zip) | Budget worksheet/generator, foundation/verifier/promotion logs, experimental probes, intermediate compiler copies, assembly, objects, and diagnostic executables |
| [Local file manifest](evidence/2026-10-30/LOCAL_FILE_MANIFEST.json) | Original local paths, byte lengths, SHA-256 hashes, publication destinations, already-published source references, and exclusions |
| [SHA256SUMS](evidence/2026-10-30/SHA256SUMS) | Hashes of published records, archives, and the manifest, relative to the repository root |

The two original uploaded documents are preserved under
[history/2026-10-29](history/2026-10-29). They are historical inputs and are
superseded where the current decision records or handover say otherwise.

Archives deliberately retain failed, timed-out, and intermediate experiments.
Their contents are evidence, not a claim that every experiment passed. Generated
compiler copies can reflect an earlier stage than the final merged implementation.
Logs and binaries describe their recorded host/run; archived executables are not
a supported compiler distribution. Rebuild from the recorded sources in a fresh
environment. Original archived reports/scripts may retain historical saved-file
references; use the readable architecture copies above for current navigation.

The original U0 archive SHA-256 remains
`63ee91cbec2b3d2f2d835e20396d533ee25a2f31543f899f77483f1d4d3ddeaa`.
It was not repacked or edited. It and the local U0 archive overlap intentionally:
one preserves the original evidence artifact, the other preserves the local tree.

## Recover the workspace

Check out this documentation branch and verify from the repository root:

```sh
sha256sum -c docs/evidence/2026-10-30/SHA256SUMS
```

Create an empty workspace beside the repository and extract `u0-local-work.zip`
and `u1-local-work.zip` into it. Their members retain the original top-level
directory names. The U0 scripts expect an `eristavi-audit` sibling containing
commit `8af0ffe3350c737550c3ab0e6c3fa89f60f6f091`; clone/check out that commit
there. Its 342 local files were verified against the recorded Git blob IDs, so
no separate duplicate source archive is needed. The implementation checkpoint
is `cd421d859e3372796e59ddf236944efc1b6aaddb`; the handover records its tests.

Install U0 Python dependencies from its `requirements.txt`. Clang/LLVM downloads,
Ubuntu package archives, Python caches, document-transfer utilities/receipts,
editor/runtime configuration, and Git internals were excluded. The manifest
records these boundaries. All local project documents and non-dependency
experimental work were included; tracked compiler source was already on GitHub.

This is separate from GitHub Actions artifacts. Their run IDs/digests and 14-day
retention are recorded in the handover; this upload does not extend their lifetime.
No full owned compiler self-build was started or established by this publication.
