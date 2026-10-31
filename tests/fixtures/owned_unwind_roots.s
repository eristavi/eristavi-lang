# Direct owned runtime ABI probe: clear abandoned value roots only.
.data
.p2align 3
.Lunwind_probe_roots:
    .quad 0,0,0,0
.Lunwind_probe_classes:
    .byte 1,1,2,1
.globl ev_types
ev_types:
    .long 0,0
    .quad .Lunwind_probe_name,0,0
    .long 1,0
    .quad .Lunwind_probe_name,0,0
.Lunwind_probe_name:
    .asciz "Int"
.text
.globl erist_entry
erist_entry:
    xorl %eax,%eax
    ret
.globl _start
_start:
    call evn_scope_enter
    movq %rax,%rbx
    movq %rax,%rdi
    leaq .Lunwind_probe_roots(%rip),%rsi
    leaq .Lunwind_probe_classes(%rip),%rdx
    movl $4,%ecx
    call evn_bind_roots
    movl $7,%edi
    call evn_int
    movq %rax,.Lunwind_probe_roots(%rip)
    call evn_frame
    movq %rax,%r12
    movq %rax,%rdi
    call setjmp
    testl %eax,%eax
    jne .Lunwind_probe_caught
    movl $9,%edi
    call evn_int
    movq %rax,.Lunwind_probe_roots+8(%rip)
    movq %rax,.Lunwind_probe_roots+16(%rip)
    movq %rax,.Lunwind_probe_roots+24(%rip)
    # Reproduce the native checked-jump ABI without a source failure payload.
    movq $1,104(%r12)
    movq %r12,%rdi
    movl $1,%esi
    call longjmp
.Lunwind_probe_caught:
    movq %r12,%rdi
    call evn_pop
    cmpq $0,.Lunwind_probe_roots+8(%rip)
    jne .Lunwind_probe_bad
    cmpq $0,.Lunwind_probe_roots+24(%rip)
    jne .Lunwind_probe_bad
    cmpq $0,.Lunwind_probe_roots+16(%rip)
    je .Lunwind_probe_bad
    movq .Lunwind_probe_roots(%rip),%rax
    cmpq $7,8(%rax)
    jne .Lunwind_probe_bad
    cmpq $1,.Lvalue_slot_count(%rip)
    jne .Lunwind_probe_bad
    call evn_frame
    movq %rax,%r12
    movq %rax,%rdi
    call setjmp
    testl %eax,%eax
    jne .Lunwind_probe_bad
    movl $42,%edi
    call evn_int
    movq %rax,.Lunwind_probe_roots+8(%rip)
    movq %r12,%rdi
    call evn_pop
    movq .Lunwind_probe_roots+8(%rip),%rax
    testq %rax,%rax
    je .Lunwind_probe_bad
    cmpq $42,8(%rax)
    jne .Lunwind_probe_bad
    call erist_rt_live_handlers
    testq %rax,%rax
    jne .Lunwind_probe_bad
    xorl %edi,%edi
    jmp .Lunwind_probe_exit
.Lunwind_probe_bad:
    movl $1,%edi
.Lunwind_probe_exit:
    movl $60,%eax
    syscall
.section .note.GNU-stack,"",@progbits
