"""Exact binary64 decimal output against the existing hosted printf contract."""
from pathlib import Path
import os
import platform
import random
import shutil
import struct
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native

ROOT = Path(__file__).resolve().parents[1]


def corpus():
    values = set()
    # Every finite exponent at difficult significand boundaries, both signs.
    for exponent in range(2047):
        for fraction in (0, 1, (1 << 51), (1 << 52)-2, (1 << 52)-1):
            values.add((exponent << 52) | fraction)
    # Decimal notation and rounding boundaries, including neighboring binary64s.
    for exponent in range(-324, 309):
        number = float(f'1e{exponent}')
        raw = struct.unpack('<Q', struct.pack('<d', number))[0]
        values.update(x for x in (raw-1, raw, raw+1) if 0 <= x < 0x7ff0000000000000)
    # Exact decimal halfway cases: both even and odd last retained digits, and carry.
    for value in (1.2345678901234566, 1.2345678901234568, 9999999999999999.0,
                  99999999999999984.0, 99999999999999992.0, 1.0/128, 1.0/1024,
                  131073.0/131072.0, 131075.0/131072.0):
        values.add(struct.unpack('<Q', struct.pack('<d', value))[0])
    rng = random.Random(0xDEC1A1)
    values.update(rng.getrandbits(63) for _ in range(2048))
    values.update((0x7ff0000000000000, 0x7ff0000000000001,
                   0x7ff8000000000000, 0x7fffffffffffffff))
    return sorted(values | {x | (1 << 63) for x in values})


ORACLE = r'''
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <fenv.h>
int main(void) {
    uint64_t bits;
    if (fesetround(FE_TONEAREST)) return 2;
    while (fread(&bits, sizeof(bits), 1, stdin) == 1) {
        double value;
        memcpy(&value, &bits, sizeof(value));
        if (printf("%.17g\n", value) < 0) return 3;
    }
    return ferror(stdin) ? 4 : 0;
}
'''


PROBE = r'''
.text
.globl _start
_start:
    xorl %ebp,%ebp
    xorl %r12d,%r12d
.Lformat_read:
    xorl %edi,%edi
    leaq .Lformat_input(%rip),%rsi
    addq %r12,%rsi
    movl $8,%edx
    subq %r12,%rdx
    xorl %eax,%eax
    syscall
    cmpq $-4,%rax
    je .Lformat_read
    testq %rax,%rax
    js .Lformat_fail
    je .Lformat_eof
    addq %rax,%r12
    cmpq $8,%r12
    jb .Lformat_read
    # Formatting must not inspect/change floating environment or touch guards.
    ldmxcsr .Lformat_hostile(%rip)
    leaq .Lformat_output(%rip),%rsi
    movq .Lformat_input(%rip),%rdi
    call erist_rt_float_format
    testq %rdx,%rdx
    jne .Lformat_fail
    testq %rax,%rax
    je .Lformat_fail
    cmpq $24,%rax
    ja .Lformat_fail
    movq %rax,%r13
    stmxcsr .Lformat_actual(%rip)
    cmpl $0xffc0,.Lformat_actual(%rip)
    jne .Lformat_fail
    movabsq $0x13579bdf2468ace0,%rcx
    cmpq .Lformat_before(%rip),%rcx
    jne .Lformat_fail
    cmpq .Lformat_after(%rip),%rcx
    jne .Lformat_fail
    # The unused portion of the 32-byte caller buffer must remain untouched.
    leaq .Lformat_output(%rip),%rsi
    movq %r13,%rcx
.Lformat_tail_check:
    cmpb $0xcc,(%rsi,%rcx)
    jne .Lformat_fail
    incq %rcx
    cmpq $32,%rcx
    jb .Lformat_tail_check
    movq %r13,%rdx
    movl $1,%edi
    call erist_rt_write_all
    testq %rax,%rax
    jne .Lformat_fail
    movl $1,%edi
    leaq .Lformat_newline(%rip),%rsi
    movl $1,%edx
    call erist_rt_write_all
    testq %rax,%rax
    jne .Lformat_fail
    # Reset only the caller buffer between cases, not formatter stack memory.
    leaq .Lformat_output(%rip),%rdi
    movl $32,%ecx
    movl $0xcc,%eax
    cld
    rep stosb
    xorl %r12d,%r12d
    jmp .Lformat_read
.Lformat_eof:
    testq %r12,%r12
    jne .Lformat_fail
    xorl %edi,%edi
    jmp erist_rt_exit
.Lformat_fail:
    movl $1,%edi
    jmp erist_rt_exit
.bss
.p2align 3
.Lformat_input:
.zero 8
.Lformat_actual:
.zero 4
.data
.p2align 3
.Lformat_before:
.quad 0x13579bdf2468ace0
.Lformat_output:
.fill 32,1,0xcc
.Lformat_after:
.quad 0x13579bdf2468ace0
.section .rodata
.Lformat_hostile:
.long 0xffc0
.Lformat_newline:
.byte 10
'''


@unittest.skipUnless(platform.system() == 'Linux' and platform.machine().lower() in ('x86_64', 'amd64'),
                     'owned Float formatting currently targets Linux x86-64')
class FreestandingFloatFormatTests(unittest.TestCase):
    def test_binary64_output_matches_existing_runtime_without_host_float_dependencies(self):
        cc = os.environ.get('CC', 'cc')
        for tool in (cc, 'as', 'ld', 'readelf', 'nm'):
            if not shutil.which(tool):
                self.skipTest(f'{tool} unavailable')
        values = corpus()
        payload = b''.join(struct.pack('<Q', value) for value in values)
        with tempfile.TemporaryDirectory() as td:
            directory = Path(td)
            oracle_source, oracle = directory/'oracle.c', directory/'oracle'
            oracle_source.write_text(ORACLE)
            subprocess.run([cc, '-std=c11', '-O2', str(oracle_source), '-lm', '-o', str(oracle)],
                           check=True, capture_output=True, timeout=30)
            reference = subprocess.run([str(oracle)], input=payload, capture_output=True, timeout=30)
            self.assertEqual((reference.returncode, reference.stderr), (0, b''))
            generator = directory/'generator'
            self.assertEqual(build_native(ROOT/'src/float_decimal_runtime.eri', generator, ROOT/'src'), 0)
            emitted = subprocess.run([str(generator)], capture_output=True, text=True, timeout=60)
            self.assertEqual((emitted.returncode, emitted.stderr), (0, ''))
            source, obj, binary = directory/'format.s', directory/'format.o', directory/'format'
            source.write_text(emitted.stdout+PROBE+'\n.section .note.GNU-stack,"",@progbits\n')
            subprocess.run(['as', '--64', str(source), '-o', str(obj)], check=True,
                           capture_output=True, timeout=20)
            subprocess.run(['ld', '-nostdlib', '-static', '-e', '_start', str(obj), '-o', str(binary)],
                           check=True, capture_output=True, timeout=20)
            headers = subprocess.check_output(['readelf', '-lW', str(binary)], text=True)
            self.assertNotIn('INTERP', headers)
            self.assertNotIn('DYNAMIC', headers)
            self.assertNotIn('RWE', next(line for line in headers.splitlines() if 'GNU_STACK' in line))
            self.assertEqual(subprocess.check_output(['nm', '-u', str(binary)], text=True).strip(), '')
            result = subprocess.run([str(binary)], input=payload, env={'PATH': '/unavailable'},
                                    capture_output=True, timeout=30)
            self.assertEqual((result.returncode, result.stderr), (0, b''))
            expected, actual = reference.stdout.splitlines(), result.stdout.splitlines()
            self.assertEqual(len(actual), len(values))
            for value, wanted, got in zip(values, expected, actual):
                if wanted != got:
                    self.fail(f'binary64 0x{value:016x}: expected {wanted!r}, got {got!r}')
