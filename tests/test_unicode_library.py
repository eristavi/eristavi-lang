from __future__ import annotations

import ctypes
import os
import random
import shlex
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import unicodedata2
from compiler.erist.c_backend_views import VIEW_RUNTIME
from compiler.erist.unicode_library_c import unicode_library_c
from compiler.erist.unicode_c import _property_ranges
from compiler.erist.unicode_support import is_xid_start, is_xid_continue
from compiler.erist.cli import analyze_frontend
from compiler.erist.diagnostics import SemanticError, RuntimeFault
from compiler.erist.runtime_ext import Interpreter


class UnicodeLibraryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cc = os.environ.get('CC', 'cc')
        if not shutil.which(cc):
            raise unittest.SkipTest('C compiler required for compiled Unicode conformance')
        cls.temp = tempfile.TemporaryDirectory()
        root = Path(cls.temp.name)
        source = root / 'unicode.c'
        source.write_text(VIEW_RUNTIME + unicode_library_c() + r'''
void *test_nfc(unsigned char *input,size_t count,size_t *length){
    eri_text result=eri_unicode_normalizeNfc((eri_text){count,input});
    *length=result.len;return result.data;
}
int test_xid(unsigned char *input,size_t count,int start){
    return eri_unicode_identifier((eri_text){count,input},start!=0);
}
void test_release(void *data){free(data);}
''')
        library = root / 'unicode.so'
        result = subprocess.run([cc, '-std=c11', '-shared', '-fPIC',
                                 *shlex.split(os.environ.get('CFLAGS', '')),
                                 str(source), '-lm', '-o', str(library)], capture_output=True, text=True)
        if result.returncode:
            cls.temp.cleanup()
            raise AssertionError(result.stderr)
        cls.lib = ctypes.CDLL(str(library))
        cls.lib.test_nfc.argtypes = [ctypes.c_char_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
        cls.lib.test_nfc.restype = ctypes.c_void_p
        cls.lib.test_release.argtypes = [ctypes.c_void_p]
        cls.lib.test_xid.argtypes = [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_int]
        cls.lib.test_xid.restype = ctypes.c_int

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def normalize(self, text):
        encoded = text.encode('utf-8')
        size = ctypes.c_size_t()
        data = self.lib.test_nfc(encoded, len(encoded), ctypes.byref(size))
        try:
            return ctypes.string_at(data, size.value).decode('utf-8')
        finally:
            self.lib.test_release(data)

    def test_all_canonical_decompositions_and_hangul_match_unicode_17(self):
        cases = 0
        for cp in range(0x110000):
            ch = chr(cp)
            decomposition = unicodedata2.decomposition(ch)
            if (decomposition and not decomposition.startswith('<')) or 0xAC00 <= cp < 0xD7A4:
                decomposed = unicodedata2.normalize('NFD', ch)
                self.assertEqual(self.normalize(decomposed), unicodedata2.normalize('NFC', ch), hex(cp))
                self.assertEqual(self.normalize(ch), unicodedata2.normalize('NFC', ch), hex(cp))
                cases += 1
        self.assertGreater(cases, 13000)

    def test_normalization_reordering_blocking_exclusions_and_embedded_nul(self):
        cases = ['', '\0A\u0301\0', '\u0344', '\u1100\u1161\u11a8',
                 '\u0301A\u0315\u0300', 'A\u0305\u0301', '\u212b', '😀']
        rng = random.Random(17)
        alphabet = 'Aa\u0300\u0301\u0315\u0327\u0344\u1100\u1161\u11a8\0'
        cases.extend(''.join(rng.choice(alphabet) for _ in range(12)) for _ in range(300))
        for text in cases:
            self.assertEqual(self.normalize(text), unicodedata2.normalize('NFC', text), repr(text))

    def test_identifier_table_boundaries_match_reference(self):
        for prop, checker, start in [('XID_Start', is_xid_start, 1), ('XID_Continue', is_xid_continue, 0)]:
            points = {0, 95, 0x10FFFF}
            for first, last in _property_ranges(prop):
                points.update((first-1, first, last, last+1))
            for cp in points:
                if not 0 <= cp <= 0x10FFFF or 0xD800 <= cp <= 0xDFFF:
                    continue
                char = chr(cp)
                encoded = char.encode('utf-8')
                expected = char == '_' or checker(char)
                self.assertEqual(bool(self.lib.test_xid(encoded, len(encoded), start)), expected, hex(cp))
            for text in ['', 'AA', '_a', 'A\u0301']:
                encoded = text.encode('utf-8')
                self.assertFalse(self.lib.test_xid(encoded, len(encoded), start))

    def test_reference_contracts_aliases_and_invalid_scalars(self):
        program, _ = analyze_frontend('import std.unicode as u; '
                                     'output(u.fromScalar(128512)); '
                                     'output(u.normalizeNfc("A\\u{301}")); '
                                     'output(u.isIdentifierContinue("\\u{301}"));')
        output = []
        Interpreter(output.append).run(program)
        self.assertEqual(output, ['😀', 'Á', 'true'])
        for value in [-1, 0xD800, 0xDFFF, 0x110000]:
            program, _ = analyze_frontend(f'import std.unicode; output(unicode.fromScalar({value}));')
            with self.assertRaises(RuntimeFault):
                Interpreter().run(program)
        for source in ['unicode.fromScalar("A")', 'unicode.normalizeNfc(1)',
                       'unicode.isIdentifierStart()', 'unicode.unknown("A")']:
            with self.assertRaises(SemanticError):
                analyze_frontend('import std.unicode; output(' + source + ');')
