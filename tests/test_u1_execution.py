"""Independent U1a call/effect/import execution acceptance on the real Eristavi runtime."""
from pathlib import Path
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = ''.join(line + ':ok\n' for line in (
    "wrong-import-adapter",
    "stale-import-version",
    "untrusted-import-effects",
    "missing-trusted-import",
    "understated-effect-bound",
    "recursive-scc-effects",
    "trusted-versioned-imports",
    "bounded-mutual-recursion",
    "multiresult-calls",
    "zeroresult-import-trace",
    "first-effect-and-fault-location",
    "bounded-divergence",
    "stale-import-after-freeze",
    "stale-body-revision",
    "recovered-budgets",
))


class U1CallExecutionTests(unittest.TestCase):
    def test_recursive_frames_effects_and_versioned_imports(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "compiler").symlink_to(
                ROOT / "src/compiler", target_is_directory=True
            )
            source = root / "execution.eri"
            source.write_text(
                (ROOT / "tests/fixtures/u1_execution.eri").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            binary = root / "execution"
            self.assertEqual(build_native(source, binary, root), 0)
            result = subprocess.run(
                [str(binary)], capture_output=True, text=True, timeout=120
            )
            self.assertEqual(
                (result.returncode, result.stdout, result.stderr),
                (0, EXPECTED, ""),
            )


if __name__ == "__main__":
    unittest.main()
