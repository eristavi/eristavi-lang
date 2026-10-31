"""Focused canonical U1b immutable aggregate SSA construction and verification.

The source fixture uses actual existing u1_builder.Function instruction tables.
This test DOES NOT claim canonical runtime execution, aggregate signature ABI,
full U1b final qualification or native code generation.
"""
from pathlib import Path
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native

ROOT = Path(__file__).resolve().parents[1]
LABELS = (
    "legacy-profile-rejected",
    "typed-aggregate-valid",
    "dead-aggregate-field",
    "dead-field-restored",
    "dead-aggregate-attribute",
    "aggregate-result-type",
    "aggregate-operand-type",
    "aggregate-source-location",
    "aggregate-records-restored",
    "malformed-aggregate-type-graph",
    "aggregate-graph-restored",
    "u1b-canonical-ssa-owners",
)
EXPECTED = "".join(f"{label}:ok\n" for label in LABELS)


class U1AggregateSSATests(unittest.TestCase):
    def test_canonical_aggregate_operations_and_independent_dead_code_verifier(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "compiler").symlink_to(
                ROOT / "src/compiler", target_is_directory=True
            )
            source = root / "aggregate_ssa.eri"
            source.write_text(
                (ROOT / "tests/fixtures/u1_aggregate_ssa.eri").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            binary = root / "aggregate_ssa"
            self.assertEqual(build_native(source, binary, root), 0)
            result = subprocess.run(
                [str(binary)], capture_output=True, text=True, timeout=120
            )
            self.assertEqual(
                (result.returncode, result.stdout, result.stderr), (0, EXPECTED, "")
            )


if __name__ == "__main__":
    unittest.main()
