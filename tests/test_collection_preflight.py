"""Small regressions for integration boundaries, without compiler self-builds."""
import tempfile
import unittest
from pathlib import Path

from compiler.erist.cli import compile_frontend, lower_project, lower_universal_file
from compiler.erist.c_backend_views import CBackend
from compiler.erist.diagnostics import SemanticError
from compiler.erist.interface import ModuleInterface
from compiler.erist.project import ProjectCompiler, compile_entry, compile_module
from compiler.erist.runtime import Interpreter as CoreInterpreter
from compiler.erist.runtime_ext import Interpreter


class CollectionPreflightTests(unittest.TestCase):
    def execute(self, source, interpreter=Interpreter):
        output=[]
        interpreter(output=output.append).run(compile_frontend(source))
        return output

    def test_existing_list_reads_evaluate_base_and_index_once(self):
        source='''
        function values() { output("base"); return [42]; }
        function index() returns Int { output("index"); return 0; }
        output(values()[index()]);
        '''
        for interpreter in (CoreInterpreter, Interpreter):
            with self.subTest(interpreter=interpreter.__module__):
                self.assertEqual(self.execute(source,interpreter),['base','index','42'])

    def test_existing_member_and_text_view_reads_evaluate_once(self):
        self.assertEqual(self.execute('''
            function values() { output("base"); return [42]; }
            function text() returns Text { output("text"); return "ab"; }
            output(values().count); output(text().characters[0]);
        '''),['base','1','text','a'])

    def test_nested_writable_paths_evaluate_each_index_once(self):
        self.assertEqual(self.execute('''
            function index() returns Int { output("index"); return 0; }
            let values be [[1]]; values[index()][index()] = 9;
            output(values[0][0]);
        '''),['index','index','9'])

    def test_map_and_bytes_reads_evaluate_each_operand_once(self):
        self.assertEqual(self.execute('''
            function key() returns Text { output("key"); return "a"; }
            function index() returns Int { output("index"); return 0; }
            let values be ["a" : 42;]; let data Bytes be [7];
            output(values[key()]); output(data[index()]);
        '''),['key','42','index','7'])

    def test_collection_interfaces_round_trip_without_implementation_source(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);library=root/'lib.eri';entry=root/'app.eri'
            library.write_text('''
                public function values() { return ["a" : ["b" : 42;];]; }
                public function echo(data Bytes) returns Bytes { return data; }
            ''')
            compiled=compile_module(library,root)
            original=compiled.interface.to_json()
            self.assertEqual(ModuleInterface.from_json(original).to_json(),original)
            ProjectCompiler.interface_path(library).write_text(original)
            library.unlink()
            entry.write_text('import lib; let values be lib.values(); output(values["a"]["b"]); output(lib.echo([1,2]).count);')
            compile_entry(entry,root)

    def test_nested_collections_keep_value_semantics(self):
        self.assertEqual(self.execute('''
            let data Bytes be [1]; let original be ["a" : [data];];
            let copy be original; copy["a"][0][0] = 2;
            output(original["a"][0][0]); output(copy["a"][0][0]);
        '''),['1','2'])

    def test_unimplemented_codegen_reports_source_diagnostic(self):
        for source in ('let values be ["a" : 42;]; output(values["a"]);',
                       'let values Bytes be [1,2]; output(values[0]);'):
            with self.subTest(source=source),tempfile.TemporaryDirectory() as td:
                root=Path(td);entry=root/'app.eri';entry.write_text(source)
                for backend in (lambda:CBackend().emit(lower_project(compile_entry(entry,root))),
                                lambda:lower_universal_file(entry,root)):
                    with self.assertRaisesRegex(SemanticError,'Map/Bytes code generation'):
                        backend()

    def test_text_containing_type_names_is_not_a_codegen_capability(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);entry=root/'app.eri';entry.write_text('output("Bytes"); output("Map from Text to Int");')
            CBackend().emit(lower_project(compile_entry(entry,root)))
            lower_universal_file(entry,root)


if __name__=='__main__':
    unittest.main()
