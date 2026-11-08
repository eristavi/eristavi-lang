"""Closed checked groups reuse aggregate bindings and typed producer proofs."""
from pathlib import Path
import unittest
import platform
import subprocess
from compiler.erist.cli import compile_entry,build_native
from compiler.erist.runtime_ext import Interpreter
import test_u2_function_failure_producer as producer
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(platform.system()=='Linux' and platform.machine().lower() in ('x86_64','amd64'),'native groups require Linux x86-64')
class U2FunctionValueGroupTests(unittest.TestCase):
    setUpClass=producer.U2FunctionFailureProducerTests.__dict__['setUpClass']
    generator=producer.U2FunctionFailureProducerTests.generator
    run_probe=producer.U2FunctionFailureProducerTests.run_probe
    caller=producer.U2FunctionFailureProducerTests.caller
    def source(self): return (ROOT/'tests/fixtures/u2_function_failure_producer_group.eri').read_text()
    def test_mutual_group_constructs_and_preserves_typed_contexts(self):
        result=self.generator('typed-value-group',self.source())
        self.assertEqual((result.returncode,result.stderr),(0,''),result.stdout[-2000:])
        outcomes=[]
        for depth in (0,1,5,16,64):
            for failed in (False,True):
                with self.subTest(depth=depth,failed=failed):
                    run=self.run_probe(f'value-group-{depth}-{int(failed)}',
                        result.stdout+self.caller(depth,failed)+producer.graph.FINISH+producer.descriptors(),types=False)
                    code=(52 if depth%2 else 42) if failed else (43 if depth%2 else 53)
                    expected=(str(code)+'\nβ\n').encode() if depth or failed else b'7\n'
                    self.assertEqual((run.returncode,run.stdout,run.stderr),(0,expected,b''))
                    outcomes.append(run.stdout)
        entry=ROOT/'tests/fixtures/u2_function_failure_group_reference.eri'
        module=compile_entry(entry,entry.parent); output=[]
        Interpreter(output=output.append,module_id=module.module_id,imported_modules=module.imports).run(module.program)
        expected=('\n'.join(output)+'\n').encode()
        self.assertEqual(b''.join(outcomes),expected)
        binary=self.directory/'group-reference'
        self.assertEqual(build_native(entry,binary,entry.parent),0)
        run=subprocess.run([str(binary)],capture_output=True,timeout=30)
        self.assertEqual((run.returncode,run.stdout,run.stderr),(0,expected,b''))
    def test_all_members_preflight_before_output(self):
        source=self.source()
        bad_origin=source.replace('import std.process;', 'import std.process;\nimport compiler.u1_words as words;')
        bad_origin=bad_origin.replace('    try native.emitValuesCheckedGroup(',
            '    let siblingPhase be try budget.constructionPhase(ownerB);\n'
            '    let captureId be try words.get(fnB.values,siblingPhase,(primaryB.index-1)*4+2);\n'
            '    fnB.instructions.frozen=false; try words.set(fnB.instructions,siblingPhase,(captureId-1)*10+6,0); fnB.instructions.frozen=true;\n'
            '    try budget.finishPhase(siblingPhase);\n    try native.emitValuesCheckedGroup(')
        for name,changed in (
            ('late-sibling-origin',bad_origin),
            ('layout',source.replace('true,[4,15]);','true,[4]);')),
            ('duplicate',source.replace('[97,98]','[97,97]')),
            ('missing-member',source.replace('[fn,fnB],[97,98]','[fn],[97]')),
            ('bad-sibling',source.replace('body.bind(fnB,graph,table,otherTarget)', 'body.bind(fnB,graph,table,target)'))):
            with self.subTest(case=name):
                self.assertNotEqual(source,changed)
                result=self.generator('bad-value-group-'+name,changed)
                self.assertNotEqual(result.returncode,0,result.stdout[-2000:])
                self.assertNotIn('.section',result.stdout)
