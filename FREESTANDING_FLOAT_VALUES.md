# Owned Float value-runtime profile

Status: qualified in PR #34 across all four CI jobs and merged.
The later combined graph profile adds the next value families; see `OWNED_GRAPH_RUNTIME.md`.

`runtime.value_output_x86_64.floatSource()` composes the existing owned Int, Bool,
void, Text, Text views and Unicode helpers with ordinary Float values.
`src/float_value_runtime.eri` generates this profile. Float uses the unchanged
32-byte value ABI: type 2, binary64 bits at +8, zero scalar tails, and the existing
40-byte slot node. No syntax, type, operator or conversion API is introduced.

The profile implements decimal literal construction (`evn_float`), exact-bit copies
and stores, unary negation, arithmetic/comparison dispatch, output, and scope escapes.
Every completed Float result reaches the ordinary protected-result safe point.
Floats contain no heap edges, so tracing skips their payload bits. Float allocations
still participate in bounded slot pruning and coexist with retained Text/view roots.
Previously shipped scalar/Text profiles retain their existing enabled type sets.

## Correct decimal input

`erist_rt_float_parse(spelling)` accepts a trusted NUL-terminated canonical decimal
spelling and returns binary64 bits in RAX, with RDX status zero on success, one for
malformed spelling or two for an internal defect. The compiler already removes
numeric separators before the existing `evn_float` call; the lexer remains the source
syntax authority. The private parser also accepts a leading sign and integer decimal
spellings. It does not add those forms to source Float token recognition.

The parser validates the entire input, including after exponent overflow or after
its significant-digit prefix fills. It normalizes the decimal order using signed
128-bit arithmetic so exponent cancellation is not silently clamped. It retains
800 significant digits plus a sticky indication for further nonzero digits; input
length is not restricted to 800. Leading/trailing zeroes and long exponent spellings
are handled without input-sized scratch allocation.

Positive finite binary64 bit patterns are ordered numerically. Binary search compares
the decimal input with each exact midpoint between adjacent values. For a lower
value M*2^E, that midpoint is (2*M+1)*2^(E-1), including zero/subnormal, normal exponent
transitions and the maximum-finite overflow boundary. Equality selects the even
low bit. The sign is applied afterward, preserving negative underflow zero.

The shared exact-expansion helper converts each midpoint to finite decimal digits
using integer arithmetic. Its largest allowed midpoint needs at most 768 significant
digits: M is at most 2^54-1 and the lowest power is -1075. Thus an 800-digit prefix
plus sticky information distinguishes every midpoint exactly. If its digits match
the padded finite midpoint, any later nonzero digit makes the input larger; all
later zeroes make it equal. No truncated binary approximation is rounded again.
The fixed base-1e9 limb workspace holds 1152 digits, and binary search performs at
most 63 comparisons. This is a correctness baseline with bounded scratch, not a
claim of optimized decimal parsing throughput.

The parser and exact-expansion helper use under 3 KiB of nested stack storage and
allocate no heap scratch. They use no floating operations, so host rounding, FTZ,
DAZ and FP exception state cannot influence parsing. Invalid literals follow the
existing terminal runtime-fault message. Slot allocation failure after parsing
remains the ordinary terminal OOM fault.

## Arithmetic and output

The qualified strict SSE2 primitives establish ties-even with gradual underflow and
restore caller MXCSR. Float remainder stays unsupported. The value adapter retains
the existing C runtime helper's explicit positive NaN for zero/zero and NaN/zero;
unary minus preserves its normal sign-bit behavior. Output uses the shared exact
17-significant-digit formatter qualified in PR #33. No implicit numeric conversions
are added. `FLOAT.md` remains authoritative.

## Validation and boundary

Focused checks passed for 2481 valid spellings and 21 malformed spellings against
hosted `strtod`, including exact midpoints and perturbations beyond 800 digits,
subnormal/normal and finite/infinite boundaries, 10000-digit exponent cancellation,
huge signed exponents, trailing junk and hostile MXCSR. The formatter's 28364-pattern
oracle comparison and the existing IEEE arithmetic and Text-operator tests also
passed after the shared-helper refactor. The five-module batch took 15.597 seconds;
the added malformed-tail and Float-OOM checks passed in a second focused check of
the two changed modules (6.797 seconds). No manual full suite, self-build, workflow
dispatch or rerun was initiated.

A real `.eri` fixture exercises copied snapshots, stores, returned Floats, arithmetic,
NaN comparisons/output, signed zero, overflow/underflow, underscore spelling and a
3000-iteration Float/function loop while Text backing remains live. It links only
against the emitted owned runtime. ELF/import/stack checks and unavailable-PATH
execution pass, as do final slot bounds and complete Text/allocator reclamation.

This profile targets Linux x86-64. Bootstrap generators and the compiler still use
the existing broad C runtime, and assembly/linking still use GNU tools. Aggregates,
`maybe`/identity, checked failures and resources are not enabled by this profile.
The next value-family batch requires their common typed, cycle-safe heap tracer.
