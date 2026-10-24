from __future__ import annotations

import platform
import subprocess
import tempfile
import unittest
from pathlib import Path

from compiler.erist.cli import build_direct

DIRECT_HOST = platform.system() == "Linux" and platform.machine().lower() in ("x86_64", "amd64")


@unittest.skipUnless(DIRECT_HOST, "generic direct execution currently targets x86-64 Linux")
class DirectGenericTests(unittest.TestCase):
    def compile_run(self, source: str):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "app.eri"
            exe = root / "app"
            src.write_text(source, encoding="utf-8")
            self.assertEqual(build_direct(src, exe, root), 0)
            return subprocess.run([str(exe)], capture_output=True, text=True)

    def test_inferred_preserve_specializes_for_int_text_and_float(self):
        p = self.compile_run(
            'function preserve(value) { return value; } '
            'output(preserve(42)); output(preserve("hello")); output(preserve(3.5));'
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout, "42\nhello\n3.5\n")

    def test_inferred_same_type_relationship(self):
        p = self.compile_run(
            'function choose(first, second, takeFirst Bool) { '
            'if takeFirst { return first; } return second; } '
            'output(choose(10, 20, true)); output(choose("A", "B", false));'
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout, "10\nB\n")

    def test_inferred_list_element_relationship(self):
        p = self.compile_run(
            'function first(values) { return values[0]; } '
            'output(first([4,5])); output(first(["A","B"]));'
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout, "4\nA\n")


if __name__ == "__main__":
    unittest.main()
