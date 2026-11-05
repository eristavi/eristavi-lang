"""Physical owned-runtime U2 identity-cycle GC root lifetime probe.

This checks the existing root ABI for an explicitly created graph cycle. It
does not claim that the redesigned canonical UIR emits identity instructions
or that File cleanup has been integrated with identity SSA.
"""
import platform
import unittest

import test_freestanding_graph_values as graph


@unittest.skipUnless(platform.system()=="Linux" and
                     platform.machine().lower() in ("x86_64","amd64"),
                     "owned identity-cycle probe requires Linux x86-64")
class U2IdentityGCCleanupTests(unittest.TestCase):
    setUpClass=classmethod(graph.FreestandingGraphValueTests.setUpClass.__func__)
    run_probe=graph.FreestandingGraphValueTests.run_probe

    def test_two_alias_roots_keep_cyclic_graph_until_last_release(self):
        # Three physical graph nodes form an 8->9->10->8 cycle, using the
        # same typed node tags as the independent 20,000-depth graph test.
        # The first (class-1) managed identity root survives one alias's
        # release. The other root alone keeps the entire cycle live.
        # Clearing both roots must reclaim every graph node under REAL GC.
        asm=r"""
.text
.globl _start
_start:
    xorl %ebp,%ebp
    call evn_scope_enter
    movq %rax,%r15
    movq %rax,%rdi
    leaq .Lidentity_root_words(%rip),%rsi
    leaq .Lidentity_root_classes(%rip),%rdx
    movl $2,%ecx
    call evn_bind_roots

    movl $1,%edi
    call erist_rt_graph_new_object
    movq %rax,%r12
    movl $1,%edi
    call erist_rt_graph_new_object
    movq %rax,%r13
    movl $1,%edi
    call erist_rt_graph_new_object
    movq %rax,%r14

    movq 8(%r12),%rax
    movq $8,(%rax)
    movq %r13,8(%rax)
    movq 8(%r13),%rax
    movq $9,(%rax)
    movq %r14,8(%rax)
    movq 8(%r14),%rax
    movq $10,(%rax)
    movq %r12,8(%rax)
    movl $10,%edi
    movq %r12,%rsi
    call erist_rt_value_new
    movq %rax,.Lidentity_root_words(%rip)
    movq %rax,.Lidentity_root_words+8(%rip)
    xorl %edi,%edi
    call erist_rt_slots_collect
    call erist_rt_text_collect
    call erist_rt_graph_live_objects
    cmpq $3,%rax
    jne .Lgraph_test_fail

    # Explicit alias release cannot invalidate a retained cycle.
    movq $0,.Lidentity_root_words(%rip)
    xorl %edi,%edi
    call erist_rt_slots_collect
    call erist_rt_text_collect
    call erist_rt_graph_live_objects
    cmpq $3,%rax
    jne .Lgraph_test_fail

    # Once the last identity handle root dies, the whole strongly
    # connected component must be reclaimed (not just the outer slot).
    movq $0,.Lidentity_root_words+8(%rip)
    xorl %edi,%edi
    call erist_rt_slots_collect
    call erist_rt_text_collect
    call erist_rt_graph_live_objects
    testq %rax,%rax
    jne .Lgraph_test_fail

    call evn_void
    movq %rax,%rsi
    movq %r15,%rdi
    call evn_scope_leave
    jmp .Lgraph_finish
.bss
.p2align 3
.Lidentity_root_words:
.zero 16
.section .rodata
.Lidentity_root_classes:
.byte 1,1
"""
        result=self.run_probe("u2-two-identity-cycle-roots",asm+graph.FINISH)
        self.assertEqual((result.returncode,result.stdout,result.stderr),
                         (0,b"",b""))
