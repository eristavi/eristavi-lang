from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from compiler.erist.build_cache import ArtifactBuilder
from compiler.erist.interface import ModuleInterface


class BuildCacheTests(unittest.TestCase):
    def test_second_identical_compile_hits_cache(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            module = root / "lib.eri"
            module.write_text('public function answer() returns Int { return 42; }', encoding="utf-8")
            first = ArtifactBuilder(root).build_module(module)
            self.assertFalse(first.cache_hit)
            second = ArtifactBuilder(root).build_module(module)
            self.assertTrue(second.cache_hit)
            self.assertEqual(first.key, second.key)

    def test_source_change_invalidates_own_cache_key(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            module = root / "lib.eri"
            module.write_text('public function answer() returns Int { return 41; }', encoding="utf-8")
            first = ArtifactBuilder(root).build_module(module)
            module.write_text('public function answer() returns Int { return 42; }', encoding="utf-8")
            second = ArtifactBuilder(root).build_module(module)
            self.assertFalse(second.cache_hit)
            self.assertNotEqual(first.key, second.key)

    def test_private_dependency_change_does_not_invalidate_importer_contract_key(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            dep = root / "dep.eri"
            app = root / "lib.eri"
            dep.write_text(
                'function hidden() returns Int { return 1; } public function exposed() returns Int { return hidden(); }',
                encoding="utf-8",
            )
            app.write_text('import dep; public function value() returns Int { return dep.exposed(); }', encoding="utf-8")
            first = ArtifactBuilder(root).build_module(app)
            first_interface = ModuleInterface.from_json((root / "dep.eri-interface.json").read_text(encoding="utf-8"))
            dep.write_text(
                'function hidden() returns Int { return 2; } public function exposed() returns Int { return hidden(); }',
                encoding="utf-8",
            )
            second = ArtifactBuilder(root).build_module(app)
            second_interface = ModuleInterface.from_json((root / "dep.eri-interface.json").read_text(encoding="utf-8"))
            self.assertEqual(first_interface.digest, second_interface.digest)
            self.assertTrue(second.cache_hit)
            self.assertEqual(first.key, second.key)

    def test_public_dependency_change_invalidates_importer(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            dep = root / "dep.eri"
            app = root / "lib.eri"
            dep.write_text('public function exposed() returns Int { return 1; }', encoding="utf-8")
            app.write_text('import dep; public function value() returns Int { return dep.exposed(); }', encoding="utf-8")
            first = ArtifactBuilder(root).build_module(app)
            dep.write_text('public function exposed() returns Text { return "x"; }', encoding="utf-8")
            app.write_text('import dep; public function value() returns Text { return dep.exposed(); }', encoding="utf-8")
            second = ArtifactBuilder(root).build_module(app)
            self.assertFalse(second.cache_hit)
            self.assertNotEqual(first.key, second.key)


if __name__ == "__main__":
    unittest.main()
