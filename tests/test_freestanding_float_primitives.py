"""Strict binary64 machine operations, independent of decimal conversion."""
from pathlib import Path
import math
import platform
import random
import shutil
import struct
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native
import test_freestanding_text_lifetimes as lifetime_tests

ROOT = Path(__file__).resolve().parents[1]
MASK = (1 << 64)-1


def bits(value):
    return struct.unpack('<Q', struct.pack('<d', value))[0]


def vectors():
    rows = []

    def case(op, a, b, expected, mask=MASK, status=0):
        rows.append((op, a, b, expected, mask, status))

    one = bits(1.0)
    # Halfway rounding in both directions, overflow, gradual underflow, signed zero.
    case(0, one, bits(2.0**-53), one)
    case(0, one+1, bits(2.0**-53), one+2)
    case(0, 1, 1, 2)
    case(2, bits(2.0**-1022), bits(0.5), 1 << 51)
    case(3, 1, bits(2.0), 0)
    case(3, 3, bits(2.0), 2)
    case(2, 0x7fefffffffffffff, bits(2.0), bits(math.inf))
    case(3, one, 0, bits(math.inf))
    case(3, bits(-1.0), 0, bits(-math.inf))
    case(3, 0, 0, 0x7ff8000000000000, 0x7ff8000000000000)
    case(0, bits(-0.0), bits(-0.0), bits(-0.0))
    case(1, bits(-0.0), 0, bits(-0.0))
    # Every comparison against NaN, including signaling NaN, is unordered.
    for a in (0x7ff8000000000123, 0x7ff0000000000001, 0xfff8000000000123):
        for b in (one, 0, bits(math.inf), a):
            for op in range(5, 11):
                case(op, a, b, int(op == 6))
                case(op, b, a, int(op == 6))
    values = [0.0, -0.0, 1.0, -1.0, math.inf, -math.inf, 2.0**-1074]
    comparisons = [lambda a,b: a == b, lambda a,b: a != b, lambda a,b: a < b,
                   lambda a,b: a <= b, lambda a,b: a > b, lambda a,b: a >= b]
    for a in values:
        for b in values:
            for op, predicate in enumerate(comparisons, 5):
                case(op, bits(a), bits(b), int(predicate(a, b)))
    # Independently evaluate a fixed finite random corpus in hosted binary64.
    rng = random.Random(0xE7157)
    for _ in range(256):
        a = math.ldexp(rng.uniform(-1, 1), rng.randrange(-500, 501))
        b = math.ldexp(rng.uniform(-1, 1), rng.randrange(-500, 501))
        for op, value in enumerate((a+b, a-b, a*b, a/b)):
            case(op, bits(a), bits(b), bits(value))
    case(4, one, one, 0, status=1)  # Float % is deliberately undefined.
    case(11, one, one, 0, status=1)
    case(MASK, one, one, 0, status=1)
    return rows


@unittest.skipUnless(platform.system() == 'Linux' and platform.machine().lower() in ('x86_64', 'amd64'),
                     'freestanding Float primitives currently target Linux x86-64')
class FreestandingFloatPrimitiveTests(unittest.TestCase):
    def test_ieee_operations_with_hostile_rounding_and_denormal_modes(self):
        for tool in ('as', 'ld', 'readelf', 'nm'):
            if not shutil.which(tool):
                self.skipTest(f'{tool} unavailable')
        with tempfile.TemporaryDirectory() as td:
            directory = Path(td)
            generator = directory/'runtime'
            self.assertEqual(build_native(ROOT/'src/float_runtime_primitives.eri', generator, ROOT/'src'), 0)
            emitted = subprocess.run([str(generator)], capture_output=True, text=True, timeout=60)
            self.assertEqual((emitted.returncode, emitted.stderr), (0, ''))
            code = r'''
.text
.globl _start
_start:
    xorl %ebp,%ebp
    leaq .Lfloat_vectors(%rip),%r12
    leaq .Lfloat_vectors_end(%rip),%r13
.Lfloat_vector_loop:
    # Deliberately enable truncation, FTZ and DAZ in the caller's environment.
    ldmxcsr .Lfloat_hostile(%rip)
    movq 0(%r12),%rdi
    movq 8(%r12),%rsi
    movq 16(%r12),%rdx
    call erist_rt_float_binary
    cmpq 40(%r12),%rdx
    jne .Lfloat_test_fail
    andq 32(%r12),%rax
    cmpq 24(%r12),%rax
    jne .Lfloat_test_fail
    stmxcsr .Lfloat_actual(%rip)
    cmpl $0xffc0,.Lfloat_actual(%rip)
    jne .Lfloat_test_fail
    addq $48,%r12
    cmpq %r13,%r12
    jb .Lfloat_vector_loop
    # Negation preserves a signaling NaN's bits except its sign, as C - does.
    movabsq $0x7ff0000000000123,%rdi
    call erist_rt_float_negate
    movabsq $0xfff0000000000123,%rcx
    cmpq %rcx,%rax
    jne .Lfloat_test_fail
    xorl %edi,%edi
    call erist_rt_float_negate
    movabsq $0x8000000000000000,%rcx
    cmpq %rcx,%rax
    jne .Lfloat_test_fail
    xorl %edi,%edi
    jmp erist_rt_exit
.Lfloat_test_fail:
    movl $1,%edi
    jmp erist_rt_exit
.bss
.p2align 2
.Lfloat_actual:
.zero 4
.section .rodata
.p2align 2
.Lfloat_hostile:
.long 0xffc0
.p2align 3
.Lfloat_vectors:
'''
            code += '\n'.join('.quad '+','.join(f'0x{x:x}' for x in row) for row in vectors())
            code += '\n.Lfloat_vectors_end:\n'
            result = lifetime_tests.FreestandingTextLifetimeTests._link_run(
                self, directory, 'float-primitives', emitted.stdout, code)
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b'', b''))
