"""U1a local FunctionId body-binding and independent verifier acceptance tests."""
from pathlib import Path
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = ''.join(label + ":ok\n" for label in (
    "signature-mismatch",
    "foreign-function-id",
    "import-not-definition",
    "forward-and-mutual-calls",
    "duplicate-definition",
    "incomplete-module",
    "all-definitions-verified",
    "import-unresolved",
    "no-binding-after-seal",
    "stale-revision",
    "no-budget-leaks",
))


class U1ModuleBindingTests(unittest.TestCase):
    def test_declarations_bind_exact_verified_bodies(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "compiler").symlink_to(
                ROOT / "src/compiler", target_is_directory=True
            )
            source = root / "module.eri"
            source.write_text(
                (ROOT / "tests/fixtures/u1_module.eri").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            binary = root / "module"
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
