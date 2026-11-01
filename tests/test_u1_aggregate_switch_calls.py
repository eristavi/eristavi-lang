"""Independent linked sparse-switch and simultaneous aggregate swap oracle."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from compiler.erist.cli import build_native
ROOT = Path(__file__).resolve().parents[1]

class U1AggregateSwitchCallTests(unittest.TestCase):
    def test_linked_sparse_switch_and_aggregate_backedge_swap(self):
        cases = {0: 10, (1 << 63)-1: 20, -(1 << 63): 30}
        expected = []
        for selector in (0, (1 << 63)-1, -(1 << 63), 1, -1):
            left, right = (cases.get(selector, 40),)*2, (100, 100)
            left, right = right, left
            expected.extend((left[0], right[0]))
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root/'compiler').symlink_to(ROOT/'src/compiler', target_is_directory=True)
            source = root/'switch.eri'
            source.write_text((ROOT/'tests/fixtures/u1_aggregate_switch_calls.eri').read_text())
            binary = root/'switch'
            self.assertEqual(build_native(source, binary, root), 0)
            result = subprocess.run([str(binary)],capture_output=True,text=True,timeout=120)
            self.assertEqual((result.returncode,result.stdout,result.stderr),
                             (0,''.join(f'{n}\n' for n in expected),''))

            # Negative control: intentionally overwrite each destination while
            # still collecting source arguments. The independent swap oracle
            # must detect the resulting lost original value.
            (root/'compiler').unlink()
            (root/'compiler').mkdir()
            for item in (ROOT/'src/compiler').iterdir():
                (root/'compiler'/item.name).symlink_to(item)
            executor = (ROOT/'src/compiler/u1_aggregate_calls.eri').read_text()
            anchor = "let token be try get(frame,source);\n                if ordinal == frame.scratch.length"
            self.assertEqual(executor.count(anchor), 1)
            broken = executor.replace(anchor,
                "let token be try get(frame,source);\n"
                "                try put(frame,destination+ordinal,token);\n"
                "                if ordinal == frame.scratch.length")
            target = root/'compiler/u1_aggregate_calls.eri'
            target.unlink()
            target.write_text(broken)
            self.assertEqual(build_native(source, binary, root), 0)
            wrong = subprocess.run([str(binary)],capture_output=True,text=True,timeout=120)
            self.assertEqual((wrong.returncode,wrong.stderr),(0,''))
            self.assertNotEqual(wrong.stdout,result.stdout)
