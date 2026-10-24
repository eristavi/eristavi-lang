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
    def test_native_list_literal_index_and_count(self):
        p=self.compile_run('let x be [10,20,30]; output(x.count); output(x[1]);'); self.assertEqual(p.stdout,'3\n20\n')
    def test_native_list_add_and_index_assignment(self):
        p=self.compile_run('let x be [1,2]; x.add(3); x[0]=9; output(x.count); output(x[0]); output(x[2]);'); self.assertEqual(p.stdout,'3\n9\n3\n')
    def test_native_list_value_semantics(self):
        p=self.compile_run('let first be [1,2]; let second be first; second.add(3); second[0]=9; output(first.count); output(first[0]); output(second.count); output(second[0]);'); self.assertEqual(p.stdout,'2\n1\n3\n9\n')
    def test_native_list_equality(self):
        p=self.compile_run('output([1,2,3]==[1,2,3]); output([1,2,3]==[3,2,1]); output(["a"]==["a"]);'); self.assertEqual(p.stdout,'true\nfalse\ntrue\n')
    def test_native_list_bounds_fault(self):
        p=self.compile_run('let i be 2; let x be [1]; output(x[i]);'); self.assertNotEqual(p.returncode,0); self.assertIn('List index out of bounds',p.stderr)
    def test_native_for_list_order(self):
        p=self.compile_run('let x be [1,2,3]; for item in x { output(item); }'); self.assertEqual(p.stdout,'1\n2\n3\n')
    def test_native_for_uses_stable_snapshot(self):
        p=self.compile_run('let x be [1,2]; for item in x { output(item); x.add(9); } output(x.count);'); self.assertEqual(p.stdout,'1\n2\n4\n')
    def test_native_user_value_construction_and_fields(self):
        p=self.compile_run('type User { name Text; age Int; } let u be User { name="Anna"; age=30; }; output(u.name); output(u.age);'); self.assertEqual(p.stdout,'Anna\n30\n')
    def test_native_user_value_copy_is_independent(self):
        p=self.compile_run('type User { name Text; } let first be User { name="Anna"; }; let second be first; second.name="Maria"; output(first.name); output(second.name);'); self.assertEqual(p.stdout,'Anna\nMaria\n')
    def test_native_user_value_structural_equality(self):
        p=self.compile_run('type User { name Text; age Int; } let a be User { name="Anna"; age=30; }; let b be User { name="Anna"; age=30; }; let c be User { name="Anna"; age=31; }; output(a==b); output(a==c);'); self.assertEqual(p.stdout,'true\nfalse\n')
    def test_native_user_value_parameter_is_independent(self):
        p=self.compile_run('type User { name Text; } function rename(user User) returns User { user.name="Maria"; return user; } let original be User { name="Anna"; }; let changed be rename(original); output(original.name); output(changed.name);'); self.assertEqual(p.stdout,'Anna\nMaria\n')
    def test_native_nested_value_mutation(self):
        p=self.compile_run('type Address { city Text; } type User { address Address; } let u be User { address=Address { city="Paphos"; }; }; u.address.city="Nicosia"; output(u.address.city);'); self.assertEqual(p.stdout,'Nicosia\n')
    def test_build_c_emits_source(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td); src=r/'app.eri'; out=r/'app.c'; src.write_text('output(42);',encoding='utf-8'); self.assertEqual(build_c_file(src,out,r),0); self.assertIn('int main',out.read_text())
if __name__=='__main__': unittest.main()
