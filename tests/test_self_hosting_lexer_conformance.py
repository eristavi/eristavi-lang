from __future__ import annotations

import random
import subprocess
import tempfile
import unittest
from pathlib import Path

from compiler.erist.cli import emit_direct_asm, build_native
from compiler.erist.diagnostics import LexError
from compiler.erist.lexer import Lexer, TokenKind
from selfhost_support import execute, literal, prepare


def probe(source):
    return (
        'import compiler.lexer; import compiler.diagnostic; '
        'function probe(source Text) { '
        'let tokens be lexer.lex(source) else error diagnostic.LexError { '
        'output("ERROR"); output(error.line); output(error.column); return; }; '
        'for item in tokens { output(item.kind); output(item.lexeme); output(item.value); '
        'output(item.line); output(item.column); } } '
        f'probe({literal(source)});'
    )


class SelfHostedLexerConformanceTests(unittest.TestCase):
    def assert_matches(self, source):
        try:
            tokens = Lexer(source).lex()
        except LexError as error:
            expected = ['ERROR', str(error.location.line), str(error.location.column)]
        else:
            expected = []
            for item in tokens:
                # Stage-1 keeps numeric spelling for the later typed-literal
                # stage; Stage-0 already decodes it into a Python number.
                value = item.value if item.kind in (TokenKind.IDENTIFIER, TokenKind.TEXT) else item.lexeme
                expected.extend([str(item.kind.value-1), item.lexeme, value,
                                 str(item.location.line), str(item.location.column)])
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            entry = prepare(root, probe(source))
            self.assertEqual(execute(entry, root), expected, repr(source))

    def test_valid_tokens_values_and_locations(self):
        cases = [
            '', '\ufefflet answer be 40 + 2;',
            'let café be "A\\u{301}\\n\\0";\r\noutput(cafe\u0301);',
            'let სახელი be "ქართული"; let имя be "😀";',
            'let 𐐀x be 0xAB_CD; let x\u0301 be 0b10_01;',
            '0 123 1_000 0B10 0Xff 1.25 0.5e-2 1e+10 00.1',
            '/* outer\n /* nested */ */ let x be 1; // tail\n',
            '"\\u{0}\\u{10FFFF}\\u{1F600}\\\\\\\"\\r\\t"',
            '== != <= >= ; , . ( ) { } [ ] = + - * / % < >',
            'let fixed be function returns return if else for in while type identity maybe '
            'error fails fail try with import as public and or not true false none',
        ]
        for source in cases:
            with self.subTest(source=source):
                self.assert_matches(source)

    def test_invalid_sources_and_diagnostic_locations(self):
        cases = [
            '1__2', '123_', '0_1', '01', '0b_1', '0xF_', '0x', '0b',
            '1.', '1._2', '1e', '1e+', '1e_2', '1.2__3', '1.2e3_',
            '"\\u{}"', '"\\u{D800}"', '"\\u{110000}"', '"\\u{1234567}"',
            '"\\u{XYZ}"', '"\\x41"', '"unfinished', '"abc\\', '"a\nb"',
            '/* unfinished', 'a\n\ufeffb', '\ufeff\ufeff', '// \ufeff',
            '"\ufeff"', 'let\u00a0x be 1;', '😀', '١٢', '0x١', '²',
        ]
        for source in cases:
            with self.subTest(source=source):
                self.assert_matches(source)

    def test_generated_numeric_separator_cases(self):
        rng = random.Random(17)
        for _ in range(30):
            source = ''.join(rng.choice('01_') for _ in range(rng.randrange(1, 8)))
            with self.subTest(source=source):
                self.assert_matches(source)

    def test_portable_c_executes_eristavi_lexer_with_unicode(self):
        source = 'let cafe\u0301 be "\\u{1F600}";\noutput(café);'
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            program = probe(source)
            for extra in ['"\\u{0}\\u{10FFFF}\\n"', '1__2', '01', '"\\u{D800}"']:
                program += f'probe({literal(extra)});'
            entry = prepare(root, program)
            expected = execute(entry, root)
            binary = root / 'lexer'
            self.assertEqual(build_native(entry, binary, root), 0)
            result = subprocess.run([str(binary)], capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, ''.join(item + '\n' for item in expected))

    def test_unimplemented_direct_unicode_fails_with_c_route_guidance(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            entry = root / 'probe.eri'
            entry.write_text('import std.unicode; output(unicode.normalizeNfc("A"));')
            from contextlib import redirect_stderr
            from io import StringIO
            errors = StringIO()
            with redirect_stderr(errors):
                self.assertEqual(emit_direct_asm(entry, root / 'app.s', root), 1)
            self.assertIn("use 'erist build'", errors.getvalue())
