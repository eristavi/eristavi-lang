# Owned Linux file/process services and deterministic cleanup

Status: combined implementation and focused qualification; automatic full CI pending.
The previous graph/failure foundation is qualified and merged in PR #35.

`runtime.value_output_x86_64.resourceSource()` and `src/resource_value_runtime.eri`
compose the explicit Linux/System-V x86-64 runtime with the existing compiler builtin
and cleanup ABI. The emitted static ELF has no C runtime, libc startup, dynamic
loader, Python invocation or imported symbols. Generating it still uses the bootstrap
compiler and GNU as/ld; ordinary compiler builds have not switched to this profile.
Existing scalar/Text/Float/graph profiles keep their supported families unchanged.

## File and process boundary

The profile implements all current `std.files` and `std.process` builtins, retaining
32-byte values and existing type/failure rules:

- `open`, `openRead`, exclusive `create`, full-file `readText`, replacement `writeText`,
  `exists`, `remove` (including empty directories), and `canonicalPath`;
- process arguments excluding argv[0], exact-byte stderr output plus newline, and
  checked 0..255 exit status;
- existing Unicode builtin dispatch, including NFC, through the same runtime profile.

File I/O uses direct Linux syscalls. Open/stat/read retry EINTR; reads handle partial
results and early EOF. File reads start at offset zero, validate UTF-8 and preserve
embedded NUL in content. Paths reject embedded NUL through a typed FileError carrying
the original Text path. Writes reopen/truncate the pathname, matching the existing
`freopen` behavior, including closing the old handle if reopening fails. Read-only
writes raise FileError. Operations on closed resources are terminal runtime faults.

`canonicalPath` opens the target with O_PATH and reads `/proc/self/fd/N`. It resolves
symlinks without requiring file read permission, and grows its readlink buffer as
needed. **This implementation requires mounted Linux procfs.** Missing procfs is a
checked FileError; a procfs-independent resolver remains follow-up portability work.
Common errno messages use the usual English Linux wording; unmapped errno values
use `file operation failed`. No new errno field or locale contract is introduced.

`erist_rt_process_start` receives the untouched Linux initial stack pointer, records
argc/argv, aligns the stack, calls `erist_entry` and exits with the selected status.
It is an explicit startup helper; the module does not inject a competing `_start`.
Arguments are UTF-8 validated and copied into owned immutable Text. An explicit
pending List root protects every initialized argument cell during construction and
collection. This is not yet the default compiler build/startup path.

## Ownership and cleanup

A file record is 96 private bytes plus an inline NUL-terminated path:

| Offset | Meaning |
| --- | --- |
| 0..31 | Owned Text path value |
| 32 | Inline C-path address |
| 40 | Linux descriptor, -1 after close |
| 48 | Closed flag |
| 56 | Writable flag |
| 64 | Registry link |
| 72 | Trace mark |
| 80 | Resource value type |
| 88 | Reserved zero word |

The compiler's opaque resource value points to this record. All size arithmetic and
allocation results are checked before publication. The private layout verifier checks
the record shape. Resources participate in typed tracing; exact registry validation
precedes pointer interpretation. Open handles are explicit administration roots until
cleanup closes them. The collector traces their paths but never closes descriptors or
runs user cleanup. Closed records are reclaimed after their value roots expire.
Consequently an embedding caller must still obey the compiler's cleanup protocol;
losing an open handle does not silently substitute GC finalization for deterministic
cleanup.

`cleanup_normal`, `cleanup_accumulate` and `unwind` use the compiler's existing reverse
cleanup order. Each close marks the resource closed and consumes its descriptor
before reporting a failure. Linux close is not retried on EINTR: the descriptor may
already be reused. Repeating cleanup does nothing, even after a failed close.

A body failure remains primary. Otherwise the first cleanup failure becomes primary.
Later cleanup failures are appended in order, with complete typed payload and message
snapshots. Secondary nodes reuse owned saved-failure records: offset 80 is the primary
secondary head, and offset 88 is a secondary node's chain link. The tracer follows
these links iteratively and retains transitive value/Text payloads. Current failures,
saved class-5 roots and the temporary cleanup primary all retain secondary contexts.

A checked unwind pops its handler and restores abandoned slot/scope boundaries before
any saved-failure safe point. This prevents collection from reading dead native stack
root maps. Pending file-error paths and process argument results have explicit roots;
no collection occurs between raw object construction and failure/result publication.
OOM remains a terminal runtime fault, including when constructing a cleanup failure.

## Qualification and remaining work

The focused resource batch covers an ordinary application compared against the existing
C/native runtime, including nested returns, a 600-read churn loop, failure payload paths,
read-only and exclusive-create failures, symlink canonicalization, invalid UTF-8,
embedded NUL content and stderr, process arguments/status, and final reclamation of
resources, graph objects, Text, failures and handlers. Test-only close-failure injection
checks ordered secondary snapshots, transitive retention after slot pruning, current
failure roots, exactly-once close and generated body-failure/return cleanup behavior.
Further probes cover 401 arguments during collection, invalid argument bytes, interrupted
open/read and one-byte partial reads, path NUL/missing paths, directory removal, closed
handle faults, invalid exit codes and allocation failure at four file construction/read
boundaries and four cleanup-failure snapshot boundaries. Production sources contain no injection hooks.

The full automatic four-platform CI and Linux self-build/offline gates qualify this
combined batch once. No workflow jobs are disabled or manually dispatched per helper.
Full compiler execution on this profile, repeated C-runtime-free self-builds, required
Python removal, direct object output/linking and independent ARM64/Windows/macOS
runtime ports remain outstanding. List append and interior-owner lookup performance
must be addressed or measured before large compiler workloads; this change does not
claim the bootstrap compiler is already independent.
