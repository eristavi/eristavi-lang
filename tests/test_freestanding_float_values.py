"""Ordinary compiled Float application through the owned value runtime."""
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
import unittest
from compiler.erist.cli import build_native
import test_freestanding_text_lifetimes as lifetime_tests

ROOT=Path(__file__).resolve().parents[1]
STARTUP=r'''
.text
.globl _start
_start:
    xorl %ebp,%ebp
    call erist_entry
    call erist_rt_slots_live
    cmpq $270,%rax
    ja .Lfloat_application_fail
    call erist_rt_text_collect
    call erist_rt_text_live_buffers
    testq %rax,%rax
    jne .Lfloat_application_fail
    call erist_rt_allocator_release_all
    testq %rax,%rax
    jne .Lfloat_application_fail
    xorl %edi,%edi
    jmp erist_rt_exit
.Lfloat_application_fail:
    movl $1,%edi
    jmp erist_rt_exit
'''


@unittest.skipUnless(platform.system()=='Linux' and platform.machine().lower() in ('x86_64','amd64'),
                     'owned Float values currently target Linux x86-64')
class FreestandingFloatValueTests(unittest.TestCase):
    def test_real_application_copy_store_scope_escape_and_text_roots(self):
        for tool in ('as','ld','nm','readelf'):
            if not shutil.which(tool): self.skipTest(f'{tool} unavailable')
        with tempfile.TemporaryDirectory() as td:
            directory=Path(td); generator=directory/'runtime'; frontend=directory/'frontend'
            self.assertEqual(build_native(ROOT/'src/float_value_runtime.eri',generator,ROOT/'src'),0)
            emitted=subprocess.run([str(generator)],capture_output=True,text=True,timeout=60)
            self.assertEqual((emitted.returncode,emitted.stderr),(0,''))
            self.assertEqual(build_native(ROOT/'src/frontend.eri',frontend,ROOT/'src'),0)
            compiled=subprocess.run([str(frontend),'emit-asm',
                                     str(ROOT/'examples/freestanding_float_values.eri')],
                                    capture_output=True,text=True,timeout=30)
            self.assertEqual((compiled.returncode,compiled.stderr),(0,''))
            result=lifetime_tests.FreestandingTextLifetimeTests._link_run(
                self,directory,'float-values',emitted.stdout,compiled.stdout+STARTUP)
            expected=('1.25\n3.75\n0.30000000000000004\n-0\ninf\n-inf\nnan\n-nan\n'
                      'false\ntrue\nfalse\n4.9406564584124654e-324\n0\n'
                      '1.7976931348623157e+308\ninf\n-0\n1\n1.25\n1500\n4\n3\n1.25\n')
            self.assertEqual((result.returncode,result.stdout,result.stderr),(0,expected.encode(),b''))
            invalid=r'''
.text
.globl _start
_start:
    leaq .Linvalid_float(%rip),%rdi
    call evn_float
    movl $99,%edi
    jmp erist_rt_exit
.section .rodata
.Linvalid_float:
.asciz "1e+"
'''
            result=lifetime_tests.FreestandingTextLifetimeTests._link_run(
                self,directory,'invalid-float',emitted.stdout,
                # Full profile consumes compiler type descriptors even though this
                # fault path never reaches a view helper.
                '.section .data.rel.ro\n.globl ev_types\nev_types:\n'+
                ''.join(f'.long {kind},0\n.quad .Lbaseline_name,0,0\n' for kind in range(6))+
                '.section .rodata\n.Lbaseline_name:\n.byte 0\n'+invalid)
            self.assertEqual((result.returncode,result.stdout,result.stderr),
                             (1,b'',b'Eristavi runtime fault: invalid internal Float literal\n'))

            # A valid Float literal needs no scratch heap allocation. Slot OOM
            # after successful parsing must remain the ordinary terminal fault.
            failing_runtime = emitted.stdout.replace('erist_rt_alloc:\n',
                'erist_rt_alloc:\n    xorl %eax,%eax\n    ret\n', 1)
            self.assertNotEqual(failing_runtime, emitted.stdout)
            result=lifetime_tests.FreestandingTextLifetimeTests._link_run(
                self,directory,'float-oom',failing_runtime,
                '.section .data.rel.ro\n.globl ev_types\nev_types:\n'+
                ''.join(f'.long {kind},0\n.quad .Lbaseline_name,0,0\n' for kind in range(6))+
                '.section .rodata\n.Lbaseline_name:\n.byte 0\n'+invalid.replace('"1e+"','"1.0"'))
            self.assertEqual((result.returncode,result.stdout,result.stderr),
                             (1,b'',b'Eristavi runtime fault: out of memory\n'))
