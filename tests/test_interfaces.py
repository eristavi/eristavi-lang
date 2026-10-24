from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from compiler.erist.diagnostics import SemanticError
from compiler.erist.interface import INTERFACE_SCHEMA, INTERFACE_VERSION, ModuleInterface
from compiler.erist.project import ProjectCompiler, compile_entry, compile_module


class InterfaceTests(unittest.TestCase):
    def project(self, files):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        for name, text in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        return td, root

    def test_interface_is_versioned_deterministic_and_hides_private_functions(self):
        td, root = self.project({
            "models/user.eri": (
                "public type User { fixed id Int; name Text; } "
                "function secret() returns Int { return 7; } "
                "public function identity(value) { return value; }"
            )
        })
        try:
            mod = compile_module(root / "models/user.eri", root)
            text1 = mod.interface.to_json()
            text2 = ModuleInterface.from_json(text1).to_json()
            self.assertEqual(text1, text2)
            self.assertEqual(mod.interface.schema, INTERFACE_SCHEMA)
            self.assertEqual(mod.interface.version, INTERFACE_VERSION)
            self.assertIsNone(mod.interface.function("secret"))
            self.assertIsNotNone(mod.interface.function("identity"))
            self.assertEqual(len(mod.interface.digest), 64)
        finally:
            td.cleanup()

    def test_source_independent_check_uses_interface_type_and_generic_contract(self):
        td, root = self.project({
            "models/user.eri": (
                "public type User { name Text; } "
                "public function identity(value) { return value; }"
            ),
            "app.eri": (
                "import models.user; "
                "let user be user.User { name=\"Anna\"; }; "
                "let n be user.identity(42); "
                "output(user.name); output(n);"
            ),
        })
        try:
            module_path = root / "models/user.eri"
            compiled = compile_module(module_path, root)
            ProjectCompiler.interface_path(module_path).write_text(compiled.interface.to_json(), encoding="utf-8")
            module_path.unlink()
            entry = compile_entry(root / "app.eri", root)
            self.assertTrue(entry.imports["user"].interface_only)
            self.assertEqual(entry.imports["user"].interface.module_id, "models.user")
        finally:
            td.cleanup()

    def test_interface_preserves_checked_error_contract(self):
        td, root = self.project({
            "service.eri": (
                "public error ServiceError { message Text; code Int; } "
                "public function risky() returns Int fails ServiceError { "
                "fail ServiceError { message=\"bad\"; code=500; }; }"
            ),
            "app.eri": (
                "import service; "
                "let value be service.risky() else error service.ServiceError { return; }; "
                "output(value);"
            ),
        })
        try:
            module_path = root / "service.eri"
            compiled = compile_module(module_path, root)
            ProjectCompiler.interface_path(module_path).write_text(compiled.interface.to_json(), encoding="utf-8")
            module_path.unlink()
            compile_entry(root / "app.eri", root)
        finally:
            td.cleanup()

    def test_private_function_remains_unavailable_from_interface(self):
        td, root = self.project({
            "lib.eri": "function hidden() returns Int { return 1; } public function shown() returns Int { return 2; }",
            "app.eri": "import lib; output(lib.hidden());",
        })
        try:
            module_path = root / "lib.eri"
            compiled = compile_module(module_path, root)
            ProjectCompiler.interface_path(module_path).write_text(compiled.interface.to_json(), encoding="utf-8")
            module_path.unlink()
            with self.assertRaises(SemanticError):
                compile_entry(root / "app.eri", root)
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
