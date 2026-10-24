from __future__ import annotations
import subprocess, tempfile, unittest
from pathlib import Path
from compiler.erist.cli import build_native

class BackendModuleTests(unittest.TestCase):
    def compile_project(self,files:dict[str,str],entry='app.eri'):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for name,source in files.items():
                path=root/name; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(source,encoding='utf-8')
            exe=root/'app'
            self.assertEqual(build_native(root/entry,exe,root),0)
            return subprocess.run([str(exe)],capture_output=True,text=True)

    def test_native_imported_public_function(self):
        p=self.compile_project({
            'math.eri':'public function double(value Int) returns Int { return value*2; }',
            'app.eri':'import math; output(math.double(21));',
        })
        self.assertEqual(p.returncode,0); self.assertEqual(p.stdout,'42\n')

    def test_native_imported_public_value_type(self):
        p=self.compile_project({
            'models/user.eri':'public type User { name Text; } public function make(name Text) returns User { return User { name=name; }; }',
            'app.eri':'import models.user; let u be user.make("Anna"); output(u.name);',
        })
        self.assertEqual(p.returncode,0); self.assertEqual(p.stdout,'Anna\n')

    def test_native_module_alias(self):
        p=self.compile_project({
            'services/math.eri':'public function value() returns Int { return 7; }',
            'app.eri':'import services.math as calc; output(calc.value());',
        })
        self.assertEqual(p.returncode,0); self.assertEqual(p.stdout,'7\n')

if __name__=='__main__': unittest.main()
