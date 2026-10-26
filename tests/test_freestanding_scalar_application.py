"""End-to-end proof: Eristavi compiler modules -> x86 app -> Eristavi-owned scalar runtime."""
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native

ROOT=Path(__file__).resolve().parents[1]


@unittest.skipUnless(platform.system()=='Linux' and platform.machine().lower() in ('x86_64','amd64'),
                     'freestanding scalar application proof currently targets Linux x86-64')
class FreestandingScalarApplicationTests(unittest.TestCase):
    def test_real_eri_program_runs_without_c_runtime(self):
        for tool in ('as','ld','readelf','nm'):
            if not shutil.which(tool): self.skipTest(f'{tool} unavailable')
        with tempfile.TemporaryDirectory() as td:
            directory=Path(td)
            frontend=directory/'erist-frontend'
            runtime_generator=directory/'runtime-generator'
            self.assertEqual(build_native(ROOT/'src/frontend.eri',frontend,ROOT/'src'),0)
            self.assertEqual(build_native(ROOT/'src/scalar_application_runtime.eri',runtime_generator,ROOT/'src'),0)

            source_path=ROOT/'examples/freestanding_scalar_application.eri'
            compiled=subprocess.run([str(frontend),'emit-asm',str(source_path)],capture_output=True,text=True,timeout=30)
            self.assertEqual((compiled.returncode,compiled.stderr),(0,''))
            app_assembly=compiled.stdout
            self.assertIn('.globl erist_entry',app_assembly)
            self.assertIn('call evn_scope_enter@PLT',app_assembly)
            self.assertIn('call evn_output@PLT',app_assembly)

            emitted_runtime=subprocess.run([str(runtime_generator)],capture_output=True,text=True,timeout=20)
            self.assertEqual((emitted_runtime.returncode,emitted_runtime.stderr),(0,''))
            runtime_assembly=emitted_runtime.stdout
            self.assertIn('.globl evn_output',runtime_assembly)
            self.assertIn('.globl evn_scope_leave',runtime_assembly)
            self.assertNotIn('write@PLT',runtime_assembly)
            self.assertNotIn('exit@PLT',runtime_assembly)

            assembly=directory/'application.s'
            assembly.write_text(app_assembly+'\n'+runtime_assembly)
            obj=directory/'application.o'; binary=directory/'application'
            subprocess.run(['as','--64',str(assembly),'-o',str(obj)],check=True,capture_output=True,timeout=20)
            subprocess.run(['ld','-nostdlib','-static','-e','_start',str(obj),'-o',str(binary)],check=True,capture_output=True,timeout=20)
            headers=subprocess.check_output(['readelf','-lW',str(binary)],text=True)
            self.assertNotIn('INTERP',headers)
            self.assertNotIn('DYNAMIC',headers)
            stack=next(line for line in headers.splitlines() if 'GNU_STACK' in line)
            self.assertNotIn('RWE',stack)
            self.assertEqual(subprocess.check_output(['nm','-u',str(binary)],text=True).strip(),'')

            result=subprocess.run([str(binary)],env={'PATH':'/unavailable'},capture_output=True,timeout=10)
            self.assertEqual(result.returncode,0)
            self.assertEqual(result.stdout,b'42\nfalse\n')
            self.assertEqual(result.stderr,b'')


if __name__=='__main__': unittest.main()
