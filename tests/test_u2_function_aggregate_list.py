"""Lists containing ordinary aggregates reuse exact canonical/runtime contracts."""
from pathlib import Path
import platform
import subprocess
from compiler.erist.cli import compile_entry,build_native
from compiler.erist.runtime_ext import Interpreter
import unittest
import test_u2_function_import_integration as imports
import test_u2_function_value_aggregate as values
import test_freestanding_graph_values as graph
import test_u2_function_managed_native as managed
ROOT=Path(__file__).resolve().parents[1]

@unittest.skipUnless(platform.system()=='Linux' and platform.machine().lower() in ('x86_64','amd64'), 'native aggregate List requires Linux x86-64')
class U2FunctionAggregateListTests(unittest.TestCase):
    setUpClass=imports.U2FunctionImportIntegrationTests.__dict__['setUpClass']
    generator=imports.U2FunctionImportIntegrationTests.generator
    run_probe=imports.U2FunctionImportIntegrationTests.run_probe
    def source(self): return (ROOT/'tests/fixtures/u2_function_aggregate_list.eri').read_text()
    def test_multiple_aggregate_list_shapes_and_nested_snapshots(self):
        result=self.generator('aggregate-lists',self.source())
        self.assertEqual((result.returncode,result.stderr),(0,''),result.stdout[-2400:])
        starter='\n.text\n.globl _start\n_start:\n xorl %edi,%edi\n xorl %esi,%esi\n call erist_u2_rooted_function_96\n cmpq $13,%rax\n jne .Lgraph_test_fail\n jmp .Lgraph_finish\n'
        run=self.run_probe('aggregate-lists-native',result.stdout+starter+graph.FINISH+values.descriptors(),types=False)
        self.assertEqual((run.returncode,run.stdout,run.stderr),(0,b'',b''))

    def test_independent_source_list_record_and_nested_value_semantics(self):
        entry=ROOT/'tests/fixtures/u2_aggregate_list_reference.eri'
        module=compile_entry(entry,entry.parent); observed=[]
        Interpreter(output=observed.append,module_id=module.module_id,
                    imported_modules=module.imports).run(module.program)
        self.assertEqual(observed,['13'])
        binary=self.directory/'aggregate-list-reference'
        self.assertEqual(build_native(entry,binary,entry.parent),0)
        result=subprocess.run([str(binary)],capture_output=True,timeout=30)
        self.assertEqual((result.returncode,result.stdout,result.stderr),(0,b'13\n',b''))

    def test_descriptor_marker_missing_child_and_identity_refuse(self):
        source=self.source()
        for name,changed in (
            ('descriptor',source.replace('managed.listOfManaged(managedTable,p,boxType)',
                                        'managed.listOfManaged(managedTable,p,outerType)')),
            ('marker',source.replace('let records be try aggregate.aggregate(g,p,[box]);',
                                    'let records be try aggregate.aggregate(g,p,[intType]);')),
            ('identity',source.replace('managed.listOfManaged(managedTable,p,boxType)',
                                      'managed.identityOfManaged(managedTable,p,boxType)')),
            ('missing-child',source.replace('[text,carrier,box,outer,records,nested,envelopes]',
                                           '[text,carrier,outer,records,nested,envelopes]')
                .replace('[managed.text(managedTable),managedList,boxType,outerType,recordsType,nestedType,envelopesType]',
                         '[managed.text(managedTable),managedList,outerType,recordsType,nestedType,envelopesType]')
                .replace('[4,7,15,16,7,7,7]','[4,7,16,7,7,7]'))):
            with self.subTest(case=name):
                self.assertNotEqual(changed,source)
                result=self.generator('aggregate-list-bad-'+name,changed)
                self.assertNotEqual(result.returncode,0,result.stdout[-1800:])
                self.assertNotIn('.section',result.stdout)

    def test_version_effects_and_symbol_signature_mismatch_refuse(self):
        source=self.source()
        for name,changed in (
            ('version',source.replace('imports.boxedListName(records.index,3),2,63,1',
                                     'imports.boxedListName(records.index,3),2,63,2')),
            ('effects',source.replace('imports.boxedListName(records.index,3),2,63,1',
                                     'imports.boxedListName(records.index,3),2,8,1')),
            ('signature',source.replace('imports.boxedListName(records.index,3),2,63,1',
                                       'imports.boxedListName(carrier.index,3),2,63,1'))):
            with self.subTest(case=name):
                self.assertNotEqual(changed,source)
                result=self.generator('aggregate-list-contract-'+name,changed)
                self.assertNotEqual(result.returncode,0,result.stdout[-1800:])
                self.assertIn('native:',result.stdout)
                self.assertNotIn('.section',result.stdout)

    def test_get_replace_and_nested_get_bounds_are_terminal_and_source_located(self):
        source=self.source()
        for name,changed in (
            ('get',source.replace('r6,[originalRecords,zero]', 'r6,[originalRecords,newLength]')),
            ('replace',source.replace('r4,[twoRecords,zero,updatedText]', 'r4,[twoRecords,limit,updatedText]')),
            ('nested-get',source.replace('n6,[nestedOriginal,zero]', 'n6,[nestedOriginal,limit]'))):
            with self.subTest(case=name):
                self.assertNotEqual(changed,source)
                result=self.generator('aggregate-list-bounds-'+name,changed)
                self.assertEqual((result.returncode,result.stderr),(0,''),result.stdout[-1800:])
                starter='\n.text\n.globl _start\n_start:\n xorl %edi,%edi\n xorl %esi,%esi\n call erist_u2_rooted_function_96\n jmp .Lgraph_test_fail\n'
                run=self.run_probe('aggregate-list-terminal-'+name,result.stdout+starter+graph.FINISH+values.descriptors(),types=False)
                self.assertEqual(run.returncode,1)
                self.assertIn(b'list-probe',run.stderr)

    def run_checked_values(self,name,source,cases):
        import test_u2_function_checked_native as checked
        import test_u2_text_unicode17 as unicode
        result=self.generator(name,source)
        self.assertEqual((result.returncode,result.stderr),(0,''),result.stdout[-2500:])
        table=unicode.unicode_descriptors()
        marker='.section .rodata\n'
        table=table.replace(marker,
            '.long 6,0\n.quad .Lchecked_value_name,2,.Lchecked_value_fields\n.globl ev_types_end\nev_types_end:\n'+marker,1)
        table+='.Lchecked_value_name:\n.asciz "ParentValue"\n.p2align 2\n.Lchecked_value_fields:\n.long 4,1\n'
        asm=result.stdout.replace('    call erist_rt_slots_collect',
            '    movq $0,.Lrecursive_roots+16(%rip)\n    call erist_rt_slots_collect')
        runtime=self.runtime.replace('erist_rt_slots_collect:\n',
            'erist_rt_slots_collect:\n    incq .Lrecursive_gc_calls(%rip)\n',1)
        outcomes=[]
        for depth,failed,handled in cases:
            with self.subTest(depth=depth,failed=failed,handled=handled):
                caller=checked.U2FunctionCheckedNativeTests.checked_caller(self,depth,failed,handled)
                expected='primary-β\n'.encode()
                if not failed or handled:
                    expected=f'{depth+5 if failed else depth+6}\ntrue\n'.encode()
                    marker=f'    cmpq ${2*depth+2},.Lrecursive_gc_calls'
                    output=('    movq %rdx,%rdi\n    call evn_int\n    movq %rax,%rdi\n    call evn_output\n'
                        '    movq .Lrecursive_roots(%rip),%rax\n    cmpq .Lrecursive_inputs(%rip),%rax\n'
                        '    sete %dil\n    movzbq %dil,%rdi\n    call evn_bool\n    movq %rax,%rdi\n    call evn_output\n')
                    self.assertIn(marker,caller)
                    caller=caller.replace(marker,output+marker,1)
                run=self.run_probe(f'{name}-{depth}-{int(failed)}-{int(handled)}',
                    asm+caller+graph.FINISH+table,runtime=runtime,types=False)
                self.assertEqual((run.returncode,run.stdout,run.stderr),(0,expected,b''))
                outcomes.append(run.stdout)
        return b''.join(outcomes)

    def test_parent_private_aggregate_survives_checked_recursion_and_failure(self):
        source=(ROOT/'tests/fixtures/u2_function_checked_value_aggregate.eri').read_text()
        observed=self.run_checked_values('checked-value-aggregate',source,
            [(depth,failed,False) for depth in (0,1,5,32,64) for failed in (False,True)])
        self.check_checked_reference(observed)

    def test_parent_private_list_of_aggregates_survives_checked_recursion(self):
        source=(ROOT/'tests/fixtures/u2_function_checked_aggregate_list.eri').read_text()
        observed=self.run_checked_values('checked-aggregate-list',source,
            [(depth,failed,False) for depth in (0,1,5,32,64) for failed in (False,True)])
        self.check_checked_reference(observed)

    def check_checked_reference(self,observed):
        # Extend the existing checked-recursion oracle with parent-private
        # List/record state and source-level checked propagation.
        entry=ROOT/'tests/fixtures/u2_function_checked_aggregate_reference.eri'
        module=compile_entry(entry,entry.parent); output=[]
        Interpreter(output=output.append,module_id=module.module_id,
                    imported_modules=module.imports).run(module.program)
        expected=('\n'.join(output)+'\n').encode()
        self.assertEqual(observed,expected)
        binary=self.directory/'checked-value-reference'
        self.assertEqual(build_native(entry,binary,entry.parent),0)
        run=subprocess.run([str(binary)],capture_output=True,timeout=30)
        self.assertEqual((run.returncode,run.stdout,run.stderr),(0,expected,b''))

    def test_checked_list_failure_handler_recovers_through_parent_frames(self):
        source=(ROOT/'tests/fixtures/u2_function_checked_aggregate_list.eri').read_text()
        source=source.replace('let propagated be try body.returnFailure(fn,graph,table,failed,failedResult,loc);',
            'try ab.returnValues(fn,graph,failed,[managedInput,failedCount],loc);')
        self.run_checked_values('checked-aggregate-list-recovery',source,[(1,True,True),(32,True,True)])

    # These existing ABI test builders keep the canonical caller and saved
    # FailureContext setup unchanged; no duplicate adapter or failure producer.
    recursive_caller=managed.U2FunctionManagedNativeTests.recursive_caller

    def test_boxed_text_relationship_uses_existing_value_semantics(self):
        source=(ROOT/'tests/fixtures/u2_function_list_text.eri').read_text()
        for op in range(1,8):
            source=source.replace(f'imports.textListName({op})',
                                  f'imports.boxedListName(carrier.index,{op})')
        result=self.generator('boxed-text-list',source)
        self.assertEqual((result.returncode,result.stderr),(0,''),result.stdout[-2000:])
        imports.U2FunctionImportIntegrationTests.run_native(self,result.stdout,'boxed-text-list-native',4,'96')

    def test_unboxed_integer_list_cannot_claim_boxed_relationship(self):
        source=(ROOT/'tests/fixtures/u2_function_nested_i64_list.eri').read_text()
        for op in range(1,8):
            source=source.replace(f'lists.name({op})',f'imports.boxedListName(carrier.index,{op})')
        result=self.generator('bad-boxed-i64-list',source)
        self.assertNotEqual(result.returncode,0,result.stdout[-1800:])
        self.assertIn('native:',result.stdout)
        self.assertNotIn('.section',result.stdout)

    def test_checked_value_entry_requires_exact_layout_vector(self):
        source=(ROOT/'tests/fixtures/u2_function_checked_value_aggregate.eri').read_text()
        changed=source.replace('[9,4,18],true,92','[9,4],true,92')
        self.assertNotEqual(changed,source)
        result=self.generator('bad-checked-value-layout',changed)
        self.assertNotEqual(result.returncode,0,result.stdout[-1800:])
        self.assertIn('unsupported:',result.stdout)
        self.assertNotIn('.section',result.stdout)
