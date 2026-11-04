"""Opt-in native U2 verified lexical cleanup plan and saved failure-root tests."""
from pathlib import Path
import platform
import subprocess
import unittest
from compiler.erist.cli import build_native
import test_freestanding_resource_values as resource

ROOT=Path(__file__).resolve().parents[1]


@unittest.skipUnless(platform.system()=='Linux' and
    platform.machine().lower() in ('x86_64','amd64'),
    'U2 native checked cleanup requires Linux x86-64 owned runtime')
class U2NativeCleanupTests(unittest.TestCase):
    setUpClass=classmethod(resource.FreestandingResourceValueTests.setUpClass.__func__)
    run_probe=resource.FreestandingResourceValueTests.run_probe

    def generator(self):
        src=ROOT/'tests/fixtures/u2_cleanup_native.eri'
        folder=self.directory/'u2-native-cleanup-generator'
        folder.mkdir(exist_ok=True)
        (folder/'compiler').symlink_to(ROOT/'src/compiler',target_is_directory=True)
        copy=folder/'app.eri'
        copy.write_text(src.read_text(encoding='utf-8'),encoding='utf-8')
        binary=folder/'generator'
        self.assertEqual(build_native(copy,binary,folder),0)
        result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=120)
        self.assertEqual((result.returncode,result.stderr),(0,''),result.stdout)
        return result.stdout

    @staticmethod
    def code_bytes(name, content):
        return f'.L{name}:\n.byte '+','.join(str(b) for b in content)+f'\n.L{name}_end:\n'

    def assembly(self,failed,close_failure,emission,paths):
        bits=[]
        for i,path in enumerate(paths):
            bits.extend([
                f'leaq .Lfile{i}(%rip),%rdi',
                f'movl $(.Lfile{i}_end-.Lfile{i}),%esi',
                'call evn_text',
                'movq %rax,%rsi',
                'movl $9,%edi',
                'xorl %edx,%edx',
                'call erist_rt_file_open',
                f'movq %rax,{i*8}(%rsp)',
            ])
        if failed:
            bits.extend([
                'leaq .Lprimary_path(%rip),%rdi',
                'movl $7,%esi',
                'call evn_text',
                'movq %rax,%rdi',
                'leaq .Lprimary_message(%rip),%rsi',
                'call erist_rt_file_failure',
            ])
        else:
            bits.append('call evn_empty_failure')
        bits.extend([
            'movq %rax,24(%rsp)',
            'movq %rsp,%rdi',
            'movq %rax,%rsi',
            'call erist_u2_cleanup_'+('32' if failed else '31'),
            'cmpq $'+('-1' if (failed or close_failure) else '0')+',%rax',
            'jne .Lresource_test_fail',
            'cmpq $0,0(%rsp)',
            'jne .Lresource_test_fail',
            'cmpq $0,8(%rsp)',
            'jne .Lresource_test_fail',
            'cmpq $0,16(%rsp)',
            'jne .Lresource_test_fail',
            'xorl %edi,%edi',
            'call erist_rt_slots_collect',
            'call erist_rt_text_collect',
            'call erist_rt_open_resources',
            'testq %rax,%rax',
            'jne .Lresource_test_fail',
            'call erist_rt_live_failures',
            'cmpq $'+str(1+(3 if (close_failure and failed) else (2 if close_failure else 0)))+',%rax',
            'jne .Lresource_test_fail',
        ])
        if failed and close_failure:
            bits.extend([
                'movq 24(%rsp),%r14',
                'movq 80(%r14),%r12',
                'testq %r12,%r12',
                'je .Lresource_test_fail',
                'movq 88(%r12),%r13',
                'testq %r13,%r13',
                'je .Lresource_test_fail',
                'movq 88(%r13),%rbx',
                'testq %rbx,%rbx',
                'je .Lresource_test_fail',
                'cmpq $0,88(%rbx)',
                'jne .Lresource_test_fail',
                'leaq 32(%r14),%rdi',
                'call evn_output',
            ])
            for reg in ('r12','r13','rbx'):
                bits.extend([
                    f'movq 8(%{reg}),%rax',
                    'movq 8(%rax),%rdi',
                    'addq $32,%rdi',
                    'call evn_output',
                ])
        bits.extend([
            'movq $0,24(%rsp)',
            'call evn_void',
            'movq %rax,%rsi',
            'movq 32(%rsp),%rdi',
            'call evn_scope_leave',
            'addq $48,%rsp',
            'call .Lresource_finish',
            'xorl %edi,%edi',
            'jmp erist_rt_exit',
        ])
        lines=[
            '.text','.globl _start','_start:',
            'subq $48,%rsp',
            'movq $0,0(%rsp)','movq $0,8(%rsp)',
            'movq $0,16(%rsp)','movq $0,24(%rsp)',
            'call evn_scope_enter',
            'movq %rax,32(%rsp)',
            'movq %rax,%rdi',
            'movq %rsp,%rsi',
            'leaq .Lu2_native_caller_classes(%rip),%rdx',
            'movl $4,%ecx',
            'call evn_bind_roots',
        ]+['    '+x for x in bits]+[
            '.section .rodata',
            '.Lu2_native_caller_classes:','.byte 1,1,1,5',
            '.Lprimary_path:','.ascii "primary"',
            '.Lprimary_message:','.asciz "original"',
        ]
        for i,path in enumerate(paths):
            lines.append(self.code_bytes('file'+str(i),str(path).encode('utf-8')))
        return emission+'\n'.join(lines)+'\n'+resource.FINISH

    def test_verified_plan_drives_real_reverse_file_cleanup_and_failure_roots(self):
        emitted=self.generator()
        for label in (31,32):
            self.assertIn('erist_u2_cleanup_'+str(label)+':',emitted)
            self.assertIn('erist_u2_cleanup_'+str(label)+'_classes:',emitted)
        self.assertIn('call evn_cleanup_accumulate',emitted)
        self.assertIn('call evn_bind_roots',emitted)
        self.assertIn('call evn_scope_leave',emitted)
        self.assertIn('erist_u2_cleanup_31_row_6:',emitted)
        paths=[self.directory/f'cleanup-{i}.txt' for i in range(3)]
        for path in paths:
            path.write_text('file',encoding='utf-8')
        # The independent plan requires reverse (file2, file1, file0).
        for initially_failed,close_failure in ((False,False),(True,False),
                                                (False,True),(True,True)):
            with self.subTest(initially_failed=initially_failed,
                              close_failure=close_failure):
                asm=self.assembly(initially_failed,close_failure,emitted,paths)
                runtime=(resource.close_failures(self.runtime) if close_failure
                         else self.runtime)
                result=self.run_probe('u2-cleanup-'+str(int(initially_failed))+
                    '-'+str(int(close_failure)),asm,runtime=runtime)
                expected=b''
                if initially_failed and close_failure:
                    expected=('original\n'+str(paths[2])+'\n'+
                              str(paths[1])+'\n'+str(paths[0])+'\n').encode()
                self.assertEqual((result.returncode,result.stdout,result.stderr),
                                 (0,expected,b''))
