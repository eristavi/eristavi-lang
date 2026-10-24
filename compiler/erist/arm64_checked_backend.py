from __future__ import annotations

import hashlib

from .arm64_runtime_backend import ARM64RuntimeLinuxBackend
from .universal_ir import UInstruction, UProgram


class ARM64CheckedRuntimeLinuxBackend(ARM64RuntimeLinuxBackend):
    """AArch64 checked-error state/handler implementation for Universal IR."""

    @staticmethod
    def _error_type_label(type_name: str) -> str:
        return ".Leri_error_type_" + hashlib.sha1(type_name.encode("utf-8")).hexdigest()[:12]

    def emit(self, program: UProgram) -> str:
        assembly = super().emit(program)
        extra = [".section .rodata"]
        for item in sorted((t for t in self.type_defs.values() if t.is_error), key=lambda t: t.name):
            label = self._error_type_label(item.name)
            data = item.name.encode("utf-8")
            extra.extend([f"{label}:", "    .byte " + ", ".join(str(b) for b in data) + ", 0"])
        extra.extend([
            ".section .bss", ".align 3",
            ".Leri_error_value:", "    .quad 0",
            ".Leri_error_type:", "    .quad 0",
            ".Leri_error_message:", "    .quad 0",
        ])
        return assembly.replace(".text\n", "\n".join(extra) + "\n.text\n", 1)

    def _message_index(self, type_name: str) -> int:
        info = self.type_defs.get(type_name)
        if info is None or not info.is_error:
            raise ValueError(f"ARM64 checked failure type {type_name!r} has no error layout")
        for index, field in enumerate(info.fields):
            if field.name == "message":
                return index
        raise ValueError(f"ARM64 checked failure type {type_name!r} has no message field")

    def _store_global(self, label: str, register: str):
        self._address("x16", label)
        self.lines.append(f"    str {register}, [x16]")

    def _load_global(self, label: str, register: str):
        self._address("x16", label)
        self.lines.append(f"    ldr {register}, [x16]")

    def _instruction(self, ins: UInstruction) -> None:
        op = ins.op
        if op == "zero_value":
            self.lines.append("    mov x0, #0")
            self._store_result(ins, "x0")
            return
        if op == "set_error":
            type_name = str(ins.immediate)
            self._load(ins.args[0], "x9")
            self._store_global(".Leri_error_value", "x9")
            self._address("x10", self._error_type_label(type_name))
            self._store_global(".Leri_error_type", "x10")
            self.lines.append(f"    ldr x11, [x9, #{self._message_index(type_name) * 8}]")
            self._store_global(".Leri_error_message", "x11")
            return
        if op == "error_pending":
            self._load_global(".Leri_error_value", "x0")
            self.lines.extend(["    cmp x0, #0", "    cset x0, ne"])
            self._store_result(ins, "x0")
            return
        if op == "error_matches":
            self._load_global(".Leri_error_type", "x9")
            self._address("x10", self._error_type_label(str(ins.immediate)))
            self.lines.extend(["    cmp x9, x10", "    cset x0, eq"])
            self._store_result(ins, "x0")
            return
        if op == "error_value":
            if ins.result is None:
                raise ValueError("ARM64 error_value requires a result")
            if ins.result.type_name == "error<any>":
                self.lines.extend(["    mov x0, #8", "    bl malloc"])
                self._store_result(ins, "x0")
                self._load_global(".Leri_error_message", "x10")
                self._load(ins.result, "x9")
                self.lines.append("    str x10, [x9]")
            else:
                self._load_global(".Leri_error_value", "x0")
                self._store_result(ins, "x0")
            return
        if op == "error_message":
            self._load(ins.args[0], "x9")
            self.lines.append("    ldr x0, [x9]")
            self._store_result(ins, "x0")
            return
        if op == "error_clear":
            self.lines.append("    mov x9, #0")
            for label in (".Leri_error_value", ".Leri_error_type", ".Leri_error_message"):
                self._store_global(label, "x9")
            return
        super()._instruction(ins)
