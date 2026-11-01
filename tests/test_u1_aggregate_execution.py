"""Canonical verified UIR aggregate execution, not the separate value-only oracle."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from compiler.erist.cli import build_native
ROOT = Path(__file__).resolve().parents[1]
class U1AggregateExecutionTests(unittest.TestCase):
    def test_verified_canonical_ssa_immutable_execution(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            (root/"compiler").symlink_to(ROOT/"src/compiler",target_is_directory=True)
            source=root/"aggregate_execution.eri"
            source.write_text((ROOT/"tests/fixtures/u1_aggregate_execution.eri").read_text(encoding="utf-8"),encoding="utf-8")
            target=root/"aggregate_execution"
            self.assertEqual(build_native(source,target,root),0)
            completed=subprocess.run([str(target)],capture_output=True,text=True,timeout=120)
            self.assertEqual((completed.returncode,completed.stdout,completed.stderr),(0,"canonical-u1b-execution:11,17:ok\n",""))
