from __future__ import annotations

from .universal_ir import UFunction
from .x86_64_gc_backend import X86_64GCLinuxBackend


class X86_64PreciseRootGCLinuxBackend(X86_64GCLinuxBackend):
    """GC backend whose compiler root frames include locals and IR temporaries.

    Universal-IR values are stack-spilled by the bootstrap x86 backend. A heap
    result can remain live across another local store, so rooting only declared
    locals is insufficient. This layer adds every heap-typed spill slot to the
    compiler root frame. Later liveness/stack-slot coalescing can shorten those
    root lifetimes without changing the collector contract.
    """

    def _function(self, fn: UFunction) -> None:
        self.fn = fn
        symbol = self._symbol(fn.name)
        total_slots = len(fn.locals) + fn.value_count
        save_count = len(self.CALLEE_SAVED)
        root_locals = [local for local in fn.locals if self._heap_type(local.type_name)]
        values = {}
        for block in fn.blocks:
            for ins in block.instructions:
                if ins.result is not None and self._heap_type(ins.result.type_name):
                    values[ins.result.id] = ins.result
        root_values = [values[key] for key in sorted(values)]

        root_words = 2 + len(root_locals) + len(root_values)
        frame_words = total_slots + save_count + root_words
        frame = ((frame_words * 8 + 15) // 16) * 16
        self.saved_offsets = {
            register: -8 * (total_slots + index + 1)
            for index, register in enumerate(self.CALLEE_SAVED)
        }
        self.gc_root_base_offset = -8 * frame_words

        self.lines.extend([
            f".globl {symbol}", f".type {symbol},@function", f"{symbol}:",
            "    pushq %rbp", "    movq %rsp, %rbp",
        ])
        if frame:
            self.lines.append(f"    subq ${frame}, %rsp")
        for register in self.CALLEE_SAVED:
            self.lines.append(f"    movq {register}, {self.saved_offsets[register]}(%rbp)")

        root_slots = []
        for local in root_locals:
            offset = self._local_offset(local.id)
            self.lines.append(f"    movq $0, {offset}(%rbp)")
            root_slots.append(offset)
        for value in root_values:
            offset = self._value_offset(value)
            self.lines.append(f"    movq $0, {offset}(%rbp)")
            root_slots.append(offset)

        base = self.gc_root_base_offset
        self.lines.extend([
            "    movq .Leri_gc_root_head(%rip), %rax",
            f"    movq %rax, {base}(%rbp)",
            f"    movq ${len(root_slots)}, {base + 8}(%rbp)",
        ])
        for index, offset in enumerate(root_slots):
            self.lines.append(f"    leaq {offset}(%rbp), %rax")
            self.lines.append(f"    movq %rax, {base + 16 + index * 8}(%rbp)")
        self.lines.extend([
            f"    leaq {base}(%rbp), %rax",
            "    movq %rax, .Leri_gc_root_head(%rip)",
        ])

        locations, _ = self._arg_locations([p.type_name for p in fn.parameters])
        for param, (kind, index) in zip(fn.parameters, locations):
            dst = self._local_offset(param.id)
            if kind == "gp":
                self.lines.append(f"    movq {self.GP_ARGS[index]}, {dst}(%rbp)")
            elif kind == "xmm":
                self.lines.append(f"    movsd {self.XMM_ARGS[index]}, {dst}(%rbp)")
            else:
                src = 16 + index * 8
                self.lines.append(f"    movq {src}(%rbp), %r11")
                self.lines.append(f"    movq %r11, {dst}(%rbp)")

        for block in fn.blocks:
            self._block(block)
        self.lines.append(f".size {symbol},.-{symbol}")
