"""File ownership and aggregate bindings share original independent proofs."""
from pathlib import Path
import unittest
import platform
import test_u2_function_file_checked as files
import test_freestanding_resource_values as resource
ROOT=Path(__file__).resolve().parents[1]
def descriptors():
    table=resource.descriptors();marker='.globl ev_types_end\nev_types_end:\n'
    return table.replace(marker,'.long 6,0\n.quad .Lrecord_name,2,.Lrecord_fields\n'+marker)+'.section .rodata\n.Lrecord_name:\n.asciz "Record"\n.p2align 2\n.Lrecord_fields:\n.long 1,4\n'
@unittest.skipUnless(platform.system()=='Linux' and platform.machine().lower() in ('x86_64','amd64'),'File values require Linux x86-64')
class U2FunctionFileValueTests(unittest.TestCase):
    setUpClass=files.U2FunctionFileCheckedTests.__dict__['setUpClass']
    generator=files.U2FunctionFileCheckedTests.generator
    run_probe=files.U2FunctionFileCheckedTests.run_probe
    caller=files.U2FunctionFileCheckedTests.caller
    def source(self): return (ROOT/'tests/fixtures/u2_function_file_value.eri').read_text()
    def test_file_aggregate_single_and_group_returns_failures_and_reclamation(self):
        source=self.source()
        grouped=source.replace('native.emitFileValuesChecked(fn,graph,table,phase,registry,[text,record],\n        [managed.text(registry),recordType],true,718,profile,9,[4,10])',
            'native.emitFileValuesCheckedGroup([fn],[718],[profile],graph,table,registry,[text,record],\n        [managed.text(registry),recordType],true,9,[4,10])')
        self.assertNotEqual(grouped,source)
        path=self.directory/'value-file.txt';path.write_text('native')
        for name,code in (('single',source),('group',grouped)):
            generated=self.generator('file-values-'+name,code)
            self.assertEqual((generated.returncode,generated.stderr),(0,''),generated.stdout[-2200:])
            for case,selected,runtime,failed in (
                ('normal',path,self.runtime,False),('acquire',self.directory/'missing.txt',self.runtime,True),
                ('close',path,resource.close_failures(self.runtime),True)):
                with self.subTest(entry=name,case=case):
                    runtime=runtime.replace('.Lr_close:\n','.Lr_close:\n    incq .Lclose_calls(%rip)\n',1)
                    caller=self.caller(selected,failed).replace('    call .Lresource_finish',
                        '    cmpq $'+str(int(case!='acquire'))+',.Lclose_calls(%rip)\n    jne .Lresource_test_fail\n    call .Lresource_finish',1)
                    run=self.run_probe('file-value-'+name+'-'+case,generated.stdout+caller+
                        '\n.bss\n.Lclose_calls: .quad 0\n'+descriptors(),runtime=runtime,types=False)
                    self.assertEqual((run.returncode,run.stdout,run.stderr),(0,b'',b''))
    def test_invalid_layout_refuses_without_plan_leak(self):
        result=self.generator('file-values-invalid',self.source().replace('9,[4,10])','9,[4])'))
        self.assertNotEqual(result.returncode,0,result.stdout[-2000:])
        self.assertNotIn('leaked',result.stdout)
        self.assertNotIn('.section',result.stdout)

    def test_fresh_typed_context_after_file_consumption(self):
        source=self.source().replace('import std.process;',
            'import std.process;\nimport compiler.u2_function_native_imports as imports;')
        source=source.replace('    try aggregate.freeze(graph);',
            '    let captureSig be try sig.signature(data,graph,mp,[record],[failure]);\n'
            '    let capture be try meta.declaration(data,mp,captureSig,imports.failureName(record.index,1),2,63,1);\n'
            '    try aggregate.freeze(graph);',1)
        source=source.replace('try ab.returnValues(fn,graph,done,[restored],loc);',
            'let captured be try ab.call(fn,graph,done,capture,[snapshot],loc);\n'
            '    let context be try build.result(fn,captured,0);\n'
            '    let raised be try body.returnFailure(fn,graph,table,done,context,loc);')
        generated=self.generator('file-values-produced-context',source)
        self.assertEqual((generated.returncode,generated.stderr),(0,''),generated.stdout[-2200:])
        path=self.directory/'captured-after-close.txt';path.write_text('native')
        caller=self.caller(path,True).replace('cmpq $8,(%rax)','cmpq $10,(%rax)')
        runtime=self.runtime.replace('.Lr_close:\n','.Lr_close:\n    incq .Lclose_calls(%rip)\n',1)
        caller=caller.replace('    call .Lresource_finish',
            '    cmpq $1,.Lclose_calls(%rip)\n    jne .Lresource_test_fail\n    call .Lresource_finish',1)
        run=self.run_probe('file-values-context-after-close',generated.stdout+caller+
            '\n.bss\n.Lclose_calls: .quad 0\n'+descriptors(),runtime=runtime,types=False)
        self.assertEqual((run.returncode,run.stdout,run.stderr),(0,b'',b''))

    def primary_source(self,chain=False):
        fixture='u2_function_file_primary_chain.eri' if chain else 'u2_function_file_primary.eri'
        source=(ROOT/'tests/fixtures'/fixture).read_text()
        source=source.replace('    let file be',
            '    let record be try aggregate.aggregate(graph,mp,[i64,text]);\n    let file be',1)
        source=source.replace('    try managed.freeze(registry);',
            '    let recordType be try managed.valueOfBase(registry,mp,record);\n    try managed.freeze(registry);',1)
        marker='    let secondPair be' if chain else '    try ab.jump(fn,graph,bridge,owned,'
        source=source.replace(marker,
            '    let snapshot be try ab.make(fn,graph,bridge,record,[bridgePending,path],loc);\n'+marker,1)
        # A damaged retained integer takes an ordinary return; the external
        # caller requires the original primary, so this cannot silently pass.
        for block,param,name in [('done',0,'returned'),('closeFailed',1,'cancelled')]:
            original=f'    let {name} be try body.returnFailure(fn,graph,table,{block},try build.parameter(fn,{block},{param}),loc);'
            replacement=f'''    let {name}Good be try ab.block(fn,graph,[failure]);
    let {name}Bad be try ab.block(fn,graph,[]);
    try owners.block(profile,fn,cp,{name}Good,[]);
    try owners.block(profile,fn,cp,{name}Bad,[]);
    let {name}Value be try ab.get(fn,graph,{block},snapshot,0,loc);
    let {name}Expected be try build.integer(fn,{block},42,loc);
    let {name}Equal be try build.compareInteger(fn,{block},{name}Value,{name}Expected,1,loc);
    try ab.branch(fn,graph,{block},{name}Equal,{name}Good,[try build.parameter(fn,{block},{param})],{name}Bad,[],loc);
    try ab.returnValues(fn,graph,{name}Bad,[{name}Value],loc);
    let {name} be try body.returnFailure(fn,graph,table,{name}Good,try build.parameter(fn,{name}Good,0),loc);'''
            self.assertIn(original,source)
            source=source.replace(original,replacement)
        source=source.replace('native.emitFileCheckedPrimary','native.emitFileValuesCheckedPrimary')
        source=source.replace('phase,registry,[text],\n        [managed.text(registry)],true,718',
            'phase,registry,[text,record],\n        [managed.text(registry),recordType],true,718')
        return source.replace('9,[innerBinding,binding])','9,[innerBinding,binding],[4,10])').replace('9,binding)','9,binding,[4,10])')

    def test_primary_values_and_nested_chain_preserve_context_and_aggregate(self):
        import test_u2_function_file_primary as primary
        # Reuse original primary identity/ordered secondary/GC/reclamation
        # assertions, extending only the runtime's concrete descriptor table.
        original=self.run_probe
        def probe(name,assembly,runtime=None,types=True):
            runtime=runtime.replace('.Lr_close:\n',
                '.Lr_close:\n    incq .Lvalue_closes(%rip)\n',1)
            assembly=assembly.replace('    call .Lresource_finish',
                '    cmpq $'+str(2 if chain else 1)+',.Lvalue_closes(%rip)\n'
                '    jne .Lresource_test_fail\n    call .Lresource_finish',1)
            return original(name,assembly+descriptors()+'\n.bss\n.Lvalue_closes: .quad 0\n',
                runtime=runtime,types=False)
        self.run_probe=probe
        try:
            for chain in (False,True):
                with self.subTest(chain=chain):
                    primary.U2FunctionFilePrimaryTests.exercise_primary(self,self.primary_source(chain),2 if chain else 1)
        finally:
            self.run_probe=original

    def test_primary_values_refuse_bad_layout_and_cleanup_binding_without_leaks(self):
        source=self.primary_source(True)
        for name,bad in (
            ('layout',source.replace('[4,10])','[4])')),
            ('duplicate',source.replace('[innerBinding,binding],[4,10])','[innerBinding,innerBinding,binding],[4,10])')),
            ('prefix',source.replace('innerActive,1,loc,true','innerActive,0,loc,true'))):
            with self.subTest(case=name):
                result=self.generator('file-primary-values-bad-'+name,bad)
                self.assertEqual(result.returncode,1,result.stdout[-2000:])
                self.assertIn('unsupported:',result.stdout)
                self.assertNotIn('.globl',result.stdout)
                self.assertNotIn('leaked',result.stdout)
