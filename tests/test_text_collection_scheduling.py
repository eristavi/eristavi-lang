"""Hosted deterministic collection-frequency and orphan-release regression."""
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native
import test_freestanding_text_lifetimes as lifetime_tests

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(platform.system() == 'Linux' and platform.machine().lower() in ('x86_64', 'amd64'),
                     'freestanding Text collector currently targets Linux x86-64')
class TextCollectionSchedulingTests(unittest.TestCase):
    def test_scalar_allocations_batch_tracing_and_text_replacement_releases_orphan(self):
        for tool in ('as', 'ld', 'readelf', 'nm'):
            if not shutil.which(tool):
                self.skipTest(f'{tool} unavailable')
        with tempfile.TemporaryDirectory() as td:
            directory = Path(td); generator = directory/'runtime'
            self.assertEqual(build_native(ROOT/'src/text_value_runtime.eri', generator, ROOT/'src'), 0)
            emitted = subprocess.run([str(generator)], capture_output=True, text=True, timeout=60)
            self.assertEqual((emitted.returncode, emitted.stderr), (0, ''))
            assembly = r'''
.text
.globl _start
_start:
    xorl %ebp,%ebp
    call evn_scope_enter
    movq %rax,%r12
    movq %rax,%rdi
    leaq .Ltrace_keys(%rip),%rsi
    leaq .Ltrace_classes(%rip),%rdx
    movl $2,%ecx
    call evn_bind_roots
    leaq .Ltrace_kept(%rip),%rdi
    movl $4,%esi
    call evn_text
    movq %rax,%rbx
    movq %rax,.Ltrace_keys(%rip)
    xorl %edi,%edi
    call evn_int
    movq %rax,%r13
    movq %rax,.Ltrace_keys+8(%rip)
    call erist_rt_text_collection_count
    movq %rax,%r15
    movl $10000,%r14d
.Ltrace_loop:
    movl $42,%edi
    call evn_int
    movq %r13,%rdi
    movq %rax,%rsi
    call evn_store
    decq %r14
    jne .Ltrace_loop
    call erist_rt_text_collection_count
    subq %r15,%rax
    cmpq $100,%rax
    ja .Ltrace_fail
    testq %rax,%rax
    je .Ltrace_fail
    call erist_rt_slots_live
    cmpq $270,%rax
    ja .Ltrace_fail
    call erist_rt_text_live_buffers
    cmpq $1,%rax
    jne .Ltrace_fail
    movq %rbx,%rdi
    call evn_output
    leaq .Ltrace_new(%rip),%rdi
    movl $3,%esi
    call evn_text
    movq %rax,%r14
    call erist_rt_text_live_buffers
    cmpq $2,%rax
    jne .Ltrace_fail
    movq %rbx,%rdi
    movq %r14,%rsi
    call evn_store
    # Below the pruning threshold, the next scalar allocation must still trace
    # the replaced Text edge and release its now-unreachable backing reservation.
    xorl %edi,%edi
    call evn_int
    call erist_rt_text_live_buffers
    cmpq $1,%rax
    jne .Ltrace_fail
    movq %rbx,%rdi
    call evn_output
    call evn_void
    movq %r12,%rdi
    movq %rax,%rsi
    call evn_scope_leave
    call erist_rt_text_live_buffers
    testq %rax,%rax
    jne .Ltrace_fail
    call erist_rt_allocator_release_all
    testq %rax,%rax
    jne .Ltrace_fail
    xorl %edi,%edi
    jmp erist_rt_exit
.Ltrace_fail:
    movl $1,%edi
    jmp erist_rt_exit
.bss
.p2align 3
.Ltrace_keys:
.zero 16
.section .rodata
.Ltrace_classes:
.byte 1,1
.Ltrace_kept:
.ascii "kept"
.Ltrace_new:
.ascii "new"
'''
            result = lifetime_tests.FreestandingTextLifetimeTests._link_run(
                self, directory, 'scheduling', emitted.stdout, assembly)
            self.assertEqual((result.returncode, result.stdout, result.stderr),
                             (0, b'kept\nnew\n', b''))
