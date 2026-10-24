from __future__ import annotations

import hashlib

from .universal_ir import UInstruction
from .x86_64_backend import X86_64LinuxBackend


class X86_64CheckedLinuxBackend(X86_64LinuxBackend):
    """x86-64 backend extension for explicit Universal-IR checked failures."""

    @staticmethod
    def _error_type_label(type_name: str) -> str:
        key = hashlib.sha1(type_name.encode("utf-8")).hexdigest()[:12]
        return f".Leri_error_type_{key}"

    def _emit_rodata(self) -> None:
        super()._emit_rodata()
        for item in sorted((t for t in self.type_defs.values() if t.is_error), key=lambda t: t.name):
            label = self._error_type_label(item.name)
            data = item.name.encode("utf-8")
            self.lines.append(f"{label}:")
            self.lines.append("    .byte " + ", ".join(str(b) for b in data) + ", 0")
        self.lines.extend([
            ".section .bss",
            ".align 8",
            ".Leri_error_value:",
            "    .quad 0",
            ".Leri_error_type:",
            "    .quad 0",
            ".Leri_error_message:",
            "    .quad 0",
        ])

    def _message_index(self, type_name: str) -> int:
        info = self.type_defs.get(type_name)
        if info is None or not info.is_error:
            raise ValueError(f"checked failure type {type_name!r} has no Universal-IR error layout")
        for index, field in enumerate(info.fields):
            if field.name == "message":
                return index
        raise ValueError(f"checked failure type {type_name!r} has no message field")

    def _instruction(self, ins: UInstruction) -> None:
        op = ins.op
        if op == "zero_value":
            self.lines.append("    xorq %rax, %rax")
            self._store_result(ins)
            return
        if op == "set_error":
            type_name = str(ins.immediate)
            message_index = self._message_index(type_name)
            self._load(ins.args[0], "%rax")
            self.lines.extend([
                "    movq %rax, .Leri_error_value(%rip)",
                f"    leaq {self._error_type_label(type_name)}(%rip), %rcx",
                "    movq %rcx, .Leri_error_type(%rip)",
                f"    movq {message_index * 8}(%rax), %rcx",
                "    movq %rcx, .Leri_error_message(%rip)",
            ])
            return
        if op == "error_pending":
            self.lines.extend([
                "    cmpq $0, .Leri_error_value(%rip)",
                "    setne %al",
                "    movzbq %al, %rax",
            ])
            self._store_result(ins)
            return
        if op == "error_matches":
            type_name = str(ins.immediate)
            self.lines.extend([
                "    movq .Leri_error_type(%rip), %rax",
                f"    leaq {self._error_type_label(type_name)}(%rip), %rcx",
                "    cmpq %rcx, %rax",
                "    sete %al",
                "    movzbq %al, %rax",
            ])
            self._store_result(ins)
            return
        if op == "error_value":
            self.lines.append("    movq .Leri_error_value(%rip), %rax")
            self._store_result(ins)
            return
        if op == "error_message":
            self.lines.append("    movq .Leri_error_message(%rip), %rax")
            self._store_result(ins)
            return
        if op == "error_clear":
            self.lines.extend([
                "    movq $0, .Leri_error_value(%rip)",
                "    movq $0, .Leri_error_type(%rip)",
                "    movq $0, .Leri_error_message(%rip)",
            ])
            return
        super()._instruction(ins)
