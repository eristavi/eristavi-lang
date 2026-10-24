from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from compiler.erist.cli import build_native


class BackendTextViewTests(unittest.TestCase):
    def compile_run(self, source: str):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "app.eri"
            exe = root / "app"
            src.write_text(source, encoding="utf-8")
            self.assertEqual(build_native(src, exe, root), 0)
            return subprocess.run([str(exe)], capture_output=True, text=True)

    def test_native_byte_view_count_and_index(self):
        p = self.compile_run(
            'let text be "A\\u{301}"; output(text.bytes.count); '
            'output(text.bytes[0]); output(text.bytes[1]); output(text.bytes[2]);'
        )
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout, "3\n65\n204\n129\n")

    def test_native_scalar_view_count_and_index(self):
        p = self.compile_run(
            'let text be "A\\u{301}😀"; output(text.scalars.count); '
            'output(text.scalars[0]); output(text.scalars[1]); output(text.scalars[2]);'
        )
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout, "3\nA\ń\n😀\n")

    def test_native_character_view_combining_and_zwj(self):
        p = self.compile_run(
            'let text be "A\\u{301}👩‍💻B"; let chars be text.characters; '
            'output(chars.count); output(chars[0]); output(chars[1]); output(chars[2]);'
        )
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout, "3\nÁ\n👩‍💻\nB\n")

    def test_native_character_view_pairs_regional_indicators(self):
        p = self.compile_run(
            'let text be "🇺🇸🇨🇾"; output(text.characters.count); '
            'output(text.characters[0]); output(text.characters[1]);'
        )
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout, "2\n🇺🇸\n🇨🇾\n")

    def test_native_character_view_indic_conjunct(self):
        p = self.compile_run(
            'let text be "क्ष"; output(text.characters.count); output(text.characters[0]);'
        )
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout, "1\nक्ष\n")

    def test_native_views_can_be_stored(self):
        p = self.compile_run(
            'let text be "é"; let bytes be text.bytes; let scalars be text.scalars; let chars be text.characters; '
            'output(bytes.count); output(scalars.count); output(chars.count); '
            'output(bytes[0]); output(scalars[0]); output(chars[0]);'
        )
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout, "2\n1\n1\n195\né\né\n")

    def test_native_scalar_view_bounds_fault(self):
        p = self.compile_run('let text be "A"; let i be 1; output(text.scalars[i]);')
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("Text view index out of bounds", p.stderr)

    def test_native_character_view_bounds_fault(self):
        p = self.compile_run('let text be "👩‍💻"; let i be 1; output(text.characters[i]);')
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("Text view index out of bounds", p.stderr)


if __name__ == "__main__":
    unittest.main()
