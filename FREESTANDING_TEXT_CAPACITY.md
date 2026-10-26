# Freestanding Text capacity and registry

Status: implementation awaiting automatic CI qualification. Linux/System-V x86-64.

Repeated concatenation previously copied the complete prefix and reserved a new
mapping every time. The backing registry also searched its ownership list once
per Text root. This batch changes both paths without changing the 32-byte value
ABI, source semantics, UTF-8 validation or byte equality.

A registry record now has six eight-byte words: ownership link, original base,
exact mapped length, longest published prefix length, mark, and hash chain link.
The private layout verifier checks all six fields. The 4096-bucket nonowning index
hashes original reservation page numbers; every hit still compares the full base.
Collisions use intrusive chains. Marking uses this index; sweeping clears it and
reinserts surviving records before returning. Dead records cannot leave dangling
index pointers. The ownership list remains authoritative for release. The fixed
index adds 32 KiB of BSS and gives expected short lookup chains, not a worst-case
constant-time guarantee for arbitrarily many reservations or adversarial collisions.

Concatenation first checks the complete length for overflow. Empty operands share
existing storage. For nonempty inputs, capacity reuse requires both:

- the left input length equals its record's longest published prefix;
- the complete output fits in the exact existing reservation.

Only bytes after that published prefix are written. Each older value retains its
own byte length and continues to expose identical bytes. After all suffix stores
succeed, the record's published length advances and a complete result slot is
installed before the safe point. No new ownership record or mapping is needed.
Self-concatenation reads entirely before the append boundary. A branch from an
older, shorter prefix allocates separate storage, preserving every later snapshot.

If reuse is impossible, concatenation requests twice the output length, capped by
the existing maximum reservation size; the OS layer still returns the exact
rounded mapped length. This gives amortized linear copying and logarithmic mapping
growth for linear append chains. Independent Text construction still maps each
nonempty buffer separately. Small-buffer pooling remains future work; the change
does not claim to eliminate every allocation cost.

Copy failure releases only a newly acquired reservation. Failure while appending
never releases the live shared reservation. All writes continue through verified
byte stores with original base, exact mapped length and checked offset.

`tests/test_text_capacity.py` adds automatic coverage for deliberate hash collisions,
non-head hits, misses, 6000 appends across a page boundary with a reservation budget,
old prefix snapshots, branching, self-concatenation, index rebuild and complete
reclamation. Existing UTF-8, views, normalization and operator tests remain enabled.
