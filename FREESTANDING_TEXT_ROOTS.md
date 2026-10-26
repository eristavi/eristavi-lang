# Freestanding Text root-map slot reclamation

Status: stacked Linux x86-64 review candidate; automatic CI qualification pending.

The Text-only runtime now prunes administrative value slots at Text safe points,
then sweeps unreachable Text buffers. This closes the previous scope-only lifetime
limit for Text-producing loops with registered frames. Public syntax, ownership,
value semantics, failure behavior, and the pinned Unicode contract are unchanged.

The existing compiler-provided root-address array and byte-class array are consumed
without changing their ABI or the compiler emitter. Class 1 roots preserve matching
tracked slots. Scope marks and the helper's pending result are also preserved. Root
words, including stale or invalid words, are compared with exact tracked addresses;
no root word is dereferenced as a pointer. Other register classes are not value roots.
The pending result is protected before its caller has stored it in a root-map spill.

Pruning starts only if every active frame has non-null root and class arrays. An
unregistered frame or embedding without scopes retains arena behavior. This avoids
examining frames during initialization or silently collecting unregistered values.
All active frame maps are scanned, preserving caller values during nested execution.
After pruning, all surviving value slots remain the typed Text heap's root set.

Automatic Text safe points run after construction and after re-slotting scope results.
A private threshold starts at 256 slots and is reset to survivors plus 256 following
collection; scope shrinkage lowers the next threshold. Counting/scanning is currently
linear and root membership uses nested scans, so this is a bounded-memory correctness
slice rather than a production throughput claim. Scalar-only loops with no Text safe
point still require broader allocation-safe-point integration. Handlers, aggregates,
interior references and failure/resource graphs remain outside this runtime profile.

The hosted regression covers 2,000 allocations in a registered long-lived scope,
exact surviving slot/buffer counts, shared aliases, machine-class exclusion, invalid
root keys, delayed frame registration, preservation of nested scope marks and pending
results, complete release, and a real `.eri` Text loop through the native compiler.
Static ELF/runtime import checks are inherited from the lifetime test helper. Tests
have not been run manually; normal GitHub CI remains the qualification path.

The next Text functionality slice is equality/inequality and concatenation over this
lifetime foundation, followed by explicit Unicode views. Compiler/generator bootstrap
and GNU assembly/link dependencies are unchanged.
