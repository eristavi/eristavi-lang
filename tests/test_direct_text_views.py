from __future__ import annotations

import platform
import subprocess
import tempfile
import unittest
from pathlib import Path

from compiler.erist.cli import build_direct

DIRECT_HOST = platform.system() == "Linux" and platform.machine().lower() in ("x86_64", "amd64")


@unittest.skipUnless(DIRECT_HOST, "direct Text-view execution currently targets x86-64 Linux")
class DirectTextViewTests(unittest.TestCase):
    def run_source(self, source: str):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "app.eri"
            exe = root / "app"
            src.write_text(source, encoding="utf-8")
            self.assertEqual(build_direct(src, exe, root), 0)
            return subprocess.run([str(exe)], capture_output=True, text=False)

    def test_byte_scalar_character_counts_and_index(self):
        p = self.run_source(
            'let text be "A\\u{301}🙂"; '
            'output(text.bytes.count); output(text.scalars.count); output(text.characters.count); '
            'output(text.bytes[0]); output(text.scalars[0]); output(text.characters[0]); output(text.characters[1]);'
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout, "7\n3\n2\n65\nA\nÁ\n🙂\n".encode("utf-8"))

    def test_character_segmentation_zwj_and_regional_indicators(self):
        p = self.run_source(
            'let family be "👩‍👩‍👧‍👦"; let flags be "🇨🇾🇬🇪"; '
            'output(family.characters.count); output(family.characters[0]); '
            'output(flags.characters.count); output(flags.characters[0]); output(flags.characters[1]);'
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout, "1\n👩‍👩‍👧‍👦\n2\n🇨🇾\n🇬🇪\n".encode("utf-8"))

    def test_character_segmentation_indic_conjunct(self):
        p = self.run_source('let text be "क्‍ष"; output(text.characters.count); output(text.characters[0]);')
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout, "1\nक्‍ष\n".encode("utf-8"))

    def test_text_view_bounds_fault(self):
        p = self.run_source('let text be "A"; output(text.scalars[1]);')
        self.assertNotEqual(p.returncode, 0)
        self.assertIn(b"Text view index out of bounds", p.stderr)


if __name__ == "__main__":
    unittest.main()
