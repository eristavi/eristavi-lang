from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from compiler.erist.arm64_resource_backend import ARM64ResourceRuntimeLinuxBackend
from compiler.erist.cli import lower_universal_file


class ARM64ResourceBackendTests(unittest.TestCase):
    def emit(self, source: str):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        src = root / "app.eri"
        src.write_text(source, encoding="utf-8")
        return td, ARM64ResourceRuntimeLinuxBackend().emit(lower_universal_file(src, root))

    def test_resource_ops_and_secondary_failure_state_emit(self):
        td, asm = self.emit(
            'import std.files; '
            'function load(path Text) returns Text fails files.FileError { '
            'with file be try files.open(path) { return try file.readText(); } } '
            'load("/tmp/missing") else error { output(error.message); };'
        )
        try:
            for symbol in (".Leri_file_open", ".Leri_file_read_text", ".Leri_file_cleanup", ".Leri_error_secondary_head"):
                self.assertIn(symbol, asm)
        finally:
            td.cleanup()

    @unittest.skipUnless(shutil.which("clang"), "Clang is required for AArch64 cross-assembly validation")
    def test_file_runtime_cross_assembles(self):
        td, asm = self.emit(
            'import std.files; '
            'function work(path Text) returns Bool fails files.FileError { '
            'if try files.exists(path) { with file be try files.open(path) { try file.writeText("hello"); return true; } } '
            'return false; } '
            'work("/tmp/eristavi-arm64-test") else error { output(error.message); };'
        )
        try:
            root=Path(td.name); path=root/"resource.s"; obj=root/"resource.o"; path.write_text(asm,encoding="utf-8")
            p=subprocess.run([shutil.which("clang"),"--target=aarch64-linux-gnu","-c",str(path),"-o",str(obj)],capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr)
        finally:
            td.cleanup()


if __name__=="__main__": unittest.main()
