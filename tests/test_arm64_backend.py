from __future__ import annotations

import platform
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from compiler.erist.arm64_backend import ARM64LinuxBackend
from compiler.erist.cli import build_direct, lower_universal_file

ARM64_LINUX_HOST = platform.system() == "Linux" and platform.machine().lower() in ("aarch64", "arm64")


class ARM64BackendTests(unittest.TestCase):
    def source(self, text: str):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        src = root / "app.eri"
        src.write_text(text, encoding="utf-8")
        return td, root, src

    def test_arm64_consumes_same_functional_universal_ir(self):
        td, root, src = self.source(
            "function factorial(value Int) returns Int { "
            "if value <= 1 { return 1; } return value * factorial(value - 1); } "
            "function average(a Float, b Float) returns Float { return (a + b) / 2.0; } "
            "output(factorial(5)); output(average(3.0, 4.0));"
        )
        try:
            program = lower_universal_file(src, root)
            asm = ARM64LinuxBackend().emit(program)
            self.assertIn("eri_fn_app_factorial", asm)
            self.assertIn("bl eri_fn_app_factorial", asm)
            self.assertIn("b.vs .Leri_fault_overflow", asm)
            self.assertIn("fadd d0, d0, d1", asm)
            self.assertIn("sdiv x2, x0, x1", asm)
        finally:
            td.cleanup()

    @unittest.skipUnless(shutil.which("clang"), "Clang is required for cross-assembly validation")
    def test_arm64_output_cross_assembles(self):
        td, root, src = self.source(
            "function add(a Int, b Int) returns Int { return a + b; } "
            "let n be 0; while n < 2 { n = n + 1; } output(add(40, n));"
        )
        try:
            asm = root / "app.s"
            obj = root / "app.o"
            asm.write_text(ARM64LinuxBackend().emit(lower_universal_file(src, root)), encoding="utf-8")
            proc = subprocess.run(
                [shutil.which("clang"), "--target=aarch64-linux-gnu", "-c", str(asm), "-o", str(obj)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue(obj.exists())
            self.assertGreater(obj.stat().st_size, 0)
        finally:
            td.cleanup()

    @unittest.skipUnless(ARM64_LINUX_HOST, "direct ARM64 execution requires an ARM64 Linux host")
    def test_arm64_native_execution(self):
        td, root, src = self.source(
            "function factorial(value Int) returns Int { "
            "if value <= 1 { return 1; } return value * factorial(value - 1); } "
            "output(factorial(5));"
        )
        try:
            exe = root / "app"
            self.assertEqual(build_direct(src, exe, root, target="arm64-linux"), 0)
            proc = subprocess.run([str(exe)], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(proc.stdout, "120\n")
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
