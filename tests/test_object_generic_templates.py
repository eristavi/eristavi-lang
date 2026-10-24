from __future__ import annotations

import platform
import subprocess
import tempfile
import unittest
from pathlib import Path

from compiler.erist.cli import build_direct, emit_interface, emit_object
from compiler.erist.object_artifact import ModuleObjectArtifact

DIRECT_HOST = platform.system() == "Linux" and platform.machine().lower() in ("x86_64", "amd64")


class GenericObjectTemplateTests(unittest.TestCase):
    def make_project(self, library: str, application: str):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        module = root / "lib.eri"
        module.write_text(library, encoding="utf-8")
        (root / "app.eri").write_text(application, encoding="utf-8")
        self.assertEqual(emit_interface(module, None, root), 0)
        self.assertEqual(emit_object(module, None, root), 0)
        artifact = ModuleObjectArtifact.from_json((root / "lib.eri-object.json").read_text(encoding="utf-8"))
        self.assertIsNotNone(artifact.generic_source)
        module.unlink()
        return td, root

    @unittest.skipUnless(DIRECT_HOST, "generic object specialization executes on x86-64 Linux")
    def test_interface_object_specializes_preserve_after_source_removal(self):
        td, root = self.make_project(
            'public function preserve(value) { return value; }',
            'import lib; output(lib.preserve(42)); output(lib.preserve("Hello")); output(lib.preserve(3.5));',
        )
        try:
            exe = root / "app"
            self.assertEqual(build_direct(root / "app.eri", exe, root), 0)
            p = subprocess.run([str(exe)], capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(p.stdout, "42\nHello\n3.5\n")
        finally:
            td.cleanup()

    @unittest.skipUnless(DIRECT_HOST, "generic object specialization executes on x86-64 Linux")
    def test_interface_object_specializes_same_type_relationship(self):
        td, root = self.make_project(
            'public function first(a, b) { return a; }',
            'import lib; output(lib.first(7, 8)); output(lib.first("A", "B"));',
        )
        try:
            exe = root / "app"
            self.assertEqual(build_direct(root / "app.eri", exe, root), 0)
            p = subprocess.run([str(exe)], capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(p.stdout, "7\nA\n")
        finally:
            td.cleanup()

    @unittest.skipUnless(DIRECT_HOST, "generic object specialization executes on x86-64 Linux")
    def test_interface_object_specializes_list_element_relationship(self):
        td, root = self.make_project(
            'public function first(values) { return values[0]; }',
            'import lib; output(lib.first([10,20])); output(lib.first(["x","y"]));',
        )
        try:
            exe = root / "app"
            self.assertEqual(build_direct(root / "app.eri", exe, root), 0)
            p = subprocess.run([str(exe)], capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(p.stdout, "10\nx\n")
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
