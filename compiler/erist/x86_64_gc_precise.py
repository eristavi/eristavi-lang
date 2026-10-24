from __future__ import annotations

from .universal_analysis import coalesce_stack_slots, heap_values_live_across_safepoints, value_types
from .universal_ir import (
    BOOL,
    F64,
    I64,
    TEXT,
    UFunction,
    identity_inner,
    list_inner,
    maybe_inner,
    nominal_name,
)
from .x86_64_gc_backend import X86_64GCLinuxBackend


class X86_64PreciseRootGCLinuxBackend(X86_64GCLinuxBackend):
    """Production-facing direct GC composition for the current bootstrap runtime.

    Heap locals always receive stable roots. Heap Universal-IR temporaries receive
    roots only when CFG liveness proves they must survive a GC safe point. Scalar
    temporaries reuse non-overlapping spill slots; heap temporary slots stay pinned
    and unique so compiler roots retain stable addresses.

    Each compiler root also carries a static type descriptor. The collector uses
    those descriptors to traverse nominal fields, maybe/identity wrappers, Lists,
    Text/view leaves and current file-resource records without treating ordinary
    integer/Float payload words as potential pointers. Dynamic checked-error state
    retains the older conservative exact-tracked-pointer scan as a safe fallback.
    """

    DESC_LEAF = 0
    DESC_WRAPPER = 1
    DESC_NOMINAL = 2
    DESC_LIST = 3
    DESC_RESOURCE = 4
    DESC_CONSERVATIVE = 5

    def __init__(self):
        super().__init__()
        self.value_slots: dict[int, int] = {}
        self.temp_slot_count = 0
        self.descriptor_types: set[str] = set()

    def _value_offset(self, value) -> int:
        if self.fn is None:
            raise ValueError("x86-64 GC backend has no active function")
        slot = self.value_slots.get(value.id)
        if slot is None:
            raise ValueError(f"Universal-IR value %{value.id} has no stack slot")
        return -8 * (len(self.fn.locals) + slot + 1)

    def _descriptor_label(self, type_name: str) -> str:
        return f".Leri_gc_desc_{self._type_key(type_name)}"

    @staticmethod
    def _descriptor_heap_type(type_name: str) -> bool:
        return type_name not in {I64, F64, BOOL, "void"}

    def _descriptor_children(self, type_name: str) -> tuple[str, ...]:
        if type_name.startswith("identity<"):
            return (identity_inner(type_name),)
        if type_name.startswith("maybe<"):
            return (maybe_inner(type_name),)
        if type_name.startswith("list<"):
            return (list_inner(type_name),)
        if type_name.startswith("nominal<"):
            item = self.type_defs.get(nominal_name(type_name))
            if item is not None:
                return tuple(field.type_name for field in item.fields)
        return ()

    def _collect_descriptor_types(self, program) -> None:
        self.type_defs = {item.name: item for item in program.types}
        pending: list[str] = []
        for fn in program.functions:
            pending.extend(local.type_name for local in fn.locals if self._descriptor_heap_type(local.type_name))
            for type_name in value_types(fn).values():
                if self._descriptor_heap_type(type_name):
                    pending.append(type_name)

        result: set[str] = set()
        while pending:
            type_name = pending.pop()
            if type_name in result or not self._descriptor_heap_type(type_name):
                continue
            result.add(type_name)
            for child in self._descriptor_children(type_name):
                if self._descriptor_heap_type(child):
                    pending.append(child)
        self.descriptor_types = result

    def _descriptor_reference(self, type_name: str) -> str:
        if not self._descriptor_heap_type(type_name):
            return "0"
        if type_name not in self.descriptor_types:
            self.descriptor_types.add(type_name)
        return self._descriptor_label(type_name)

    def _descriptor_lines(self) -> list[str]:
        lines = [".section .rodata", ".align 8"]
        for type_name in sorted(self.descriptor_types):
            label = self._descriptor_label(type_name)
            lines.append(f"{label}:")
            if type_name == TEXT or type_name.startswith("textview<"):
                lines.append(f"    .quad {self.DESC_LEAF}")
                continue
            if type_name.startswith("resource<"):
                lines.append(f"    .quad {self.DESC_RESOURCE}")
                continue
            if type_name.startswith("identity<"):
                inner = identity_inner(type_name)
                if self._descriptor_heap_type(inner):
                    lines.extend([f"    .quad {self.DESC_WRAPPER}", f"    .quad {self._descriptor_reference(inner)}"])
                else:
                    lines.append(f"    .quad {self.DESC_LEAF}")
                continue
            if type_name.startswith("maybe<"):
                inner = maybe_inner(type_name)
                if self._descriptor_heap_type(inner):
                    lines.extend([f"    .quad {self.DESC_WRAPPER}", f"    .quad {self._descriptor_reference(inner)}"])
                else:
                    lines.append(f"    .quad {self.DESC_LEAF}")
                continue
            if type_name.startswith("list<"):
                inner = list_inner(type_name)
                lines.extend([
                    f"    .quad {self.DESC_LIST}",
                    f"    .quad {self._descriptor_reference(inner) if self._descriptor_heap_type(inner) else 0}",
                ])
                continue
            if type_name.startswith("nominal<"):
                item = self.type_defs.get(nominal_name(type_name))
                if item is not None:
                    lines.extend([f"    .quad {self.DESC_NOMINAL}", f"    .quad {len(item.fields)}"])
                    for field in item.fields:
                        ref = self._descriptor_reference(field.type_name) if self._descriptor_heap_type(field.type_name) else "0"
                        lines.append(f"    .quad {ref}")
                    continue
            lines.append(f"    .quad {self.DESC_CONSERVATIVE}")
        return lines

    def emit(self, program) -> str:
        self._collect_descriptor_types(program)
        assembly = super().emit(program)
        descriptor_text = "\n".join(self._descriptor_lines())
        marker = ".text\n"
        if marker not in assembly:
            raise ValueError("direct GC backend could not locate text section for descriptors")
        return assembly.replace(marker, descriptor_text + "\n.text\n", 1)

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

        root_count = len(root_locals) + len(root_values)
        # Root frame: [previous, count, address0, descriptor0, address1, descriptor1, ...].
        root_words = 2 + root_count * 2
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
            self.lines.append(f"    movq %rax, {base + 16 + root_index * 16}(%rbp)")
            self.lines.append(f"    leaq {self._descriptor_label(local.type_name)}(%rip), %rax")
            self.lines.append(f"    movq %rax, {base + 24 + root_index * 16}(%rbp)")
            root_index += 1

        for value in root_values:
            offset = self._value_offset(value)
            self.lines.append(f"    movq $0, {offset}(%rbp)")
            self.lines.append(f"    leaq {offset}(%rbp), %rax")
            self.lines.append(f"    movq %rax, {base + 16 + root_index * 16}(%rbp)")
            self.lines.append(f"    leaq {self._descriptor_label(value.type_name)}(%rip), %rax")
            self.lines.append(f"    movq %rax, {base + 24 + root_index * 16}(%rbp)")
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

        typed_helpers = r'''
# rdi=payload candidate. Mark the tracked allocation itself without scanning.
.Leri_gc_mark_allocation_only:
    testq %rdi, %rdi
    je .Leri_gc_mark_alloc_done
    pushq %rbp
    movq %rsp, %rbp
    call .Leri_gc_find
    testq %rax, %rax
    je .Leri_gc_mark_alloc_leave
    movq $1, 16(%rax)
.Leri_gc_mark_alloc_leave:
    leave
.Leri_gc_mark_alloc_done:
    ret

# rdi=payload candidate, rsi=descriptor.
# descriptor kinds: 0 leaf, 1 wrapper, 2 nominal, 3 list, 4 resource,
# 5 conservative fallback.
.Leri_gc_mark_typed:
    testq %rdi, %rdi
    je .Leri_gc_mark_typed_ret
    pushq %rbp
    movq %rsp, %rbp
    subq $96, %rsp
    movq %rdi, -8(%rbp)
    movq %rsi, -16(%rbp)
    call .Leri_gc_find
    testq %rax, %rax
    je .Leri_gc_mark_typed_done
    cmpq $0, 16(%rax)
    jne .Leri_gc_mark_typed_done
    movq $1, 16(%rax)
    movq %rax, -24(%rbp)
    movq -16(%rbp), %rax
    testq %rax, %rax
    je .Leri_gc_mark_typed_conservative
    movq 0(%rax), %rcx
    cmpq $0, %rcx
    je .Leri_gc_mark_typed_done
    cmpq $1, %rcx
    je .Leri_gc_mark_typed_wrapper
    cmpq $2, %rcx
    je .Leri_gc_mark_typed_nominal
    cmpq $3, %rcx
    je .Leri_gc_mark_typed_list
    cmpq $4, %rcx
    je .Leri_gc_mark_typed_resource
    jmp .Leri_gc_mark_typed_conservative

.Leri_gc_mark_typed_wrapper:
    movq -16(%rbp), %rax
    movq 8(%rax), %rsi
    testq %rsi, %rsi
    je .Leri_gc_mark_typed_done
    movq -8(%rbp), %rax
    movq 0(%rax), %rdi
    call .Leri_gc_mark_typed
    jmp .Leri_gc_mark_typed_done

.Leri_gc_mark_typed_nominal:
    movq -16(%rbp), %rax
    movq 8(%rax), %rcx
    movq %rcx, -32(%rbp)
    movq $0, -40(%rbp)
.Leri_gc_mark_typed_nominal_loop:
    movq -40(%rbp), %rcx
    cmpq -32(%rbp), %rcx
    jae .Leri_gc_mark_typed_done
    movq -16(%rbp), %rax
    movq 16(%rax,%rcx,8), %rsi
    testq %rsi, %rsi
    je .Leri_gc_mark_typed_nominal_next
    movq -8(%rbp), %rax
    movq (%rax,%rcx,8), %rdi
    call .Leri_gc_mark_typed
.Leri_gc_mark_typed_nominal_next:
    incq -40(%rbp)
    jmp .Leri_gc_mark_typed_nominal_loop

.Leri_gc_mark_typed_list:
    movq -8(%rbp), %rax
    movq 16(%rax), %rdi
    movq %rdi, -32(%rbp)
    testq %rdi, %rdi
    je .Leri_gc_mark_typed_done
    call .Leri_gc_mark_allocation_only
    movq -16(%rbp), %rax
    movq 8(%rax), %rcx
    movq %rcx, -40(%rbp)
    testq %rcx, %rcx
    je .Leri_gc_mark_typed_done
    movq -8(%rbp), %rax
    movq 0(%rax), %rcx
    movq %rcx, -48(%rbp)
    movq $0, -56(%rbp)
.Leri_gc_mark_typed_list_loop:
    movq -56(%rbp), %rcx
    cmpq -48(%rbp), %rcx
    jae .Leri_gc_mark_typed_done
    movq -32(%rbp), %rax
    movq (%rax,%rcx,8), %rdi
    movq -40(%rbp), %rsi
    call .Leri_gc_mark_typed
    incq -56(%rbp)
    jmp .Leri_gc_mark_typed_list_loop

.Leri_gc_mark_typed_resource:
    # Current std.files resource record: word0 FILE*, word1 tracked path buffer.
    movq -8(%rbp), %rax
    movq 8(%rax), %rdi
    call .Leri_gc_mark_allocation_only
    jmp .Leri_gc_mark_typed_done

.Leri_gc_mark_typed_conservative:
    movq -24(%rbp), %rax
    movq 8(%rax), %rcx
    shrq $3, %rcx
    movq %rcx, -32(%rbp)
    movq $0, -40(%rbp)
.Leri_gc_mark_typed_conservative_loop:
    movq -40(%rbp), %rcx
    cmpq -32(%rbp), %rcx
    jae .Leri_gc_mark_typed_done
    movq -8(%rbp), %rax
    movq (%rax,%rcx,8), %rdi
    call .Leri_gc_mark
    incq -40(%rbp)
    jmp .Leri_gc_mark_typed_conservative_loop

.Leri_gc_mark_typed_done:
    leave
.Leri_gc_mark_typed_ret:
    ret

'''
        marker = "# Free a tracked payload immediately. Used by runtime temporaries and by\n"
        if marker not in runtime:
            raise ValueError("GC runtime allocation marker changed unexpectedly")
        runtime = runtime.replace(marker, typed_helpers + marker, 1)

        old_roots = r'''.Leri_gc_frame_roots:
    movq -24(%rbp), %rax
    cmpq -16(%rbp), %rax
    jae .Leri_gc_next_frame
    movq -8(%rbp), %rcx
    movq 16(%rcx,%rax,8), %rdx
    movq (%rdx), %rdi
    call .Leri_gc_mark
    incq -24(%rbp)
    jmp .Leri_gc_frame_roots'''
        new_roots = r'''.Leri_gc_frame_roots:
    movq -24(%rbp), %rax
    cmpq -16(%rbp), %rax
    jae .Leri_gc_next_frame
    leaq (%rax,%rax), %rdx
    movq -8(%rbp), %rcx
    movq 16(%rcx,%rdx,8), %r8
    movq (%r8), %rdi
    movq 24(%rcx,%rdx,8), %rsi
    call .Leri_gc_mark_typed
    incq -24(%rbp)
    jmp .Leri_gc_frame_roots'''
        if old_roots not in runtime:
            raise ValueError("GC root-frame runtime template changed unexpectedly")
        runtime = runtime.replace(old_roots, new_roots, 1)

        old_sweep = '''.Leri_gc_sweep_free:\n    movq -32(%rbp), %rdi\n    call free@PLT\n    incq .Leri_gc_reclaimed(%rip)\n    movq -40(%rbp), %rax\n    jmp .Leri_gc_sweep_loop'''
        new_sweep = '''.Leri_gc_sweep_free:\n    movq %rcx, -48(%rbp)\n    movq -32(%rbp), %rdi\n    call free@PLT\n    movq -48(%rbp), %rcx\n    incq .Leri_gc_reclaimed(%rip)\n    movq -40(%rbp), %rax\n    jmp .Leri_gc_sweep_loop'''
        if old_sweep not in runtime:
            raise ValueError("GC runtime sweep template changed unexpectedly")
        return runtime.replace(old_sweep, new_sweep, 1)
