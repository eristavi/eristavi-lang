from __future__ import annotations
import subprocess, tempfile, unittest
from pathlib import Path
from compiler.erist.cli import build_native

class BackendResourceTests(unittest.TestCase):
    def compile_run(self,source_builder,files:dict[str,str]|None=None):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for name,text in (files or {}).items():
                p=root/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text,encoding='utf-8')
            source=source_builder(root)
            src=root/'app.eri'; exe=root/'app'; src.write_text(source,encoding='utf-8')
            self.assertEqual(build_native(src,exe,root),0)
            return subprocess.run([str(exe)],capture_output=True,text=True), root

    @staticmethod
    def q(path:Path)->str:
        return str(path).replace('\\','\\\\').replace('"','\\"')

    def test_native_file_read_and_return_cleanup(self):
        def source(root):
            path=self.q(root/'data.txt')
            return f'import std.files; function read(path Text) returns Text fails files.FileError {{ with file be try files.open(path) {{ return try file.readText(); }} }} function show(path Text) {{ let text be read(path) else error {{ output(error.message); return; }}; output(text); }} show("{path}");'
        p,_=self.compile_run(source,{'data.txt':'hello'})
        self.assertEqual(p.returncode,0); self.assertEqual(p.stdout,'hello\n')

    def test_native_file_write_then_read(self):
        def source(root):
            path=self.q(root/'data.txt')
            return f'import std.files; function write(path Text, text Text) fails files.FileError {{ with file be try files.open(path) {{ try file.writeText(text); }} }} function read(path Text) returns Text fails files.FileError {{ with file be try files.open(path) {{ return try file.readText(); }} }} function run(path Text) {{ write(path,"new text") else error {{ output(error.message); return; }}; let text be read(path) else error {{ output(error.message); return; }}; output(text); }} run("{path}");'
        p,_=self.compile_run(source,{'data.txt':'old'})
        self.assertEqual(p.returncode,0); self.assertEqual(p.stdout,'new text\n')

    def test_native_file_open_failure_is_checked(self):
        def source(root):
            path=self.q(root/'missing.txt')
            return f'import std.files; function read(path Text) returns Text fails files.FileError {{ with file be try files.open(path) {{ return try file.readText(); }} }} function run() {{ let text be read("{path}") else error {{ output(error.message); return; }}; output(text); }} run();'
        p,_=self.compile_run(source)
        self.assertEqual(p.returncode,0); self.assertTrue(p.stdout.strip())

    def test_native_body_failure_remains_primary_through_cleanup(self):
        def source(root):
            path=self.q(root/'data.txt')
            return f'import std.files; error BodyError {{ message Text; }} function work(path Text) fails BodyError, files.FileError {{ with file be try files.open(path) {{ fail BodyError {{ message="body failed"; }}; }} }} work("{path}") else error BodyError {{ output(error.message); }} else error files.FileError {{ output("file failure"); }};'
        p,_=self.compile_run(source,{'data.txt':'x'})
        self.assertEqual(p.returncode,0); self.assertEqual(p.stdout,'body failed\n')

    def test_native_nested_resources_cleanup_on_return(self):
        def source(root):
            a=self.q(root/'a.txt'); b=self.q(root/'b.txt')
            return f'import std.files; function readBoth(a Text,b Text) returns Text fails files.FileError {{ with first be try files.open(a) {{ with second be try files.open(b) {{ return try first.readText() + try second.readText(); }} }} }} function run() {{ let text be readBoth("{a}","{b}") else error {{ output(error.message); return; }}; output(text); }} run();'
        p,_=self.compile_run(source,{'a.txt':'A','b.txt':'B'})
        self.assertEqual(p.returncode,0); self.assertEqual(p.stdout,'AB\n')

if __name__=='__main__': unittest.main()
