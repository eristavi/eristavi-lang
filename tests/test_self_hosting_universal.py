from __future__ import annotations
import json
import os
from pathlib import Path
import platform
import re
import shlex
import shutil
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native

ROOT=Path(__file__).resolve().parents[1]

class SelfHostedUniversalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.binary=Path(cls.temp.name)/'compiler'
        if build_native(ROOT/'src/frontend.eri',cls.binary,ROOT/'src'):
            cls.temp.cleanup();raise AssertionError('frontend bootstrap failed')
    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def test_cfg_is_explicit_deterministic_and_discards_unreachable_blocks(self):
        source=('function f(n Int) returns Int { if n<1 { return 1; } else { return n; } } '
                'let n be 0; while n<3 { n=n+1; } output(f(n));')
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);entry=root/'app.eri';entry.write_text(source)
            results=[subprocess.run([str(self.binary),'uir',str(entry)],capture_output=True,text=True,timeout=60,env={'PATH':'','LANG':'C'}) for _ in range(2)]
            self.assertEqual(results[0].returncode,0,results[0].stderr);self.assertEqual(results[0].stdout,results[1].stdout)
            data=json.loads(results[0].stdout)
            self.assertEqual(data['format'],'eristavi-universal-ir-v1');self.assertTrue(data['experimental'])
            for routine in [*data['functions'],data['entry']]:
                blocks={b['index']:b for b in routine['blocks']};self.assertIn(0,blocks)
                reached=set();todo=[0]
                while todo:
                    index=todo.pop()
                    if index in reached: continue
                    reached.add(index);terminal=blocks[index]['terminator'];self.assertIsNotNone(terminal)
                    self.assertIn(terminal['op'],(6,7,8,9,10))
                    if terminal['op'] in (6,7,9): todo.append(terminal['first'])
                    if terminal['op'] in (7,9): todo.append(terminal['second'])
                self.assertEqual(reached,set(blocks))
                for block in blocks.values():
                    for operation in block['instructions']:
                        self.assertEqual(routine['registers'][operation['result']],operation['class'])

    def test_both_native_targets_assemble_as_elf(self):
        clang=shutil.which('clang')
        if not clang: self.skipTest('cross-assembler clang is unavailable')
        source=('function sum(a Int,b Int,c Int,d Int,e Int,f Int,g Int,h Int,i Int) { return a+b+c+d+e+f+g+h+i; } '
                'output(sum(1,2,3,4,5,6,7,8,9));')
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);entry=root/'app.eri';entry.write_text(source)
            for target,triple,machine in [('x86_64-linux','x86_64-linux-gnu',62),('arm64-linux','aarch64-linux-gnu',183)]:
                with self.subTest(target=target):
                    emitted=subprocess.run([str(self.binary),'emit-asm',str(entry),'--target',target],capture_output=True,text=True,timeout=60)
                    self.assertEqual(emitted.returncode,0,emitted.stderr)
                    assembly=root/(target+'.s');obj=root/(target+'.o');assembly.write_text(emitted.stdout)
                    compiled=subprocess.run([clang,'--target='+triple,'-c',str(assembly),'-o',str(obj)],capture_output=True,text=True)
                    self.assertEqual(compiled.returncode,0,compiled.stderr)
                    data=obj.read_bytes();self.assertEqual(data[:4],b'\x7fELF');self.assertEqual(int.from_bytes(data[18:20],'little'),machine)

    def test_native_root_maps_cover_verified_registers_and_stack_parameters(self):
        source=('function sum(a Int,b Int,c Int,d Int,e Int,f Int,g Int,h Int,i Int) { return a+b+c+d+e+f+g+h+i; } '
                'let n be 0; while n<3 { n=sum(n,1,2,3,4,5,6,7,8); } output(n);')
        with tempfile.TemporaryDirectory() as td:
            entry=Path(td)/'app.eri';entry.write_text(source)
            report=subprocess.run([str(self.binary),'uir',str(entry)],capture_output=True,text=True,timeout=60)
            self.assertEqual(report.returncode,0,report.stderr);data=json.loads(report.stdout)
            expected={}
            for routine in [*data['functions'],data['entry']]:
                name='erist_entry' if routine is data['entry'] else 'f'+str(routine['index'])
                # Physical spill words ascend from saved parameters to reversed registers.
                expected[name]=[1]*routine['parameters']+list(reversed(routine['registers']))+[0]
            for target in ('x86_64-linux','arm64-linux'):
                with self.subTest(target=target):
                    emitted=subprocess.run([str(self.binary),'emit-asm',str(entry),'--target',target],capture_output=True,text=True,timeout=60)
                    self.assertEqual(emitted.returncode,0,emitted.stderr)
                    actual={name:list(map(int,values.split(','))) for name,values in
                            re.findall(r'\.Lroots_(\w+):\n\.byte ([0-9,]+)',emitted.stdout)}
                    self.assertEqual(actual,expected)

    def test_universal_verifier_rejects_bad_calls_classes_cfg_and_initialization(self):
        helper='''
import compiler.universal_model as u;
import compiler.universal_verify;
import compiler.universal_optimize;
import compiler.typed_ir as t;
import compiler.semantic_model as m;
function fresh() returns identity u.Builder {
    let location be identity m.Location { path="test.eri"; line=1; column=1; next=none; };
    let source be identity t.Function { index=-1; name="entry"; result=5; locals=none; body=t.node(0,5,location); failures=none; next=none; };
    let typed be identity t.Program { functions=none; entry=source; types=none; };
    let entry be identity u.Function { index=-1; parameters=0; registers=none; registerTail=none; blocks=none; next=none; };
    let program be identity u.Program { types=typed; entry=entry; functions=none; };
    let block be identity u.Block { index=0; instructions=none; tail=none; terminator=none; live=false; next=none; }; entry.blocks=block;
    return identity u.Builder { program=program; routine=entry; current=block; registerCount=0; blockCount=1; locals=none; };
}
function rejected(builder identity u.Builder) {
    let checked be universal_verify.verify(builder.program) else error m.SemanticError { output(error.category); return; };
    output("bad acceptance");
}
function finish(builder identity u.Builder,value Int) { u.returnValue(builder,value); rejected(builder); }
'''
        mutations=[
            'let value be u.allocate(b,1); finish(b,value);',
            'let raw be u.number(b,1); finish(b,raw);',
            'let value be u.zero(b,"int"); finish(b,value);',
            'let value be u.zero(b,"void"); let invalid be u.call(b,"int",[value]); finish(b,invalid);',
            'let value be u.zero(b,"arbitrary_symbol;unsafe"); finish(b,value);',
            'let value be u.zero(b,"f99"); finish(b,value);',
            'let terminal be u.instruction(6); terminal.first=99; u.end(b,terminal); rejected(b);',
            'let value be u.zero(b,"void"); let branch be u.instruction(7); branch.arguments=u.operands([value]); branch.first=0; branch.second=0; u.end(b,branch); rejected(b);',
            'let value be u.instruction(5); value.result=u.allocate(b,1); value.valueClass=1; value.number=0; u.append(b,value); finish(b,value.result);',
            'let value be u.instruction(999); value.result=u.allocate(b,1); value.valueClass=1; u.append(b,value); finish(b,value.result);',
            'let value be u.zero(b,"void"); let cyclic be b.current.tail; if cyclic != none { cyclic.next=cyclic; } finish(b,value);',
            'let test be u.number(b,1); let first be u.block(b); let second be u.block(b); let done be u.block(b); u.branch(b,test,first,second); b.current=first; let value be u.zero(b,"void"); u.jump(b,done); b.current=second; u.jump(b,done); b.current=done; finish(b,value);',
        ]
        cases=''.join(f'function case{i}() {{ let b be fresh(); {body} }}\n' for i,body in enumerate(mutations))
        source=helper+cases+''.join(f'case{i}();\n' for i in range(len(mutations)))
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'compiler').symlink_to(ROOT/'src/compiler',target_is_directory=True)
            entry=root/'app.eri';entry.write_text(source);binary=root/'verify'
            self.assertEqual(build_native(entry,binary,root),0)
            result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=30)
            self.assertEqual((result.returncode,result.stdout,result.stderr),(0,'ir-verify\n'*len(mutations),''))

    def test_prefix_append_keeps_old_text_and_list_values_unchanged(self):
        source=('let a be "α"; let b be a; a=a+"β"; let c be b+"γ"; output(a); output(b); output(c); '
                'let items be [1]; let copy be items; items.add(2); copy.add(3); output(items==[1,2]); output(copy==[1,3]); '
                'let fixed snapshot be items; items[0]=9; output(snapshot[0]);')
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);entry=root/'app.eri';entry.write_text(source);binary=root/'reference'
            self.assertEqual(build_native(entry,binary,root),0)
            result=subprocess.run([str(binary)],capture_output=True,text=True)
            self.assertEqual((result.returncode,result.stdout,result.stderr),(0,'αβ\nα\nαγ\ntrue\ntrue\n1\n',''))
