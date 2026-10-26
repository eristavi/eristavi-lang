"""Focused checks for the private freestanding memory-layout/allocator slice."""
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native

ROOT=Path(__file__).resolve().parents[1]


@unittest.skipUnless(platform.system()=='Linux' and platform.machine().lower() in ('x86_64','amd64'),
                     'freestanding allocator currently targets Linux x86-64')
class InternalMemoryAllocatorTests(unittest.TestCase):
    def test_allocator_is_freestanding_aligned_reusable_and_releasable(self):
        for tool in ('as','ld','readelf','nm'):
            if not shutil.which(tool):
                self.skipTest(f'{tool} unavailable')
        with tempfile.TemporaryDirectory() as td:
            directory=Path(td)
            generator=directory/'allocator-generator'
            self.assertEqual(build_native(ROOT/'src/allocator_probe.eri',generator,ROOT/'src'),0)
            generated=subprocess.run([str(generator)],capture_output=True,text=True,timeout=20)
            self.assertEqual((generated.returncode,generated.stderr),(0,''))
            self.assertIn('erist_rt_alloc',generated.stdout)
            self.assertIn('erist_rt_free',generated.stdout)
            self.assertIn('erist_rt_allocator_release_all',generated.stdout)
            for forbidden in ('malloc@','free@','calloc@','realloc@','memcpy@','libc'):
                self.assertNotIn(forbidden,generated.stdout)

            assembly=directory/'allocator.s'
            assembly.write_text(generated.stdout)
            obj=directory/'allocator.o'
            binary=directory/'allocator-probe'
            subprocess.run(['as','--64',str(assembly),'-o',str(obj)],check=True,capture_output=True,timeout=20)
            subprocess.run(['ld','-nostdlib','-static','-e','_start',str(obj),'-o',str(binary)],
                           check=True,capture_output=True,timeout=20)

            headers=subprocess.check_output(['readelf','-lW',str(binary)],text=True)
            self.assertNotIn('INTERP',headers)
            self.assertNotIn('DYNAMIC',headers)
            stack=next(line for line in headers.splitlines() if 'GNU_STACK' in line)
            self.assertNotIn('RWE',stack)
            self.assertEqual(subprocess.check_output(['nm','-u',str(binary)],text=True).strip(),'')

            result=subprocess.run([str(binary)],env={'PATH':'/unavailable'},capture_output=True,timeout=10)
            self.assertEqual((result.returncode,result.stdout,result.stderr),(0,b'',b''))


if __name__=='__main__':
    unittest.main()
