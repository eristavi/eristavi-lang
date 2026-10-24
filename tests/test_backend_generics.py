from __future__ import annotations
import subprocess, tempfile, unittest
from pathlib import Path
from compiler.erist.cli import build_native

class BackendGenericTests(unittest.TestCase):
    def compile_run(self,source:str):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); src=root/'app.eri'; exe=root/'app'
            src.write_text(source,encoding='utf-8')
            self.assertEqual(build_native(src,exe,root),0)
            return subprocess.run([str(exe)],capture_output=True,text=True)

    def test_native_preserve_specializes_for_multiple_types(self):
        p=self.compile_run('function preserve(value) { return value; } output(preserve(42)); output(preserve("hello"));')
        self.assertEqual(p.returncode,0); self.assertEqual(p.stdout,'42\nhello\n')

    def test_native_choose_infers_same_type_relationship(self):
        p=self.compile_run('function choose(first, second, pick Bool) { if pick { return first; } return second; } output(choose(10,20,true)); output(choose("A","B",false));')
        self.assertEqual(p.returncode,0); self.assertEqual(p.stdout,'10\nB\n')

    def test_native_generic_operation_constraints(self):
        p=self.compile_run('function double(value) { return value+value; } output(double(21)); output(double(1.5)); output(double("A"));')
        self.assertEqual(p.returncode,0); self.assertEqual(p.stdout,'42\n3\nAA\n')

    def test_native_generic_list_element_relationship(self):
        p=self.compile_run('function first(items) { return items[0]; } output(first([10,20])); output(first(["Anna","Maria"]));')
        self.assertEqual(p.returncode,0); self.assertEqual(p.stdout,'10\nAnna\n')

    def test_native_generic_user_value(self):
        p=self.compile_run('type User { name Text; } function same(value) { return value; } let u be same(User { name="Anna"; }); output(u.name);')
        self.assertEqual(p.returncode,0); self.assertEqual(p.stdout,'Anna\n')

if __name__=='__main__': unittest.main()
