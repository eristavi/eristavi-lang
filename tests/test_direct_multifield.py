from __future__ import annotations

import platform
import subprocess
import tempfile
import unittest
from pathlib import Path

from compiler.erist.cli import build_direct

DIRECT_HOST = platform.system() == "Linux" and platform.machine().lower() in ("x86_64", "amd64")


@unittest.skipUnless(DIRECT_HOST, "direct multi-field execution currently targets x86-64 Linux")
class DirectMultiFieldTests(unittest.TestCase):
    def test_local_two_field_value_preserves_declared_layout(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "app.eri"
            exe = root / "app"
            src.write_text(
                'type User { name Text; score Int; } '
                'let user be User { name="Anna"; score=5; }; '
                'output(user.score); output(user.name);',
                encoding="utf-8",
            )
            self.assertEqual(build_direct(src, exe, root), 0)
            p = subprocess.run([str(exe)], capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(p.stdout, "5\nAnna\n")


if __name__ == "__main__":
    unittest.main()
