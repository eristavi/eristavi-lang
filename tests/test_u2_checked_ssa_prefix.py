"""Native checked File.close moves a live outer canonical File owner."""
from pathlib import Path
import platform
import re
import subprocess
import unittest

from compiler.erist.cli import build_native
import test_freestanding_resource_values as resource

ROOT=Path(__file__).resolve().parents[1]


@unittest.skipUnless(platform.system()=="Linux" and
                     platform.machine().lower() in ("x86_64","amd64"),
                     "bounded checked SSA prefix native Linux x86-64 only")
class U2CheckedSSAPrefixTests(unittest.TestCase):
    setUpClass=classmethod(resource.FreestandingResourceValueTests.setUpClass.__func__)
    run_probe=resource.FreestandingResourceValueTests.run_probe

    def generator(self):
        directory=self.directory/"u2-checked-ssa-prefix-generator"
        directory.mkdir(exist_ok=True)
        link=directory/"compiler"
        target=(ROOT/"src/compiler").resolve()
        if link.is_symlink():
            self.assertEqual(link.resolve(),target)
        else:
            self.assertFalse(link.exists())
            link.symlink_to(target,target_is_directory=True)
        source=directory/"app.eri"
        source.write_text(
            (ROOT/"tests/fixtures/u2_checked_ssa_prefix.eri").read_text(encoding="utf-8"),
            encoding="utf-8")
        binary=directory/"generator"
        self.assertEqual(build_native(source,binary,directory),0)
        run=subprocess.run([str(binary)],capture_output=True,text=True,timeout=180)
        self.assertEqual((run.returncode,run.stderr),(0,""),run.stdout[-3500:])
        return run.stdout

    def offsets(self,emission):
        for name in ("erist_u2_ssa_71:","erist_u2_cleanup_71:",
                     "erist_u2_bind_71:","erist_u2_cleanup_73:",
                     "erist_u2_cleanup_74:"):
            self.assertIn(name,emission)
        self.assertNotIn("erist_u2_cleanup_72:",emission)
        self.assertNotIn("erist_u2_ssa_72:",emission)
        def get(pattern,text):
            m=re.search(pattern,text,re.M)
            self.assertIsNotNone(m,pattern)
            return int(m.group(1))
        body=emission.split("erist_u2_ssa_71:",1)[1]
        success,failed=body.split("erist_u2_ssa_71_failure:",1)
        sourceScalar=get(r"^    movq (\d+)\(%r15\),%rbx$",body)
        normalScalar=get(r"^    movq %rbx,(\d+)\(%r15\)$",success)
        failureScalar=get(r"^    movq %rbx,(\d+)\(%r15\)$",failed)
        failureRecord=get(r"^    movq %r13,(\d+)\(%r15\)$",failed)
        sourceOuter=get(r"^    movq (\d+)\(%r15\),%rax$",success)
        normalOuter=get(r"^    movq %rax,(\d+)\(%r15\)$",success)
        failureOuter=get(r"^    movq %rax,(\d+)\(%r15\)$",failed)
        root=get(r"^    cmpq \$0,(\d+)\(%r14\)$",body)
        self.assertEqual(root,16)
        self.assertEqual(sourceScalar,sourceOuter+8)
        self.assertEqual(len(set((sourceScalar,normalScalar,failureScalar,
                                  failureRecord,sourceOuter,normalOuter,
                                  failureOuter))),7)
        for off in (sourceScalar,normalScalar,failureScalar,failureRecord,
                    sourceOuter,normalOuter,failureOuter):
            self.assertEqual(off%8,0)
            self.assertGreaterEqual(off,0)
            self.assertLess(off,512)
        return (sourceScalar,normalScalar,failureScalar,failureRecord,
                sourceOuter,normalOuter,failureOuter,root)

    def assembly(self,emitted,paths,pending,fails,slots):
        (src_scalar,normal_scalar,failed_scalar,failed_record,src_outer,
         normal_outer,failed_outer,root)=slots
        base=128
        root_at=24+root
        status=-1 if fails else 0
        code=[
            ".text",".globl _start","_start:","    subq $1024,%rsp",
            "    movq $0,0(%rsp)","    movq $0,8(%rsp)",
            "    movq $0,16(%rsp)",
            "    call evn_scope_enter",
            "    movq %rax,88(%rsp)",
            "    movq %rax,%rdi","    movq %rsp,%rsi",
            "    leaq .Lowner_classes(%rip),%rdx",
            "    movl $3,%ecx","    call evn_bind_roots",
            "    call evn_scope_enter",
            "    movq %rax,80(%rsp)",
            "    movq %rax,%rdi",
            "    leaq 24(%rsp),%rsi",
            "    call erist_u2_bind_71",
        ]
        for i,path in enumerate(paths):
            code+= [
                "    leaq .Lfile%d(%%rip),%%rdi"%i,
                "    movl $(.Lfile%d_end-.Lfile%d),%%esi"%(i,i),
                "    call evn_text",
                "    movq %rax,%rsi","    movl $9,%edi","    xorl %edx,%edx",
                "    call erist_rt_file_open","    movq %%rax,%d(%%rsp)"%(i*8)
            ]
        code += [
            "    call evn_empty_failure",
            "    movq %rax,16(%rsp)",
            # Canonical source layout is [inner File, outer File, i64].
            # The inner source SSA File must be poisoned after consumption.
            "    movq 8(%rsp),%rax",
            "    movq %%rax,%d(%%rsp)"%(base+src_outer-8),
            "    movq 0(%rsp),%rax",
            "    movq %%rax,%d(%%rsp)"%(base+src_outer),
            "    movq $%d,%d(%%rsp)"%(pending,base+src_scalar),
            "    movq %rsp,%rdi",
            "    movq 16(%rsp),%rsi",
            "    leaq 24(%rsp),%rdx",
            "    leaq 128(%rsp),%rcx",
            "    call erist_u2_ssa_71",
            "    cmpq $%d,%%rax"%status,
            "    jne .Lresource_test_fail",
            "    cmpq $0,8(%rsp)","    jne .Lresource_test_fail",
            "    cmpq $0,%d(%%rsp)"%(base+src_outer-8),
            "    jne .Lresource_test_fail",
            "    cmpq $0,0(%rsp)","    je .Lresource_test_fail",
            "    cmpq $0,%d(%%rsp)"%(base+src_outer),
            "    jne .Lresource_test_fail",
            "    call erist_rt_open_resources",
            "    cmpq $1,%rax","    jne .Lresource_test_fail"
        ]
        if fails:
            code += [
                "    cmpq $0,%d(%%rsp)"%(base+normal_scalar),
                "    jne .Lresource_test_fail",
                "    cmpq $0,%d(%%rsp)"%(base+normal_outer),
                "    jne .Lresource_test_fail",
                "    cmpq $%d,%d(%%rsp)"%(pending,base+failed_scalar),
                "    jne .Lresource_test_fail",
                "    movq %d(%%rsp),%%rax"%(base+failed_record),
                "    cmpq %rax,16(%rsp)","    jne .Lresource_test_fail",
                "    cmpq %%rax,%d(%%rsp)"%root_at,
                "    jne .Lresource_test_fail",
                "    cmpq $0,(%rax)","    je .Lresource_test_fail",
                "    movq 0(%rsp),%rax",
                "    cmpq %%rax,%d(%%rsp)"%(base+failed_outer),
                "    jne .Lresource_test_fail"
            ]
        else:
            code += [
                "    cmpq $%d,%d(%%rsp)"%(pending,base+normal_scalar),
                "    jne .Lresource_test_fail",
                "    cmpq $0,%d(%%rsp)"%(base+failed_scalar),
                "    jne .Lresource_test_fail",
                "    cmpq $0,%d(%%rsp)"%(base+failed_outer),
                "    jne .Lresource_test_fail",
                "    cmpq $0,%d(%%rsp)"%(base+failed_record),
                "    jne .Lresource_test_fail",
                "    cmpq $0,%d(%%rsp)"%root_at,
                "    jne .Lresource_test_fail",
                "    movq 0(%rsp),%rax",
                "    cmpq %%rax,%d(%%rsp)"%(base+normal_outer),
                "    jne .Lresource_test_fail"
            ]
        code += [
            "    xorl %edi,%edi","    call erist_rt_slots_collect",
            "    call erist_rt_text_collect",
            "    movq 16(%rsp),%r14",
            "    movq (%r14),%r15",
            # These helpers were emitted from the two ORIGINAL verified
            # canonical File.close plans after full checked-path admission.
            # The second checked close must never synthesize a success if
            # the incoming inner File.close has already failed.
            "    movq %rsp,%rdi","    movq 16(%rsp),%rsi",
            "    call erist_u2_cleanup_"+("74" if fails else "73"),
            "    cmpq $%d,%%rax"%(-1 if fails else 0),
            "    jne .Lresource_test_fail",
            "    cmpq %r15,(%r14)",
            "    jne .Lresource_test_fail",
            "    cmpq $0,0(%rsp)",
            "    jne .Lresource_test_fail",
        ]
        if fails:
            code += [
                "    movq 80(%r14),%r12",
                "    testq %r12,%r12",
                "    je .Lresource_test_fail",
                "    cmpq $0,88(%r12)",
                "    jne .Lresource_test_fail",
            ]
        else:
            code += [
                "    cmpq $0,80(%r14)",
                "    jne .Lresource_test_fail",
            ]
        code += [
            "    call erist_rt_open_resources",
            "    testq %rax,%rax","    jne .Lresource_test_fail",
            "    call erist_rt_live_failures",
            # Caller-owned class-5 root pins even an empty saved
            # FailureContext until scope release. The two injected
            # close failures fill it and append a secondary record.
            "    cmpq $%d,%%rax"%(2 if fails else 1),
            "    jne .Lresource_test_fail",
            "    movq $0,%d(%%rsp)"%root_at,
            "    movq $0,16(%rsp)",
            "    movq $0,%d(%%rsp)"%(base+failed_record),
            "    movq $0,%d(%%rsp)"%(base+failed_outer),
            "    movq $0,%d(%%rsp)"%(base+normal_outer),
            "    call evn_void","    movq %rax,%rsi",
            "    movq 80(%rsp),%rdi","    call evn_scope_leave",
            "    call evn_void","    movq %rax,%rsi",
            "    movq 88(%rsp),%rdi","    call evn_scope_leave",
            "    addq $1024,%rsp","    call .Lresource_finish",
            "    xorl %edi,%edi","    jmp erist_rt_exit",
            ".section .rodata",".Lowner_classes:",".byte 1,1,5"
        ]
        for i,path in enumerate(paths):
            code.extend([
                ".Lfile%d:"%i,
                ".byte "+",".join(str(v) for v in str(path).encode("utf-8")),
                ".Lfile%d_end:"%i
            ])
        return emitted+"\n".join(code)+"\n"+resource.FINISH

    def test_canonical_outer_file_owner_moves_on_both_checked_edges(self):
        emitted=self.generator()
        offsets=self.offsets(emitted)
        paths=[self.directory/("u2-ssa-prefix-%d.txt"%i) for i in range(2)]
        for path in paths:
            path.write_text("file",encoding="utf-8")
        for pending in (0,74565,-19):
            for fails in (False,True):
                with self.subTest(pending=pending,fails=fails):
                    assembly=self.assembly(emitted,paths,pending,fails,offsets)
                    runtime=(resource.close_failures(self.runtime) if fails
                             else self.runtime)
                    run=self.run_probe(
                        "u2-ssa-prefix-%d-%d"%(pending,int(fails)),
                        assembly,runtime=runtime)
                    self.assertEqual((run.returncode,run.stdout,run.stderr),
                                     (0,b"",b""))
