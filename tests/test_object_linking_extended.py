from __future__ import annotations

import platform
import subprocess
import tempfile
import unittest
from pathlib import Path

from compiler.erist.cli import build_direct, emit_interface, emit_object

DIRECT_HOST = platform.system() == "Linux" and platform.machine().lower() in ("x86_64", "amd64")


@unittest.skipUnless(DIRECT_HOST, "extended object linkage executes on x86-64 Linux")
class ExtendedObjectLinkingTests(unittest.TestCase):
    def build_artifact_project(self, library: str, app: str):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        module = root / "lib.eri"
        module.write_text(library, encoding="utf-8")
        (root / "app.eri").write_text(app, encoding="utf-8")
        self.assertEqual(emit_interface(module, None, root), 0)
        self.assertEqual(emit_object(module, None, root), 0)
        module.unlink()
        return td, root

    def compile_run(self, root: Path):
        exe = root / "app"
        self.assertEqual(build_direct(root / "app.eri", exe, root), 0)
        return subprocess.run([str(exe)], capture_output=True, text=True)

    def test_interface_object_link_supports_nominal_parameters_and_returns(self):
        td, root = self.build_artifact_project(
            'public type User { name Text; score Int; } '
            'public function promote(user User) returns User { user.score = user.score + 1; return user; }',
            'import lib; let original be lib.User { name="Anna"; score=5; }; '
            'let changed be lib.promote(original); '
            'output(original.score); output(changed.name); output(changed.score);',
        )
        try:
            p = self.compile_run(root)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(p.stdout, "5\nAnna\n6\n")
        finally:
            td.cleanup()

    def test_interface_object_link_supports_list_return(self):
        td, root = self.build_artifact_project(
            'public function pair(a Int, b Int) { return [a,b]; }',
            'import lib; let values be lib.pair(4,5); output(values.count); output(values[0] + values[1]);',
        )
        try:
            p = self.compile_run(root)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(p.stdout, "2\n9\n")
        finally:
            td.cleanup()

    def test_interface_object_link_preserves_checked_error_contract(self):
        td, root = self.build_artifact_project(
            'public error E { message Text; code Int; } '
            'public function risky() returns Int fails E { fail E { message="object failure"; code=12; }; }',
            'import lib; lib.risky() else error lib.E { output(error.message); output(error.code); };',
        )
        try:
            p = self.compile_run(root)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(p.stdout, "object failure\n12\n")
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
