"""Verified canonical checked File.close preserves managed carrier on both SSA edges.

This runs the real Eristavi owned canonical verifier (including unreachable
instructions) but does not claim full native identity/FailureContext lowering.
"""
from pathlib import Path
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native

ROOT=Path(__file__).resolve().parents[1]


class U2CheckedIdentitySSATests(unittest.TestCase):
    def test_canonical_identity_carries_and_wrong_source_refusals(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder=Path(temporary)
            (folder/'compiler').symlink_to(ROOT/'src/compiler',
                                          target_is_directory=True)
            source=ROOT/'tests/fixtures/u2_checked_identity_ssa.eri'
            binary=folder/'checked-identity-ssa'
            self.assertEqual(build_native(source,binary,folder),0)
            run=subprocess.run([str(binary)],capture_output=True,
                               text=True,timeout=120)
            self.assertEqual((run.returncode,run.stdout,run.stderr),
                             (0,'u2-identity-checked-ssa:ok\\n',''))
