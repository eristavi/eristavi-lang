from __future__ import annotations

import json
import os
import shlex
import subprocess
import tempfile
import unittest
from pathlib import Path

from compiler.erist.cli import build_native
from compiler.erist.project import compile_entry
from compiler.erist.runtime_ext import Interpreter

ROOT=Path(__file__).resolve().parents[1]
CASES=json.loads((ROOT/'tests/fixtures/scalar_ir_cases.json').read_text())


def materialize(root,files):
    for name,source in files.items():
        path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(source,encoding='utf-8')
    return root/'app.eri'


class SelfHostedIRTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.binary=Path(cls.temp.name)/'erist-frontend'
        if build_native(ROOT/'src/frontend.eri',cls.binary,ROOT/'src'):
            cls.temp.cleanup();raise AssertionError('IR frontend failed to compile')

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def invoke(self,entry,root,command='emit-c'):
        return subprocess.run([str(self.binary),command,str(entry),'--source-root',str(root)],
                              capture_output=True,text=True,timeout=120,env={'PATH':'','LANG':'C'})

    def compile_c(self,text,root,*,sanitize=False):
        source=root/'generated.c';source.write_text(text,encoding='utf-8');binary=root/'generated'
        flags=['-std=c11','-pedantic-errors','-O2']
        if sanitize:
            flags+=['-fsanitize=undefined','-fno-sanitize-recover=all']
        result=subprocess.run([*shlex.split(os.environ.get('CC','cc')),*flags,str(source),'-o',str(binary)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        return subprocess.run([str(binary)],capture_output=True,text=True,timeout=10,env={'PATH':'','LANG':'C'})

    def test_scalar_corpus_matches_frozen_outputs_and_stage0(self):
        self.assertEqual(len({c['name'] for c in CASES}),len(CASES))
        for case in CASES:
            with self.subTest(case=case['name']),tempfile.TemporaryDirectory() as td:
                root=Path(td);entry=materialize(root,case['files'])
                emitted=self.invoke(entry,root)
                self.assertEqual(emitted.returncode,0,emitted.stderr)
                self.assertEqual(emitted.stderr,'')
                actual=self.compile_c(emitted.stdout,root)
                self.assertEqual((actual.returncode,actual.stdout,actual.stderr),(0,case['stdout'],''))
                module=compile_entry(entry,root);lines=[]
                interpreter=Interpreter(lines.append,module.module_id,module.imports)
                interpreter.run(module.program)
                self.assertEqual(''.join(line+'\n' for line in lines),case['stdout'])
                reference=root/'reference'
                self.assertEqual(build_native(entry,reference,root),0)
                expected=subprocess.run([str(reference)],capture_output=True,text=True,timeout=10)
                self.assertEqual((actual.returncode,actual.stdout,actual.stderr),(expected.returncode,expected.stdout,expected.stderr))

    def test_runtime_faults_match_stage0_without_c_undefined_behavior(self):
        expressions={
            'add':'max+one','subtract':'min-one','multiply':'max*two',
            'multiply_min':'min*(-one)','multiply_negative':'(-max)*two',
            'divide_zero':'one/zero','remainder_zero':'one%zero',
            'divide_min':'min/(-one)','remainder_min':'min%(-one)','negate_min':'-min',
        }
        prefix='let max be 9223372036854775807; let min be -max-1; let one be 1; let two be 2; let zero be 0; '
        for name,expression in expressions.items():
            with self.subTest(case=name),tempfile.TemporaryDirectory() as td:
                root=Path(td);entry=materialize(root,{'app.eri':prefix+'output('+expression+');'})
                emitted=self.invoke(entry,root);self.assertEqual(emitted.returncode,0,emitted.stderr)
                actual=self.compile_c(emitted.stdout,root,sanitize=True)
                reference=root/'reference';self.assertEqual(build_native(entry,reference,root),0)
                expected=subprocess.run([str(reference)],capture_output=True,text=True,timeout=10)
                self.assertEqual(actual.returncode,1)
                self.assertEqual((actual.returncode,actual.stdout,actual.stderr),(expected.returncode,expected.stdout,expected.stderr))

    def test_ir_is_typed_located_and_deterministic(self):
        case=next(c for c in CASES if c['name']=='factorial')
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);entry=materialize(root,case['files'])
            first=self.invoke(entry,root,'ir');second=self.invoke(entry,root,'ir')
            self.assertEqual(first.returncode,0,first.stderr);self.assertEqual(first.stdout,second.stdout)
            data=json.loads(first.stdout)
            self.assertEqual(data['format'],'eristavi-typed-ir-v1');self.assertTrue(data['experimental'])
            self.assertEqual(len(data['functions']),1)
            routine=data['functions'][0];self.assertEqual(routine['result'],1)
            self.assertEqual([(p['name'],p['type'],p['parameter']) for p in routine['locals']],[('n',1,True)])
            self.assertEqual(routine['body']['location']['path'],str(entry.resolve()))
            a=self.invoke(entry,root);b=self.invoke(entry,root);self.assertEqual(a.stdout,b.stdout)

    def test_unsupported_features_are_located_without_partial_output(self):
        sources=[
            'output(1.5);','let items be [1,2]; output(items.count);',
            'let x maybe Int be none;','type Box { value Int; } let x be Box { value=1; };',
            'let x be identity 1;','function echo(x) { return x; } output(echo(1));',
            'error Oops { message Text; } function f() fails Oops { fail Oops { message="x"; }; }',
            'import std.process; output(process.arguments().count);',
        ]
        for source in sources:
            with self.subTest(source=source),tempfile.TemporaryDirectory() as td:
                root=Path(td);entry=materialize(root,{'app.eri':source})
                for command in ('ir','emit-c'):
                    result=self.invoke(entry,root,command)
                    self.assertEqual(result.returncode,1,result.stderr);self.assertEqual(result.stdout,'')
                    self.assertRegex(result.stderr,r'app\.eri:\d+:\d+: compiler error \[lower\]:')
                    self.assertEqual(sorted(p.name for p in root.iterdir()),['app.eri'])

    def test_semantic_errors_precede_lowering_and_never_execute_the_program(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);entry=materialize(root,{'app.eri':'output("must not run"); let fixed x be 1; x=2;'})
            result=self.invoke(entry,root)
            self.assertEqual(result.returncode,1);self.assertEqual(result.stdout,'')
            self.assertIn('semantic error [fixed]',result.stderr)

    def test_interpreted_and_compiled_eristavi_lowering_agree(self):
        case=next(c for c in CASES if c['name']=='text_values')
        module=compile_entry(ROOT/'src/frontend.eri',ROOT/'src')
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);entry=materialize(root,case['files'])
            for command in ('ir','emit-c'):
                output=[];errors=[]
                interpreter=Interpreter(output.append,module.module_id,module.imports,
                                        arguments=[command,str(entry),'--source-root',str(root)],error_output=errors.append)
                interpreter.run(module.program)
                compiled=self.invoke(entry,root,command)
                self.assertEqual(compiled.returncode,0,compiled.stderr)
                self.assertEqual(interpreter.process_state.exit_code,0)
                self.assertEqual(errors,[])
                self.assertEqual(''.join(line+'\n' for line in output),compiled.stdout)

    def test_verifier_and_backend_reject_malformed_ir(self):
        helpers="""
import compiler.typed_ir as ir;
import compiler.ir_verify;
import compiler.ir_c;
import compiler.semantic_model as m;
function location() returns identity m.Location { return identity m.Location { path="test.eri"; line=4; column=2; next=none; }; }
function node(kind Int,valueType Int) returns identity ir.Node { return ir.node(kind,valueType,location()); }
function empty() returns identity ir.Program {
    let entry be identity ir.Function { index=-1; name="entry"; result=5; locals=none; body=node(0,5); next=none; };
    return identity ir.Program { functions=none; entry=entry; };
}
function item(immutable Bool) returns identity ir.Local { return identity ir.Local { index=0; name="x"; valueType=1; immutable=immutable; parameter=false; next=none; }; }
function discard(value identity ir.Node) returns identity ir.Node { let result be node(12,5); result.first=value; return result; }
function declare() returns identity ir.Node { let result be node(10,5); result.index=0; result.first=node(1,1); return result; }
function read() returns identity ir.Node { let result be node(2,1); result.index=0; return result; }
function routine(p identity ir.Program) returns identity ir.Function {
    let result be identity ir.Function { index=0; name="f"; result=1; locals=none; body=node(0,5); next=none; };
    let returned be node(15,5); returned.first=node(1,1); result.body.first=returned; p.functions=result; return result;
}
function check(p identity ir.Program) {
    ir_verify.verify(p) else error m.SemanticError { output("bad verification"); return; };
    let ignored be ir_c.emit(p) else error m.SemanticError { output("bad emission"); return; };
    output("ok");
}
function rejected(p identity ir.Program) {
    let accepted be ir_verify.verify(p) else error m.SemanticError { output(error.category); return; };
    output("bad acceptance");
}
function backendRejected(p identity ir.Program) {
    let generated be ir_c.emit(p) else error m.SemanticError { output(error.category); return; };
    output("bad backend acceptance");
}
"""
        mutations=[
            'p.entry.body.first=discard(node(99,1));',
            'p.entry.body.first=discard(read());',
            'let value be node(1,3); value.number=2; p.entry.body.first=discard(value);',
            'let value be node(3,3); value.text="not"; value.first=node(1,1); p.entry.body.first=discard(value);',
            'let value be node(4,1); value.text="+"; value.first=node(1,1); value.second=node(1,3); p.entry.body.first=discard(value);',
            'let value be node(5,1); value.index=3; p.entry.body.first=discard(value);',
            'let f be routine(p); let value be node(5,3); value.index=0; p.entry.body.first=discard(value);',
            'let f be routine(p); f.body.first=none;',
            'let f be routine(p); let returned be node(15,5); returned.first=node(1,3); f.body.first=returned;',
            'let f be routine(p); let parameter be item(false); parameter.parameter=true; f.locals=parameter; let value be node(5,1); value.index=0; p.entry.body.first=discard(value);',
            'let f be routine(p); let value be node(5,1); value.index=0; value.first=node(1,1); p.entry.body.first=discard(value);',
            'p.entry.body.first=node(15,5);',
            'let value be node(13,5); value.first=node(1,1); value.second=node(0,5); p.entry.body.first=value;',
            'p.entry.locals=item(true); let first be declare(); first.immutable=true; let second be node(11,5); second.index=0; second.first=node(1,1); first.next=second; p.entry.body.first=first;',
            'p.entry.locals=item(false); let branch be node(13,5); branch.first=node(1,3); let body be node(0,5); body.first=declare(); branch.second=body; branch.next=discard(read()); p.entry.body.first=branch;',
            'p.entry.locals=item(false); let branch be node(13,5); branch.first=node(1,3); let a be node(0,5); let b be node(0,5); a.first=declare(); b.first=declare(); branch.second=a; branch.third=b; p.entry.body.first=branch;',
            'let value be discard(node(1,1)); value.next=value; p.entry.body.first=value;',
            'let f be routine(p); f.next=f;',
            'let value be item(false); value.next=value; p.entry.locals=value;',
            'let a be node(1,1); let value be node(4,1); value.text="+"; value.first=a; value.second=a; p.entry.body.first=discard(value);',
            'p.entry.locals=item(false);',
            'let value be discard(node(1,1)); value.valueType=1; p.entry.body.first=value;',
        ]
        cases=''
        for index,mutation in enumerate(mutations):
            cases+=f'function case{index}() {{ let p be empty(); {mutation} rejected(p); backendRejected(p); }}\n'
        source=helpers+cases+'check(empty()); let p be empty(); let f be routine(p); check(p);\n'
        source+=''.join(f'case{index}();\n' for index in range(len(mutations)))
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'compiler').symlink_to(ROOT/'src/compiler',target_is_directory=True)
            entry=root/'app.eri';entry.write_text(source);binary=root/'verify'
            self.assertEqual(build_native(entry,binary,root),0)
            result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(result.stdout,'ok\nok\n'+('ir-verify\nir-verify\n'*len(mutations)))
