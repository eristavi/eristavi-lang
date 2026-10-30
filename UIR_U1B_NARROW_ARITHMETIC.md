# U1b narrow wrap, overflow and comparison operations

Checkpoint: 2026-10-30. This is an **isolated U1b implementation candidate**, stacked on U1b narrow type/constant integration (PR #84). Governing contracts: `docs/architecture/Eristavi-UIR-U1-Contract-2026-10-29.md`, `LANGUAGE_SEMANTICS.md`, and `CI_QUALIFICATION.md`. It does not introduce new public Eristavi types.

## Private opcode schema

| Opcode | Operation | Inputs | Output |
| --- | --- | --- | --- |
| 37 | `narrow.wrap` | two identical i8/i16/i32 types | same width |
| 38 | `narrow.signed.overflow` | same | width value + pred |
| 39 | `narrow.unsigned.overflow` | same | width value + pred |
| 40 | `narrow.cmp` | same | pred |

For 37–39, payload mode 1 add, 2 subtract, 3 multiply. For 40, payload relation 1 eq, 2 ne, 3 signed lt, 4 le, 5 gt, 6 ge, 7 unsigned lt, 8 le, 9 gt, 10 ge. Instruction `extra` field **must** be width TypeId 4=i8, 5=i16 or 6=i32; operand and result types must equal that ID exactly. No implicit widening, signedness inference or checked source arithmetic is introduced. Opcode numbers are private, not serialized ABI.

Wrapping returns the low W bits interpreted in signed W-bit form. The paired overflow predicate compares the exact **unbounded mathematical** signed or unsigned result to its selected W-bit range. Overflow never produces poison or silently traps. All are pure, nontrapping scalar operations.

## Evidence and limits

- Builder and independent verifier enforce exact modes, width attributes, operand/result types and reachable/unreachable malformed operations.
- `tests/test_u1_promotion.py` independently interprets op37–40 over exact W-bit patterns and checks its separate mathematical oracle for each width across 7×7 boundary pairs, all 3 wrapping modes, signed/unsigned overflow pairs and 10 comparisons. Before/after SSA promotion must match, plus an i8 scalar cell/diamond merge with exactly one inserted parameter/two edge args.
- `tests/fixtures/u1_verifier.eri` mutates operation mode, width, operand/result type, comparison relation and a dead-block instruction. Repaired records must reverify. Existing prior U1a and U1b regression suites remain mandatory.
- Four-platform normal CI and exact-head completed-batch bootstrap/offline + owned integration qualification are required before merging. Do not run the experimental owned self-build by default.

**Not yet implemented:** width-specific signed/unsigned div/rem and exact MIN/-1 faults, immutable aggregate make/get/set, managed Text/List/identity, checked failures, deterministic cleanup, native legalization, production frontend/native execution. These require independently qualified follow-on slices; issue #73 remains open. Do not classify U1b, U2 or the whole redesign as finished from this patch.
