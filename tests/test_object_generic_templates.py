from __future__ import annotations

import platform
import subprocess
import tempfile
import unittest
from pathlib import Path

from compiler.erist.cli import build_direct, emit_interface, emit_object
from compiler.erist.direct_project import lower_direct_entry
from compiler.erist.object_artifact import ModuleObjectArtifact

DIRECT_HOST = platform.system() == "Linux" and platform.machine().lower() in ("x86_64", "amd64")


class GenericObjectTemplateTests(unittest.TestCase):
    def test_transitive_object_specializations_close_over_nested_and_private_calls(self):
        cases = [
            ('public function first(value) { return value; }',
             'import dep; public function answer() returns Int { return dep.first(42); }',
             'import lib; output(lib.answer());', '42\n'),
            ('public function first(value) { return value; }',
             'import dep; public function answer(value) { return dep.first(value); }',
             'import lib; output(lib.answer(42)); output(lib.answer("hello"));', '42\nhello\n'),
            ('function helper(value) { return value; } public function first(value) { return helper(value); }',
             'import dep; public function answer(value) { return dep.first(value); }',
             'import lib; output(lib.answer([1,2]).count);', '2\n'),
        ]
        # Lowering/verification is platform independent; no compiler invocation is
        # needed to detect missing specialization definitions or duplicate symbols.
        for dependency,library,application,expected in cases:
            with self.subTest(library=library,dependency=dependency), tempfile.TemporaryDirectory() as td:
                root=Path(td)
                dep=root/'dep.eri'; lib=root/'lib.eri'; app=root/'app.eri'
                dep.write_text(dependency);lib.write_text(library);app.write_text(application)
                for module in (dep,lib):
                    self.assertEqual(emit_interface(module,None,root),0)
                    self.assertEqual(emit_object(module,None,root),0)
                dep.unlink();lib.unlink()
                program=lower_direct_entry(app,root)
                names=[fn.name for fn in program.functions]
                self.assertEqual(len(names),len(set(names)))
                self.assertTrue(any(name.startswith('dep.first$') for name in names))
                if DIRECT_HOST:
                    executable=root/'application'
                    self.assertEqual(build_direct(app,executable,root),0)
                    result=subprocess.run([str(executable)],capture_output=True,text=True,timeout=10)
                    self.assertEqual((result.returncode,result.stdout,result.stderr),(0,expected,''))

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
