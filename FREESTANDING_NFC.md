# Freestanding Unicode 17 canonical normalization

Status: Linux x86-64 review candidate; automatic qualification pending.

The explicit `nfcSource()` runtime composition implements the existing
`std.unicode.normalizeNfc` ABI without a C/Python/host-Unicode target dependency.
The primitive-only view composition remains available. No implicit normalization,
source/type/ownership change or Unicode-version advance is introduced.

Canonical decomposition data, canonical composition pairs and combining classes are
frozen from the qualified Unicode 17 source tables. The emitter owns the data and
UNICODE_NFC_PROVENANCE.json records hashes, counts and the checked maximum expansion.
Transitive canonical decompositions are flattened ahead of target execution; Hangul
is decomposed and composed algorithmically. Stable combining-class ordering never
crosses a starter. Canonical composition retains blocking and exclusion behavior.

Temporary scalar storage uses its own zeroed OS reservation, bounded by the frozen
maximum of four decomposed scalars per input scalar. All scratch-word reads/writes
use the verified four-byte memory profile; output bytes use the existing verified
byte stores. Arithmetic and capacity are checked before allocation. The final result
is registered and fully slotted before its safe point. Scratch storage is released
with the original exact mapping length; immutable source snapshots remain untouched.
The initial reserve policy favors a simple correctness proof over allocation economy.

Automatic CI verifies data/provenance against pinned Unicode 17, then executes more
than 16,000 native normalization cases: every canonical mapping, every Hangul syllable,
every canonical composition pair, fully expanded spellings, reordered/blocked marks,
composition exclusions, NUL and emoji. Each case releases tracked Text storage before
the next; independent reserve/release boundary counters check total mapping balance,
including untracked scratch storage. A real `.eri` program checks function return, idempotence, snapshots and
1,000 normalization iterations. Static ELF/import and unusable-PATH checks remain.
Only syntax/diff/ABI review ran locally; tests are left to normal automatic GitHub CI.

Together with the preceding grapheme/Unicode primitive slice this covers the existing
Text views and std.unicode functions in this freestanding profile. Text performance,
Float, aggregates/identity, failures/resources, full collector and compiler bootstrap
independence, own object/linking tools and other target runtimes remain separate work.
The generator still uses the bootstrap toolchain; GNU as/ld remain required.
