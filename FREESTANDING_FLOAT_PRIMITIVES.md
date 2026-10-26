# Freestanding binary64 operation foundation

Status: primitive operations qualified in PR #32 and merged. Linux/System-V x86-64.

`runtime.float_x86_64.source()` emits private machine operations on binary64 bit
patterns. `src/float_runtime_primitives.eri` exposes an assembly generator for
qualification. This is not yet a Float value-runtime profile or a replacement for
`evn_float` decimal literal parsing, output formatting, or compiler self-build.

`erist_rt_float_binary(op, firstBits, secondBits)` follows existing operation numbers:
0 addition, 1 subtraction, 2 multiplication, 3 division, 5 equality, 6 inequality,
7 less, 8 less/equal, 9 greater, 10 greater/equal. Arithmetic returns binary64 bits;
comparisons return 0/1. Status in RDX is zero on success, one for an invalid code.
Float remainder code 4 remains unsupported as required by `FLOAT.md`.
`erist_rt_float_negate(bits)` flips the sign bit, including signed zero.

Separate SSE2 instructions enforce binary64 intermediates without FMA contraction.
Each binary operation saves the caller MXCSR, installs masked IEEE exceptions,
round-to-nearest/ties-even with DAZ and FTZ disabled, and restores the exact caller
state on every return, including invalid operations. Division by zero yields IEEE
infinities/NaNs. Comparisons explicitly handle unordered operands, including
signaling NaNs. No libc, libm, C runtime, Python or dynamic loader is linked into
the emitted target.

Automatic regression coverage checks halfway rounding, overflow, gradual underflow,
signed zero, infinity and every NaN comparison; a fixed random finite corpus is
compared with hosted binary64 results. The caller deliberately enables truncation,
DAZ and FTZ before every call and checks exact MXCSR restoration afterward. Static
ELF/import checks and unavailable-PATH execution use the existing harness.

PR #33 qualified the exact decimal-output helper matching `%.17g`. The subsequent
Float value profile adds exact literal parsing, slots, scope escapes and ordinary
helper dispatch; see `FREESTANDING_FLOAT_VALUES.md` for its qualification boundary. Existing language semantics do not define a new numeric conversion
API; this batch introduces none.
