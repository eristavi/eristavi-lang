"""Canonical checked File acquisition bridge; not full Function qualification."""
from pathlib import Path
import platform
import subprocess
import unittest
from compiler.erist.cli import build_native
import test_freestanding_resource_values as resource

ROOT=Path(__file__).resolve().parents[1]

@unittest.skipUnless(platform.system()=='Linux' and platform.machine().lower() in
                     ('x86_64','amd64'), 'owned Linux x86-64 bridge')
class U2FileAcquireNativeTests(unittest.TestCase):
    setUpClass=classmethod(resource.FreestandingResourceValueTests.setUpClass.__func__)
    run_probe=resource.FreestandingResourceValueTests.run_probe

    def generator(self,text=None):
        folder=self.directory/'acquire-generator'
        folder.mkdir(exist_ok=True)
        link=folder/'compiler'
        if not link.exists():
            link.symlink_to(ROOT/'src/compiler',target_is_directory=True)
        source=folder/'probe.eri'
        source.write_text(text or (ROOT/'tests/fixtures/u2_file_acquire_native.eri').read_text())
        binary=folder/'probe'
        self.assertEqual(build_native(source,binary,folder),0)
        return subprocess.run([str(binary)],capture_output=True,text=True,timeout=120)

    def test_checked_acquire_success_failure_gc_and_reclamation(self):
        emitted=self.generator()
        self.assertEqual((emitted.returncode,emitted.stderr),(0,''),emitted.stdout)
        for missing in (False,True):
            path=self.directory/('absent' if missing else 'present')
            if not missing: path.write_text('contents')
            body=r'''
.text
.globl _start
_start:
    subq $48,%rsp
    movq $0,0(%rsp)
    movq $0,8(%rsp)
    movq $0,16(%rsp)
    movq $0,24(%rsp)
    call evn_scope_enter
    movq %rax,32(%rsp)
    movq %rax,%rdi
    movq %rsp,%rsi
    leaq .Lclasses(%rip),%rdx
    movl $4,%ecx
    call evn_bind_roots
    leaq .Lpath(%rip),%rdi
    movl $PATHLEN,%esi
    call evn_text
    movq %rax,0(%rsp)
    movq %rax,%rdi
    leaq 8(%rsp),%rsi
    leaq 16(%rsp),%rdx
    movl $9,%ecx
    call erist_u2_acquire_91
    cmpq $STATUS,%r10
    jne .Lresource_test_fail
    cmpq $0,%rdx
    jne .Lresource_test_fail
    xorl %edi,%edi
    call erist_rt_slots_collect
    call erist_rt_text_collect
CHECK
    movq $0,0(%rsp)
    movq $0,8(%rsp)
    movq $0,16(%rsp)
    movq $0,24(%rsp)
    call evn_void
    movq %rax,%rsi
    movq 32(%rsp),%rdi
    call evn_scope_leave
    addq $48,%rsp
    call .Lresource_finish
    xorl %edi,%edi
    jmp erist_rt_exit
.section .rodata
.Lclasses: .byte 1,1,5,5
.Lpath: .byte PATHBYTES
'''
            check='''    cmpq $0,8(%rsp)
    jne .Lresource_test_fail
    movq 16(%rsp),%rax
    testq %rax,%rax
    je .Lresource_test_fail
    cmpq $0,(%rax)
    je .Lresource_test_fail
'''
            if not missing:
                check='''    cmpq $0,16(%rsp)
    jne .Lresource_test_fail
    call evn_empty_failure
    movq %rax,24(%rsp)
    movq %rax,%rsi
    movq 8(%rsp),%rdi
    call evn_cleanup_accumulate
    movq 24(%rsp),%rax
    cmpq $0,(%rax)
    jne .Lresource_test_fail
'''
            data=str(path).encode()
            body=body.replace('PATHLEN',str(len(data))).replace('PATHBYTES',','.join(map(str,data)))
            body=body.replace('STATUS',str(int(missing))).replace('CHECK',check)
            result=self.run_probe("acquire-"+str(int(missing)),emitted.stdout+body+resource.FINISH)
            self.assertEqual((result.returncode,result.stdout,result.stderr),(0,b"",b""))

    def test_unknown_acquire_symbol_refuses_before_output(self):
        text=(ROOT/'tests/fixtures/u2_file_acquire_native.eri').read_text()
        result=self.generator(text.replace('u2.file.openRead.v1','u2.file.openRedd.v1'))
        self.assertEqual(result.returncode,1)
        self.assertNotIn('.text',result.stdout)
        self.assertIn('native:',result.stdout)
