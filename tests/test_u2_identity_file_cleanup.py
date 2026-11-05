"""Native identity alias roots remain live through real checked File cleanup.

This composes two previously verified owned-runtime primitives in one live
scope chain. It does NOT claim automatic canonical identity-File lowering.
"""
import platform
import unittest

import test_freestanding_resource_values as resource
import test_u2_native_cleanup as cleanup


def identity_file_descriptors():
    # Preserve the checked File/FileError runtime types 0..9 exactly,
    # adding three private one-field graph nodes only to this linked probe.
    text=resource.descriptors()
    marker=".globl ev_types_end\nev_types_end:\n.section .rodata\n"
    assert text.count(marker)==1
    more=""
    names=""
    for index,next_type in ((10,11),(11,12),(12,10)):
        more+=f".long 6,0\n.quad .Lu2_cycle_name{index},1,.Lu2_cycle_field{index}\n"
        names+=(f".Lu2_cycle_name{index}:\n.asciz \"Cycle{index}\"\n"
                f".p2align 2\n.Lu2_cycle_field{index}:\n.long {next_type}\n")
    return text.replace(marker,more+marker,1)+names


@unittest.skipUnless(platform.system()=="Linux" and
                     platform.machine().lower() in ("x86_64","amd64"),
                     "owned identity/checked File cleanup needs Linux x86-64")
class U2IdentityFileCleanupTests(unittest.TestCase):
    setUpClass=classmethod(resource.FreestandingResourceValueTests.setUpClass.__func__)
    run_probe=resource.FreestandingResourceValueTests.run_probe
    generator=cleanup.U2NativeCleanupTests.generator
    code_bytes=staticmethod(cleanup.U2NativeCleanupTests.code_bytes)
    assembly=cleanup.U2NativeCleanupTests.assembly

    def test_two_identity_aliases_survive_checked_cleanup_and_ordered_failures(self):
        emitted=self.generator()
        paths=[self.directory/f"identity-file-{i}.txt" for i in range(3)]
        for path in paths:
            path.write_text("open",encoding="utf-8")
        code=self.assembly(True,True,emitted,paths)
        bound=(
            "    leaq .Lu2_native_caller_classes(%rip),%rdx\n"
            "    movl $4,%ecx\n"
            "    call evn_bind_roots\n"
        )
        self.assertEqual(code.count(bound),1)
        prepare=r"""    # A second nested live scope protects two aliases of one graph cycle.
    call evn_scope_enter
    movq %rax,40(%rsp)
    movq %rax,%rdi
    leaq .Lu2_cycle_root_words(%rip),%rsi
    leaq .Lu2_cycle_root_classes(%rip),%rdx
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
    movq $10,(%rax)
    movq %r13,8(%rax)
    movq 8(%r13),%rax
    movq $11,(%rax)
    movq %r14,8(%rax)
    movq 8(%r14),%rax
    movq $12,(%rax)
    movq %r12,8(%rax)
    movl $10,%edi
    movq %r12,%rsi
    call erist_rt_value_new
    movq %rax,.Lu2_cycle_root_words(%rip)
    movq %rax,.Lu2_cycle_root_words+8(%rip)

"""
        code=code.replace(bound,bound+prepare,1)
        status=(
            "    jne .Lresource_test_fail\n"
            "    cmpq $0,0(%rsp)\n"
        )
        self.assertEqual(code.count(status),1)
        during=r"""    # After the real checked File close, original primary and ordered
    # secondary FileErrors coexist with the caller's graph aliases.
    xorl %edi,%edi
    call erist_rt_slots_collect
    call erist_rt_text_collect
    call erist_rt_graph_live_objects
    cmpq $3,%rax
    jb .Lresource_test_fail
    movq $0,.Lu2_cycle_root_words(%rip)
    xorl %edi,%edi
    call erist_rt_slots_collect
    call erist_rt_text_collect
    call erist_rt_graph_live_objects
    cmpq $3,%rax
    jb .Lresource_test_fail

"""
        code=code.replace(status,status.replace("    cmpq $0,0(%rsp)\n","")+during+
                          "    cmpq $0,0(%rsp)\n",1)
        release="    movq $0,24(%rsp)\n    call evn_void\n"
        self.assertEqual(code.count(release),1)
        before_release=r"""    # The last identity alias and its registered scope are retired
    # before the class-5 File failure root and the resource owner scope.
    movq $0,.Lu2_cycle_root_words+8(%rip)
    call evn_void
    movq %rax,%rsi
    movq 40(%rsp),%rdi
    call evn_scope_leave
"""
        code=code.replace(release,before_release+release,1)
        code+="""\n.bss
.p2align 3
.Lu2_cycle_root_words:
.zero 16
.section .rodata
.Lu2_cycle_root_classes:
.byte 1,1
"""
        result=self.run_probe("u2-identity-with-checked-files",
            identity_file_descriptors()+code,
            runtime=resource.close_failures(self.runtime),types=False)
        expected=("original\n"+str(paths[2])+"\n"+
                  str(paths[1])+"\n"+str(paths[0])+"\n").encode()
        self.assertEqual((result.returncode,result.stdout,result.stderr),
                         (0,expected,b""))
