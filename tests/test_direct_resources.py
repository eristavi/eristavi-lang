from __future__ import annotations

import platform
import subprocess
import tempfile
import unittest
from pathlib import Path

from compiler.erist.cli import build_direct

DIRECT_HOST = platform.system() == "Linux" and platform.machine().lower() in ("x86_64", "amd64")


@unittest.skipUnless(DIRECT_HOST, "resource direct execution currently targets x86-64 Linux")
class DirectResourceTests(unittest.TestCase):
    @staticmethod
    def q(path: Path) -> str:
        return str(path).replace("\\", "\\\\").replace('"', '\\"')

    def compile_run(self, source_builder, files: dict[str, bytes | str] | None = None):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for name, content in (files or {}).items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                if isinstance(content, bytes):
                    path.write_bytes(content)
                else:
                    path.write_text(content, encoding="utf-8")
            src = root / "app.eri"
            exe = root / "app"
            src.write_text(source_builder(root), encoding="utf-8")
            self.assertEqual(build_direct(src, exe, root), 0)
            process = subprocess.run([str(exe)], capture_output=True, text=False)
            result_bytes = {name: (root / name).read_bytes() for name in (files or {}) if (root / name).exists()}
            return process, result_bytes

    def test_direct_file_read_and_return_cleanup(self):
        def source(root):
            path = self.q(root / "data.txt")
            return (
                'import std.files; '
                'function read(path Text) returns Text fails files.FileError { '
                'with file be try files.open(path) { return try file.readText(); } } '
                'function show(path Text) { let text be read(path) else error { output(error.message); return; }; output(text); } '
                f'show("{path}");'
            )
        p, _ = self.compile_run(source, {"data.txt": "hello"})
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout, b"hello\n")

    def test_direct_file_write_read_and_embedded_nul(self):
        def source(root):
            path = self.q(root / "data.txt")
            return (
                'import std.files; '
                'function work(path Text) returns Text fails files.FileError { '
                'with file be try files.open(path) { try file.writeText("A\\0B"); return try file.readText(); } } '
                'function show(path Text) { let text be work(path) else error { output(error.message); return; }; output(text); } '
                f'show("{path}");'
            )
        p, files = self.compile_run(source, {"data.txt": "old"})
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout, b"A\x00B\n")
        self.assertEqual(files["data.txt"], b"A\x00B")

    def test_direct_missing_file_is_checked(self):
        def source(root):
            path = self.q(root / "missing.txt")
            return (
                'import std.files; '
                'function read(path Text) returns Text fails files.FileError { '
                'with file be try files.open(path) { return try file.readText(); } } '
                f'read("{path}") else error {{ output(error.message); }};'
            )
        p, _ = self.compile_run(source)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertTrue(p.stdout.strip())

    def test_direct_invalid_utf8_is_checked(self):
        def source(root):
            path = self.q(root / "bad.bin")
            return (
                'import std.files; '
                'function read(path Text) returns Text fails files.FileError { '
                'with file be try files.open(path) { return try file.readText(); } } '
                f'read("{path}") else error {{ output(error.message); }};'
            )
        p, _ = self.compile_run(source, {"bad.bin": b"\xff\xfe"})
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn(b"invalid UTF-8", p.stdout)

    def test_direct_nul_path_is_checked(self):
        def source(root):
            base = self.q(root / "bad")
            return (
                'import std.files; '
                'function check(path Text) returns Bool fails files.FileError { return try files.exists(path); } '
                f'check("{base}\\0tail") else error {{ output(error.message); }};'
            )
        p, _ = self.compile_run(source)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn(b"NUL", p.stdout)

    def test_direct_exists_and_remove(self):
        def source(root):
            path = self.q(root / "data.txt")
            return (
                'import std.files; '
                'function run(path Text) fails files.FileError { '
                'output(try files.exists(path)); try files.remove(path); output(try files.exists(path)); } '
                f'run("{path}") else error {{ output(error.message); }};'
            )
        p, _ = self.compile_run(source, {"data.txt": "x"})
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout, b"true\nfalse\n")

    def test_direct_remove_missing_is_checked(self):
        def source(root):
            path = self.q(root / "missing.txt")
            return (
                'import std.files; '
                'function run(path Text) fails files.FileError { try files.remove(path); } '
                f'run("{path}") else error {{ output(error.message); }};'
            )
        p, _ = self.compile_run(source)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertTrue(p.stdout.strip())

    def test_direct_body_failure_remains_primary_through_cleanup(self):
        def source(root):
            path = self.q(root / "data.txt")
            return (
                'import std.files; error BodyError { message Text; } '
                'function work(path Text) fails BodyError, files.FileError { '
                'with file be try files.open(path) { fail BodyError { message="body failed"; }; } } '
                f'work("{path}") else error BodyError {{ output(error.message); }} '
                'else error files.FileError { output("file failure"); };'
            )
        p, _ = self.compile_run(source, {"data.txt": "x"})
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout, b"body failed\n")

    def test_direct_nested_resources_cleanup_on_return(self):
        def source(root):
            a = self.q(root / "a.txt")
            b = self.q(root / "b.txt")
            return (
                'import std.files; '
                'function readBoth(a Text,b Text) returns Text fails files.FileError { '
                'with first be try files.open(a) { with second be try files.open(b) { '
                'return try first.readText() + try second.readText(); } } } '
                'function show(a Text,b Text) { let text be readBoth(a,b) else error { output(error.message); return; }; output(text); } '
                f'show("{a}","{b}");'
            )
        p, _ = self.compile_run(source, {"a.txt": "A", "b.txt": "B"})
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout, b"AB\n")


if __name__ == "__main__":
    unittest.main()
