from __future__ import annotations
import os, tempfile, unittest
from compiler.erist.cli import compile_frontend
from compiler.erist.diagnostics import SemanticError, RuntimeFault
from compiler.erist.runtime import Interpreter

class Tests(unittest.TestCase):
    def execute(self,src):
        out=[]; p=compile_frontend(src); Interpreter(output=out.append).run(p); return out
    def bad(self,src):
        with self.assertRaises(SemanticError): compile_frontend(src)

    def test_hello(self): self.assertEqual(self.execute('let x be 40; let y be 2; output(x+y);'),['42'])
    def test_fixed(self): self.bad('let fixed x be 1; x=2;')
    def test_annotations(self): self.assertEqual(self.execute('let x Int be 3; output(x);'),['3'])
    def test_annotation_mismatch(self): self.bad('let x Float be 3;')
    def test_if_bool(self): self.assertEqual(self.execute('let a be true; if a { output("yes"); } else { output("no"); }'),['yes'])
    def test_if_nonbool(self): self.bad('if 1 { output(1); }')
    def test_scope_no_leak(self): self.bad('if true { let x be 1; } output(x);')
    def test_no_shadow(self): self.bad('let x be 1; if true { let x be 2; }')
    def test_while(self): self.assertEqual(self.execute('let i be 0; while i<3 { output(i); i=i+1; }'),['0','1','2'])
    def test_function_infer(self): self.assertEqual(self.execute('function d(x Int){ return x*2; } output(d(4));'),['8'])
    def test_function_explicit(self): self.assertEqual(self.execute('function d(x Int) returns Int { return x*2; } output(d(4));'),['8'])
    def test_recursive(self): self.assertEqual(self.execute('function f(n Int) returns Int { if n<=1 { return 1; } return n*f(n-1); } output(f(5));'),['120'])
    def test_recursive_infer_bad(self): self.bad('function f(n Int){ if n<=1 { return 1; } return n*f(n-1); } output(f(3));')
    def test_generic_identity(self): self.assertEqual(self.execute('function same(x){ return x; } output(same(3)); output(same("a"));'),['3','a'])
    def test_generic_choose(self): self.assertEqual(self.execute('function choose(a,b,use Bool){ if use { return a; } return b; } output(choose(1,2,true)); output(choose("a","b",false));'),['1','b'])
    def test_generic_choose_mismatch(self): self.bad('function choose(a,b,use Bool){ if use { return a; } return b; } output(choose(1,"b",true));')
    def test_parameter_value_semantics(self): self.assertEqual(self.execute('function inc(x Int) returns Int { x=x+1; return x; } let a be 1; output(inc(a)); output(a);'),['2','1'])

    def test_list_literal(self): self.assertEqual(self.execute('let a be [1,2,3]; output(a.count); output(a[1]);'),['3','2'])
    def test_list_add(self): self.assertEqual(self.execute('let a be [1]; a.add(2); output(a.count); output(a[1]);'),['2','2'])
    def test_empty_list_inference(self): self.assertEqual(self.execute('let a be []; a.add("x"); output(a[0]);'),['x'])
    def test_empty_list_unresolved(self): self.bad('let a be []; output(1);')
    def test_mixed_list(self): self.bad('let a be [1,"x"];')
    def test_index_type(self): self.bad('let a be [1]; output(a[0.0]);')
    def test_index_bounds_literal(self): self.bad('output([1,2][2]);')
    def test_index_bounds_runtime(self):
        with self.assertRaises(RuntimeFault): self.execute('let a be [1]; let i be 2; output(a[i]);')
    def test_index_assign(self): self.assertEqual(self.execute('let a be [1,2]; a[1]=5; output(a[1]);'),['5'])
    def test_list_value_semantics(self): self.assertEqual(self.execute('let a be [1,2]; let b be a; b.add(3); output(a.count); output(b.count);'),['2','3'])
    def test_fixed_list(self): self.bad('let fixed a be [1]; a.add(2);')
    def test_list_equality(self): self.assertEqual(self.execute('output([1,2]==[1,2]); output([1,2]==[2,1]);'),['true','false'])
    def test_for(self): self.assertEqual(self.execute('for x in [1,2,3] { output(x); }'),['1','2','3'])
    def test_for_stable_snapshot(self): self.assertEqual(self.execute('let a be [1,2]; for x in a { output(x); a.add(9); } output(a.count);'),['1','2','4'])
    def test_list_parameter_value(self): self.assertEqual(self.execute('function addx(a){ a.add(9); output(a.count); } let a be [1]; addx(a); output(a.count);'),['2','1'])

    USER='type User { fixed id Int; name Text; } '
    def test_construct(self): self.assertEqual(self.execute(self.USER+'let u be User { id=1; name="A"; }; output(u.name);'),['A'])
    def test_missing_field(self): self.bad(self.USER+'let u be User { id=1; };')
    def test_unknown_field(self): self.bad(self.USER+'let u be User { id=1; name="A"; x=2; };')
    def test_duplicate_field(self): self.bad(self.USER+'let u be User { id=1; id=2; name="A"; };')
    def test_fixed_field(self): self.bad(self.USER+'let u be User { id=1; name="A"; }; u.id=2;')
    def test_mutable_field(self): self.assertEqual(self.execute(self.USER+'let u be User { id=1; name="A"; }; u.name="B"; output(u.name);'),['B'])
    def test_user_value_semantics(self): self.assertEqual(self.execute(self.USER+'let a be User { id=1; name="A"; }; let b be a; b.name="B"; output(a.name); output(b.name);'),['A','B'])
    def test_user_equality(self): self.assertEqual(self.execute(self.USER+'let a be User { id=1; name="A"; }; let b be User { id=1; name="A"; }; output(a==b);'),['true'])
    def test_nested_mutation(self):
        src='type Address { city Text; } type User { address Address; } let u be User { address=Address { city="P"; }; }; u.address.city="L"; output(u.address.city);'
        self.assertEqual(self.execute(src),['L'])

    def test_maybe_none(self): self.assertEqual(self.execute('let x maybe Int be none; output(x==none);'),['true'])
    def test_maybe_narrow_if(self):
        src=self.USER+'let u maybe User be User { id=1; name="A"; }; if u != none { output(u.name); }'
        self.assertEqual(self.execute(src),['A'])
    def test_maybe_no_narrow(self): self.bad(self.USER+'let u maybe User be none; output(u.name);')
    def test_maybe_early_return(self):
        src=self.USER+'function name(u maybe User) returns Text { if u==none { return "none"; } return u.name; } output(name(User { id=1; name="A"; }));'
        self.assertEqual(self.execute(src),['A'])
    def test_maybe_assignment_narrows(self):
        src=self.USER+'let u maybe User be none; u=User { id=1; name="A"; }; output(u.name);'
        self.assertEqual(self.execute(src),['A'])

    def test_identity_alias(self):
        src='type Counter { value Int; } let a be identity Counter { value=0; }; let b be a; b.value=5; output(a.value); output(a==b);'
        self.assertEqual(self.execute(src),['5','true'])
    def test_identity_distinct(self):
        src='type Counter { value Int; } let a be identity Counter { value=0; }; let b be identity Counter { value=0; }; output(a==b);'
        self.assertEqual(self.execute(src),['false'])
    def test_value_identity_compare_bad(self): self.bad('type C { x Int; } let a be C { x=1; }; let b be identity C { x=1; }; output(a==b);')
    def test_fixed_identity_bad(self): self.bad('type C { x Int; } let fixed a be identity C { x=1; };')
    def test_fixed_nested_identity_bad(self): self.bad('type C { x Int; } type M { c identity C; } let c be identity C { x=1; }; let fixed m be M { c=c; };')
    def test_maybe_identity_assignment_compare(self):
        src='type C { x Int; } let selected maybe identity C be none; let c be identity C { x=1; }; selected=c; output(selected==c);'
        self.assertEqual(self.execute(src),['true'])

    def test_error_message_required(self): self.bad('error E { code Int; }')
    def test_checked_handler(self):
        src='error E { message Text; code Int; } function risky() returns Int fails E { fail E { message="bad"; code=1; }; } function run(){ let x be risky() else error { output(error.message); return; }; output(x); } run();'
        self.assertEqual(self.execute(src),['bad'])
    def test_typed_handler(self):
        src='error E { message Text; } function risky() returns Int fails E { fail E { message="bad"; }; } risky() else error E { output(error.message); };'
        self.assertEqual(self.execute(src),['bad'])
    def test_unhandled_checked_bad(self): self.bad('error E { message Text; } function risky() fails E { fail E { message="bad"; }; } risky();')
    def test_try_propagation(self):
        src='error E { message Text; } function risky() returns Int fails E { fail E { message="bad"; }; } function outer() returns Int fails E { return try risky(); } outer() else error { output(error.message); };'
        self.assertEqual(self.execute(src),['bad'])
    def test_try_missing_contract(self): self.bad('error E { message Text; } function risky() returns Int fails E { fail E { message="bad"; }; } function outer() returns Int { return try risky(); }')
    def test_incomplete_handler(self): self.bad('error A { message Text; } error B { message Text; } function f() returns Int fails A,B { fail A { message="a"; }; } function g(){ let x be f() else error A { return; }; }')

    def test_resource_read(self):
        fd,path=tempfile.mkstemp(text=True); os.write(fd,b'hello') if False else None; os.close(fd)
        with open(path,'w',encoding='utf-8') as f: f.write('hello')
        q=path.replace('\\','\\\\').replace('"','\\"')
        src=f'import std.files; function read(path Text) returns Text fails files.FileError {{ with file be try files.open(path) {{ return try file.readText(); }} }} function show(path Text) {{ let text be read(path) else error {{ output(error.message); return; }}; output(text); }} show("{q}");'
        try: self.assertEqual(self.execute(src),['hello'])
        finally: os.unlink(path)
    def test_resource_missing_caught(self):
        p='/tmp/definitely-no-eristavi-file-xyz'
        src=f'import std.files; function read(path Text) returns Text fails files.FileError {{ with file be try files.open(path) {{ return try file.readText(); }} }} function show() {{ let text be read("{p}") else error {{ output(error.message); return; }}; output(text); }} show();'
        out=self.execute(src); self.assertEqual(len(out),1)
    def test_resource_let_bad(self): self.bad('import std.files; function f() fails files.FileError { let x be try files.open("x"); }')

    def test_uncalled_generic_body_is_checked(self): self.bad('function bad(x){ return x + true; } output(1);')
    def test_generic_list_index_relationship(self): self.assertEqual(self.execute('function first(items){ return items[0]; } output(first([7,8])); output(first(["a","b"]));'),['7','a'])
    def test_text_ordering_is_not_defined(self): self.bad('output("a" < "b");')
    def test_generic_operation_constraint(self):
        self.assertEqual(self.execute('function double(x){ return x+x; } output(double(2)); output(double("a"));'),['4','aa'])
        self.bad('type U { x Int; } function double(x){ return x+x; } let u be U { x=1; }; output(double(u));')

if __name__=='__main__': unittest.main()
