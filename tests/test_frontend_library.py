from __future__ import annotations

import io
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from compiler.erist.cli import build_native, main, analyze_frontend
from compiler.erist.diagnostics import RuntimeFault, SemanticError
from compiler.erist.project import compile_entry
from compiler.erist.runtime_ext import Interpreter
from selfhost_support import literal


class FrontendLibraryTests(unittest.TestCase):
    def both(self, root, source, arguments=()):
        entry=root/'app.eri';entry.write_text(source)
        module=compile_entry(entry,root)
        output=[];errors=[]
        interpreter=Interpreter(output.append,module.module_id,module.imports,arguments=arguments,error_output=errors.append)
        interpreter.run(module.program)
        binary=root/'app'
        self.assertEqual(build_native(entry,binary,root),0)
        result=subprocess.run([str(binary),*arguments],capture_output=True,timeout=30)
        result.stdout=result.stdout.decode('utf-8');result.stderr=result.stderr.decode('utf-8')
        self.assertEqual(result.returncode,interpreter.process_state.exit_code,result.stderr)
        self.assertEqual(result.stdout,''.join(item+'\n' for item in output))
        self.assertEqual(result.stderr,''.join(item+'\n' for item in errors))
        return result

    def test_process_arguments_are_value_snapshots_with_unicode_and_empty_values(self):
        source=('import std.process as p; '
                'let first be p.arguments(); first[0] = "changed"; '
                'let second be p.arguments(); for item in second { output(item); } '
                'output(first[0]);')
        with tempfile.TemporaryDirectory() as td:
            result=self.both(Path(td),source,['a b','λ😀',''])
            self.assertEqual(result.stdout,'a b\nλ😀\n\nchanged\n')

    def test_process_state_is_shared_across_imported_calls(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/'helper.eri').write_text('import std.process; public function inspect() { '
                                          'output(process.arguments()[0]); '
                                          'process.writeError("diagnostic"); process.setExitCode(7); }')
            result=self.both(root,'import helper; helper.inspect(); output("after");',['argument'])
            self.assertEqual(result.returncode,7)
            self.assertEqual(result.stdout,'argument\nafter\n')

    def test_exit_status_preserves_deterministic_resource_cleanup(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);path=root/'resource.txt';path.write_text('ready')
            source=('import std.files; import std.process; '
                    'function use(path Text) fails files.FileError { '
                    'with file be try files.openRead(path) { process.setExitCode(9); output(try file.readText()); } } '
                    f'use({literal(str(path))}) else error {{ output(error.message); }};')
            self.assertEqual(self.both(root,source).returncode,9)

    def test_readonly_file_write_is_checked_and_preserves_content(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);path=root/'input.txt';path.write_text('original\r\nλ',newline='')
            source=('import std.files; function probe(path Text) fails files.FileError { '
                    'with file be try files.openRead(path) { '
                    'file.writeText("changed") else error files.FileError { output(error.path); }; '
                    'output(try file.readText()); } } '
                    f'probe({literal(str(path))}) else error {{ output(error.message); }};')
            self.both(root,source)
            self.assertEqual(path.read_bytes(),'original\r\nλ'.encode())

    def test_exclusive_create_does_not_truncate_existing_files(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);path=root/'existing.txt';path.write_text('preserve me')
            source=('import std.files; function create(path Text) fails files.FileError { '
                    'with file be try files.create(path) { try file.writeText("replace"); } } '
                    f'create({literal(str(path))}) else error files.FileError {{ output(error.path); }};')
            self.both(root,source)
            self.assertEqual(path.read_text(),'preserve me')

    def test_exclusive_create_writes_utf8_and_embedded_nul(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            source=('import std.files; import std.process; '
                    'function create(path Text) fails files.FileError { '
                    'with file be try files.create(path) { try file.writeText("A\\0λ\\n"); } } '
                    'create(process.arguments()[0]) else error { output(error.message); };')
            entry=root/'app.eri';entry.write_text(source)
            module=compile_entry(entry,root)
            first=root/'reference.txt';second=root/'compiled.txt'
            Interpreter(module_id=module.module_id,imported_modules=module.imports,arguments=[str(first)]).run(module.program)
            binary=root/'app';self.assertEqual(build_native(entry,binary,root),0)
            result=subprocess.run([str(binary),str(second)],capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(first.read_bytes(),b'A\0\xce\xbb\n')
            self.assertEqual(second.read_bytes(),first.read_bytes())

    def test_invalid_nul_paths_are_checked_file_failures(self):
        with tempfile.TemporaryDirectory() as td:
            source=('import std.files; function probe() fails files.FileError { '
                    'with file be try files.openRead("bad\\0path") { output(try file.readText()); } } '
                    'probe() else error { output("caught"); };')
            self.assertEqual(self.both(Path(td),source).stdout,'caught\n')

    def test_reference_cli_forwards_arguments_only_after_separator(self):
        with tempfile.TemporaryDirectory() as td:
            source=Path(td)/'args.eri'
            source.write_text('import std.process; output(process.arguments()[0]); process.setExitCode(4);')
            output=io.StringIO()
            with redirect_stdout(output):
                status=main(['run',str(source),'--','--help'])
            self.assertEqual(status,4);self.assertEqual(output.getvalue(),'--help\n')
            with redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):
                main(['check',str(source),'--','argument'])

    def test_check_cli_keeps_standard_separator_for_dash_prefixed_paths(self):
        import os
        with tempfile.TemporaryDirectory() as td:
            previous=Path.cwd()
            try:
                os.chdir(td)
                Path('-input.eri').write_text('output(1);')
                self.assertEqual(main(['check','--','-input.eri']),0)
            finally:
                os.chdir(previous)

    def test_canonical_paths_resolve_existing_unicode_paths_and_symlinks(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);folder=root/'folder';folder.mkdir();target=root/'λ.txt';target.write_text('content')
            alias=root/'alias.txt';alias.symlink_to(target)
            source=('import std.files; function probe(path Text) { '
                    'let value be files.canonicalPath(path) else error { output(error.message); return; }; '
                    'output(value); } '+f'probe({literal(str(folder/".."/"alias.txt"))});')
            result=self.both(root,source)
            self.assertEqual(result.stdout,str(target.resolve())+'\n')

    def test_canonical_path_failures_use_checked_file_error(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            source=('import std.files; function probe(path Text) { '
                    'let value be files.canonicalPath(path) else error files.FileError { output("caught"); return; }; '
                    'output(value); } '
                    f'probe({literal(str(root/"missing"))}); probe("bad\\0path");')
            self.assertEqual(self.both(root,source).stdout,'caught\ncaught\n')

    def test_process_contracts_reject_invalid_types_and_exit_ranges(self):
        for call in ['process.arguments(1)', 'process.setExitCode("x")', 'process.writeError(1)',
                     'process.unknown()', 'output(process.setExitCode(1))']:
            with self.subTest(call=call),self.assertRaises(SemanticError):
                analyze_frontend('import std.process; '+call+';')
        for code in [-1,256]:
            source='import std.process; process.setExitCode('+str(code)+');'
            program,_=analyze_frontend(source)
            with self.assertRaises(RuntimeFault):
                Interpreter().run(program)
            with tempfile.TemporaryDirectory() as td:
                root=Path(td);entry=root/'app.eri';entry.write_text(source);binary=root/'app'
                self.assertEqual(build_native(entry,binary,root),0)
                result=subprocess.run([str(binary)],capture_output=True,text=True)
                self.assertEqual(result.returncode,1)
                self.assertIn('exit code must be',result.stderr)
