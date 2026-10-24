# Eristavi Universal IR

> **Status: First executable lower-IR slice implemented**

Eristavi now has two distinct IR levels.

```text
Eristavi source
    ↓
semantic analysis
    ↓
typed/source-close Eristavi IR
    ↓
Universal IR
    ↓
target backend
```

The distinction is intentional. The typed IR retains high-level Eristavi concepts useful for semantics and portable backends. Universal IR makes control flow and primitive operations explicit enough for direct machine-code backends.

## Current model

The first Universal IR slice contains:

- explicit basic blocks;
- virtual typed values;
- explicit local slots;
- `jump` and conditional `branch` terminators;
- explicit `return` terminators;
- signed 64-bit integer and Boolean primitive values;
- checked integer arithmetic operations;
- integer comparisons;
- Boolean negation;
- primitive textual-output operations for Int/Bool.

Representative operations include:

```text
const_i64
const_bool
load_local
store_local
add_checked
sub_checked
mul_checked
div_checked
rem_checked
neg_checked
cmp_eq / cmp_ne / cmp_lt / cmp_le / cmp_gt / cmp_ge
bool_not
output_i64
output_bool
```

A source loop therefore no longer reaches a direct CPU backend as a C-style `while` expression. It becomes explicit blocks and branches.

## Current lowering boundary

The first executable slice lowers:

- Int/Bool locals;
- assignment;
- checked integer arithmetic;
- comparisons;
- `if / else`;
- `while`;
- Int/Bool `output`.

It deliberately rejects features not yet represented at this level, including higher-level aggregates, checked failures, resources, Text, Float, general function calls and short-circuit Boolean operators.

Those features remain supported through the broader typed-IR/C backend. Rejecting an unsupported Universal-IR lowering is preferable to changing Eristavi semantics for backend convenience.

## Direct x86-64 backend

The first direct CPU backend consumes Universal IR and emits x86-64 System V assembly for Linux.

```text
.eri
 ↓
frontend
 ↓
typed IR
 ↓
Universal IR
 ↓
x86-64 assembly
 ↓
system assembler/linker
 ↓
native executable
```

No generated C source participates in this route.

The bootstrap backend currently uses libc for basic output/linking and a simple stack-spill strategy for virtual values. Those are implementation choices, not Eristavi language semantics.

## Why x86-64 first

The original architecture intentionally did not freeze the first CPU backend. x86-64 Linux was selected for the first executable direct slice because the project CI can assemble, link and execute it immediately on hosted Linux runners.

This does not privilege x86-64 in the language model. ARM64 and other native backends must consume the same target-neutral semantics rather than introduce architecture-specific language behavior.

## Next IR work

Future Universal-IR growth should add semantic capability in layers:

1. function ABI/calls and short-circuit control flow;
2. Float and Text/runtime values;
3. aggregates, Lists, optionals and identities;
4. checked-failure edges and deterministic cleanup;
5. runtime/GC operations and target-independent layout metadata;
6. optimization passes only after correctness boundaries are stable.
