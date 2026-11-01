"""Typed self-loop UIR aggregate oracle and original-LocId fuel refusal.

The expected output is calculated independently with immutable Python tuples.
This tests a repeatedly executed SSA definition and parallel backedge arguments;
it does not qualify multi-function aggregate calls, U2, or native UIR lowering.
"""
from pathlib import Path
import subprocess
import tempfile
import unittest
from compiler.erist.cli import build_native

ROOT=Path(__file__).resolve().parents[1]


class U1AggregateLoopTests(unittest.TestCase):
    def test_canonical_aggregate_loop_reentry_and_fuel(self):
        original=(11,11)
        state=original
        for _ in range(2):
            state=state[:1]+(17,)
        oracle=f"{original[1]}\n{state[1]}\nu1b-aggregate-loop:ok\n"
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"compiler").symlink_to(ROOT/"src/compiler",target_is_directory=True)
            src=root/"aggregate_loop.eri"
            src.write_text((ROOT/"tests/fixtures/u1_aggregate_loops.eri").read_text(encoding="utf-8"),encoding="utf-8")
            target=root/"aggregate_loop"
            self.assertEqual(build_native(src,target,root),0)
            result=subprocess.run([str(target)],capture_output=True,text=True,timeout=120,check=False)
            self.assertEqual((result.returncode,result.stdout,result.stderr),(0,oracle,""))
