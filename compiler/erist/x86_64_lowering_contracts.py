from __future__ import annotations

from dataclasses import dataclass


GP_CALLER_SAVED = frozenset({
    "%rax",
    "%rcx",
    "%rdx",
    "%rsi",
    "%rdi",
    "%r8",
    "%r9",
    "%r10",
    "%r11",
})
XMM_CALLER_SAVED = frozenset(f"%xmm{index}" for index in range(16))


@dataclass(frozen=True)
class X86LoweringContract:
    """Machine-level use/clobber contract for one Universal-IR operation.

    The physical allocator reasons about the composed x86 backend rather than
    assuming a Universal-IR instruction is a single machine instruction.

    `operands_before_clobber` means every source operand has been copied out of
    its allocated location before the lowering reaches any register clobber
    listed by this contract. `scalar_result_register_safe` means a scalar result
    is produced after the lowering's final clobber and can therefore be moved
    into an allocated physical register safely.

    Unknown operations deliberately use the conservative contract below.
    """

    may_call: bool
    operands_before_clobber: bool
    scalar_result_register_safe: bool
    gp_clobbers: frozenset[str]
    xmm_clobbers: frozenset[str]


_CONSERVATIVE = X86LoweringContract(
    may_call=True,
    operands_before_clobber=False,
    scalar_result_register_safe=False,
    gp_clobbers=GP_CALLER_SAVED,
    xmm_clobbers=XMM_CALLER_SAVED,
)


def _pure(
    *,
    gp: frozenset[str] = frozenset(),
    xmm: frozenset[str] = frozenset(),
    result_safe: bool = True,
) -> X86LoweringContract:
    return X86LoweringContract(
        may_call=False,
        operands_before_clobber=True,
        scalar_result_register_safe=result_safe,
        gp_clobbers=gp,
        xmm_clobbers=xmm,
    )


def _call_region(*, result_safe: bool = False) -> X86LoweringContract:
    return X86LoweringContract(
        may_call=True,
        operands_before_clobber=True,
        scalar_result_register_safe=result_safe,
        gp_clobbers=GP_CALLER_SAVED,
        xmm_clobbers=XMM_CALLER_SAVED,
    )


# Contracts here describe the actual composed x86 lowering. Keep this table
# deliberately explicit. Adding an operation to the allocator requires first
# auditing its emitter and any subclass override for calls/scratch registers.
_CONTRACTS: dict[str, X86LoweringContract] = {
    # Scalar constants / lexical loads.
    "const_i64": _pure(gp=frozenset({"%rax"})),
    "const_bool": _pure(gp=frozenset({"%rax"})),
    "const_f64": _pure(gp=frozenset({"%rax"})),
    "load_local": _pure(gp=frozenset({"%rax"})),

    # Checked integer and Bool arithmetic.
    "neg_checked": _pure(gp=frozenset({"%rax"})),
    "add_checked": _pure(gp=frozenset({"%rax", "%rcx"})),
    "sub_checked": _pure(gp=frozenset({"%rax", "%rcx"})),
    "mul_checked": _pure(gp=frozenset({"%rax", "%rcx"})),
    "div_checked": _pure(gp=frozenset({"%rax", "%rcx", "%rdx"})),
    "rem_checked": _pure(gp=frozenset({"%rax", "%rcx", "%rdx"})),
    "bool_not": _pure(gp=frozenset({"%rax"})),
    "cmp_eq": _pure(gp=frozenset({"%rax", "%rcx"})),
    "cmp_ne": _pure(gp=frozenset({"%rax", "%rcx"})),
    "cmp_lt": _pure(gp=frozenset({"%rax", "%rcx"})),
    "cmp_le": _pure(gp=frozenset({"%rax", "%rcx"})),
    "cmp_gt": _pure(gp=frozenset({"%rax", "%rcx"})),
    "cmp_ge": _pure(gp=frozenset({"%rax", "%rcx"})),

    # Float arithmetic. Float comparisons also materialize Bool through GP
    # scratch registers.
    "f64_neg": _pure(xmm=frozenset({"%xmm0"})),
    "f64_add": _pure(xmm=frozenset({"%xmm0", "%xmm1"})),
    "f64_sub": _pure(xmm=frozenset({"%xmm0", "%xmm1"})),
    "f64_mul": _pure(xmm=frozenset({"%xmm0", "%xmm1"})),
    "f64_div": _pure(xmm=frozenset({"%xmm0", "%xmm1"})),
    "f64_cmp_eq": _pure(
        gp=frozenset({"%rax", "%rcx"}),
        xmm=frozenset({"%xmm0", "%xmm1"}),
    ),
    "f64_cmp_ne": _pure(
        gp=frozenset({"%rax", "%rcx"}),
        xmm=frozenset({"%xmm0", "%xmm1"}),
    ),
    "f64_cmp_lt": _pure(
        gp=frozenset({"%rax", "%rcx"}),
        xmm=frozenset({"%xmm0", "%xmm1"}),
    ),
    "f64_cmp_le": _pure(
        gp=frozenset({"%rax", "%rcx"}),
        xmm=frozenset({"%xmm0", "%xmm1"}),
    ),
    "f64_cmp_gt": _pure(
        gp=frozenset({"%rax", "%rcx"}),
        xmm=frozenset({"%xmm0", "%xmm1"}),
    ),
    "f64_cmp_ge": _pure(
        gp=frozenset({"%rax", "%rcx"}),
        xmm=frozenset({"%xmm0", "%xmm1"}),
    ),

    # Call-free scalar extraction lowerings audited in x86_64_backend.py.
    "get_field": _pure(gp=frozenset({"%rax"})),
    "identity_get": _pure(gp=frozenset({"%rax"})),
    "maybe_get": _pure(gp=frozenset({"%rax"})),
    "list_count": _pure(gp=frozenset({"%rax"})),
    "list_get": _pure(gp=frozenset({"%rax", "%rcx", "%r12"})),

    # Checked-state scalar queries are call-free in the checked backend.
    "zero_value": _pure(gp=frozenset({"%rax"})),
    "error_pending": _pure(gp=frozenset({"%rax"})),
    "error_matches": _pure(gp=frozenset({"%rax", "%rcx"})),

    # These composed lowerings consume their scalar inputs before the call or
    # GC safe point, so a dead-after-use operand may remain register-resident.
    "store_local": _call_region(result_safe=False),
    "output_i64": _call_region(result_safe=False),
    "output_bool": _call_region(result_safe=False),
    "output_f64": _call_region(result_safe=False),
    "output_text": _call_region(result_safe=False),

    # Function arguments are fully marshalled before the call; a scalar result
    # is copied into its allocated location after the call returns.
    "call": _call_region(result_safe=True),
}


def x86_lowering_contract(op: str) -> X86LoweringContract:
    """Return the audited x86 lowering contract or a conservative fallback."""

    return _CONTRACTS.get(op, _CONSERVATIVE)
