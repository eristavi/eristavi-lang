"""Execute compiler-generated original File CFG, not test-driven close calls."""
from pathlib import Path
import platform
import re
import subprocess
import time
import test_freestanding_graph_values as graph
from compiler.erist.cli import build_native, compile_entry
from compiler.erist.runtime_ext import Interpreter
import unittest
import test_freestanding_resource_values as resource
import test_u2_function_managed_native as managed

ROOT = Path(__file__).resolve().parents[1]

@unittest.skipUnless(platform.system() == 'Linux' and platform.machine().lower() in
                    ('x86_64', 'amd64'), 'owned File CFG requires Linux x86-64')
class U2FunctionFileCheckedTests(unittest.TestCase):
    setUpClass = classmethod(resource.FreestandingResourceValueTests.setUpClass.__func__)
    run_probe = resource.FreestandingResourceValueTests.run_probe
    generator = managed.U2FunctionManagedNativeTests.generator

    def source(self):
        return (ROOT/'tests/fixtures/u2_function_file_checked.eri').read_text()

    def caller(self, path, failed, handled=False):
        encoded = str(path).encode()
        body = r'''
.text
.globl _start
_start:
    call evn_scope_enter
    movq %rax,%r15
    movq %rax,%rdi
    leaq .Lroots(%rip),%rsi
    leaq .Lclasses(%rip),%rdx
    movl $2,%ecx
    call evn_bind_roots
    leaq .Lpath(%rip),%rdi
    movl $PATHLEN,%esi
    call evn_text
    movq %rax,.Lroots(%rip)
    leaq .Lroots(%rip),%rdi
    xorl %esi,%esi
    xorl %edx,%edx
    leaq .Lroots+8(%rip),%rcx
    call erist_u2_rooted_function_718
'''.replace('PATHLEN', str(len(encoded)))
        if failed and not handled:
            body += r'''
    cmpq $1,%r10
    jne .Lresource_test_fail
    testq %rax,%rax
    je .Lresource_test_fail
    cmpq %rax,.Lroots+8(%rip)
    jne .Lresource_test_fail
    cmpq $8,(%rax)
    jne .Lresource_test_fail
    cmpq $0,80(%rax)
    jne .Lresource_test_fail
'''
        else:
            body += r'''
    testq %r10,%r10
    jne .Lresource_test_fail
    cmpq $ANSWER,%rax
    jne .Lresource_test_fail
    cmpq $0,.Lroots+8(%rip)
    jne .Lresource_test_fail
'''.replace('ANSWER', '7' if failed else '42')
        body += r'''
    xorl %edi,%edi
    call erist_rt_slots_collect
    call erist_rt_text_collect
    call erist_rt_open_resources
    testq %rax,%rax
    jne .Lresource_test_fail
    movq $0,.Lroots(%rip)
    movq $0,.Lroots+8(%rip)
    call evn_void
    movq %rax,%rsi
    movq %r15,%rdi
    call evn_scope_leave
    call .Lresource_finish
    xorl %edi,%edi
    jmp erist_rt_exit
.bss
.p2align 3
.Lroots: .zero 16
.section .rodata
.Lclasses: .byte 1,5
.Lpath:
.byte ''' + ','.join(map(str, encoded)) + '\n'
        return body + resource.FINISH

    def test_generated_acquire_close_failure_handler_and_reclamation(self):
        path = self.directory/'present.txt'
        path.write_text('native')
        missing = self.directory/'absent.txt'
        for handled in (False, True):
            source = self.source()
            if handled:
                source = source.replace(
                    'let propagated be try body.returnFailure(fn,graph,table,failed,errorValue,loc);',
                    'let recovery be try build.integer(fn,failed,7,loc); '
                    'try ab.returnValues(fn,graph,failed,[recovery],loc);')
                source = source.replace(
                    'let cancelled be try body.returnFailure(fn,graph,table,closeFailed,closeError,loc);',
                    'let recoveredClose be try build.integer(fn,closeFailed,7,loc); '
                    'try ab.returnValues(fn,graph,closeFailed,[recoveredClose],loc);')
            result = self.generator('file-cfg-'+str(handled), source)
            self.assertEqual((result.returncode, result.stderr), (0, ''), result.stdout[-2000:])
            self.assertIn('call erist_rt_file_open', result.stdout)
            self.assertIn('call erist_u2_file_718_poison_', result.stdout)
            for scenario, selected, runtime, failed in (
                    ('success', path, self.runtime, False),
                    ('open-failure', missing, self.runtime, True),
                    ('close-failure', path, resource.close_failures(self.runtime), True)):
                with self.subTest(handled=handled, scenario=scenario):
                    runtime = runtime.replace('.Lr_close:\n',
                        '.Lr_close:\n    incq .Lclose_calls(%rip)\n',1)
                    caller = self.caller(selected, failed, handled).replace(
                        '    call .Lresource_finish',
                        '    cmpq $'+str(int(scenario != 'open-failure'))+',.Lclose_calls(%rip)\n'
                        '    jne .Lresource_test_fail\n    call .Lresource_finish',1)
                    run = self.run_probe('file-'+str(handled)+'-'+scenario,
                        result.stdout+caller+'\n.bss\n.Lclose_calls: .quad 0\n', runtime=runtime)
                    self.assertEqual((run.returncode,run.stdout,run.stderr),(0,b'',b''))

    def test_independent_source_reference_normal_and_acquisition_failure(self):
        present = self.directory/'reference.txt'
        present.write_text('native')
        entry = self.directory/'reference.eri'
        entry.write_text('''import std.files;
function acquire(path Text) returns Int fails files.FileError {
    with file be try files.openRead(path) { return 42; }
}
function probe(path Text) {
    let value be acquire(path) else error { output(7); return; };
    output(value);
}
''' + 'probe("'+str(present)+'");\nprobe("'+str(present)+'.missing");\n')
        module = compile_entry(entry, self.directory)
        observed = []
        Interpreter(output=observed.append,module_id=module.module_id,
                    imported_modules=module.imports).run(module.program)
        self.assertEqual(observed,['42','7'])
        binary = self.directory/'reference'
        self.assertEqual(build_native(entry,binary,self.directory),0)
        run = subprocess.run([str(binary)],capture_output=True,timeout=30)
        self.assertEqual((run.returncode,run.stdout,run.stderr),(0,b'42\n7\n',b''))

    def test_missing_roots_and_allocator_refusal_are_terminal(self):
        path = self.directory/'fault.txt'
        path.write_text('native')
        generated = self.generator('file-faults', self.source())
        self.assertEqual((generated.returncode, generated.stderr),(0,''),generated.stdout[-2000:])
        emitted = generated.stdout
        caller = self.caller(path, False)
        publish = emitted.split('erist_u2_file_718_publish_2:',1)[1].split('.size',1)[0]
        offset = re.search(r'movq (\d+)\(%rdi\),%rax', publish).group(1)
        missing_owner = emitted.replace('    call erist_u2_file_718_publish_2',
            '    movq $0,'+offset+'(%rsp)\n    call erist_u2_file_718_publish_2',1)
        for name, assembly in (
                ('owner', missing_owner+caller),
                ('failure-root', emitted+caller.replace('    call erist_u2_rooted_function_718',
                    '    xorl %ecx,%ecx\n    call erist_u2_rooted_function_718',1))):
            with self.subTest(root=name):
                run = self.run_probe('file-missing-'+name,assembly)
                self.assertEqual(run.returncode,1)
                self.assertIn(b'invalid internal scalar value operation',run.stderr)
        for stage in ('open','close'):
            runtime = self.runtime if stage == 'open' else resource.close_failures(self.runtime)
            boundary = 'erist_rt_file_open:' if stage == 'open' else '.Lr_close:'
            self.assertEqual(runtime.count(boundary+'\n'),1)
            runtime = runtime.replace(boundary+'\n',boundary+'\n    movq $1,.Lrefuse_alloc(%rip)\n',1)
            runtime = runtime.replace('erist_rt_alloc:\n',
                'erist_rt_alloc:\n    cmpq $0,.Lrefuse_alloc(%rip)\n'
                '    je .Lallow_alloc\n    xorl %eax,%eax\n    ret\n.Lallow_alloc:\n',1)
            with self.subTest(allocator=stage):
                run = self.run_probe('file-refuse-'+stage,
                    emitted+caller+'\n.bss\n.Lrefuse_alloc: .quad 0\n',runtime=runtime)
                self.assertEqual((run.returncode,run.stdout,run.stderr),
                    (1,b'',b'Eristavi runtime fault: out of memory\n'))

    def test_owned_and_c_generators_emit_identical_file_cfg(self):
        # Execute only this small generator fixture on owned runtime, not a
        # compiler self-build. Keep the established 120-second watchdog.
        folder = self.directory/'file-owned-generator'
        folder.mkdir()
        (folder/'compiler').symlink_to(ROOT/'src/compiler',target_is_directory=True)
        source = folder/'generator.eri'
        source.write_text(self.source())
        bootstrap = self.generator('file-parity-c',self.source())
        self.assertEqual((bootstrap.returncode,bootstrap.stderr),(0,''),bootstrap.stdout[-2000:])
        application = subprocess.run([str(self.frontend),'emit-asm',str(source),
            '--source-root',str(folder)],capture_output=True,text=True,timeout=120)
        self.assertEqual((application.returncode,application.stderr),(0,''),application.stdout[-2000:])
        assembly = folder/'owned.s'
        assembly.write_text(self.runtime+'\n'+application.stdout+
            '\n.text\n.globl _start\n_start:\n    xorl %ebp,%ebp\n'
            '    call erist_entry\n    jmp .Lgraph_finish\n'+graph.FINISH+
            '\n.section .note.GNU-stack,"",@progbits\n')
        obj = folder/'owned.o'
        binary = folder/'owned'
        subprocess.run(['as','--64',str(assembly),'-o',str(obj)],check=True,capture_output=True,timeout=20)
        subprocess.run(['ld','-nostdlib','-static','-e','_start',str(obj),'-o',str(binary)],
                       check=True,capture_output=True,timeout=20)
        headers = subprocess.check_output(['readelf','-lW',str(binary)],text=True)
        self.assertNotIn('INTERP',headers)
        self.assertNotIn('DYNAMIC',headers)
        self.assertNotIn('RWE',next(line for line in headers.splitlines() if 'GNU_STACK' in line))
        self.assertEqual(subprocess.check_output(['nm','-u',str(binary)],text=True).strip(),'')
        started = time.monotonic()
        owned = subprocess.run([str(binary)],env={'PATH':'/unavailable'},
                               capture_output=True,timeout=120)
        print('U2_FILE_OWNED_GENERATOR_SECONDS='+str(time.monotonic()-started),flush=True)
        self.assertEqual((owned.returncode,owned.stderr),(0,b''),owned.stdout[-2000:])
        self.assertEqual(owned.stdout,bootstrap.stdout.encode())
        path = self.directory/'owned-generated.txt'
        path.write_text('native')
        for fail_close in (False,True):
            runtime = resource.close_failures(self.runtime) if fail_close else self.runtime
            run = self.run_probe('file-owned-generated-'+str(fail_close),
                owned.stdout.decode()+self.caller(path,fail_close),runtime=runtime)
            self.assertEqual((run.returncode,run.stdout,run.stderr),(0,b'',b''))

    def test_unknown_binding_and_stale_owner_refuse_before_output(self):
        for name, source in (
            ('symbol', self.source().replace('u2.file.openRead.v1', 'u2.file.openFake.v1')),
            ('failure-shape', self.source().replace('aggregate.aggregate(graph,mp,[text,text])', 'aggregate.aggregate(graph,mp,[i64,text])')),
            ('effects', self.source().replace('"u2.file.openRead.v1",2,63,1', '"u2.file.openRead.v1",2,8,1')),
            ('owner', self.source().replace('native.emitFileChecked',
                'profile.entries.frozen=false; try words.set(profile.entries,phase,1,path.index); '
                'profile.entries.frozen=true;\n    native.emitFileChecked')),
            ('live-primary', self.source().replace('[text],[i64]', '[text,failure],[i64]',1)
                .replace('ab.block(fn,graph,[text])', 'ab.block(fn,graph,[text,failure])',1)
                .replace('let path be try build.parameter(fn,entry,0);',
                         'let primary be try build.parameter(fn,entry,1); let path be try build.parameter(fn,entry,0);')
                .replace('try ab.returnValues(fn,graph,done,[answer],loc);',
                         'let result be try body.returnFailure(fn,graph,table,done,primary,loc);')),
            ('stale', self.source().replace('native.emitFileChecked',
                                           'profile.revision=profile.revision+1;\n    native.emitFileChecked'))):
            with self.subTest(name=name):
                result = self.generator('file-refusal-'+name, source)
                self.assertEqual(result.returncode,1,result.stdout[-2000:])
                self.assertNotIn('.globl',result.stdout)
                self.assertIn('unsupported:',result.stdout)
                self.assertNotIn('leaked',result.stdout)

if __name__ == '__main__':
    unittest.main()
