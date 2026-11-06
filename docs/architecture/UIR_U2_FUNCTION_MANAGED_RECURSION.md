# Whole canonical Function managed self calls

Development profile, 6 November 2026. This extends the existing whole-Function
emitter, not the earlier standalone Text recursion adapter or handwritten
recursive cleanup tests. Follow the frozen language value/identity semantics,
canonical signatures, exact SSA liveness, runtime root ABI and CI qualification
policy. No public source syntax, collector, 32-byte ABI or default compiler change.

## Meaning and admission

`emitRecursive` explicitly associates one metadata-owned defined FunctionId with
this original frozen canonical Function. Independently check the complete body,
including dead instructions, and require the declaration's exact SignatureId,
kind 1, conservative effects 63, version 0, and no fallible registry entry.
A foreign/zero FunctionId, imported target, wrong signature or effects refuses
before assembly. Other defined targets remain unsupported. The ordinary `emit`
entry retains its previous import-only admission.

Canonical opcode 34 remains authoritative for argument/result ValueIds and
original source location. No executable call graph or alternative IR is made.
The self call shares the existing private packed-word frame ABI, which admits
up to eight parameters and one or two results. Scalar i64/pred words are raw;
managed Text/List/identity words are already boxed. Existing exact descriptor
admission still applies. Unknown representations and opcode 46 fail closed.

## Live frames and return handoff

The caller publishes independently verified `liveBefore` roots before the call.
Stage every argument in frame scratch without retiring those roots, then call
the generated Function label. Each child creates and registers its own scope
and root words before collecting. Parent-only values stay rooted even when
they are absent from the child's arguments.

The parent's two registered class-1 temporary words are the child's return root
vector. A child publishes each managed result into its corresponding word
before clearing its own vector, allocating its no-value scope-leave operand,
or leaving its scope. On return the parent writes all canonical result slots,
publishes `liveAfter`, and only then clears both temporary roots. Two results
are stored from RAX/RDX; result position determines the temporary root offset.
Scalar results never enter a class-1 word.

No global recursion depth, shared return roots, physical identity comparison
or extra value-copy semantics are introduced. This profile transports opaque
managed values and uses the existing runtime imports for actual Text/List copies.

## Resource cost

For V canonical SSA words and R tracked managed roots, the stack allocation is
`align16(8*V + 8*R + 304)` bytes plus one saved register and the return address.
The 256-byte scratch region already reserved for parallel phi transport is
reused only while a call is executing; arguments occupy at most 64 bytes.
Root storage and two temporary roots are separate from every SSA/scratch word.
The existing caps V <= 256, R <= 64, 64 blocks and 512 instructions still apply.
Call adaptation is O(parameter count + result count); root publication retains
the existing O(R) stores per instruction. Runtime scope registration and the
existing collector remain responsible for their own allocations. There is no
claim of measured compiler speedup, bounded total recursion depth or RSS.

## Evidence boundary

The new original UIR fixture retains a parent-private Text through collection
in recursive child frames, returns the original identity and independently
computed total, then reclaims all child Text buffers. Depths 0/1/5/32/64 and a
32-deep two-managed-result variant exercise real compiler-emitted recursion.
A separate frozen source fixture compares Stage-0 and old C-native with the
new native result; this is a narrow behavior oracle, not full U2 differential
acceptance. The native root/graph/Text/allocator finish audit still runs.

Sanitizing the C-bootstrap generators checks those C programs only. It cannot
instrument the owned assembler runtime or prove general checked cleanup safety.

Still required for #74: arbitrary nested managed construction/copy, complete
checked Function return/handler/cleanup contracts, recursive opcode-46 native
execution and class-5 roots, malicious/stale/missing-root refusal, combined
allocator-fault/physical/GC pause evidence, broad independent comparisons and
exact-head four-platform/completed-batch qualification. Keep #111 draft and
#74 open until these actually pass.
