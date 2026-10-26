"""Automatic CI qualification for Text-only typed heap lifetimes and real .eri output."""
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(platform.system() == 'Linux' and platform.machine().lower() in ('x86_64', 'amd64'),
                     'freestanding managed Text currently targets Linux x86-64')
class FreestandingTextLifetimeTests(unittest.TestCase):
    def _link_run(self, directory, name, runtime, assembly):
        source, obj, binary = (directory/(name+suffix) for suffix in ('.s', '.o', '.bin'))
        source.write_text(runtime + '\n' + assembly + '\n.section .note.GNU-stack,"",@progbits\n')
        subprocess.run(['as', '--64', str(source), '-o', str(obj)], check=True,
                       capture_output=True, timeout=20)
        subprocess.run(['ld', '-nostdlib', '-static', '-e', '_start', str(obj), '-o', str(binary)],
                       check=True, capture_output=True, timeout=20)
        headers = subprocess.check_output(['readelf', '-lW', str(binary)], text=True)
        self.assertNotIn('INTERP', headers)
        self.assertNotIn('DYNAMIC', headers)
        self.assertNotIn('RWE', next(line for line in headers.splitlines() if 'GNU_STACK' in line))
        self.assertEqual(subprocess.check_output(['nm', '-u', str(binary)], text=True).strip(), '')
        return subprocess.run([str(binary)], env={'PATH': '/unavailable'}, capture_output=True, timeout=20)

    def test_copies_stores_scope_escapes_collection_and_real_program(self):
        for tool in ('as', 'ld', 'readelf', 'nm'):
            if not shutil.which(tool):
                self.skipTest(f'{tool} unavailable')
        with tempfile.TemporaryDirectory() as td:
            directory = Path(td)
            generator = directory/'text-runtime'
            self.assertEqual(build_native(ROOT/'src/text_value_runtime.eri', generator, ROOT/'src'), 0)
            emitted = subprocess.run([str(generator)], capture_output=True, text=True, timeout=30)
            self.assertEqual((emitted.returncode, emitted.stderr), (0, ''))
            runtime = emitted.stdout
            success = r'''
.text
.globl _start
_start:
    xorl %ebp,%ebp
    call evn_scope_enter
    movq %rax,%r12
    leaq .Lold(%rip),%rdi
    movl $4,%esi
    call evn_text
    movq %rax,%r13
    movq %r13,%rdi
    call evn_copy
    movq %rax,%r14
    cmpq $4,0(%r14)
    jne .Lfail
    cmpq $4,8(%r14)
    jne .Lfail
    movq 16(%r13),%rax
    cmpq 16(%r14),%rax
    jne .Lfail
    cmpq $0,24(%r14)
    jne .Lfail
    call evn_scope_enter
    movq %rax,%r15
    leaq .Lnew(%rip),%rdi
    movl $3,%esi
    call evn_text
    movq %rax,%rbx
    movq %r13,%rdi
    movq %rbx,%rsi
    call evn_store
    movq %r15,%rdi
    movq %rbx,%rsi
    call evn_scope_leave
    movq %rax,%rbx
    call erist_rt_text_live_buffers
    cmpq $2,%rax
    jne .Lfail
    movq %r13,%rdi
    call evn_output
    movq %r14,%rdi
    call evn_output
    movq %rbx,%rdi
    call evn_output
    // Leave an outer scope while a nested scope is still active.
    call evn_scope_enter
    movq %r12,%rdi
    movq %rbx,%rsi
    call evn_scope_leave
    movq %rax,%r12
    call erist_rt_text_live_buffers
    cmpq $1,%rax
    jne .Lfail
    movl $100,%r14d
.Lchurn:
    call evn_scope_enter
    movq %rax,%r13
    leaq .Lold(%rip),%rdi
    movl $4,%esi
    call evn_text
    call erist_rt_text_live_buffers
    cmpq $2,%rax
    jne .Lfail
    call evn_void
    movq %r13,%rdi
    movq %rax,%rsi
    call evn_scope_leave
    // Each void result belongs to the outer slot stack; Text storage must still
    // return to baseline, without requiring global allocator release.
    call erist_rt_text_live_buffers
    cmpq $1,%rax
    jne .Lfail
    decq %r14
    jne .Lchurn
    movq %r12,%rdi
    call evn_output
    // Test-only shutdown: discard every remaining administrative slot, then
    // verify the typed Text sweep returns all tracked mappings to zero.
.Ldrop_slots:
    movq .Lvalue_slots(%rip),%rdi
    testq %rdi,%rdi
    je .Ldropped
    movq 32(%rdi),%rax
    movq %rax,.Lvalue_slots(%rip)
    call erist_rt_free
    testq %rax,%rax
    jne .Lfail
    jmp .Ldrop_slots
.Ldropped:
    call erist_rt_text_collect
    call erist_rt_text_live_buffers
    testq %rax,%rax
    jne .Lfail
    call erist_rt_allocator_release_all
    testq %rax,%rax
    jne .Lfail
    xorl %edi,%edi
    jmp erist_rt_exit
.Lfail:
    movl $1,%edi
    jmp erist_rt_exit
.section .rodata
.Lold:
.byte 65,0,195,169
.Lnew:
.byte 66,206,178
'''
            result = self._link_run(directory, 'lifetime', runtime, success)
            self.assertEqual((result.returncode, result.stdout, result.stderr),
                             (0, b'B\xce\xb2\nA\0\xc3\xa9\nB\xce\xb2\nB\xce\xb2\n', b''))
            invalid = '''.text
.globl _start
_start:
    leaq .Lbad(%rip),%rdi
    movl $3,%esi
    call evn_text
    movl $2,%edi
    jmp erist_rt_exit
.section .rodata
.Lbad:
.byte 237,160,128
'''
            result = self._link_run(directory, 'invalid', runtime, invalid)
            self.assertEqual((result.returncode, result.stdout, result.stderr),
                             (1, b'', b'Eristavi runtime fault: invalid UTF-8 inside Text\n'))
            frontend = directory/'frontend'
            self.assertEqual(build_native(ROOT/'src/frontend.eri', frontend, ROOT/'src'), 0)
            program = ROOT/'examples/freestanding_text_application.eri'
            compiled = subprocess.run([str(frontend), 'emit-asm', str(program)],
                                      capture_output=True, text=True, timeout=30)
            self.assertEqual((compiled.returncode, compiled.stderr), (0, ''))
            startup = '''.text
.globl _start
_start:
    xorl %ebp,%ebp
    call erist_entry
    call erist_rt_text_collect
    call erist_rt_text_live_buffers
    testq %rax,%rax
    jne .Lapp_fail
    call erist_rt_allocator_release_all
    testq %rax,%rax
    jne .Lapp_fail
    xorl %edi,%edi
    jmp erist_rt_exit
.Lapp_fail:
    movl $1,%edi
    jmp erist_rt_exit
'''
            result = self._link_run(directory, 'application', runtime, compiled.stdout+startup)
            self.assertEqual((result.returncode, result.stdout, result.stderr),
                             (0, 'Γεια σου — Привет 👋\nΓεια σου — Привет 👋\n\n'.encode(), b''))
