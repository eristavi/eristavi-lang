from __future__ import annotations
import tempfile, unittest
from pathlib import Path
from compiler.erist.project import compile_entry
from compiler.erist.runtime import Interpreter
from compiler.erist.diagnostics import SemanticError

class ProjectTests(unittest.TestCase):
    def project(self, files):
        td=tempfile.TemporaryDirectory(); root=Path(td.name)
        for name,text in files.items():
            p=root/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text,encoding='utf-8')
        return td,root
    def run_entry(self,root):
        mod=compile_entry(root/'app.eri',root); out=[]; Interpreter(out.append,mod.module_id,mod.imports).run(mod.program); return out
    def test_user_module_function_and_type(self):
        td,root=self.project({
            'models/user.eri':'public type User { name Text; } public function make(name Text) returns User { return User { name=name; }; } public function greet(user User) { output(user.name); }',
            'app.eri':'import models.user; let u be user.make("Anna"); user.greet(u);'
        })
        try: self.assertEqual(self.run_entry(root),['Anna'])
        finally: td.cleanup()
    def test_import_alias_and_direct_type_construction(self):
        td,root=self.project({'models/user.eri':'public type User { name Text; } public function greet(u User){ output(u.name); }','app.eri':'import models.user as people; let u be people.User { name="A"; }; people.greet(u);'})
        try: self.assertEqual(self.run_entry(root),['A'])
        finally: td.cleanup()
    def test_private_function_not_exposed(self):
        td,root=self.project({'m.eri':'function hidden(){ output(1); }','app.eri':'import m; m.hidden();'})
        try:
            with self.assertRaises(SemanticError): compile_entry(root/'app.eri',root)
        finally: td.cleanup()
    def test_imported_module_must_be_declaration_only(self):
        td,root=self.project({'m.eri':'output(1);','app.eri':'import m; output(2);'})
        try:
            with self.assertRaises(SemanticError): compile_entry(root/'app.eri',root)
        finally: td.cleanup()
    def test_circular_import_rejected(self):
        td,root=self.project({'a.eri':'import b; public function a(){ }','b.eri':'import a; public function b(){ }','app.eri':'import a; a.a();'})
        try:
            with self.assertRaises(SemanticError): compile_entry(root/'app.eri',root)
        finally: td.cleanup()
    def test_imported_checked_error(self):
        td,root=self.project({'m.eri':'public error E { message Text; } public function risky() fails E { fail E { message="bad"; }; }','app.eri':'import m; m.risky() else error m.E { output(error.message); };'})
        try: self.assertEqual(self.run_entry(root),['bad'])
        finally: td.cleanup()
if __name__=='__main__': unittest.main()
