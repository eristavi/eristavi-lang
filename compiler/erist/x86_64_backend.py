from __future__ import annotations

import hashlib
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
    UType,
    UValue,
    identity_inner,
    is_value_composite,
    list_inner,
    maybe_inner,
    nominal_name,
)


class X86_64LinuxBackend:
    """Direct x86-64 System V backend for Universal IR.

    Every Universal-IR value occupies one machine-word stack slot. Scalars are
    stored directly; Text and heap-backed language values use typed pointers.
    Composite ordinary values are cloned by explicit Universal-IR operations,
    while identity handles remain shared. The backend therefore implements a
    representation contract rather than deciding Eristavi value semantics.
    """

    GP_ARGS = ("%rdi", "%rsi", "%rdx", "%rcx", "%r8", "%r9")
    XMM_ARGS = tuple(f"%xmm{i}" for i in range(8))
    CALLEE_SAVED = ("%rbx", "%r12", "%r13", "%r14", "%r15")

    def __init__(self):
        self.fn: UFunction | None = None
        self.lines: list[str] = []
        self.label_counter = 0
        self.text_labels: dict[str, str] = {}
        self.type_defs: dict[str, UType] = {}
        self.saved_offsets: dict[str, int] = {}
        self.clone_types: set[str] = set()
        self.equal_types: set[str] = set()

    @staticmethod
    def _safe(name: str) -> str:
        return re.sub(r"[^A-Za-z0-9_]", "_", name)

    def _symbol(self, name: str) -> str:
        return "main" if name == "__entry" else f"eri_fn_{self._safe(name)}"

    def _block_label(self, name: str) -> str:
        assert self.fn is not None
        return f".Leri_{self._safe(self.fn.name)}_{self._safe(name)}"

    @staticmethod
    def _type_key(type_name: str) -> str:
        return hashlib.sha1(type_name.encode("utf-8")).hexdigest()[:12]

    def _clone_symbol(self, type_name: str) -> str:
        return f".Leri_clone_{self._type_key(type_name)}"

    def _eq_symbol(self, type_name: str) -> str:
        return f".Leri_eq_{self._type_key(type_name)}"

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

    def _type_children(self, type_name: str) -> list[str]:
        if type_name.startswith("maybe<"):
            return [maybe_inner(type_name)]
        if type_name.startswith("list<"):
            return [list_inner(type_name)]
        if type_name.startswith("nominal<"):
            item = self.type_defs.get(nominal_name(type_name))
            if item is None:
                raise ValueError(f"x86-64 backend has no layout for {type_name}")
            return [field.type_name for field in item.fields]
        return []

    def _collect_helpers(self, program: UProgram) -> None:
        clone: set[str] = set()
        equal: set[str] = set()
        for fn in program.functions:
            for block in fn.blocks:
                for ins in block.instructions:
                    if ins.op == "clone_value":
                        clone.add(str(ins.immediate))
                    if ins.op in ("value_eq", "value_ne"):
                        equal.add(str(ins.immediate))

        changed = True
        while changed:
            changed = False
            for type_name in list(clone):
                for child in self._type_children(type_name):
                    if is_value_composite(child) and child not in clone:
                        clone.add(child); changed = True
            for type_name in list(equal):
                for child in self._type_children(type_name):
                    if child not in equal:
                        equal.add(child); changed = True
        self.clone_types = clone
        self.equal_types = equal

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
            ".Leri_bounds:", '    .ascii "Eristavi runtime fault: List index out of bounds\\n"',
            ".Leri_bounds_end:",
            ".Leri_absent:", '    .ascii "Eristavi runtime fault: absent maybe value\\n"',
            ".Leri_absent_end:",
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
        self.type_defs = {item.name: item for item in program.types}
        self._collect_text_constants(program)
        self._collect_helpers(program)
        self.lines = []
        self.label_counter = 0
        self._emit_rodata()
        self.lines.append(".text")
        for fn in program.functions:
            self._function(fn)
        self._emit_runtime_helpers()
        self._fault_runtime()
        self.lines.extend(['.section .note.GNU-stack,"",@progbits', ""])
        return "\n".join(self.lines)

    def _function(self, fn: UFunction) -> None:
        self.fn = fn
        symbol = self._symbol(fn.name)
        total_slots = len(fn.locals) + fn.value_count
        save_count = len(self.CALLEE_SAVED)
        frame = (((total_slots + save_count) * 8 + 15) // 16) * 16
        self.saved_offsets = {
            register: -8 * (total_slots + index + 1)
            for index, register in enumerate(self.CALLEE_SAVED)
        }
        self.lines.extend([f".globl {symbol}", f".type {symbol},@function", f"{symbol}:", "    pushq %rbp", "    movq %rsp, %rbp"])
        if frame:
            self.lines.append(f"    subq ${frame}, %rsp")
        for register in self.CALLEE_SAVED:
            self.lines.append(f"    movq {register}, {self.saved_offsets[register]}(%rbp)")

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

    def _restore_saved(self) -> None:
        for register in reversed(self.CALLEE_SAVED):
            self.lines.append(f"    movq {self.saved_offsets[register]}(%rbp), {register}")

    def _fault_runtime(self) -> None:
        self._fault(".Leri_fault_overflow", ".Leri_overflow", ".Leri_overflow_end")
        self._fault(".Leri_fault_divzero", ".Leri_divzero", ".Leri_divzero_end")
        self._fault(".Leri_fault_bounds", ".Leri_bounds", ".Leri_bounds_end")
        self._fault(".Leri_fault_absent", ".Leri_absent", ".Leri_absent_end")

    def _fault(self, label: str, message: str, end: str) -> None:
        self.lines.extend([
            f"{label}:",
            "    movl $2, %edi",
            f"    leaq {message}(%rip), %rsi",
            f"    movl $({end}-{message}), %edx",
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
            self._restore_saved()
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

    def _bounds_check(self, list_register: str, index_register: str) -> None:
        self.lines.extend([
            f"    testq {index_register}, {index_register}",
            "    js .Leri_fault_bounds",
            f"    cmpq 0({list_register}), {index_register}",
            "    jae .Leri_fault_bounds",
        ])

    def _field_index(self, ins: UInstruction) -> int:
        if not isinstance(ins.immediate, dict) or "index" not in ins.immediate:
            raise ValueError(f"{ins.op} is missing field metadata")
        return int(ins.immediate["index"])

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
        if op == "clone_value":
            type_name = str(ins.immediate)
            self._load(ins.args[0], "%rdi")
            self.lines.append(f"    call {self._clone_symbol(type_name)}")
            self._store_result(ins); return
        if op == "make_struct":
            size = max(8, len(ins.args) * 8)
            self.lines.extend([f"    movl ${size}, %edi", "    call malloc@PLT", "    movq %rax, %r12"])
            for index, value in enumerate(ins.args):
                self._load(value, "%rax")
                self.lines.append(f"    movq %rax, {index * 8}(%r12)")
            self.lines.append("    movq %r12, %rax")
            self._store_result(ins); return
        if op == "get_field":
            index = self._field_index(ins)
            self._load(ins.args[0], "%rax")
            self.lines.append(f"    movq {index * 8}(%rax), %rax")
            self._store_result(ins); return
        if op == "set_field":
            index = self._field_index(ins)
            self._load(ins.args[0], "%r12")
            self._load(ins.args[1], "%rax")
            self.lines.append(f"    movq %rax, {index * 8}(%r12)")
            return
        if op == "make_identity":
            self._load(ins.args[0], "%r12")
            self.lines.extend(["    movl $8, %edi", "    call malloc@PLT", "    movq %r12, 0(%rax)"])
            self._store_result(ins); return
        if op == "identity_get":
            self._load(ins.args[0], "%rax")
            self.lines.append("    movq 0(%rax), %rax")
            self._store_result(ins); return
        if op in ("identity_eq", "identity_ne"):
            self._load(ins.args[0], "%rax"); self._load(ins.args[1], "%rcx")
            self.lines.extend(["    cmpq %rcx, %rax", "    sete %al" if op == "identity_eq" else "    setne %al", "    movzbq %al, %rax"])
            self._store_result(ins); return
        if op == "maybe_none":
            self.lines.append("    xorq %rax, %rax")
            self._store_result(ins); return
        if op == "maybe_some":
            self._load(ins.args[0], "%r12")
            self.lines.extend(["    movl $8, %edi", "    call malloc@PLT", "    movq %r12, 0(%rax)"])
            self._store_result(ins); return
        if op == "maybe_get":
            self._load(ins.args[0], "%rax")
            self.lines.extend(["    testq %rax, %rax", "    je .Leri_fault_absent", "    movq 0(%rax), %rax"])
            self._store_result(ins); return
        if op == "make_list":
            count = len(ins.args)
            self.lines.extend(["    movl $24, %edi", "    call malloc@PLT", "    movq %rax, %r12", f"    movq ${count}, 0(%r12)", f"    movq ${count}, 8(%r12)"])
            if count:
                self.lines.extend([f"    movl ${count * 8}, %edi", "    call malloc@PLT", "    movq %rax, 16(%r12)"])
                for index, value in enumerate(ins.args):
                    self._load(value, "%rcx")
                    self.lines.append(f"    movq %rcx, {index * 8}(%rax)")
            else:
                self.lines.append("    movq $0, 16(%r12)")
            self.lines.append("    movq %r12, %rax")
            self._store_result(ins); return
        if op == "list_count":
            self._load(ins.args[0], "%rax")
            self.lines.append("    movq 0(%rax), %rax")
            self._store_result(ins); return
        if op == "list_get":
            self._load(ins.args[0], "%r12"); self._load(ins.args[1], "%rcx")
            self._bounds_check("%r12", "%rcx")
            self.lines.extend(["    movq 16(%r12), %rax", "    movq (%rax,%rcx,8), %rax"])
            self._store_result(ins); return
        if op == "list_set":
            self._load(ins.args[0], "%r12"); self._load(ins.args[1], "%rcx")
            self._bounds_check("%r12", "%rcx")
            self._load(ins.args[2], "%rdx")
            self.lines.extend(["    movq 16(%r12), %rax", "    movq %rdx, (%rax,%rcx,8)"])
            return
        if op == "list_add":
            self._load(ins.args[0], "%r12"); self._load(ins.args[1], "%r13")
            self.lines.extend(["    movq 0(%r12), %r14", "    movq 8(%r12), %r15", "    cmpq %r15, %r14"])
            unique = self.label_counter; self.label_counter += 1
            ready = f".Leri_list_ready_{unique}"; nonzero = f".Leri_list_cap_nonzero_{unique}"
            self.lines.append(f"    jl {ready}")
            self.lines.extend(["    testq %r15, %r15", f"    jne {nonzero}", "    movq $4, %rbx", f"    jmp {nonzero}_go", f"{nonzero}:", "    leaq (%r15,%r15), %rbx", f"{nonzero}_go:", "    movq 16(%r12), %rdi", "    leaq (,%rbx,8), %rsi", "    call realloc@PLT", "    movq %rax, 16(%r12)", "    movq %rbx, 8(%r12)", f"{ready}:", "    movq 16(%r12), %rax", "    movq %r13, (%rax,%r14,8)", "    incq %r14", "    movq %r14, 0(%r12)"])
            return
        if op in ("value_eq", "value_ne"):
            type_name = str(ins.immediate)
            self._load(ins.args[0], "%rdi"); self._load(ins.args[1], "%rsi")
            self.lines.append(f"    call {self._eq_symbol(type_name)}")
            if op == "value_ne": self.lines.append("    xorq $1, %rax")
            self._store_result(ins); return
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
            self._load(ins.args[0], "%rdi"); self._load(ins.args[1], "%rsi")
            self.lines.append(f"    call {self._eq_symbol(TEXT)}")
            if op == "text_ne": self.lines.append("    xorq $1, %rax")
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

    def _emit_runtime_helpers(self) -> None:
        # Text equality is also used by the scalar Text comparison operations.
        self.equal_types.add(TEXT)
        for type_name in sorted(self.clone_types):
            self._emit_clone_helper(type_name)
        for type_name in sorted(self.equal_types):
            self._emit_eq_helper(type_name)

    def _helper_prologue(self, label: str, frame: int = 0) -> None:
        self.lines.extend([f"{label}:", "    pushq %rbp", "    movq %rsp, %rbp"])
        if frame:
            frame = ((frame + 15) // 16) * 16
            self.lines.append(f"    subq ${frame}, %rsp")

    def _helper_return(self) -> None:
        self.lines.extend(["    leave", "    ret"])

    def _emit_clone_helper(self, type_name: str) -> None:
        label = self._clone_symbol(type_name)
        if type_name.startswith("maybe<"):
            inner = maybe_inner(type_name)
            self._helper_prologue(label, 16)
            self.lines.extend(["    movq %rdi, -8(%rbp)", "    testq %rdi, %rdi"])
            none = label + "_none"; done = label + "_done"
            self.lines.append(f"    je {none}")
            self.lines.extend(["    movl $8, %edi", "    call malloc@PLT", "    movq %rax, -16(%rbp)", "    movq -8(%rbp), %rcx", "    movq 0(%rcx), %rax"])
            if is_value_composite(inner):
                self.lines.extend(["    movq %rax, %rdi", f"    call {self._clone_symbol(inner)}"])
            self.lines.extend(["    movq -16(%rbp), %rcx", "    movq %rax, 0(%rcx)", "    movq %rcx, %rax", f"    jmp {done}", f"{none}:", "    xorq %rax, %rax", f"{done}:"])
            self._helper_return(); return
        if type_name.startswith("list<"):
            inner = list_inner(type_name)
            self._helper_prologue(label, 48)
            loop = label + "_loop"; done = label + "_done"
            self.lines.extend(["    movq %rdi, -8(%rbp)", "    movq 0(%rdi), %rax", "    movq %rax, -24(%rbp)", "    movq 16(%rdi), %rax", "    movq %rax, -32(%rbp)", "    movl $24, %edi", "    call malloc@PLT", "    movq %rax, -16(%rbp)", "    movq -24(%rbp), %rcx", "    movq %rcx, 0(%rax)", "    movq %rcx, 8(%rax)", "    leaq (,%rcx,8), %rdi", "    call malloc@PLT", "    movq %rax, -40(%rbp)", "    movq -16(%rbp), %rcx", "    movq %rax, 16(%rcx)", "    movq $0, -48(%rbp)", f"{loop}:", "    movq -48(%rbp), %rcx", "    cmpq -24(%rbp), %rcx", f"    jae {done}", "    movq -32(%rbp), %rax", "    movq (%rax,%rcx,8), %rax"])
            if is_value_composite(inner):
                self.lines.extend(["    movq %rax, %rdi", f"    call {self._clone_symbol(inner)}", "    movq -48(%rbp), %rcx"])
            self.lines.extend(["    movq -40(%rbp), %rdx", "    movq %rax, (%rdx,%rcx,8)", "    incq -48(%rbp)", f"    jmp {loop}", f"{done}:", "    movq -16(%rbp), %rax"])
            self._helper_return(); return
        if type_name.startswith("nominal<"):
            item = self.type_defs[nominal_name(type_name)]
            self._helper_prologue(label, 16)
            self.lines.extend(["    movq %rdi, -8(%rbp)", f"    movl ${max(8, len(item.fields) * 8)}, %edi", "    call malloc@PLT", "    movq %rax, -16(%rbp)"])
            for index, field in enumerate(item.fields):
                self.lines.extend(["    movq -8(%rbp), %rcx", f"    movq {index * 8}(%rcx), %rax"])
                if is_value_composite(field.type_name):
                    self.lines.extend(["    movq %rax, %rdi", f"    call {self._clone_symbol(field.type_name)}"])
                self.lines.extend(["    movq -16(%rbp), %rcx", f"    movq %rax, {index * 8}(%rcx)"])
            self.lines.append("    movq -16(%rbp), %rax")
            self._helper_return(); return
        raise ValueError(f"clone helper requested for non-composite type {type_name}")

    def _emit_eq_helper(self, type_name: str) -> None:
        label = self._eq_symbol(type_name)
        if type_name in (I64, BOOL) or type_name.startswith("identity<") or type_name.startswith("resource<"):
            self.lines.extend([f"{label}:", "    cmpq %rsi, %rdi", "    sete %al", "    movzbq %al, %rax", "    ret"]); return
        if type_name == F64:
            self.lines.extend([f"{label}:", "    movq %rdi, %xmm0", "    movq %rsi, %xmm1", "    ucomisd %xmm1, %xmm0", "    sete %al", "    setnp %cl", "    andb %cl, %al", "    movzbq %al, %rax", "    ret"]); return
        if type_name == TEXT:
            self._helper_prologue(label)
            unequal = label + "_unequal"; done = label + "_done"
            self.lines.extend(["    movq 0(%rdi), %rdx", "    cmpq 0(%rsi), %rdx", f"    jne {unequal}", "    leaq 8(%rdi), %rdi", "    leaq 8(%rsi), %rsi", "    call memcmp@PLT", "    testl %eax, %eax", "    sete %al", "    movzbq %al, %rax", f"    jmp {done}", f"{unequal}:", "    xorq %rax, %rax", f"{done}:"])
            self._helper_return(); return
        if type_name.startswith("maybe<"):
            inner = maybe_inner(type_name)
            self._helper_prologue(label, 16)
            both_none = label + "_both_none"; false = label + "_false"; done = label + "_done"; present = label + "_present"
            self.lines.extend(["    movq %rdi, -8(%rbp)", "    movq %rsi, -16(%rbp)", "    testq %rdi, %rdi", f"    jne {present}", "    testq %rsi, %rsi", f"    je {both_none}", f"    jmp {false}", f"{present}:", "    testq %rsi, %rsi", f"    je {false}", "    movq -8(%rbp), %rax", "    movq 0(%rax), %rdi", "    movq -16(%rbp), %rax", "    movq 0(%rax), %rsi", f"    call {self._eq_symbol(inner)}", f"    jmp {done}", f"{both_none}:", "    movq $1, %rax", f"    jmp {done}", f"{false}:", "    xorq %rax, %rax", f"{done}:"])
            self._helper_return(); return
        if type_name.startswith("nominal<"):
            item = self.type_defs[nominal_name(type_name)]
            self._helper_prologue(label, 16)
            false = label + "_false"; done = label + "_done"
            self.lines.extend(["    movq %rdi, -8(%rbp)", "    movq %rsi, -16(%rbp)"])
            for index, field in enumerate(item.fields):
                self.lines.extend(["    movq -8(%rbp), %rax", f"    movq {index * 8}(%rax), %rdi", "    movq -16(%rbp), %rax", f"    movq {index * 8}(%rax), %rsi", f"    call {self._eq_symbol(field.type_name)}", "    testq %rax, %rax", f"    je {false}"])
            self.lines.extend(["    movq $1, %rax", f"    jmp {done}", f"{false}:", "    xorq %rax, %rax", f"{done}:"])
            self._helper_return(); return
        if type_name.startswith("list<"):
            inner = list_inner(type_name)
            self._helper_prologue(label, 40)
            false = label + "_false"; loop = label + "_loop"; done = label + "_done"
            self.lines.extend(["    movq %rdi, -8(%rbp)", "    movq %rsi, -16(%rbp)", "    movq 0(%rdi), %rax", "    cmpq 0(%rsi), %rax", f"    jne {false}", "    movq %rax, -24(%rbp)", "    movq $0, -32(%rbp)", f"{loop}:", "    movq -32(%rbp), %rcx", "    cmpq -24(%rbp), %rcx", f"    jae {done}", "    movq -8(%rbp), %rax", "    movq 16(%rax), %rax", "    movq (%rax,%rcx,8), %rdi", "    movq -16(%rbp), %rax", "    movq 16(%rax), %rax", "    movq (%rax,%rcx,8), %rsi", f"    call {self._eq_symbol(inner)}", "    testq %rax, %rax", f"    je {false}", "    incq -32(%rbp)", f"    jmp {loop}", f"{done}:", "    movq $1, %rax", "    leave", "    ret", f"{false}:", "    xorq %rax, %rax"])
            self._helper_return(); return
        raise ValueError(f"equality helper requested for unsupported type {type_name}")
