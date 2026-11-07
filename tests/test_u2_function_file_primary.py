"""Actual whole-Function close composition with explicitly bound primary."""
from pathlib import Path
import unittest
import platform
import test_freestanding_resource_values as resource
import test_u2_function_file_checked as fileTests

ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(platform.system() == "Linux" and platform.machine().lower() in ("x86_64","amd64"),
                     "owned primary File CFG requires Linux x86-64")
class U2FunctionFilePrimaryTests(unittest.TestCase):
    setUpClass=fileTests.U2FunctionFileCheckedTests.__dict__['setUpClass']
    generator=fileTests.U2FunctionFileCheckedTests.generator
    run_probe=fileTests.U2FunctionFileCheckedTests.run_probe
    caller=fileTests.U2FunctionFileCheckedTests.caller
    nested_caller=fileTests.U2FunctionFileCheckedTests.nested_caller
    def test_generated_primary_preservation_and_secondary_append(self):
        source=(ROOT/'tests/fixtures/u2_function_file_primary.eri').read_text()
        generated=self.generator('primary-function',source)
        self.assertEqual((generated.returncode,generated.stderr),(0,''),generated.stdout[-2000:])
        self.assertIn('call erist_rt_failure_append',generated.stdout)
        path=self.directory/'primary-owned.txt';path.write_text('native')
        for failed, prior in ((False,False),(True,False),(False,True),(True,True)):
            caller=self.caller(path,True).replace('movl $2,%ecx','movl $3,%ecx').replace('.Lroots: .zero 16','.Lroots: .zero 24').replace('.Lclasses: .byte 1,5','.Lclasses: .byte 1,5,5').replace('.Lroots+8','.Lroots+16')
            setup='''    movq %rax,%rdi
    leaq .Lprimary_message(%rip),%rsi
    call erist_rt_file_failure
    movq %rax,.Lroots+8(%rip)
'''
            if prior:
                setup += '''    movq .Lroots(%rip),%rdi
    leaq .Lprior_message(%rip),%rsi
    call erist_rt_file_failure
    movq %rax,%rsi
    movq .Lroots+8(%rip),%rdi
    call erist_rt_failure_append
'''
            caller=caller.replace('    leaq .Lroots(%rip),%rdi\n    xorl %esi,%esi',setup+'    leaq .Lroots(%rip),%rdi\n    xorl %esi,%esi',1)
            check='''    cmpq %rax,.Lroots+8(%rip)
    jne .Lresource_test_fail
'''
            if prior:
                check+='''    movq 80(%rax),%rax
    testq %rax,%rax
    je .Lresource_test_fail
    cmpq $13,40(%rax)
    jne .Lresource_test_fail
'''
            if failed:
                check+='''    movq NEXT(%rax),%rax
    testq %rax,%rax
    je .Lresource_test_fail
    cmpq $8,(%rax)
    jne .Lresource_test_fail
    cmpq $0,88(%rax)
    jne .Lresource_test_fail
'''.replace('NEXT','88' if prior else '80')
            else:
                check+='''    cmpq $0,NEXT(%rax)
    jne .Lresource_test_fail
'''.replace('NEXT','88' if prior else '80')
            caller=caller.replace('    cmpq $0,80(%rax)\n    jne .Lresource_test_fail',check)
            caller=caller.replace('    movq $0,.Lroots(%rip)','    movq $0,.Lroots+8(%rip)\n    movq $0,.Lroots(%rip)')
            caller+='\n.section .rodata\n.Lprimary_message: .asciz "original primary"\n.Lprior_message: .asciz "prior cleanup"\n'
            runtime=resource.close_failures(self.runtime) if failed else self.runtime
            run=self.run_probe('primary-'+str(failed)+'-'+str(prior),generated.stdout+caller,runtime=runtime)
            self.assertEqual((run.returncode,run.stdout,run.stderr),(0,b'',b''))

    def test_nested_close_failure_becomes_primary_through_outer_cleanup(self):
        source=(ROOT/'tests/fixtures/u2_function_file_nested_primary.eri').read_text()
        generated=self.generator('nested-primary',source)
        self.assertEqual((generated.returncode,generated.stderr),(0,''),generated.stdout[-2500:])
        asm=generated.stdout
        self.assertIn('call erist_rt_failure_append',asm)
        self.assertIn('erist_u2_file_723_publish_3:',asm)
        present=self.directory/'nested-primary-present.txt'
        present.write_text('native')
        missing=self.directory/'nested-primary-absent.txt'
        scenarios=(
            ('clean',present,present,42,False,2,False),
            ('inner-open-recovery',present,missing,7,False,1,False),
            ('outer-open-failure',missing,present,None,True,0,False),
            ('inner-and-outer-close-failure',present,present,None,True,2,True),
        )
        for name,outer,inner,answer,failing,closes,inject in scenarios:
            with self.subTest(scenario=name):
                runtime=resource.close_failures(self.runtime) if inject else self.runtime
                runtime=runtime.replace('.Lr_close:\n',
                    '.Lr_close:\n    incq .Lnested_close_calls(%rip)\n',1)
                caller=self.nested_caller(outer,inner,answer,failing,closes)
                caller=caller.replace('erist_u2_rooted_function_719',
                    'erist_u2_rooted_function_723')
                if inject:
                    # New failed outer close must append after the original
                    # inner-close primary, not replace it with a later error.
                    needle='    cmpq $8,(%rax)\n    jne .Lresource_test_fail\n'
                    self.assertEqual(caller.count(needle),1)
                    caller=caller.replace(needle,needle+
                        '    movq 80(%rax),%rax\n'
                        '    testq %rax,%rax\n'
                        '    je .Lresource_test_fail\n'
                        '    cmpq $8,(%rax)\n'
                        '    jne .Lresource_test_fail\n'
                        '    cmpq $0,88(%rax)\n'
                        '    jne .Lresource_test_fail\n',1)
                result=self.run_probe('nested-primary-'+name,asm+caller,runtime=runtime)
                self.assertEqual((result.returncode,result.stdout,result.stderr),
                                 (0,b'',b''),name)

    def test_nested_primary_binding_corruption_refuses_before_output(self):
        source=(ROOT/'tests/fixtures/u2_function_file_nested_primary.eri').read_text()
        marker='    let binding be native.PrimaryBinding'
        self.assertEqual(source.count(marker),1)
        for name,mutation in (
            ('wrong-failed-cleanup-plan','cleanupPlan.entry=1;'),
            ('stale-continuation','pair.revision=pair.revision+1;'),
        ):
            with self.subTest(corruption=name):
                generated=self.generator('nested-primary-refuse-'+name,
                    source.replace(marker,mutation+'\n'+marker,1))
                self.assertEqual(generated.returncode,1,generated.stdout[-2500:])
                self.assertIn('unsupported:',generated.stdout)
                self.assertNotIn('.globl',generated.stdout)
                self.assertNotIn('leaked',generated.stdout)

    def test_bad_primary_binding_refuses_before_output(self):
        source=(ROOT/'tests/fixtures/u2_function_file_primary.eri').read_text()
        for name, mutation in (
            ('normal-mode','cleanupPlan.entry=1;'),
            ('stale','pair.revision=pair.revision+1;')):
            result=self.generator('bad-primary-'+name,source.replace(
                '    let binding be native.PrimaryBinding',mutation+'\n    let binding be native.PrimaryBinding'))
            self.assertEqual(result.returncode,1,result.stdout[-2000:])
            self.assertIn('unsupported:',result.stdout)
            self.assertNotIn('.globl',result.stdout)
