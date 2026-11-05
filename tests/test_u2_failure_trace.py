"""Canonical plan -> typed checked-failure reference semantics, bounded 3-owner matrix."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from compiler.erist.cli import build_native
ROOT=Path(__file__).resolve().parents[1]
class U2FailureTraceTests(unittest.TestCase):
    def test_three_owner_primary_and_ordered_secondary_matrix(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            (root/'compiler').symlink_to(ROOT/'src/compiler',target_is_directory=True)
            source=root/'trace.eri'
            source.write_text((ROOT/'tests/fixtures/u2_failure_trace.eri').read_text())
            binary=root/'trace'
            self.assertEqual(build_native(source,binary,root),0)
            outcome=subprocess.run([str(binary)],text=True,capture_output=True,timeout=120)
            self.assertEqual((outcome.returncode,outcome.stdout,outcome.stderr),
                             (0,'u2-failure-trace:ok\n',''))
