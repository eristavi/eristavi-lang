from __future__ import annotations
import subprocess, tempfile, unittest
from pathlib import Path
from compiler.erist.cli import build_native

class BackendErrorTests(unittest.TestCase):
    def compile_run(self,source:str):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); src=root/'app.eri'; exe=root/'app'
            src.write_text(source,encoding='utf-8')
            self.assertEqual(build_native(src,exe,root),0)
            return subprocess.run([str(exe)],capture_output=True,text=True)

    def test_native_catch_all_handler(self):
        src='error E { message Text; code Int; } function risky() returns Int fails E { fail E { message="bad"; code=7; }; } function run(){ let x be risky() else error { output(error.message); return; }; output(x); } run();'
        p=self.compile_run(src); self.assertEqual(p.returncode,0); self.assertEqual(p.stdout,'bad\n')

    def test_native_typed_handler_fields(self):
        src='error E { message Text; code Int; } function risky() returns Int fails E { fail E { message="bad"; code=42; }; } risky() else error E { output(error.message); output(error.code); };'
        p=self.compile_run(src); self.assertEqual(p.returncode,0); self.assertEqual(p.stdout,'bad\n42\n')

    def test_native_try_propagation(self):
        src='error E { message Text; } function risky() returns Int fails E { fail E { message="deep"; }; } function outer() returns Int fails E { return try risky(); } outer() else error { output(error.message); };'
        p=self.compile_run(src); self.assertEqual(p.returncode,0); self.assertEqual(p.stdout,'deep\n')

    def test_native_handler_selects_error_type(self):
        src='error A { message Text; } error B { message Text; code Int; } function risky(which Bool) returns Int fails A,B { if which { fail A { message="A"; }; } fail B { message="B"; code=9; }; } function show(which Bool){ risky(which) else error A { output("caught A"); } else error B { output(error.message); output(error.code); }; } show(true); show(false);'
        p=self.compile_run(src); self.assertEqual(p.returncode,0); self.assertEqual(p.stdout,'caught A\nB\n9\n')

    def test_native_success_bypasses_handler(self):
        src='error E { message Text; } function value(ok Bool) returns Int fails E { if ok { return 7; } fail E { message="no"; }; } let x be value(true) else error { output("failure"); }; output(x);'
        p=self.compile_run(src); self.assertEqual(p.returncode,0); self.assertEqual(p.stdout,'7\n')

    def test_native_nested_handler_propagates_from_handler(self):
        src='error E { message Text; } function bad(message Text) returns Int fails E { fail E { message=message; }; } function middle() returns Int fails E { return bad("second") else error E { return try bad("third"); }; } middle() else error { output(error.message); };'
        p=self.compile_run(src); self.assertEqual(p.returncode,0); self.assertEqual(p.stdout,'third\n')

if __name__=='__main__': unittest.main()
