# Freestanding Unicode 17 graphemes and scalar primitives

Status: Linux x86-64 review candidate; automatic qualification pending.

The explicit Text-view runtime now supports `characters` count/index in addition to
bytes and scalars. A streaming scanner implements the existing Unicode 17 GB3–GB999
rules, with separate state for RI parity, EP/Extend/ZWJ chains and Indic conjunct
linkers. It scans decoded scalars without allocating a decoded-text array. Indexed
clusters become independently managed Text; copied/escaping views retain their
immutable backing storage through the existing typed roots and collector.

Read-only property ranges are frozen as Eristavi-owned emitter data, copied exactly
from the previously qualified Unicode 17 tables. UNICODE_TABLE_PROVENANCE.json records
the source snapshot, per-table hashes and row counts. The target performs native
binary-search lookups; no C routine, Python module, OS locale or host Unicode service
participates in target execution. The runtime-source generator retains the existing
bootstrap dependency. Frozen data is checked against the independently pinned regex
property generator in automatic CI, including all range boundaries in native lookup.

The same native UTF-8 decoder and lookup layer implement existing std.unicode
`fromScalar`, `isIdentifierStart` and `isIdentifierContinue` through the current
builtin ABI. Scalar encoding covers 1–4-byte canonical UTF-8 and rejects negatives,
surrogates and values above U+10FFFF with the existing fault. Identifier checks accept
exactly one scalar and preserve the existing underscore behavior and pinned XID data.
NFC normalization remains unimplemented in this freestanding profile: it requires its
own canonical decomposition, ordering and composition migration. No substitution or
implicit normalization is introduced.

Hosted native qualification runs the complete official Unicode 17 grapheme vectors
already supplied by CI, checking count, every cluster's byte span, and out-of-bounds
results. It also covers every property-range boundary, returned/copied character
views under allocation churn, source-scope escape, NUL/control/Hangul/RI/ZWJ/Indic
cases, Unicode scalar encoding boundaries/faults, XID examples, complete managed
release and static/no-import ELF execution. No tests were manually run; normal GitHub
CI provides qualification. Syntax, read-only semantics and Unicode version are fixed.

This completes the view families and starts Unicode-library runtime migration; it
is not completion of NFC, Text performance, Float, aggregate/identity, failures and
resources, the full collector, compiler independence, or machine-code/object/linker
and platform work. GNU as/ld remain required.
