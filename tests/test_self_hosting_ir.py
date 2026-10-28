from __future__ import annotations

import json
import os
import platform
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
        path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(source.replace('$ROOT',str(root)),encoding='utf-8')
    return root/'app.eri'


class SelfHostedIRTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.binary=Path(cls.temp.name)/'erist-frontend'
        if build_native(ROOT/'src/frontend.eri',cls.binary,ROOT/'src'):
            cls.temp.cleanup();raise AssertionError('IR frontend failed to compile')
        cls.native=platform.system()=='Linux' and platform.machine().lower() in ('x86_64','amd64','aarch64','arm64')
        cls.target='x86_64-linux' if platform.machine().lower() in ('x86_64','amd64') else 'arm64-linux'
        cls.runtime=Path(cls.temp.name)/'runtime.o'
        if cls.native:
            result=subprocess.run([*shlex.split(os.environ.get('CC','cc')),'-std=c11','-O2','-DERIST_NATIVE_RUNTIME','-c',str(ROOT/'runtime/value_runtime.c'),'-o',str(cls.runtime)],capture_output=True,text=True)
            if result.returncode: raise AssertionError(result.stderr)


    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def invoke(self,entry,root,command='emit-c'):
        return subprocess.run([str(self.binary),command,str(entry),'--source-root',str(root),*(['--target',self.target] if command=='emit-asm' else [])],
                              capture_output=True,text=True,timeout=120,env={'PATH':'','LANG':'C'})

    def compile_c(self,text,root,*,sanitize=False):
        source=root/'generated.c';source.write_text(text,encoding='utf-8');binary=root/'generated'
        flags=['-std=c11','-pedantic-errors','-O2']
        if sanitize:
            flags+=['-fsanitize=undefined','-fno-sanitize-recover=all']
        result=subprocess.run([*shlex.split(os.environ.get('CC','cc')),*flags,str(source),'-lm','-o',str(binary)],capture_output=True,text=True)
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
                if self.native:
                    native=self.invoke(entry,root,'emit-asm')
                    self.assertEqual(native.returncode,0,native.stderr)
                    assembly=root/'generated.s';assembly.write_text(native.stdout)
                    executable=root/'native'
                    linked=subprocess.run([*shlex.split(os.environ.get('CC','cc')),str(assembly),str(self.runtime),'-lm','-o',str(executable)],capture_output=True,text=True)
                    self.assertEqual(linked.returncode,0,linked.stderr)
                    executed=subprocess.run([str(executable)],capture_output=True,text=True,timeout=10,env={'PATH':'','LANG':'C'})
                    self.assertEqual((executed.returncode,executed.stdout,executed.stderr),(0,case['stdout'],''))

                module=compile_entry(entry,root);lines=[]
                interpreter=Interpreter(lines.append,module.module_id,module.imports)
                interpreter.run(module.program)
                self.assertEqual(''.join(line+'\n' for line in lines),case['stdout'])
                if case.get('referenceC') is False:
                    continue  # Stage-0 C does not lower these nested mutation paths.
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

    def test_semantic_errors_precede_lowering_and_never_execute_the_program(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);entry=materialize(root,{'app.eri':'output("must not run"); let fixed x be 1; x=2;'})
            result=self.invoke(entry,root)
            self.assertEqual(result.returncode,1);self.assertEqual(result.stdout,'')
            self.assertIn('semantic error [fixed]',result.stderr)

    def test_interpreted_and_compiled_eristavi_lowering_agree(self):
        case=next(c for c in CASES if c['name']=='generic_echo_scalar_kinds')
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
function location() returns identity m.Location { return identity m.Location { path="test.eri"; line=4; column=2; next=none;  ordinal=-1; left=none; right=none; facts=none; }; }
function node(kind Int,valueType Int) returns identity ir.Node { return ir.node(kind,valueType,location()); }
function empty() returns identity ir.Program {
    let entry be identity ir.Function { index=-1; name="entry"; result=5; locals=none; body=node(0,5); failures=none; next=none; };
    return identity ir.Program { functions=none; entry=entry; types=none; };
}
function item(immutable Bool) returns identity ir.Local { return identity ir.Local { index=0; name="x"; valueType=1; immutable=immutable; parameter=false; next=none; }; }
function discard(value identity ir.Node) returns identity ir.Node { let result be node(12,5); result.first=value; return result; }
function declare() returns identity ir.Node { let result be node(10,5); result.index=0; result.first=node(1,1); return result; }
function read() returns identity ir.Node { let result be node(2,1); result.index=0; return result; }
function routine(p identity ir.Program) returns identity ir.Function {
    let result be identity ir.Function { index=0; name="f"; result=1; locals=none; body=node(0,5); failures=none; next=none; };
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
            'let a be item(false); let b be item(false); a.next=b; b.next=a; p.entry.locals=a;',
            'let a be item(false); let b be item(false); let c be item(false); a.next=b; b.next=c; c.next=b; p.entry.locals=a;',
            'let f be routine(p); let shared be item(false); f.locals=shared; p.entry.locals=shared;',
            'let f be routine(p); let a be item(false); let b be item(false); let shared be item(false); a.next=shared; b.next=shared; f.locals=a; p.entry.locals=b;',

            'let a be node(1,1); let value be node(4,1); value.text="+"; value.first=a; value.second=a; p.entry.body.first=discard(value);',
            'p.entry.locals=item(false);',
            'let value be node(1,2); value.text="1.25; exit(0)"; p.entry.body.first=discard(value);',
            'let value be node(1,2); value.text="nan"; p.entry.body.first=discard(value);',
            'let value be node(1,2); value.text="-1.25"; p.entry.body.first=discard(value);',
            'let value be node(1,2); value.text="1.25 "; p.entry.body.first=discard(value);',
            'let value be node(4,2); value.text="%"; let a be node(1,2); a.text="1.25"; let b be node(1,2); b.text="2.5"; value.first=a; value.second=b; p.entry.body.first=discard(value);',
            'let value be node(4,2); value.text="+"; value.first=node(1,1); let b be node(1,2); b.text="2.5"; value.second=b; p.entry.body.first=discard(value);',
            'let value be discard(node(1,1)); value.valueType=1; p.entry.body.first=value;',
        ]
        cases=''
        for index,mutation in enumerate(mutations):
            cases+=f'function case{index}() {{ let p be empty(); {mutation} rejected(p); backendRejected(p); }}\n'
        repair="""
function repaired() {
    let p be empty(); let f be routine(p); let shared be item(false);
    p.entry.locals=shared; f.locals=shared;
    ir_verify.verify(p) else error m.SemanticError {
        output(error.category); output(error.message); output(error.path); output(error.line); output(error.column);
    };
    p.entry.locals=none; f.locals=none; check(p); check(p);
}
"""
        source=helpers+cases+repair+'check(empty()); let p be empty(); let f be routine(p); check(p);\n'
        source+=''.join(f'case{index}();\n' for index in range(len(mutations)))+'repaired();\n'
        expected='ok\nok\n'+('ir-verify\nir-verify\n'*len(mutations))
        expected+='ir-verify\ncyclic or shared local table\ntest.eri\n4\n2\nok\nok\n'

        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'compiler').symlink_to(ROOT/'src/compiler',target_is_directory=True)
            entry=root/'app.eri';entry.write_text(source);binary=root/'verify'
            self.assertEqual(build_native(entry,binary,root),0)
            result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(result.stdout,expected)
            if self.native:
                emitted=self.invoke(entry,root,'emit-asm')
                self.assertEqual((emitted.returncode,emitted.stderr),(0,''))
                assembly=root/'verify.s';assembly.write_text(emitted.stdout)
                native=root/'verify-native'
                linked=subprocess.run([*shlex.split(os.environ.get('CC','cc')),str(assembly),str(self.runtime),'-lm','-o',str(native)],capture_output=True,text=True)
                self.assertEqual(linked.returncode,0,linked.stderr)
                executed=subprocess.run([str(native)],capture_output=True,text=True,timeout=20)
                self.assertEqual((executed.returncode,executed.stdout,executed.stderr),(0,result.stdout,''))


    def test_specializations_are_concrete_cached_and_deterministic(self):
        source=('function echo(value) { let copied be value; if true { let branch be value; } else { let other be value; } return copied; } '
                'function wrap(value) { return echo(value); } '
                'output(wrap(1)); output(wrap(2)); output(wrap(true)); '
                'output(wrap("text")); output(wrap(1.25));')
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);entry=materialize(root,{'app.eri':source})
            first=self.invoke(entry,root,'ir');second=self.invoke(entry,root,'ir')
            self.assertEqual(first.returncode,0,first.stderr);self.assertEqual(first.stdout,second.stdout)
            functions=json.loads(first.stdout)['functions']
            self.assertEqual(len(functions),8)
            self.assertEqual(len({f['index'] for f in functions}),8)
            for name in ('app.echo','app.wrap'):
                specializations=[f for f in functions if f['name'].startswith(name+'$')]
                self.assertEqual({f['name'] for f in specializations},{name+'$'+str(kind) for kind in (1,2,3,4)})
                for routine in specializations:
                    kind=int(routine['name'].split('$')[-1])
                    self.assertEqual(routine['result'],kind)
                    self.assertEqual([p['type'] for p in routine['locals'] if p['parameter']],[kind])
                    self.assertEqual([p['index'] for p in routine['locals']],list(range(len(routine['locals']))))
                    if name=='app.echo':
                        self.assertEqual([p['name'] for p in routine['locals']],['value','copied','branch','other'])
            emitted=self.invoke(entry,root);again=self.invoke(entry,root)
            self.assertEqual(emitted.stdout,again.stdout)

    def test_specialization_preserves_type_relationships_and_numeric_rules(self):
        sources=[
            'function choose(flag Bool,a,b) { if flag { return a; } return b; } output(choose(true,1,"text"));',
            'function add(a,b) { return a+b; } output(add(1,2.5));',
            'function remainder(a,b) { return a%b; } output(remainder(1.5,2.0));',
            'function value(a) { let fixed b be a; b=a; return b; } output(value(1));',
        ]
        for source in sources:
            with self.subTest(source=source),tempfile.TemporaryDirectory() as td:
                root=Path(td);entry=materialize(root,{'app.eri':source})
                result=self.invoke(entry,root)
                self.assertEqual(result.returncode,1);self.assertEqual(result.stdout,'')
                self.assertIn('semantic error',result.stderr)

    def test_float_rounding_is_reset_and_operations_cannot_contract(self):
        source=('let a be 1.0000000000000002; let b be 1.0000000000000002; '
                'let c be -1.0000000000000004; output(a*b+c==0.0); '
                'output(1.00000000000000011102230246251565404236316680908203125==1.0); '
                'let huge be 9007199254740992.0; let one be 1.0; output(huge+one==huge);')
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);entry=materialize(root,{'app.eri':source})
            result=self.invoke(entry,root);self.assertEqual(result.returncode,0,result.stderr)
            text=result.stdout.replace('int main(int argc,char **argv) {','int eri_application(int argc,char **argv) {')
            text+='\nint main(void) { if(fesetround(FE_DOWNWARD)) return 2; return eri_application(0,NULL); }\n'
            c_source=root/'rounding.c';c_source.write_text(text);binary=root/'rounding'
            for flags in (['-O0'],['-O3','-ffp-contract=fast']):
                with self.subTest(flags=flags):
                    compiled=subprocess.run([*shlex.split(os.environ.get('CC','cc')),'-std=c11','-pedantic-errors',*flags,str(c_source),'-lm','-o',str(binary)],capture_output=True,text=True)
                    self.assertEqual(compiled.returncode,0,compiled.stderr)
                    run=subprocess.run([str(binary)],capture_output=True,text=True)
                    self.assertEqual((run.returncode,run.stdout,run.stderr),(0,'true\ntrue\ntrue\n',''))

    def test_float_backend_rejects_fast_math(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);entry=materialize(root,{'app.eri':'output(1.25);'})
            emitted=self.invoke(entry,root);self.assertEqual(emitted.returncode,0,emitted.stderr)
            source=root/'unsafe.c';source.write_text(emitted.stdout)
            compiled=subprocess.run([*shlex.split(os.environ.get('CC','cc')),'-std=c11','-O3','-ffast-math',str(source),'-lm','-o',str(root/'unsafe')],capture_output=True,text=True)
            self.assertNotEqual(compiled.returncode,0)
            self.assertIn('fast-math is unsupported',compiled.stderr)

    def test_all_accepted_semantic_projects_lower_without_python_fallback(self):
        semantic=json.loads((ROOT/'tests/fixtures/semantic_cases.json').read_text())
        for case in semantic:
            if not case['accept']: continue
            with self.subTest(case=case['name']),tempfile.TemporaryDirectory() as td:
                root=Path(td)
                for name,source in case['files'].items():
                    path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(source)
                result=self.invoke(root/case['entry'],root)
                self.assertEqual(result.returncode,0,result.stderr)
                self.assertIn('int main(',result.stdout)

    def test_cleanup_failure_preserves_primary_and_secondary_order(self):
        prefix='import std.files; error Problem { message Text; } '
        for failure,expected in [('return 42;','inner\nouter\n'),('fail Problem { message="body"; };','body\ninner\nouter\n')]:
            with self.subTest(failure=failure),tempfile.TemporaryDirectory() as td:
                root=Path(td)
                for name in ('outer','inner'): (root/name).write_text('')
                source=(prefix+'function run() returns Int fails files.FileError, Problem { '
                        f'with outer be try files.openRead("{root}/outer") {{ '
                        f'with inner be try files.openRead("{root}/inner") {{ '+failure+' } } } '
                        'function main() { let ignored be run() else error { output(error.message); return; }; } main();')
                entry=materialize(root,{'app.eri':source});emitted=self.invoke(entry,root)
                self.assertEqual(emitted.returncode,0,emitted.stderr)
                text=emitted.stdout
                start=text.index('static bool eri_file_cleanup(');end=text.index('\n',start)
                original=text[start:end].replace('eri_file_cleanup(','eri_file_cleanup_real(',1)
                injected='''
static bool eri_file_cleanup(eri_file *file,eri_failure_value *failure){
    bool closed=!file||file->closed;
    bool actual=eri_file_cleanup_real(file,failure);
    if(actual||closed)return actual;
    const char *name=strrchr(file->c_path,'/');name=name?name+1:file->c_path;
    *failure=eri_make_file_failure(name,file->path);return true;
}
'''
                text=text[:start]+original+injected+text[end:]
                text=text.replace('int main(int argc,char **argv) {','int erist_application(int argc,char **argv) {')
                text+='''
int main(int argc,char **argv){int code=erist_application(argc,argv);eri_secondary_failure *next=eri_failure.secondary;while(next){eri_out_text(next->message);next=next->next;}return code;}
'''
                actual=self.compile_c(text,root)
                self.assertEqual((actual.returncode,actual.stdout,actual.stderr),(0,expected,''))
                if self.native:
                    assembly=self.invoke(entry,root,'emit-asm')
                    self.assertEqual(assembly.returncode,0,assembly.stderr)
                    asm=root/'cleanup.s';asm.write_text(assembly.stdout)
                    runtime=(ROOT/'runtime/value_runtime.c').read_text()
                    begin=runtime.index('static bool eri_file_cleanup(');end=runtime.index('\n',begin)
                    original=runtime[begin:end].replace('eri_file_cleanup(','eri_file_cleanup_real(',1)
                    runtime=runtime[:begin]+original+injected+runtime[end:]
                    runtime=runtime.replace('int main(int argc,char **argv){','int erist_application(int argc,char **argv){')
                    runtime+='''
int main(int argc,char **argv){int code=erist_application(argc,argv);eri_secondary_failure *next=eri_failure.secondary;while(next){eri_out_text(next->message);next=next->next;}return code;}
'''
                    runtime_source=root/'runtime.c';runtime_source.write_text(runtime)
                    executable=root/'native-cleanup'
                    compiled=subprocess.run([*shlex.split(os.environ.get('CC','cc')),'-std=c11','-O2',
                        '-DERIST_NATIVE_RUNTIME',str(asm),str(runtime_source),'-lm','-o',str(executable)],capture_output=True,text=True)
                    self.assertEqual(compiled.returncode,0,compiled.stderr)
                    actual=subprocess.run([str(executable)],capture_output=True,text=True,timeout=10)
                    self.assertEqual((actual.returncode,actual.stdout,actual.stderr),(0,expected,''))

    def test_repeated_checked_unwinds_preserve_caller_state_and_error_payload(self):
        source='''
error Problem { message Text; total Int; }
type State { total Int; }
function inner(shared identity State) fails Problem {
    let items be [10,20]; shared.total=shared.total+items[0];
    fail Problem { message="caught"; total=shared.total; };
}
function middle(shared identity State) fails Problem { try inner(shared); }
function run() {
    let shared be identity State { total=0; }; let last be 0; let index be 0;
    while index<1000 {
        middle(shared) else error Problem { last=error.total; };
        index=index+1;
    }
    output(shared.total); output(last);
}
run();
'''
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);entry=materialize(root,{'app.eri':source})
            emitted=self.invoke(entry,root)
            self.assertEqual(emitted.returncode,0,emitted.stderr)
            result=self.compile_c(emitted.stdout,root)
            self.assertEqual((result.returncode,result.stdout,result.stderr),(0,'10000\n10000\n',''))
            if self.native:
                assembly=self.invoke(entry,root,'emit-asm')
                self.assertEqual(assembly.returncode,0,assembly.stderr)
                asm=root/'unwind.s';asm.write_text(assembly.stdout);executable=root/'unwind'
                compiled=subprocess.run([*shlex.split(os.environ.get('CC','cc')),str(asm),str(self.runtime),
                    '-lm','-o',str(executable)],capture_output=True,text=True)
                self.assertEqual(compiled.returncode,0,compiled.stderr)
                result=subprocess.run([str(executable)],capture_output=True,text=True,timeout=10)
                self.assertEqual((result.returncode,result.stdout,result.stderr),(0,'10000\n10000\n',''))

    def test_native_scalar_loop_temporary_slots_are_bounded(self):
        if not self.native:self.skipTest('matching native ELF host required')
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            runtime=(ROOT/'runtime/value_runtime.c').read_text()
            runtime=runtime.replace('static size_t ev_live_slots,','static size_t test_peak_slots;\nstatic size_t ev_live_slots,')
            runtime=runtime.replace('ev_live_slots++;','ev_live_slots++;if(ev_live_slots>test_peak_slots)test_peak_slots=ev_live_slots;')
            runtime=runtime.replace('return eri_process_exit_code;',
                'fprintf(stderr,"%zu\\n",test_peak_slots);return eri_process_exit_code;')
            c=root/'runtime.c';c.write_text(runtime);obj=root/'runtime.o'
            compiled=subprocess.run([*shlex.split(os.environ.get('CC','cc')),'-std=c11','-O2',
                '-DERIST_NATIVE_RUNTIME','-c',str(c),'-o',str(obj)],capture_output=True,text=True)
            self.assertEqual(compiled.returncode,0,compiled.stderr)
            peaks=[]
            for iterations in (1000,100000):
                entry=materialize(root,{'app.eri':f'let i be 0; while i<{iterations} {{ i=i+1; }} output(i);'})
                emitted=self.invoke(entry,root,'emit-asm')
                self.assertEqual(emitted.returncode,0,emitted.stderr)
                asm=root/'loop.s';asm.write_text(emitted.stdout);binary=root/'loop'
                built=subprocess.run([*shlex.split(os.environ.get('CC','cc')),str(asm),str(obj),'-lm','-o',str(binary)],capture_output=True,text=True)
                self.assertEqual(built.returncode,0,built.stderr)
                result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=30)
                self.assertEqual((result.returncode,result.stdout),(0,str(iterations)+'\n'))
                peaks.append(int(result.stderr.strip()))
            self.assertLess(max(peaks),4200)
            self.assertLessEqual(peaks[1],peaks[0]+32)

    def test_native_heap_diagnostics_preserve_output_and_account_for_slot_collection(self):
        if not self.native:self.skipTest('matching native ELF host required')
        source='''
error Problem { message Text; }
function failer() fails Problem { fail Problem { message="caught"; }; }
function run() {
    let values be [1]; let copy be values; copy.add(2); copy.add(3);
    output(values.count); output(copy.count); output("a"+"β");
    failer() else error Problem { output(error.message); };
    let i be 0; while i<10000 { i=i+1; } output(i);
}
run();
'''
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);entry=materialize(root,{'app.eri':source})
            emitted=self.invoke(entry,root,'emit-asm');self.assertEqual(emitted.returncode,0,emitted.stderr)
            asm=root/'stats.s';asm.write_text(emitted.stdout);expected='1\n3\naβ\ncaught\n10000\n'
            for diagnostic in (False,True):
                with self.subTest(diagnostic=diagnostic):
                    binary=root/('diagnostic' if diagnostic else 'normal')
                    runtime=self.runtime;flags=[]
                    if diagnostic:
                        runtime=ROOT/'runtime/value_runtime.c'
                        flags=['-std=c11','-O2','-DERIST_NATIVE_RUNTIME','-DERIST_HEAP_STATS','-DERIST_SLOT_GC_INTERVAL=32']
                    built=subprocess.run([*shlex.split(os.environ.get('CC','cc')),*flags,str(asm),str(runtime),
                        '-lm','-o',str(binary)],capture_output=True,text=True)
                    self.assertEqual(built.returncode,0,built.stderr)
                    result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=30)
                    self.assertEqual((result.returncode,result.stdout),(0,expected))
                    if not diagnostic:self.assertEqual(result.stderr,'');continue
                    report=json.loads(result.stderr)
                    self.assertTrue(report['registry_consistent']);self.assertEqual(report['format'],'eristavi-heap-stats-v1')
                    for kind in ('object','object_data','text','failure'):
                        self.assertGreater(report['categories'][kind]['live_bytes'],0)
                    for kind in ('scope','handler','root_table'):
                        self.assertEqual(report['categories'][kind]['live_allocations'],0)
                    slots=report['categories']['slot']
                    self.assertGreater(slots['allocations'],50000);self.assertLess(slots['peak_allocations'],512)
                    self.assertEqual(slots['live_allocations'],1)

    def test_native_forced_slot_collection_preserves_snapshots_calls_and_failures(self):
        if not self.native:self.skipTest('matching native ELF host required')
        source='''
import std.files;
error Problem { message Text; number Int; }
type Counter { value Int; }
function plus(a Int,b Int,c Int,d Int,e Int,f Int,g Int,h Int,i Int) { return a+b+c+d+e+f+g+h+i; }
function recurse(n Int) returns Int { if n==0 { return 0; } return n+recurse(n-1); }
function failer(counter identity Counter) fails Problem {
    let i be 0; while i<20 { counter.value=counter.value+1; i=i+1; }
    fail Problem { message="expected"; number=counter.value; };
}
function read(path Text) returns Text fails files.FileError {
    with file be try files.openRead(path) {
        let i be 0; while i<20 { i=i+1; }
        return try file.readText();
    }
}
function resourceFailure(path Text) fails files.FileError,Problem {
    with file be try files.openRead(path) {
        let i be 0; while i<20 { i=i+1; }
        fail Problem { message="resource"; number=1; };
    }
}
function run() {
    let original be [1,2,3]; let copy be original; let count be 0;
    for item in original { copy[0]=9; count=count+item; }
    let counter be identity Counter { value=0; }; let alias be counter; let last be 0;
    let index be 0; while index<100 {
        failer(counter) else error Problem { last=error.number; };
        let test be index<50 and index<99 or index==99;
        if test { alias.value=alias.value+1; }
        index=index+1;
    }
    output(original[0]); output(copy[0]); output(count); output(counter.value==last);
    output(plus(1,2,3,4,5,6,7,8,9)); output(recurse(20));
    let text be read("$ROOT/data.txt") else error files.FileError { output(error.message); return; }; output(text);
    resourceFailure("$ROOT/data.txt") else error { output(error.message); };
}
run();
'''
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);entry=materialize(root,{'app.eri':source,'data.txt':'kept'})
            emitted=self.invoke(entry,root,'emit-asm')
            self.assertEqual(emitted.returncode,0,emitted.stderr)
            asm=root/'forced.s';asm.write_text(emitted.stdout);binary=root/'forced'
            flags=['-std=c11','-O2','-DERIST_NATIVE_RUNTIME','-DERIST_SLOT_GC_INTERVAL=1',
                   '-fsanitize=address,undefined','-fno-sanitize-recover=all']
            built=subprocess.run([*shlex.split(os.environ.get('CC','cc')),*flags,str(asm),str(ROOT/'runtime/value_runtime.c'),
                                  '-lm','-o',str(binary)],capture_output=True,text=True)
            self.assertEqual(built.returncode,0,built.stderr)
            environment={**os.environ,'ASAN_OPTIONS':'detect_leaks=0'} # general value buffers remain process-owned
            result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=30,env=environment)
            self.assertEqual((result.returncode,result.stdout,result.stderr),(0,'1\n9\n6\nfalse\n45\n210\nkept\nresource\n',''))
