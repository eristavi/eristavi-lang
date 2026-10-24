from __future__ import annotations

from .universal_analysis import coalesce_stack_slots, heap_values_live_across_safepoints, value_types
from .universal_ir import BOOL, F64, I64, UFunction
from .x86_64_gc_backend import X86_64GCLinuxBackend


class X86_64PreciseRootGCLinuxBackend(X86_64GCLinuxBackend):
    """Production-facing direct GC composition for the current bootstrap runtime.

    Heap locals always receive stable roots. Heap Universal-IR temporaries receive
    roots only when CFG liveness proves they must survive a GC safe point. Scalar
    temporaries are spill-slot colored so non-overlapping values reuse stack space;
    heap temporary slots remain pinned and unique so root addresses stay stable.

    Heap child traversal still falls back to tracked-pointer payload scanning. The
    next collector layer can attach typed descriptors without changing this root
    frame or stack-allocation contract.
    """

    def __init__(self):
        super().__init__()
        self.value_slots: dict[int, int] = {}
        self.temp_slot_count = 0

    def _value_offset(self, value) -> int:
        if self.fn is None:
            raise ValueError("x86-64 GC backend has no active function")
        slot = self.value_slots.get(value.id)
        if slot is None:
            raise ValueError(f"Universal-IR value %{value.id} has no stack slot")
        return -8 * (len(self.fn.locals) + slot + 1)

    def _function(self, fn: UFunction) -> None:
        self.fn = fn
        symbol = self._symbol(fn.name)

        types = value_types(fn)
        heap_value_ids = {
            value_id
            for value_id, type_name in types.items()
            if type_name not in {I64, F64, BOOL, "void"}
        }
        plan = coalesce_stack_slots(fn, heap_value_ids)
        self.value_slots = plan.slots
        self.temp_slot_count = plan.slot_count

        total_slots = len(fn.locals) + self.temp_slot_count
        save_count = len(self.CALLEE_SAVED)
        root_locals = [local for local in fn.locals if self._heap_type(local.type_name)]
        live_heap_ids = heap_values_live_across_safepoints(fn)

        heap_values = {}
        for block in fn.blocks:
            for instruction in block.instructions:
                value = instruction.result
                if value is not None and value.id in live_heap_ids:
                    heap_values[value.id] = value
        root_values = [heap_values[key] for key in sorted(heap_values)]

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

        base = self.gc_root_base_offset
        root_count = len(root_locals) + len(root_values)
        self.lines.extend([
            "    movq .Leri_gc_root_head(%rip), %rax",
            f"    movq %rax, {base}(%rbp)",
            f"    movq ${root_count}, {base + 8}(%rbp)",
        ])

        root_index = 0
        for local in root_locals:
            offset = self._local_offset(local.id)
            self.lines.append(f"    movq $0, {offset}(%rbp)")
            self.lines.append(f"    leaq {offset}(%rbp), %rax")
            self.lines.append(f"    movq %rax, {base + 16 + root_index * 8}(%rbp)")
            root_index += 1

        for value in root_values:
            offset = self._value_offset(value)
            self.lines.append(f"    movq $0, {offset}(%rbp)")
            self.lines.append(f"    leaq {offset}(%rbp), %rax")
            self.lines.append(f"    movq %rax, {base + 16 + root_index * 8}(%rbp)")
            root_index += 1

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

    @staticmethod
    def _gc_runtime() -> str:
        runtime = X86_64GCLinuxBackend._gc_runtime()
        old = '''.Leri_gc_sweep_free:\n    movq -32(%rbp), %rdi\n    call free@PLT\n    incq .Leri_gc_reclaimed(%rip)\n    movq -40(%rbp), %rax\n    jmp .Leri_gc_sweep_loop'''
        new = '''.Leri_gc_sweep_free:\n    movq %rcx, -48(%rbp)\n    movq -32(%rbp), %rdi\n    call free@PLT\n    movq -48(%rbp), %rcx\n    incq .Leri_gc_reclaimed(%rip)\n    movq -40(%rbp), %rax\n    jmp .Leri_gc_sweep_loop'''
        if old not in runtime:
            raise ValueError("GC runtime sweep template changed unexpectedly")
        return runtime.replace(old, new, 1)
