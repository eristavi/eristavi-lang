from __future__ import annotations

from .universal_ir import BOOL, F64, I64, UFunction, UInstruction
from .x86_64_direct_backend import X86_64DirectLinuxBackend


class X86_64GCLinuxBackend(X86_64DirectLinuxBackend):
    """Direct backend with bootstrap automatic memory reclamation.

    All compiler/runtime malloc/free/realloc calls are routed through a tracked,
    non-moving mark-and-sweep heap. Each compiled function links a root frame
    containing the addresses of its heap-typed Eristavi locals. Collection is
    performed only after `store_local`, a compiler-known statement boundary at
    which newly produced heap values have reached a rooted local and transient
    Universal-IR values are no longer required by the completed store.

    Root discovery is therefore compiler-described rather than a blind machine
    stack scan. Heap payload traversal still recognizes child allocations by
    exact tracked pointer identity while scanning payload words; typed heap
    descriptor masks remain a later production refinement. Deterministic
    external resources remain separate from GC ownership.
    """

    def __init__(self):
        super().__init__()
        self.gc_root_base_offset: int | None = None

    @staticmethod
    def _heap_type(type_name: str) -> bool:
        return type_name not in (I64, F64, BOOL, "void")

    def _function(self, fn: UFunction) -> None:
        # This mirrors the base System-V frame layout and extends it with a
        # linked compiler root frame: [prev, count, &root0, &root1, ...].
        self.fn = fn
        symbol = self._symbol(fn.name)
        total_slots = len(fn.locals) + fn.value_count
        save_count = len(self.CALLEE_SAVED)
        root_locals = [local for local in fn.locals if self._heap_type(local.type_name)]
        root_words = 2 + len(root_locals)
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
            f"    movq ${len(root_locals)}, {base + 8}(%rbp)",
        ])
        for index, local in enumerate(root_locals):
            # Zero the root itself before linking the frame so future lexical
            # locals cannot accidentally retain an allocation before execution
            # reaches their declaration.
            self.lines.append(f"    movq $0, {self._local_offset(local.id)}(%rbp)")
            self.lines.append(f"    leaq {self._local_offset(local.id)}(%rbp), %rax")
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
                self.lines.append(f"    movq {src}(%rbp), %rax")
                self.lines.append(f"    movq %rax, {dst}(%rbp)")

        for block in fn.blocks:
            self._block(block)
        self.lines.append(f".size {symbol},.-{symbol}")

    def _restore_saved(self) -> None:
        if self.gc_root_base_offset is None:
            raise ValueError("GC root frame is not initialized")
        self.lines.extend([
            f"    movq {self.gc_root_base_offset}(%rbp), %rax",
            "    movq %rax, .Leri_gc_root_head(%rip)",
        ])
        super()._restore_saved()

    def _instruction(self, ins: UInstruction) -> None:
        super()._instruction(ins)
        if ins.op == "store_local":
            # Safe point: all function root frames are linked and the value just
            # stored is visible through its declared local slot.
            self.lines.append("    call .Leri_gc_collect")

    def emit(self, program) -> str:
        assembly = super().emit(program)

        # Route only code emitted by the ordinary backend through the tracked
        # allocator. The collector runtime appended below deliberately retains
        # raw libc malloc/free calls for its own metadata blocks.
        assembly = assembly.replace("call malloc@PLT", "call .Leri_gc_alloc")
        assembly = assembly.replace("call free@PLT", "call .Leri_gc_free")
        assembly = assembly.replace("call realloc@PLT", "call .Leri_gc_realloc")

        marker = '.section .note.GNU-stack,"",@progbits'
        runtime = self._gc_runtime()
        if marker not in assembly:
            raise ValueError("direct GC backend could not locate assembly trailer")
        return assembly.replace(marker, runtime + "\n" + marker, 1)

    @staticmethod
    def _gc_runtime() -> str:
        return r'''
.section .bss
.align 8
.Leri_gc_head:
    .quad 0
.Leri_gc_root_head:
    .quad 0
.Leri_gc_allocations:
    .quad 0
.Leri_gc_collections:
    .quad 0
.Leri_gc_reclaimed:
    .quad 0
.text

# Allocation header (32 bytes before payload):
#   +0 next header, +8 payload size, +16 mark, +24 reserved.
# rdi=size -> rax=payload.
.Leri_gc_alloc:
    pushq %rbp
    movq %rsp, %rbp
    subq $32, %rsp
    movq %rdi, -8(%rbp)
    addq $32, %rdi
    call malloc@PLT
    testq %rax, %rax
    je .Leri_gc_oom
    movq .Leri_gc_head(%rip), %rcx
    movq %rcx, 0(%rax)
    movq -8(%rbp), %rcx
    movq %rcx, 8(%rax)
    movq $0, 16(%rax)
    movq $0, 24(%rax)
    movq %rax, .Leri_gc_head(%rip)
    incq .Leri_gc_allocations(%rip)
    addq $32, %rax
    leave
    ret
.Leri_gc_oom:
    movl $111, %edi
    call exit@PLT

# rdi=payload candidate -> rax=allocation header or zero.
.Leri_gc_find:
    movq .Leri_gc_head(%rip), %rax
.Leri_gc_find_loop:
    testq %rax, %rax
    je .Leri_gc_find_none
    leaq 32(%rax), %rcx
    cmpq %rdi, %rcx
    je .Leri_gc_find_done
    movq 0(%rax), %rax
    jmp .Leri_gc_find_loop
.Leri_gc_find_none:
    xorq %rax, %rax
.Leri_gc_find_done:
    ret

# rdi=payload candidate. Exact payload pointers are marked; payload words are
# recursively examined for child allocation pointers.
.Leri_gc_mark:
    pushq %rbp
    movq %rsp, %rbp
    subq $48, %rsp
    movq %rdi, -8(%rbp)
    call .Leri_gc_find
    testq %rax, %rax
    je .Leri_gc_mark_done
    cmpq $0, 16(%rax)
    jne .Leri_gc_mark_done
    movq $1, 16(%rax)
    movq %rax, -16(%rbp)
    movq 8(%rax), %rcx
    shrq $3, %rcx
    movq %rcx, -24(%rbp)
    movq $0, -32(%rbp)
.Leri_gc_mark_words:
    movq -32(%rbp), %rax
    cmpq -24(%rbp), %rax
    jae .Leri_gc_mark_done
    movq -8(%rbp), %rcx
    movq (%rcx,%rax,8), %rdi
    call .Leri_gc_mark
    incq -32(%rbp)
    jmp .Leri_gc_mark_words
.Leri_gc_mark_done:
    leave
    ret

# Free a tracked payload immediately. Used by runtime temporaries and by
# compiler operations that explicitly resize storage.
.Leri_gc_free:
    testq %rdi, %rdi
    je .Leri_gc_free_ret
    pushq %rbp
    movq %rsp, %rbp
    subq $32, %rsp
    movq %rdi, -8(%rbp)
    xorq %rcx, %rcx
    movq .Leri_gc_head(%rip), %rax
.Leri_gc_free_find:
    testq %rax, %rax
    je .Leri_gc_free_unknown
    leaq 32(%rax), %rdx
    cmpq -8(%rbp), %rdx
    je .Leri_gc_free_found
    movq %rax, %rcx
    movq 0(%rax), %rax
    jmp .Leri_gc_free_find
.Leri_gc_free_found:
    movq %rax, -16(%rbp)
    movq 0(%rax), %rdx
    testq %rcx, %rcx
    je .Leri_gc_free_head
    movq %rdx, 0(%rcx)
    jmp .Leri_gc_free_raw
.Leri_gc_free_head:
    movq %rdx, .Leri_gc_head(%rip)
.Leri_gc_free_raw:
    movq -16(%rbp), %rdi
    call free@PLT
    leave
.Leri_gc_free_ret:
    ret
.Leri_gc_free_unknown:
    # Runtime code should never ask the tracked allocator to free an unknown
    # payload. Ignore it rather than risking a static/foreign pointer.
    leave
    ret

# rdi=old payload (or null), rsi=new size -> rax=new payload.
.Leri_gc_realloc:
    pushq %rbp
    movq %rsp, %rbp
    subq $64, %rsp
    movq %rdi, -8(%rbp)
    movq %rsi, -16(%rbp)
    testq %rdi, %rdi
    je .Leri_gc_realloc_new
    call .Leri_gc_find
    testq %rax, %rax
    je .Leri_gc_oom
    movq 8(%rax), %rcx
    movq %rcx, -24(%rbp)
    movq -16(%rbp), %rdi
    call .Leri_gc_alloc
    movq %rax, -32(%rbp)
    movq -24(%rbp), %rdx
    cmpq -16(%rbp), %rdx
    jbe .Leri_gc_realloc_copy
    movq -16(%rbp), %rdx
.Leri_gc_realloc_copy:
    movq -32(%rbp), %rdi
    movq -8(%rbp), %rsi
    call memcpy@PLT
    movq -8(%rbp), %rdi
    call .Leri_gc_free
    movq -32(%rbp), %rax
    leave
    ret
.Leri_gc_realloc_new:
    movq -16(%rbp), %rdi
    call .Leri_gc_alloc
    leave
    ret

# Walk compiler-emitted root frames, mark checked-error globals, then sweep.
.Leri_gc_collect:
    pushq %rbp
    movq %rsp, %rbp
    subq $80, %rsp
    incq .Leri_gc_collections(%rip)
    movq .Leri_gc_root_head(%rip), %rax
    movq %rax, -8(%rbp)
.Leri_gc_frame_loop:
    movq -8(%rbp), %rax
    testq %rax, %rax
    je .Leri_gc_globals
    movq 8(%rax), %rcx
    movq %rcx, -16(%rbp)
    movq $0, -24(%rbp)
.Leri_gc_frame_roots:
    movq -24(%rbp), %rax
    cmpq -16(%rbp), %rax
    jae .Leri_gc_next_frame
    movq -8(%rbp), %rcx
    movq 16(%rcx,%rax,8), %rdx
    movq (%rdx), %rdi
    call .Leri_gc_mark
    incq -24(%rbp)
    jmp .Leri_gc_frame_roots
.Leri_gc_next_frame:
    movq -8(%rbp), %rax
    movq 0(%rax), %rax
    movq %rax, -8(%rbp)
    jmp .Leri_gc_frame_loop

.Leri_gc_globals:
    # Checked-error globals are roots outside ordinary function locals.
    movq .Leri_error_value(%rip), %rdi
    call .Leri_gc_mark
    movq .Leri_error_message(%rip), %rdi
    call .Leri_gc_mark
    movq .Leri_error_secondary_head(%rip), %rdi
    call .Leri_gc_mark

    xorq %rcx, %rcx
    movq .Leri_gc_head(%rip), %rax
.Leri_gc_sweep_loop:
    testq %rax, %rax
    je .Leri_gc_sweep_done
    cmpq $0, 16(%rax)
    jne .Leri_gc_keep
    movq %rax, -32(%rbp)
    movq 0(%rax), %rdx
    movq %rdx, -40(%rbp)
    testq %rcx, %rcx
    je .Leri_gc_sweep_head
    movq %rdx, 0(%rcx)
    jmp .Leri_gc_sweep_free
.Leri_gc_sweep_head:
    movq %rdx, .Leri_gc_head(%rip)
.Leri_gc_sweep_free:
    movq -32(%rbp), %rdi
    call free@PLT
    incq .Leri_gc_reclaimed(%rip)
    movq -40(%rbp), %rax
    jmp .Leri_gc_sweep_loop
.Leri_gc_keep:
    movq $0, 16(%rax)
    movq %rax, %rcx
    movq 0(%rax), %rax
    jmp .Leri_gc_sweep_loop
.Leri_gc_sweep_done:
    leave
    ret
'''
