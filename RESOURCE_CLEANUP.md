# Eristavi Resource Cleanup Semantics

> **Status: Locked for pre-0.1**

This document defines deterministic resource cleanup and the composition of checked cleanup failures with ordinary completion, return, and already-propagating checked failures.

The governing rule is:

> Cleanup always runs exactly once. A cleanup failure prevents an otherwise successful exit. If another checked failure is already propagating, that original failure remains primary and cleanup failures are preserved as secondary failure context rather than replacing or silently discarding it.

## 1. Cleanup is deterministic

A resource owned by `with` is released exactly once when its block is left through ordinary language-level control flow.

```eri
with file be try files.open("data.txt") {
    let text be try file.readText();
    output(text);
}
```

Cleanup occurs on:

- normal fallthrough;
- `return`;
- checked failure propagation;
- exit from nested ordinary blocks that leave the owning `with` scope.

Nested resources clean up in reverse acquisition / nesting order.

Garbage collection is not the semantic mechanism for external-resource cleanup.

## 2. Cleanup failure contracts are statically known

A deterministic resource type has a statically known cleanup-failure contract, which may be empty.

The source-language spelling used by a future custom-resource declaration is not part of pre-0.1. Standard-library/runtime resource types may provide this metadata directly to the compiler.

The important semantic rule is that the compiler knows whether cleanup can produce checked failures and which error types are possible.

Those cleanup error types participate in ordinary checked-failure analysis for the enclosing function.

No new keyword or `with` syntax is introduced for cleanup failure contracts.

## 3. Successful body and successful cleanup

If the body completes normally and cleanup succeeds, the `with` statement completes normally.

If the body performs a valid `return` and cleanup succeeds, the pending return continues normally after cleanup.

## 4. Successful body but cleanup fails

If no checked failure is already propagating and cleanup produces a checked failure, that cleanup failure becomes the primary checked failure of the `with` exit.

This means cleanup failure prevents false success.

A pending successful return is cancelled by a cleanup failure:

```eri
function save() returns Int fails FileError {
    with file be try files.open("data.txt") {
        return 1;
    }
}
```

If cleanup fails with `FileError`, the function propagates that failure instead of returning `1`.

The same applies to normal fallthrough: failed cleanup cannot be silently converted into successful completion.

## 5. Body failure plus cleanup failure

Consider a block whose body is already propagating a checked failure:

```eri
with file be try files.open("data.txt") {
    fail SaveError {
        message = "Save failed";
    };
}
```

If cleanup succeeds, `SaveError` continues to propagate normally.

If cleanup also fails:

1. the already-propagating `SaveError` remains the **primary failure**;
2. the cleanup failure is attached as **secondary cleanup failure context**;
3. cleanup failure never replaces the original failure;
4. neither failure may be silently discarded.

The primary error's static type therefore remains stable during propagation.

This avoids surprising behavior where attempting to clean up changes which operation is reported as the original cause of failure.

## 6. Secondary failure context

Secondary cleanup failures are part of the propagation context, not a new source-level union or wrapper error type.

Pre-0.1 introduces no new syntax such as `FailureGroup`, `suppressed`, `cause`, or a second error operator merely to represent this situation.

The runtime/compiler must preserve secondary cleanup failures alongside the primary checked failure for diagnostics and failure reporting while that propagation context remains active.

When a checked-error handler handles the primary propagation, it handles that complete propagation context. The ordinary `error` binding continues to denote the primary typed error.

Pre-0.1 does not expose a programmatic API for enumerating attached secondary cleanup failures. Such an API may be designed later if real programs require it; the absence of an API does not permit implementations to overwrite or silently lose the secondary diagnostic context during propagation.

## 7. Multiple nested cleanup failures

Nested resources clean up in reverse order.

If no failure was active before cleanup begins:

- the first cleanup failure encountered in reverse cleanup order becomes the primary checked failure;
- later cleanup failures are attached as secondary cleanup failure context.

If a checked failure was already active from the body:

- that body failure remains primary;
- every cleanup failure encountered during unwinding is attached as secondary context, in cleanup order.

This gives deterministic behavior independent of target platform or backend implementation.

## 8. Static checked-failure analysis

A cleanup error type that may become primary participates in the enclosing function's checked `fails` analysis just like another checked failure source.

For pre-0.1, the compiler may conservatively include the statically known cleanup-failure set of every reachable `with` resource in the enclosing function's possible checked failures.

Therefore a function using a resource whose cleanup may fail must either have a compatible `fails` contract or be structured so the failure is handled at an ordinary checked-error boundary outside that function call.

The selected entry execution body still has no `fails` contract. A top-level `with` whose cleanup may produce an unhandled checked failure is therefore invalid at the entry boundary, just as any other unhandled checked failure is invalid there.

No special exemption exists merely because the failure arose during cleanup.

## 9. Runtime defects remain separate

This document defines composition of ordinary **checked cleanup failures**.

Runtime defects such as arithmetic faults, bounds faults, process termination, hardware faults, or catastrophic runtime failure remain outside the ordinary `fails` model.

A runtime defect is not converted into a checked cleanup error merely because it occurs while cleaning up.

## 10. Resource ownership remains unchanged

This decision does not add ownership transfer, borrowing, manual release, lifetime annotations, or identity wrapping for resources.

The existing pre-0.1 rules remain:

- a `with` resource has one scoped owner;
- the resource cannot be implicitly copied;
- it cannot silently escape its owning scope;
- it cannot be wrapped in `identity` to bypass ownership;
- cleanup is exactly once;
- nested cleanup is reverse-order.

Advanced ownership transfer and borrowing remain deliberately postponed until real programs justify them.

## 11. No new surface syntax

The existing syntax remains sufficient:

```eri
with resource be expression {
    ...
}
```

Cleanup-failure composition is a semantic/runtime rule, not additional grammar.

## Governing principle

> Successful control flow must never hide failed cleanup, and failed cleanup must never erase the failure that caused cleanup to run. Eristavi preserves one stable primary checked failure and deterministic secondary cleanup context without adding exception-style syntax or composite error machinery to the language surface.
