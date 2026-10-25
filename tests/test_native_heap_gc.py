"""Native heap tracing must preserve live Eristavi values and reclaim dead graphs."""
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


class NativeHeapGCTests(unittest.TestCase):
    def exercise(self,flags):
        with tempfile.TemporaryDirectory() as td:
            binary=Path(td)/'native-heap-gc'
            command=[*shlex.split(os.environ.get('CC','cc')),'-std=c11','-O2',*flags,
                '-I',str(ROOT),str(ROOT/'tests/fixtures/native_heap_gc.c'),'-lm','-o',str(binary)]
            built=subprocess.run(command,capture_output=True,text=True,timeout=90)
            self.assertEqual(built.returncode,0,built.stderr)
            run=subprocess.run([str(binary)],capture_output=True,text=True,timeout=60)
            self.assertEqual((run.returncode,run.stdout,run.stderr),(0,'',''))

    def test_typed_native_gc_preserves_roots_cycles_failures_and_weak_prefixes(self):
        self.exercise([])

    def test_typed_native_gc_under_address_and_undefined_sanitizers(self):
        self.exercise(['-fsanitize=address,undefined','-fno-sanitize-recover=all'])
