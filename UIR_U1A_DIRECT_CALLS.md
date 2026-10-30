# U1a direct-call declaration and structural verification slice

Status: proposed, *not qualified or merged*. Base is merged strict Float on `main`; main remains the existing production compiler. This is a first **representation/verification** increment of issue #71, not its completed execution/effect gate.

## Owned function declarations

`meta.FunctionId` is a nominal owned ID in the shared immutable metadata. `metadata.declarations` uses fixed six-word rows: SignatureId, logical symbol UTF-8 byte-range, defined/imported kind, conservative effect bitmask, and selected import contract version. A separate `symbolBytes` table never aliases source identity/digest bytes. Function symbols are unique, nonempty, UTF-8, and at most 1024 bytes; functions are bounded to 65536 per module-program. Effects use closed bits: read=1, write=2, external=4, allocation=8, terminal-trap=16, divergence=32. Defined records have version 0, imported records require positive version.

This representation is *not* a proof that an imported native function fulfills the declared effect contract, nor a final trusted import-resolution mechanism. For safety, every call is conservatively observable until verified whole-program effect closure and trusted contract validation are implemented.

## Direct call opcode

Private op 34 `call.direct` stores FunctionId as an instruction attribute, not a guessed helper-name string. It uses **exact ordered** parameter/result TypeIds from the immutable declaration's SignatureId. Zero results produce no fake Void; multiple results produce individual SSA ValueIds. Forward declarations and recursion have stable declaration IDs but still require actual body binding/execution at the next gate. A successful call continues in the block. Traps/divergence and possible I/O are conservative and cannot be discarded because results are unused.

Builder validates owner, call arity, operand types, and result types; independent verifier checks every declaration's symbol table, signature, kind, version/effects, and every live or dead call's target, types, result definitions and attributes. No new native call generator, runtime import lookup, compiler frontend direct binding, trusted versioned imports, interprocedural SCC effect inference, or independent call executor is claimed here.

## Acceptance evidence and next gates

- New `tests/test_u1_calls.py` uses a separately compiled Eristavi probe, checking both two-result and zero-result calls and malformed foreign FunctionId, operand/result typing, import version and repair/reverification.
- Existing foundation tests audit new op 34 as non-cell, non-CFG-terminator, non-inline-edge and conservative effectful.
- Require four-platform CI and full completed-batch qualification before merge. The separate full owned compiler self-build remains unqualified and skipped.
- Finish issue #71 with defined function binding to bodies, recursion and forward resolution, independent multi-function execution oracle, effect propagation over SCCs, runtime/import contract validation, and preserved first-effect/fault order. Add joint SSA promotion and cancellations before proclaiming U1a calls complete.
