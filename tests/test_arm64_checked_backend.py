from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from compiler.erist.arm64_checked_backend import ARM64CheckedRuntimeLinuxBackend
from compiler.erist.cli import lower_universal_file


class ARM64CheckedBackendTests(unittest.TestCase):
    def emit(self, source: str):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        src = root / "app.eri"
        src.write_text(source, encoding="utf-8")
        return td, ARM64CheckedRuntimeLinuxBackend().emit(lower_universal_file(src, root))

    def test_typed_and_catch_all_error_state_emit(self):
        td, asm = self.emit(
            'error E { message Text; code Int; } '
            'function risky(flag Bool) returns Int fails E { if flag { fail E { message="bad"; code=7; }; } return 2; } '
            'risky(true) else error E { output(error.message); output(error.code); }; '
            'risky(false) else error { output(error.message); };'
        )
        try:
            self.assertIn(".Leri_error_value", asm)
            self.assertIn(".Leri_error_type_", asm)
            self.assertIn(".Leri_error_message", asm)
        finally:
            td.cleanup()

    @unittest.skipUnless(shutil.which("clang"), "Clang is required for AArch64 cross-assembly validation")
    def test_checked_errors_cross_assemble(self):
        td, asm = self.emit(
            'error E { message Text; code Int; } '
            'function risky() returns Int fails E { fail E { message="bad"; code=9; }; } '
            'risky() else error E { output(error.message); output(error.code); };'
        )
        try:
            root = Path(td.name)
            path = root / "errors.s"
            obj = root / "errors.o"
            path.write_text(asm, encoding="utf-8")
            p = subprocess.run([shutil.which("clang"), "--target=aarch64-linux-gnu", "-c", str(path), "-o", str(obj)], capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
