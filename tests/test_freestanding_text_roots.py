"""Hosted checks for exact-address root-map slot pruning in the Text profile."""
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native
import test_freestanding_text_lifetimes as lifetime_tests

ROOT = Path(__file__).resolve().parents[1]


LARGE_ROOT_PROBE = r'''
.text
.globl _start
_start:
    call evn_scope_enter
    movq %rax,%r12
    xorl %ebx,%ebx
.Lroot_create:
    movq %rbx,%rdi
    call evn_int
    leaq .Lroot_keys(%rip),%r8
    movq %rax,(%r8,%rbx,8)
    leaq .Lroot_classes(%rip),%r9
    movb $1,(%r9,%rbx)
    movq %rbx,%rcx
    andl $3,%ecx
    cmpq $1,%rcx
    jne .Lroot_not_duplicate
    movq -8(%r8,%rbx,8),%rax
    movq %rax,(%r8,%rbx,8)
.Lroot_not_duplicate:
    cmpq $2,%rcx
    jne .Lroot_not_machine
    movb $7,(%r9,%rbx)
.Lroot_not_machine:
    cmpq $3,%rcx
    jne .Lroot_created
    movq $1,(%r8,%rbx,8)
.Lroot_created:
    incq %rbx
    cmpq $1024,%rbx
    jb .Lroot_create
    movq %r12,%rdi
    leaq .Lroot_keys(%rip),%rsi
    leaq .Lroot_classes(%rip),%rdx
    movl $1024,%ecx
    call evn_bind_roots
    movl $1024,%ebx
.Lroot_garbage:
    call evn_void
    decq %rbx
    jne .Lroot_garbage
    movq %rax,%r13
    movq %rax,%rdi
    call erist_rt_slots_collect
    call erist_rt_slots_live
    cmpq $257,%rax
    jne .Lfail
    # A newly entered scope's mark is a root even if its key is overwritten.
    call evn_scope_enter
    movq %rax,%r14
    movq %rax,%rdi
    leaq .Lroot_keys(%rip),%rsi
    leaq .Lroot_classes(%rip),%rdx
    xorl %ecx,%ecx
    call evn_bind_roots
    # Clear all old root keys, then install a different live slot at a late key.
    leaq .Lroot_keys(%rip),%rdi
    movl $1024,%ecx
    xorl %eax,%eax
    rep stosq
    movl $42,%edi
    call evn_int
    movq %rax,.Lroot_keys+8184(%rip)
    xorl %edi,%edi
    call erist_rt_slots_collect
    call erist_rt_slots_live
    cmpq $2,%rax
    jne .Lfail
    movq %r13,%rdi
    cmpq $5,(%rdi)
    jne .Lfail
    movq .Lroot_keys+8184(%rip),%rdi
    cmpq $42,8(%rdi)
    jne .Lfail
    call evn_void
    movq %r14,%rdi
    movq %rax,%rsi
    call evn_scope_leave
    movq %r12,%rdi
    movq %rax,%rsi
    call evn_scope_leave
    movq .Lroot_reservations(%rip),%rax
    movl $ROOT_PROBE_LIMIT,%ecx
    testq %rcx,%rcx
    je .Lroot_compare_releases
    testq %rax,%rax
    je .Lfail
.Lroot_compare_releases:
    cmpq .Lroot_releases(%rip),%rax
    jne .Lfail
    movq .Lroot_probes(%rip),%rax
    cmpq $ROOT_PROBE_LIMIT,%rax
    ja .Lfail
    movq .Lvalue_slots(%rip),%rdi
    movq $0,.Lvalue_slots(%rip)
    movq $0,.Lvalue_slot_count(%rip)
    call erist_rt_free
    testq %rax,%rax
    jne .Lfail
    cmpq $0,.Lslots_scratch_busy(%rip)
    jne .Lfail
    call erist_rt_allocator_release_all
    testq %rax,%rax
    jne .Lfail
    xorl %edi,%edi
    jmp erist_rt_exit
.Lfail:
    movl $99,%edi
    jmp erist_rt_exit
.bss
.p2align 3
.Lroot_keys:
.zero 8192
.Lroot_classes:
.zero 1024
.p2align 3
.Lroot_probes:
.quad 0
.Lroot_reservations:
.quad 0
.Lroot_releases:
.quad 0
'''


@unittest.skipUnless(platform.system() == 'Linux' and platform.machine().lower() in ('x86_64', 'amd64'),
                     'freestanding Text roots currently target Linux x86-64')
class FreestandingTextRootTests(unittest.TestCase):
    def test_registered_roots_bound_loop_slots_and_preserve_pending_results(self):
        for tool in ('as', 'ld', 'readelf', 'nm'):
            if not shutil.which(tool):
                self.skipTest(f'{tool} unavailable')
        probe = r'''
.text
.globl _start
_start:
    xorl %ebp,%ebp
    call evn_scope_enter
    movq %rax,%r12
    movl $300,%r14d
.Lunregistered:
    leaq .Ltemporary(%rip),%rdi
    movl $3,%esi
    call evn_text
    decq %r14
    jne .Lunregistered
    movq %rax,%r13
    call erist_rt_slots_live
    cmpq $300,%rax
    jne .Lfail
    movq %r12,%rdi
    leaq .Lkeys(%rip),%rsi
    leaq .Lclasses(%rip),%rdx
    xorl %ecx,%ecx
    call evn_bind_roots
    movq %r13,%rdi
    call erist_rt_slots_collect
    call erist_rt_text_collect
    call erist_rt_slots_live
    cmpq $1,%rax
    jne .Lfail
    call erist_rt_text_live_buffers
    cmpq $1,%rax
    jne .Lfail
    call evn_void
    movq %r12,%rdi
    movq %rax,%rsi
    call evn_scope_leave
    movq %rax,%rdi
    movq $0,.Lvalue_slots(%rip)
    movq $0,.Lvalue_slot_count(%rip)
    call erist_rt_free
    testq %rax,%rax
    jne .Lfail
    call erist_rt_text_live_buffers
    testq %rax,%rax
    jne .Lfail

    call evn_scope_enter
    movq %rax,%r12
    movq %rax,%rdi
    leaq .Lkeys(%rip),%rsi
    leaq .Lclasses(%rip),%rdx
    movl $4,%ecx
    call evn_bind_roots
    leaq .Lkept(%rip),%rdi
    movl $4,%esi
    call evn_text
    movq %rax,.Lkeys(%rip)
    movq %rax,%rdi
    call evn_copy
    movq %rax,.Lkeys+8(%rip)
    leaq .Ltemporary(%rip),%rdi
    movl $3,%esi
    call evn_text
    # This exact slot address is deliberately classified as a machine word.
    movq %rax,.Lkeys+16(%rip)
    # A stale/invalid value-class key must never be dereferenced.
    movq $1,.Lkeys+24(%rip)
    movl $2000,%r14d
.Lloop:
    leaq .Ltemporary(%rip),%rdi
    movl $3,%esi
    call evn_text
    decq %r14
    jne .Lloop
    movq %rax,%r13
    call erist_rt_slots_live
    cmpq $260,%rax
    ja .Lfail
    call erist_rt_text_live_buffers
    cmpq $259,%rax
    ja .Lfail
    # Force a collection below the automatic threshold to inspect exact survivors.
    movq %r13,%rdi
    call erist_rt_slots_collect
    call erist_rt_text_collect
    call erist_rt_slots_live
    cmpq $3,%rax
    jne .Lfail
    call erist_rt_text_live_buffers
    cmpq $2,%rax
    jne .Lfail
    movq .Lkeys(%rip),%rdi
    call evn_output
    movq .Lkeys+8(%rip),%rdi
    call evn_output
    movq %r13,%rdi
    call evn_output

    call evn_scope_enter
    movq %rax,%r15
    movq %rax,%rdi
    leaq .Linner_keys(%rip),%rsi
    leaq .Lclasses(%rip),%rdx
    xorl %ecx,%ecx
    call evn_bind_roots
    leaq .Linner(%rip),%rdi
    movl $5,%esi
    call evn_text
    movq %rax,%rbx
    movq %rax,%rdi
    call erist_rt_slots_collect
    call erist_rt_text_collect
    # Two outer root slots, the inner scope's mark, and the pending inner result.
    call erist_rt_slots_live
    cmpq $4,%rax
    jne .Lfail
    call erist_rt_text_live_buffers
    cmpq $3,%rax
    jne .Lfail
    movq %r15,%rdi
    movq %rbx,%rsi
    call evn_scope_leave
    movq %rax,%rsi
    movq %r12,%rdi
    call evn_scope_leave
    movq %rax,%r12
    movq %rax,%rdi
    call evn_output
    call erist_rt_text_live_buffers
    cmpq $1,%rax
    jne .Lfail
    movq $0,.Lvalue_slots(%rip)
    movq $0,.Lvalue_slot_count(%rip)
    movq %r12,%rdi
    call erist_rt_free
    testq %rax,%rax
    jne .Lfail
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
.bss
.p2align 3
.Lkeys:
.zero 32
.Linner_keys:
.zero 8
.section .rodata
.Lclasses:
.byte 1,1,7,1
.Lkept:
.byte 65,0,195,169
.Ltemporary:
.ascii "tmp"
.Linner:
.ascii "inner"
'''
        with tempfile.TemporaryDirectory() as td:
            directory = Path(td)
            generator = directory/'runtime'
            self.assertEqual(build_native(ROOT/'src/text_value_runtime.eri', generator, ROOT/'src'), 0)
            emitted = subprocess.run([str(generator)], capture_output=True, text=True, timeout=30)
            self.assertEqual((emitted.returncode, emitted.stderr), (0, ''))
            result = lifetime_tests.FreestandingTextLifetimeTests._link_run(
                self, directory, 'roots', emitted.stdout, probe)
            self.assertEqual((result.returncode, result.stdout, result.stderr),
                             (0, b'A\0\xc3\xa9\nA\0\xc3\xa9\ntmp\ninner\n', b''))
            # Production index now has 64 KiB of reusable cleared scratch.
            # Force acquire failure to verify the *same* linear fallback,
            # without changing or weakening any root-output oracles.
            entry = '.Lslots_scratch_acquire:\n'
            self.assertEqual(emitted.stdout.count(entry), 1)
            fallback = emitted.stdout.replace(
                entry, entry+'    xorl %eax,%eax\n    xorl %edx,%edx\n    ret\n', 1)
            result = lifetime_tests.FreestandingTextLifetimeTests._link_run(
                self, directory, 'roots-no-index-memory', fallback, probe)
            self.assertEqual((result.returncode, result.stdout, result.stderr),
                             (0, b'A\0\\xc3\\xa9\\nA\0\\xc3\\xa9\\ntmp\\ninner\\n', b''))
            # Every indexed probe must use exact membership, never the
            # slow frame-by-frame fallback. Count acquire/release pairs
            # instead of syscalls: shared cache ownership is the contract.
            indexed = emitted.stdout.replace('.Lslots_root:\n',
                '.Lslots_root:\n    jmp .Lfail\n', 1)
            indexed = indexed.replace('.Lslots_index_find_probe:\n',
                '.Lslots_index_find_probe:\n    incq .Lroot_probes(%rip)\n', 1)
            indexed = indexed.replace(entry,
                entry+'    incq .Lroot_reservations(%rip)\n', 1)
            release_entry = '.Lslots_scratch_release:\n'
            self.assertEqual(indexed.count(release_entry), 1)
            indexed = indexed.replace(release_entry,
                release_entry+'    incq .Lroot_releases(%rip)\n', 1)
            for name, runtime, bound in [('indexed', indexed, 20000),
                                         ('fallback', fallback, 0)]:
                result = lifetime_tests.FreestandingTextLifetimeTests._link_run(
                    self, directory, 'large-roots-'+name, runtime,
                    LARGE_ROOT_PROBE.replace('ROOT_PROBE_LIMIT', str(bound)))
                self.assertEqual((result.returncode, result.stdout, result.stderr),
                                 (0, b'', b''))
            frontend = directory/'frontend'
            self.assertEqual(build_native(ROOT/'src/frontend.eri', frontend, ROOT/'src'), 0)
            compiled = subprocess.run([str(frontend), 'emit-asm',
                                       str(ROOT/'examples/freestanding_text_loop.eri')],
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
    jne .Lloop_fail
    call erist_rt_allocator_release_all
    testq %rax,%rax
    jne .Lloop_fail
    xorl %edi,%edi
    jmp erist_rt_exit
.Lloop_fail:
    movl $1,%edi
    jmp erist_rt_exit
'''
            result = lifetime_tests.FreestandingTextLifetimeTests._link_run(
                self, directory, 'loop', emitted.stdout, compiled.stdout+startup)
            self.assertEqual((result.returncode, result.stdout, result.stderr),
                             (0, 'Γεια σου 👋\n3000\n'.encode(), b''))
