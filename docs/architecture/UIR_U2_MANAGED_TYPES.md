# U2 managed Text/List/identity semantic descriptors

Status: managed descriptors focused-tested; operation-contract follow-up unqualified.
Locked design: `DESIGN_PHILOSOPHY.md`, `LANGUAGE_SEMANTICS.md`, `COLLECTIONS.md`, `IDENTITY_EQUALITY.md`.

The first managed-runtime integration gate adds a **private semantic descriptor
registry**, not a second executable UIR, a new public type syntax or a native
heap/GC layout. The qualified U1/U1b structural type graph is unchanged.
A metadata-owner-scoped registry refers to that frozen graph, with a unique
identity key and exact graph identity, and uses a separate local TypeId
namespace. Every managed descriptor has exactly four words:

- kind: 1 = Text, 2 = List, 3 = identity;
- elementDomain: 0 = structural aggregate graph, 1 = managed descriptor table;
- element: previous descriptor index or existing structural TypeId;
- copyPolicy: 1 = ordinary value/snapshot semantics, 2 = shared identity alias.

Canonical row 1 is Text (1,0,0,1); other rows are List and identity only.
Descriptor rows may refer to earlier managed entries but never forward/cyclic
ones. Distinct List and identity wrappers never intern to the same TypeId.
Repeated identical relationships intern to one deterministic descriptor.
List copyPolicy 1 does not permit physical in-place aliasing; identity
copyPolicy 2 preserves logical sharing, not raw address comparison.
Nested List identity positions reject deep-fixability. Text/view contents
are governed by Unicode 17 and frozen Text semantics, not by this descriptor.

## Accepted boundaries for this incremental implementation

The metadata-backed registry is bounded to 64 descriptors (256 words), and
uses fixed-size owner-charged radix backing. Construction phases use the
existing accounting/cancellation protocol. A storage failure poisons the
registry until close; no partial record can be frozen for publication.
The independent checker reruns the existing structural graph verifier,
validates all records including unreachable type rows, rejects forged
copy policy and missing/stale backing, and reports counts. All code remains
opt-in and uses existing ordinary .eri / bootstrap flow.

**NOT implemented by these descriptors:** canonical UIR managed type
references/operations, actual owned Text/List/identity allocation or copy
lowering, Unicode 17 runtime behavioral conformance for the redesigned UIR,
root-class mapping, automatic machine safe-point publication, recursive
frame lifetime handling, runtime resource adapters, or full four-platform
qualification. The currently qualified owned runtime already supports
Text/List/identity via its separate existing production mechanisms, but
calling those mechanisms from complete redesigned UIR is still pending.

See `HANDOVER.md` for latest tested source head. Keep U2 #74
open and PR #111 draft until all semantic, runtime and qualification gates
are satisfied.

## Focused evidence and new private operation semantics

[CI #41629331699](https://github.com/eristavi/eristavi-lang/actions/runs/41629331699)
completed SUCCESS on exact source `b57c5dfc88a1e618069a2c002f01f06e88821d26`:
85 run, 82 passed, 0 failed, 3 intentionally skipped.
The original standalone fixture failed in CI #41625310530 due to
a missing U1a generic `TypeId`-list specialization, resolved by using
the accepted U1b metadata test initialization. The frozen compiler
and public runtime were not modified.

The next **unqualified** opt-in `u2_managed_operation_contract.eri`
selects these private version-one semantic obligations:

| ID | Logical contract | Return behavior | Root/allocator obligation |
| --- | --- | --- | --- |
| 1 | Copy: Text immutable, List value snapshot, identity shared alias | One value | List may allocate and must root |
| 2 | List.add | No value | Allocation and live-root preservation |
| 3 | List indexed replacement | No value | Bounds terminal fault; allocation/root |
| 4 | Structural List equality | Bool | Conservative temporary state/root |
| 5 | List iteration snapshot | Snapshot value | Allocation/root |
| 6 | Text scalar-sequence equality | Bool | No normalization or implicit allocation |
| 7 | Unicode17 Text view | View value | Explicit grapheme/scalar/byte selector |
| 8 | Logical identity equality | Bool | No physical-address equality |

The operation selection API rejects foreign or mutable tables, wrong
type families, invalid view selectors and unknown mandatory operations.
`mayAllocate` is conservative, not an assertion that the machine
lowering exists. No fake Void, new source syntax, public ABI change,
second executable UIR or collector is introduced.

**Do not confuse operation contract selection with implementation.**
The canonical UIR backend must still encode/verify typed managed operands,
result/no-result conventions, allocation/fault effects, physical runtime
copy/update/view semantics and actual live-root stores. These new
selectors are not executable and the new CI remains pending.

## Corrected operation profile and baseline runtime-parity regression

The first operation-contract CI [#41630206523](https://github.com/eristavi/eristavi-lang/actions/runs/41630206523)
failed one new test due to unsupported `else if` syntax. The corrected
selector uses disjoint `if` cases, validates the frozen type copy policy,
and conservatively roots Text copies as potentially allocating until a
backend separately proves a no-allocation implementation. No public ABI or
frozen source semantic rule was modified.

The new `test_u2_managed_unicode17_list_value_and_identity_alias_parity`
executes a mixed regression on the existing Stage-0 reference interpreter,
existing C-native runtime and existing owned Linux x86-64 graph runtime:
decomposed versus composed Text equality (no implicit normalization),
Unicode17 grapheme/scalar/UTF-8 byte counts, stable copied List length,
explicit identity mutation sharing and distinct-identity inequality.
The owned runtime probe also checks final graph/Text reclamation.
This is a prerequisite behavior oracle for future redesigned UIR lowering,
**not** proof that the new UIR path executes managed operations. The exact
source-head smoke outcome remains pending.
