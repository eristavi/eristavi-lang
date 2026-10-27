"""Hosted qualification of Text operators and all supported value safe points."""
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native
import test_freestanding_text_lifetimes as lifetime_tests

ROOT = Path(__file__).resolve().parents[1]


def byte_data(label, data):
    return [label+':', '.byte '+','.join(map(str, data or b'\0'))]


def check_text(value, label, data):
    return [f'cmpq $4,0({value})', 'jne .Lfail', f'cmpq ${len(data)},8({value})',
            'jne .Lfail', f'movq 16({value}),%rdi', f'leaq {label}(%rip),%rsi',
            f'movq ${len(data)},%rcx', 'cld', 'repe cmpsb', 'jne .Lfail'] if data else [
                f'cmpq $4,0({value})', 'jne .Lfail', f'cmpq $0,8({value})', 'jne .Lfail']


def operator_probe():
    cases = [b'', b'A', b'A\0B', 'α'.encode(), 'é'.encode(), 'e\u0301'.encode(), '👋'.encode()]
    pairs = [(a, b) for a in cases for b in cases] + [(b'x'*4095, 'é'.encode())]
    code = ['.text', '.globl _start', '_start:', 'xorl %ebp,%ebp',
            'call evn_scope_enter', 'movq %rax,%r12']
    data = ['.section .rodata']
    for index, (a, b) in enumerate(pairs):
        la, lb, lc = (f'.Lpair_{index}_{part}' for part in ('a', 'b', 'joined'))
        data += byte_data(la, a)+byte_data(lb, b)+byte_data(lc, a+b)
        code += [f'leaq {la}(%rip),%rdi', f'movq ${len(a)},%rsi', 'call evn_text',
                 'movq %rax,%r13', f'leaq {lb}(%rip),%rdi', f'movq ${len(b)},%rsi',
                 'call evn_text', 'movq %rax,%r14']
        for op, expected in ((5, a == b), (6, a != b)):
            code += [f'movl ${op},%edi', 'movq %r13,%rsi', 'movq %r14,%rdx',
                     'call evn_binary', 'cmpq $3,0(%rax)', 'jne .Lfail',
                     f'cmpq ${int(expected)},8(%rax)', 'jne .Lfail']
        code += ['xorl %edi,%edi', 'movq %r13,%rsi', 'movq %r14,%rdx',
                 'call evn_binary', 'movq %rax,%r15']
        code += check_text('%r15', lc, a+b)
        code += check_text('%r13', la, a)+check_text('%r14', lb, b)
        # Self-concatenation must preserve its input snapshot too.
        if index == 10:
            doubled = f'.Lpair_{index}_double'
            data += byte_data(doubled, a+a)
            code += ['xorl %edi,%edi', 'movq %r13,%rsi', 'movq %r13,%rdx',
                     'call evn_binary', 'movq %rax,%r15']
            code += check_text('%r15', doubled, a+a)+check_text('%r13', la, a)
    code += ['call evn_void', 'movq %r12,%rdi', 'movq %rax,%rsi', 'call evn_scope_leave',
             'call erist_rt_text_live_buffers', 'testq %rax,%rax', 'jne .Lfail',
             'call erist_rt_allocator_release_all', 'testq %rax,%rax', 'jne .Lfail',
             'xorl %edi,%edi', 'jmp erist_rt_exit', '.Lfail:', 'movl $1,%edi',
             'jmp erist_rt_exit']
    return '\n'.join(code+data)


def allocation_probe():
    code = ['.text', '.globl _start', '_start:', 'xorl %ebp,%ebp',
            'call evn_scope_enter', 'movq %rax,%r12', 'movq %rax,%rdi',
            'leaq .Lkeys(%rip),%rsi', 'leaq .Lclasses(%rip),%rdx',
            'movl $5,%ecx', 'call evn_bind_roots',
            'leaq .Lkept(%rip),%rdi', 'movl $4,%esi', 'call evn_text',
            'movq %rax,.Lkeys(%rip)', 'movq %rax,%rdi', 'call evn_copy',
            'movq %rax,.Lkeys+8(%rip)', 'movl $7,%edi', 'call evn_int',
            'movq %rax,.Lkeys+16(%rip)', 'movl $2,%edi', 'call evn_int',
            'movq %rax,.Lkeys+24(%rip)', 'xorl %edi,%edi', 'call evn_bool',
            'movq %rax,.Lkeys+32(%rip)']
    phases = [
        ('int', ['movl $42,%edi', 'call evn_int'], 1, 42, 1),
        ('bool', ['movl $9,%edi', 'call evn_bool'], 3, 1, 1),
        ('void', ['call evn_void'], 5, 0, 1),
        ('negate', ['xorl %edi,%edi', 'movq .Lkeys+16(%rip),%rsi', 'call evn_unary'], 1, -7, 1),
        ('not', ['movl $1,%edi', 'movq .Lkeys+32(%rip),%rsi', 'call evn_unary'], 3, 1, 1),
        ('int_add', ['xorl %edi,%edi', 'movq .Lkeys+16(%rip),%rsi',
                     'movq .Lkeys+24(%rip),%rdx', 'call evn_binary'], 1, 9, 1),
        ('bool_ne', ['movl $6,%edi', 'movq .Lkeys+32(%rip),%rsi',
                     'movq %rsi,%rdx', 'call evn_binary'], 3, 0, 1),
        ('copy_int', ['movq .Lkeys+16(%rip),%rdi', 'call evn_copy'], 1, 7, 1),
        ('copy_bool', ['movq .Lkeys+32(%rip),%rdi', 'call evn_copy'], 3, 0, 1),
        ('copy_void', ['call evn_void', 'movq %rax,%rdi', 'call evn_copy'], 5, 0, 1),
        ('copy_text', ['movq .Lkeys(%rip),%rdi', 'call evn_copy'], 4, 4, 1),
        ('text_eq', ['movl $5,%edi', 'movq .Lkeys(%rip),%rsi',
                     'movq .Lkeys+8(%rip),%rdx', 'call evn_binary'], 3, 1, 1),
        ('concat', ['xorl %edi,%edi', 'movq .Lkeys(%rip),%rsi',
                    'movq .Lkeys+8(%rip),%rdx', 'call evn_binary'], 4, 8, 2),
    ]
    for name, body, kind, payload, buffers in phases:
        # This temporary must disappear even when the next phase allocates only scalars.
        code += ['leaq .Ldead(%rip),%rdi', 'movl $4,%esi', 'call evn_text',
                 'movl $1200,%r14d', f'.Lphase_{name}:']+body
        code += [f'cmpq ${kind},0(%rax)', 'jne .Lfail', f'cmpq ${payload},8(%rax)',
                 'jne .Lfail', 'decq %r14', f'jne .Lphase_{name}', 'movq %rax,%rbx',
                 'call erist_rt_slots_live', 'cmpq $270,%rax', 'ja .Lfail',
                 'movq %rbx,%rdi', 'call erist_rt_slots_collect', 'call erist_rt_text_collect',
                 'call erist_rt_slots_live', 'cmpq $6,%rax', 'jne .Lfail',
                 'call erist_rt_text_live_buffers', f'cmpq ${buffers},%rax', 'jne .Lfail']
        if kind == 4:
            code += check_text('%rbx', '.Ljoined' if name == 'concat' else '.Lkept',
                               b'A\0\xc3\xa9'*2 if name == 'concat' else b'A\0\xc3\xa9')
    code += ['movq .Lkeys(%rip),%rsi', 'movq %r12,%rdi', 'call evn_scope_leave',
             'movq %rax,%r12', 'movq %rax,%rdi', 'call evn_output',
             'movq $0,.Lvalue_slots(%rip)', 'movq $0,.Lvalue_slot_count(%rip)', 'movq %r12,%rdi', 'call erist_rt_free',
             'testq %rax,%rax', 'jne .Lfail', 'call erist_rt_text_collect',
             'call erist_rt_text_live_buffers', 'testq %rax,%rax', 'jne .Lfail',
             'call erist_rt_allocator_release_all', 'testq %rax,%rax', 'jne .Lfail',
             'xorl %edi,%edi', 'jmp erist_rt_exit', '.Lfail:', 'movl $1,%edi',
             'jmp erist_rt_exit', '.bss', '.p2align 3', '.Lkeys:', '.zero 40',
             '.section .rodata', '.Lclasses:', '.byte 1,1,1,1,1']
    code += byte_data('.Lkept', b'A\0\xc3\xa9')+byte_data('.Ljoined', b'A\0\xc3\xa9'*2)
    code += byte_data('.Ldead', b'dead')
    return '\n'.join(code)


@unittest.skipUnless(platform.system() == 'Linux' and platform.machine().lower() in ('x86_64', 'amd64'),
                     'freestanding Text operators currently target Linux x86-64')
class FreestandingTextOperatorTests(unittest.TestCase):
    def test_operators_overflow_safe_points_and_real_program(self):
        for tool in ('as', 'ld', 'readelf', 'nm'):
            if not shutil.which(tool):
                self.skipTest(f'{tool} unavailable')
        with tempfile.TemporaryDirectory() as td:
            directory = Path(td)
            generator = directory/'runtime'
            self.assertEqual(build_native(ROOT/'src/text_value_runtime.eri', generator, ROOT/'src'), 0)
            emitted = subprocess.run([str(generator)], capture_output=True, text=True, timeout=30)
            self.assertEqual((emitted.returncode, emitted.stderr), (0, ''))
            runtime = emitted.stdout
            for name, assembly, output in [('operators', operator_probe(), b''),
                                           ('allocations', allocation_probe(), b'A\0\xc3\xa9\n')]:
                with self.subTest(name=name):
                    result = lifetime_tests.FreestandingTextLifetimeTests._link_run(
                        self, directory, name, runtime, assembly)
                    self.assertEqual((result.returncode, result.stdout, result.stderr), (0, output, b''))
            for name, a, b in [('size', 9223372036854771712, 1), ('wrap', 18446744073709551615, 1)]:
                overflow = f'''.text
.globl _start
_start:
    xorl %edi,%edi
    leaq .Lhuge(%rip),%rsi
    leaq .Lsuffix(%rip),%rdx
    call evn_binary
    movl $2,%edi
    jmp erist_rt_exit
.section .rodata
.p2align 3
.Lhuge:
.quad 4,{a},0,0
.Lsuffix:
.quad 4,{b},0,0
'''
                result = lifetime_tests.FreestandingTextLifetimeTests._link_run(
                    self, directory, name, runtime, overflow)
                self.assertEqual((result.returncode, result.stdout, result.stderr),
                                 (1, b'', b'Eristavi runtime fault: Text size overflow\n'))
            frontend = directory/'frontend'
            self.assertEqual(build_native(ROOT/'src/frontend.eri', frontend, ROOT/'src'), 0)
            compiled = subprocess.run([str(frontend), 'emit-asm',
                                       str(ROOT/'examples/freestanding_text_operators.eri')],
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
            result = lifetime_tests.FreestandingTextLifetimeTests._link_run(
                self, directory, 'application', runtime, compiled.stdout+startup)
            expected = ('αβ\nα\ntrue\nfalse\n\nx\nx\nA\0B\ntrue\nfalse\nfalse\ntrue\n10000\n').encode()
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, expected, b''))
