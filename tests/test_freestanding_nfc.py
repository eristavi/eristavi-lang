"""Pinned canonical data and exhaustive hosted native NFC qualification."""
from pathlib import Path
import ast
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import tempfile
import unittest
import unicodedata2 as u

from compiler.erist.cli import build_native
import test_freestanding_text_views as view_tests

ROOT = Path(__file__).resolve().parents[1]


def tables():
    text = (ROOT/'src/runtime/unicode_nfc_tables_x86_64.eri').read_text()
    assembly = json.loads(re.search(r'return ("(?:\\.|[^"\\])*");', text).group(1))
    result = {}
    for name in ('ccc', 'decomp', 'compose', 'flat'):
        body = assembly.split('.Lnfc_'+name+':\n', 1)[1].split('.Lnfc_'+name+'_end:', 1)[0]
        rows = [tuple(map(int, x.split(','))) for x in re.findall(r'\.long ([0-9,]+)', body)]
        result[name] = [v for row in rows for v in row] if name == 'flat' else rows
    return result


class FrozenNfcTableTests(unittest.TestCase):
    def test_canonical_data_matches_unicode_17_and_provenance(self):
        self.assertEqual(u.unidata_version, '17.0.0')
        data = tables(); meta = json.loads((ROOT/'UNICODE_NFC_PROVENANCE.json').read_text())
        self.assertEqual(len(data['decomp']), meta['decompositions'])
        self.assertEqual(len(data['compose']), meta['compositions'])
        self.assertEqual(len(data['ccc']), meta['ccc_ranges'])
        self.assertEqual(len(data['flat']), meta['flat_scalars'])
        previous = -1
        for cp, offset, count in data['decomp']:
            self.assertGreater(cp, previous); previous = cp
            self.assertGreater(count, 0); self.assertLessEqual(count, meta['maximum_expansion'])
            self.assertLessEqual(offset+count, len(data['flat']))
            expanded = ''.join(chr(v) for v in data['flat'][offset:offset+count])
            self.assertEqual(u.normalize('NFD', expanded), u.normalize('NFD', chr(cp)))
            for value in data['flat'][offset:offset+count]:
                self.assertFalse(0xd800 <= value <= 0xdfff)
                self.assertEqual(u.normalize('NFD', chr(value)), chr(value))
        for a, b, result in data['compose']:
            self.assertEqual(u.normalize('NFC', chr(a)+chr(b)), chr(result))
        for a, b, cc in data['ccc']:
            for cp in range(a, b+1):
                self.assertEqual(u.combining(chr(cp)), cc)
        source = (ROOT/meta['source']).read_text()
        patterns = {'decompositions': r'static const eri_decomp eri_decompositions\[\]=\{(.*?)\};',
                    'data': r'static const uint32_t eri_decomposition_data\[\]=\{(.*?)\};',
                    'compositions': r'static const eri_comp eri_compositions\[\]=\{(.*?)\};',
                    'ccc': r'static const eri_unicode_range eri_ccc\[\] = \{(.*?)\n\};'}
        for name, pattern in patterns.items():
            raw = re.search(pattern, source, re.S).group(1)
            self.assertEqual(hashlib.sha256(raw.encode()).hexdigest(), meta['source_sha256'][name])


def normalization_vectors():
    data = tables()
    cases = ['', 'A\0B', 'A\u0301\u0327', '\u0308\u0301', 'α\u0313\u0301',
             '\u1100\u1161\u11a8', '\u212b', '\u0344', '👩🏽\u200d💻',
             'a'+('\u0315\u0300\u0327'*40)]
    cases += [chr(cp) for cp, _, _ in data['decomp']]
    cases += [chr(cp) for cp in range(0xac00, 0xd7a4)]
    cases += [chr(a)+chr(b) for a, b, _ in data['compose']]
    # Include fully expanded spellings to exercise composition rather than only
    # decomposition of already precomposed input.
    cases += [''.join(chr(v) for v in data['flat'][offset:offset+count])
              for _, offset, count in data['decomp']]
    rows, strings = [], ['.section .rodata']
    for i, text in enumerate(cases):
        raw = text.encode(); expected = u.normalize('NFC', text).encode()
        for suffix, value in [('input', raw), ('expected', expected)]:
            strings += [f'.Lnfc_case_{i}_{suffix}:', '.byte '+','.join(map(str, value or b'\0'))]
        rows += [f'.quad .Lnfc_case_{i}_input,{len(raw)},.Lnfc_case_{i}_expected,{len(expected)}']
    code = f'''.text
.globl _start
_start:
    xorl %ebp,%ebp
    call evn_scope_enter
    movq %rax,%r15
    movq %rax,%rdi
    leaq .Lnfc_root_dummy(%rip),%rsi
    leaq .Lnfc_class_dummy(%rip),%rdx
    xorl %ecx,%ecx
    call evn_bind_roots
    leaq .Lnfc_cases(%rip),%r12
    movq ${len(cases)},%r13
.Lnfc_case_loop:
    call evn_scope_enter
    movq %rax,%r14
    movq %rax,%rdi
    leaq .Lnfc_root_dummy(%rip),%rsi
    leaq .Lnfc_class_dummy(%rip),%rdx
    xorl %ecx,%ecx
    call evn_bind_roots
    movq 0(%r12),%rdi
    movq 8(%r12),%rsi
    call evn_text
    movq %rax,%rdi
    call erist_rt_unicode_normalize_nfc
    cmpq $4,0(%rax)
    jne .Lnfc_test_fail
    movq 24(%r12),%rcx
    cmpq %rcx,8(%rax)
    jne .Lnfc_test_fail
    movq 16(%rax),%rdi
    movq 16(%r12),%rsi
    cld
    repe cmpsb
    jne .Lnfc_test_fail
    call evn_void
    movq %r14,%rdi
    movq %rax,%rsi
    call evn_scope_leave
    call erist_rt_text_live_buffers
    testq %rax,%rax
    jne .Lnfc_test_fail
    addq $32,%r12
    decq %r13
    jne .Lnfc_case_loop
    call evn_void
    movq %r15,%rdi
    movq %rax,%rsi
    call evn_scope_leave
    call erist_rt_text_collect
    call erist_rt_text_live_buffers
    testq %rax,%rax
    jne .Lnfc_test_fail
    call erist_rt_allocator_release_all
    testq %rax,%rax
    jne .Lnfc_test_fail
    xorl %edi,%edi
    jmp erist_rt_exit
.Lnfc_test_fail:
    movl $1,%edi
    jmp erist_rt_exit
.section .rodata
.p2align 3
.Lnfc_cases:
'''
    code += '\n'.join(rows)+'\n'+ '\n'.join(strings)
    code += '\n.p2align 3\n.globl ev_types\nev_types:\n'
    for kind in range(6):
        code += f'.long {kind},0\n.quad .Lnfc_type_empty,0,0\n'
    code += '.Lnfc_type_empty:\n.byte 0\n.Lnfc_class_dummy:\n.byte 0\n.bss\n.p2align 3\n.Lnfc_root_dummy:\n.quad 0\n'
    return code, len(cases)


@unittest.skipUnless(platform.system() == 'Linux' and platform.machine().lower() in ('x86_64', 'amd64'),
                     'freestanding NFC execution currently targets Linux x86-64')
class FreestandingNfcTests(unittest.TestCase):
    def test_native_nfc_canonical_hangul_snapshots_and_lifetimes(self):
        for tool in ('as', 'ld', 'readelf', 'nm'):
            if not shutil.which(tool):
                self.skipTest(f'{tool} unavailable')
        with tempfile.TemporaryDirectory() as td:
            directory = Path(td)
            generator, frontend = directory/'runtime', directory/'frontend'
            self.assertEqual(build_native(ROOT/'src/text_unicode_runtime.eri', generator, ROOT/'src'), 0)
            self.assertEqual(build_native(ROOT/'src/frontend.eri', frontend, ROOT/'src'), 0)
            emitted = subprocess.run([str(generator)], capture_output=True, text=True, timeout=60)
            self.assertEqual((emitted.returncode, emitted.stderr), (0, ''))

            # Independent boundary accounting catches leaked scratch mappings as
            # well as managed Text leaks; production helpers are unchanged.
            runtime = emitted.stdout.replace('erist_rt_reserve:\n',
                'erist_rt_reserve:\n    addq $1,.Lnfc_test_mappings(%rip)\n')
            runtime = runtime.replace('erist_rt_release:\n',
                'erist_rt_release:\n    subq $1,.Lnfc_test_mappings(%rip)\n')
            runtime = runtime.replace('erist_rt_exit:\n',
                'erist_rt_exit:\n    testq %rdi,%rdi\n    jne .Lnfc_test_exit\n'
                '    cmpq $0,.Lnfc_test_mappings(%rip)\n    je .Lnfc_test_exit\n'
                '    movl $99,%edi\n.Lnfc_test_exit:\n')
            runtime += '\n.bss\n.p2align 3\n.Lnfc_test_mappings:\n.quad 0\n'

            def execute(name, assembly):
                source, obj, binary = (directory/(name+suffix) for suffix in ('.s', '.o', '.bin'))
                source.write_text(runtime+'\n'+assembly+'\n.section .note.GNU-stack,"",@progbits\n')
                subprocess.run(['as', '--64', str(source), '-o', str(obj)], check=True,
                               capture_output=True, timeout=60)
                subprocess.run(['ld', '-nostdlib', '-static', '-e', '_start', str(obj), '-o', str(binary)],
                               check=True, capture_output=True, timeout=30)
                headers = subprocess.check_output(['readelf', '-lW', str(binary)], text=True)
                self.assertNotIn('INTERP', headers); self.assertNotIn('DYNAMIC', headers)
                self.assertNotIn('RWE', next(line for line in headers.splitlines() if 'GNU_STACK' in line))
                self.assertEqual(subprocess.check_output(['nm', '-u', str(binary)], text=True).strip(), '')
                return subprocess.run([str(binary)], env={'PATH': '/unavailable'},
                                      capture_output=True, timeout=60)

            vectors, count = normalization_vectors()
            self.assertGreater(count, 16000)
            result = execute('vectors', vectors)
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b'', b''))
            compiled = subprocess.run([str(frontend), 'emit-asm', str(ROOT/'examples/freestanding_nfc.eri')],
                                      capture_output=True, text=True, timeout=30)
            self.assertEqual((compiled.returncode, compiled.stderr), (0, ''))
            result = execute('application', compiled.stdout+view_tests.STARTUP)
            self.assertEqual((result.returncode, result.stdout, result.stderr),
                             (0, 'true\nfalse\ntrue\n각\nA\0B\ntrue\n'.encode(), b''))
