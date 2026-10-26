"""Snapshot-safe append capacity and nonowning Text registry regression."""
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
                     'freestanding Text currently targets Linux x86-64')
class TextCapacityTests(unittest.TestCase):
    def test_append_capacity_snapshots_branching_and_reclamation(self):
        for tool in ('as', 'ld', 'readelf', 'nm'):
            if not shutil.which(tool):
                self.skipTest(f'{tool} unavailable')
        with tempfile.TemporaryDirectory() as td:
            directory = Path(td)
            generator = directory/'runtime'
            self.assertEqual(build_native(ROOT/'src/text_value_runtime.eri', generator, ROOT/'src'), 0)
            emitted = subprocess.run([str(generator)], capture_output=True, text=True, timeout=60)
            self.assertEqual((emitted.returncode, emitted.stderr), (0, ''))
            runtime = emitted.stdout.replace('erist_rt_reserve:\n',
                'erist_rt_reserve:\n    incq .Lcapacity_reserves(%rip)\n', 1)
            self.assertNotEqual(runtime, emitted.stdout)
            assembly = r'''
.text
.globl _start
_start:
    xorl %ebp,%ebp
    # Three synthetic reservation bases deliberately collide in bucket zero.
    # The index neither dereferences nor owns these addresses.
    leaq .Lcapacity_fake(%rip),%rdi
    call erist_rt_text_registry_insert
    leaq .Lcapacity_fake+48(%rip),%rdi
    call erist_rt_text_registry_insert
    leaq .Lcapacity_fake+96(%rip),%rdi
    call erist_rt_text_registry_insert
    movl $0x1001000,%edi
    call erist_rt_text_registry_find
    leaq .Lcapacity_fake(%rip),%rcx
    cmpq %rcx,%rax
    jne .Lcapacity_fail
    movl $0x2002000,%edi
    call erist_rt_text_registry_find
    leaq .Lcapacity_fake+48(%rip),%rcx
    cmpq %rcx,%rax
    jne .Lcapacity_fail
    movl $0x4004000,%edi
    call erist_rt_text_registry_find
    testq %rax,%rax
    jne .Lcapacity_fail
    call erist_rt_text_registry_probe_count
    cmpq $8,%rax
    jne .Lcapacity_fail
    call erist_rt_text_registry_clear
    call evn_scope_enter
    movq %rax,%r12
    movq %rax,%rdi
    leaq .Lcapacity_keys(%rip),%rsi
    leaq .Lcapacity_classes(%rip),%rdx
    movl $4,%ecx
    call evn_bind_roots
    leaq .Lcapacity_a(%rip),%rdi
    movl $1,%esi
    call evn_text
    movq %rax,.Lcapacity_keys(%rip)
    movq %rax,.Lcapacity_keys+8(%rip)
    leaq .Lcapacity_b(%rip),%rdi
    movl $1,%esi
    call evn_text
    movq %rax,.Lcapacity_keys+16(%rip)
    movl $6000,%r14d
.Lcapacity_loop:
    movq .Lcapacity_keys(%rip),%rdi
    movq .Lcapacity_keys+16(%rip),%rsi
    call erist_rt_text_concat
    movq %rax,.Lcapacity_keys(%rip)
    decq %r14
    jne .Lcapacity_loop
    cmpq $80,.Lcapacity_reserves(%rip)
    ja .Lcapacity_fail
    movq .Lcapacity_keys(%rip),%rax
    cmpq $6001,8(%rax)
    jne .Lcapacity_fail
    movq 16(%rax),%rdi
    cmpb $97,(%rdi)
    jne .Lcapacity_fail
    movq $1,%rcx
.Lcapacity_check:
    cmpb $98,(%rdi,%rcx)
    jne .Lcapacity_fail
    incq %rcx
    cmpq $6001,%rcx
    jb .Lcapacity_check
    # Original prefix has retained both its length and its only byte.
    movq .Lcapacity_keys+8(%rip),%rax
    cmpq $1,8(%rax)
    jne .Lcapacity_fail
    movq 16(%rax),%rcx
    cmpb $97,(%rcx)
    jne .Lcapacity_fail
    # Branch from an old prefix. Its previously published suffix is immutable.
    movq %rax,%rdi
    movq .Lcapacity_keys+16(%rip),%rsi
    call erist_rt_text_concat
    movq %rax,.Lcapacity_keys+24(%rip)
    cmpq $2,8(%rax)
    jne .Lcapacity_fail
    movq 16(%rax),%rdi
    cmpw $0x6261,(%rdi)
    jne .Lcapacity_fail
    movq .Lcapacity_keys+8(%rip),%rcx
    cmpq 16(%rcx),%rdi
    je .Lcapacity_fail
    # Rebuild the index while deleting unrooted temporaries, then look up all
    # surviving buffers and concatenate from the newly published branch.
    movq %rax,%rdi
    call erist_rt_slots_collect
    call erist_rt_text_collect
    movq .Lcapacity_keys+24(%rip),%rdi
    movq %rdi,%rsi
    call erist_rt_text_concat
    movq %rax,.Lcapacity_keys+24(%rip)
    cmpq $4,8(%rax)
    jne .Lcapacity_fail
    movq 16(%rax),%rdi
    cmpl $0x62616261,(%rdi)
    jne .Lcapacity_fail
    call evn_void
    movq %r12,%rdi
    movq %rax,%rsi
    call evn_scope_leave
    call erist_rt_text_live_buffers
    testq %rax,%rax
    jne .Lcapacity_fail
    # No dangling hash entry may survive sweeping its owned record.
    leaq .Ltext_buckets(%rip),%rdi
    movl $4096,%ecx
    xorl %eax,%eax
    cld
    repe scasq
    jne .Lcapacity_fail
    call erist_rt_allocator_release_all
    testq %rax,%rax
    jne .Lcapacity_fail
    xorl %edi,%edi
    jmp erist_rt_exit
.Lcapacity_fail:
    movl $1,%edi
    jmp erist_rt_exit
.bss
.p2align 3
.Lcapacity_keys:
.zero 32
.Lcapacity_reserves:
.quad 0
.section .rodata
.Lcapacity_classes:
.byte 1,1,1,1
.data
.p2align 3
.Lcapacity_fake:
.quad 0,0x1001000,4096,1,0,0
.quad 0,0x2002000,4096,1,0,0
.quad 0,0x3003000,4096,1,0,0
.section .rodata
.Lcapacity_a:
.ascii "a"
.Lcapacity_b:
.ascii "b"
'''
            result = lifetime_tests.FreestandingTextLifetimeTests._link_run(
                self, directory, 'capacity', runtime, assembly)
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b'', b''))
