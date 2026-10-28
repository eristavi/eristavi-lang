from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from compiler.erist.cli import build_native


class BackendTextRuntimeTests(unittest.TestCase):
    @staticmethod
    def q(path: Path) -> str:
        return str(path).replace("\\", "\\\\").replace('"', '\\"')

    def compile_run(self, source: str, files: dict[str, bytes] | None = None):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for name, data in (files or {}).items():
                p = root / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(data)
            src = root / "app.eri"
            exe = root / "app"
            src.write_text(source, encoding="utf-8")
            self.assertEqual(build_native(src, exe, root), 0)
            return subprocess.run([str(exe)], capture_output=True)

    def test_native_text_preserves_embedded_nul_output(self):
        p = self.compile_run('output("A\\0B");')
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout, b"A\x00B\n")

    def test_native_text_embedded_nul_equality_and_concat(self):
        p = self.compile_run(
            'let a be "A\\0"; let b be a + "B"; '
            'output(b == "A\\0B"); output(b != "A"); output(b);'
            'output("" == ""); output(b == ""); output("" == b);'
        )
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout, b"true\ntrue\nA\x00B\ntrue\nfalse\nfalse\n")

    def test_native_file_roundtrip_preserves_embedded_nul(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "data.txt"
            path.write_bytes(b"old")
            q = self.q(path)
            source = f'''
import std.files;
function write(path Text, text Text) fails files.FileError {{
    with file be try files.open(path) {{
        try file.writeText(text);
    }}
}}
function read(path Text) returns Text fails files.FileError {{
    with file be try files.open(path) {{
        return try file.readText();
    }}
}}
function run() {{
    write("{q}", "A\\0B") else error {{ output(error.message); return; }};
    let text be read("{q}") else error {{ output(error.message); return; }};
    output(text == "A\\0B");
    output(text);
}}
run();
'''
            src = root / "app.eri"
            exe = root / "app"
            src.write_text(source, encoding="utf-8")
            self.assertEqual(build_native(src, exe, root), 0)
            p = subprocess.run([str(exe)], capture_output=True)
            self.assertEqual(p.returncode, 0)
            self.assertEqual(p.stdout, b"true\nA\x00B\n")
            self.assertEqual(path.read_bytes(), b"A\x00B")

    def test_native_invalid_utf8_read_is_checked_failure(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "bad.bin"
            path.write_bytes(b"\xff\xfe")
            q = self.q(path)
            source = f'''
import std.files;
function read(path Text) returns Text fails files.FileError {{
    with file be try files.open(path) {{
        return try file.readText();
    }}
}}
function run() {{
    let text be read("{q}") else error {{
        output("decode failed");
        return;
    }};
    output(text);
}}
run();
'''
            src = root / "app.eri"
            exe = root / "app"
            src.write_text(source, encoding="utf-8")
            self.assertEqual(build_native(src, exe, root), 0)
            p = subprocess.run([str(exe)], capture_output=True)
            self.assertEqual(p.returncode, 0)
            self.assertEqual(p.stdout, b"decode failed\n")

    def test_native_nul_in_file_path_is_checked_failure(self):
        source = '''
import std.files;
function read(path Text) returns Text fails files.FileError {
    with file be try files.open(path) {
        return try file.readText();
    }
}
function run() {
    let text be read("bad\\0path") else error {
        output("path failed");
        return;
    };
    output(text);
}
run();
'''
        p = self.compile_run(source)
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout, b"path failed\n")


if __name__ == "__main__":
    unittest.main()
