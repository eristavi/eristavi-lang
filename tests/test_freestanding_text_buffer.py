"""Hosted qualification of the private UTF-8/storage foundation, not managed Text."""
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(platform.system() == 'Linux' and platform.machine().lower() in ('x86_64', 'amd64'),
                     'freestanding Text storage currently targets Linux x86-64')
class FreestandingTextBufferTests(unittest.TestCase):
    def test_utf8_storage_boundaries_and_release(self):
        for tool in ('as', 'ld', 'readelf', 'nm'):
            if not shutil.which(tool):
                self.skipTest(f'{tool} unavailable')
        valid = [b'', b'A\0B', 'Привет — Γεια σου'.encode(),
                 'e\u0301 👨\u200d👩\u200d👦'.encode(), b'x' * 4097]
        valid += [chr(cp).encode() for cp in (0x7f, 0x80, 0x7ff, 0x800, 0xd7ff,
                                              0xe000, 0xffff, 0x10000, 0x10ffff)]
        invalid = [b'\x80', b'\xbf', b'\xc0\x80', b'\xc1\xbf', b'\xc2',
                   b'\xc2A', b'\xe0\x9f\xbf', b'\xed\xa0\x80',
                   b'\xe1\x80', b'\xe1A\x80', b'\xe1\x80A',
                   b'\xf0\x8f\xbf\xbf', b'\xf4\x90\x80\x80',
                   b'\xf5\x80\x80\x80', b'\xff', b'\xf0\x90\x80',
                   b'\xf0\x90A\x80', b'\xf0\x90\x80A']
        body = ['.text', '.globl _start', '_start:', 'xorl %ebp,%ebp']
        data = ['.data']
        for index, raw in enumerate(valid + invalid):
            label = f'.Ltext_input_{index}'
            data += [label + ':', '.byte ' + ','.join(map(str, raw or b'\0'))]
            accepted = index < len(valid)
            # Python's strict UTF-8 decoder is an independent encoding oracle;
            # grapheme segmentation and normalization are intentionally not involved.
            try:
                raw.decode('utf-8')
                oracle = True
            except UnicodeDecodeError:
                oracle = False
            self.assertEqual(oracle, accepted)
            body += [f'leaq {label}(%rip),%rdi', f'movq ${len(raw)},%rsi',
                     'call erist_rt_utf8_valid', f'cmpq ${int(accepted)},%rax', 'jne .Lfail',
                     f'leaq {label}(%rip),%rdi', f'movq ${len(raw)},%rsi',
                     'call erist_rt_text_buffer_copy']
            if not accepted:
                body += ['cmpq $1,%rcx', 'jne .Lfail', 'orq %rdx,%rax', 'jne .Lfail']
                continue
            body += ['testq %rcx,%rcx', 'jne .Lfail']
            if not raw:
                body += ['orq %rdx,%rax', 'jne .Lfail']
                continue
            body += ['movq %rax,%r12', 'movq %rdx,%r13',
                     f'cmpq ${((len(raw)+4095)//4096)*4096},%r13', 'jne .Lfail',
                     f'leaq {label}(%rip),%rsi', 'cmpq %rsi,%r12', 'je .Lfail',
                     'movq %r12,%rdi', f'movq ${len(raw)},%rcx', 'cld', 'repe cmpsb',
                     'jne .Lfail',
                     # Mutating the source must not change the owned snapshot.
                     f'xorb $255,{label}(%rip)', 'movq %r12,%rdi', 'movq %r13,%rsi',
                     'xorl %edx,%edx', 'call erist_rt_text_load8', 'testq %rdx,%rdx',
                     'jne .Lfail', f'cmpq ${raw[0]},%rax', 'jne .Lfail',
                     # Out-of-reservation access must be rejected before dereference.
                     'movq %r12,%rdi', 'movq %r13,%rsi', 'movq %r13,%rdx',
                     'movl $7,%ecx', 'call erist_rt_text_store8', 'cmpq $1,%rdx',
                     'jne .Lfail', 'movq %r12,%rdi', 'movq %r13,%rsi',
                     'movq %r13,%rdx', 'call erist_rt_text_load8', 'cmpq $1,%rdx',
                     'jne .Lfail', 'movq %r12,%rdi', 'movq %r13,%rsi',
                     'call erist_rt_release', 'testq %rax,%rax', 'jne .Lfail']
        body += ['xorl %edi,%edi', 'movl $1,%esi', 'call erist_rt_text_buffer_copy',
                 'cmpq $1,%rcx', 'jne .Lfail', 'orq %rdx,%rax', 'jne .Lfail',
                 # Oversize rejection precedes even reading a bogus non-null input.
                 'movl $1,%edi', 'movabsq $9223372036854771713,%rsi',
                 'call erist_rt_text_buffer_copy', 'cmpq $2,%rcx', 'jne .Lfail',
                 'orq %rdx,%rax', 'jne .Lfail',
                 # A truncated UTF-8 sequence ends at an actual inaccessible page.
                 'movl $8192,%edi', 'call erist_rt_reserve', 'testq %rax,%rax',
                 'je .Lfail', 'movq %rax,%r12', 'movq %rdx,%r13',
                 'movb $240,4093(%r12)', 'movb $144,4094(%r12)',
                 'movb $128,4095(%r12)', 'leaq 4096(%r12),%rdi',
                 'movl $4096,%esi', 'xorl %edx,%edx', 'movl $10,%eax', 'syscall',
                 'testq %rax,%rax', 'jne .Lfail', 'leaq 4093(%r12),%rdi',
                 'movl $3,%esi', 'call erist_rt_text_buffer_copy', 'cmpq $1,%rcx',
                 'jne .Lfail', 'orq %rdx,%rax', 'jne .Lfail',
                 'movq %r12,%rdi', 'movq %r13,%rsi', 'call erist_rt_release',
                 'testq %rax,%rax', 'jne .Lfail', 'xorl %edi,%edi', 'jmp erist_rt_exit',
                 '.Lfail:', 'movl $1,%edi', 'jmp erist_rt_exit']
        with tempfile.TemporaryDirectory() as td:
            directory = Path(td)
            generator = directory / 'text-generator'
            self.assertEqual(build_native(ROOT/'src/text_buffer_runtime.eri', generator, ROOT/'src'), 0)
            emitted = subprocess.run([str(generator)], capture_output=True, text=True, timeout=30)
            self.assertEqual((emitted.returncode, emitted.stderr), (0, ''))
            self.assertIn('movb %cl, (%rax)', emitted.stdout)
            assembly = directory/'text.s'
            assembly.write_text(emitted.stdout + '\n' + '\n'.join(body + data) +
                                '\n.section .note.GNU-stack,"",@progbits\n')
            obj, binary = directory/'text.o', directory/'text'
            subprocess.run(['as', '--64', str(assembly), '-o', str(obj)], check=True,
                           capture_output=True, timeout=20)
            subprocess.run(['ld', '-nostdlib', '-static', '-e', '_start', str(obj), '-o', str(binary)],
                           check=True, capture_output=True, timeout=20)
            headers = subprocess.check_output(['readelf', '-lW', str(binary)], text=True)
            self.assertNotIn('INTERP', headers)
            self.assertNotIn('DYNAMIC', headers)
            self.assertNotIn('RWE', next(line for line in headers.splitlines() if 'GNU_STACK' in line))
            self.assertEqual(subprocess.check_output(['nm', '-u', str(binary)], text=True).strip(), '')
            result = subprocess.run([str(binary)], env={'PATH': '/unavailable'},
                                    capture_output=True, timeout=20)
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b'', b''))
