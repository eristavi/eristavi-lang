from __future__ import annotations

from .ir import STD_FILE_ERROR
from .universal_ir import UInstruction
from .x86_64_checked_backend import X86_64CheckedLinuxBackend


class X86_64ResourceLinuxBackend(X86_64CheckedLinuxBackend):
    """Direct x86-64 std.files runtime for resource-aware Universal IR."""

    def _emit_rodata(self) -> None:
        super()._emit_rodata()
        self.lines.extend([
            ".section .rodata",
            ".Leri_mode_readwrite:", '    .string "r+"',
            ".Leri_mode_write:", '    .string "w+"',
            ".Leri_path_nul_message:", '    .string "file path contains NUL"',
            ".Leri_utf8_message:", '    .string "invalid UTF-8"',
            ".Leri_closed_message:", '    .ascii "Eristavi runtime fault: file resource is closed\\n"',
            ".Leri_closed_message_end:",
            ".section .bss",
            ".align 8",
            ".Leri_error_secondary_head:", "    .quad 0",
            ".Leri_error_secondary_tail:", "    .quad 0",
        ])

    def _instruction(self, ins: UInstruction) -> None:
        op = ins.op
        if op == "error_clear":
            super()._instruction(ins)
            self.lines.extend([
                "    movq $0, .Leri_error_secondary_head(%rip)",
                "    movq $0, .Leri_error_secondary_tail(%rip)",
            ])
            return
        if op == "set_error":
            super()._instruction(ins)
            self.lines.extend([
                "    movq $0, .Leri_error_secondary_head(%rip)",
                "    movq $0, .Leri_error_secondary_tail(%rip)",
            ])
            return
        if op == "file_open":
            self._load(ins.args[0], "%rdi")
            self.lines.append("    call .Leri_file_open")
            self._store_result(ins)
            return
        if op == "file_read_text":
            self._load(ins.args[0], "%rdi")
            self.lines.append("    call .Leri_file_read_text")
            self._store_result(ins)
            return
        if op == "file_write_text":
            self._load(ins.args[0], "%rdi")
            self._load(ins.args[1], "%rsi")
            self.lines.append("    call .Leri_file_write_text")
            return
        if op == "file_exists":
            self._load(ins.args[0], "%rdi")
            self.lines.append("    call .Leri_file_exists")
            self._store_result(ins)
            return
        if op == "file_remove":
            self._load(ins.args[0], "%rdi")
            self.lines.append("    call .Leri_file_remove")
            return
        if op == "resource_cleanup":
            self._load(ins.args[0], "%rdi")
            self.lines.append("    call .Leri_file_cleanup")
            return
        super()._instruction(ins)

    def _emit_runtime_helpers(self) -> None:
        super()._emit_runtime_helpers()
        self._emit_file_runtime()

    def _emit_file_runtime(self) -> None:
        error_label = self._error_type_label(STD_FILE_ERROR)
        self.lines.extend([
            # Convert NUL-terminated libc text into an Eristavi length-aware Text.
            ".Leri_text_from_c:",
            "    pushq %rbp", "    movq %rsp, %rbp", "    subq $32, %rsp",
            "    movq %rdi, -8(%rbp)",
            "    call strlen@PLT", "    movq %rax, -16(%rbp)",
            "    leaq 8(%rax), %rdi", "    call malloc@PLT", "    movq %rax, -24(%rbp)",
            "    movq -16(%rbp), %rcx", "    movq %rcx, 0(%rax)",
            "    leaq 8(%rax), %rdi", "    movq -8(%rbp), %rsi", "    movq %rcx, %rdx", "    call memcpy@PLT",
            "    movq -24(%rbp), %rax", "    leave", "    ret",

            # Install a FileError as primary, or append it as secondary while a
            # previous checked failure is already unwinding.
            ".Leri_set_file_error:",
            "    pushq %rbp", "    movq %rsp, %rbp", "    subq $48, %rsp",
            "    movq %rsi, -8(%rbp)", "    call .Leri_text_from_c", "    movq %rax, -16(%rbp)",
            "    movl $16, %edi", "    call malloc@PLT", "    movq %rax, -24(%rbp)",
            "    movq -16(%rbp), %rcx", "    movq %rcx, 0(%rax)",
            "    movq -8(%rbp), %rcx", "    movq %rcx, 8(%rax)",
            "    cmpq $0, .Leri_error_value(%rip)", "    jne .Leri_file_error_secondary",
            "    movq %rax, .Leri_error_value(%rip)",
            f"    leaq {error_label}(%rip), %rcx", "    movq %rcx, .Leri_error_type(%rip)",
            "    movq -16(%rbp), %rcx", "    movq %rcx, .Leri_error_message(%rip)",
            "    leave", "    ret",
            ".Leri_file_error_secondary:",
            "    movq %rax, -32(%rbp)", "    movl $32, %edi", "    call malloc@PLT", "    movq %rax, -40(%rbp)",
            "    movq -32(%rbp), %rcx", "    movq %rcx, 0(%rax)",
            f"    leaq {error_label}(%rip), %rcx", "    movq %rcx, 8(%rax)",
            "    movq -16(%rbp), %rcx", "    movq %rcx, 16(%rax)", "    movq $0, 24(%rax)",
            "    movq .Leri_error_secondary_tail(%rip), %rcx", "    testq %rcx, %rcx", "    je .Leri_secondary_first",
            "    movq %rax, 24(%rcx)", "    jmp .Leri_secondary_store_tail",
            ".Leri_secondary_first:", "    movq %rax, .Leri_error_secondary_head(%rip)",
            ".Leri_secondary_store_tail:", "    movq %rax, .Leri_error_secondary_tail(%rip)", "    leave", "    ret",

            # Convert Eristavi Text to a temporary C path, rejecting embedded NUL.
            ".Leri_text_to_path:",
            "    pushq %rbp", "    movq %rsp, %rbp", "    subq $32, %rsp", "    movq %rdi, -8(%rbp)",
            "    movq 0(%rdi), %rcx", "    xorq %rdx, %rdx",
            ".Leri_path_scan:", "    cmpq %rcx, %rdx", "    jae .Leri_path_copy",
            "    cmpb $0, 8(%rdi,%rdx)", "    je .Leri_path_nul", "    incq %rdx", "    jmp .Leri_path_scan",
            ".Leri_path_nul:", "    leaq .Leri_path_nul_message(%rip), %rdi", "    movq -8(%rbp), %rsi", "    call .Leri_set_file_error", "    xorq %rax, %rax", "    leave", "    ret",
            ".Leri_path_copy:", "    movq %rcx, -16(%rbp)", "    leaq 1(%rcx), %rdi", "    call malloc@PLT", "    movq %rax, -24(%rbp)",
            "    movq %rax, %rdi", "    movq -8(%rbp), %rsi", "    addq $8, %rsi", "    movq -16(%rbp), %rdx", "    call memcpy@PLT",
            "    movq -24(%rbp), %rax", "    movq -16(%rbp), %rcx", "    movb $0, (%rax,%rcx)", "    leave", "    ret",

            # Set FileError from current errno. rdi = Eristavi path.
            ".Leri_file_errno:",
            "    pushq %rbp", "    movq %rsp, %rbp", "    subq $16, %rsp", "    movq %rdi, -8(%rbp)",
            "    call __errno_location@PLT", "    movl (%rax), %edi", "    call strerror@PLT",
            "    movq %rax, %rdi", "    movq -8(%rbp), %rsi", "    call .Leri_set_file_error", "    leave", "    ret",

            ".Leri_file_open:",
            "    pushq %rbp", "    movq %rsp, %rbp", "    subq $32, %rsp", "    movq %rdi, -8(%rbp)",
            "    call .Leri_text_to_path", "    testq %rax, %rax", "    je .Leri_file_open_fail", "    movq %rax, -16(%rbp)",
            "    movq %rax, %rdi", "    leaq .Leri_mode_readwrite(%rip), %rsi", "    call fopen@PLT", "    testq %rax, %rax", "    je .Leri_file_open_errno", "    movq %rax, -24(%rbp)",
            "    movl $16, %edi", "    call malloc@PLT", "    movq -24(%rbp), %rcx", "    movq %rcx, 0(%rax)", "    movq -8(%rbp), %rcx", "    movq %rcx, 8(%rax)", "    leave", "    ret",
            ".Leri_file_open_errno:", "    movq -8(%rbp), %rdi", "    call .Leri_file_errno",
            ".Leri_file_open_fail:", "    xorq %rax, %rax", "    leave", "    ret",

            # UTF-8 validator: rdi=data, rsi=len -> rax bool.
            ".Leri_utf8_valid:",
            "    xorq %rcx, %rcx",
            ".Leri_utf8_loop:", "    cmpq %rsi, %rcx", "    jae .Leri_utf8_yes", "    movzbl (%rdi,%rcx), %eax", "    cmpb $0x80, %al", "    jb .Leri_utf8_one",
            "    cmpb $0xC2, %al", "    jb .Leri_utf8_no", "    cmpb $0xDF, %al", "    jbe .Leri_utf8_two", "    cmpb $0xEF, %al", "    jbe .Leri_utf8_three", "    cmpb $0xF4, %al", "    jbe .Leri_utf8_four", "    jmp .Leri_utf8_no",
            ".Leri_utf8_one:", "    incq %rcx", "    jmp .Leri_utf8_loop",
            ".Leri_utf8_two:", "    leaq 1(%rcx), %rdx", "    cmpq %rsi, %rdx", "    jae .Leri_utf8_no", "    movzbl 1(%rdi,%rcx), %edx", "    andl $0xC0, %edx", "    cmpl $0x80, %edx", "    jne .Leri_utf8_no", "    addq $2, %rcx", "    jmp .Leri_utf8_loop",
            ".Leri_utf8_three:", "    leaq 2(%rcx), %rdx", "    cmpq %rsi, %rdx", "    jae .Leri_utf8_no", "    movzbl 1(%rdi,%rcx), %edx", "    movzbl 2(%rdi,%rcx), %r8d", "    movl %r8d, %r9d", "    andl $0xC0, %r9d", "    cmpl $0x80, %r9d", "    jne .Leri_utf8_no", "    cmpb $0xE0, %al", "    jne .Leri_utf8_three_ed", "    cmpl $0xA0, %edx", "    jb .Leri_utf8_no", "    cmpl $0xBF, %edx", "    ja .Leri_utf8_no", "    jmp .Leri_utf8_three_ok", ".Leri_utf8_three_ed:", "    cmpb $0xED, %al", "    jne .Leri_utf8_three_general", "    cmpl $0x80, %edx", "    jb .Leri_utf8_no", "    cmpl $0x9F, %edx", "    ja .Leri_utf8_no", "    jmp .Leri_utf8_three_ok", ".Leri_utf8_three_general:", "    andl $0xC0, %edx", "    cmpl $0x80, %edx", "    jne .Leri_utf8_no", ".Leri_utf8_three_ok:", "    addq $3, %rcx", "    jmp .Leri_utf8_loop",
            ".Leri_utf8_four:", "    leaq 3(%rcx), %rdx", "    cmpq %rsi, %rdx", "    jae .Leri_utf8_no", "    movzbl 1(%rdi,%rcx), %edx", "    movzbl 2(%rdi,%rcx), %r8d", "    movzbl 3(%rdi,%rcx), %r9d", "    movl %r8d, %r10d", "    andl $0xC0, %r10d", "    cmpl $0x80, %r10d", "    jne .Leri_utf8_no", "    movl %r9d, %r10d", "    andl $0xC0, %r10d", "    cmpl $0x80, %r10d", "    jne .Leri_utf8_no", "    cmpb $0xF0, %al", "    jne .Leri_utf8_four_f4", "    cmpl $0x90, %edx", "    jb .Leri_utf8_no", "    cmpl $0xBF, %edx", "    ja .Leri_utf8_no", "    jmp .Leri_utf8_four_ok", ".Leri_utf8_four_f4:", "    cmpb $0xF4, %al", "    jne .Leri_utf8_four_general", "    cmpl $0x80, %edx", "    jb .Leri_utf8_no", "    cmpl $0x8F, %edx", "    ja .Leri_utf8_no", "    jmp .Leri_utf8_four_ok", ".Leri_utf8_four_general:", "    andl $0xC0, %edx", "    cmpl $0x80, %edx", "    jne .Leri_utf8_no", ".Leri_utf8_four_ok:", "    addq $4, %rcx", "    jmp .Leri_utf8_loop",
            ".Leri_utf8_yes:", "    movl $1, %eax", "    ret", ".Leri_utf8_no:", "    xorl %eax, %eax", "    ret",

            ".Leri_file_read_text:",
            "    pushq %rbp", "    movq %rsp, %rbp", "    subq $64, %rsp", "    movq %rdi, -8(%rbp)", "    movq 0(%rdi), %rdi", "    testq %rdi, %rdi", "    je .Leri_file_closed_fault",
            "    xorl %esi, %esi", "    movl $2, %edx", "    call fseek@PLT", "    testl %eax, %eax", "    jne .Leri_file_read_errno", "    movq -8(%rbp), %rax", "    movq 0(%rax), %rdi", "    call ftell@PLT", "    testq %rax, %rax", "    js .Leri_file_read_errno", "    movq %rax, -16(%rbp)", "    movq -8(%rbp), %rax", "    movq 0(%rax), %rdi", "    call rewind@PLT",
            "    movq -16(%rbp), %rax", "    addq $8, %rax", "    movq %rax, %rdi", "    call malloc@PLT", "    movq %rax, -24(%rbp)", "    movq $0, 0(%rax)",
            "    leaq 8(%rax), %rdi", "    movl $1, %esi", "    movq -16(%rbp), %rdx", "    movq -8(%rbp), %rax", "    movq 0(%rax), %rcx", "    call fread@PLT", "    movq %rax, -32(%rbp)", "    movq -24(%rbp), %rcx", "    movq %rax, 0(%rcx)",
            "    leaq 8(%rcx), %rdi", "    movq %rax, %rsi", "    call .Leri_utf8_valid", "    testq %rax, %rax", "    je .Leri_file_read_utf8", "    movq -24(%rbp), %rax", "    leave", "    ret",
            ".Leri_file_read_utf8:", "    leaq .Leri_utf8_message(%rip), %rdi", "    movq -8(%rbp), %rax", "    movq 8(%rax), %rsi", "    call .Leri_set_file_error", "    xorq %rax, %rax", "    leave", "    ret",
            ".Leri_file_read_errno:", "    movq -8(%rbp), %rax", "    movq 8(%rax), %rdi", "    call .Leri_file_errno", "    xorq %rax, %rax", "    leave", "    ret",

            ".Leri_file_write_text:",
            "    pushq %rbp", "    movq %rsp, %rbp", "    subq $48, %rsp", "    movq %rdi, -8(%rbp)", "    movq %rsi, -16(%rbp)", "    movq 0(%rdi), %rax", "    testq %rax, %rax", "    je .Leri_file_closed_fault",
            "    movq 8(%rdi), %rdi", "    call .Leri_text_to_path", "    testq %rax, %rax", "    je .Leri_file_write_done", "    movq %rax, %rdi", "    leaq .Leri_mode_write(%rip), %rsi", "    movq -8(%rbp), %rax", "    movq 0(%rax), %rdx", "    call freopen@PLT", "    testq %rax, %rax", "    je .Leri_file_write_errno", "    movq -8(%rbp), %rcx", "    movq %rax, 0(%rcx)",
            "    movq -16(%rbp), %rcx", "    leaq 8(%rcx), %rdi", "    movl $1, %esi", "    movq 0(%rcx), %rdx", "    movq %rax, %rcx", "    call fwrite@PLT", "    movq -16(%rbp), %rcx", "    cmpq 0(%rcx), %rax", "    jne .Leri_file_write_errno", "    movq -8(%rbp), %rax", "    movq 0(%rax), %rdi", "    call fflush@PLT", "    testl %eax, %eax", "    jne .Leri_file_write_errno", "    movq -8(%rbp), %rax", "    movq 0(%rax), %rdi", "    call rewind@PLT", ".Leri_file_write_done:", "    leave", "    ret",
            ".Leri_file_write_errno:", "    movq -8(%rbp), %rax", "    movq 8(%rax), %rdi", "    call .Leri_file_errno", "    leave", "    ret",

            ".Leri_file_cleanup:",
            "    pushq %rbp", "    movq %rsp, %rbp", "    subq $16, %rsp", "    testq %rdi, %rdi", "    je .Leri_file_cleanup_done", "    movq %rdi, -8(%rbp)", "    movq 0(%rdi), %rdi", "    testq %rdi, %rdi", "    je .Leri_file_cleanup_done", "    call fclose@PLT", "    movq -8(%rbp), %rcx", "    movq $0, 0(%rcx)", "    testl %eax, %eax", "    je .Leri_file_cleanup_done", "    movq 8(%rcx), %rdi", "    call .Leri_file_errno", ".Leri_file_cleanup_done:", "    leave", "    ret",

            ".Leri_file_exists:",
            "    pushq %rbp", "    movq %rsp, %rbp", "    subq $24, %rsp", "    movq %rdi, -8(%rbp)", "    call .Leri_text_to_path", "    testq %rax, %rax", "    je .Leri_file_exists_false", "    movq %rax, %rdi", "    xorl %esi, %esi", "    call access@PLT", "    testl %eax, %eax", "    je .Leri_file_exists_true", "    call __errno_location@PLT", "    cmpl $2, (%rax)", "    je .Leri_file_exists_false", "    movq -8(%rbp), %rdi", "    call .Leri_file_errno", ".Leri_file_exists_false:", "    xorl %eax, %eax", "    leave", "    ret", ".Leri_file_exists_true:", "    movl $1, %eax", "    leave", "    ret",

            ".Leri_file_remove:",
            "    pushq %rbp", "    movq %rsp, %rbp", "    subq $16, %rsp", "    movq %rdi, -8(%rbp)", "    call .Leri_text_to_path", "    testq %rax, %rax", "    je .Leri_file_remove_done", "    movq %rax, %rdi", "    call remove@PLT", "    testl %eax, %eax", "    je .Leri_file_remove_done", "    movq -8(%rbp), %rdi", "    call .Leri_file_errno", ".Leri_file_remove_done:", "    leave", "    ret",

            ".Leri_file_closed_fault:",
            "    movl $2, %edi", "    leaq .Leri_closed_message(%rip), %rsi", "    movl $(.Leri_closed_message_end-.Leri_closed_message), %edx", "    call write@PLT", "    movl $1, %edi", "    call exit@PLT", "    ud2",
        ])
