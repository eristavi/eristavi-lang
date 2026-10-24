from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from compiler.erist.cli import build_native
from compiler.erist.diagnostics import EristaviError
from compiler.erist.interface import _type_to_data
from compiler.erist.project import compile_entry
from compiler.erist.runtime_ext import Interpreter

ROOT=Path(__file__).resolve().parents[1]
CASES=json.loads((ROOT/'tests/fixtures/semantic_cases.json').read_text())


def materialize(root,case):
    for name,source in case['files'].items():
        path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(source,encoding='utf-8')
    return root/case['entry']


def contracts(module):
    result={}
    for name,function in module.analyzer.functions.items():
        spec=next(s for s in function.specializations.values() if s.state=='done')
        variables={}
        result[name]={'parameters':[_type_to_data(t,variables) for t in spec.parameter_types],
                      'result':_type_to_data(spec.return_type,variables),'fails':sorted(function.fails)}
    return result


class SelfHostedSemanticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.binary=Path(cls.temp.name)/'erist-frontend'
        if build_native(ROOT/'src/frontend.eri',cls.binary,ROOT/'src'):
            cls.temp.cleanup();raise AssertionError('semantic frontend failed to compile')

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def invoke(self,entry,root,command='analyze',**kwargs):
        return subprocess.run([str(self.binary),command,str(entry),'--source-root',str(root)],
                              capture_output=True,text=True,timeout=120,**kwargs)

    def test_corpus_is_independently_frozen_against_stage0(self):
        self.assertEqual(len({c['name'] for c in CASES}),len(CASES))
        for case in CASES:
            with self.subTest(case=case['name']),tempfile.TemporaryDirectory() as td:
                root=Path(td);entry=materialize(root,case)
                if case['accept']:
                    compile_entry(entry,root)
                else:
                    with self.assertRaises(EristaviError) as raised:
                        compile_entry(entry,root)
                    error=raised.exception;expected=case['referenceDiagnostic']
                    self.assertEqual(error.kind,expected['phase']+' error')
                    if error.location is not None:
                        self.assertEqual((error.location.line,error.location.column),(expected['line'],expected['column']))

    def test_compiled_semantic_acceptance_and_diagnostics_match_the_corpus(self):
        for case in CASES:
            with self.subTest(case=case['name']),tempfile.TemporaryDirectory() as td:
                root=Path(td);entry=materialize(root,case)
                result=self.invoke(entry,root)
                self.assertEqual(result.returncode,0 if case['accept'] else 1,result.stderr)
                self.assertEqual(result.stdout,'')
                if case['accept']:
                    self.assertEqual(result.stderr,'')
                else:
                    expected=case['diagnostic']
                    match=re.search(r'^(.*):(\d+):(\d+): (\w+) error(?: \[(\w+)\])?: (.+)',result.stderr)
                    self.assertIsNotNone(match,result.stderr)
                    self.assertEqual(Path(match[1]).relative_to(root),Path(expected['path']))
                    self.assertEqual((int(match[2]),int(match[3]),match[4]),(expected['line'],expected['column'],expected['phase']))
                    self.assertEqual(match[5],expected.get('category'))
                    self.assertTrue(match[6].strip())

    def test_inferred_function_contracts_match_stage0(self):
        for case in CASES:
            if not case['accept']:
                continue
            with self.subTest(case=case['name']),tempfile.TemporaryDirectory() as td:
                root=Path(td);entry=materialize(root,case)
                reference=contracts(compile_entry(entry,root))
                result=self.invoke(entry,root,'analyze-report')
                self.assertEqual(result.returncode,0,result.stderr)
                report=json.loads(result.stdout)
                self.assertEqual(report['format'],'eristavi-semantics-v1')
                self.assertTrue(report['experimental'])
                actual={f['name']:{'parameters':f['parameters'],'result':f['result'],'fails':sorted(f['fails'])} for f in report['functions']}
                self.assertEqual(actual,reference)
                self.assertGreaterEqual(report['expressionFacts'],0)

    def test_analyzer_checks_its_own_frontend_module_graph_offline(self):
        result=self.invoke(ROOT/'src/frontend.eri',ROOT/'src',env={'PATH':'','LANG':'C'})
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout,'')

    def test_reference_execution_of_eristavi_analyzer_matches_compiled_execution(self):
        selected=[next(c for c in CASES if c['name']==name) for name in ('generic_nested_list_0','fixed_nested_identity','module_checked')]
        module=compile_entry(ROOT/'src/frontend.eri',ROOT/'src')
        for case in selected:
            with self.subTest(case=case['name']),tempfile.TemporaryDirectory() as td:
                root=Path(td);entry=materialize(root,case);output=[];errors=[]
                interpreter=Interpreter(output.append,module.module_id,module.imports,
                                        arguments=['analyze',str(entry),'--source-root',str(root)],error_output=errors.append)
                interpreter.run(module.program)
                compiled=self.invoke(entry,root)
                self.assertEqual(interpreter.process_state.exit_code,compiled.returncode)
                self.assertEqual(''.join(line+'\n' for line in output),compiled.stdout)
                self.assertEqual(''.join(line+'\n' for line in errors),compiled.stderr)

    def test_entry_outside_source_root_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);entry=root/'outside.eri';entry.write_text('output(1);')
            source_root=root/'src';source_root.mkdir()
            result=self.invoke(entry,source_root)
            self.assertEqual(result.returncode,1)
            self.assertIn('semantic error [module]',result.stderr)
            self.assertIn('inside the configured source root',result.stderr)

    def test_symlinked_entry_outside_source_root_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);source_root=root/'src';source_root.mkdir()
            outside=root/'outside.eri';outside.write_text('output(1);')
            entry=source_root/'link.eri';entry.symlink_to(outside)
            result=self.invoke(entry,source_root)
            self.assertEqual(result.returncode,1)
            self.assertIn('inside the configured source root',result.stderr)

    def test_relative_source_roots_and_module_cache_preserve_visibility(self):
        case=next(c for c in CASES if c['name']=='module_duplicate_paths')
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);materialize(root,case)
            result=self.invoke('app.eri','.',cwd=root)
            self.assertEqual(result.returncode,0,result.stderr)

    def test_semantic_failure_does_not_run_entry_code_or_create_outputs(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);entry=root/'app.eri';entry.write_text('output("must not run"); output(missing);')
            result=self.invoke(entry,root)
            self.assertEqual(result.returncode,1)
            self.assertEqual(result.stdout,'')
            self.assertEqual(sorted(p.name for p in root.iterdir()),['app.eri'])
