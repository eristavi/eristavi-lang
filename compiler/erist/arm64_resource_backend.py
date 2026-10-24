from __future__ import annotations

from .arm64_checked_backend import ARM64CheckedRuntimeLinuxBackend
from .ir import STD_FILE_ERROR
from .universal_ir import UInstruction, UProgram


class ARM64ResourceRuntimeLinuxBackend(ARM64CheckedRuntimeLinuxBackend):
    """AArch64 std.files implementation with deterministic `with` cleanup.

    File resources are explicit owned records `[FILE*, path Text]`. Cleanup is
    driven by Universal IR, while cleanup failures preserve an already-active
    checked failure as primary and retain cleanup context in the secondary list.
    """

    def emit(self, program: UProgram) -> str:
        assembly = super().emit(program)
        extra = [
            ".section .rodata",
            ".Leri_mode_readwrite:", '    .asciz "r+"',
            ".Leri_path_nul_message:", '    .asciz "file path contains NUL"',
            ".Leri_utf8_message:", '    .asciz "invalid UTF-8"',
            ".Leri_io_message:", '    .asciz "file I/O failed"',
            ".Leri_closed_message:", '    .ascii "Eristavi runtime fault: file resource is closed\\n"',
            ".Leri_closed_message_end:",
            ".section .bss", ".align 3",
            ".Leri_error_secondary_head:", "    .quad 0",
            ".Leri_error_secondary_tail:", "    .quad 0",
        ]
        return assembly.replace(".text\n", "\n".join(extra) + "\n.text\n", 1)

    def _clear_secondary(self):
        self.lines.append("    mov x9, #0")
        for label in (".Leri_error_secondary_head", ".Leri_error_secondary_tail"):
            self._store_global(label, "x9")

    def _instruction(self, ins: UInstruction) -> None:
        op=ins.op
        if op in ("error_clear","set_error"):
            super()._instruction(ins)
            self._clear_secondary()
            return
        if op=="file_open":
            self._load(ins.args[0],"x0"); self.lines.append("    bl .Leri_file_open"); self._store_result(ins,"x0"); return
        if op=="file_read_text":
            self._load(ins.args[0],"x0"); self.lines.append("    bl .Leri_file_read_text"); self._store_result(ins,"x0"); return
        if op=="file_write_text":
            self._load(ins.args[0],"x0"); self._load(ins.args[1],"x1"); self.lines.append("    bl .Leri_file_write_text"); return
        if op=="file_exists":
            self._load(ins.args[0],"x0"); self.lines.append("    bl .Leri_file_exists"); self._store_result(ins,"x0"); return
        if op=="file_remove":
            self._load(ins.args[0],"x0"); self.lines.append("    bl .Leri_file_remove"); return
        if op=="resource_cleanup":
            self._load(ins.args[0],"x0"); self.lines.append("    bl .Leri_file_cleanup"); return
        super()._instruction(ins)

    def _fault_runtime(self):
        self._emit_file_runtime()
        self.lines.extend([".Leri_file_closed_fault:","    mov x0, #2"])
        self._address("x1",".Leri_closed_message")
        self.lines.extend(["    mov x2, #48","    bl write","    mov x0, #1","    bl exit","    brk #0"])
        super()._fault_runtime()

    def _emit_file_runtime(self):
        error_label=self._error_type_label(STD_FILE_ERROR)
        self.lines.extend([
            # x0=C string -> x0=length-aware Eristavi Text.
            ".Leri_text_from_c:",
            "    stp x29, x30, [sp, #-48]!", "    mov x29, sp", "    str x0, [sp, #16]", "    bl strlen", "    str x0, [sp, #24]", "    add x0, x0, #8", "    bl malloc", "    str x0, [sp, #32]", "    ldr x2, [sp, #24]", "    str x2, [x0]", "    add x0, x0, #8", "    ldr x1, [sp, #16]", "    bl memcpy", "    ldr x0, [sp, #32]", "    ldp x29, x30, [sp], #48", "    ret",

            # x0=C message, x1=path Text. Preserve active primary failure.
            ".Leri_set_file_error:",
            "    stp x29, x30, [sp, #-80]!", "    mov x29, sp", "    str x1, [sp, #16]", "    bl .Leri_text_from_c", "    str x0, [sp, #24]", "    mov x0, #16", "    bl malloc", "    str x0, [sp, #32]", "    ldr x9, [sp, #24]", "    str x9, [x0]", "    ldr x9, [sp, #16]", "    str x9, [x0, #8]",
        ])
        self._load_global(".Leri_error_value","x10")
        self.lines.extend(["    cbnz x10, .Leri_file_error_secondary", "    ldr x9, [sp, #32]"])
        self._store_global(".Leri_error_value","x9"); self._address("x9",error_label); self._store_global(".Leri_error_type","x9"); self.lines.append("    ldr x9, [sp, #24]"); self._store_global(".Leri_error_message","x9")
        self.lines.extend(["    ldp x29, x30, [sp], #80", "    ret", ".Leri_file_error_secondary:", "    mov x0, #32", "    bl malloc", "    str x0, [sp, #40]", "    ldr x9, [sp, #32]", "    str x9, [x0]"])
        self._address("x9",error_label); self.lines.extend(["    str x9, [x0, #8]", "    ldr x9, [sp, #24]", "    str x9, [x0, #16]", "    str xzr, [x0, #24]"])
        self._load_global(".Leri_error_secondary_tail","x10")
        self.lines.extend(["    cbz x10, .Leri_secondary_first", "    ldr x9, [sp, #40]", "    str x9, [x10, #24]", "    b .Leri_secondary_tail", ".Leri_secondary_first:", "    ldr x9, [sp, #40]"])
        self._store_global(".Leri_error_secondary_head","x9")
        self.lines.extend([".Leri_secondary_tail:", "    ldr x9, [sp, #40]"])
        self._store_global(".Leri_error_secondary_tail","x9")
        self.lines.extend(["    ldp x29, x30, [sp], #80", "    ret"])

        self.lines.extend([
            # x0=Text -> x0=temporary C path or null after setting checked error.
            ".Leri_text_to_path:",
            "    stp x29, x30, [sp, #-64]!", "    mov x29, sp", "    str x0, [sp, #16]", "    ldr x9, [x0]", "    str x9, [sp, #24]", "    mov x10, #0",
            ".Leri_path_scan:", "    cmp x10, x9", "    b.hs .Leri_path_copy", "    add x11, x0, #8", "    ldrb w12, [x11, x10]", "    cbz w12, .Leri_path_nul", "    add x10, x10, #1", "    b .Leri_path_scan",
            ".Leri_path_nul:",
        ])
        self._address("x0",".Leri_path_nul_message")
        self.lines.extend(["    ldr x1, [sp, #16]", "    bl .Leri_set_file_error", "    mov x0, #0", "    ldp x29, x30, [sp], #64", "    ret", ".Leri_path_copy:", "    add x0, x9, #1", "    bl malloc", "    str x0, [sp, #32]", "    mov x2, x9", "    ldr x1, [sp, #16]", "    add x1, x1, #8", "    bl memcpy", "    ldr x0, [sp, #32]", "    ldr x9, [sp, #24]", "    strb wzr, [x0, x9]", "    ldp x29, x30, [sp], #64", "    ret",

            # x0=Eristavi path, use current errno to install FileError.
            ".Leri_file_errno:",
            "    stp x29, x30, [sp, #-32]!", "    mov x29, sp", "    str x0, [sp, #16]", "    bl __errno_location", "    ldr w0, [x0]", "    bl strerror", "    ldr x1, [sp, #16]", "    bl .Leri_set_file_error", "    ldp x29, x30, [sp], #32", "    ret",

            # x0=Text path -> x0=resource or null.
            ".Leri_file_open:",
            "    stp x29, x30, [sp, #-64]!", "    mov x29, sp", "    str x0, [sp, #16]", "    bl .Leri_text_to_path", "    cbz x0, .Leri_file_open_fail", "    str x0, [sp, #24]", "    mov x1, x0",
        ])
        self._address("x1",".Leri_mode_readwrite")
        self.lines.extend(["    ldr x0, [sp, #24]", "    bl fopen", "    str x0, [sp, #32]", "    ldr x0, [sp, #24]", "    bl free", "    ldr x9, [sp, #32]", "    cbz x9, .Leri_file_open_errno", "    mov x0, #16", "    bl malloc", "    ldr x9, [sp, #32]", "    str x9, [x0]", "    ldr x9, [sp, #16]", "    str x9, [x0, #8]", "    ldp x29, x30, [sp], #64", "    ret", ".Leri_file_open_errno:", "    ldr x0, [sp, #16]", "    bl .Leri_file_errno", ".Leri_file_open_fail:", "    mov x0, #0", "    ldp x29, x30, [sp], #64", "    ret",

            # UTF-8 validator: x0=data, x1=len -> x0 Bool.
            ".Leri_utf8_valid:", "    mov x2, #0", ".Leri_utf8_loop:", "    cmp x2, x1", "    b.hs .Leri_utf8_yes", "    ldrb w3, [x0, x2]", "    cmp w3, #0x80", "    b.lo .Leri_utf8_one", "    cmp w3, #0xC2", "    b.lo .Leri_utf8_no", "    cmp w3, #0xDF", "    b.ls .Leri_utf8_two", "    cmp w3, #0xEF", "    b.ls .Leri_utf8_three", "    cmp w3, #0xF4", "    b.ls .Leri_utf8_four", "    b .Leri_utf8_no",
            ".Leri_utf8_one:", "    add x2, x2, #1", "    b .Leri_utf8_loop",
            ".Leri_utf8_two:", "    add x4, x2, #1", "    cmp x4, x1", "    b.hs .Leri_utf8_no", "    ldrb w5, [x0, x4]", "    and w5, w5, #0xC0", "    cmp w5, #0x80", "    b.ne .Leri_utf8_no", "    add x2, x2, #2", "    b .Leri_utf8_loop",
            ".Leri_utf8_three:", "    add x4, x2, #2", "    cmp x4, x1", "    b.hs .Leri_utf8_no", "    add x4, x2, #1", "    ldrb w5, [x0, x4]", "    add x4, x2, #2", "    ldrb w6, [x0, x4]", "    and w7, w6, #0xC0", "    cmp w7, #0x80", "    b.ne .Leri_utf8_no", "    cmp w3, #0xE0", "    b.ne .Leri_utf8_three_ed", "    cmp w5, #0xA0", "    b.lo .Leri_utf8_no", "    cmp w5, #0xBF", "    b.hi .Leri_utf8_no", "    b .Leri_utf8_three_ok", ".Leri_utf8_three_ed:", "    cmp w3, #0xED", "    b.ne .Leri_utf8_three_general", "    cmp w5, #0x80", "    b.lo .Leri_utf8_no", "    cmp w5, #0x9F", "    b.hi .Leri_utf8_no", "    b .Leri_utf8_three_ok", ".Leri_utf8_three_general:", "    and w5, w5, #0xC0", "    cmp w5, #0x80", "    b.ne .Leri_utf8_no", ".Leri_utf8_three_ok:", "    add x2, x2, #3", "    b .Leri_utf8_loop",
            ".Leri_utf8_four:", "    add x4, x2, #3", "    cmp x4, x1", "    b.hs .Leri_utf8_no", "    add x4, x2, #1", "    ldrb w5, [x0, x4]", "    add x4, x2, #2", "    ldrb w6, [x0, x4]", "    add x4, x2, #3", "    ldrb w7, [x0, x4]", "    and w8, w6, #0xC0", "    cmp w8, #0x80", "    b.ne .Leri_utf8_no", "    and w8, w7, #0xC0", "    cmp w8, #0x80", "    b.ne .Leri_utf8_no", "    cmp w3, #0xF0", "    b.ne .Leri_utf8_four_f4", "    cmp w5, #0x90", "    b.lo .Leri_utf8_no", "    cmp w5, #0xBF", "    b.hi .Leri_utf8_no", "    b .Leri_utf8_four_ok", ".Leri_utf8_four_f4:", "    cmp w3, #0xF4", "    b.ne .Leri_utf8_four_general", "    cmp w5, #0x80", "    b.lo .Leri_utf8_no", "    cmp w5, #0x8F", "    b.hi .Leri_utf8_no", "    b .Leri_utf8_four_ok", ".Leri_utf8_four_general:", "    and w5, w5, #0xC0", "    cmp w5, #0x80", "    b.ne .Leri_utf8_no", ".Leri_utf8_four_ok:", "    add x2, x2, #4", "    b .Leri_utf8_loop", ".Leri_utf8_yes:", "    mov x0, #1", "    ret", ".Leri_utf8_no:", "    mov x0, #0", "    ret",

            # x0=resource -> x0=Text or null with checked failure.
            ".Leri_file_read_text:", "    stp x29, x30, [sp, #-96]!", "    mov x29, sp", "    str x0, [sp, #16]", "    ldr x0, [x0]", "    cbz x0, .Leri_file_closed_fault", "    mov x1, #0", "    mov x2, #2", "    bl fseek", "    cbnz w0, .Leri_read_errno", "    ldr x9, [sp, #16]", "    ldr x0, [x9]", "    bl ftell", "    tbnz x0, #63, .Leri_read_errno", "    str x0, [sp, #24]", "    ldr x9, [sp, #16]", "    ldr x0, [x9]", "    mov x1, #0", "    mov x2, #0", "    bl fseek", "    cbnz w0, .Leri_read_errno", "    ldr x9, [sp, #24]", "    add x0, x9, #8", "    bl malloc", "    str x0, [sp, #32]", "    ldr x9, [sp, #24]", "    str x9, [x0]", "    add x0, x0, #8", "    mov x1, #1", "    ldr x2, [sp, #24]", "    ldr x9, [sp, #16]", "    ldr x3, [x9]", "    bl fread", "    ldr x9, [sp, #24]", "    cmp x0, x9", "    b.ne .Leri_read_io", "    ldr x9, [sp, #32]", "    add x0, x9, #8", "    ldr x1, [sp, #24]", "    bl .Leri_utf8_valid", "    cbz x0, .Leri_read_utf8", "    ldr x0, [sp, #32]", "    ldp x29, x30, [sp], #96", "    ret",
            ".Leri_read_errno:", "    ldr x9, [sp, #16]", "    ldr x0, [x9, #8]", "    bl .Leri_file_errno", "    b .Leri_read_fail", ".Leri_read_io:",
        ])
        self._address("x0",".Leri_io_message")
        self.lines.extend(["    ldr x9, [sp, #16]", "    ldr x1, [x9, #8]", "    bl .Leri_set_file_error", "    b .Leri_read_fail", ".Leri_read_utf8:"])
        self._address("x0",".Leri_utf8_message")
        self.lines.extend(["    ldr x9, [sp, #16]", "    ldr x1, [x9, #8]", "    bl .Leri_set_file_error", ".Leri_read_fail:", "    ldr x0, [sp, #32]", "    cbz x0, 1f", "    bl free", "1:", "    mov x0, #0", "    ldp x29, x30, [sp], #96", "    ret",

            # x0=resource, x1=Text -> checked write.
            ".Leri_file_write_text:", "    stp x29, x30, [sp, #-80]!", "    mov x29, sp", "    str x0, [sp, #16]", "    str x1, [sp, #24]", "    ldr x0, [x0]", "    cbz x0, .Leri_file_closed_fault", "    mov x1, #0", "    mov x2, #0", "    bl fseek", "    cbnz w0, .Leri_write_errno", "    ldr x9, [sp, #24]", "    add x0, x9, #8", "    mov x1, #1", "    ldr x2, [x9]", "    ldr x10, [sp, #16]", "    ldr x3, [x10]", "    bl fwrite", "    ldr x9, [sp, #24]", "    ldr x10, [x9]", "    cmp x0, x10", "    b.ne .Leri_write_io", "    ldr x9, [sp, #16]", "    ldr x0, [x9]", "    bl fflush", "    cbnz w0, .Leri_write_errno", "    ldr x9, [sp, #16]", "    ldr x0, [x9]", "    bl fileno", "    ldr x9, [sp, #24]", "    ldr x1, [x9]", "    bl ftruncate", "    cbnz w0, .Leri_write_errno", "    ldp x29, x30, [sp], #80", "    ret", ".Leri_write_errno:", "    ldr x9, [sp, #16]", "    ldr x0, [x9, #8]", "    bl .Leri_file_errno", "    ldp x29, x30, [sp], #80", "    ret", ".Leri_write_io:",
        ])
        self._address("x0",".Leri_io_message")
        self.lines.extend(["    ldr x9, [sp, #16]", "    ldr x1, [x9, #8]", "    bl .Leri_set_file_error", "    ldp x29, x30, [sp], #80", "    ret",

            # x0=Text path -> Bool, false only for ordinary ENOENT.
            ".Leri_file_exists:", "    stp x29, x30, [sp, #-64]!", "    mov x29, sp", "    str x0, [sp, #16]", "    bl .Leri_text_to_path", "    cbz x0, .Leri_exists_fail", "    str x0, [sp, #24]", "    mov x1, #0", "    bl access", "    str w0, [sp, #32]", "    ldr x0, [sp, #24]", "    bl free", "    ldr w9, [sp, #32]", "    cbz w9, .Leri_exists_yes", "    bl __errno_location", "    ldr w9, [x0]", "    cmp w9, #2", "    b.eq .Leri_exists_no", "    ldr x0, [sp, #16]", "    bl .Leri_file_errno", ".Leri_exists_fail:", ".Leri_exists_no:", "    mov x0, #0", "    ldp x29, x30, [sp], #64", "    ret", ".Leri_exists_yes:", "    mov x0, #1", "    ldp x29, x30, [sp], #64", "    ret",

            # x0=Text path -> checked no-value remove.
            ".Leri_file_remove:", "    stp x29, x30, [sp, #-64]!", "    mov x29, sp", "    str x0, [sp, #16]", "    bl .Leri_text_to_path", "    cbz x0, .Leri_remove_done", "    str x0, [sp, #24]", "    bl remove", "    str w0, [sp, #32]", "    ldr x0, [sp, #24]", "    bl free", "    ldr w9, [sp, #32]", "    cbz w9, .Leri_remove_done", "    ldr x0, [sp, #16]", "    bl .Leri_file_errno", ".Leri_remove_done:", "    ldp x29, x30, [sp], #64", "    ret",

            # x0=resource -> exactly-once cleanup. fclose failure composes.
            ".Leri_file_cleanup:", "    stp x29, x30, [sp, #-48]!", "    mov x29, sp", "    str x0, [sp, #16]", "    ldr x9, [x0]", "    cbz x9, .Leri_cleanup_done", "    str xzr, [x0]", "    mov x0, x9", "    bl fclose", "    cbz w0, .Leri_cleanup_done", "    ldr x9, [sp, #16]", "    ldr x0, [x9, #8]", "    bl .Leri_file_errno", ".Leri_cleanup_done:", "    ldp x29, x30, [sp], #48", "    ret",
        ])
