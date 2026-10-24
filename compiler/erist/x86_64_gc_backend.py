from __future__ import annotations

from .universal_ir import BOOL, F64, I64, UInstruction
from .x86_64_direct_backend import X86_64DirectLinuxBackend


class X86_64GCLinuxBackend(X86_64DirectLinuxBackend):
    """Direct backend with bootstrap automatic memory reclamation.

    All compiler/runtime malloc/free/realloc calls are routed through a tracked
    non-moving heap. Collection happens only at compiler-known safe points after
    a heap-producing Universal-IR result has been spilled to its stack slot, so
    helper routines can freely construct nested graphs without exposing
    half-built objects to a collector.

    The current collector has precise allocation boundaries and exact pointer
    identity, while root/heap discovery scans machine words conservatively. This
    is safe and already reclaims unreachable graphs, but it intentionally leaves
    fully typed/precise root maps as the next production-hardening step.
    Deterministic external resources remain outside GC ownership.
    """

    @staticmethod
    def _heap_type(type_name: str) -> bool:
        return type_name not in (I64, F64, BOOL, "void")

    def _store_result(self, instruction: UInstruction, register: str = "%rax") -> None:
        super()._store_result(instruction, register)
        if instruction.result is not None and self._heap_type(instruction.result.type_name):
            self.lines.append("    call .Leri_gc_collect")

    def _store_result_f64(self, instruction: UInstruction, register: str = "%xmm0") -> None:
        # Floating-point values are never heap roots.
        super()._store_result_f64(instruction, register)

    def emit(self, program) -> str:
        assembly = super().emit(program)

        # Route only code emitted by the ordinary backend through the tracked
        # allocator. The collector runtime appended below deliberately retains
        # raw libc malloc/free calls for its own metadata blocks.
        assembly = assembly.replace("call malloc@PLT", "call .Leri_gc_alloc")
        assembly = assembly.replace("call free@PLT", "call .Leri_gc_free")
        assembly = assembly.replace("call realloc@PLT", "call .Leri_gc_realloc")

        main_prologue = "main:\n    pushq %rbp\n    movq %rsp, %rbp"
        if main_prologue in assembly:
            assembly = assembly.replace(
                main_prologue,
                main_prologue + "\n    movq %rbp, .Leri_gc_stack_bottom(%rip)",
                1,
            )
        else:
            raise ValueError("direct GC backend could not locate entry stack frame")

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
.Leri_gc_stack_bottom:
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
    # payload. Ignore it rather than risking freeing a static/foreign pointer.
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

# Mark roots by scanning active machine stack words for exact tracked payload
# pointers, then sweep unmarked headers. Collection occurs only at explicit
# compiler safe points after heap results have been spilled.
.Leri_gc_collect:
    pushq %rbp
    movq %rsp, %rbp
    subq $64, %rsp
    incq .Leri_gc_collections(%rip)
    leaq 16(%rbp), %rax
    movq %rax, -8(%rbp)
    movq .Leri_gc_stack_bottom(%rip), %rax
    movq %rax, -16(%rbp)
.Leri_gc_root_loop:
    movq -8(%rbp), %rax
    cmpq -16(%rbp), %rax
    ja .Leri_gc_roots_done
    movq (%rax), %rdi
    call .Leri_gc_mark
    addq $8, -8(%rbp)
    jmp .Leri_gc_root_loop
.Leri_gc_roots_done:
    # Checked-error globals are roots outside the ordinary stack.
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
    movq %rax, -24(%rbp)
    movq 0(%rax), %rdx
    movq %rdx, -32(%rbp)
    testq %rcx, %rcx
    je .Leri_gc_sweep_head
    movq %rdx, 0(%rcx)
    jmp .Leri_gc_sweep_free
.Leri_gc_sweep_head:
    movq %rdx, .Leri_gc_head(%rip)
.Leri_gc_sweep_free:
    movq -24(%rbp), %rdi
    call free@PLT
    incq .Leri_gc_reclaimed(%rip)
    movq -32(%rbp), %rax
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
