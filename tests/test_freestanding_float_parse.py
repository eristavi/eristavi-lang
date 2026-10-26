"""Canonical decimal parsing against hosted strtod and exact midpoint vectors."""
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path
import math
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


def value(bits):
    return struct.unpack('<d', struct.pack('<Q', bits))[0]


def corpus():
    result = [f'1e{e}' for e in range(-350, 330)]
    rng = random.Random(0xF1047)
    for _ in range(400):
        number = value(rng.randrange(0x7ff0000000000000))
        result.append(format(number, '.17g'))
    boundaries = [0, 1, 2, 0xfffffffffffff, 0x10000000000000,
                  0x3fefffffffffffff, 0x3ff0000000000000, 0x3ff0000000000001,
                  0x7fefffffffffffff]
    boundaries += [rng.randrange(0x7fefffffffffffff) for _ in range(40)]
    with localcontext() as ctx:
        ctx.prec = 2200
        for lower in boundaries:
            if lower == 0x7fefffffffffffff:
                fraction = Fraction(((1 << 54)-1) << 970)
            else:
                fraction = (Fraction.from_float(value(lower)) +
                            Fraction.from_float(value(lower+1)))/2
            midpoint = Decimal(fraction.numerator)/Decimal(fraction.denominator)
            quantum = Decimal(1).scaleb(-1500)
            result.extend(format(x, 'f') for x in (midpoint-quantum, midpoint, midpoint+quantum))
    result += ['0e'+'9'*1000, '1e'+'9'*1000, '1e-'+'9'*1000,
               '1e18446744073709551615', '1e-18446744073709551615',
               '1e18446744073709551616', '1e-18446744073709551616',
               '0.'+'0'*10000+'1e10001', '1'+'0'*10000+'e-10000',
               '1e'+'0'*1000+'2', '0.0', '1.0', '123.4500', '+1.25E+2']
    return result+['-'+x for x in result if not x.startswith('+')]


INVALID = ['', '+', '-', '.5', '5.', '1..2', '1e', '1e+', '1e-', '1e2x',
           '1_0.0', 'nan', 'inf', '0x1p2', ' 1.0', '1.0 ', '1.e2', '1e1.0',
           '1e'+'9'*1000+'x', '0e'+'9'*1000+'x', '1.'+'0'*1000+'x']
ORACLE = r'''
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <fenv.h>
int main(void) {
    char *line=NULL; size_t cap=0; ssize_t size;
    if(fesetround(FE_TONEAREST)) return 2;
    while((size=getline(&line,&cap,stdin))>=0) {
        if(size && line[size-1]=='\n') line[--size]=0;
        char *end; double x=strtod(line,&end); uint64_t words[2]={0,0};
        if(end==line||*end) return 3;
        memcpy(words,&x,8);
        if(fwrite(words,8,2,stdout)!=2) return 4;
    }
    free(line); return ferror(stdin)?5:0;
}
'''
PROBE = r'''
.text
.globl _start
_start:
    xorl %ebp,%ebp
    xorl %r12d,%r12d
.Lparse_read:
    xorl %edi,%edi
    leaq .Lparse_input(%rip),%rsi
    addq %r12,%rsi
    movl $1,%edx
    xorl %eax,%eax
    syscall
    cmpq $-4,%rax
    je .Lparse_read
    testq %rax,%rax
    js .Lparse_fail
    je .Lparse_eof
    cmpb $10,(%rsi)
    je .Lparse_call
    incq %r12
    cmpq $32767,%r12
    jae .Lparse_fail
    jmp .Lparse_read
.Lparse_call:
    movb $0,(%rsi)
    ldmxcsr .Lparse_hostile(%rip)
    leaq .Lparse_input(%rip),%rdi
    call erist_rt_float_parse
    movq %rax,.Lparse_output(%rip)
    movq %rdx,.Lparse_output+8(%rip)
    stmxcsr .Lparse_actual(%rip)
    cmpl $0xffc0,.Lparse_actual(%rip)
    jne .Lparse_fail
    movl $1,%edi
    leaq .Lparse_output(%rip),%rsi
    movl $16,%edx
    call erist_rt_write_all
    testq %rax,%rax
    jne .Lparse_fail
    xorl %r12d,%r12d
    jmp .Lparse_read
.Lparse_eof:
    testq %r12,%r12
    jne .Lparse_fail
    xorl %edi,%edi
    jmp erist_rt_exit
.Lparse_fail:
    movl $1,%edi
    jmp erist_rt_exit
.bss
.p2align 3
.Lparse_input:
.zero 32768
.Lparse_output:
.zero 16
.Lparse_actual:
.zero 4
.section .rodata
.Lparse_hostile:
.long 0xffc0
'''


@unittest.skipUnless(platform.system() == 'Linux' and platform.machine().lower() in ('x86_64','amd64'),
                     'owned Float parsing currently targets Linux x86-64')
class FreestandingFloatParseTests(unittest.TestCase):
    def test_exact_midpoints_long_inputs_and_malformed_canonical_spellings(self):
        cc = os.environ.get('CC','cc')
        for tool in (cc,'as','ld','nm','readelf'):
            if not shutil.which(tool):
                self.skipTest(f'{tool} unavailable')
        valid = corpus()
        payload = ('\n'.join(valid)+'\n').encode()
        with tempfile.TemporaryDirectory() as td:
            directory=Path(td); oracle=directory/'oracle'; c=directory/'oracle.c'
            c.write_text(ORACLE)
            subprocess.run([cc,'-std=c11','-O2',str(c),'-lm','-o',str(oracle)],
                           check=True,capture_output=True,timeout=30)
            reference=subprocess.run([str(oracle)],input=payload,capture_output=True,timeout=30)
            self.assertEqual((reference.returncode,reference.stderr),(0,b''))
            generator=directory/'generator'
            self.assertEqual(build_native(ROOT/'src/float_parse_runtime.eri',generator,ROOT/'src'),0)
            emitted=subprocess.run([str(generator)],capture_output=True,text=True,timeout=60)
            self.assertEqual((emitted.returncode,emitted.stderr),(0,''))
            source=directory/'parse.s'; obj=directory/'parse.o'; binary=directory/'parse'
            source.write_text(emitted.stdout+PROBE+'\n.section .note.GNU-stack,"",@progbits\n')
            subprocess.run(['as','--64',str(source),'-o',str(obj)],check=True,capture_output=True,timeout=20)
            subprocess.run(['ld','-nostdlib','-static','-e','_start',str(obj),'-o',str(binary)],
                           check=True,capture_output=True,timeout=20)
            headers=subprocess.check_output(['readelf','-lW',str(binary)],text=True)
            self.assertNotIn('INTERP',headers); self.assertNotIn('DYNAMIC',headers)
            self.assertNotIn('RWE',next(x for x in headers.splitlines() if 'GNU_STACK' in x))
            self.assertEqual(subprocess.check_output(['nm','-u',str(binary)],text=True).strip(),'')
            all_input=payload+('\n'.join(INVALID)+'\n').encode()
            result=subprocess.run([str(binary)],input=all_input,capture_output=True,
                                  env={'PATH':'/unavailable'},timeout=30)
            self.assertEqual((result.returncode,result.stderr),(0,b''))
            expected=reference.stdout+b''.join(struct.pack('<QQ',0,1) for _ in INVALID)
            self.assertEqual(len(result.stdout),len(expected))
            for i,text in enumerate(valid+INVALID):
                a,b=expected[i*16:i*16+16],result.stdout[i*16:i*16+16]
                if a!=b:
                    self.fail(f'{text[:90]!r}: expected {struct.unpack("<QQ",a)}, got {struct.unpack("<QQ",b)}')
