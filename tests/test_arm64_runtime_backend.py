from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from compiler.erist.arm64_runtime_backend import ARM64RuntimeLinuxBackend
from compiler.erist.cli import lower_universal_file


class ARM64RuntimeBackendTests(unittest.TestCase):
    def lower(self, source: str):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        src = root / "app.eri"
        src.write_text(source, encoding="utf-8")
        return td, ARM64RuntimeLinuxBackend().emit(lower_universal_file(src, root))

    def test_text_values_lists_nominals_maybe_and_identity_emit(self):
        td, asm = self.lower(
            'type User { name Text; score Int; } '
            'let original be User { name="Anna"; score=5; }; '
            'let copy be original; copy.score = 6; '
            'let users be [original]; users.add(copy); '
            'let optional maybe User be original; '
            'let shared be identity User { name="Shared"; score=1; }; '
            'output(original.name + "!"); output(users.count); '
            'if optional != none { output(optional.name); } output(shared.name);'
        )
        try:
            self.assertIn("bl malloc", asm)
            self.assertIn("bl realloc", asm)
            self.assertIn("bl memcpy", asm)
            self.assertIn(".Leri_clone_", asm)
            self.assertIn(".Leri_text_", asm)
        finally:
            td.cleanup()

    @unittest.skipUnless(shutil.which("clang"), "Clang is required for AArch64 cross-assembly validation")
    def test_text_and_aggregate_output_cross_assembles(self):
        td, asm = self.lower(
            'type Pair { left Text; right Int; } '
            'let a be Pair { left="A"; right=1; }; let b be a; b.right=2; '
            'let values be [a,b]; output(values[0].left + values[1].left); output(values.count);'
        )
        try:
            root = Path(td.name)
            path = root / "app.s"
            obj = root / "app.o"
            path.write_text(asm, encoding="utf-8")
            p = subprocess.run([shutil.which("clang"), "--target=aarch64-linux-gnu", "-c", str(path), "-o", str(obj)], capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertTrue(obj.exists())
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
