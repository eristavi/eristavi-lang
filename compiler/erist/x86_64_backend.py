from __future__ import annotations

import re

from .universal_ir import (
    BOOL,
    I64,
    UBlock,
    UBranch,
    UFunction,
    UInstruction,
    UJump,
    UProgram,
    UReturn,
    UValue,
)


class X86_64LinuxBackend:
    """First direct Eristavi CPU backend.

    It consumes Universal IR and emits x86-64 System V assembly directly.
    The system assembler/linker and libc are still used for object/link steps and
    bootstrap textual output, but C is not part of this path.
    """

    def __init__(self):
        self.fn: UFunction | None = None
        self.lines: list[str] = []
        self.label_counter = 0

    @staticmethod
    def _safe(name: str) -> str:
        return re.sub(r"[^A-Za-z0-9_]", "_", name)

    def _block_label(self, name: str) -> str:
        return f".Leri_{self._safe(name)}"

    def _value_offset(self, value: UValue) -> int:
        assert self.fn is not None
        return -8 * (len(self.fn.locals) + value.id + 1)

    @staticmethod
    def _local_offset(local_id: int) -> int:
        return -8 * (local_id + 1)

    def _load(self, value: UValue, register: str = "%rax") -> None:
        self.lines.append(f"    movq {self._value_offset(value)}(%rbp), {register}")

    def _store_result(self, instruction: UInstruction, register: str = "%rax") -> None:
        if instruction.result is None:
            raise ValueError(f"x86-64 instruction {instruction.op} unexpectedly has no result")
        self.lines.append(f"    movq {register}, {self._value_offset(instruction.result)}(%rbp)")

    def emit(self, program: UProgram) -> str:
        if len(program.functions) != 1 or program.functions[0].name != program.entry:
            raise ValueError("first x86-64 backend currently expects one universal entry function")
        self.fn = program.functions[0]
        fn = self.fn
        total_slots = len(fn.locals) + fn.value_count
        frame = ((total_slots * 8 + 15) // 16) * 16
        self.lines = [
            ".section .rodata",
            ".Leri_fmt_i64:",
            '    .string "%ld\\n"',
            ".Leri_true:",
            '    .string "true"',
            ".Leri_false:",
            '    .string "false"',
            ".Leri_overflow:",
            '    .ascii "Eristavi runtime fault: Int arithmetic overflow\\n"',
            ".Leri_overflow_end:",
            ".Leri_divzero:",
            '    .ascii "Eristavi runtime fault: Int division by zero\\n"',
            ".Leri_divzero_end:",
            ".text",
            ".globl main",
            ".type main,@function",
            "main:",
            "    pushq %rbp",
            "    movq %rsp, %rbp",
        ]
        if frame:
            self.lines.append(f"    subq ${frame}, %rsp")
        # Fall through into the first block.
        for block in fn.blocks:
            self._block(block)
        self.lines.extend(
            [
                ".Leri_fault_overflow:",
                "    movl $2, %edi",
                "    leaq .Leri_overflow(%rip), %rsi",
                "    movl $(.Leri_overflow_end-.Leri_overflow), %edx",
                "    call write@PLT",
                "    movl $1, %eax",
                "    leave",
                "    ret",
                ".Leri_fault_divzero:",
                "    movl $2, %edi",
                "    leaq .Leri_divzero(%rip), %rsi",
                "    movl $(.Leri_divzero_end-.Leri_divzero), %edx",
                "    call write@PLT",
                "    movl $1, %eax",
                "    leave",
                "    ret",
                ".size main,.-main",
                '.section .note.GNU-stack,"",@progbits',
                "",
            ]
        )
        return "\n".join(self.lines)

    def _block(self, block: UBlock) -> None:
        self.lines.append(f"{self._block_label(block.name)}:")
        for instruction in block.instructions:
            self._instruction(instruction)
        term = block.terminator
        if isinstance(term, UJump):
            self.lines.append(f"    jmp {self._block_label(term.target)}")
        elif isinstance(term, UBranch):
            self._load(term.condition)
            self.lines.extend(
                [
                    "    testq %rax, %rax",
                    f"    jne {self._block_label(term.true_target)}",
                    f"    jmp {self._block_label(term.false_target)}",
                ]
            )
        elif isinstance(term, UReturn):
            if term.value is not None:
                self._load(term.value)
            else:
                self.lines.append("    xorl %eax, %eax")
            self.lines.extend(["    leave", "    ret"])
        else:
            raise ValueError(f"x86-64 block {block.name!r} has invalid terminator")

    def _instruction(self, ins: UInstruction) -> None:
        op = ins.op
        if op in ("const_i64", "const_bool"):
            value = int(bool(ins.immediate)) if op == "const_bool" else int(ins.immediate)
            self.lines.append(f"    movabsq ${value}, %rax")
            self._store_result(ins)
            return
        if op == "load_local":
            if ins.local is None:
                raise ValueError("load_local missing local id")
            self.lines.append(f"    movq {self._local_offset(ins.local)}(%rbp), %rax")
            self._store_result(ins)
            return
        if op == "store_local":
            if ins.local is None or len(ins.args) != 1:
                raise ValueError("store_local is malformed")
            self._load(ins.args[0])
            self.lines.append(f"    movq %rax, {self._local_offset(ins.local)}(%rbp)")
            return
        if op == "neg_checked":
            self._load(ins.args[0])
            self.lines.extend(["    negq %rax", "    jo .Leri_fault_overflow"])
            self._store_result(ins)
            return
        if op in ("add_checked", "sub_checked", "mul_checked"):
            self._load(ins.args[0], "%rax")
            self._load(ins.args[1], "%rcx")
            mnemonic = {"add_checked": "addq", "sub_checked": "subq", "mul_checked": "imulq"}[op]
            self.lines.extend([f"    {mnemonic} %rcx, %rax", "    jo .Leri_fault_overflow"])
            self._store_result(ins)
            return
        if op in ("div_checked", "rem_checked"):
            self._load(ins.args[0], "%rax")
            self._load(ins.args[1], "%rcx")
            unique = self.label_counter
            self.label_counter += 1
            ok = f".Leri_div_ok_{unique}"
            self.lines.extend(
                [
                    "    testq %rcx, %rcx",
                    "    je .Leri_fault_divzero",
                    "    cmpq $-1, %rcx",
                    f"    jne {ok}",
                    "    movabsq $-9223372036854775808, %rdx",
                    "    cmpq %rdx, %rax",
                    "    je .Leri_fault_overflow",
                    f"{ok}:",
                    "    cqto",
                    "    idivq %rcx",
                ]
            )
            self._store_result(ins, "%rdx" if op == "rem_checked" else "%rax")
            return
        if op == "bool_not":
            self._load(ins.args[0])
            self.lines.extend(["    testq %rax, %rax", "    sete %al", "    movzbq %al, %rax"])
            self._store_result(ins)
            return
        if op in ("cmp_eq", "cmp_ne", "cmp_lt", "cmp_le", "cmp_gt", "cmp_ge"):
            self._load(ins.args[0], "%rax")
            self._load(ins.args[1], "%rcx")
            setcc = {
                "cmp_eq": "sete",
                "cmp_ne": "setne",
                "cmp_lt": "setl",
                "cmp_le": "setle",
                "cmp_gt": "setg",
                "cmp_ge": "setge",
            }[op]
            self.lines.extend(["    cmpq %rcx, %rax", f"    {setcc} %al", "    movzbq %al, %rax"])
            self._store_result(ins)
            return
        if op == "output_i64":
            self._load(ins.args[0], "%rsi")
            self.lines.extend(
                [
                    "    leaq .Leri_fmt_i64(%rip), %rdi",
                    "    xorl %eax, %eax",
                    "    call printf@PLT",
                ]
            )
            return
        if op == "output_bool":
            self._load(ins.args[0])
            unique = self.label_counter
            self.label_counter += 1
            false_label = f".Leri_bool_false_{unique}"
            ready = f".Leri_bool_ready_{unique}"
            self.lines.extend(
                [
                    "    testq %rax, %rax",
                    f"    je {false_label}",
                    "    leaq .Leri_true(%rip), %rdi",
                    f"    jmp {ready}",
                    f"{false_label}:",
                    "    leaq .Leri_false(%rip), %rdi",
                    f"{ready}:",
                    "    call puts@PLT",
                ]
            )
            return
        raise ValueError(f"x86-64 backend does not support universal op {op!r}")
