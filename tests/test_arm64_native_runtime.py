from __future__ import annotations

import platform
import subprocess
import tempfile
import unittest
from pathlib import Path

from compiler.erist.cli import build_direct

ARM64_LINUX = platform.system() == "Linux" and platform.machine().lower() in ("aarch64", "arm64")


@unittest.skipUnless(ARM64_LINUX, "expanded ARM64 runtime execution requires ARM64 Linux")
class ARM64NativeRuntimeTests(unittest.TestCase):
    @staticmethod
    def q(path: Path) -> str:
        return str(path).replace("\\", "\\\\").replace('"', '\\"')

    def compile_run(self, source: str, *, files: dict[str, bytes | str] | None = None):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for name, content in (files or {}).items():
                path = root / name
                if isinstance(content, bytes):
                    path.write_bytes(content)
                else:
                    path.write_text(content, encoding="utf-8")
            src = root / "app.eri"
            exe = root / "app"
            src.write_text(source, encoding="utf-8")
            self.assertEqual(build_direct(src, exe, root, "arm64-linux"), 0)
            return subprocess.run([str(exe)], capture_output=True, text=False)

    def test_text_nominal_list_maybe_and_identity_execute(self):
        p = self.compile_run(
            'type User { name Text; score Int; } '
            'let original be User { name="Anna"; score=5; }; '
            'let copy be original; copy.score = 6; '
            'let users be [original]; users.add(copy); '
            'let optional maybe User be original; '
            'let shared be identity User { name="Shared"; score=1; }; '
            'shared.score = 9; '
            'output(original.name + "!"); output(users.count); output(users[1].score); '
            'if optional != none { output(optional.name); } output(shared.score);'
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout, b"Anna!\n2\n6\nAnna\n9\n")

    def test_checked_errors_execute_natively(self):
        p = self.compile_run(
            'error E { message Text; code Int; } '
            'function risky(flag Bool) returns Int fails E { '
            'if flag { fail E { message="bad"; code=9; }; } return 2; } '
            'risky(true) else error E { output(error.message); output(error.code); }; '
            'let good be risky(false) else error { output(error.message); }; output(good);'
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout, b"bad\n9\n2\n")

    def test_file_resource_roundtrip_executes_natively(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            data = root / "data.txt"
            data.write_text("old", encoding="utf-8")
            src = root / "app.eri"
            exe = root / "app"
            path = self.q(data)
            src.write_text(
                'import std.files; '
                'function work(path Text) returns Text fails files.FileError { '
                'with file be try files.open(path) { try file.writeText("A\\0B"); return try file.readText(); } } '
                'function show(path Text) { let text be work(path) else error { output(error.message); return; }; output(text); } '
                f'show("{path}");',
                encoding="utf-8",
            )
            self.assertEqual(build_direct(src, exe, root, "arm64-linux"), 0)
            p = subprocess.run([str(exe)], capture_output=True, text=False)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(p.stdout, b"A\x00B\n")
            self.assertEqual(data.read_bytes(), b"A\x00B")


if __name__ == "__main__":
    unittest.main()
