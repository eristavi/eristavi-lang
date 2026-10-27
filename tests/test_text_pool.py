"""Independent storage isolation, recycling, OOM and reclamation checks."""
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
                     'owned Text pools target Linux x86-64')
class TextPoolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for tool in ('as', 'ld', 'readelf', 'nm'):
            if not shutil.which(tool):
                raise unittest.SkipTest(f'{tool} unavailable')
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.directory = Path(cls.temporary.name)
        generator = cls.directory/'generator'
        if build_native(ROOT/'src/text_value_runtime.eri', generator, ROOT/'src') != 0:
            raise AssertionError('Text generator did not compile')
        result = subprocess.run([generator], capture_output=True, text=True, timeout=60)
        if (result.returncode, result.stderr) != (0, ''):
            raise AssertionError(result.stderr)
        cls.runtime = result.stdout

    def test_independent_slices_recycle_and_release_all_reservations(self):
        runtime = self.runtime.replace('erist_rt_reserve:\n', '''erist_rt_reserve:
    incq .Lpool_test_reserves(%rip)
''', 1).replace('erist_rt_release:\n', '''erist_rt_release:
    incq .Lpool_test_releases(%rip)
''', 1)
        probe = r'''
.text
.globl _start
_start:
    # Reject null and out-of-slice access before reading administrative headers.
    xorl %edi,%edi
    movl $256,%esi
    xorl %edx,%edx
    call erist_rt_text_load8
    cmpq $1,%rdx
    jne .Lpool_fail
    xorl %edi,%edi
    movl $256,%esi
    call erist_rt_text_storage_release
    cmpq $-1,%rax
    jne .Lpool_fail
    # Keep hundreds of independently writable buffers live across several slabs.
    xorl %r12d,%r12d
.Lpool_allocate:
    movl $256,%edi
    call erist_rt_text_storage_reserve
    testq %rax,%rax
    je .Lpool_fail
    cmpq $256,%rdx
    jne .Lpool_fail
    leaq .Lpool_keys(%rip),%r13
    movq %rax,(%r13,%r12,8)
    movq %rax,%rdi
    movq %rdx,%rsi
    xorl %edx,%edx
    movq %r12,%rcx
    call erist_rt_text_store8
    testq %rdx,%rdx
    jne .Lpool_fail
    movq (%r13,%r12,8),%rdi
    movl $256,%esi
    movl $255,%edx
    movq %r12,%rcx
    call erist_rt_text_store8
    testq %rdx,%rdx
    jne .Lpool_fail
    incq %r12
    cmpq $181,%r12
    jb .Lpool_allocate
    # A page reservation per small buffer would exceed this independent budget.
    cmpq $10,.Lpool_test_reserves(%rip)
    ja .Lpool_fail
    movq .Lpool_test_reserves(%rip),%r15
    # Verify isolation, rejecting an access exactly beyond the slice capacity.
    xorl %r12d,%r12d
.Lpool_verify:
    movq (%r13,%r12,8),%rdi
    movl $256,%esi
    xorl %edx,%edx
    call erist_rt_text_load8
    testq %rdx,%rdx
    jne .Lpool_fail
    cmpq %r12,%rax
    jne .Lpool_fail
    movq (%r13,%r12,8),%rdi
    movl $256,%esi
    movl $255,%edx
    call erist_rt_text_load8
    testq %rdx,%rdx
    jne .Lpool_fail
    cmpq %r12,%rax
    jne .Lpool_fail
    movq (%r13,%r12,8),%rdi
    movl $256,%esi
    movl $256,%edx
    movl $255,%ecx
    call erist_rt_text_store8
    cmpq $1,%rdx
    jne .Lpool_fail
    incq %r12
    cmpq $181,%r12
    jb .Lpool_verify
    # Return a block from a full slab; reject a second return while its slab lives.
    movq (%r13),%rdi
    movl $256,%esi
    call erist_rt_text_storage_release
    testq %rax,%rax
    jne .Lpool_fail
    movq (%r13),%rdi
    movl $256,%esi
    call erist_rt_text_storage_release
    cmpq $-1,%rax
    jne .Lpool_fail
    movl $1,%edi
    call erist_rt_text_storage_reserve
    cmpq (%r13),%rax
    jne .Lpool_fail
    cmpq .Lpool_test_reserves(%rip),%r15
    jne .Lpool_fail
    # Interleaved frees exercise non-head empty slabs and available-list links.
    xorl %r14d,%r14d
.Lpool_free_pass:
    movq %r14,%r12
.Lpool_free:
    movq (%r13,%r12,8),%rdi
    movl $256,%esi
    call erist_rt_text_storage_release
    testq %rax,%rax
    jne .Lpool_fail
    addq $2,%r12
    cmpq $181,%r12
    jb .Lpool_free
    incq %r14
    cmpq $2,%r14
    jb .Lpool_free_pass
    cmpq $0,.Ltext_pool_count(%rip)
    jne .Lpool_fail
    cmpq $0,.Ltext_pool_available(%rip)
    jne .Lpool_fail
    movq .Lpool_test_reserves(%rip),%rax
    cmpq .Lpool_test_releases(%rip),%rax
    jne .Lpool_fail
    # The next use must work after the entire pool has been unmapped.
    movl $2,%edi
    call erist_rt_text_storage_reserve
    testq %rax,%rax
    je .Lpool_fail
    movq %rax,%rdi
    movq %rdx,%rsi
    call erist_rt_text_storage_release
    testq %rax,%rax
    jne .Lpool_fail
    cmpq $0,.Ltext_pool_count(%rip)
    jne .Lpool_fail
    xorl %edi,%edi
    jmp erist_rt_exit
.Lpool_fail:
    movl $99,%edi
    jmp erist_rt_exit
.bss
.p2align 3
.Lpool_keys:
.zero 1448
.Lpool_test_reserves:
.quad 0
.Lpool_test_releases:
.quad 0
'''
        result = lifetime_tests.FreestandingTextLifetimeTests._link_run(
            self, self.directory, 'pool-isolation', runtime, probe)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b'', b''))

    def test_failed_slab_growth_preserves_full_slabs_and_large_storage(self):
        runtime = self.runtime.replace('erist_rt_reserve:\n', '''erist_rt_reserve:
    cmpq $0,.Lpool_deny_reserve(%rip)
    je .Lpool_real_reserve
    xorl %eax,%eax
    xorl %edx,%edx
    ret
.Lpool_real_reserve:
''', 1)
        probe = r'''
.text
.globl _start
_start:
    xorl %r12d,%r12d
    leaq .Lpool_growth_keys(%rip),%r13
.Lpool_fill:
    movl $1,%edi
    call erist_rt_text_storage_reserve
    testq %rax,%rax
    je .Lpool_growth_fail
    movq %rax,(%r13,%r12,8)
    movb $42,(%rax)
    incq %r12
    cmpq $60,%r12
    jb .Lpool_fill
    movq $1,.Lpool_deny_reserve(%rip)
    movl $1,%edi
    call erist_rt_text_storage_reserve
    orq %rdx,%rax
    jne .Lpool_growth_fail
    cmpq $1,.Ltext_pool_count(%rip)
    jne .Lpool_growth_fail
    cmpq $0,.Ltext_pool_available(%rip)
    jne .Lpool_growth_fail
    movq $0,.Lpool_deny_reserve(%rip)
    xorl %r12d,%r12d
.Lpool_growth_free:
    movq (%r13,%r12,8),%rdi
    cmpb $42,(%rdi)
    jne .Lpool_growth_fail
    movl $256,%esi
    call erist_rt_text_storage_release
    testq %rax,%rax
    jne .Lpool_growth_fail
    incq %r12
    cmpq $60,%r12
    jb .Lpool_growth_free
    cmpq $0,.Ltext_pool_count(%rip)
    jne .Lpool_growth_fail
    # A 257-byte request retains the raw page-backed path and exact release pair.
    movl $257,%edi
    call erist_rt_text_storage_reserve
    testq %rax,%rax
    je .Lpool_growth_fail
    cmpq $4096,%rdx
    jne .Lpool_growth_fail
    movq %rax,%rdi
    movq %rdx,%rsi
    call erist_rt_text_storage_release
    testq %rax,%rax
    jne .Lpool_growth_fail
    xorl %edi,%edi
    jmp erist_rt_exit
.Lpool_growth_fail:
    movl $99,%edi
    jmp erist_rt_exit
.bss
.p2align 3
.Lpool_growth_keys:
.zero 480
.Lpool_deny_reserve:
.quad 0
'''
        result = lifetime_tests.FreestandingTextLifetimeTests._link_run(
            self, self.directory, 'pool-failed-growth', runtime, probe)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b'', b''))
