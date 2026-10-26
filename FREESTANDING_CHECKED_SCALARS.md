# Freestanding checked scalar runtime

> **Status: stacked runtime-independence review candidate; Linux x86-64 only**

This slice begins the value-runtime migration without changing Eristavi source
syntax, public types, fault semantics or design philosophy. It deliberately stays
below managed `ev_value`/GC allocation: the operations work on compiler-private
machine words and return private status codes.

Ordinary Eristavi still has checked signed `Int`, `Bool`, no pointer syntax, no
manual allocation API, no ownership annotations and no unchecked integer mode.

## Frozen operator mapping

The helper dispatcher follows the existing compiler mapping:

```text
binary: 0 +, 1 -, 2 *, 3 /, 4 %, 5 ==, 6 !=, 7 <, 8 <=, 9 >, 10 >=
unary:  0 checked Int negation, 1 Bool not
```

The private ABI is:

```text
rax = result word
rdx = status
      0 success
      1 signed Int overflow
      2 Int division by zero
      3 Int remainder by zero
      4 invalid internal operator
```

These statuses are runtime implementation details. They are **not** Eristavi
`fails` values and do not alter the locked distinction between arithmetic defects
and checked application failures.

## Integer behavior

`src/runtime/scalar_x86_64.eri` emits checked x86-64 operations directly:

- negation uses the CPU overflow flag;
- addition/subtraction/multiplication use signed overflow detection;
- division and remainder reject zero divisors;
- the signed-minimum / `-1` pair is rejected as overflow for both `/` and `%`;
- signed `idiv` gives the locked truncation-toward-zero quotient;
- the remainder therefore follows the dividend sign as required by the frozen
  remainder specification;
- comparisons produce normalized `0`/`1` Bool words;
- Bool `not` produces normalized `0`/`1`.

No C arithmetic, compiler builtin, libc math helper or host-language integer
semantics participate in the generated target operations.

## Freestanding fault path

`src/runtime/linux_x86_64.eri` now also emits `erist_rt_write_all`, a private
Linux `write(2)` syscall loop that retries `EINTR`, handles partial writes and
returns a negative Linux errno on failure.

`src/runtime/scalar_fault_x86_64.eri` maps private scalar status codes to runtime
fault messages and terminates through the existing direct `exit` syscall helper.
It does not call libc `write`, `fprintf`, `exit` or a dynamic loader.

The overflow probe verifies the observable target behavior:

```text
stderr: Eristavi runtime fault: Int arithmetic overflow\n
exit status: 1
```

The generated target has no unresolved imports, interpreter or dynamic section.

## Focused validation

The scalar probe covers successful and faulting operations including:

- signed add/subtract/multiply;
- signed division and remainder;
- checked negation;
- Bool not;
- signed comparisons;
- maximum-plus-one overflow;
- minimum-minus-one overflow;
- multiplication overflow;
- negating signed minimum;
- division by zero;
- remainder by zero;
- signed minimum divided/remaindered by `-1`;
- invalid internal operator status.

The focused runtime-independence stack also reruns the freestanding page,
allocator, verified-memory-lowering and reservation-aware free-list probes.

## What this does not claim

This is not yet a replacement for `evn_int`, `evn_bool`, `evn_unary` or
`evn_binary` in the existing managed native runtime. Those helpers allocate or
return managed `ev_value` slots and participate in the current scope/GC ABI.
Replacing them before the value/slot representation is independently owned would
reintroduce the bootstrap cycle.

The C runtime's `ev_value` layout must therefore be matched or deliberately
replaced together with its slot/scope ABI before these raw scalar operations are
wired into the managed compiler path.

GNU `as` and `ld` remain the explicit assembly/link boundary at this stage, and
the Eristavi generator still runs on the qualified bootstrap runtime.

## Next boundary

The next slice should define and verify the freestanding scalar `ev_value`/slot
layout and implement the scalar native helper ABI over the owned allocator and
this checked scalar engine. Only after that is proven should the existing managed
compiler path stop linking the corresponding C scalar helpers.
