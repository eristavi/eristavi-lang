from __future__ import annotations

import re
import struct

from .universal_ir import (
    BOOL,
    F64,
    I64,
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


class ARM64LinuxBackend:
    """Direct AArch64/AAPCS64 backend for the scalar Universal-IR slice.

    This backend intentionally consumes exactly the same Universal IR used by
    the x86-64 backend.  It currently covers Int/Bool/Float values, functions,
    calls, checked Int arithmetic, branches, loops and scalar output.  Higher
    runtime values remain explicit unsupported operations until their Universal
    IR representation contracts are available.
    """

    GP_ARGS = tuple(f"x{i}" for i in range(8))
    FP_ARGS = tuple(f"d{i}" for i in range(8))

    def __init__(self):
        self.fn: UFunction | None = None
        self.lines: list[str] = []
        self.label_counter = 0

    @staticmethod
    def _safe(name: str) -> str:
        return re.sub(r"[^A-Za-z0-9_]", "_", name)

    def _symbol(self, name: str) -> str:
        return "main" if name == "__entry" else f"eri_fn_{self._safe(name)}"

    def _block_label(self, name: str) -> str:
        assert self.fn is not None
        return f".Leri_{self._safe(self.fn.name)}_{self._safe(name)}"

    def _slot_offset(self, slot: int) -> int:
        return 8 * (slot + 1)

    def _value_slot(self, value: UValue) -> int:
        assert self.fn is not None
        return len(self.fn.locals) + value.id

    def _slot_addr(self, slot: int, scratch: str = "x16") -> str:
        offset = self._slot_offset(slot)
        if offset <= 4095:
            self.lines.append(f"    sub {scratch}, x29, #{offset}")
        else:
            self._mov_imm64("x17", offset)
            self.lines.append(f"    sub {scratch}, x29, x17")
        return scratch

    def _load(self, value: UValue, register: str = "x0") -> None:
        address = self._slot_addr(self._value_slot(value))
        self.lines.append(f"    ldr {register}, [{address}]")

    def _load_f64(self, value: UValue, register: str = "d0") -> None:
        address = self._slot_addr(self._value_slot(value))
        self.lines.append(f"    ldr {register}, [{address}]")

    def _store_result(self, ins: UInstruction, register: str = "x0") -> None:
        if ins.result is None:
            raise ValueError(f"ARM64 instruction {ins.op} unexpectedly has no result")
        address = self._slot_addr(self._value_slot(ins.result))
        self.lines.append(f"    str {register}, [{address}]")

    def _store_result_f64(self, ins: UInstruction, register: str = "d0") -> None:
        if ins.result is None:
            raise ValueError(f"ARM64 instruction {ins.op} unexpectedly has no result")
        address = self._slot_addr(self._value_slot(ins.result))
        self.lines.append(f"    str {register}, [{address}]")

    def _load_local(self, local: int, register: str = "x0") -> None:
        address = self._slot_addr(local)
        self.lines.append(f"    ldr {register}, [{address}]")

    def _store_local(self, local: int, register: str = "x0") -> None:
        address = self._slot_addr(local)
        self.lines.append(f"    str {register}, [{address}]")

    @staticmethod
    def _arg_locations(types: list[str]):
        gp = 0
        fp = 0
        stack = 0
        result = []
        for type_name in types:
            if type_name == F64 and fp < 8:
                result.append(("fp", fp))
                fp += 1
            elif type_name != F64 and gp < 8:
                result.append(("gp", gp))
                gp += 1
            else:
                result.append(("stack", stack))
                stack += 1
        return result, stack

    def _mov_imm64(self, register: str, value: int) -> None:
        value &= (1 << 64) - 1
        parts = [(value >> shift) & 0xFFFF for shift in (0, 16, 32, 48)]
        self.lines.append(f"    movz {register}, #{parts[0]}")
        for index, part in enumerate(parts[1:], start=1):
            if part:
                self.lines.append(f"    movk {register}, #{part}, lsl #{index * 16}")

    def _address(self, register: str, label: str) -> None:
        self.lines.append(f"    adrp {register}, {label}")
        self.lines.append(f"    add {register}, {register}, :lo12:{label}")

    def emit(self, program: UProgram) -> str:
        if not any(fn.name == program.entry for fn in program.functions):
            raise ValueError("universal program has no entry function")
        self.lines = [
            ".section .rodata",
            ".Leri_fmt_i64:",
            '    .asciz "%ld\\n"',
            ".Leri_fmt_f64:",
            '    .asciz "%.17g\\n"',
            ".Leri_true:",
            '    .asciz "true"',
            ".Leri_false:",
            '    .asciz "false"',
            ".Leri_overflow:",
            '    .ascii "Eristavi runtime fault: Int arithmetic overflow\\n"',
            ".Leri_divzero:",
            '    .ascii "Eristavi runtime fault: Int division by zero\\n"',
            ".text",
        ]
        self.label_counter = 0
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
        self.lines.extend([
            f".globl {symbol}",
            f".type {symbol}, %function",
            f"{symbol}:",
            "    stp x29, x30, [sp, #-16]!",
            "    mov x29, sp",
        ])
        if frame:
            if frame <= 4095:
                self.lines.append(f"    sub sp, sp, #{frame}")
            else:
                self._mov_imm64("x16", frame)
                self.lines.append("    sub sp, sp, x16")

        locations, _ = self._arg_locations([p.type_name for p in fn.parameters])
        for parameter, (kind, index) in zip(fn.parameters, locations):
            if kind == "gp":
                self._store_local(parameter.id, self.GP_ARGS[index])
            elif kind == "fp":
                address = self._slot_addr(parameter.id)
                self.lines.append(f"    str {self.FP_ARGS[index]}, [{address}]")
            else:
                self.lines.append(f"    ldr x0, [x29, #{16 + index * 8}]")
                self._store_local(parameter.id, "x0")

        for block in fn.blocks:
            self._block(block)
        self.lines.append(f".size {symbol}, .-{symbol}")

    def _epilogue(self) -> None:
        self.lines.extend([
            "    mov sp, x29",
            "    ldp x29, x30, [sp], #16",
            "    ret",
        ])

    def _block(self, block: UBlock) -> None:
        self.lines.append(f"{self._block_label(block.name)}:")
        for ins in block.instructions:
            self._instruction(ins)
        term = block.terminator
        if isinstance(term, UJump):
            self.lines.append(f"    b {self._block_label(term.target)}")
        elif isinstance(term, UBranch):
            self._load(term.condition, "x0")
            self.lines.append(f"    cbnz x0, {self._block_label(term.true_target)}")
            self.lines.append(f"    b {self._block_label(term.false_target)}")
        elif isinstance(term, UReturn):
            if term.value is not None:
                if term.value.type_name == F64:
                    self._load_f64(term.value, "d0")
                else:
                    self._load(term.value, "x0")
            elif self.fn is not None and self.fn.name == "__entry":
                self.lines.append("    mov w0, #0")
            self._epilogue()
        else:
            raise ValueError(f"ARM64 block {block.name!r} has invalid terminator")

    def _call(self, ins: UInstruction) -> None:
        locations, stack_count = self._arg_locations([arg.type_name for arg in ins.args])
        stack_size = ((stack_count * 8 + 15) // 16) * 16
        if stack_size:
            self.lines.append(f"    sub sp, sp, #{stack_size}")
        for value, (kind, index) in zip(ins.args, locations):
            if kind == "stack":
                self._load(value, "x16")
                self.lines.append(f"    str x16, [sp, #{index * 8}]")
        for value, (kind, index) in zip(ins.args, locations):
            if kind == "gp":
                self._load(value, self.GP_ARGS[index])
            elif kind == "fp":
                self._load_f64(value, self.FP_ARGS[index])
        self.lines.append(f"    bl {self._symbol(str(ins.immediate))}")
        if stack_size:
            self.lines.append(f"    add sp, sp, #{stack_size}")
        if ins.result is not None:
            if ins.result.type_name == F64:
                self._store_result_f64(ins, "d0")
            else:
                self._store_result(ins, "x0")

    def _fault_runtime(self) -> None:
        overflow_len = len("Eristavi runtime fault: Int arithmetic overflow\n".encode())
        divzero_len = len("Eristavi runtime fault: Int division by zero\n".encode())
        self.lines.extend([
            ".Leri_fault_overflow:",
            "    mov x0, #2",
        ])
        self._address("x1", ".Leri_overflow")
        self.lines.extend([
            f"    mov x2, #{overflow_len}",
            "    bl write",
            "    mov x0, #1",
            "    bl exit",
            "    brk #0",
            ".Leri_fault_divzero:",
            "    mov x0, #2",
        ])
        self._address("x1", ".Leri_divzero")
        self.lines.extend([
            f"    mov x2, #{divzero_len}",
            "    bl write",
            "    mov x0, #1",
            "    bl exit",
            "    brk #0",
        ])

    def _instruction(self, ins: UInstruction) -> None:
        op = ins.op
        if op in ("const_i64", "const_bool"):
            value = int(bool(ins.immediate)) if op == "const_bool" else int(ins.immediate)
            self._mov_imm64("x0", value)
            self._store_result(ins, "x0")
            return
        if op == "const_f64":
            bits = struct.unpack("<Q", struct.pack("<d", float(ins.immediate)))[0]
            self._mov_imm64("x0", bits)
            self.lines.append("    fmov d0, x0")
            self._store_result_f64(ins, "d0")
            return
        if op == "load_local":
            if ins.local is None:
                raise ValueError("load_local missing local id")
            self._load_local(ins.local, "x0")
            self._store_result(ins, "x0")
            return
        if op == "store_local":
            if ins.local is None or len(ins.args) != 1:
                raise ValueError("store_local is malformed")
            if ins.args[0].type_name == F64:
                self._load_f64(ins.args[0], "d0")
                address = self._slot_addr(ins.local)
                self.lines.append(f"    str d0, [{address}]")
            else:
                self._load(ins.args[0], "x0")
                self._store_local(ins.local, "x0")
            return
        if op == "call":
            self._call(ins)
            return
        if op == "neg_checked":
            self._load(ins.args[0], "x0")
            self.lines.extend(["    negs x0, x0", "    b.vs .Leri_fault_overflow"])
            self._store_result(ins, "x0")
            return
        if op in ("add_checked", "sub_checked"):
            self._load(ins.args[0], "x0")
            self._load(ins.args[1], "x1")
            mnemonic = "adds" if op == "add_checked" else "subs"
            self.lines.extend([f"    {mnemonic} x0, x0, x1", "    b.vs .Leri_fault_overflow"])
            self._store_result(ins, "x0")
            return
        if op == "mul_checked":
            self._load(ins.args[0], "x0")
            self._load(ins.args[1], "x1")
            self.lines.extend([
                "    mul x2, x0, x1",
                "    smulh x3, x0, x1",
                "    cmp x3, x2, asr #63",
                "    b.ne .Leri_fault_overflow",
                "    mov x0, x2",
            ])
            self._store_result(ins, "x0")
            return
        if op in ("div_checked", "rem_checked"):
            self._load(ins.args[0], "x0")
            self._load(ins.args[1], "x1")
            unique = self.label_counter
            self.label_counter += 1
            okay = f".Leri_div_ok_{unique}"
            self.lines.extend([
                "    cbz x1, .Leri_fault_divzero",
                "    cmp x1, #-1",
                f"    b.ne {okay}",
                "    mov x2, #1",
                "    lsl x2, x2, #63",
                "    cmp x0, x2",
                "    b.eq .Leri_fault_overflow",
                f"{okay}:",
                "    sdiv x2, x0, x1",
            ])
            if op == "rem_checked":
                self.lines.append("    msub x0, x2, x1, x0")
            else:
                self.lines.append("    mov x0, x2")
            self._store_result(ins, "x0")
            return
        if op == "bool_not":
            self._load(ins.args[0], "x0")
            self.lines.extend(["    cmp x0, #0", "    cset x0, eq"])
            self._store_result(ins, "x0")
            return
        if op in ("cmp_eq", "cmp_ne", "cmp_lt", "cmp_le", "cmp_gt", "cmp_ge"):
            self._load(ins.args[0], "x0")
            self._load(ins.args[1], "x1")
            condition = {
                "cmp_eq": "eq", "cmp_ne": "ne", "cmp_lt": "lt",
                "cmp_le": "le", "cmp_gt": "gt", "cmp_ge": "ge",
            }[op]
            self.lines.extend(["    cmp x0, x1", f"    cset x0, {condition}"])
            self._store_result(ins, "x0")
            return
        if op == "f64_neg":
            self._load_f64(ins.args[0], "d0")
            self.lines.append("    fneg d0, d0")
            self._store_result_f64(ins, "d0")
            return
        if op in ("f64_add", "f64_sub", "f64_mul", "f64_div"):
            self._load_f64(ins.args[0], "d0")
            self._load_f64(ins.args[1], "d1")
            mnemonic = {
                "f64_add": "fadd", "f64_sub": "fsub",
                "f64_mul": "fmul", "f64_div": "fdiv",
            }[op]
            self.lines.append(f"    {mnemonic} d0, d0, d1")
            self._store_result_f64(ins, "d0")
            return
        if op.startswith("f64_cmp_"):
            self._load_f64(ins.args[0], "d0")
            self._load_f64(ins.args[1], "d1")
            self.lines.append("    fcmp d0, d1")
            condition = {
                "eq": "eq", "ne": "ne", "lt": "mi",
                "le": "ls", "gt": "gt", "ge": "ge",
            }.get(op[8:])
            if condition is None:
                raise ValueError(f"unknown Float comparison {op!r}")
            self.lines.append(f"    cset x0, {condition}")
            self._store_result(ins, "x0")
            return
        if op == "output_i64":
            self._load(ins.args[0], "x1")
            self._address("x0", ".Leri_fmt_i64")
            self.lines.append("    bl printf")
            return
        if op == "output_bool":
            self._load(ins.args[0], "x0")
            unique = self.label_counter
            self.label_counter += 1
            false_label = f".Leri_bool_false_{unique}"
            ready = f".Leri_bool_ready_{unique}"
            self.lines.extend(["    cbz x0, " + false_label])
            self._address("x0", ".Leri_true")
            self.lines.append(f"    b {ready}")
            self.lines.append(false_label + ":")
            self._address("x0", ".Leri_false")
            self.lines.extend([ready + ":", "    bl puts"])
            return
        if op == "output_f64":
            self._load_f64(ins.args[0], "d0")
            self._address("x0", ".Leri_fmt_f64")
            self.lines.append("    bl printf")
            return
        raise ValueError(f"ARM64 backend does not support universal op {op!r}")
