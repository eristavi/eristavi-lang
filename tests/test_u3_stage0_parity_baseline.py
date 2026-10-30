"""Frozen Stage-0/native behavior baseline for the later U3 UIR migration.

No new UIR backend is exercised here: the goal is to preserve independent
observable behavior before the existing production lowering path is retired.
"""
from __future__ import annotations

import json
import platform
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from compiler.erist.cli import build_direct, build_native

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "tests/fixtures/semantic_cases.json"
CASES = {case["name"]: case for case in json.loads(CORPUS.read_text(encoding="utf-8"))}
NATIVE_NAMES = (
    "hello",
    "function_infer",
    "mutual_recursion",
    "list_value_semantics",
    "checked_handler",
)
DIRECT_NAMES = frozenset(("hello", "function_infer"))
DIRECT_HOST = platform.system() == "Linux" and platform.machine().lower() in ("x86_64", "amd64")


class U3Stage0ParityBaseline(unittest.TestCase):
    def test_frozen_successful_programs_match_existing_native_compilers(self):
        for name in NATIVE_NAMES:
            with self.subTest(case=name), tempfile.TemporaryDirectory() as temporary:
                case = CASES[name]
                self.assertTrue(case["accept"], name)
                root = Path(temporary)
                for relative, text in case["files"].items():
                    filename = root / relative
                    filename.parent.mkdir(parents=True, exist_ok=True)
                    filename.write_text(text, encoding="utf-8")
                entry = root / case["entry"]

                stage0 = subprocess.run(
                    [sys.executable, "-m", "compiler.erist", "run",
                     str(entry), "--source-root", str(root)],
                    cwd=ROOT, capture_output=True, text=True, timeout=90,
                )
                self.assertEqual(stage0.returncode, 0, (name, stage0.stderr))
                self.assertEqual(stage0.stderr, "", (name, stage0.stderr))

                executable = root / "native-c"
                self.assertEqual(build_native(entry, executable, root), 0, name)
                native = subprocess.run([str(executable)], capture_output=True,
                                        text=True, timeout=90)
                self.assertEqual(native.returncode, 0, (name, native.stderr))
                self.assertEqual((native.returncode, native.stdout),
                                 (stage0.returncode, stage0.stdout), name)

                if DIRECT_HOST and name in DIRECT_NAMES:
                    direct_binary = root / "native-direct"
                    self.assertEqual(build_direct(entry, direct_binary, root), 0, name)
                    direct = subprocess.run([str(direct_binary)], capture_output=True,
                                            text=True, timeout=90)
                    self.assertEqual(direct.returncode, 0, (name, direct.stderr))
                    self.assertEqual((direct.returncode, direct.stdout),
                                     (stage0.returncode, stage0.stdout), name)


if __name__ == "__main__":
    unittest.main()
