# Owned binary64 decimal output

Status: isolated formatter qualified in PR #33 and merged. Shared-helper refactor
and value-profile integration have focused checks passed; full CI pending.

`runtime.float_format_x86_64.source()` emits the private
`erist_rt_float_format(bits, buffer)` helper. The caller supplies a trusted writable
32-byte buffer; the helper returns the byte length in RAX and status in RDX
(zero success, one internal capacity fault). It writes exactly the result bytes,
without a NUL or newline. The helper is not a new source-language conversion API.
`src/float_decimal_runtime.eri` generates this target assembly with existing Linux
syscall helpers for qualification.

The output matches the existing value runtime's `%.17g` formatting: at most 17
significant decimal digits, round-to-nearest/ties-even, trailing fractional zeros
removed, fixed notation for rounded decimal exponents -4 through 16, scientific
notation otherwise, and signed exponents padded to at least two digits. Signed
zero, infinities and signed NaNs retain the current hosted formatting behavior.
Output uses ASCII and a decimal point, independent of locale.

## Exact conversion

Decode the binary64 significand M and power E directly from integer bits. For
nonnegative E, form the exact integer M*2^E. For negative E, form M*5^(-E) with
decimal scale -E. No floating operation or approximate decimal conversion occurs.
The exact integer is represented by base-1e9 limbs and expanded to decimal digits.
Only then is it rounded once to 17 significant digits using the discarded digit,
sticky digits, and parity of the last retained digit. Carry propagation precedes
the fixed/scientific notation decision.

The fixed workspace holds 128 limbs (1152 decimal digits), while every finite
binary64 input requires at most 767 digits in this representation. Up to twelve
powers are multiplied per pass: 5^12 is less than 1e9, so a limb product plus carry
fits in an unsigned 64-bit word and introduces at most one new limb. The formatter
uses a 1792-byte stack workspace and calls the shared exact-digit
helper, which uses 512 bytes of limb workspace. Including saved registers and the
call boundary, nested stack use remains below 2.5 KiB; neither function allocates
heap storage. The longest formatted result is at most 24 bytes,
within the caller's 32-byte buffer. The capacity guard returns an internal status
rather than writing beyond the limb array.

No libc, printf, libm, C runtime, Python, locale service or dynamic loader is linked
into the emitted target. The function neither reads nor modifies floating state;
rounding, DAZ and FTZ modes cannot change its result. The generator still uses the
existing bootstrap runtime, and qualification still uses GNU as/ld.

## Qualification and boundary

`tests/test_freestanding_float_format.py` compares 28,364 bit patterns with an
independent hosted C `printf("%.17g")` oracle matching the existing contract. The
corpus covers every finite exponent with difficult significands, decimal powers
and adjacent representable values, exact halfway cases of both parities, random
patterns, both signs, and special values. The target checks both buffer guards,
every unused output byte, exact length, and unchanged hostile MXCSR state. Static
ELF checks require no imports or dynamic loader and a nonexecutable stack; target
execution uses an unavailable PATH. The hosted oracle's C dependency is confined
to the test and is not present in the target executable.

The focused formatter and thirteen Text allocation-failure cases passed together:
`python -m unittest test_freestanding_float_format test_owned_runtime_allocation_failures -v`
with `tests` and the pinned project dependencies on PYTHONPATH. This took 5.973
seconds. No manual full suite, self-build, workflow dispatch or rerun was initiated.
Full CI remains required before merging the new batch.

The subsequent Float value profile adds correctly rounded literal parsing, ordinary
value-helper dispatch, copies, stores, scope escapes and a real application fixture;
see `FREESTANDING_FLOAT_VALUES.md` for its pending qualification boundary. The
compiler retains its broad C-runtime dependency until all required value families
and failure/resource services have been ported.
