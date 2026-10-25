"""Bound native administrative allocations without changing value ownership."""
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


class NativeRuntimeLifetimeTests(unittest.TestCase):
    def exercise(self,flags):
        with tempfile.TemporaryDirectory() as td:
            binary=Path(td)/'lifetimes'
            command=[*shlex.split(os.environ.get('CC','cc')),'-std=c11','-O2',*flags,
                     '-I',str(ROOT),str(ROOT/'tests/fixtures/native_unwind_lifetimes.c'),
                     '-lm','-o',str(binary)]
            built=subprocess.run(command,capture_output=True,text=True,timeout=60)
            self.assertEqual(built.returncode,0,built.stderr)
            for mode in ('normal','failure','resource'):
                with self.subTest(mode=mode):
                    result=subprocess.run([str(binary),mode],capture_output=True,text=True,timeout=30)
                    self.assertEqual((result.returncode,result.stdout,result.stderr),(0,'',''))

    def test_native_handler_and_abandoned_call_allocations_are_reclaimed(self):
        self.exercise([])

    def test_native_lifetimes_under_address_and_undefined_sanitizers(self):
        self.exercise(['-fsanitize=address,undefined','-fno-sanitize-recover=all'])
