"""Batched qualification of owned file/process services and deterministic cleanup."""
from pathlib import Path
import os
import platform
import re
import shutil
import subprocess
import tempfile
import unittest
from compiler.erist.cli import build_native
import test_freestanding_text_lifetimes as lifetime_tests

ROOT=Path(__file__).resolve().parents[1]


def descriptors():
    rows=[(i,0,'',[]) for i in range(6)]+[
        (6,0,'Problem',[4]),(11,0,'error',[4]),
        (6,0,'std.files.FileError',[4,4]),(10,0,'std.files.File',[])]
    text='.section .data.rel.ro\n.p2align 3\n.globl ev_types\nev_types:\n'
    for i,(kind,inner,name,fields) in enumerate(rows):
        text+=f'.long {kind},{inner}\n.quad .Lresource_kind{i},{len(fields)},'+(f'.Lresource_fields{i}' if fields else '0')+'\n'
    text+='.globl ev_types_end\nev_types_end:\n.section .rodata\n'
    for i,(kind,inner,name,fields) in enumerate(rows):
        text+=f'.Lresource_kind{i}:\n.asciz "{name}"\n'
        if fields:text+=f'.p2align 2\n.Lresource_fields{i}:\n.long '+','.join(map(str,fields))+'\n'
    return text


FINISH=r'''
.text
.Lresource_finish:
    subq $8,%rsp
    call erist_rt_failure_clear
    call erist_rt_text_collect
    call erist_rt_open_resources
    testq %rax,%rax
    jne .Lresource_test_fail
    call erist_rt_live_resources
    testq %rax,%rax
    jne .Lresource_test_fail
    call erist_rt_graph_live_objects
    testq %rax,%rax
    jne .Lresource_test_fail
    call erist_rt_text_live_buffers
    testq %rax,%rax
    jne .Lresource_test_fail
    call erist_rt_live_failures
    testq %rax,%rax
    jne .Lresource_test_fail
    call erist_rt_live_handlers
    testq %rax,%rax
    jne .Lresource_test_fail
    call erist_rt_allocator_release_all
    testq %rax,%rax
    jne .Lresource_test_fail
    addq $8,%rsp
    ret
.Lresource_test_fail:
    movl $99,%edi
    jmp erist_rt_exit
'''


def close_failures(runtime):
    needle='    movl $3,%eax\n    syscall\n    testq %rax,%rax\n    jns .Lr_close_empty'
    assert runtime.count(needle)==1
    return runtime.replace(needle,'    movl $3,%eax\n    syscall\n    movq $-5,%rax\n    testq %rax,%rax\n    jns .Lr_close_empty')


@unittest.skipUnless(platform.system()=='Linux' and platform.machine().lower() in ('x86_64','amd64'),
                     'owned resource profile currently targets Linux x86-64')
class FreestandingResourceValueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for tool in ('as','ld','nm','readelf'):
            if not shutil.which(tool):raise unittest.SkipTest(f'{tool} unavailable')
        cls.temporary=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.temporary.cleanup)
        cls.directory=Path(cls.temporary.name)
        generator=cls.directory/'runtime';cls.frontend=cls.directory/'frontend'
        if build_native(ROOT/'src/resource_value_runtime.eri',generator,ROOT/'src')!=0:
            raise AssertionError('resource generator did not compile')
        emitted=subprocess.run([str(generator)],capture_output=True,text=True,timeout=60)
        if (emitted.returncode,emitted.stderr)!=(0,''):raise AssertionError(emitted.stderr)
        cls.runtime=emitted.stdout
        if build_native(ROOT/'src/frontend.eri',cls.frontend,ROOT/'src')!=0:
            raise AssertionError('frontend did not compile')

    def run_probe(self,name,assembly,runtime=None,types=True):
        return lifetime_tests.FreestandingTextLifetimeTests._link_run(
            self,self.directory,name,self.runtime if runtime is None else runtime,
            (descriptors() if types else '')+assembly)

    def compile_application(self,path):
        compiled=subprocess.run([str(self.frontend),'emit-asm',str(path)],capture_output=True,text=True,timeout=30)
        self.assertEqual((compiled.returncode,compiled.stderr),(0,''))
        return compiled.stdout

    def test_file_process_application_matches_existing_runtime_and_reclaims_every_family(self):
        path=self.directory/'roundtrip';path.with_suffix('.bad').write_bytes(b'\xff')
        (self.directory/'roundtrip.link').symlink_to(path)
        app=self.compile_application(ROOT/'examples/freestanding_resource_values.eri')
        asm=self.directory/'reference.s';reference=self.directory/'reference'
        asm.write_text(app+'\n.section .note.GNU-stack,"",@progbits\n')
        subprocess.run([os.environ.get('CC','cc'),'-std=c11','-O2','-DERIST_NATIVE_RUNTIME',
                        str(ROOT/'runtime/native_gc_runtime.c'),str(asm),'-lm','-o',str(reference)],
                       check=True,capture_output=True,timeout=30)
        hosted=subprocess.run([str(reference),str(path)],capture_output=True,timeout=30)
        expected=('false\nA\0β\ntrue\ntrue\nA\0βA\0β\n42\nbody preserved\n'
                  'file was opened read-only\nFile exists\ntrue\nNo such file or directory\n'
                  'invalid UTF-8\nfalse\n').encode()
        self.assertEqual((hosted.returncode,hosted.stdout,hosted.stderr),(7,expected,'service β\0\n'.encode()))
        runtime=self.runtime.replace('    call erist_entry\n    movq .Lprocess_exit_code',
                                    '    call erist_entry\n    call .Lresource_finish\n    movq .Lprocess_exit_code',1)
        runtime=runtime.replace('.Ltext_safe_return:\n', '.Ltext_safe_return:\n    cmpq $512,.Lresource_count(%rip)\n    ja .Lresource_test_fail\n    cmpq $512,.Lfailure_count(%rip)\n    ja .Lresource_test_fail\n',1)
        # Check the System-V entry alignment of every new returning public helper.
        resource_module=ROOT/'src/runtime/resource_x86_64.eri'
        import json
        emitted=json.loads(re.search(r'return ("(?:[^"\\]|\\.)*");',resource_module.read_text()).group(1))
        names=re.findall(r'\.globl (\w+)\n',emitted)
        for name in names:
            if name=='erist_rt_process_start':continue
            label=name+':\n'
            self.assertEqual(runtime.count(label),1)
            runtime=runtime.replace(label,label+'''    pushq %rax
    movq %rsp,%rax
    andl $15,%eax
    jne .Lresource_test_fail
    popq %rax
''',1)
        starter=r'''
.text
.globl _start
_start:
    movq %rsp,%rdi
    jmp erist_rt_process_start
'''
        result=self.run_probe('resources-app',app+starter+FINISH,runtime=runtime,types=False)
        # No arguments in the generic probe launcher: separately run the same audited static binary.
        self.assertEqual((result.returncode,result.stdout,result.stderr),(7,b'','service β\0\n'.encode()))
        result=subprocess.run([str(self.directory/'resources-app.bin'),str(path)],
                              env={'PATH':'/unavailable'},capture_output=True,timeout=20)
        self.assertEqual((result.returncode,result.stdout,result.stderr),(7,expected,'service β\0\n'.encode()))
        self.assertFalse(path.exists())

    def test_secondary_cleanup_failures_preserve_order_payload_and_transitive_roots(self):
        first=self.directory/'first';second=self.directory/'second'
        first.write_text('x');second.write_text('y')
        assembly=r'''
.text
.globl _start
_start:
    call evn_scope_enter
    movq %rax,%r15
    movq %rax,%rdi
    leaq .Lkeys(%rip),%rsi
    leaq .Lclasses(%rip),%rdx
    movl $3,%ecx
    call evn_bind_roots
    leaq .Lfirst(%rip),%rdi
    movl $(.Lfirst_end-.Lfirst),%esi
    call evn_text
    movq %rax,%rsi
    movl $9,%edi
    xorl %edx,%edx
    call erist_rt_file_open
    movq %rax,%r12
    movq %rax,.Lkeys(%rip)
    leaq .Lsecond(%rip),%rdi
    movl $(.Lsecond_end-.Lsecond),%esi
    call evn_text
    movq %rax,%rsi
    movl $9,%edi
    xorl %edx,%edx
    call erist_rt_file_open
    movq %rax,%r13
    movq %rax,.Lkeys+8(%rip)
    # Primary is also a fully typed failure with a path payload.
    leaq .Lprimary_path(%rip),%rdi
    movl $7,%esi
    call evn_text
    movq %rax,%rdi
    leaq .Lprimary_message(%rip),%rsi
    call erist_rt_file_failure
    movq %rax,%r14
    movq %rax,.Lkeys+16(%rip)
    movq %r12,%rdi
    movq %r14,%rsi
    call evn_cleanup_accumulate
    movq %r13,%rdi
    movq %r14,%rsi
    call evn_cleanup_accumulate
    # Repeating cleanup must neither close nor append a second time.
    movq %r13,%rdi
    movq %r14,%rsi
    call evn_cleanup_accumulate
    movq $0,.Lkeys(%rip)
    movq $0,.Lkeys+8(%rip)
    xorl %edi,%edi
    call erist_rt_slots_collect
    call erist_rt_text_collect
    call erist_rt_live_failures
    cmpq $3,%rax
    jne .Lresource_test_fail
    call erist_rt_live_resources
    testq %rax,%rax
    jne .Lresource_test_fail
    movq 80(%r14),%r12
    testq %r12,%r12
    je .Lresource_test_fail
    movq 88(%r12),%r13
    testq %r13,%r13
    je .Lresource_test_fail
    cmpq $0,88(%r13)
    jne .Lresource_test_fail
    leaq 32(%r14),%rdi
    call evn_output
    movq 8(%r12),%rax
    movq 8(%rax),%rdi
    addq $32,%rdi
    call evn_output
    movq 8(%r13),%rax
    movq 8(%rax),%rdi
    addq $32,%rdi
    call evn_output
    # Transfer to current failure; its secondary chain remains strong without saved roots.
    call evn_frame
    movq %rax,%rbx
    movq %rax,%rdi
    call setjmp
    testq %rax,%rax
    jne .Lcaught
    movq %r14,%rdi
    call evn_propagate
.Lcaught:
    movq %rbx,%rdi
    call evn_pop
    movq $0,.Lkeys+16(%rip)
    xorl %edi,%edi
    call erist_rt_slots_collect
    call erist_rt_text_collect
    call erist_rt_live_failures
    cmpq $2,%rax
    jne .Lresource_test_fail
    call evn_void
    movq %r15,%rdi
    movq %rax,%rsi
    call evn_scope_leave
    call .Lresource_finish
    xorl %edi,%edi
    jmp erist_rt_exit
.bss
.p2align 3
.Lkeys:
.zero 24
.section .rodata
.Lclasses:
.byte 1,1,5
.Lprimary_path:
.ascii "primary"
.Lprimary_message:
.asciz "original"
'''
        for label,path in [('first',first),('second',second)]:
            assembly+=f'.L{label}:\n.byte '+','.join(str(b) for b in str(path).encode())+f'\n.L{label}_end:\n'
        result=self.run_probe('secondary-roots',assembly+FINISH,runtime=close_failures(self.runtime))
        self.assertEqual((result.returncode,result.stdout,result.stderr),
                         (0,f'original\n{first}\n{second}\n'.encode(),b''))

    def test_process_arguments_survive_collection_and_reject_invalid_utf8(self):
        path=self.directory/'arguments.eri'
        path.write_text('import std.process; let args be process.arguments(); output(args.count); for item in args { output(item); }')
        app=self.compile_application(path)
        starter='\n.text\n.globl _start\n_start:\nmovq %rsp,%rdi\njmp erist_rt_process_start\n'
        runtime=self.runtime.replace('    call erist_entry\n    movq .Lprocess_exit_code',
                                    '    call erist_entry\n    call .Lresource_finish\n    movq .Lprocess_exit_code',1)
        result=self.run_probe('arguments',app+starter+FINISH,runtime=runtime,types=False)
        self.assertEqual((result.returncode,result.stdout,result.stderr),(0,b'0\n',b''))
        args=['αβ' if i%2 else str(i) for i in range(400)]+['']
        result=subprocess.run([str(self.directory/'arguments.bin'),*args],
                              env={'PATH':'/unavailable'},capture_output=True,timeout=20)
        self.assertEqual((result.returncode,result.stdout,result.stderr),
                         (0,('401\n'+'\n'.join(args)+'\n').encode(),b''))
        result=subprocess.run([os.fsencode(self.directory/'arguments.bin'),b'\xff'],
                              env={'PATH':'/unavailable'},capture_output=True,timeout=20)
        self.assertEqual((result.returncode,result.stdout,result.stderr),
                         (1,b'',b'Eristavi runtime fault: process arguments must be valid UTF-8\n'))

    def test_open_and_read_retry_eintr_and_complete_partial_reads(self):
        path=self.directory/'partial';path.write_text('Aβ\0tail')
        source=self.directory/'partial.eri'
        source.write_text(f'''import std.files;
        function read() returns Text fails files.FileError {{
          with file be try files.openRead("{path}") {{ return try file.readText(); }}
        }}
        function run() {{ let text be read() else error {{ output(error.message); return; }}; output(text); }} run();''')
        app=self.compile_application(source)
        runtime=self.runtime
        # One interrupted open, one interrupted read, then one byte per actual read.
        start=runtime.index('.Lr_open_retry:');end=runtime.index('.Lr_current:')
        part=runtime[start:end].replace('    syscall\n', '''    cmpq $0,.Linterrupted_open(%rip)
    jne .Ltest_open_actual
    incq .Linterrupted_open(%rip)
    movq $-4,%rax
    jmp .Ltest_open_done
.Ltest_open_actual:
    syscall
.Ltest_open_done:
''',1)
        runtime=runtime[:start]+part+runtime[end:]
        start=runtime.index('.Lr_read_loop:');end=runtime.index('.Lr_read_validate:')
        part=runtime[start:end].replace('    syscall\n', '''    cmpq $0,.Linterrupted_read(%rip)
    jne .Ltest_read_actual
    incq .Linterrupted_read(%rip)
    movq $-4,%rax
    jmp .Ltest_read_done
.Ltest_read_actual:
    movl $1,%edx
    syscall
.Ltest_read_done:
''',1)
        runtime=runtime[:start]+part+runtime[end:]
        starter='\n.text\n.globl _start\n_start:\ncall erist_entry\ncall .Lresource_finish\nxorl %edi,%edi\njmp erist_rt_exit\n.bss\n.Linterrupted_open:\n.quad 0\n.Linterrupted_read:\n.quad 0\n'
        result=self.run_probe('partial-read',app+starter+FINISH,runtime=runtime,types=False)
        self.assertEqual((result.returncode,result.stdout,result.stderr),(0,'Aβ\0tail\n'.encode(),b''))

    def test_terminal_oom_and_invalid_process_exit_codes(self):
        # Static trusted Text lets allocation counts isolate each private construction boundary.
        path=self.directory/'oom-file';path.write_text('data')
        static='\n.section .rodata\n.p2align 3\n.Lpath_value:\n.quad 4, .Lpath_end-.Lpath, .Lpath, 0\n.Lpath:\n.byte '+','.join(str(b) for b in str(path).encode())+'\n.Lpath_end:\n'
        # Resource path scratch, resource record, result slot; then read scratch.
        for name,body,at,resources,opened in (
            ('path-oom','leaq .Lpath_value(%rip),%rsi\nmovl $9,%edi\nxorl %edx,%edx\ncall erist_rt_file_open',1,0,0),
            ('resource-oom','leaq .Lpath_value(%rip),%rsi\nmovl $9,%edi\nxorl %edx,%edx\ncall erist_rt_file_open',2,0,0),
            ('resource-slot-oom','leaq .Lpath_value(%rip),%rsi\nmovl $9,%edi\nxorl %edx,%edx\ncall erist_rt_file_open',3,1,1),
            ('read-scratch-oom','leaq .Lpath_value(%rip),%rsi\nmovl $9,%edi\nxorl %edx,%edx\ncall erist_rt_file_open\nmovq %rax,%rdi\ncall erist_rt_file_read',4,1,1),
        ):
            with self.subTest(case=name):
                runtime=self.runtime.replace('erist_rt_alloc:\n',f'''erist_rt_alloc:
    incq .Loom_calls(%rip)
    cmpq ${at},.Loom_calls(%rip)
    jne .Loom_real
    xorl %eax,%eax
    ret
.Loom_real:
''',1).replace('erist_rt_exit:\n',f'''erist_rt_exit:
    cmpq ${resources},.Lresource_count(%rip)
    jne .Loom_bad
    cmpq ${opened},.Lopen_resource_count(%rip)
    jne .Loom_bad
''',1)
                probe='\n.text\n.globl _start\n_start:\n'+body+'\njmp .Loom_bad\n.Loom_bad:\nmovl $99,%edi\nmovl $60,%eax\nsyscall\nud2\n.bss\n.Loom_calls:\n.quad 0\n'+static
                result=self.run_probe(name,probe,runtime=runtime)
                self.assertEqual((result.returncode,result.stdout,result.stderr),(1,b'',b'Eristavi runtime fault: out of memory\n'))
        # Cleanup must already have consumed the descriptor if its failure snapshot runs out of memory.
        for at in (7,8,9,10):
            with self.subTest(cleanup_oom_at=at):
                runtime=close_failures(self.runtime).replace('erist_rt_alloc:\n',f'''erist_rt_alloc:
    incq .Loom_calls(%rip)
    cmpq ${at},.Loom_calls(%rip)
    jne .Loom_real
    xorl %eax,%eax
    ret
.Loom_real:
''',1).replace('erist_rt_exit:\n','''erist_rt_exit:
    cmpq $0,.Lopen_resource_count(%rip)
    jne .Loom_bad
''',1)
                body='''leaq .Lpath(%rip),%rdi
    movl $(.Lpath_end-.Lpath),%esi
    call evn_text
    movq %rax,%rsi
    movl $9,%edi
    xorl %edx,%edx
    call erist_rt_file_open
    movq %rax,%r12
    call evn_empty_failure
    movq %rax,%rsi
    movq %r12,%rdi
    call evn_cleanup_accumulate
'''
                probe='\n.text\n.globl _start\n_start:\n'+body+'\njmp .Loom_bad\n.Loom_bad:\nmovl $99,%edi\nmovl $60,%eax\nsyscall\nud2\n.bss\n.Loom_calls:\n.quad 0\n'+static
                result=self.run_probe(f'cleanup-oom-{at}',probe,runtime=runtime)
                self.assertEqual((result.returncode,result.stdout,result.stderr),(1,b'',b'Eristavi runtime fault: out of memory\n'))
        for code in (-1,256):
            with self.subTest(exit_code=code):
                source=self.directory/f'exit-{code}.eri';source.write_text(f'import std.process; process.setExitCode({code});')
                app=self.compile_application(source)
                result=self.run_probe(f'exit-{code}',app+'\n.text\n.globl _start\n_start:\ncall erist_entry\n',types=False)
                self.assertEqual((result.returncode,result.stdout,result.stderr),
                                 (1,b'',b'Eristavi runtime fault: process exit code must be between 0 and 255\n'))

    def test_generated_nested_cleanup_keeps_body_primary_and_reports_close_failure_on_return(self):
        path=self.directory/'cleanup';path.write_text('x')
        source=self.directory/'cleanup.eri'
        source.write_text(f'''import std.files;
        error Body {{ message Text; }}
        function failBody() fails Body,files.FileError {{
          with a be try files.openRead("{path}") {{
            with b be try files.openRead("{path}") {{ fail Body {{ message="body wins"; }}; }}
          }}
        }}
        function early() returns Int fails files.FileError {{
          with a be try files.openRead("{path}") {{
            with b be try files.openRead("{path}") {{ return 42; }}
          }}
        }}
        failBody() else error Body {{ output(error.message); }} else error files.FileError {{ output("wrong primary"); }};
        early() else error files.FileError {{ output(error.message); }};
        ''')
        app=self.compile_application(source)
        starter='\n.text\n.globl _start\n_start:\ncall erist_entry\ncall .Lresource_finish\nxorl %edi,%edi\njmp erist_rt_exit\n'
        result=self.run_probe('cleanup-generated',app+starter+FINISH,runtime=close_failures(self.runtime),types=False)
        self.assertEqual((result.returncode,result.stdout,result.stderr),(0,b'body wins\nInput/output error\n',b''))

    def test_checked_path_failures_directory_removal_and_closed_resource_fault(self):
        directory=self.directory/'empty-dir';directory.mkdir()
        source=self.directory/'paths.eri'
        source.write_text(f'''import std.files;
        function run() {{
          files.openRead("nul\\0path") else error files.FileError {{ output(error.message); output(error.path.bytes.count); }};
          files.exists("{directory}/absent/child") else error {{ output("unexpected missing"); }};
          files.remove("{directory}") else error {{ output(error.message); }};
          let absent be files.exists("{directory}") else error {{ output(error.message); return; }};
          output(absent);
          files.canonicalPath("{directory}") else error files.FileError {{ output(error.path == "{directory}"); output(error.message); }};
        }} run();
        ''')
        app=self.compile_application(source)
        starter='\n.text\n.globl _start\n_start:\ncall erist_entry\ncall .Lresource_finish\nxorl %edi,%edi\njmp erist_rt_exit\n'
        result=self.run_probe('path-errors',app+starter+FINISH,types=False)
        self.assertEqual((result.returncode,result.stdout,result.stderr),
                         (0,b'file path contains NUL\n8\nfalse\ntrue\nNo such file or directory\n',b''))
        self.assertFalse(directory.exists())
        path=self.directory/'closed-file';path.write_text('x')
        probe='''\n.text\n.globl _start\n_start:
    leaq .Lclosed_path(%rip),%rdi
    movl $(.Lclosed_path_end-.Lclosed_path),%esi
    call evn_text
    movq %rax,%rsi
    movl $9,%edi
    xorl %edx,%edx
    call erist_rt_file_open
    movq %rax,%r12
    call evn_empty_failure
    movq %rax,%rsi
    movq %r12,%rdi
    call evn_cleanup_accumulate
    movq %r12,%rdi
    call erist_rt_file_read
    ud2
.section .rodata
.Lclosed_path:
.byte '''+','.join(str(b) for b in str(path).encode())+'\n.Lclosed_path_end:\n'
        result=self.run_probe('closed-fault',probe)
        self.assertEqual((result.returncode,result.stdout,result.stderr),
                         (1,b'',b'Eristavi runtime fault: file resource is closed\n'))
