"""Actual compiler-generated typed error payload and saved-context construction."""
from pathlib import Path
import platform
import subprocess
from compiler.erist.cli import compile_entry,build_native
from compiler.erist.runtime_ext import Interpreter
import unittest
import test_u2_function_import_integration as imports
import test_freestanding_graph_values as graph
ROOT=Path(__file__).resolve().parents[1]

def descriptors():
    table=graph.descriptors();marker='.section .rodata\n'
    return table.replace(marker,
        '.long 6,0\n.quad .Lproducer_name,2,.Lproducer_fields\n.globl ev_types_end\nev_types_end:\n'+marker,1)+'.Lproducer_name:\n.asciz "Problem"\n.p2align 2\n.Lproducer_fields:\n.long 1,4\n'

@unittest.skipUnless(platform.system()=='Linux' and platform.machine().lower() in ('x86_64','amd64'), 'typed failure producer requires Linux x86-64')
class U2FunctionFailureProducerTests(unittest.TestCase):
    setUpClass=imports.U2FunctionImportIntegrationTests.__dict__['setUpClass']
    generator=imports.U2FunctionImportIntegrationTests.generator
    run_probe=imports.U2FunctionImportIntegrationTests.run_probe
    def source(self): return (ROOT/'tests/fixtures/u2_function_typed_failure_producer.eri').read_text()
    def caller(self,depth,fail_base):
        failure=bool(depth or fail_base)
        checks=('    cmpq $1,%r10\n    jne .Lgraph_test_fail\n'
                '    cmpq %rax,.Lproducer_roots(%rip)\n    jne .Lgraph_test_fail\n'
                '    call erist_rt_text_collect\n    call erist_rt_live_failures\n'
                '    cmpq $1,%rax\n    jne .Lgraph_test_fail\n'
                '    movq .Lproducer_roots(%rip),%rdi\n    movl $15,%esi\n    call evn_match\n'
                '    cmpq $1,%rax\n    jne .Lgraph_test_fail\n'
                '    movq .Lproducer_roots(%rip),%rdi\n    movl $15,%esi\n    call evn_error\n'
                '    movq %rax,.Lproducer_roots+8(%rip)\n    movq %rax,%rdi\n    xorl %esi,%esi\n'
                '    call evn_member\n    movq %rax,%rdi\n    call evn_output\n'
                '    movq .Lproducer_roots+8(%rip),%rdi\n    movl $1,%esi\n    call evn_member\n'
                '    movq %rax,%rdi\n    call evn_output\n') if failure else (
                '    testq %r10,%r10\n    jne .Lgraph_test_fail\n'
                '    cmpq $7,%rax\n    jne .Lgraph_test_fail\n'
                '    cmpq $0,.Lproducer_roots(%rip)\n    jne .Lgraph_test_fail\n'
                '    movq %rax,%rdi\n    call evn_int\n    movq %rax,%rdi\n    call evn_output\n')
        return ('.bss\n.p2align 3\n.Lproducer_roots:\n.zero 16\n.section .rodata\n.Lproducer_classes:\n.byte 5,1\n'
            '.section .data\n.Lproducer_inputs:\n.quad '+str(depth)+','+str(int(fail_base))+'\n'
            '.text\n.globl _start\n_start:\n    call evn_scope_enter\n    movq %rax,%r12\n    movq %rax,%rdi\n'
            '    leaq .Lproducer_roots(%rip),%rsi\n    leaq .Lproducer_classes(%rip),%rdx\n'
            '    movl $2,%ecx\n    call evn_bind_roots\n    leaq .Lproducer_inputs(%rip),%rdi\n'
            '    xorl %esi,%esi\n    xorl %edx,%edx\n    leaq .Lproducer_roots(%rip),%rcx\n'
            '    call erist_u2_rooted_function_97\n'+checks+
            '    movq $0,.Lproducer_roots(%rip)\n    movq $0,.Lproducer_roots+8(%rip)\n'
            '    call evn_void\n    movq %rax,%rsi\n    movq %r12,%rdi\n    call evn_scope_leave\n'
            '    jmp .Lgraph_finish\n')
    def test_constructs_typed_primary_without_failure_ingress(self):
        result=self.generator('typed-failure-producer',self.source())
        self.assertEqual((result.returncode,result.stderr),(0,''),result.stdout[-2500:])
        outcomes=[]
        for depth in (0,1,5,16,64):
            for fail_base in (False,True):
                with self.subTest(depth=depth,fail_base=fail_base):
                    caller=self.caller(depth,fail_base)
                    self.assertNotIn('call evn_fail',caller)
                    run=self.run_probe(f'failure-produced-{depth}-{int(fail_base)}',
                        result.stdout+caller+graph.FINISH+descriptors(),types=False)
                    expected=(('42' if fail_base else '43')+'\nβ\n').encode() if depth or fail_base else b'7\n'
                    self.assertEqual((run.returncode,run.stdout,run.stderr),(0,expected,b''))
                    outcomes.append(run.stdout)
        entry=ROOT/'tests/fixtures/u2_function_failure_producer_reference.eri'
        module=compile_entry(entry,entry.parent); output=[]
        Interpreter(output=output.append,module_id=module.module_id,
                    imported_modules=module.imports).run(module.program)
        expected=('\n'.join(output)+'\n').encode()
        self.assertEqual(b''.join(outcomes),expected)
        binary=self.directory/'failure-producer-reference'
        self.assertEqual(build_native(entry,binary,entry.parent),0)
        run=subprocess.run([str(binary)],capture_output=True,timeout=30)
        self.assertEqual((run.returncode,run.stdout,run.stderr),(0,expected,b''))

    def test_message_field_zero_and_later_field_keep_exact_typed_payload(self):
        source=self.source()
        zero=source.replace('aggregate.aggregate(graph,p,[i64,text])',
                            'aggregate.aggregate(graph,p,[text,i64])')
        zero=zero.replace('imports.failureName(payload.index,1)', 'imports.failureName(payload.index,0)')
        zero=zero.replace('payload,[code,message]', 'payload,[message,code]')
        zero=zero.replace('entry,original,0,otherCode','entry,original,1,otherCode')
        zero=zero.replace('entry,changedCode,1,otherMessage','entry,changedCode,0,otherMessage')
        later=source.replace('aggregate.aggregate(graph,p,[i64,text])',
                             'aggregate.aggregate(graph,p,[i64,i64,i64,i64,text])')
        later=later.replace('imports.failureName(payload.index,1)', 'imports.failureName(payload.index,4)')
        later=later.replace('payload,[code,message]', 'payload,[code,code,code,code,message]')
        later=later.replace('entry,changedCode,1,otherMessage','entry,changedCode,4,otherMessage')
        for name,changed,field_types,message_field in (
            ('zero',zero,'4,1',0),('later',later,'1,1,1,1,4',4)):
            with self.subTest(case=name):
                result=self.generator('failure-message-'+name,changed)
                self.assertEqual((result.returncode,result.stderr),(0,''),result.stdout[-2400:])
                table=descriptors().replace('.Lproducer_name,2,',
                    '.Lproducer_name,'+str(len(field_types.split(',')))+',').replace('.long 1,4\n','.long '+field_types+'\n')
                caller=self.caller(5,True)
                if message_field == 0:
                    caller=caller.replace('movq %rax,%rdi\n    xorl %esi,%esi\n    call evn_member',
                                          'movq %rax,%rdi\n    movl $1,%esi\n    call evn_member')
                caller=caller.replace('.Lproducer_roots+8(%rip),%rdi\n    movl $1,%esi\n    call evn_member',
                    '.Lproducer_roots+8(%rip),%rdi\n    movl $'+str(message_field)+',%esi\n    call evn_member')
                run=self.run_probe('failure-message-native-'+name,result.stdout+caller+graph.FINISH+table,types=False)
                self.assertEqual((run.returncode,run.stdout,run.stderr),(0,'42\nβ\n'.encode(),b''))

    def test_message_carrier_effects_version_and_kind_refuse_before_output(self):
        source=self.source()
        for name,changed in (
            ('non-text',source.replace('imports.failureName(payload.index,1)', 'imports.failureName(payload.index,0)')),
            ('out-of-range',source.replace('imports.failureName(payload.index,1)', 'imports.failureName(payload.index,32)')),
            ('carrier',source.replace('imports.failureName(payload.index,1)', 'imports.failureName(text.index,1)')),
            ('effects',source.replace('imports.failureName(payload.index,1),2,63,1', 'imports.failureName(payload.index,1),2,8,1')),
            ('version',source.replace('imports.failureName(payload.index,1),2,63,1', 'imports.failureName(payload.index,1),2,63,2')),
            ('kind',source.replace('imports.failureName(payload.index,1),2,63,1', 'imports.failureName(payload.index,1),1,63,0'))):
            with self.subTest(case=name):
                self.assertNotEqual(changed,source)
                result=self.generator('bad-failure-'+name,changed)
                self.assertNotEqual(result.returncode,0,result.stdout[-1800:])
                self.assertNotIn('.section',result.stdout)

    def test_wrong_descriptor_signature_layout_and_source_origin_refuse(self):
        source=self.source()
        bad_origin=source.replace('import std.process;','import std.process;\nimport compiler.u1_words as words;')
        bad_origin=bad_origin.replace('try native.emitValuesChecked(',
            'let captureId be try words.get(fn.values,phase,(primary.index-1)*4+2);\n'
            '    fn.instructions.frozen=false; try words.set(fn.instructions,phase,(captureId-1)*10+6,0); fn.instructions.frozen=true;\n'
            '    try native.emitValuesChecked(',1)
        for name,changed in (
            ('descriptor',source.replace('managed.valueOfBase(registry,p,payload)', 'managed.identityOfBase(registry,p,payload)')),
            ('signature',source.replace('p,[payload],[failure]', 'p,[text],[failure]')),
            ('layout',source.replace('[4,15],true,97','[4],true,97')),
            ('origin',bad_origin)):
            with self.subTest(case=name):
                self.assertNotEqual(changed,source)
                result=self.generator('bad-failure-'+name,changed)
                self.assertNotEqual(result.returncode,0,result.stdout[-1800:])
                self.assertNotIn('.section',result.stdout)

    def test_context_allocation_refusal_remains_terminal(self):
        result=self.generator('failure-context-refusal',self.source())
        self.assertEqual((result.returncode,result.stderr),(0,''),result.stdout[-2200:])
        self.assertEqual(self.runtime.count('evn_saved:\n'),1)
        self.assertEqual(self.runtime.count('erist_rt_alloc:\n'),1)
        runtime=self.runtime.replace('evn_saved:\n',
            'evn_saved:\n    movq $1,.Lproducer_refuse_context(%rip)\n',1)
        runtime=runtime.replace('erist_rt_alloc:\n',
            'erist_rt_alloc:\n    cmpq $0,.Lproducer_refuse_context(%rip)\n'
            '    je .Lproducer_alloc_allowed\n    xorl %eax,%eax\n    ret\n.Lproducer_alloc_allowed:\n',1)
        state='\n.bss\n.Lproducer_refuse_context:\n.quad 0\n'
        run=self.run_probe('failure-context-allocation-terminal',result.stdout+self.caller(0,True)+
            state+graph.FINISH+descriptors(),runtime=runtime,types=False)
        self.assertEqual((run.returncode,run.stdout),(1,b''))
        self.assertIn(b'out of memory',run.stderr)

    def test_unchecked_entry_cannot_produce_unbound_class_five_values(self):
        source=self.source().replace('native.emitValuesChecked(', 'native.emitValues(')
        result=self.generator('failure-unchecked-entry',source)
        self.assertNotEqual(result.returncode,0,result.stdout[-1800:])
        self.assertNotIn('.section',result.stdout)

    def test_saved_typed_payload_keeps_nested_list_and_text_alive(self):
        source=self.source()
        source=source.replace('let payload be try aggregate.aggregate(graph,p,[i64,text]);',
            'let listCarrier be try aggregate.aggregate(graph,p,[text]);\n'
            '    let payload be try aggregate.aggregate(graph,p,[i64,text,listCarrier]);')
        source=source.replace('    let captureSig be try sig.signature(',
            '    let listEmptySig be try sig.signature(data,graph,p,[],[listCarrier]);\n'
            '    let listEmpty be try meta.declaration(data,p,listEmptySig,imports.textListName(1),2,63,1);\n'
            '    let listAddSig be try sig.signature(data,graph,p,[listCarrier,text],[listCarrier]);\n'
            '    let listAdd be try meta.declaration(data,p,listAddSig,imports.textListName(3),2,63,1);\n'
            '    let captureSig be try sig.signature(',1)
        source=source.replace('try managed.freeze(registry);',
            'let listType be try managed.listOfManaged(registry,p,managed.text(registry));\n'
            '    try managed.freeze(registry);',1)
        source=source.replace('let original be try ab.make(fn,graph,entry,payload,[code,message],loc);',
            'call=try ab.call(fn,graph,entry,listEmpty,[],loc); let emptyList be try build.result(fn,call,0);\n'
            '    call=try ab.call(fn,graph,entry,listAdd,[emptyList,message],loc); let retainedList be try build.result(fn,call,0);\n'
            '    let original be try ab.make(fn,graph,entry,payload,[code,message,retainedList],loc);')
        source=source.replace('[text,payload],[managed.text(registry),payloadType],[4,15]',
                              '[text,payload,listCarrier],[managed.text(registry),payloadType,listType],[4,15,7]')
        result=self.generator('failure-nested-list',source)
        self.assertEqual((result.returncode,result.stderr),(0,''),result.stdout[-2200:])
        table=descriptors().replace('.Lproducer_name,2,','.Lproducer_name,3,').replace('.long 1,4\n','.long 1,4,7\n')
        for depth,failed in ((1,False),(5,True)):
            caller=self.caller(depth,failed)
            marker='    movq $0,.Lproducer_roots(%rip)'
            inspect=('    movq .Lproducer_roots+8(%rip),%rdi\n    movl $2,%esi\n    call evn_member\n'
                '    movq %rax,%rdi\n    call evn_count\n    movq %rax,%rdi\n    call evn_output\n'
                '    movq .Lproducer_roots+8(%rip),%rdi\n    movl $2,%esi\n    call evn_member\n'
                '    movq %rax,%rdi\n    xorl %esi,%esi\n    call evn_index\n    movq %rax,%rdi\n    call evn_output\n')
            self.assertIn(marker,caller)
            caller=caller.replace(marker,inspect+marker,1)
            run=self.run_probe(f'failure-nested-list-{depth}',result.stdout+caller+graph.FINISH+table,types=False)
            expected=(('42' if failed else '43')+'\nβ\n1\nβ\n').encode()
            self.assertEqual((run.returncode,run.stdout,run.stderr),(0,expected,b''))
