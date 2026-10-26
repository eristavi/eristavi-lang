# Freestanding Text operators and complete supported-value safe points

Status: Linux/System-V x86-64 review candidate; automatic qualification pending.

This completes steps 3–5 of the current Text stack: equality/inequality, checked
concatenation, and allocation safe points for every supported ordinary value helper.
It builds on validated UTF-8 storage, managed Text lifetimes and root-map slot pruning.
No syntax, public type, ownership rule, operator mapping or Unicode contract changes.

## Operators

`evn_binary` dispatches type-4 operations through the existing mapping: 0 is addition,
5 equality, and 6 inequality. Equality compares byte length and every UTF-8 byte,
including embedded NUL. It does not normalize or segment text implicitly. Composed
and decomposed spellings therefore retain the existing exact-byte equality behavior.
Comparison results are normalized Bool values and pass through the normal safe point.
Other internal Text operator codes remain runtime defects.

Concatenation checks unsigned addition overflow and the reservation boundary's maximum
supported length before reading payload bytes or allocating. Empty operands share the
other immutable value through normal Text copy. Nonempty operands append within an existing reservation only when the left input
is its longest published prefix and sufficient capacity remains. Otherwise they
allocate geometrically sized storage and copy both byte spans. All destination
byte writes use the verified lowerer. Previously published bytes and snapshot
lengths remain unchanged, including self-concatenation and branches from older
prefixes. See `FREESTANDING_TEXT_CAPACITY.md` for the capacity and registry rules.

A common private publish operation installs the owned reservation in the typed Text
registry and completes the 32-byte Text value slot before collection. Constructors
and concatenation use the same publication boundary. Registry allocation failure
releases the unpublished reservation; a failed copy releases its reservation before
terminating with an internal fault. Fatal slot-allocation failure terminates the
process through the existing out-of-memory path.

## Allocation safe points

The Text-enabled runtime now reaches a safe point after each supported allocating
ordinary-value helper completes its result:

| Helpers | Publication boundary |
| --- | --- |
| Int, Bool, void constructors | Complete scalar slot, then safe point |
| Scalar copies, unary and binary operations | Complete scalar result, then safe point |
| Text copies | Full immutable Text representation installed, then safe point |
| Text construction and concatenation | Owned buffer registered and full slot installed |
| Scope return/unwind | Full escaping value re-slotted before safe point |

The low-level `erist_rt_value_new` remains deliberately raw for multi-step construction;
only private runtime implementation code calls it. Scalar-only composition retains its
previous behavior. The Text-enabled composition bounds both scalar-only loops and
Text-producing loops using the existing registered root maps. Scope administration
is not an ordinary value: scope entry installs an unregistered frame and pruning is
deferred until all active frames have registered their maps.

Every safe point protects its pending result before the caller can spill it, retains
all registered value-class roots and scope marks, prunes dead slots at the bounded
threshold, then traces the surviving Text roots. Partially constructed Text never
enters a collection gap. Handlers, failures/resources, aggregates and interior views
are still outside this supported runtime profile.

## Qualification

Automatic-CI regressions compare operators against independent expected byte results
across empty, multilingual, composed/decomposed, emoji and NUL-containing inputs.
They cover self-concatenation, stable input snapshots, a result spanning a page,
size/carry overflow rejection before bogus payload dereference, and full tracked
Text release. Allocation stress checks all supported constructor/copy/operator families
in one registered long-lived scope, validates pending results, bounds temporary slots,
and confirms that scalar allocations reclaim abandoned Text buffers.

A real `.eri` fixture uses function returns, comparisons, snapshot-preserving updates,
300 repeated concatenations and a 10,000-iteration scalar loop. It compiles through
the Eristavi-written frontend and links against only the emitted freestanding runtime.
Static ELF/import checks and execution with an unavailable PATH remain required.
No tests were run manually; normal GitHub CI supplies qualification.

This finishes the current basic Text/value-lifetime stack, not the whole Text runtime.
Byte/scalar/grapheme views and Unicode library operations remain next. Registry lookup,
collection scans and page-per-buffer allocation still need performance work. The
compiler/generator retain their bootstrap runtime; GNU as/ld remain required.
