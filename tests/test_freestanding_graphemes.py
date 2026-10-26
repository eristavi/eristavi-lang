"""Pinned-data and hosted native Unicode/grapheme qualification."""
from pathlib import Path
import bisect
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native
from compiler.erist.unicode_asm import _rows, GCB_PROPERTIES
from compiler.erist.unicode_c import _property_ranges
from compiler.erist.unicode_support import grapheme_clusters
import test_freestanding_text_lifetimes as lifetime_tests
import test_freestanding_text_views as view_tests

ROOT = Path(__file__).resolve().parents[1]


def canonical_tables():
    return {'gcb': _rows(GCB_PROPERTIES),
            'incb': _rows((('InCB=Consonant', 1), ('InCB=Extend', 2), ('InCB=Linker', 3))),
            'ep': [(a, b, 1) for a, b in _property_ranges('Extended_Pictographic')],
            'xid_start': [(a, b, 1) for a, b in _property_ranges('XID_Start')],
            'xid_continue': [(a, b, 1) for a, b in _property_ranges('XID_Continue')]}


class FrozenUnicodeTableTests(unittest.TestCase):
    def test_owned_tables_match_pinned_unicode_and_source_provenance(self):
        source = (ROOT/'src/runtime/unicode_tables_x86_64.eri').read_text()
        assembly = json.loads(re.search(r'return ("(?:\\.|[^"\\])*");', source).group(1))
        metadata = json.loads((ROOT/'UNICODE_TABLE_PROVENANCE.json').read_text())
        self.assertEqual(metadata['unicode_version'], '17.0.0')
        original = (ROOT/metadata['source']).read_text()
        for name, expected in canonical_tables().items():
            label = '.Lunicode_'+name if name.startswith('xid') else '.Lgrapheme_'+name
            body = assembly.split(label+':\n', 1)[1].split(label+'_end:', 1)[0]
            actual = [tuple(map(int, row.split(','))) for row in re.findall(r'\.long ([0-9,]+)', body)]
            self.assertEqual(actual, expected, name)
            self.assertEqual(len(actual), metadata['rows'][name])
            table_name = 'eri_'+name if name.startswith('xid') else 'eri_'+name+'_table'
            chunk = re.search(r'static const eri_unicode_range '+table_name+r'\[\] = \{(.*?)\n\};',
                              original, re.S).group(1)
            self.assertEqual(hashlib.sha256(chunk.encode()).hexdigest(),
                             metadata['source_table_sha256'][name])


def native_vectors(test):
    samples = ['', '\r\n', '\0\u0301', '\u1100\u1161\u11a8', '🇨🇾🇧🇪🇬',
               'A\u0301', '👩🏽\u200d💻', '👨\u200d👩\u200d👦', 'क्\u200dष', '\u0600A']
    vectors = [(s, grapheme_clusters(s)) for s in samples]
    fixture = os.environ.get('ERISTAVI_GRAPHEME_BREAK_TEST')
    if fixture:
        lines = Path(fixture).read_text().splitlines()
        test.assertIn('GraphemeBreakTest-17.0.0', lines[0])
        official = 0
        for line in lines:
            body = line.split('#', 1)[0].strip()
            if not body:
                continue
            clusters, current = [], []
            for token in body.split():
                if token == '÷':
                    if current:
                        clusters.append(''.join(current)); current = []
                elif token != '×':
                    current.append(chr(int(token, 16)))
            if current:
                clusters.append(''.join(current))
            vectors.append((''.join(clusters), clusters)); official += 1
        test.assertGreater(official, 500)
    code = ['.text', '.globl _start', '_start:', 'xorl %ebp,%ebp']
    data = ['.section .rodata']
    for i, (text, clusters) in enumerate(vectors):
        raw = text.encode(); label = f'.Lvector_{i}'
        data += [label+':', '.byte '+','.join(map(str, raw or b'\0'))]
        code += [f'leaq {label}(%rip),%rdi', f'movq ${len(raw)},%rsi', 'movq $-1,%rdx',
                 'call erist_rt_grapheme_scan', 'testq %rcx,%rcx', 'jne .Lfail',
                 f'cmpq ${len(clusters)},%rax', 'jne .Lfail']
        offset = 0
        for j, cluster in enumerate(clusters):
            size = len(cluster.encode())
            code += [f'leaq {label}(%rip),%rdi', f'movq ${len(raw)},%rsi', f'movq ${j},%rdx',
                     'call erist_rt_grapheme_scan', 'testq %rcx,%rcx', 'jne .Lfail',
                     f'cmpq ${offset},%rax', 'jne .Lfail', f'cmpq ${size},%rdx', 'jne .Lfail']
            offset += size
        code += [f'leaq {label}(%rip),%rdi', f'movq ${len(raw)},%rsi',
                 f'movq ${len(clusters)},%rdx', 'call erist_rt_grapheme_scan',
                 'cmpq $1,%rcx', 'jne .Lfail']
    # Exercise every property-range boundary through the actual native binary search.
    for name, rows in canonical_tables().items():
        label = '.Lunicode_'+name if name.startswith('xid') else '.Lgrapheme_'+name
        points = sorted({0, 0x10ffff} | {p for a, b, _ in rows for p in (a-1, a, b, b+1) if p >= 0})
        firsts = [a for a, _, _ in rows]
        values = []
        for cp in points:
            index = bisect.bisect_right(firsts, cp)-1
            value = rows[index][2] if index >= 0 and cp <= rows[index][1] else 0
            values.append((cp, value))
        data += [f'.Llookup_{name}:'] + [f'.long {cp},{value}' for cp, value in values]
        code += [f'leaq {label}(%rip),%r12', f'leaq .Llookup_{name}(%rip),%r13',
                 f'movq ${len(values)},%r14', f'.Llookup_loop_{name}:',
                 'movl 0(%r13),%edi', 'movq %r12,%rsi', f'movl ${len(rows)},%edx',
                 'call erist_rt_unicode_lookup', 'cmpl 4(%r13),%eax', 'jne .Lfail',
                 'addq $8,%r13', 'decq %r14', f'jne .Llookup_loop_{name}']
    code += ['xorl %edi,%edi', 'jmp erist_rt_exit', '.Lfail:', 'movl $1,%edi', 'jmp erist_rt_exit']
    # The scanner harness supplies the ordinary six baseline descriptors; production
    # applications receive their descriptor table from the Eristavi compiler.
    data += ['.p2align 3', '.globl ev_types', 'ev_types:']
    for kind in range(6):
        data += [f'.long {kind},0', '.quad .Lempty_type_name,0,0']
    data += ['.Lempty_type_name:', '.byte 0']
    return '\n'.join(code+data)


@unittest.skipUnless(platform.system() == 'Linux' and platform.machine().lower() in ('x86_64', 'amd64'),
                     'freestanding Unicode execution currently targets Linux x86-64')
class FreestandingGraphemeTests(unittest.TestCase):
    def test_native_conformance_views_and_unicode_primitives(self):
        for tool in ('as', 'ld', 'readelf', 'nm'):
            if not shutil.which(tool):
                self.skipTest(f'{tool} unavailable')
        with tempfile.TemporaryDirectory() as td:
            directory = Path(td)
            generator, frontend = directory/'runtime', directory/'frontend'
            self.assertEqual(build_native(ROOT/'src/text_view_runtime.eri', generator, ROOT/'src'), 0)
            self.assertEqual(build_native(ROOT/'src/frontend.eri', frontend, ROOT/'src'), 0)
            emitted = subprocess.run([str(generator)], capture_output=True, text=True, timeout=60)
            self.assertEqual((emitted.returncode, emitted.stderr), (0, ''))
            runtime = emitted.stdout
            result = lifetime_tests.FreestandingTextLifetimeTests._link_run(
                self, directory, 'vectors', runtime, native_vectors(self))
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b'', b''))

            def execute(name, source):
                path = directory/(name+'.eri'); path.write_text(source)
                compiled = subprocess.run([str(frontend), 'emit-asm', str(path)],
                                          capture_output=True, text=True, timeout=30)
                self.assertEqual((compiled.returncode, compiled.stderr), (0, ''))
                return lifetime_tests.FreestandingTextLifetimeTests._link_run(
                    self, directory, name, runtime, compiled.stdout+view_tests.STARTUP)

            program = (ROOT/'examples/freestanding_graphemes.eri').read_text()
            result = execute('application', program)
            expected = '2\nÁ\n👩🏽\u200d💻\n2\n🇨🇾\n0\n😀\ntrue\ntrue\ntrue\nfalse\ntrue\nfalse\ntrue\nfalse\nfalse\n'.encode()
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, expected, b''))
            for value in (-1, 0xd800, 0xdfff, 0x110000):
                result = execute('invalid_scalar_'+str(value).replace('-', 'neg'),
                                 f'import std.unicode; output(unicode.fromScalar({value}));')
                self.assertEqual((result.returncode, result.stdout, result.stderr),
                                 (1, b'', b'Eristavi runtime fault: invalid Unicode scalar value\n'))
            valid_scalars = [0, 0x7f, 0x80, 0x7ff, 0x800, 0xd7ff, 0xe000, 0xffff, 0x10000, 0x10ffff]
            source = 'import std.unicode;\n'+'\n'.join(
                f'output(unicode.fromScalar({cp})=="\\u{{{cp:X}}}");' for cp in valid_scalars)
            result = execute('scalar_boundaries', source)
            self.assertEqual((result.returncode, result.stdout, result.stderr),
                             (0, b'true\n'*len(valid_scalars), b''))
            for name, expr in [('negative', '"A".characters[-1]'), ('end', '"Á".characters[1]'),
                               ('empty', '"".characters[0]')]:
                result = execute('bounds_'+name, 'output('+expr+');')
                self.assertEqual((result.returncode, result.stdout, result.stderr),
                                 (1, b'', b'Eristavi runtime fault: Text view index out of bounds\n'))
