from __future__ import annotations

from .unicode_asm import unicode_asm_tables
from .universal_ir import UInstruction
from .x86_64_resource_backend import X86_64ResourceLinuxBackend


class X86_64DirectLinuxBackend(X86_64ResourceLinuxBackend):
    """Final composed direct x86-64 backend.

    Text output uses raw length-aware writes so embedded NUL remains valid. The
    scalar output helpers use stdio. Flush stdio before a raw Text write so a
    program's observable output order never depends on libc buffering policy.

    Explicit Text views are also native here. Byte/scalar operations decode the
    length-aware UTF-8 representation directly; character operations use pinned
    Unicode 17 property tables and UAX #29 extended-grapheme rules generated
    from the same data source as the reference/C runtimes.
    """

    def __init__(self):
        super().__init__()
        self.needs_text_views = False
        self.unicode_counts = {}

    def emit(self, program):
        self.needs_text_views = any(
            ins.op in ("text_view", "text_view_count", "text_view_index")
            for fn in program.functions
            for block in fn.blocks
            for ins in block.instructions
        )
        return super().emit(program)

    def _emit_rodata(self) -> None:
        super()._emit_rodata()
        if not self.needs_text_views:
            return
        table_lines, counts = unicode_asm_tables()
        self.unicode_counts = counts
        self.lines.extend([
            ".section .rodata",
            ".Leri_text_view_bounds:",
            '    .ascii "Eristavi runtime fault: Text view index out of bounds\\n"',
            ".Leri_text_view_bounds_end:",
            *table_lines,
        ])

    def _fault_runtime(self) -> None:
        super()._fault_runtime()
        if self.needs_text_views:
            self._fault(".Leri_fault_text_view_bounds", ".Leri_text_view_bounds", ".Leri_text_view_bounds_end")

    def _instruction(self, ins: UInstruction) -> None:
        if ins.op == "output_text":
            self.lines.extend([
                "    xorl %edi, %edi",
                "    call fflush@PLT",
            ])
        if ins.op == "text_view":
            self._load(ins.args[0], "%rax")
            self._store_result(ins)
            return
        if ins.op == "text_view_count":
            kind = str(ins.immediate)
            self._load(ins.args[0], "%rdi")
            if kind == "bytes":
                self.lines.append("    movq 0(%rdi), %rax")
            elif kind == "scalars":
                self.lines.append("    call .Leri_text_scalar_count")
            elif kind == "characters":
                self.lines.append("    call .Leri_text_character_count")
            else:
                raise ValueError(f"unknown direct Text view kind {kind!r}")
            self._store_result(ins)
            return
        if ins.op == "text_view_index":
            kind = str(ins.immediate)
            self._load(ins.args[0], "%rdi")
            self._load(ins.args[1], "%rsi")
            if kind == "bytes":
                self.lines.extend([
                    "    testq %rsi, %rsi",
                    "    js .Leri_fault_text_view_bounds",
                    "    cmpq 0(%rdi), %rsi",
                    "    jae .Leri_fault_text_view_bounds",
                    "    movzbq 8(%rdi,%rsi), %rax",
                ])
            elif kind == "scalars":
                self.lines.append("    call .Leri_text_scalar_get")
            elif kind == "characters":
                self.lines.append("    call .Leri_text_character_get")
            else:
                raise ValueError(f"unknown direct Text view kind {kind!r}")
            self._store_result(ins)
            return
        super()._instruction(ins)

    def _emit_runtime_helpers(self) -> None:
        super()._emit_runtime_helpers()
        if self.needs_text_views:
            self._emit_text_view_runtime()

    def _emit_text_view_runtime(self) -> None:
        gcb_count = self.unicode_counts[".Leri_unicode_gcb"]
        incb_count = self.unicode_counts[".Leri_unicode_incb"]
        ep_count = self.unicode_counts[".Leri_unicode_ep"]
        self.lines.extend([
            # Generic binary search over 12-byte Unicode range rows.
            # rdi=table, rsi=count, edx=codepoint -> eax=value or zero.
            ".Leri_unicode_lookup:",
            "    xorq %rcx, %rcx",
            "    movq %rsi, %r8",
            ".Leri_unicode_lookup_loop:",
            "    cmpq %r8, %rcx",
            "    jae .Leri_unicode_lookup_none",
            "    leaq (%rcx,%r8), %rax",
            "    shrq $1, %rax",
            "    leaq (%rax,%rax,2), %r9",
            "    leaq (%rdi,%r9,4), %r9",
            "    cmpl 0(%r9), %edx",
            "    jb .Leri_unicode_lookup_lower",
            "    cmpl 4(%r9), %edx",
            "    ja .Leri_unicode_lookup_higher",
            "    movl 8(%r9), %eax",
            "    ret",
            ".Leri_unicode_lookup_lower:",
            "    movq %rax, %r8",
            "    jmp .Leri_unicode_lookup_loop",
            ".Leri_unicode_lookup_higher:",
            "    leaq 1(%rax), %rcx",
            "    jmp .Leri_unicode_lookup_loop",
            ".Leri_unicode_lookup_none:",
            "    xorl %eax, %eax",
            "    ret",

            ".Leri_gcb:",
            "    movl %edi, %edx",
            "    leaq .Leri_unicode_gcb(%rip), %rdi",
            f"    movl ${gcb_count}, %esi",
            "    jmp .Leri_unicode_lookup",
            ".Leri_incb:",
            "    movl %edi, %edx",
            "    leaq .Leri_unicode_incb(%rip), %rdi",
            f"    movl ${incb_count}, %esi",
            "    jmp .Leri_unicode_lookup",
            ".Leri_ep:",
            "    movl %edi, %edx",
            "    leaq .Leri_unicode_ep(%rip), %rdi",
            f"    movl ${ep_count}, %esi",
            "    jmp .Leri_unicode_lookup",

            # Decode one scalar from an already-valid Eristavi Text.
            # rdi=text, rsi=byte position -> eax=codepoint, rdx=next position.
            ".Leri_text_decode_scalar:",
            "    movzbl 8(%rdi,%rsi), %eax",
            "    cmpl $0x80, %eax",
            "    jb .Leri_decode_one",
            "    cmpl $0xE0, %eax",
            "    jb .Leri_decode_two",
            "    cmpl $0xF0, %eax",
            "    jb .Leri_decode_three",
            "    movl %eax, %ecx", "    andl $7, %ecx", "    shll $18, %ecx",
            "    movzbl 9(%rdi,%rsi), %eax", "    andl $63, %eax", "    shll $12, %eax", "    orl %eax, %ecx",
            "    movzbl 10(%rdi,%rsi), %eax", "    andl $63, %eax", "    shll $6, %eax", "    orl %eax, %ecx",
            "    movzbl 11(%rdi,%rsi), %eax", "    andl $63, %eax", "    orl %ecx, %eax",
            "    leaq 4(%rsi), %rdx", "    ret",
            ".Leri_decode_three:",
            "    movl %eax, %ecx", "    andl $15, %ecx", "    shll $12, %ecx",
            "    movzbl 9(%rdi,%rsi), %eax", "    andl $63, %eax", "    shll $6, %eax", "    orl %eax, %ecx",
            "    movzbl 10(%rdi,%rsi), %eax", "    andl $63, %eax", "    orl %ecx, %eax",
            "    leaq 3(%rsi), %rdx", "    ret",
            ".Leri_decode_two:",
            "    movl %eax, %ecx", "    andl $31, %ecx", "    shll $6, %ecx",
            "    movzbl 9(%rdi,%rsi), %eax", "    andl $63, %eax", "    orl %ecx, %eax",
            "    leaq 2(%rsi), %rdx", "    ret",
            ".Leri_decode_one:",
            "    leaq 1(%rsi), %rdx", "    ret",

            ".Leri_text_scalar_count:",
            "    pushq %rbp", "    movq %rsp, %rbp", "    subq $32, %rsp",
            "    movq %rdi, -8(%rbp)", "    xorq %rax, %rax", "    movq %rax, -16(%rbp)", "    movq %rax, -24(%rbp)",
            ".Leri_scalar_count_loop:",
            "    movq -24(%rbp), %rsi", "    movq -8(%rbp), %rdi", "    cmpq 0(%rdi), %rsi", "    jae .Leri_scalar_count_done",
            "    call .Leri_text_decode_scalar", "    movq %rdx, -24(%rbp)", "    incq -16(%rbp)", "    jmp .Leri_scalar_count_loop",
            ".Leri_scalar_count_done:", "    movq -16(%rbp), %rax", "    leave", "    ret",

            # rdi=text, rsi=start byte, rdx=length -> rax=new length-aware Text.
            ".Leri_text_slice:",
            "    pushq %rbp", "    movq %rsp, %rbp", "    subq $48, %rsp",
            "    movq %rdi, -8(%rbp)", "    movq %rsi, -16(%rbp)", "    movq %rdx, -24(%rbp)",
            "    leaq 8(%rdx), %rdi", "    call malloc@PLT", "    movq %rax, -32(%rbp)",
            "    movq -24(%rbp), %rcx", "    movq %rcx, 0(%rax)",
            "    leaq 8(%rax), %rdi", "    movq -8(%rbp), %rsi", "    addq $8, %rsi", "    addq -16(%rbp), %rsi", "    movq %rcx, %rdx", "    call memcpy@PLT",
            "    movq -32(%rbp), %rax", "    leave", "    ret",

            ".Leri_text_scalar_get:",
            "    testq %rsi, %rsi", "    js .Leri_fault_text_view_bounds",
            "    pushq %rbp", "    movq %rsp, %rbp", "    subq $48, %rsp",
            "    movq %rdi, -8(%rbp)", "    movq %rsi, -16(%rbp)", "    movq $0, -24(%rbp)", "    movq $0, -32(%rbp)",
            ".Leri_scalar_get_loop:",
            "    movq -8(%rbp), %rdi", "    movq -24(%rbp), %rsi", "    cmpq 0(%rdi), %rsi", "    jae .Leri_scalar_get_fault",
            "    movq %rsi, -40(%rbp)", "    call .Leri_text_decode_scalar", "    movq %rdx, -24(%rbp)",
            "    movq -32(%rbp), %rax", "    cmpq -16(%rbp), %rax", "    je .Leri_scalar_get_found", "    incq -32(%rbp)", "    jmp .Leri_scalar_get_loop",
            ".Leri_scalar_get_found:",
            "    movq -24(%rbp), %rdx", "    subq -40(%rbp), %rdx", "    movq -8(%rbp), %rdi", "    movq -40(%rbp), %rsi", "    call .Leri_text_slice", "    leave", "    ret",
            ".Leri_scalar_get_fault:", "    leave", "    jmp .Leri_fault_text_view_bounds",

            # Decode a Text into uint32 scalar and uint64 byte-offset arrays.
            # rdi=text -> rax=cp array, rdx=offset array, rcx=count.
            ".Leri_text_decode_arrays:",
            "    pushq %rbp", "    movq %rsp, %rbp", "    subq $80, %rsp", "    movq %rdi, -8(%rbp)",
            "    call .Leri_text_scalar_count", "    movq %rax, -16(%rbp)",
            "    leaq (,%rax,4), %rdi", "    testq %rdi, %rdi", "    jne .Leri_decode_cp_alloc", "    movl $4, %edi",
            ".Leri_decode_cp_alloc:", "    call malloc@PLT", "    movq %rax, -24(%rbp)",
            "    movq -16(%rbp), %rax", "    leaq 8(,%rax,8), %rdi", "    call malloc@PLT", "    movq %rax, -32(%rbp)",
            "    movq $0, -40(%rbp)", "    movq $0, -48(%rbp)",
            ".Leri_decode_arrays_loop:",
            "    movq -48(%rbp), %rax", "    cmpq -16(%rbp), %rax", "    jae .Leri_decode_arrays_done",
            "    movq -32(%rbp), %rcx", "    movq -40(%rbp), %rdx", "    movq %rdx, (%rcx,%rax,8)",
            "    movq -8(%rbp), %rdi", "    movq -40(%rbp), %rsi", "    call .Leri_text_decode_scalar",
            "    movq -48(%rbp), %rcx", "    movq -24(%rbp), %r8", "    movl %eax, (%r8,%rcx,4)", "    movq %rdx, -40(%rbp)", "    incq -48(%rbp)", "    jmp .Leri_decode_arrays_loop",
            ".Leri_decode_arrays_done:",
            "    movq -32(%rbp), %rax", "    movq -16(%rbp), %rcx", "    movq -40(%rbp), %r8", "    movq %r8, (%rax,%rcx,8)",
            "    movq -24(%rbp), %rax", "    movq -32(%rbp), %rdx", "    movq -16(%rbp), %rcx", "    leave", "    ret",

            # rdi=cp array, rsi=count, rdx=index i (between i-1 and i) -> eax break bool.
            ".Leri_grapheme_break:",
            "    pushq %rbp", "    movq %rsp, %rbp", "    subq $96, %rsp",
            "    movq %rdi, -8(%rbp)", "    movq %rsi, -16(%rbp)", "    movq %rdx, -24(%rbp)",
            "    movl -4(%rdi,%rdx,4), %eax", "    movl %eax, -28(%rbp)",
            "    movl (%rdi,%rdx,4), %eax", "    movl %eax, -32(%rbp)",
            "    movl -28(%rbp), %edi", "    call .Leri_gcb", "    movl %eax, -36(%rbp)",
            "    movl -32(%rbp), %edi", "    call .Leri_gcb", "    movl %eax, -40(%rbp)",
            # GB3
            "    cmpl $1, -36(%rbp)", "    jne .Leri_gb4", "    cmpl $2, -40(%rbp)", "    je .Leri_gb_no",
            # GB4
            ".Leri_gb4:", "    movl -36(%rbp), %eax", "    cmpl $1, %eax", "    je .Leri_gb_yes", "    cmpl $2, %eax", "    je .Leri_gb_yes", "    cmpl $3, %eax", "    je .Leri_gb_yes",
            # GB5
            "    movl -40(%rbp), %eax", "    cmpl $1, %eax", "    je .Leri_gb_yes", "    cmpl $2, %eax", "    je .Leri_gb_yes", "    cmpl $3, %eax", "    je .Leri_gb_yes",
            # GB6
            "    cmpl $9, -36(%rbp)", "    jne .Leri_gb7", "    movl -40(%rbp), %eax", "    cmpl $9, %eax", "    je .Leri_gb_no", "    cmpl $10, %eax", "    je .Leri_gb_no", "    cmpl $12, %eax", "    je .Leri_gb_no", "    cmpl $13, %eax", "    je .Leri_gb_no",
            # GB7
            ".Leri_gb7:", "    movl -36(%rbp), %eax", "    cmpl $12, %eax", "    je .Leri_gb7_left", "    cmpl $10, %eax", "    jne .Leri_gb8", ".Leri_gb7_left:", "    movl -40(%rbp), %eax", "    cmpl $10, %eax", "    je .Leri_gb_no", "    cmpl $11, %eax", "    je .Leri_gb_no",
            # GB8
            ".Leri_gb8:", "    movl -36(%rbp), %eax", "    cmpl $13, %eax", "    je .Leri_gb8_left", "    cmpl $11, %eax", "    jne .Leri_gb9", ".Leri_gb8_left:", "    cmpl $11, -40(%rbp)", "    je .Leri_gb_no",
            # GB9/9a/9b
            ".Leri_gb9:", "    movl -40(%rbp), %eax", "    cmpl $4, %eax", "    je .Leri_gb_no", "    cmpl $5, %eax", "    je .Leri_gb_no", "    cmpl $8, %eax", "    je .Leri_gb_no", "    cmpl $7, -36(%rbp)", "    je .Leri_gb_no",
            # GB9c
            "    movl -32(%rbp), %edi", "    call .Leri_incb", "    cmpl $1, %eax", "    jne .Leri_gb11", "    movq -24(%rbp), %rax", "    movq %rax, -48(%rbp)", "    movq $0, -56(%rbp)",
            ".Leri_gb9c_loop:", "    cmpq $0, -48(%rbp)", "    je .Leri_gb11", "    movq -48(%rbp), %rax", "    decq %rax", "    movq -8(%rbp), %rcx", "    movl (%rcx,%rax,4), %edi", "    call .Leri_incb", "    cmpl $3, %eax", "    je .Leri_gb9c_linker", "    cmpl $2, %eax", "    je .Leri_gb9c_extend", "    jmp .Leri_gb9c_check",
            ".Leri_gb9c_linker:", "    movq $1, -56(%rbp)", ".Leri_gb9c_extend:", "    decq -48(%rbp)", "    jmp .Leri_gb9c_loop",
            ".Leri_gb9c_check:", "    cmpq $0, -56(%rbp)", "    je .Leri_gb11", "    cmpq $0, -48(%rbp)", "    je .Leri_gb11", "    movq -48(%rbp), %rax", "    decq %rax", "    movq -8(%rbp), %rcx", "    movl (%rcx,%rax,4), %edi", "    call .Leri_incb", "    cmpl $1, %eax", "    je .Leri_gb_no",
            # GB11
            ".Leri_gb11:", "    movl -32(%rbp), %edi", "    call .Leri_ep", "    testl %eax, %eax", "    je .Leri_gb12", "    cmpl $5, -36(%rbp)", "    jne .Leri_gb12", "    movq -24(%rbp), %rax", "    cmpq $1, %rax", "    jbe .Leri_gb12", "    subq $2, %rax", "    movq %rax, -48(%rbp)",
            ".Leri_gb11_loop:", "    movq -8(%rbp), %rcx", "    movq -48(%rbp), %rax", "    movl (%rcx,%rax,4), %edi", "    call .Leri_gcb", "    cmpl $4, %eax", "    jne .Leri_gb11_ep", "    cmpq $0, -48(%rbp)", "    je .Leri_gb12", "    decq -48(%rbp)", "    jmp .Leri_gb11_loop",
            ".Leri_gb11_ep:", "    movq -8(%rbp), %rcx", "    movq -48(%rbp), %rax", "    movl (%rcx,%rax,4), %edi", "    call .Leri_ep", "    testl %eax, %eax", "    jne .Leri_gb_no",
            # GB12/13
            ".Leri_gb12:", "    cmpl $6, -36(%rbp)", "    jne .Leri_gb_yes", "    cmpl $6, -40(%rbp)", "    jne .Leri_gb_yes", "    movq -24(%rbp), %rax", "    movq %rax, -48(%rbp)", "    movq $0, -56(%rbp)",
            ".Leri_gbri_loop:", "    cmpq $0, -48(%rbp)", "    je .Leri_gbri_done", "    movq -48(%rbp), %rax", "    decq %rax", "    movq -8(%rbp), %rcx", "    movl (%rcx,%rax,4), %edi", "    call .Leri_gcb", "    cmpl $6, %eax", "    jne .Leri_gbri_done", "    incq -56(%rbp)", "    decq -48(%rbp)", "    jmp .Leri_gbri_loop",
            ".Leri_gbri_done:", "    movq -56(%rbp), %rax", "    andq $1, %rax", "    jne .Leri_gb_no",
            ".Leri_gb_yes:", "    movl $1, %eax", "    leave", "    ret",
            ".Leri_gb_no:", "    xorl %eax, %eax", "    leave", "    ret",

            ".Leri_text_character_count:",
            "    pushq %rbp", "    movq %rsp, %rbp", "    subq $64, %rsp", "    movq %rdi, -8(%rbp)",
            "    call .Leri_text_decode_arrays", "    movq %rax, -16(%rbp)", "    movq %rdx, -24(%rbp)", "    movq %rcx, -32(%rbp)",
            "    testq %rcx, %rcx", "    je .Leri_char_count_zero", "    movq $1, -40(%rbp)", "    movq $1, -48(%rbp)",
            ".Leri_char_count_loop:", "    movq -48(%rbp), %rax", "    cmpq -32(%rbp), %rax", "    jae .Leri_char_count_done", "    movq -16(%rbp), %rdi", "    movq -32(%rbp), %rsi", "    movq %rax, %rdx", "    call .Leri_grapheme_break", "    testl %eax, %eax", "    je .Leri_char_count_next", "    incq -40(%rbp)", ".Leri_char_count_next:", "    incq -48(%rbp)", "    jmp .Leri_char_count_loop",
            ".Leri_char_count_done:", "    movq -16(%rbp), %rdi", "    call free@PLT", "    movq -24(%rbp), %rdi", "    call free@PLT", "    movq -40(%rbp), %rax", "    leave", "    ret",
            ".Leri_char_count_zero:", "    movq -16(%rbp), %rdi", "    call free@PLT", "    movq -24(%rbp), %rdi", "    call free@PLT", "    xorq %rax, %rax", "    leave", "    ret",

            ".Leri_text_character_get:",
            "    testq %rsi, %rsi", "    js .Leri_fault_text_view_bounds",
            "    pushq %rbp", "    movq %rsp, %rbp", "    subq $96, %rsp", "    movq %rdi, -8(%rbp)", "    movq %rsi, -16(%rbp)",
            "    call .Leri_text_decode_arrays", "    movq %rax, -24(%rbp)", "    movq %rdx, -32(%rbp)", "    movq %rcx, -40(%rbp)", "    testq %rcx, %rcx", "    je .Leri_char_get_fault",
            "    movq $0, -48(%rbp)", "    movq $0, -56(%rbp)", "    movq $1, -64(%rbp)",
            ".Leri_char_get_loop:", "    movq -64(%rbp), %rax", "    cmpq -40(%rbp), %rax", "    je .Leri_char_get_boundary", "    movq -24(%rbp), %rdi", "    movq -40(%rbp), %rsi", "    movq %rax, %rdx", "    call .Leri_grapheme_break", "    testl %eax, %eax", "    je .Leri_char_get_next",
            ".Leri_char_get_boundary:", "    movq -48(%rbp), %rax", "    cmpq -16(%rbp), %rax", "    je .Leri_char_get_found", "    incq -48(%rbp)", "    movq -64(%rbp), %rax", "    movq %rax, -56(%rbp)",
            ".Leri_char_get_next:", "    incq -64(%rbp)", "    movq -64(%rbp), %rax", "    cmpq -40(%rbp), %rax", "    jbe .Leri_char_get_loop", "    jmp .Leri_char_get_fault",
            ".Leri_char_get_found:",
            "    movq -32(%rbp), %rcx", "    movq -56(%rbp), %rax", "    movq (%rcx,%rax,8), %rsi", "    movq -64(%rbp), %rax", "    movq (%rcx,%rax,8), %rdx", "    subq %rsi, %rdx", "    movq -8(%rbp), %rdi", "    call .Leri_text_slice", "    movq %rax, -72(%rbp)", "    movq -24(%rbp), %rdi", "    call free@PLT", "    movq -32(%rbp), %rdi", "    call free@PLT", "    movq -72(%rbp), %rax", "    leave", "    ret",
            ".Leri_char_get_fault:", "    movq -24(%rbp), %rdi", "    call free@PLT", "    movq -32(%rbp), %rdi", "    call free@PLT", "    leave", "    jmp .Leri_fault_text_view_bounds",
        ])
