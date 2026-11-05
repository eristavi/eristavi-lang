"""Native identity transfer on both verified checked File.close continuations.

The emitter is target-specific, but verification consumes only canonical
metadata; the caller still owns a live class-1 and class-5 root scope.
"""
from pathlib import Path
import platform
import re
import subprocess
import unittest

from compiler.erist.cli import build_native
import test_freestanding_graph_values as graph

ROOT=Path(__file__).resolve().parents[1]


@unittest.skipUnless(platform.system()=="Linux" and
                     platform.machine().lower() in ("x86_64","amd64"),
                     "native checked identity edge requires Linux x86-64")
class U2CheckedIdentityEdgeTests(unittest.TestCase):
    setUpClass=classmethod(graph.FreestandingGraphValueTests.setUpClass.__func__)
    run_probe=graph.FreestandingGraphValueTests.run_probe

    def generator(self,negative=False):
        directory=self.directory/("checked-identity-edge-bad" if negative
                                  else "checked-identity-edge")
        directory.mkdir()
        (directory/"compiler").symlink_to(ROOT/"src/compiler",target_is_directory=True)
        source=(ROOT/"tests/fixtures/u2_checked_identity_ssa.eri").read_text(
            encoding="utf-8")
        old="import compiler.u2_checked_identity_ssa_bind as ssa;"
        self.assertEqual(source.count(old),1)
        source=source.replace(old,old+"\n"
            "import compiler.u2_checked_identity_edge_x86_64 as nativeEdge;",1)
        marker='    output("u2-identity-checked-ssa:ok");'
        self.assertEqual(source.count(marker),1)
        descriptor="identityType"
        if negative:
            descriptor="managed.text(managedRegistry)"
        source=source.replace(marker,
            "    try nativeEdge.emit(fn,graph,profile,registry,phase,map,"
            "checkedPair,closeCall,plan,active,0,loc,managedRegistry,"
            "carrier,"+descriptor+",94);",1)
        source=source.replace("graphVerify.InvalidGraph,ProbeError {",
            "graphVerify.InvalidGraph,nativeEdge.Unsupported,ProbeError {",1)
        anchor='else error ProbeError { output("probe:"+error.message);'
        self.assertEqual(source.count(anchor),1)
        source=source.replace(anchor,
            'else error nativeEdge.Unsupported { output("native:"+error.message); '
            'process.setExitCode(1); }\n'+anchor,1)
        target=directory/"generate.eri"
        target.write_text(source,encoding="utf-8")
        binary=directory/"generate"
        self.assertEqual(build_native(target,binary,directory),0)
        return subprocess.run([str(binary)],capture_output=True,text=True,
                              timeout=120)

    def test_emitted_checked_identity_edges_preserve_live_gc_roots(self):
        generated=self.generator()
        self.assertEqual((generated.returncode,generated.stderr),
                         (0,""),generated.stdout)
        asm=generated.stdout
        self.assertIn("erist_u2_checked_identity_edge_94:",asm)
        self.assertIn("cmpq %rax,(%rsi)",asm)
        self.assertIn("cmpq $0,(%rdx)",asm)
        self.assertIn("cmpq $-1,%rcx",asm)
        from_offset=int(re.search(
            r"^    movq (\d+)\(%rdi\),%rax$",asm,re.M).group(1))
        next_offsets=[int(i) for i in re.findall(
            r"^    movq %rax,(\d+)\(%rdi\)$",asm,re.M)]
        self.assertEqual(len(next_offsets),2)
        normal_offset,fail_offset=next_offsets[0],next_offsets[1]
        self.assertEqual(len({from_offset,normal_offset,fail_offset}),3)
        for offset in (from_offset,normal_offset,fail_offset):
            self.assertEqual(offset%8,0)
            self.assertLess(offset,1024)

        for failed in (False,True):
            with self.subTest(failed=failed):
                body=r"""
.text
.globl _start
_start:
    xorl %ebp,%ebp
    call evn_scope_enter
    movq %rax,%r15
    movq %rax,%rdi
    leaq .Lu2_check_roots(%rip),%rsi
    leaq .Lu2_check_classes(%rip),%rdx
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
    movq %rax,.Lu2_check_roots(%rip)
"""
                body+=f"    movq %rax,.Lu2_check_ssa+{from_offset}(%rip)\n"
                if failed:
                    body+="""    call evn_saved
    movq %rax,.Lu2_check_roots+8(%rip)
"""
                body+=r"""    leaq .Lu2_check_ssa(%rip),%rdi
    leaq .Lu2_check_roots(%rip),%rsi
    leaq .Lu2_check_roots+8(%rip),%rdx
"""
                body+="    movq $"+("-1" if failed else "0")+",%rcx\n"
                body+="    call erist_u2_checked_identity_edge_94\n"
                body+="    cmpq $"+("-1" if failed else "0")+",%rax\n"
                body+="    jne .Lgraph_test_fail\n"
                body+=f"""    cmpq $0,.Lu2_check_ssa+{from_offset}(%rip)
    jne .Lgraph_test_fail
"""
                dead=normal_offset if failed else fail_offset
                live=fail_offset if failed else normal_offset
                body+=f"""    cmpq $0,.Lu2_check_ssa+{dead}(%rip)
    jne .Lgraph_test_fail
    movq .Lu2_check_ssa+{live}(%rip),%rax
    cmpq %rax,.Lu2_check_roots(%rip)
    jne .Lgraph_test_fail
"""
                body+=r"""    xorl %edi,%edi
    call erist_rt_slots_collect
    call erist_rt_text_collect
    call erist_rt_graph_live_objects
    cmpq $3,%rax
    jne .Lgraph_test_fail
    movq $0,.Lu2_check_roots(%rip)
    xorl %edi,%edi
    call erist_rt_slots_collect
    call erist_rt_text_collect
    call erist_rt_graph_live_objects
    testq %rax,%rax
    jne .Lgraph_test_fail
    movq $0,.Lu2_check_roots+8(%rip)
    call erist_rt_failure_clear
    call evn_void
    movq %rax,%rsi
    movq %r15,%rdi
    call evn_scope_leave
    jmp .Lgraph_finish
.bss
.p2align 3
.Lu2_check_ssa:
.zero 4096
.Lu2_check_roots:
.zero 16
.section .rodata
.Lu2_check_classes:
.byte 1,5
"""
                # Retain an independent exit code for EACH native assertion.
                # A generic 99 from the test runtime otherwise hides which
                # root/checked outcome was lost during collection.
                checks=re.findall(r"\\b(?:jne|je|jb|ja|jbe|jae) \\.Lgraph_test_fail",body)
                targets=[]
                for index,check in enumerate(checks):
                    label=".Lu2_checked_assert_"+str(index)
                    body=body.replace(check,check.replace(".Lgraph_test_fail",label),1)
                    targets.append((label,30+index))
                for label,exit_code in targets:
                    body+=("\\n.text\\n"+label+":\\n"
                           "    movl $"+str(exit_code)+",%edi\\n"
                           "    jmp erist_rt_exit\\n")
                result=self.run_probe("checked-identity-edge-"+str(int(failed)),
                     asm+body+graph.FINISH)
                self.assertEqual((result.returncode,result.stdout,result.stderr),
                                 (0,b"",b""),"native assertion index "+
                                 str(result.returncode-30))

    def test_wrong_managed_identity_refuses_before_assembly(self):
        result=self.generator(negative=True)
        self.assertEqual(result.returncode,1,result.stdout)
        self.assertTrue(result.stdout.startswith("identity:"),result.stdout)
        self.assertNotIn("erist_u2_checked_identity_edge_94",result.stdout)
        self.assertNotIn(".section",result.stdout)
