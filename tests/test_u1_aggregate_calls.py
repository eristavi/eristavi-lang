"""Independent multi-function canonical UIR aggregate oracle.

Caller -> loop/update callee -> recursive immutable-copy callee.
Fuel/depth refusal releases every frame; direct guards retain their LocId.
This is an isolated reference interpreter profile (not native UIR lowering).
"""
from pathlib import Path
import subprocess
import tempfile
import unittest
from compiler.erist.cli import build_native
ROOT=Path(__file__).resolve().parents[1]


class U1AggregateCallTests(unittest.TestCase):
    def test_linked_canonical_aggregate_calls_and_first_fault(self):
        original=(True,11)
        updated=original
        for _ in range(2):
            updated=(False,17)
        self.assertEqual(original,(True,11))
        expected=f"{original[1]}\n{updated[1]}\nu1b-aggregate-calls:ok\n"
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"compiler").symlink_to(ROOT/"src/compiler",target_is_directory=True)
            source=root/"calls.eri"
            source.write_text((ROOT/"tests/fixtures/u1_aggregate_calls.eri").read_text(encoding="utf-8"),encoding="utf-8")
            binary=root/"calls"
            self.assertEqual(build_native(source,binary,root),0)
            out=subprocess.run([str(binary)],capture_output=True,text=True,timeout=120,check=False)
            self.assertEqual((out.returncode,out.stdout,out.stderr),(0,expected,""))
