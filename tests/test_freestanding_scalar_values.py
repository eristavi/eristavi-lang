"""Focused checks for the freestanding Int/Bool ev_value helper ABI slice."""
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native

ROOT=Path(__file__).resolve().parents[1]
OVERFLOW=b'Eristavi runtime fault: Int arithmetic overflow\n'


@unittest.skipUnless(platform.system()=='Linux' and platform.machine().lower() in ('x86_64','amd64'),
                     'freestanding scalar value probes currently target Linux x86-64')
class FreestandingScalarValueTests(unittest.TestCase):
    def _build_probe(self, source_name: str, directory: Path):
        generator=directory/(source_name+'.generator')
        self.assertEqual(build_native(ROOT/'src'/source_name,generator,ROOT/'src'),0)
        generated=subprocess.run([str(generator)],capture_output=True,text=True,timeout=20)
        self.assertEqual((generated.returncode,generated.stderr),(0,''))
        source=generated.stdout
        assembly=directory/(source_name+'.s'); assembly.write_text(source)
        obj=directory/(source_name+'.o'); binary=directory/(source_name+'.bin')
        subprocess.run(['as','--64',str(assembly),'-o',str(obj)],check=True,capture_output=True,timeout=20)
        subprocess.run(['ld','-nostdlib','-static','-e','_start',str(obj),'-o',str(binary)],check=True,capture_output=True,timeout=20)
        headers=subprocess.check_output(['readelf','-lW',str(binary)],text=True)
        self.assertNotIn('INTERP',headers); self.assertNotIn('DYNAMIC',headers)
        self.assertEqual(subprocess.check_output(['nm','-u',str(binary)],text=True).strip(),'')
        return source,binary

    def test_scalar_value_helpers_allocate_copy_store_and_compute_without_c_runtime(self):
        for tool in ('as','ld','readelf','nm'):
            if not shutil.which(tool): self.skipTest(f'{tool} unavailable')
        with tempfile.TemporaryDirectory() as td:
            source,binary=self._build_probe('scalar_value_probe.eri',Path(td))
            for symbol in ('evn_int','evn_bool','evn_void','evn_copy','evn_store','evn_truth','evn_unary','evn_binary'):
                self.assertIn('.globl '+symbol,source)
            self.assertNotIn('@PLT',source)
            result=subprocess.run([str(binary)],env={'PATH':'/unavailable'},capture_output=True,timeout=10)
            self.assertEqual((result.returncode,result.stdout,result.stderr),(0,b'',b''))

    def test_scalar_value_overflow_uses_freestanding_fault_adapter(self):
        for tool in ('as','ld','readelf','nm'):
            if not shutil.which(tool): self.skipTest(f'{tool} unavailable')
        with tempfile.TemporaryDirectory() as td:
            source,binary=self._build_probe('scalar_value_fault_probe.eri',Path(td))
            self.assertNotIn('@PLT',source)
            result=subprocess.run([str(binary)],env={'PATH':'/unavailable'},capture_output=True,timeout=10)
            self.assertEqual(result.returncode,1)
            self.assertEqual(result.stdout,b'')
            self.assertEqual(result.stderr,OVERFLOW)


if __name__=='__main__': unittest.main()
