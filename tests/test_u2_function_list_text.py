"""Canonical List<Text> producers, snapshots and Text roots in native CFG."""
from pathlib import Path
import platform
import unittest
import subprocess
from compiler.erist.cli import compile_entry,build_native
from compiler.erist.runtime_ext import Interpreter
import test_u2_function_import_integration as imports

ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(platform.system()=='Linux' and platform.machine().lower() in ('x86_64','amd64'),
                     'native List<Text> requires Linux x86-64')
class U2FunctionListTextTests(unittest.TestCase):
    setUpClass=imports.U2FunctionImportIntegrationTests.__dict__['setUpClass']
    generator=imports.U2FunctionImportIntegrationTests.generator
    run_probe=imports.U2FunctionImportIntegrationTests.run_probe
    run_native=imports.U2FunctionImportIntegrationTests.run_native
    def source(self):
        return (ROOT/'tests/fixtures/u2_function_list_text.eri').read_text()
    def test_text_elements_snapshot_copy_replace_and_forced_gc(self):
        result=self.generator('list-text',self.source())
        self.assertEqual((result.returncode,result.stderr),(0,''),result.stdout[-2200:])
        self.run_native(result.stdout,'list-text-native',4,'96')
    def test_wrong_element_descriptor_and_import_type_refuse(self):
        source=self.source()
        for name,changed in (
            ('descriptor',source.replace('managed.listOfManaged(managedTable,p,managed.text(managedTable))',
                'managed.listOfBase(managedTable,p,intType)')),
            ('effects',source.replace('imports.textListName(3),2,63,1', 'imports.textListName(3),2,8,1')),
            ('type',source.replace('[carrier,text],[carrier]', '[carrier,intType],[carrier]',1))):
            result=self.generator('bad-list-text-'+name,changed)
            self.assertNotEqual(result.returncode,0,result.stdout[-1800:])
            self.assertNotIn('.globl',result.stdout)

    def test_independent_source_value_semantics(self):
        entry=ROOT/'tests/fixtures/u2_list_text_reference.eri'
        module=compile_entry(entry,entry.parent); observed=[]
        Interpreter(output=observed.append,module_id=module.module_id,
            imported_modules=module.imports).run(module.program)
        self.assertEqual(observed,['4'])
        binary=self.directory/'text-list-reference'
        self.assertEqual(build_native(entry,binary,entry.parent),0)
        result=subprocess.run([str(binary)],capture_output=True,timeout=30)
        self.assertEqual((result.returncode,result.stdout,result.stderr),(0,b'4\n',b''))

    def test_text_element_get_bounds_keep_terminal_source_fault(self):
        source=self.source().replace('f6,[changed,zero]', 'f6,[changed,newCount]')
        result=self.generator('list-text-bounds',source)
        self.assertEqual((result.returncode,result.stderr),(0,''),result.stdout[-2000:])
        starter='\n.text\n.globl _start\n_start:\n xorl %edi,%edi\n xorl %esi,%esi\n call erist_u2_rooted_function_96\n'
        run=self.run_probe('list-text-terminal',result.stdout+starter)
        self.assertEqual(run.returncode,1)
        self.assertIn(b'list-probe',run.stderr)
