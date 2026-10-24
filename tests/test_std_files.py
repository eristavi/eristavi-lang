from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from compiler.erist.cli import build_native
from compiler.erist.project import compile_entry
from compiler.erist.runtime_ext import Interpreter


class StdFilesTests(unittest.TestCase):
    @staticmethod
    def quote(path: Path) -> str:
        return str(path).replace("\\", "\\\\").replace('"', '\\"')

    def run_bootstrap(self, root: Path, source: str):
        entry = root / "app.eri"
        entry.write_text(source, encoding="utf-8")
        mod = compile_entry(entry, root)
        out: list[str] = []
        Interpreter(out.append, mod.module_id, mod.imports).run(mod.program)
        return out

    def compile_run(self, root: Path, source: str):
        entry = root / "app.eri"
        exe = root / "app"
        entry.write_text(source, encoding="utf-8")
        self.assertEqual(build_native(entry, exe, root), 0)
        return subprocess.run([str(exe)], capture_output=True, text=True)

    def source_for_exists(self, path: str) -> str:
        return f'''
import std.files;
function probe(path Text) returns Bool fails files.FileError {{
    return try files.exists(path);
}}
function show(path Text) {{
    let found be probe(path) else error {{ output(error.message); return; }};
    output(found);
}}
show("{path}");
'''

    def test_files_exists_bootstrap_present_and_missing(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            present = root / "present.txt"
            present.write_text("ok", encoding="utf-8")
            self.assertEqual(self.run_bootstrap(root, self.source_for_exists(self.quote(present))), ["true"])
            missing = root / "missing.txt"
            self.assertEqual(self.run_bootstrap(root, self.source_for_exists(self.quote(missing))), ["false"])

    def test_files_exists_native_present_and_missing(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            present = root / "present.txt"
            present.write_text("ok", encoding="utf-8")
            p = self.compile_run(root, self.source_for_exists(self.quote(present)))
            self.assertEqual((p.returncode, p.stdout), (0, "true\n"))
            missing = root / "missing.txt"
            p = self.compile_run(root, self.source_for_exists(self.quote(missing)))
            self.assertEqual((p.returncode, p.stdout), (0, "false\n"))

    def source_for_remove(self, path: str) -> str:
        return f'''
import std.files;
function erase(path Text) fails files.FileError {{
    try files.remove(path);
}}
function act(path Text) {{
    erase(path) else error {{ output(error.message); return; }};
    output("removed");
}}
act("{path}");
'''

    def test_files_remove_bootstrap(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = root / "remove.txt"
            target.write_text("bye", encoding="utf-8")
            self.assertEqual(self.run_bootstrap(root, self.source_for_remove(self.quote(target))), ["removed"])
            self.assertFalse(target.exists())

    def test_files_remove_native_and_missing_is_checked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = root / "remove.txt"
            target.write_text("bye", encoding="utf-8")
            p = self.compile_run(root, self.source_for_remove(self.quote(target)))
            self.assertEqual((p.returncode, p.stdout), (0, "removed\n"))
            self.assertFalse(target.exists())
            p = self.compile_run(root, self.source_for_remove(self.quote(target)))
            self.assertEqual(p.returncode, 0)
            self.assertNotIn("removed", p.stdout)
            self.assertTrue(p.stdout.strip())


if __name__ == "__main__":
    unittest.main()
