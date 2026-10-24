from __future__ import annotations

import re
import struct

from .universal_ir import (
    BOOL,
    F64,
    I64,
    TEXT,
    VOID,
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
    """Direct x86-64 System V backend for Universal IR.

    The backend uses explicit stack slots for virtual values.  This is not an
    optimization strategy; it is a deliberately simple, auditable bootstrap ABI
    implementation.  Eristavi calls follow the platform ABI at the machine
    boundary while Universal IR remains target-neutral.
    """

    GP_ARGS = ("%rdi", "%rsi", "%rdx", "%rcx", "%r8", "%r9")
    XMM_ARGS = tuple(f"%xmm{i}" for i in range(8))

    def __init__(self):
        self.fn: UFunction | None = None
        self.lines: list[str] = []
        self.label_counter = 0
        self.text_labels: dict[str, str] = {}

    @staticmethod
    def _safe(name: str) -> str:
        return re.sub(r"[^A-Za-z0-9_]", "_", name)

    def _symbol(self, name: str) -> str:
        return "main" if name == "__entry" else f"eri_fn_{self._safe(name)}"

    def _block_label(self, name: str) -> str:
        assert self.fn is not None
        return f".Leri_{self._safe(self.fn.name)}_{self._safe(name)}"

    def _value_offset(self, value: UValue) -> int:
        assert self.fn is not None
        return -8 * (len(self.fn.locals) + value.id + 1)

    @staticmethod
    def _local_offset(local_id: int) -> int:
        return -8 * (local_id + 1)

    def _load(self, value: UValue, register: str = "%rax") -> None:
        self.lines.append(f"    movq {self._value_offset(value)}(%rbp), {register}")

    def _load_f64(self, value: UValue, register: str = "%xmm0") -> None:
        self.lines.append(f"    movsd {self._value_offset(value)}(%rbp), {register}")

    def _store_result(self, instruction: UInstruction, register: str = "%rax") -> None:
        if instruction.result is None:
            raise ValueError(f"x86-64 instruction {instruction.op} unexpectedly has no result")
        self.lines.append(f"    movq {register}, {self._value_offset(instruction.result)}(%rbp)")

    def _store_result_f64(self, instruction: UInstruction, register: str = "%xmm0") -> None:
        if instruction.result is None:
            raise ValueError(f"x86-64 instruction {instruction.op} unexpectedly has no result")
        self.lines.append(f"    movsd {register}, {self._value_offset(instruction.result)}(%rbp)")

    @staticmethod
    def _arg_locations(types: list[str]):
        gp = 0
        xmm = 0
        stack = 0
        out = []
        for t in types:
            if t == F64 and xmm < 8:
                out.append(("xmm", xmm)); xmm += 1
            elif t != F64 and gp < 6:
                out.append(("gp", gp)); gp += 1
            else:
                out.append(("stack", stack)); stack += 1
        return out, stack

    def _collect_text_constants(self, program: UProgram) -> None:
        self.text_labels = {}
        for fn in program.functions:
            for block in fn.blocks:
                for ins in block.instructions:
                    if ins.op == "const_text":
                        text = str(ins.immediate)
                        if text not in self.text_labels:
                            self.text_labels[text] = f".Leri_text_{len(self.text_labels)}"

    def _emit_rodata(self) -> None:
        self.lines.extend([
            ".section .rodata",
            ".Leri_fmt_i64:", '    .string "%ld\\n"',
            ".Leri_fmt_f64:", '    .string "%.17g\\n"',
            ".Leri_true:", '    .string "true"',
            ".Leri_false:", '    .string "false"',
            ".Leri_newline:", '    .byte 10',
            ".Leri_overflow:", '    .ascii "Eristavi runtime fault: Int arithmetic overflow\\n"',
            ".Leri_overflow_end:",
            ".Leri_divzero:", '    .ascii "Eristavi runtime fault: Int division by zero\\n"',
            ".Leri_divzero_end:",
            ".Leri_f64_sign:", "    .quad 0x8000000000000000",
        ])
        for text, label in self.text_labels.items():
            data = text.encode("utf-8")
            self.lines.append(f"{label}:")
            self.lines.append(f"    .quad {len(data)}")
            if data:
                self.lines.append("    .byte " + ", ".join(str(b) for b in data))

    def emit(self, program: UProgram) -> str:
        if not any(fn.name == program.entry for fn in program.functions):
            raise ValueError("universal program has no entry function")
        self._collect_text_constants(program)
        self.lines = []
        self.label_counter = 0
        self._emit_rodata()
        self.lines.append(".text")
        for fn in program.functions:
            self._function(fn)
        self._fault_runtime()
        self.lines.extend(['.section .note.GNU-stack,"",@progbits', ""])
        return "\n".join(self.lines)

    def _function(self, fn: UFunction) -> None:
        self.fn = fn
        symbol = self._symbol(fn.name)
        total_slots = len(fn.locals) + fn.value_count
        frame = ((total_slots * 8 + 15) // 16) * 16
        self.lines.extend([f".globl {symbol}", f".type {symbol},@function", f"{symbol}:", "    pushq %rbp", "    movq %rsp, %rbp"])
        if frame:
            self.lines.append(f"    subq ${frame}, %rsp")

        locations, _ = self._arg_locations([p.type_name for p in fn.parameters])
        for param, (kind, index) in zip(fn.parameters, locations):
            dst = self._local_offset(param.id)
            if kind == "gp":
                self.lines.append(f"    movq {self.GP_ARGS[index]}, {dst}(%rbp)")
            elif kind == "xmm":
                self.lines.append(f"    movsd {self.XMM_ARGS[index]}, {dst}(%rbp)")
            else:
                src = 16 + index * 8
                self.lines.append(f"    movq {src}(%rbp), %rax")
                self.lines.append(f"    movq %rax, {dst}(%rbp)")

        for block in fn.blocks:
            self._block(block)
        self.lines.append(f".size {symbol},.-{symbol}")

    def _fault_runtime(self) -> None:
        self.lines.extend([
            ".Leri_fault_overflow:",
            "    movl $2, %edi",
            "    leaq .Leri_overflow(%rip), %rsi",
            "    movl $(.Leri_overflow_end-.Leri_overflow), %edx",
            "    call write@PLT",
            "    movl $1, %edi",
            "    call exit@PLT",
            "    ud2",
            ".Leri_fault_divzero:",
            "    movl $2, %edi",
            "    leaq .Leri_divzero(%rip), %rsi",
            "    movl $(.Leri_divzero_end-.Leri_divzero), %edx",
            "    call write@PLT",
            "    movl $1, %edi",
            "    call exit@PLT",
            "    ud2",
        ])

    def _block(self, block: UBlock) -> None:
        self.lines.append(f"{self._block_label(block.name)}:")
        for instruction in block.instructions:
            self._instruction(instruction)
        term = block.terminator
        if isinstance(term, UJump):
            self.lines.append(f"    jmp {self._block_label(term.target)}")
        elif isinstance(term, UBranch):
            self._load(term.condition)
            self.lines.extend(["    testq %rax, %rax", f"    jne {self._block_label(term.true_target)}", f"    jmp {self._block_label(term.false_target)}"])
        elif isinstance(term, UReturn):
            if term.value is not None:
                if term.value.type_name == F64:
                    self._load_f64(term.value, "%xmm0")
                else:
                    self._load(term.value, "%rax")
            elif self.fn is not None and self.fn.name == "__entry":
                self.lines.append("    xorl %eax, %eax")
            self.lines.extend(["    leave", "    ret"])
        else:
            raise ValueError(f"x86-64 block {block.name!r} has invalid terminator")

    def _call(self, ins: UInstruction) -> None:
        name = str(ins.immediate)
        types = [v.type_name for v in ins.args]
        locations, stack_count = self._arg_locations(types)
        stack_args = [(v, loc[1]) for v, loc in zip(ins.args, locations) if loc[0] == "stack"]
        pad = 8 if stack_count % 2 else 0
        if pad:
            self.lines.append("    subq $8, %rsp")
        for value, _ in reversed(stack_args):
            self._load(value, "%rax")
            self.lines.append("    pushq %rax")
        for value, (kind, index) in zip(ins.args, locations):
            if kind == "gp":
                self._load(value, self.GP_ARGS[index])
            elif kind == "xmm":
                self._load_f64(value, self.XMM_ARGS[index])
        self.lines.append(f"    call {self._symbol(name)}")
        cleanup = stack_count * 8 + pad
        if cleanup:
            self.lines.append(f"    addq ${cleanup}, %rsp")
        if ins.result is not None:
            if ins.result.type_name == F64:
                self._store_result_f64(ins, "%xmm0")
            else:
                self._store_result(ins, "%rax")

    def _instruction(self, ins: UInstruction) -> None:
        op = ins.op
        if op in ("const_i64", "const_bool"):
            value = int(bool(ins.immediate)) if op == "const_bool" else int(ins.immediate)
            self.lines.append(f"    movabsq ${value}, %rax")
            self._store_result(ins); return
        if op == "const_f64":
            bits = struct.unpack("<Q", struct.pack("<d", float(ins.immediate)))[0]
            self.lines.append(f"    movabsq ${bits}, %rax")
            self._store_result(ins); return
        if op == "const_text":
            label = self.text_labels[str(ins.immediate)]
            self.lines.append(f"    leaq {label}(%rip), %rax")
            self._store_result(ins); return
        if op == "load_local":
            if ins.local is None: raise ValueError("load_local missing local id")
            self.lines.append(f"    movq {self._local_offset(ins.local)}(%rbp), %rax")
            self._store_result(ins); return
        if op == "store_local":
            if ins.local is None or len(ins.args) != 1: raise ValueError("store_local is malformed")
            self._load(ins.args[0])
            self.lines.append(f"    movq %rax, {self._local_offset(ins.local)}(%rbp)")
            return
        if op == "call":
            self._call(ins); return
        if op == "neg_checked":
            self._load(ins.args[0]); self.lines.extend(["    negq %rax", "    jo .Leri_fault_overflow"]); self._store_result(ins); return
        if op in ("add_checked", "sub_checked", "mul_checked"):
            self._load(ins.args[0], "%rax"); self._load(ins.args[1], "%rcx")
            mnemonic = {"add_checked": "addq", "sub_checked": "subq", "mul_checked": "imulq"}[op]
            self.lines.extend([f"    {mnemonic} %rcx, %rax", "    jo .Leri_fault_overflow"]); self._store_result(ins); return
        if op in ("div_checked", "rem_checked"):
            self._load(ins.args[0], "%rax"); self._load(ins.args[1], "%rcx")
            unique = self.label_counter; self.label_counter += 1; ok = f".Leri_div_ok_{unique}"
            self.lines.extend(["    testq %rcx, %rcx", "    je .Leri_fault_divzero", "    cmpq $-1, %rcx", f"    jne {ok}", "    movabsq $-9223372036854775808, %rdx", "    cmpq %rdx, %rax", "    je .Leri_fault_overflow", f"{ok}:", "    cqto", "    idivq %rcx"])
            self._store_result(ins, "%rdx" if op == "rem_checked" else "%rax"); return
        if op == "bool_not":
            self._load(ins.args[0]); self.lines.extend(["    testq %rax, %rax", "    sete %al", "    movzbq %al, %rax"]); self._store_result(ins); return
        if op in ("cmp_eq", "cmp_ne", "cmp_lt", "cmp_le", "cmp_gt", "cmp_ge"):
            self._load(ins.args[0], "%rax"); self._load(ins.args[1], "%rcx")
            setcc = {"cmp_eq":"sete","cmp_ne":"setne","cmp_lt":"setl","cmp_le":"setle","cmp_gt":"setg","cmp_ge":"setge"}[op]
            self.lines.extend(["    cmpq %rcx, %rax", f"    {setcc} %al", "    movzbq %al, %rax"]); self._store_result(ins); return
        if op == "f64_neg":
            self._load_f64(ins.args[0]); self.lines.append("    xorpd .Leri_f64_sign(%rip), %xmm0"); self._store_result_f64(ins); return
        if op in ("f64_add", "f64_sub", "f64_mul", "f64_div"):
            self._load_f64(ins.args[0], "%xmm0"); self._load_f64(ins.args[1], "%xmm1")
            mnemonic={"f64_add":"addsd","f64_sub":"subsd","f64_mul":"mulsd","f64_div":"divsd"}[op]
            self.lines.append(f"    {mnemonic} %xmm1, %xmm0"); self._store_result_f64(ins); return
        if op.startswith("f64_cmp_"):
            self._load_f64(ins.args[0], "%xmm0"); self._load_f64(ins.args[1], "%xmm1"); self.lines.append("    ucomisd %xmm1, %xmm0")
            kind=op[8:]
            if kind == "eq": self.lines.extend(["    sete %al", "    setnp %cl", "    andb %cl, %al"])
            elif kind == "ne": self.lines.extend(["    setne %al", "    setp %cl", "    orb %cl, %al"])
            elif kind == "lt": self.lines.extend(["    setb %al", "    setnp %cl", "    andb %cl, %al"])
            elif kind == "le": self.lines.extend(["    setbe %al", "    setnp %cl", "    andb %cl, %al"])
            elif kind == "gt": self.lines.append("    seta %al")
            elif kind == "ge": self.lines.append("    setae %al")
            else: raise ValueError(f"unknown float comparison {op}")
            self.lines.append("    movzbq %al, %rax"); self._store_result(ins); return
        if op == "text_concat":
            self._load(ins.args[0], "%r12"); self._load(ins.args[1], "%r13")
            self.lines.extend(["    movq 0(%r12), %r14", "    movq 0(%r13), %r15", "    leaq 8(%r14,%r15), %rdi", "    call malloc@PLT", "    movq %rax, %rbx", "    leaq (%r14,%r15), %rcx", "    movq %rcx, 0(%rbx)", "    leaq 8(%rbx), %rdi", "    leaq 8(%r12), %rsi", "    movq %r14, %rdx", "    call memcpy@PLT", "    leaq 8(%rbx,%r14), %rdi", "    leaq 8(%r13), %rsi", "    movq %r15, %rdx", "    call memcpy@PLT", "    movq %rbx, %rax"])
            self._store_result(ins); return
        if op in ("text_eq", "text_ne"):
            self._load(ins.args[0], "%r12"); self._load(ins.args[1], "%r13"); unique=self.label_counter; self.label_counter+=1
            unequal=f".Leri_text_unequal_{unique}"; done=f".Leri_text_cmp_done_{unique}"
            self.lines.extend(["    movq 0(%r12), %rdx", "    cmpq 0(%r13), %rdx", f"    jne {unequal}", "    leaq 8(%r12), %rdi", "    leaq 8(%r13), %rsi", "    call memcmp@PLT", "    testl %eax, %eax", "    sete %al", "    movzbq %al, %rax", f"    jmp {done}", f"{unequal}:", "    xorq %rax, %rax", f"{done}:"])
            if op == "text_ne": self.lines.extend(["    xorq $1, %rax"])
            self._store_result(ins); return
        if op == "output_i64":
            self._load(ins.args[0], "%rsi"); self.lines.extend(["    leaq .Leri_fmt_i64(%rip), %rdi", "    xorl %eax, %eax", "    call printf@PLT"]); return
        if op == "output_bool":
            self._load(ins.args[0]); unique=self.label_counter; self.label_counter+=1; false_label=f".Leri_bool_false_{unique}"; ready=f".Leri_bool_ready_{unique}"
            self.lines.extend(["    testq %rax, %rax", f"    je {false_label}", "    leaq .Leri_true(%rip), %rdi", f"    jmp {ready}", f"{false_label}:", "    leaq .Leri_false(%rip), %rdi", f"{ready}:", "    call puts@PLT"]); return
        if op == "output_f64":
            self._load_f64(ins.args[0], "%xmm0"); self.lines.extend(["    leaq .Leri_fmt_f64(%rip), %rdi", "    movl $1, %eax", "    call printf@PLT"]); return
        if op == "output_text":
            self._load(ins.args[0], "%r12"); self.lines.extend(["    movl $1, %edi", "    leaq 8(%r12), %rsi", "    movq 0(%r12), %rdx", "    call write@PLT", "    movl $1, %edi", "    leaq .Leri_newline(%rip), %rsi", "    movl $1, %edx", "    call write@PLT"]); return
        raise ValueError(f"x86-64 backend does not support universal op {op!r}")
