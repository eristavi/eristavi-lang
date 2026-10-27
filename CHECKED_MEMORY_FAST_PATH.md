# Profile-guided checked-memory lowering

A fresh owned self-build on main `0549aca22125c18b4ca5311877f01697e92f6f5f`
created compiler B successfully but timed out during B-to-C emission at 900 seconds.
No old compiler assembly was reused. The source snapshot remained unchanged;
compiler C, repeatability and the final offline audit did not complete.

A separate profiling executable sampled instruction pointers during the beginning
of that full-compilation workload. Of 1,000 CPU samples, 630 landed in the generic
`erist_rt_memory_load64` helper and 28 in its store counterpart. This is an early
sampling window, not a profile of the complete 900-second run. Debugger attachment
was unavailable, so the diagnostic executable used its own CPU timer and signal
handler; neither instrumentation nor timers are included in production builds.

The compiler-private memory emitter now recognizes exact, complete, verified
single-load/single-store programs and emits register-only code. IR verification
still runs first. Recognition checks register classes, instruction topology,
operands, widths, alignment and requested result. Unmatched programs retain the
existing general stack-based lowering; helper names do not select a bypass.

Null-base, positive page-multiple length, relative alignment, access bounds and
address-addition overflow checks remain. Verified widths are 1/2/4/8 bytes; a
positive page-multiple length is at least 4096, making the bounds subtraction
safe. Loads retain zero-extension semantics, stores return the original input
word, and failure still returns result zero/status one. The implementation uses
only result/status scratch registers and changes no public ABI or source semantics.

## Validation and measurements

Twenty-one allocator/raw-Text/OOM/graph/resource/pool checks passed. An additional
differential executable compared fast and generic lowering for all four widths,
loads/stores, null/invalid lengths, final-byte bounds, relative alignment, negative
offsets and address overflow. Its generic reference adds an unused verified
constant, retaining the general lowering. The frozen memory verifier is unchanged.

Three alternating owned-native `ir` runs per input used identical compiler-B
assembly and byte-identical output. Only the linked runtime changed:

| Declarations | Original median | Optimized median | Reduction |
| --- | --- | --- | --- |
| 80 | 1.164 s | 0.819 s | 30% |
| 160 | 6.349 s | 4.527 s | 29% |

These are host-specific parsing/semantic/IR/report timings, not full self-build
completion evidence. No additional 900-second attempt was started. No correctness
error was identified by this investigation; it located and reduced a CPU hotspot.

The changed emitter is outside the native frontend's 29-module dependency closure;
this batch changes the owned runtime implementation, not compiler-B assembly.
Normal four-platform CI and one owned integration qualification are required before
merge. The default stays on the bootstrap runtime, and repeated owned self-builds
remain unqualified. Further profiling of the full workload remains necessary.
