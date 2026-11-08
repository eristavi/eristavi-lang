"""Canonical managed aggregate make/get/set use existing owned graph helpers."""
from pathlib import Path
import platform
import subprocess
from compiler.erist.cli import compile_entry, build_native
from compiler.erist.runtime_ext import Interpreter
import unittest
import test_u2_function_import_integration as imports
import test_freestanding_graph_values as graph
ROOT=Path(__file__).resolve().parents[1]

def descriptors():
    s=graph.descriptors()
    at=s.index('.section .rodata\n')
    return s[:at]+'.long 6,0\n.quad .Lrecord_name,2,.Lrecord_fields\n.long 6,0\n.quad .Louter_name,2,.Louter_fields\n.globl ev_types_end\nev_types_end:\n'+s[at:]+'.Lrecord_name:\n.asciz "Record"\n.Louter_name:\n.asciz "Outer"\n.p2align 2\n.Lrecord_fields:\n.long 1,4\n.Louter_fields:\n.long 15,7\n'

@unittest.skipUnless(platform.system()=='Linux' and platform.machine().lower() in ('x86_64','amd64'),'native aggregate requires Linux x86-64')
class U2FunctionValueAggregateTests(unittest.TestCase):
    setUpClass=imports.U2FunctionImportIntegrationTests.__dict__['setUpClass']
    generator=imports.U2FunctionImportIntegrationTests.generator
    run_probe=imports.U2FunctionImportIntegrationTests.run_probe
    def source(self): return (ROOT/'tests/fixtures/u2_function_value_aggregate.eri').read_text()
    def test_nested_aggregate_snapshot_text_list_and_forced_gc(self):
        result=self.generator('aggregate-values',self.source())
        self.assertEqual((result.returncode,result.stderr),(0,''),result.stdout[-2500:])
        starter='\n.text\n.globl _start\n_start:\n xorl %edi,%edi\n xorl %esi,%esi\n call erist_u2_rooted_function_96\n cmpq $7,%rax\n jne .Lgraph_test_fail\n jmp .Lgraph_finish\n'
        run=self.run_probe('aggregate-native',result.stdout+starter+graph.FINISH+descriptors(),types=False)
        self.assertEqual((run.returncode,run.stdout,run.stderr),(0,b'',b''))

    def test_independent_source_value_copy(self):
        entry=ROOT/'tests/fixtures/u2_value_aggregate_reference.eri'
        module=compile_entry(entry,entry.parent); observed=[]
        Interpreter(output=observed.append,module_id=module.module_id,
                    imported_modules=module.imports).run(module.program)
        self.assertEqual(observed,['7'])
        binary=self.directory/'aggregate-reference'
        self.assertEqual(build_native(entry,binary,entry.parent),0)
        result=subprocess.run([str(binary)],capture_output=True,timeout=30)
        self.assertEqual((result.returncode,result.stdout,result.stderr),(0,b'7\n',b''))

    def test_missing_duplicate_and_wrong_descriptor_layouts_refuse(self):
        source=self.source()
        for name,changed in (
            ('missing',source.replace('[4,7,15,16]','[4,7,15]')),
            ('duplicate',source.replace('[4,7,15,16]','[4,7,15,15]')),
            ('zero',source.replace('[4,7,15,16]','[4,7,0,16]')),
            ('identity',source.replace('managed.valueOfBase(managedTable,p,box)',
                                      'managed.identityOfBase(managedTable,p,box)')),
            ('wrong-shape',source.replace('managed.valueOfBase(managedTable,p,outer)',
                                         'managed.valueOfBase(managedTable,p,carrier)')),
            ('missing-child',source.replace('[text,carrier,box,outer]', '[carrier,box,outer]')
                .replace('[managed.text(managedTable),managedList,boxType,outerType]',
                         '[managedList,boxType,outerType]').replace('[4,7,15,16]', '[7,15,16]'))):
            with self.subTest(case=name):
                self.assertNotEqual(changed,source)
                result=self.generator('aggregate-bad-'+name,changed)
                self.assertNotEqual(result.returncode,0,result.stdout[-1800:])
                self.assertNotIn('.section',result.stdout)

    def test_linked_layout_mismatch_and_out_of_table_are_terminal(self):
        for name,source,layout in (
            ('kind',self.source(),descriptors().replace('.long 6,0\n.quad .Lrecord_name',
                                                       '.long 9,0\n.quad .Lrecord_name')),
            ('fields',self.source(),descriptors().replace('.long 1,4\n', '.long 4,1\n')),
            ('count',self.source(),descriptors().replace('.Lrecord_name,2,', '.Lrecord_name,1,')),
            ('out-of-table',self.source().replace('[4,7,15,16]','[4,7,255,16]'),descriptors())):
            with self.subTest(case=name):
                result=self.generator('aggregate-layout-'+name,source)
                self.assertEqual((result.returncode,result.stderr),(0,''),result.stdout[-1800:])
                starter='\n.text\n.globl _start\n_start:\n xorl %edi,%edi\n xorl %esi,%esi\n call erist_u2_rooted_function_96\n jmp .Lgraph_test_fail\n'
                run=self.run_probe('aggregate-terminal-'+name,result.stdout+starter+graph.FINISH+layout,types=False)
                self.assertEqual(run.returncode,1)
                self.assertIn(b'Eristavi runtime fault',run.stderr)

    def test_predicate_fields_are_boxed_and_unboxed_as_predicates(self):
        source=self.source().replace('aggregate.aggregate(g,p,[intType,text])',
            'aggregate.aggregate(g,p,[try aggregate.primitive(g,meta.pred()),text])')
        source=source.replace('let record be try ab.make(fn,g,done,box,[oldCount,ten],loc);',
            'let yes be try build.predicate(fn,done,true,loc);\n let no be try build.predicate(fn,done,false,loc);\n let record be try ab.make(fn,g,done,box,[yes,ten],loc);')
        source=source.replace('record,0,newCount,loc','record,0,no,loc')
        source=source.replace('let sum be try build.wrapAdd(fn,good,oldInteger,newInteger,loc);',
            'let sum be try build.wrapAdd(fn,good,oldCount,newCount,loc);')
        source=source.replace('try ab.branch(fn,g,done,oldEqual,',
            'oldEqual=try build.andPredicate(fn,done,oldEqual,oldInteger,loc);\n try ab.branch(fn,g,done,oldEqual,')
        source=source.replace('try ab.branch(fn,g,secondCheck,newEqual,',
            'let inverted be try build.negatePredicate(fn,secondCheck,newInteger,loc);\n newEqual=try build.andPredicate(fn,secondCheck,newEqual,inverted,loc);\n try ab.branch(fn,g,secondCheck,newEqual,')
        result=self.generator('aggregate-predicates',source)
        self.assertEqual((result.returncode,result.stderr),(0,''),result.stdout[-2000:])
        starter='\n.text\n.globl _start\n_start:\n xorl %edi,%edi\n xorl %esi,%esi\n call erist_u2_rooted_function_96\n cmpq $7,%rax\n jne .Lgraph_test_fail\n jmp .Lgraph_finish\n'
        run=self.run_probe('aggregate-predicate-native',result.stdout+starter+graph.FINISH+
                           descriptors().replace('.long 1,4\n','.long 0,4\n'),types=False)
        self.assertEqual((run.returncode,run.stdout,run.stderr),(0,b'',b''))

    def test_new_descriptor_policy_domain_and_primitive_shape_refuse(self):
        source=self.source().replace('import compiler.u1_budget as budget;',
            'import compiler.u1_budget as budget;\nimport compiler.u1_words as words;')
        for name,changed in (
            ('policy',source.replace('try managed.freeze(managedTable);',
                'try words.set(managedTable.records,p,(boxType.index-1)*4+3,2);\n try managed.freeze(managedTable);')),
            ('domain',source.replace('try managed.freeze(managedTable);',
                'try words.set(managedTable.records,p,(boxType.index-1)*4+1,1);\n try managed.freeze(managedTable);')),
            ('primitive',source.replace('managed.valueOfBase(managedTable,p,box)',
                                       'managed.valueOfBase(managedTable,p,intType)'))):
            with self.subTest(case=name):
                self.assertNotEqual(changed,source)
                result=self.generator('aggregate-descriptor-'+name,changed)
                self.assertNotEqual(result.returncode,0,result.stdout[-2000:])
                self.assertNotIn('.section',result.stdout)
