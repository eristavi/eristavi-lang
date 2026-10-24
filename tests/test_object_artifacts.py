from __future__ import annotations

import platform
import subprocess
import tempfile
import unittest
from pathlib import Path

from compiler.erist.cli import build_direct, emit_interface, emit_object
from compiler.erist.object_artifact import ModuleObjectArtifact

DIRECT_HOST = platform.system() == "Linux" and platform.machine().lower() in ("x86_64", "amd64")


class ObjectArtifactTests(unittest.TestCase):
    def project(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "lib.eri").write_text(
            "public function double(value Int) returns Int { return value * 2; }",
            encoding="utf-8",
        )
        (root / "app.eri").write_text(
            "import lib; output(lib.double(21));",
            encoding="utf-8",
        )
        return td, root

    def test_object_is_versioned_deterministic_and_bound_to_interface(self):
        td, root = self.project()
        try:
            module = root / "lib.eri"
            self.assertEqual(emit_interface(module, None, root), 0)
            self.assertEqual(emit_object(module, None, root), 0)
            path = root / "lib.eri-object.json"
            first = path.read_text(encoding="utf-8")
            artifact = ModuleObjectArtifact.from_json(first)
            self.assertEqual(artifact.module_id, "lib")
            self.assertEqual(first, artifact.to_json())
            self.assertEqual(len(artifact.digest), 64)
            self.assertEqual([fn.name for fn in artifact.functions], ["lib.double"])
        finally:
            td.cleanup()

    @unittest.skipUnless(DIRECT_HOST, "direct object linkage executes on x86-64 Linux")
    def test_direct_build_links_object_after_module_source_is_removed(self):
        td, root = self.project()
        try:
            module = root / "lib.eri"
            self.assertEqual(emit_interface(module, None, root), 0)
            self.assertEqual(emit_object(module, None, root), 0)
            module.unlink()
            exe = root / "app"
            self.assertEqual(build_direct(root / "app.eri", exe, root), 0)
            p = subprocess.run([str(exe)], capture_output=True, text=True)
            self.assertEqual(p.returncode, 0)
            self.assertEqual(p.stdout, "42\n")
        finally:
            td.cleanup()

    def test_interface_object_digest_mismatch_is_rejected(self):
        td, root = self.project()
        try:
            module = root / "lib.eri"
            self.assertEqual(emit_interface(module, None, root), 0)
            self.assertEqual(emit_object(module, None, root), 0)
            interface = root / "lib.eri-interface.json"
            # Change metadata that preserves the callable public contract from the
            # importer's point of view, so validation reaches the object/interface
            # digest check instead of failing name resolution earlier.
            text = interface.read_text(encoding="utf-8").replace('"name":"value"', '"name":"renamed"')
            interface.write_text(text, encoding="utf-8")
            module.unlink()
            with self.assertRaises(ValueError):
                from compiler.erist.direct_project import lower_direct_entry
                lower_direct_entry(root / "app.eri", root)
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
