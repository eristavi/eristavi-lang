"""Native GC-rooted recursive File cleanup keeps the first checked failure primary.

Runtime evidence, not yet canonical recursive Function-to-native lowering.
Each native recursive frame independently binds its three File roots plus
the same saved typed FailureContext in a distinct live scope; already-failing
verified cleanup then appends all real close failures in strict inner-first
lexical order while the caller's primary is preserved.
"""
from pathlib import Path
import platform
import unittest

import test_u2_native_cleanup as native_cleanup
import test_freestanding_resource_values as resource


@unittest.skipUnless(
    platform.system()=="Linux" and platform.machine().lower() in ("x86_64","amd64"),
    "recursive owned cleanup is an opt-in Linux x86-64 runtime profile",
)
class U2RecursiveNativeCleanupTests(unittest.TestCase):
    setUpClass=classmethod(resource.FreestandingResourceValueTests.setUpClass.__func__)
    run_probe=resource.FreestandingResourceValueTests.run_probe
    generator=native_cleanup.U2NativeCleanupTests.generator

    def build(self,emitted,depth,fail_close):
        paths={}
        for level in range(1,depth+1):
            for slot in range(3):
                path=self.directory/("recursive-file-%d-%d.txt"%(level,slot))
                path.write_text("open",encoding="utf-8")
                paths[(level,slot)]=path

        asm=[
            ".text",".globl _start","_start:",
            "    subq $48,%rsp",
            "    movq $0,0(%rsp)",
            "    call evn_scope_enter",
            "    movq %rax,8(%rsp)",
            "    movq %rax,%rdi",
            "    movq %rsp,%rsi",
            "    leaq .Louter_root_classes(%rip),%rdx",
            "    movl $1,%ecx",
            "    call evn_bind_roots",
            # The body failure becomes the stable checked primary. Every
            # recursive cleanup failure is attached in encounter order.
            "    leaq .Lprimary_path(%rip),%rdi",
            "    movl $7,%esi",
            "    call evn_text",
            "    movq %rax,%rdi",
            "    leaq .Lprimary_message(%rip),%rsi",
            "    call erist_rt_file_failure",
            "    movq %rax,0(%rsp)",
            "    movq $%d,%%rdi"%depth,
            "    movq %rax,%rsi",
            "    call .Lrecursive_checked_cleanup",
            "    call erist_rt_open_resources",
            "    testq %rax,%rax",
            "    jne .Lresource_test_fail",
            "    xorl %edi,%edi",
            "    call erist_rt_slots_collect",
            "    call erist_rt_text_collect",
            "    call erist_rt_live_failures",
            "    cmpq $%d,%%rax"%(1+(3*depth if fail_close else 0)),
            "    jne .Lresource_test_fail",
            # Walk the REAL linked secondary context in order, not a
            # generated-only reference oracle or a count-only proxy.
            "    movq 0(%rsp),%r14",
            "    cmpq $0,(%r14)",
            "    je .Lresource_test_fail",
            "    leaq 32(%r14),%rdi",
            "    call evn_output",
            "    movq 80(%r14),%r12",
        ]
        if fail_close:
            for i in range(depth*3):
                asm.extend([
                    "    testq %r12,%r12",
                    "    je .Lresource_test_fail",
                    "    movq 8(%r12),%rax",
                    "    movq 8(%rax),%rdi",
                    "    addq $32,%rdi",
                    "    call evn_output",
                    "    movq 88(%r12),%r12",
                ])
        asm.extend([
            "    testq %r12,%r12",
            "    jne .Lresource_test_fail",
            # The typed primary must remain live until the *outer* frame
            # stops rooting it, including after all nested frames exit.
            "    movq $0,0(%rsp)",
            "    call evn_void",
            "    movq %rax,%rsi",
            "    movq 8(%rsp),%rdi",
            "    call evn_scope_leave",
            "    addq $48,%rsp",
            "    call .Lresource_finish",
            "    xorl %edi,%edi",
            "    jmp erist_rt_exit",
            ".Lrecursive_checked_cleanup:",
            "    testq %rdi,%rdi",
            "    je .Lrecursive_base",
            "    pushq %r12",
            "    pushq %r13",
            "    pushq %r14",
            "    pushq %r15",
            "    subq $56,%rsp",
            "    movq $0,0(%rsp)",
            "    movq $0,8(%rsp)",
            "    movq $0,16(%rsp)",
            "    movq %rsi,24(%rsp)",
            "    movq %rdi,40(%rsp)",
            "    call evn_scope_enter",
            "    movq %rax,32(%rsp)",
            "    movq %rax,%rdi",
            "    movq %rsp,%rsi",
            "    leaq .Lrecursive_root_classes(%rip),%rdx",
            "    movl $4,%ecx",
            "    call evn_bind_roots",
        ])
        for slot in range(3):
            asm.extend([
                "    movq 40(%rsp),%r8",
                "    decq %r8",
                "    imulq $3,%r8,%r8",
                "    addq $%d,%%r8"%slot,
                "    shlq $4,%r8",
                "    leaq .Lfile_table(%rip),%r9",
                "    movq (%r9,%r8),%rdi",
                "    movq 8(%r9,%r8),%rsi",
                "    call evn_text",
                "    movq %rax,%rsi",
                "    movl $9,%edi",
                "    xorl %edx,%edx",
                "    call erist_rt_file_open",
                "    movq %%rax,%d(%%rsp)"%(8*slot),
            ])
        asm.extend([
            # Open ancestors are still pinned while the child runs.
            "    movq 40(%rsp),%rdi",
            "    decq %rdi",
            "    movq 24(%rsp),%rsi",
            "    call .Lrecursive_checked_cleanup",
            "    xorl %edi,%edi",
            "    call erist_rt_slots_collect",
            "    call erist_rt_text_collect",
            "    movq %rsp,%rdi",
            "    movq 24(%rsp),%rsi",
            "    call erist_u2_cleanup_32",
            "    cmpq $-1,%rax",
            "    jne .Lresource_test_fail",
            "    cmpq $0,0(%rsp)",
            "    jne .Lresource_test_fail",
            "    cmpq $0,8(%rsp)",
            "    jne .Lresource_test_fail",
            "    cmpq $0,16(%rsp)",
            "    jne .Lresource_test_fail",
            # The parent primary remains rooted throughout cleanup and
            # cannot be replaced with the child's latest close failure.
            "    movq 24(%rsp),%r14",
            "    cmpq $0,(%r14)",
            "    je .Lresource_test_fail",
            "    xorl %edi,%edi",
            "    call erist_rt_slots_collect",
            "    call erist_rt_text_collect",
            "    movq $0,24(%rsp)",
            "    call evn_void",
            "    movq %rax,%rsi",
            "    movq 32(%rsp),%rdi",
            "    call evn_scope_leave",
            "    addq $56,%rsp",
            "    popq %r15",
            "    popq %r14",
            "    popq %r13",
            "    popq %r12",
            ".Lrecursive_base:",
            "    ret",
            ".section .rodata",
            ".Louter_root_classes:","    .byte 5",
            ".Lrecursive_root_classes:","    .byte 1,1,1,5",
            ".Lprimary_path:","    .ascii \"primary\"",
            ".Lprimary_message:","    .asciz \"original\"",
            ".p2align 3",
            ".Lfile_table:",
        ])
        for level in range(1,depth+1):
            for slot in range(3):
                asm.append("    .quad .Lfile_%d_%d, .Lfile_%d_%d_end-.Lfile_%d_%d"%
                           (level,slot,level,slot,level,slot))
        for level in range(1,depth+1):
            for slot in range(3):
                path=paths[(level,slot)]
                content=','.join(str(v) for v in str(path).encode('utf-8'))
                asm.extend([
                    ".Lfile_%d_%d:"%(level,slot),
                    "    .byte "+content,
                    ".Lfile_%d_%d_end:"%(level,slot),
                ])

        expected="original\n"
        if fail_close:
            for level in range(1,depth+1):
                for slot in (2,1,0):
                    expected+=str(paths[(level,slot)])+"\n"
        return emitted+"\n".join(asm)+"\n"+resource.FINISH,expected.encode("utf-8")

    def test_nested_live_frames_preserve_primary_and_ordered_close_failures(self):
        emitted=self.generator()
        self.assertIn("erist_u2_cleanup_32:",emitted)
        self.assertIn("call evn_cleanup_accumulate",emitted)
        for depth,fail_close in ((2,False),(2,True),(5,True)):
            with self.subTest(depth=depth,fail_close=fail_close):
                native,expected=self.build(emitted,depth,fail_close)
                runtime=(resource.close_failures(self.runtime) if fail_close
                         else self.runtime)
                result=self.run_probe(
                    "u2-recursive-%d-%d"%(depth,int(fail_close)),
                    native,runtime=runtime)
                self.assertEqual(
                    (result.returncode,result.stdout,result.stderr),
                    (0,expected,b""))
