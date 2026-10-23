from __future__ import annotations
import subprocess, tempfile, unittest
from pathlib import Path
from compiler.erist.cli import build_native, build_c_file

class BackendTests(unittest.TestCase):
    def compile_run(self,source):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); src=root/'app.eri'; exe=root/'app'; src.write_text(source,encoding='utf-8')
            self.assertEqual(build_native(src,exe,root),0)
            return subprocess.run([str(exe)],capture_output=True,text=True)
    def test_native_hello(self):
        p=self.compile_run('let x be 40; let y be 2; output(x+y);'); self.assertEqual(p.returncode,0); self.assertEqual(p.stdout,'42\n')
    def test_native_function_recursion(self):
        p=self.compile_run('function f(n Int) returns Int { if n<=1 { return 1; } return n*f(n-1); } output(f(5));'); self.assertEqual(p.stdout,'120\n')
    def test_native_while(self):
        p=self.compile_run('let i be 0; while i<3 { output(i); i=i+1; }'); self.assertEqual(p.stdout,'0\n1\n2\n')
    def test_native_checked_int_fault(self):
        p=self.compile_run('let x be 9223372036854775807; output(x+1);'); self.assertNotEqual(p.returncode,0); self.assertIn('Int overflow',p.stderr)
    def test_native_text_equality(self):
        p=self.compile_run('output("a"=="a"); output("a"!="b");'); self.assertEqual(p.stdout,'true\ntrue\n')
    def test_native_text_escape(self):
        p=self.compile_run('output("A\\nB");'); self.assertEqual(p.stdout,'A\nB\n')
    def test_native_unicode_identifier(self):
        p=self.compile_run('let τιμή be 42; output(τιμή);'); self.assertEqual(p.stdout,'42\n')
    def test_build_c_emits_source(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td); src=r/'app.eri'; out=r/'app.c'; src.write_text('output(42);',encoding='utf-8'); self.assertEqual(build_c_file(src,out,r),0); self.assertIn('int main',out.read_text())
if __name__=='__main__': unittest.main()
