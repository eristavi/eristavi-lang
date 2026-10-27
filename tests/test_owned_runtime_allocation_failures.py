"""Fault injection at owned-runtime publication boundaries; no production hooks."""
from dataclasses import dataclass
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native
import test_freestanding_text_lifetimes as lifetime_tests

ROOT = Path(__file__).resolve().parents[1]
OOM = b'Eristavi runtime fault: out of memory\n'
INTERNAL = b'Eristavi runtime fault: invalid internal scalar value operation\n'


@dataclass(frozen=True)
class FailureCase:
    name: str
    setup: str = 'constructor'
    allocation: int = 0
    reservation: int = 0
    store: int = 0
    allocations: int = 0
    reservations: int = 0
    releases: int = 0
    buffers: int = 0
    published: int = 0
    message: bytes = OOM


CASES = (
    FailureCase('constructor-buffer-oom', reservation=1, reservations=1),
    FailureCase('constructor-record-oom', allocation=1, allocations=1, reservations=1, releases=1),
    FailureCase('constructor-arena-oom', reservation=2, allocations=1, reservations=2, releases=1),
    FailureCase('constructor-slot-oom', allocation=2, allocations=2, reservations=2, buffers=1),
    FailureCase('constructor-copy-failure', store=2, reservations=1, releases=1, message=INTERNAL),
    FailureCase('pooled-record-oom', setup='pooled-constructor', allocation=1,
                allocations=1, buffers=1),
    FailureCase('pooled-copy-failure', setup='pooled-constructor', store=2,
                buffers=1, message=INTERNAL),
    FailureCase('pooled-slot-oom', setup='pooled-constructor', allocation=2,
                allocations=2, buffers=2),
    FailureCase('empty-slot-oom', setup='empty', allocation=1, allocations=1),
    FailureCase('invalid-before-allocation', setup='invalid',
                message=b'Eristavi runtime fault: invalid UTF-8 inside Text\n'),
    FailureCase('append-slot-oom', setup='append', allocation=1, allocations=1, buffers=2, published=3),
    FailureCase('append-partial-copy-failure', setup='append', store=2,
                buffers=2, published=1, message=INTERNAL),
    FailureCase('growth-buffer-oom', setup='growth', reservation=1, reservations=1,
                buffers=2, published=4096),
    FailureCase('growth-record-oom', setup='growth', allocation=1, allocations=1,
                reservations=1, releases=1, buffers=2, published=4096),
    FailureCase('growth-slot-oom', setup='growth', allocation=2, allocations=2,
                reservations=1, buffers=3, published=4096),
    FailureCase('growth-partial-copy-failure', setup='growth', store=2,
                reservations=1, releases=1, buffers=2, published=4096, message=INTERNAL),
)


def replace_entry(runtime, name, instructions):
    entry = name+':\n'
    if runtime.count(entry) != 1:
        raise AssertionError(f'expected exactly one entry for {name}')
    return runtime.replace(entry, entry+instructions, 1)


def instrument(runtime, case):
    # Entry wrappers preserve all argument registers. Failures return the existing
    # private helper status; no simulated failure reaches a real store or syscall.
    for name, counter, stop, result in (
        ('erist_rt_alloc', 'allocations', case.allocation, '    xorl %eax,%eax\n'),
        ('erist_rt_text_store8', 'stores', case.store, '    xorl %eax,%eax\n    movl $1,%edx\n'),
    ):
        runtime = replace_entry(runtime, name, f'''    cmpq $0,.Lfi_armed(%rip)
    je .Lfi_continue_{counter}
    incq .Lfi_{counter}(%rip)
    cmpq ${stop},.Lfi_{counter}(%rip)
    jne .Lfi_continue_{counter}
{result}    ret
.Lfi_continue_{counter}:
''')
    runtime = replace_entry(runtime, 'erist_rt_reserve', f'''    cmpq $0,.Lfi_armed(%rip)
    je .Lfi_real_reserve
    incq .Lfi_reservations(%rip)
    cmpq ${case.reservation},.Lfi_reservations(%rip)
    je .Lfi_reserve_failed
    subq $8,%rsp
    call .Lfi_real_reserve
    addq $8,%rsp
    testq %rax,%rax
    je .Lfi_reserve_return
    movq .Lfi_mapped(%rip),%r8
    cmpq $8,%r8
    jae .Lfi_bad_exit
    shlq $4,%r8
    leaq .Lfi_pairs(%rip),%r9
    movq %rax,0(%r9,%r8)
    movq %rdx,8(%r9,%r8)
    incq .Lfi_mapped(%rip)
.Lfi_reserve_return:
    ret
.Lfi_reserve_failed:
    xorl %eax,%eax
    xorl %edx,%edx
    ret
.Lfi_real_reserve:
''')
    runtime = replace_entry(runtime, 'erist_rt_release', '''    cmpq $0,.Lfi_armed(%rip)
    je .Lfi_real_release
    incq .Lfi_releases(%rip)
    xorl %r8d,%r8d
    leaq .Lfi_pairs(%rip),%r9
.Lfi_release_find:
    cmpq .Lfi_mapped(%rip),%r8
    jae .Lfi_bad_exit
    movq %r8,%r10
    shlq $4,%r10
    cmpq 0(%r9,%r10),%rdi
    je .Lfi_release_found
    incq %r8
    jmp .Lfi_release_find
.Lfi_release_found:
    cmpq 8(%r9,%r10),%rsi
    jne .Lfi_bad_exit
    # Zeroing detects duplicate release as well as release of fixture storage.
    movq $0,0(%r9,%r10)
.Lfi_real_release:
''')
    checks = f'''    cmpq $1,%rdi
    jne .Lfi_bad_exit
    cmpq ${case.allocations},.Lfi_allocations(%rip)
    jne .Lfi_bad_exit
    cmpq ${case.reservations},.Lfi_reservations(%rip)
    jne .Lfi_bad_exit
    cmpq ${case.releases},.Lfi_releases(%rip)
    jne .Lfi_bad_exit
    cmpq ${case.buffers},.Ltext_count(%rip)
    jne .Lfi_bad_exit
'''
    if case.buffers == 0:
        checks += '''    cmpq $0,.Ltext_records(%rip)
    jne .Lfi_bad_exit
    leaq .Ltext_buckets(%rip),%rdi
    movl $4096,%ecx
    xorl %eax,%eax
    cld
    repe scasq
    jne .Lfi_bad_exit
'''
    if case.name in ('constructor-slot-oom', 'growth-slot-oom', 'pooled-slot-oom'):
        length = 4098 if case.setup == 'growth' else 2
        checks += f'''    movq .Ltext_records(%rip),%rdi
    movq 8(%rdi),%rdi
    subq $8,%rsp
    call erist_rt_text_registry_find
    addq $8,%rsp
    testq %rax,%rax
    je .Lfi_bad_exit
    cmpq ${length},24(%rax)
    jne .Lfi_bad_exit
'''
    if case.setup == 'pooled-constructor':
        expected_live = 2 if case.name == 'pooled-slot-oom' else 1
        checks += f'''    cmpq $1,.Ltext_pool_count(%rip)
    jne .Lfi_bad_exit
    movq .Lfi_left(%rip),%rax
    movq 16(%rax),%rax
    cmpb $98,(%rax)
    jne .Lfi_bad_exit
    cmpb $99,1(%rax)
    jne .Lfi_bad_exit
    movq -16(%rax),%rax
    cmpq ${expected_live},16(%rax)
    jne .Lfi_bad_exit
'''
    if case.setup in ('append', 'growth'):
        left_length = 4096 if case.setup == 'growth' else 1
        checks += f'''    movq .Lfi_left(%rip),%rax
    cmpq $4,0(%rax)
    jne .Lfi_bad_exit
    cmpq ${left_length},8(%rax)
    jne .Lfi_bad_exit
    movq 16(%rax),%rdi
    cmpb $97,(%rdi)
    jne .Lfi_bad_exit
    # Verify published high-water mark and index after the failure.
    subq $8,%rsp
    call erist_rt_text_registry_find
    addq $8,%rsp
    testq %rax,%rax
    je .Lfi_bad_exit
    cmpq ${case.published},24(%rax)
    jne .Lfi_bad_exit
'''
    return replace_entry(runtime, 'erist_rt_exit', checks+'    movl $1,%edi\n')


def program(case):
    setup = '.text\n.globl _start\n_start:\n    xorl %ebp,%ebp\n'
    if case.setup == 'pooled-constructor':
        setup += '''    leaq .Lfi_bytes(%rip),%rdi
    movl $2,%esi
    call evn_text
    movq %rax,.Lfi_left(%rip)
'''
    if case.setup in ('append', 'growth'):
        left_length = 4096 if case.setup == 'growth' else 1
        setup += f'''    leaq .Lfi_left_bytes(%rip),%rdi
    movl ${left_length},%esi
    call evn_text
    movq %rax,.Lfi_left(%rip)
    leaq .Lfi_bytes(%rip),%rdi
    movl $2,%esi
    call evn_text
    movq %rax,%rsi
    movq .Lfi_left(%rip),%rdi
    movq $1,.Lfi_armed(%rip)
    call erist_rt_text_concat
'''
    else:
        pointer, count = ('.Lfi_invalid', 3) if case.setup == 'invalid' else ('.Lfi_bytes', 2)
        if case.setup == 'empty':
            count = 0
        setup += f'''    movq $1,.Lfi_armed(%rip)
    leaq {pointer}(%rip),%rdi
    movl ${count},%esi
    call evn_text
'''
    return setup+'''
    # Returning normally would falsely turn a failed allocation into success.
.Lfi_bad_exit:
    movl $99,%edi
    movl $60,%eax
    syscall
    ud2
.bss
.p2align 3
.Lfi_armed:
.quad 0
.Lfi_allocations:
.quad 0
.Lfi_reservations:
.quad 0
.Lfi_stores:
.quad 0
.Lfi_releases:
.quad 0
.Lfi_mapped:
.quad 0
.Lfi_pairs:
.zero 128
.Lfi_left:
.quad 0
.section .rodata
.Lfi_bytes:
.ascii "bc"
.Lfi_invalid:
.byte 0xed,0xa0,0x80
.Lfi_left_bytes:
.fill 4096,1,97
'''


@unittest.skipUnless(platform.system() == 'Linux' and platform.machine().lower() in ('x86_64', 'amd64'),
                     'owned runtime currently targets Linux x86-64')
class OwnedRuntimeAllocationFailureTests(unittest.TestCase):
    def test_text_publication_and_shared_capacity_failure_boundaries(self):
        for tool in ('as', 'ld', 'readelf', 'nm'):
            if not shutil.which(tool):
                self.skipTest(f'{tool} unavailable')
        with tempfile.TemporaryDirectory() as td:
            directory = Path(td)
            generator = directory/'runtime'
            self.assertEqual(build_native(ROOT/'src/text_value_runtime.eri', generator, ROOT/'src'), 0)
            emitted = subprocess.run([str(generator)], capture_output=True, text=True, timeout=60)
            self.assertEqual((emitted.returncode, emitted.stderr), (0, ''))
            for case in CASES:
                with self.subTest(case=case.name):
                    result = lifetime_tests.FreestandingTextLifetimeTests._link_run(
                        self, directory, case.name, instrument(emitted.stdout, case), program(case))
                    self.assertEqual((result.returncode, result.stdout, result.stderr),
                                     (1, b'', case.message))
