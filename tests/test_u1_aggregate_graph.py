"""Focused U1b opt-in aggregate graph and independent verification.

This validates an isolated metadata sidecar only. It does NOT certify full U1b
aggregate make/get/set execution, canonical production integration, or U2.
"""
from pathlib import Path
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = (
    "canonical-and-physical-owner:ok\n"
    "cycle-rejection:ok\n"
    "bucket-rejection:ok\n"
    "duplicate-rejection:ok\n"
)


class U1AggregateTypeGraphTests(unittest.TestCase):
    def test_native_owned_type_graph_and_independent_verifier(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "compiler").symlink_to(ROOT / "src/compiler", target_is_directory=True)
            source = root / "aggregate.eri"
            source.write_text((ROOT / "tests/fixtures/u1_aggregate_graph.eri").read_text(encoding="utf-8"), encoding="utf-8")
            target = root / "aggregate"
            self.assertEqual(build_native(source, target, root), 0)
            process = subprocess.run(
                [str(target)], capture_output=True, text=True, timeout=120, check=False
            )
            self.assertEqual((process.returncode, process.stdout, process.stderr), (0, EXPECTED, ""))


if __name__ == "__main__":
    unittest.main()
