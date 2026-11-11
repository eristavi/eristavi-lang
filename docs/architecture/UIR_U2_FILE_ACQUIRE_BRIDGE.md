# U2 private checked File acquisition bridge — reconciled contract

Development-only opt-in embedding adapter. The bounded whole-Function File
emitter on PR #121 already acquires and closes Files through the existing
runtime and original SSA/control-flow path. This separate bridge preserves
PR #111's independently admitted helper but **does not** replace or route
the whole-Function emitter. No second resource runtime, executable IR,
source syntax or production ABI is introduced.

The bridge verifies the original complete canonical ownership profile and
checked failure root map before output; it selects exact opcode-46 File
acquisition and its original path ValueId, then obtains the failure carrier
from the verified matching class-5 root-map entry. It requires Text, File
owner and saved-failure carriers to be pairwise distinct. Admission delegates
the imported symbol/signature to
`u2_function_native_imports.inspectFile`, the same verifier called by
the whole-Function emitter: `u2.file.openRead.v1`, imported kind 2,
effects 63, version 1, one opaque Text input, one noncopyable File result,
and exact two-Text-field FileError. There is no supported effects-8 alias.
Wrong metadata/layout or stale/foreign root maps reject before assembly.

Private embedding ABI remains unchanged: RDI=caller-rooted boxed Text,
RSI=empty registered class-1 File root address, RDX=distinct empty
registered class-5 failure root address, RCX=native File runtime type.
Returns RAX=File or saved failure, R10=0 or 1, and RDX=0.
Successful acquisition publishes its File root before handler retirement.
A checked failure saves and roots the failure before clearing the runtime
state. Terminal faults remain terminal.

The embedding caller remains responsible for binding actual SSA words,
checked edges, lexical owner moves, cleanup and final exits. PR #121's
existing whole-Function emitter already performs these operations in its
bounded verified profiles; no additional integration of this helper is
required or implied for this reconciliation.

Historical pre-reconciliation PR #111 evidence:
`docs/evidence/2026-11-09/u2-file-acquire/README.md` (effects-8 private
fixture, 2/2 local pass, not compatible with the normalized File contract).
Reconciled exact-head tests and limitations belong in
`docs/evidence/2026-11-11/u2-reconciliation/README.md`.
U2 issue #74 remains open and final qualification is not claimed.
