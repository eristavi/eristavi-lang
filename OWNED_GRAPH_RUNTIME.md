# Owned aggregate, optional, identity and checked-failure runtime

Status: implementation and focused Linux/System-V x86-64 qualification passed;
automatic full CI qualification pending for the combined batch.

`runtime.value_output_x86_64.graphSource()` and `src/graph_value_runtime.eri` compose
the owned scalar/Float/Text/Unicode runtime with Objects, Lists, maybe/identity and
ordinary checked failures. The source language, type rules and 32-byte value ABI
are unchanged. Existing scalar, Text and Float profiles retain their enabled value
families. General compiler builds still use the existing broad bootstrap runtime.

## Owned storage and value operations

Every object allocation contains a 48-byte private header followed by initialized
32-byte cells. The first two words keep the existing object ABI (count and data
pointer); the remaining words hold registry, mark, work-list and hash links. Empty
objects have no data cells. The allocator owns the entire payload as one block.
Count/size arithmetic is checked before allocation. Every cell starts as void before
any constructor result can reach a safe point. Object, saved-failure and handler
word layouts are checked by `compiler.runtime_value.graphLayoutsValid()`.

Ordinary value copies share backing until a mutation detaches the affected container.
Nested member/index reference paths detach each ordinary container on that path.
Identity wrappers remain shared, while their contained ordinary value detaches when
updated. Optional absence uses null backing; present optionals have a one-cell
wrapper. Updating an optional value detaches its wrapper; identity aliases keep
their common wrapper. Source presence/refinement rules remain unchanged.

Lists support construction, initialization, checked reads/writes, count, append and
snapshot iteration. Append allocates fresh backing and copies the prefix, preserving
all older snapshots. Its current cost is linear per append; reusable prefix capacity
and more efficient long append chains are performance follow-up work. This batch
does not claim parity with the C runtime's prefix-append optimization.

Equality is structural for ordinary values, Lists and present optionals, exact-byte
for Text, IEEE for Float, and logical identity for identity handles. Identity edges
terminate structural comparison; equal state does not merge identities. A List
containing NaN can compare unequal to itself. Structural equality remains recursive;
the bounded-stack claim below applies to tracing, not arbitrary structural equality.

## Tracing and roots

Object pointers use a nonowning 4096-bucket hash index with full-address collision
checks. The registry owns the allocations. Sweep rebuilds the index from survivors.
Interior cell roots are accepted only after finding a tracked owner and proving a
complete 32-byte cell at an aligned offset inside its initialized data span. Unknown,
stale and machine-class words are not dereferenced as values. Interior lookup scans
the ownership registry; improving that lookup for very large live heaps is future
performance work.

Tracing marks an object before enqueueing it on an intrusive work list, then visits
its initialized cells iteratively. Cycles and deep mixed optional/identity graphs
need no recursive marking or heap-allocated mark queue. Text/view leaves mark their
existing reservation records, including shorter immutable prefix snapshots. Only
after all graph roots and transitive edges are marked may Text and object sweep run.

Root ownership is explicit:

| Category | Retention rule |
| --- | --- |
| Surviving value slots | Trace every complete slot after exact-address pruning |
| Interior value roots (class 1) | Validate owner and full cell, then retain/trace the owner |
| Saved failure roots (class 5) | Validate exact failure-record ownership before tracing payload/message |
| Current failure | Trace stable primary value and message snapshots |
| Active scopes and handlers (classes 6/4) | Explicitly owned active chains; never inferred from arbitrary root words |
| Handler slot boundaries | Pin every active handler's slot mark during slot pruning |
| Pending value/failure results | Protect before collection and clear protection after return publication |
| Machine/literal words | Do not interpret as managed value/failure roots |

Collection pressure includes managed object/failure allocations (threshold 128 at completed safe points)
as well as the existing slot-pruning threshold. Unregistered embedding scopes retain
the established arena fallback. There are no resource finalizers. A current failure
remains a strong snapshot until replacement, matching the existing native runtime;
`erist_rt_failure_clear` is an explicit private embedding/shutdown operation.

## Checked control transfer

The compiler's existing opaque `frame` and `setjmp` call boundary now has an owned
112-byte frame and native context save/restore. It saves callee-preserved GPRs,
post-call stack/continuation addresses, MXCSR and x87 control. No libc setjmp/longjmp
is linked into the emitted target. This is a private owned-runtime frame ABI, not
an interchangeable libc jmp_buf or a new language exception mechanism.

Failing snapshots the full primary typed value and its named message field before
jumping. The message need not be the first declared field. On a checked jump, popping
the frame restores the saved slot/scope boundaries without following root maps on
dead native stacks. Normal completion preserves its result. Saved failures are
managed records; typed matching uses canonical descriptor names. Typed handlers
receive the original payload, catch-all handlers receive the message view, and
propagation preserves the selected primary failure. Uncaught diagnostics preserve
UTF-8 and embedded NUL bytes.

Allocation defects remain terminal runtime faults, even inside an active checked
handler. The terminal fault writer now aligns its own stack before its nested write
call, so faults reached from partially constructed private frames obey the ABI.
Published storage remains internally consistent on terminal slot OOM; this does
not provide resumable OOM recovery. No production fault-injection hooks are added.

## Qualification and remaining boundary

Six focused graph tests passed in 5.269 seconds. They include:

- one ordinary application compared with the existing C native/collector runtime,
  using the same Eristavi-generated application assembly as the semantic oracle;
- deep copy-on-write, stable List iteration, aliases, optional updates, cyclic graphs,
  a 1200-iteration churn loop and nested failures while outer error payloads remain live;
- live-object/failure/handler bounds during that application and full final reclamation;
- a 60001-object, 20000-link mixed graph, marked and fully reclaimed without recursive tracing;
- validated interior/saved-failure roots, stale/machine root words, protected results,
  and callee-register/stack/FP-control restoration across a native checked jump;
- ten bounds/absence/size/OOM subcases, including OOM inside an active handler, plus
  uncaught diagnostics with a nonfirst message field and embedded NUL.

The existing Float application, Text operators and thirteen Text allocation-failure
probes also passed focused regression checks after the production changes. Static
ELF checks require no imports, dynamic loader or executable stack; target execution
uses an unavailable PATH. No manual full suite, self-build, workflow dispatch or
rerun was initiated. The complete batch is published once for normal automatic CI.

Resources, file/process builtins and deterministic cleanup are the next port. The
saved-context secondary slot is reserved; secondary cleanup contexts cannot yet be
created by this profile. Resource values are rejected rather than traced incompletely.
Full resource/secondary-failure integration and a compiler self-build on the owned
runtime remain outstanding. Bootstrap C/Python and GNU as/ld have not been removed,
and independent ARM64/Windows/macOS execution is not implemented by this batch.
