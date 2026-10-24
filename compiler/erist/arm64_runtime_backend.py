from __future__ import annotations

import hashlib

from .arm64_backend import ARM64LinuxBackend
from .universal_ir import (
    BOOL, F64, I64, TEXT, UInstruction, UProgram, UType,
    identity_inner, is_value_composite, list_inner, maybe_inner, nominal_name,
)


class ARM64RuntimeLinuxBackend(ARM64LinuxBackend):
    """AArch64 backend extension for Text and heap-backed pre-0.1 values.

    The representation matches the target-neutral direct-runtime contract used
    by x86-64: Text is length+UTF-8 bytes, Lists are count/capacity/data, maybe
    is null-or-boxed, identity is a shared box, and ordinary aggregate transfer
    invokes recursive clone helpers. This is intentionally architecture parity,
    not a separate ARM-specific language model.
    """

    def __init__(self):
        super().__init__()
        self.text_labels = {}
        self.type_defs: dict[str, UType] = {}
        self.clone_types: set[str] = set()
        self.equal_types: set[str] = set()

    @staticmethod
    def _type_key(type_name: str) -> str:
        return hashlib.sha1(type_name.encode("utf-8")).hexdigest()[:12]

    def _clone_symbol(self, type_name: str) -> str:
        return f".Leri_clone_{self._type_key(type_name)}"

    def _eq_symbol(self, type_name: str) -> str:
        return f".Leri_eq_{self._type_key(type_name)}"

    def _collect(self, program: UProgram):
        self.type_defs = {item.name: item for item in program.types}
        self.text_labels = {}
        self.clone_types = set()
        self.equal_types = {TEXT}
        for fn in program.functions:
            for block in fn.blocks:
                for ins in block.instructions:
                    if ins.op == "const_text":
                        text = str(ins.immediate)
                        self.text_labels.setdefault(text, f".Leri_text_{len(self.text_labels)}")
                    elif ins.op == "clone_value":
                        self.clone_types.add(str(ins.immediate))
                    elif ins.op in ("value_eq", "value_ne"):
                        self.equal_types.add(str(ins.immediate))
        changed=True
        while changed:
            changed=False
            for t in list(self.clone_types):
                for child in self._children(t):
                    if is_value_composite(child) and child not in self.clone_types:
                        self.clone_types.add(child); changed=True
            for t in list(self.equal_types):
                for child in self._children(t):
                    if child not in self.equal_types:
                        self.equal_types.add(child); changed=True

    def _children(self, t):
        if t.startswith("maybe<"): return [maybe_inner(t)]
        if t.startswith("list<"): return [list_inner(t)]
        if t.startswith("nominal<"):
            info=self.type_defs.get(nominal_name(t))
            if info is None: raise ValueError(f"ARM64 backend has no layout for {t}")
            return [field.type_name for field in info.fields]
        return []

    def emit(self, program: UProgram) -> str:
        self._collect(program)
        assembly = super().emit(program)
        extra=[
            ".section .rodata",
            ".Leri_newline:", "    .byte 10",
            ".Leri_bounds:", '    .ascii "Eristavi runtime fault: List index out of bounds\\n"', ".Leri_bounds_end:",
            ".Leri_absent:", '    .ascii "Eristavi runtime fault: absent maybe value\\n"', ".Leri_absent_end:",
        ]
        for text,label in self.text_labels.items():
            data=text.encode("utf-8")
            extra.extend([f"{label}:",f"    .quad {len(data)}"])
            if data: extra.append("    .byte "+", ".join(str(x) for x in data))
        return assembly.replace(".text\n", "\n".join(extra)+"\n.text\n",1)

    def _bounds(self, list_reg="x9", index_reg="x10"):
        self.lines.extend([
            f"    tbnz {index_reg}, #63, .Leri_fault_bounds",
            f"    ldr x11, [{list_reg}]",
            f"    cmp {index_reg}, x11",
            "    b.hs .Leri_fault_bounds",
        ])

    def _instruction(self, ins: UInstruction) -> None:
        op=ins.op
        if op=="const_text":
            self._address("x0", self.text_labels[str(ins.immediate)]); self._store_result(ins,"x0"); return
        if op=="text_concat":
            self._load(ins.args[0],"x9"); self._load(ins.args[1],"x10")
            self.lines.extend(["    ldr x11, [x9]","    ldr x12, [x10]","    add x0, x11, x12","    add x0, x0, #8","    bl malloc"])
            self._store_result(ins,"x0")
            self._load(ins.result,"x9"); self._load(ins.args[0],"x10"); self._load(ins.args[1],"x11")
            self.lines.extend(["    ldr x12, [x10]","    ldr x13, [x11]","    add x14, x12, x13","    str x14, [x9]","    add x0, x9, #8","    add x1, x10, #8","    mov x2, x12","    bl memcpy"])
            self._load(ins.result,"x9"); self._load(ins.args[0],"x10"); self._load(ins.args[1],"x11")
            self.lines.extend(["    ldr x12, [x10]","    ldr x13, [x11]","    add x0, x9, #8","    add x0, x0, x12","    add x1, x11, #8","    mov x2, x13","    bl memcpy"])
            return
        if op in ("text_eq","text_ne"):
            unique=self.label_counter; self.label_counter+=1; no=f".Leri_text_ne_{unique}"; done=f".Leri_text_cmp_done_{unique}"
            self._load(ins.args[0],"x9"); self._load(ins.args[1],"x10")
            self.lines.extend(["    ldr x11, [x9]","    ldr x12, [x10]","    cmp x11, x12",f"    b.ne {no}","    add x0, x9, #8","    add x1, x10, #8","    mov x2, x11","    bl memcmp","    cmp w0, #0","    cset x0, eq",f"    b {done}",f"{no}:","    mov x0, #0",f"{done}:"])
            if op=="text_ne": self.lines.append("    eor x0, x0, #1")
            self._store_result(ins,"x0"); return
        if op=="output_text":
            self._load(ins.args[0],"x9")
            self.lines.extend(["    mov x0, #1","    add x1, x9, #8","    ldr x2, [x9]","    bl write","    mov x0, #1"])
            self._address("x1",".Leri_newline"); self.lines.extend(["    mov x2, #1","    bl write"]); return
        if op=="clone_value":
            self._load(ins.args[0],"x0"); self.lines.append(f"    bl {self._clone_symbol(str(ins.immediate))}"); self._store_result(ins,"x0"); return
        if op=="make_struct":
            size=max(8,len(ins.args)*8); self._mov_imm64("x0",size); self.lines.append("    bl malloc"); self._store_result(ins,"x0")
            for index,value in enumerate(ins.args):
                self._load(ins.result,"x9"); self._load(value,"x10"); self.lines.append(f"    str x10, [x9, #{index*8}]")
            return
        if op=="get_field":
            index=int(ins.immediate["index"]); self._load(ins.args[0],"x9"); self.lines.append(f"    ldr x0, [x9, #{index*8}]"); self._store_result(ins,"x0"); return
        if op=="set_field":
            index=int(ins.immediate["index"]); self._load(ins.args[0],"x9"); self._load(ins.args[1],"x10"); self.lines.append(f"    str x10, [x9, #{index*8}]"); return
        if op=="make_identity":
            self._mov_imm64("x0",8); self.lines.append("    bl malloc"); self._store_result(ins,"x0"); self._load(ins.result,"x9"); self._load(ins.args[0],"x10"); self.lines.append("    str x10, [x9]"); return
        if op=="identity_get": self._load(ins.args[0],"x9"); self.lines.append("    ldr x0, [x9]"); self._store_result(ins,"x0"); return
        if op in ("identity_eq","identity_ne"):
            self._load(ins.args[0],"x9"); self._load(ins.args[1],"x10"); self.lines.append("    cmp x9, x10"); self.lines.append("    cset x0, "+("eq" if op=="identity_eq" else "ne")); self._store_result(ins,"x0"); return
        if op=="maybe_none": self.lines.append("    mov x0, #0"); self._store_result(ins,"x0"); return
        if op=="maybe_some":
            self._mov_imm64("x0",8); self.lines.append("    bl malloc"); self._store_result(ins,"x0"); self._load(ins.result,"x9"); self._load(ins.args[0],"x10"); self.lines.append("    str x10, [x9]"); return
        if op=="maybe_get":
            self._load(ins.args[0],"x9"); self.lines.extend(["    cbz x9, .Leri_fault_absent","    ldr x0, [x9]"]); self._store_result(ins,"x0"); return
        if op=="make_list":
            count=len(ins.args); self._mov_imm64("x0",24); self.lines.append("    bl malloc"); self._store_result(ins,"x0"); self._load(ins.result,"x9"); self._mov_imm64("x10",count); self.lines.extend(["    str x10, [x9]","    str x10, [x9, #8]"])
            if count:
                self._mov_imm64("x0",count*8); self.lines.append("    bl malloc"); self._load(ins.result,"x9"); self.lines.append("    str x0, [x9, #16]")
                for index,value in enumerate(ins.args): self._load(ins.result,"x9"); self.lines.append("    ldr x11, [x9, #16]"); self._load(value,"x10"); self.lines.append(f"    str x10, [x11, #{index*8}]")
            else: self.lines.append("    str xzr, [x9, #16]")
            return
        if op=="list_count": self._load(ins.args[0],"x9"); self.lines.append("    ldr x0, [x9]"); self._store_result(ins,"x0"); return
        if op=="list_get": self._load(ins.args[0],"x9"); self._load(ins.args[1],"x10"); self._bounds(); self.lines.extend(["    ldr x11, [x9, #16]","    ldr x0, [x11, x10, lsl #3]"]); self._store_result(ins,"x0"); return
        if op=="list_set": self._load(ins.args[0],"x9"); self._load(ins.args[1],"x10"); self._bounds(); self._load(ins.args[2],"x12"); self.lines.extend(["    ldr x11, [x9, #16]","    str x12, [x11, x10, lsl #3]"]); return
        if op=="list_add":
            self._load(ins.args[0],"x9"); self.lines.extend(["    ldr x10, [x9]","    ldr x11, [x9, #8]","    cmp x10, x11"]); unique=self.label_counter; self.label_counter+=1; ready=f".Leri_list_ready_{unique}"; grow=f".Leri_list_grow_{unique}"
            self.lines.append(f"    b.lo {ready}"); self.lines.extend(["    cmp x11, #0",f"    b.ne {grow}","    mov x11, #4",f"    b {grow}_do",f"{grow}:","    lsl x11, x11, #1",f"{grow}_do:","    sub sp, sp, #16","    str x11, [sp]","    ldr x0, [x9, #16]","    lsl x1, x11, #3","    bl realloc","    ldr x11, [sp]","    add sp, sp, #16"]); self._load(ins.args[0],"x9"); self.lines.extend(["    str x0, [x9, #16]","    str x11, [x9, #8]",f"{ready}:"]); self._load(ins.args[0],"x9"); self._load(ins.args[1],"x12"); self.lines.extend(["    ldr x10, [x9]","    ldr x11, [x9, #16]","    str x12, [x11, x10, lsl #3]","    add x10, x10, #1","    str x10, [x9]"]); return
        if op in ("value_eq","value_ne"):
            self._load(ins.args[0],"x0"); self._load(ins.args[1],"x1"); self.lines.append(f"    bl {self._eq_symbol(str(ins.immediate))}");
            if op=="value_ne": self.lines.append("    eor x0, x0, #1")
            self._store_result(ins,"x0"); return
        super()._instruction(ins)

    def _helper_prologue(self): self.lines.extend(["    stp x29, x30, [sp, #-64]!","    mov x29, sp","    stp x19, x20, [sp, #16]","    stp x21, x22, [sp, #32]","    stp x23, x24, [sp, #48]"])
    def _helper_return(self): self.lines.extend(["    ldp x23, x24, [sp, #48]","    ldp x21, x22, [sp, #32]","    ldp x19, x20, [sp, #16]","    ldp x29, x30, [sp], #64","    ret"])

    def _clone_child(self,t):
        if is_value_composite(t): self.lines.append(f"    bl {self._clone_symbol(t)}")

    def _emit_clone(self,t):
        self.lines.append(f"{self._clone_symbol(t)}:")
        if t in (I64,F64,BOOL,TEXT) or t.startswith("identity<"): self.lines.append("    ret"); return
        self._helper_prologue(); self.lines.append("    mov x19, x0")
        if t.startswith("maybe<"):
            inner=maybe_inner(t); none=f"{self._clone_symbol(t)}_none"; done=f"{self._clone_symbol(t)}_done"; self.lines.extend([f"    cbz x19, {none}","    mov x0, #8","    bl malloc","    mov x20, x0","    ldr x0, [x19]"]); self._clone_child(inner); self.lines.extend(["    str x0, [x20]","    mov x0, x20",f"    b {done}",f"{none}:","    mov x0, #0",f"{done}:"]); self._helper_return(); return
        if t.startswith("nominal<"):
            info=self.type_defs[nominal_name(t)]; self._mov_imm64("x0",max(8,len(info.fields)*8)); self.lines.append("    bl malloc"); self.lines.append("    mov x20, x0")
            for index,field in enumerate(info.fields): self.lines.append(f"    ldr x0, [x19, #{index*8}]"); self._clone_child(field.type_name); self.lines.append(f"    str x0, [x20, #{index*8}]")
            self.lines.append("    mov x0, x20"); self._helper_return(); return
        if t.startswith("list<"):
            inner=list_inner(t); self.lines.extend(["    ldr x21, [x19]","    mov x0, #24","    bl malloc","    mov x20, x0","    str x21, [x20]","    str x21, [x20, #8]","    cbz x21, 2f","    lsl x0, x21, #3","    bl malloc","    mov x22, x0","    str x22, [x20, #16]","    mov x23, #0","1:","    ldr x0, [x19, #16]","    ldr x0, [x0, x23, lsl #3]"]); self._clone_child(inner); self.lines.extend(["    str x0, [x22, x23, lsl #3]","    add x23, x23, #1","    cmp x23, x21","    b.lo 1b","    b 3f","2:","    str xzr, [x20, #16]","3:","    mov x0, x20"]); self._helper_return(); return
        raise ValueError(f"ARM64 clone helper does not support {t}")

    def _emit_eq(self,t):
        label=self._eq_symbol(t); self.lines.append(f"{label}:")
        if t in (I64,BOOL) or t.startswith("identity<"):
            self.lines.extend(["    cmp x0, x1","    cset x0, eq","    ret"]); return
        if t==F64:
            self.lines.extend(["    fmov d0, x0","    fmov d1, x1","    fcmp d0, d1","    cset x0, eq","    ret"]); return
        if t==TEXT:
            self._helper_prologue(); self.lines.extend(["    mov x19, x0","    mov x20, x1","    ldr x21, [x19]","    ldr x22, [x20]","    cmp x21, x22",f"    b.ne {label}_no","    add x0, x19, #8","    add x1, x20, #8","    mov x2, x21","    bl memcmp","    cmp w0, #0","    cset x0, eq",f"    b {label}_done",f"{label}_no:","    mov x0, #0",f"{label}_done:"]); self._helper_return(); return
        self._helper_prologue(); self.lines.extend(["    mov x19, x0","    mov x20, x1"])
        if t.startswith("maybe<"):
            inner=maybe_inner(t); self.lines.extend(["    cmp x19, x20",f"    b.eq {label}_yes","    cbz x19, "+label+"_no","    cbz x20, "+label+"_no","    ldr x0, [x19]","    ldr x1, [x20]"]); self.lines.append(f"    bl {self._eq_symbol(inner)}"); self.lines.append(f"    b {label}_done")
        elif t.startswith("nominal<"):
            info=self.type_defs[nominal_name(t)]
            for index,field in enumerate(info.fields): self.lines.extend([f"    ldr x0, [x19, #{index*8}]",f"    ldr x1, [x20, #{index*8}]",f"    bl {self._eq_symbol(field.type_name)}",f"    cbz x0, {label}_no"])
            self.lines.append(f"    b {label}_yes")
        elif t.startswith("list<"):
            inner=list_inner(t); self.lines.extend(["    ldr x21, [x19]","    ldr x22, [x20]","    cmp x21, x22",f"    b.ne {label}_no","    mov x23, #0",f"{label}_loop:","    cmp x23, x21",f"    b.hs {label}_yes","    ldr x9, [x19, #16]","    ldr x10, [x20, #16]","    ldr x0, [x9, x23, lsl #3]","    ldr x1, [x10, x23, lsl #3]",f"    bl {self._eq_symbol(inner)}",f"    cbz x0, {label}_no","    add x23, x23, #1",f"    b {label}_loop"])
        else: raise ValueError(f"ARM64 equality helper does not support {t}")
        self.lines.extend([f"{label}_yes:","    mov x0, #1",f"    b {label}_done",f"{label}_no:","    mov x0, #0",f"{label}_done:"]); self._helper_return()

    def _fault_runtime(self):
        for label,message,end in ((".Leri_fault_bounds",".Leri_bounds",".Leri_bounds_end"),(".Leri_fault_absent",".Leri_absent",".Leri_absent_end")):
            self.lines.extend([label+":","    mov x0, #2"]); self._address("x1",message); self.lines.extend([f"    mov x2, #{48 if 'bounds' in label else 43}","    bl write","    mov x0, #1","    bl exit","    brk #0"])
        for t in sorted(self.clone_types): self._emit_clone(t)
        # Equality recursion may need primitive helpers even if not directly requested.
        for t in sorted(self.equal_types): self._emit_eq(t)
        super()._fault_runtime()
