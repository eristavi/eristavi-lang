"""Focused source-level regression for U2 ordered checked cleanup failures."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from compiler.erist.cli import build_native

ROOT = Path(__file__).resolve().parents[1]

class U2FailureOrderTests(unittest.TestCase):
    def test_primary_and_ordered_cleanup_failures(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "compiler").symlink_to(ROOT / "src/compiler", target_is_directory=True)
            source = root / "probe.eri"
            source.write_text((ROOT / "tests/fixtures/u2_failure_order.eri").read_text())
            binary = root / "probe"
            self.assertEqual(build_native(source, binary, root), 0)
            result = subprocess.run([str(binary)], capture_output=True, text=True, timeout=120)
            self.assertEqual((result.returncode, result.stdout, result.stderr),
                             (0, "u2-failure-order:ok\n", ""))
