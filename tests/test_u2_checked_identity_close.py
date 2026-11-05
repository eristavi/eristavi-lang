"""Real native checked File.close with compiler-published identity/Failure roots.

The emitter consumes original canonical SSA/owner/managed metadata. This test
uses one bounded verified opcode-46 and a real owned File.close, not a
handwritten substitute for either the closed native adapter or GC.
"""
from pathlib import Path
import platform
import re
import subprocess
import unittest

from compiler.erist.cli import build_native
import test_freestanding_resource_values as resource
import test_u2_identity_file_cleanup as identities

ROOT=Path(__file__).resolve().parents[1]


@unittest.skipUnless(platform.system()=="Linux" and
                     platform.machine().lower() in ("x86_64","amd64"),
                     "combined canonical identity and File needs Linux x86-64")
class U2CheckedIdentityCloseTests(unittest.TestCase):
    setUpClass=classmethod(resource.FreestandingResourceValueTests.setUpClass.__func__)
    run_probe=resource.FreestandingResourceValueTests.run_probe

    def generator(self,negative=False):
        directory=self.directory/("u2-identity-close-invalid" if negative
                                  else "u2-identity-close")
        directory.mkdir(exist_ok=True)
        link=directory/"compiler"
        target=(ROOT/"src/compiler").resolve()
        if link.is_symlink():
            self.assertEqual(link.resolve(),target)
        else:
            self.assertFalse(link.exists())
            link.symlink_to(target,target_is_directory=True)
        source=(ROOT/"tests/fixtures/u2_checked_identity_ssa.eri").read_text(
            encoding="utf-8")
        old="import compiler.u2_checked_identity_ssa_bind as ssa;"
        self.assertEqual(source.count(old),1)
        source=source.replace(old,old+"\n"
            "import compiler.u2_checked_identity_close_x86_64 as nativeClose;",1)
        marker='    output("u2-identity-checked-ssa:ok");'
        self.assertEqual(source.count(marker),1)
        descriptor=("identityType" if negative else
                    "identityType")
        source=source.replace(marker,
            "    try nativeClose.emit(fn,graph,profile,registry,phase,map,"
            "checkedPair,closeCall,plan,active,0,loc,managedRegistry,"
            "carrier,"+descriptor+",95);",1)
        declaration="managed.InvalidManagedTypes,graphVerify.InvalidGraph,ProbeError {"
        self.assertEqual(source.count(declaration),1)
        source=source.replace(declaration,
            "managed.InvalidManagedTypes,nativeClose.Unsupported,graphVerify.InvalidGraph,ProbeError {",1)
        handler='else error ProbeError { output("probe:"+error.message);'
        self.assertEqual(source.count(handler),1)
        source=source.replace(handler,
            'else error nativeClose.Unsupported { output("native:"+error.message); '
            'process.setExitCode(1); }\n'+handler,1)
        path=directory/"generate.eri"
        path.write_text(source,encoding="utf-8")
        binary=directory/"generate"
        self.assertEqual(build_native(path,binary,directory),0)
        return subprocess.run([str(binary)],capture_output=True,text=True,
                              timeout=180)

    def offsets(self,emitted):
        base="erist_u2_identity_close_95"
        self.assertIn(base+":",emitted)
        self.assertIn("erist_u2_cleanup_95:",emitted)
        self.assertIn("call erist_u2_cleanup_95",emitted)
        self.assertIn("call evn_bind_roots",emitted)
        names=("source","normal","failed","scalar","normal_scalar",
               "failed_scalar","failure_record","consumed")
        offsets={}
        for name in names:
            pattern=r"^\.set "+base+"_"+name+r", (\d+)$"
            matched=re.findall(pattern,emitted,re.M)
            self.assertEqual(len(matched),1,(name,matched))
            offsets[name]=int(matched[0])
            self.assertEqual(offsets[name]%8,0,name)
            self.assertLess(offsets[name],1024,name)
        self.assertEqual(len(set(offsets.values())),len(names))
        native=emitted.split(base+":",1)[1]
        self.assertLess(native.index("call evn_bind_roots"),
                        native.index("call erist_u2_cleanup_95"))
        self.assertIn("movq %rax,(%rbx)",native)
        self.assertIn("movq $0,"+str(offsets["consumed"])+"(%r15)",native)
        return offsets

    def assembly(self,emitted,offsets,path,pending,fail):
        base="erist_u2_identity_close_95"
        status=-1 if fail else 0
        dead="normal" if fail else "failed"
        live="failed" if fail else "normal"
        lines=[
            ".text",".globl _start","_start:",
            "    subq $512,%rsp",
            "    movq $0,0(%rsp)",
            "    movq $0,.Lu2_saved_failure(%rip)",
            "    call evn_scope_enter",
            "    movq %rax,16(%rsp)",
            "    movq %rax,%rdi",
            "    movq %rsp,%rsi",
            "    leaq .Lu2_owner_classes(%rip),%rdx",
            "    movl $1,%ecx",
            "    call evn_bind_roots",
            "    call evn_scope_enter",
            "    movq %rax,24(%rsp)",
            "    movq %rax,%rdi",
            "    leaq .Lu2_failure_root(%rip),%rsi",
            "    leaq .Lu2_failure_class(%rip),%rdx",
            "    movl $1,%ecx",
            "    call evn_bind_roots",
            "    call evn_scope_enter",
            "    movq %rax,32(%rsp)",
            "    movq %rax,%rdi",
            "    leaq .Lu2_temporary_root(%rip),%rsi",
            "    leaq .Lu2_identity_class(%rip),%rdx",
            "    movl $1,%ecx",
            "    call evn_bind_roots",
            "    leaq .Lu2_file(%rip),%rdi",
            "    movl $(.Lu2_file_end-.Lu2_file),%esi",
            "    call evn_text",
            "    movq %rax,%rsi",
            "    movl $9,%edi",
            "    xorl %edx,%edx",
            "    call erist_rt_file_open",
            "    movq %rax,0(%rsp)",
            "    call evn_empty_failure",
            "    movq %rax,.Lu2_saved_failure(%rip)",
            "    movq $0,.Lu2_failure_root(%rip)",
        ]
        # The independently observed native identity carries three cyclic
        # graph nodes. A temporary producer root protects construction only;
        # it is cleared before the integrated checked closer takes ownership.
        for register in ("r12","r13","r14"):
            lines+=["    movl $1,%edi","    call erist_rt_graph_new_object",
                    "    movq %rax,%"+register]
        for idx,(at,next_at) in enumerate((("r12","r13"),
                                           ("r13","r14"),("r14","r12"))):
            lines+=["    movq 8(%"+at+"),%rax",
                    "    movq $"+str(10+idx)+",(%rax)",
                    "    movq %"+next_at+",8(%rax)"]
        lines += [
            "    movl $10,%edi","    movq %r12,%rsi",
            "    call erist_rt_value_new",
            "    movq %rax,.Lu2_temporary_root(%rip)",
            "    movq %rax,.Lu2_ssa+"+str(offsets["source"])+"(%rip)",
            "    movq 0(%rsp),%rax",
            "    movq %rax,.Lu2_ssa+"+str(offsets["consumed"])+"(%rip)",
            "    movq $"+str(pending)+",.Lu2_ssa+"+str(offsets["scalar"])+"(%rip)",
            "    call evn_scope_enter",
            "    movq %rax,40(%rsp)",
            # No allocation, GC, or scope leave may intervene until the new
            # native emitter binds and publishes the two required roots.
            "    movq $0,.Lu2_temporary_root(%rip)",
            "    movq $0,.Lu2_failure_root(%rip)",
            "    leaq 0(%rsp),%rdi",
            "    leaq .Lu2_saved_failure(%rip),%rsi",
            "    leaq .Lu2_failure_root(%rip),%rdx",
            "    leaq .Lu2_ssa(%rip),%rcx",
            "    movq 40(%rsp),%r8",
            "    leaq .Lu2_identity_root(%rip),%r9",
            "    call "+base,
            "    cmpq $"+str(status)+",%rax",
            "    jne .Lresource_test_fail",
            "    cmpq $0,0(%rsp)",
            "    jne .Lresource_test_fail",
            "    cmpq $0,.Lu2_ssa+"+str(offsets["consumed"])+"(%rip)",
            "    jne .Lresource_test_fail",
            "    cmpq $0,.Lu2_ssa+"+str(offsets["source"])+"(%rip)",
            "    jne .Lresource_test_fail",
            "    cmpq $0,.Lu2_ssa+"+str(offsets[dead])+"(%rip)",
            "    jne .Lresource_test_fail",
            "    movq .Lu2_ssa+"+str(offsets[live])+"(%rip),%rax",
            "    testq %rax,%rax",
            "    je .Lresource_test_fail",
            "    cmpq %rax,.Lu2_identity_root(%rip)",
            "    jne .Lresource_test_fail",
            "    call erist_rt_open_resources",
            "    testq %rax,%rax",
            "    jne .Lresource_test_fail",
        ]
        if fail:
            lines += [
                "    cmpq $0,.Lu2_ssa+"+str(offsets["normal_scalar"])+"(%rip)",
                "    jne .Lresource_test_fail",
                "    cmpq $"+str(pending)+",.Lu2_ssa+"+
                    str(offsets["failed_scalar"])+"(%rip)",
                "    jne .Lresource_test_fail",
                "    leaq .Lu2_saved_failure(%rip),%rax",
                "    cmpq %rax,.Lu2_failure_root(%rip)",
                "    jne .Lresource_test_fail",
                "    cmpq %rax,.Lu2_ssa+"+
                    str(offsets["failure_record"])+"(%rip)",
                "    jne .Lresource_test_fail",
                "    cmpq $0,(%rax)",
                "    je .Lresource_test_fail",
            ]
        else:
            lines += [
                "    cmpq $"+str(pending)+",.Lu2_ssa+"+
                    str(offsets["normal_scalar"])+"(%rip)",
                "    jne .Lresource_test_fail",
                "    cmpq $0,.Lu2_ssa+"+str(offsets["failed_scalar"])+"(%rip)",
                "    jne .Lresource_test_fail",
                "    cmpq $0,.Lu2_ssa+"+
                    str(offsets["failure_record"])+"(%rip)",
                "    jne .Lresource_test_fail",
                "    cmpq $0,.Lu2_failure_root(%rip)",
                "    jne .Lresource_test_fail",
            ]
        lines += [
            "    xorl %edi,%edi",
            "    call erist_rt_slots_collect",
            "    call erist_rt_text_collect",
            "    call erist_rt_graph_live_objects",
            "    cmpq $3,%rax",
            "    jb .Lresource_test_fail",
            "    movq $0,.Lu2_identity_root(%rip)",
            "    movq $0,.Lu2_failure_root(%rip)",
            "    movq $0,.Lu2_temporary_root(%rip)",
            "    movq $0,.Lu2_ssa+"+str(offsets[live])+"(%rip)",
            "    movq $0,.Lu2_ssa+"+str(offsets["failure_record"])+"(%rip)",
            "    movq $0,8(%rsp)",
            "    xorl %edi,%edi",
            "    call erist_rt_slots_collect",
            "    call erist_rt_text_collect",
            "    call erist_rt_graph_live_objects",
            "    testq %rax,%rax",
            "    jne .Lresource_test_fail",
        ]
        for offset in (40,32,24,16):
            lines += ["    call evn_void",
                      "    movq %rax,%rsi",
                      "    movq "+str(offset)+"(%rsp),%rdi",
                      "    call evn_scope_leave"]
        lines += [
            "    addq $512,%rsp",
            "    call .Lresource_finish",
            "    xorl %edi,%edi",
            "    jmp erist_rt_exit",
            ".section .rodata",
            ".Lu2_owner_classes:",".byte 1",
            ".Lu2_failure_class:",".byte 5",
            ".Lu2_identity_class:",".byte 1",
            ".Lu2_file:",
            ".byte "+",".join(str(v) for v in str(path).encode("utf-8")),
            ".Lu2_file_end:",
            ".bss",".p2align 3",
            ".Lu2_ssa:",".zero 1024",
            ".Lu2_failure_root:",".zero 8",
            ".Lu2_saved_failure:",".zero 96",
            ".Lu2_identity_root:",".zero 8",
            ".Lu2_temporary_root:",".zero 8",
        ]
        return (emitted+"\n".join(lines)+"\n"+resource.FINISH)

    def test_real_file_close_publishes_identity_on_both_checked_edges(self):
        generation=self.generator()
        self.assertEqual((generation.returncode,generation.stderr),
                         (0,""),generation.stdout[-3200:])
        emitted=generation.stdout
        offsets=self.offsets(emitted)
        path=self.directory/"u2-checked-identity-close.txt"
        path.write_text("resource",encoding="utf-8")
        for pending in (0,74565,-19):
            for failed in (False,True):
                with self.subTest(pending=pending,failed=failed):
                    code=self.assembly(emitted,offsets,path,pending,failed)
                    runtime=(resource.close_failures(self.runtime) if failed
                             else self.runtime)
                    result=self.run_probe(
                        "u2-identity-close-%d-%d"%(pending,int(failed)),
                        identities.identity_file_descriptors()+code,
                        runtime=runtime,types=False)
                    self.assertEqual(
                        (result.returncode,result.stdout,result.stderr),
                        (0,b"",b""))

    def test_wrong_identity_descriptor_rejected_before_native_emission(self):
        generation=self.generator(negative=True)
        self.assertEqual(generation.returncode,1,generation.stdout[-1500:])
        self.assertTrue(generation.stdout.startswith("identity:"),
                        generation.stdout)
        self.assertNotIn("erist_u2_identity_close_95:",generation.stdout)
        self.assertNotIn("erist_u2_cleanup_95:",generation.stdout)
        self.assertNotIn(".section",generation.stdout)
