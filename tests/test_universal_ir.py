from __future__ import annotations

import platform
import subprocess
import tempfile
import unittest
from pathlib import Path

from compiler.erist.cli import build_direct, lower_universal_file
from compiler.erist.universal_ir import UBranch, UJump, format_program


DIRECT_HOST = platform.system() == "Linux" and platform.machine().lower() in ("x86_64", "amd64")


class UniversalIRTests(unittest.TestCase):
    def source(self, text: str):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        src = root / "app.eri"
        src.write_text(text, encoding="utf-8")
        return td, root, src

    def test_universal_ir_has_explicit_checked_arithmetic_and_control_flow(self):
        td, root, src = self.source(
            "let x be 1; let y be 2; let z be x + y; "
            "if z == 3 { output(z); } else { output(0); }"
        )
        try:
            program = lower_universal_file(src, root)
            text = format_program(program)
            self.assertIn("add_checked", text)
            self.assertIn("cmp_eq", text)
            self.assertIn("branch", text)
            self.assertTrue(any(isinstance(block.terminator, UBranch) for block in program.function("__entry").blocks))
        finally:
            td.cleanup()

    def test_universal_ir_while_uses_basic_blocks(self):
        td, root, src = self.source("let n be 0; while n < 3 { n = n + 1; } output(n);")
        try:
            program = lower_universal_file(src, root)
            names = [block.name for block in program.function("__entry").blocks]
            self.assertTrue(any(name.startswith("while.cond") for name in names))
            self.assertTrue(any(isinstance(block.terminator, UJump) for block in program.function("__entry").blocks))
        finally:
            td.cleanup()

    @unittest.skipUnless(DIRECT_HOST, "first direct backend executes on x86-64 Linux")
    def test_direct_x86_64_hello(self):
        p = self.compile_run("let x be 40; let y be 2; output(x + y);")
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout, "42\n")

    @unittest.skipUnless(DIRECT_HOST, "first direct backend executes on x86-64 Linux")
    def test_direct_x86_64_if_while_and_bool(self):
        p = self.compile_run(
            "let n be 0; while n < 3 { n = n + 1; } "
            "if n == 3 { output(true); output(n); } else { output(false); }"
        )
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout, "true\n3\n")

    @unittest.skipUnless(DIRECT_HOST, "first direct backend executes on x86-64 Linux")
    def test_direct_x86_64_signed_division_and_remainder(self):
        p = self.compile_run("output(-10 / 3); output(-10 % 3); output(10 % -3);")
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout, "-3\n-1\n1\n")

    @unittest.skipUnless(DIRECT_HOST, "first direct backend executes on x86-64 Linux")
    def test_direct_x86_64_overflow_fault(self):
        p = self.compile_run("let x be 9223372036854775807; output(x + 1);")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("Int arithmetic overflow", p.stderr)

    @unittest.skipUnless(DIRECT_HOST, "first direct backend executes on x86-64 Linux")
    def test_direct_x86_64_division_by_zero_fault(self):
        p = self.compile_run("let zero be 0; output(10 / zero);")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("Int division by zero", p.stderr)

    def compile_run(self, source: str):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "app.eri"
            exe = root / "app"
            src.write_text(source, encoding="utf-8")
            self.assertEqual(build_direct(src, exe, root), 0)
            return subprocess.run([str(exe)], capture_output=True, text=True)


if __name__ == "__main__":
    unittest.main()
