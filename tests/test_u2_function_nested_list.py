"""Whole-Function boxed nested List producers share existing runtime semantics."""
from pathlib import Path
import platform
import subprocess
import unittest
from compiler.erist.cli import compile_entry, build_native
from compiler.erist.runtime_ext import Interpreter
import test_u2_function_import_integration as imports

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(platform.system() == 'Linux' and
                     platform.machine().lower() in ('x86_64', 'amd64'),
                     'nested native List requires Linux x86-64')
class U2FunctionNestedListTests(unittest.TestCase):
    setUpClass = imports.U2FunctionImportIntegrationTests.__dict__['setUpClass']
    generator = imports.U2FunctionImportIntegrationTests.generator
    run_probe = imports.U2FunctionImportIntegrationTests.run_probe
    run_native = imports.U2FunctionImportIntegrationTests.run_native

    def source(self, kind='text'):
        return (ROOT / f'tests/fixtures/u2_function_nested_{kind}_list.eri').read_text()

    def test_nested_text_and_i64_snapshot_constructors(self):
        for kind in ('text', 'i64'):
            with self.subTest(kind=kind):
                generated = self.generator('nested-' + kind, self.source(kind))
                self.assertEqual((generated.returncode, generated.stderr), (0, ''),
                                 generated.stdout[-2400:])
                self.run_native(generated.stdout, 'nested-native-' + kind, 13, '96')

    def test_independent_source_snapshots(self):
        for kind in ('text', 'i64'):
            with self.subTest(kind=kind):
                entry = ROOT / f'tests/fixtures/u2_nested_{kind}_list_reference.eri'
                module = compile_entry(entry, entry.parent)
                observed = []
                Interpreter(output=observed.append, module_id=module.module_id,
                            imported_modules=module.imports).run(module.program)
                self.assertEqual(observed, ['13'])
                binary = self.directory / ('nested-reference-' + kind)
                self.assertEqual(build_native(entry, binary, entry.parent), 0)
                result = subprocess.run([str(binary)], capture_output=True, timeout=30)
                self.assertEqual((result.returncode, result.stdout, result.stderr),
                                 (0, b'13\n', b''))

    def test_wrong_nested_descriptor_marker_effects_and_type_refuse(self):
        source = self.source()
        for name, changed in (
            ('descriptor', source.replace('managed.listOfManaged(managedTable,p,managedList)',
                                         'managed.listOfManaged(managedTable,p,managed.text(managedTable))')),
            ('marker', source.replace('aggregate.aggregate(g,p,[carrier])',
                                     'aggregate.aggregate(g,p,[text])')),
            ('missing-inner', source.replace('[text,carrier,outerCarrier]', '[text,outerCarrier]')
                             .replace('[managed.text(managedTable),managedList,nestedType]',
                                      '[managed.text(managedTable),nestedType]')),
            ('effects', source.replace('imports.nestedListName(true,3),2,63,1',
                                      'imports.nestedListName(true,3),2,8,1')),
            ('type', source.replace('[outerCarrier,carrier],[outerCarrier]',
                                   '[outerCarrier,text],[outerCarrier]', 1))):
            with self.subTest(case=name):
                self.assertNotEqual(changed, source)
                result = self.generator('bad-nested-' + name, changed)
                self.assertNotEqual(result.returncode, 0, result.stdout[-1800:])
                self.assertNotIn('.globl', result.stdout)

    def test_nested_get_and_replace_bounds_keep_terminal_source_fault(self):
        source = self.source()
        for op, changed in (
            ('get', source.replace('n6,[outerOriginal,zero]', 'n6,[outerOriginal,limit]')),
            ('replace', source.replace('n4,[outerCopy,zero,changed]',
                                       'n4,[outerCopy,limit,changed]'))):
            with self.subTest(operation=op):
                self.assertNotEqual(changed, source)
                result = self.generator('nested-bounds-' + op, changed)
                self.assertEqual((result.returncode, result.stderr), (0, ''),
                                 result.stdout[-2000:])
                starter = ('\n.text\n.globl _start\n_start:\n xorl %edi,%edi\n'
                           ' xorl %esi,%esi\n call erist_u2_rooted_function_96\n')
                run = self.run_probe('nested-terminal-' + op, result.stdout + starter)
                self.assertEqual(run.returncode, 1)
                self.assertIn(b'list-probe', run.stderr)
