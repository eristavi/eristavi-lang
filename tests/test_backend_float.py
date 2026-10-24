from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from compiler.erist.cli import build_native


class BackendFloatTests(unittest.TestCase):
    def compile_run(self, source: str):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "app.eri"
            exe = root / "app"
            src.write_text(source, encoding="utf-8")
            self.assertEqual(build_native(src, exe, root), 0)
            return subprocess.run([str(exe)], capture_output=True, text=True)

    def test_native_nan_equality_follows_ieee(self):
        p = self.compile_run(
            "let a be 0.0 / 0.0; let b be 0.0 / 0.0; "
            "output(a == b); output(a != b);"
        )
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout, "false\ntrue\n")

    def test_native_signed_zero_is_preserved(self):
        p = self.compile_run(
            "let positive be 0.0; let negative be -0.0; "
            "output(positive == negative); "
            "output(1.0 / positive > 0.0); "
            "output(1.0 / negative < 0.0);"
        )
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout, "true\ntrue\ntrue\n")

    def test_native_infinities_follow_ieee_division(self):
        p = self.compile_run(
            "let positive be 1.0 / 0.0; let negative be -1.0 / 0.0; "
            "output(positive > 1.0e308); output(negative < -1.0e308);"
        )
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout, "true\ntrue\n")

    def test_native_smallest_subnormal_is_not_flushed_to_zero(self):
        p = self.compile_run(
            "let tiny be 4.9406564584124654e-324; output(tiny > 0.0);"
        )
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout, "true\n")

    def test_native_float_overflow_produces_infinity(self):
        p = self.compile_run(
            "let huge be 1.0e308 * 1.0e308; output(huge > 1.0e308);"
        )
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout, "true\n")


if __name__ == "__main__":
    unittest.main()
