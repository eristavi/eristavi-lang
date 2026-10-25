"""Diagnostic allocation statistics are accounting, not reachability or RSS."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


class HeapAccountingTests(unittest.TestCase):
    def exercise(self,flags):
        with tempfile.TemporaryDirectory() as td:
            binary=Path(td)/'accounting'
            built=subprocess.run([*shlex.split(os.environ.get('CC','cc')),'-std=c11','-O2',
                '-DERIST_HEAP_STATS',*flags,'-I',str(ROOT),str(ROOT/'tests/fixtures/heap_accounting.c'),
                '-lm','-o',str(binary)],capture_output=True,text=True,timeout=60)
            self.assertEqual(built.returncode,0,built.stderr)
            for mode in ('accounting','stress'):
                with self.subTest(mode=mode):
                    run=subprocess.run([str(binary),mode],capture_output=True,text=True,timeout=30)
                    self.assertEqual((run.returncode,run.stderr),(0,''))
                    reports=[json.loads(line) for line in run.stdout.splitlines()]
                    for report in reports:
                        self.assertEqual(report['format'],'eristavi-heap-stats-v1')
                        self.assertTrue(report['payload_bytes_only'] and report['registry_consistent'])
                        for name in ('allocations','reallocations','frees','live_allocations','live_bytes','requested_bytes'):
                            self.assertEqual(report['total'][name],sum(c[name] for c in report['categories'].values()))
                    self.assertEqual(reports[-1]['total']['live_bytes'],0)
                    self.assertEqual(reports[-1]['total']['live_allocations'],0)
                    if mode=='stress':
                        for kind in ('object','object_data','text','prefix_index','failure'):
                            self.assertGreater(reports[1]['categories'][kind]['live_bytes'],reports[0]['categories'][kind]['live_bytes'])
                        for kind in ('slot','scope','handler','unicode'):
                            self.assertEqual(reports[1]['categories'][kind]['live_bytes'],0)
            for mode in ('overflow','resize-overflow'):
                result=subprocess.run([str(binary),mode],capture_output=True,text=True,timeout=10)
                self.assertEqual((result.returncode,result.stdout,result.stderr),
                    (1,'','Eristavi runtime fault: allocation size overflow\n'))

    def test_heap_registry_categories_resizes_and_retained_value_stress(self):
        self.exercise([])

    def test_heap_accounting_under_address_and_undefined_sanitizers(self):
        self.exercise(['-fsanitize=address,undefined','-fno-sanitize-recover=all'])
