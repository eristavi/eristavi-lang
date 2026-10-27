# Owned aggregate, optional, identity and checked-failure runtime

Foundation: qualified in PR #35, merged as `e7be684613f08486544c3252e9520ef85c8f96d0`.
All four automatic CI jobs passed, including the three Linux self-build/offline gates.
The subsequent storage/index/scheduling optimizations are qualified as part of the
build-integration batch described in `OWNED_BUILD_INTEGRATION.md`.

`runtime.value_output_x86_64.graphSource()` and `src/graph_value_runtime.eri` compose
the owned scalar/Float/Text/Unicode runtime with Objects, Lists, maybe/identity and
ordinary checked failures. The source language, type rules and 32-byte value ABI
are unchanged. Existing scalar, Text and Float profiles retain their enabled value
families. General compiler builds still use the existing broad bootstrap runtime.

## Owned storage and value operations

Every object allocation contains a 64-byte private header followed by initialized
32-byte cells. The first two words keep the existing object ABI (count and data
pointer); the remaining words hold registry, mark, work-list, hash, capacity and backing-owner links. Empty
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
snapshot iteration. Append publishes a separate logical-prefix header. A private
backing owner stores initialized length and geometrically grown capacity. Only an
append to its latest complete prefix may fill unused tail capacity. Appending to
an older prefix allocates independent backing; member/index mutation still detaches.
Older snapshot lengths and cells never change. Marking a snapshot retains its backing
owner, whose initialized cells are visited once. Spare capacity is never interpreted.
A shorter live snapshot can retain the initialized tail of its shared backing until
that backing dies; this is bounded by that backing's geometric capacity.
The ordinary monotonic append path initializes/copies a linear number of cells,
plus one fixed-size snapshot header per append. Branching from old prefixes still
requires copying their logical contents.

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
stale and machine-class words are not dereferenced as values. Before marking, a nonowning sorted interval index is prepared over initialized
backing owners (snapshot aliases are excluded). Iterative in-place heapsort uses no
recursive stack or auxiliary sort allocation. Interior lookup then uses binary search
and validates full-cell alignment and initialized bounds. Outside a prepared collection,
private probes retain a validated linear fallback. New allocations and sweep invalidate
the index; sweep releases its scratch allocation when the object heap empties.

Tracing marks an object before enqueueing it on an intrusive work list, then visits
its initialized cells iteratively. Cycles and deep mixed optional/identity graphs
need no recursive marking or heap-allocated mark queue. Index preparation may grow
its private scratch allocation before marking; OOM there remains a terminal fault. Text/view leaves mark their
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

The graph/resource profiles batch dirty graph tracing using a safe-point budget.
After a collection the budget is half the surviving graph/Text/failure record count,
bounded to 128..65536. Mutation marks reachability dirty without forcing a full trace
at the very next helper call. Slot pruning remains independent, and explicit
`erist_rt_text_collect` performs an immediate complete trace. This changes collection
timing, not value semantics or deterministic resource cleanup. Small Text-only
profiles retain their existing orphan-release scheduling.

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

The explicit graph profile continues to reject resource values. The next combined
resource profile adds file/process builtins, deterministic cleanup and secondary
failure contexts; see `OWNED_RESOURCE_RUNTIME.md`. Secondary contexts use the saved
failure reserved word as an ordered chain link and share the typed failure tracer.
The resource composition is qualified in PR #36. Owned build/startup integration and
compiler self-build qualification are tracked in `OWNED_BUILD_INTEGRATION.md`. Bootstrap C/Python and GNU as/ld have not been removed,
and independent ARM64/Windows/macOS execution is not implemented by this batch.
