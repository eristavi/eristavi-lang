"""Opt-in immutable aggregate signatures, typed CFG and canonical SSA promotion.

An independently verified construction and reverified promoted output is
required; this test is not aggregate function-call runtime qualification.
"""
from pathlib import Path
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native

ROOT=Path(__file__).resolve().parents[1]


class U1AggregateSignatureTests(unittest.TestCase):
    def test_canonical_aggregate_signature_cfg_and_promotion(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/"compiler").symlink_to(ROOT/"src/compiler",target_is_directory=True)
            source=root/"aggregate_signature.eri"
            source.write_text((ROOT/"tests/fixtures/u1_aggregate_signatures.eri").read_text(encoding="utf-8"),encoding="utf-8")
            exe=root/"aggregate_signature"
            self.assertEqual(build_native(source,exe,root),0)
            completed=subprocess.run([str(exe)],capture_output=True,text=True,timeout=120,check=False)
            self.assertEqual((completed.returncode,completed.stdout,completed.stderr),
                             (0,"aggregate-signature-promotion:ok\n",""))
