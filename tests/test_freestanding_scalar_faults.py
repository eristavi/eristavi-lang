"""Focused proof that checked scalar defects reach libc-free Eristavi faults."""
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native

ROOT=Path(__file__).resolve().parents[1]
EXPECTED=b'Eristavi runtime fault: Int arithmetic overflow\n'


@unittest.skipUnless(platform.system()=='Linux' and platform.machine().lower() in ('x86_64','amd64'),
                     'freestanding scalar fault probe currently targets Linux x86-64')
class FreestandingScalarFaultTests(unittest.TestCase):
    def test_overflow_fault_writes_to_stderr_and_exits_without_libc(self):
        for tool in ('as','ld','readelf','nm'):
            if not shutil.which(tool): self.skipTest(f'{tool} unavailable')
        with tempfile.TemporaryDirectory() as td:
            directory=Path(td); generator=directory/'generator'
            self.assertEqual(build_native(ROOT/'src/scalar_fault_probe.eri',generator,ROOT/'src'),0)
            generated=subprocess.run([str(generator)],capture_output=True,text=True,timeout=20)
            self.assertEqual((generated.returncode,generated.stderr),(0,''))
            source=generated.stdout
            self.assertIn('erist_rt_write_all',source)
            self.assertIn('Eristavi runtime fault: Int division by zero',source)
            self.assertIn('Eristavi runtime fault: Int remainder by zero',source)
            self.assertNotIn('@PLT',source)
            assembly=directory/'probe.s'; assembly.write_text(source)
            obj=directory/'probe.o'; binary=directory/'probe'
            subprocess.run(['as','--64',str(assembly),'-o',str(obj)],check=True,capture_output=True,timeout=20)
            subprocess.run(['ld','-nostdlib','-static','-e','_start',str(obj),'-o',str(binary)],check=True,capture_output=True,timeout=20)
            headers=subprocess.check_output(['readelf','-lW',str(binary)],text=True)
            self.assertNotIn('INTERP',headers); self.assertNotIn('DYNAMIC',headers)
            self.assertEqual(subprocess.check_output(['nm','-u',str(binary)],text=True).strip(),'')
            result=subprocess.run([str(binary)],env={'PATH':'/unavailable'},capture_output=True,timeout=10)
            self.assertEqual(result.returncode,1)
            self.assertEqual(result.stdout,b'')
            self.assertEqual(result.stderr,EXPECTED)


if __name__=='__main__': unittest.main()
