from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from compiler.erist.cli import build_native
from compiler.erist.diagnostics import LexError, ParseError
from compiler.erist.project import compile_entry
from compiler.erist.runtime_ext import Interpreter
from frontend_contract import reference_tree

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / 'tests/fixtures/frontend_cases.json').read_text())


class FrontendToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.binary = Path(cls.temp.name) / 'erist-frontend'
        if build_native(ROOT/'src/frontend.eri', cls.binary, ROOT/'src'):
            cls.temp.cleanup()
            raise AssertionError('Eristavi frontend failed to compile')

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def invoke(self, *arguments, **kwargs):
        return subprocess.run([str(self.binary), *map(str,arguments)], capture_output=True,
                              text=True, timeout=60, **kwargs)

    def test_shared_valid_corpus_matches_complete_reference_ast_and_locations(self):
        for case in CASES:
            if not case['valid']:
                continue
            with self.subTest(case=case['name']), tempfile.TemporaryDirectory() as td:
                source=Path(td)/'source.eri';source.write_text(case['source'],newline='',encoding='utf-8')
                result=self.invoke('ast',source)
                self.assertEqual(result.returncode,0,result.stderr)
                report=json.loads(result.stdout)
                self.assertEqual(report['format'],'eristavi-ast-v1')
                self.assertTrue(report['syntaxOnly'])
                self.assertEqual(report['tree'],reference_tree(case['source']))

    def test_shared_invalid_corpus_matches_reference_phase_and_error_location(self):
        for case in CASES:
            if case['valid']:
                continue
            with self.subTest(case=case['name']), tempfile.TemporaryDirectory() as td:
                try:
                    reference_tree(case['source'])
                except (LexError,ParseError) as error:
                    expected=(error.location.line,error.location.column,'lex' if isinstance(error,LexError) else 'parse')
                else:
                    self.fail('negative corpus entry was accepted by Stage-0')
                source=Path(td)/'source.eri';source.write_text(case['source'],newline='',encoding='utf-8')
                result=self.invoke('check',source)
                self.assertEqual(result.returncode,1,result.stderr)
                self.assertEqual(result.stdout,'')
                match=re.search(r':(\d+):(\d+): (lex|parse) error:',result.stderr)
                self.assertIsNotNone(match,result.stderr)
                self.assertEqual((int(match[1]),int(match[2]),match[3]),expected)

    def test_repository_eristavi_sources_match_reference_ast(self):
        for source in sorted((ROOT/'src').rglob('*.eri')):
            with self.subTest(source=source.relative_to(ROOT)):
                result=self.invoke('ast',source)
                self.assertEqual(result.returncode,0,result.stderr)
                self.assertEqual(json.loads(result.stdout)['tree'],reference_tree(source.read_text()))

    def test_relative_paths_use_the_process_working_directory(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);source=root/'input λ.eri';source.write_text('let x be 1;')
            result=self.invoke('ast',source.name,'--output','report.json',cwd=root)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(json.loads((root/'report.json').read_text())['tree'],reference_tree(source.read_text()))

    def test_offline_executable_needs_no_python_or_c_compiler_at_runtime(self):
        result=self.invoke('check',ROOT/'examples/hello.eri',env={'PATH':'','LANG':'C'})
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout,'')

    def test_new_report_file_contains_valid_json_and_input_is_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            source=Path(td)/'source with spaces λ.eri';source.write_text('let café be "😀";')
            output=Path(td)/'report with spaces.json'
            result=self.invoke('ast',source,'--output',output)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(result.stdout,'')
            self.assertEqual(json.loads(output.read_text())['tree'],reference_tree(source.read_text()))
            self.assertEqual(source.read_text(),'let café be "😀";')
            repeated=self.invoke('ast',source,'--output',output)
            self.assertEqual(repeated.returncode,1)
            self.assertIn('file error:',repeated.stderr)
            same=self.invoke('ast',source,'--output',source)
            self.assertEqual(same.returncode,1)
            self.assertEqual(source.read_text(),'let café be "😀";')

    def test_syntax_failure_creates_no_report(self):
        with tempfile.TemporaryDirectory() as td:
            source=Path(td)/'bad.eri';source.write_text('let value be ;')
            report=Path(td)/'report.json'
            result=self.invoke('ast',source,'--output',report)
            self.assertEqual(result.returncode,1)
            self.assertFalse(report.exists())

    def test_missing_and_invalid_utf8_inputs_are_checked_file_errors(self):
        with tempfile.TemporaryDirectory() as td:
            missing=self.invoke('check',Path(td)/'missing.eri')
            self.assertEqual(missing.returncode,1);self.assertIn('file error:',missing.stderr)
            invalid=Path(td)/'invalid.eri';invalid.write_bytes(b'\xff')
            result=self.invoke('check',invalid)
            self.assertEqual(result.returncode,1);self.assertIn('file error:',result.stderr)

    def test_token_report_preserves_decoded_text_and_nfc_identifier(self):
        with tempfile.TemporaryDirectory() as td:
            source=Path(td)/'text.eri';source.write_text('let cafe\u0301 be "A\\u{0}\\n";')
            result=self.invoke('tokens',source)
            self.assertEqual(result.returncode,0,result.stderr)
            tokens=json.loads(result.stdout)['tokens']
            self.assertEqual(tokens[1][1:3],['cafe\u0301','café'])
            self.assertEqual(tokens[3][2],'A\0\n')

    def test_usage_and_help_have_distinct_exit_codes(self):
        for arguments in [(),('unknown','file.eri'),('check',),('check','x','--output','y')]:
            with self.subTest(arguments=arguments):
                result=self.invoke(*arguments)
                self.assertEqual(result.returncode,2)
                self.assertIn('Usage:',result.stderr)
        help_result=self.invoke('--help')
        self.assertEqual(help_result.returncode,0)
        self.assertIn('syntax only',help_result.stdout)

    def test_frontend_accepts_syntax_without_claiming_semantic_validation(self):
        with tempfile.TemporaryDirectory() as td:
            source=Path(td)/'not_typed.eri';source.write_text('let value be unknown(1);')
            self.assertEqual(self.invoke('check',source).returncode,0)

    def test_reference_frontend_matches_compiled_report_and_status(self):
        with tempfile.TemporaryDirectory() as td:
            source=Path(td)/'source.eri';source.write_text('let café be [1,2]; output(café[0]);')
            arguments=['ast',str(source)]
            module=compile_entry(ROOT/'src/frontend.eri',ROOT/'src')
            output=[];errors=[]
            interpreter=Interpreter(output.append,module.module_id,module.imports,arguments=arguments,error_output=errors.append)
            interpreter.run(module.program)
            compiled=self.invoke(*arguments)
            self.assertEqual(interpreter.process_state.exit_code,compiled.returncode)
            self.assertEqual(json.loads(output[0]),json.loads(compiled.stdout))
            self.assertEqual(errors,[])

    def test_opt_in_phase_trace_preserves_reports_assembly_and_unicode_paths(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);source=root/'entry λ\u2028\n.eri'
            source.write_text('import helper; output(helper.double(2));')
            (root/'helper.eri').write_text('public function double(x Int) returns Int { return x*2; }')
            cases=[('check',()),('ast',()),('tokens',()),('analyze',('--source-root',root)),
                   ('analyze-report',('--source-root',root)),('ir',('--source-root',root)),
                   ('uir',('--source-root',root)),('emit-c',('--source-root',root)),
                   ('emit-asm',('--source-root',root,'--target','x86_64-linux')),
                   ('emit-asm',('--source-root',root,'--target','arm64-linux'))]
            for command,options in cases:
                with self.subTest(command=command,options=options):
                    plain=self.invoke(command,source,*options)
                    traced=self.invoke(command,source,'--trace-phases',*options)
                    self.assertEqual((plain.returncode,plain.stderr),(0,''))
                    self.assertEqual((traced.returncode,traced.stdout),(0,plain.stdout))
                    records=[]
                    for line in traced.stderr.split("\n"):
                        if not line:continue
                        self.assertTrue(line.startswith('[erist-phase] '),line)
                        records.append(json.loads(line[len('[erist-phase] '):]))
                    self.assertEqual(records[0],{'event':'begin','phase':'read','subject':str(source)})
                    self.assertTrue(any(row['event']=='end' and row['phase']=='read' for row in records))
                    if command in ('uir','emit-asm'):
                        for phase in ('typed-ir-verify','typed-ir-structure','typed-ir-descriptors','typed-ir-function','universal-lower-function'):
                            events=[row['event'] for row in records if row['phase']==phase]
                            self.assertTrue(events,phase)
                            self.assertEqual(events.count('begin'),events.count('end'),phase)
                    if command=='emit-asm':
                        self.assertTrue(any(row['phase']=='emit-function' for row in records))
                        self.assertTrue(any(row['phase']=='lower-function' for row in records))
                        self.assertEqual(records[-1]['phase'],'write-output')

    def test_phase_trace_preserves_failure_status_and_original_diagnostics(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);source=root/'input.eri'
            for contents in ('"unterminated','let value be ;','output(missing);',None):
                with self.subTest(contents=contents):
                    if contents is None:source.unlink()
                    else:source.write_text(contents)
                    plain=self.invoke('analyze',source,'--source-root',root)
                    traced=self.invoke('analyze',source,'--source-root',root,'--trace-phases')
                    self.assertEqual((plain.returncode,traced.returncode),(1,1))
                    self.assertEqual(traced.stdout,plain.stdout)
                    diagnostic=re.sub(r'(?m)^\[erist-phase\] [^\n]*\n','',traced.stderr)
                    self.assertEqual(diagnostic,plain.stderr)
                    self.assertIn('[erist-phase] ',traced.stderr)

    def test_phase_flag_does_not_hide_duplicate_or_incomplete_options(self):
        for options in [('--trace-phases','--trace-phases'),('--trace-phases','--source-root'),
                        ('--trace-phases','--target','unknown'),('--trace-phases','--output','unused')]:
            with self.subTest(options=options):
                result=self.invoke('emit-asm',ROOT/'examples/hello.eri',*options)
                self.assertEqual(result.returncode,2,result.stderr)
                self.assertIn('Usage:',result.stderr)
