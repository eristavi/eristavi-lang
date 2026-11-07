# Closed checked Function groups

Development contract, 7 November 2026. Extends the opt-in checked native
whole-Function profile; no source syntax, public ABI or default compiler change.

## Meaning

A checked call can name any defined Function in an explicitly supplied closed
set of original canonical bodies. Each body's existing `definedTarget` binds
its exact frozen declaration and normal/failure signature. The original opcode
46 and its typed normal/failure edges remain the only executable call contract.
Direct and mutual recursion use the same native frames, independently verified
SSA roots and caller result/failure handoff as existing self recursion.

No missing body, foreign metadata, duplicate FunctionId, duplicate native label,
imported binding or signature substitution is admitted. Every member, including
unreachable instructions, is independently verified before the first assembly
section is emitted. Each call resolves its original metadata FunctionId to one
member's native label, never by signature similarity. Labels are positive unique
integers; no arbitrary assembly symbol/string is accepted.

The initial group profile retains the existing single exact saved-context
failure carrier per caller and at most two normal results/eight arguments per
callee. Different normal signatures are permitted. General failure construction,
File ownership transfer and nested managed producers remain separate U2 work.
Ordinary value copies still use admitted existing imports; identity is shared.

## Mechanism and cost

Reuse `roots.create`, full `ssa.verifyPublications`, canonical checked-return
verification and the existing emitter. A bounded preflight compiles/verifies each
member without output; an emission pass freshly verifies each member again.
No alternate executable graph, global call registry or persistent verified flag
is created. Resource failure during emission makes the generator fail; partial
stdout from a failed generator is never an accepted artifact.

At most 16 members, 1024 total SSA values and 2048 total instructions; existing
per-body/frame/root caps remain. Resolution is O(member count) per checked call,
charged to the current phase; admission duplicate checks are O(members squared).
Only integer target/label lists span bodies. Plans and temporary verification
phases close after each member, including failure paths. Runtime stack/root
layout is unchanged from the checked Function contract, with no new per-call
heap structure. No whole-compiler speed or total recursion-memory claim follows.

## Evidence required

Execute distinct-target calls and mutual recursion at depths 0/1/5/32/64;
normal/failure propagation, recovery in a different member, differing normal
signatures, managed return handoff, parent-private Text and live saved failures
through forced GC. Check post-scope reclamation and independent source/reference
outcomes. Refuse malformed/dead members, wrong/foreign/missing/duplicate targets,
labels and signatures before output. Preserve legacy self-call tests and the
owned/C byte-identity gate. Record actual scope and remaining physical/fault
limits; keep #111 draft and #74 open pending all U2 acceptance conditions.
