"""One batched qualification of owned graphs, aliases, roots and checked jumps."""
from pathlib import Path
import os
import platform
import shutil
import subprocess
import tempfile
import unittest
from compiler.erist.cli import build_native
import test_freestanding_text_lifetimes as lifetime_tests

ROOT=Path(__file__).resolve().parents[1]


def descriptors():
    rows=[(i,0,'',[]) for i in range(6)]+[
        (6,0,'Box',[4]),(7,1,'List',[]),(8,9,'MaybeNode',[]),
        (9,10,'IdentityNode',[]),(6,0,'Node',[8]),(6,0,'Problem',[1,4]),(11,0,'error',[4])]
    text='.section .data.rel.ro\n.p2align 3\n.globl ev_types\nev_types:\n'
    for i,(kind,inner,name,fields) in enumerate(rows):
        text+=f'.long {kind},{inner}\n.quad .Lkind_name{i},{len(fields)},'+(f'.Lkind_fields{i}' if fields else '0')+'\n'
    text+='.section .rodata\n'
    for i,(kind,inner,name,fields) in enumerate(rows):
        text+=f'.Lkind_name{i}:\n.asciz "{name}"\n'
        if fields: text+=f'.p2align 2\n.Lkind_fields{i}:\n.long '+','.join(map(str,fields))+'\n'
    return text


FINISH=r'''
.text
.Lgraph_finish:
    call erist_rt_failure_clear
    call erist_rt_text_collect
    call erist_rt_graph_live_objects
    testq %rax,%rax
    jne .Lgraph_test_fail
    call erist_rt_text_live_buffers
    testq %rax,%rax
    jne .Lgraph_test_fail
    call erist_rt_live_failures
    testq %rax,%rax
    jne .Lgraph_test_fail
    call erist_rt_live_handlers
    testq %rax,%rax
    jne .Lgraph_test_fail
    call erist_rt_allocator_release_all
    testq %rax,%rax
    jne .Lgraph_test_fail
    xorl %edi,%edi
    jmp erist_rt_exit
.Lgraph_test_fail:
    movl $99,%edi
    jmp erist_rt_exit
'''


@unittest.skipUnless(platform.system()=='Linux' and platform.machine().lower() in ('x86_64','amd64'),
                     'owned graph profile currently targets Linux x86-64')
class FreestandingGraphValueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for tool in ('as','ld','nm','readelf'):
            if not shutil.which(tool): raise unittest.SkipTest(f'{tool} unavailable')
        cls.temporary=tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.directory=Path(cls.temporary.name)
        generator=cls.directory/'runtime'; cls.frontend=cls.directory/'frontend'
        if build_native(ROOT/'src/graph_value_runtime.eri',generator,ROOT/'src')!=0:
            raise AssertionError('graph runtime generator did not compile')
        emitted=subprocess.run([str(generator)],capture_output=True,text=True,timeout=60)
        if (emitted.returncode,emitted.stderr)!=(0,''): raise AssertionError(emitted.stderr)
        cls.runtime=lifetime_tests.audit_slot_count(emitted.stdout)
        if build_native(ROOT/'src/frontend.eri',cls.frontend,ROOT/'src')!=0:
            raise AssertionError('frontend did not compile')

    def run_probe(self,name,assembly,runtime=None,types=True):
        return lifetime_tests.FreestandingTextLifetimeTests._link_run(
            self,self.directory,name,self.runtime if runtime is None else runtime,
            (descriptors() if types else '')+assembly)

    def compile_application(self,path):
        compiled=subprocess.run([str(self.frontend),'emit-asm',str(path)],capture_output=True,
                                text=True,timeout=30)
        self.assertEqual((compiled.returncode,compiled.stderr),(0,''))
        return compiled.stdout

    def test_geometric_list_growth_preserves_prefixes_and_reclaims_backing(self):
        source=self.directory/'list-growth.eri'
        source.write_text("""
        let values be []; let prefix be [-1]; let i be 0;
        while i<10000 {
            values.add(i);
            if i==1999 { prefix=values; }
            i=i+1;
        }
        let branch be prefix; branch.add(-9);
        values[0]=42;
        output(values.count); output(prefix.count); output(prefix[0]);
        output(branch.count); output(branch[2000]); output(values[0]);
        for item in prefix { values.add(item); }
        output(values.count); output(prefix.count);
        """)
        app=self.compile_application(source)
        runtime=self.runtime.replace('erist_rt_graph_new_capacity:\n',
            'erist_rt_graph_new_capacity:\n    addq %rdi,.Ltest_initialized_cells(%rip)\n',1)
        starter="""
.text
.globl _start
_start:
    call erist_entry
    cmpq $100000,.Ltest_initialized_cells(%rip)
    ja .Lgraph_test_fail
    cmpq $2000,.Ltext_collections(%rip)
    ja .Lgraph_test_fail
    jmp .Lgraph_finish
.bss
.Ltest_initialized_cells:
.quad 0
"""
        result=self.run_probe('geometric-list-growth',app+starter+FINISH,runtime=runtime,types=False)
        self.assertEqual((result.returncode,result.stdout,result.stderr),
                         (0,b'10000\n2000\n0\n2001\n-9\n42\n12000\n2000\n',b''))

    def test_real_aggregate_alias_cycle_and_checked_failure_application(self):
        fixture=ROOT/'examples/freestanding_graph_values.eri'
        reference=self.directory/'reference'
        app=self.compile_application(fixture)
        asm=self.directory/'reference.s'
        asm.write_text(app+'\n.section .note.GNU-stack,"",@progbits\n')
        subprocess.run([os.environ.get('CC','cc'),'-std=c11','-O2','-DERIST_NATIVE_RUNTIME',
                        str(ROOT/'runtime/native_gc_runtime.c'),str(asm),'-lm','-o',str(reference)],
                       check=True,capture_output=True,timeout=30)
        hosted=subprocess.run([str(reference)],capture_output=True,timeout=30)
        self.assertEqual((hosted.returncode,hosted.stderr),(0,b''))
        expected=('1\n9\nfalse\nrenamed\n4\n4\nB\n1\n2\n4\ntrue\n8\n3\ntrue\n'
                  'updated\ntrue\nfalse\ntrue\nupdated\n42\nouter\nretained\n7\nother\nother\nfalse\n3\nβ\n').encode()
        self.assertEqual(hosted.stdout,expected)
        bounded=self.runtime.replace('.Ltext_safe_return:\n', '''.Ltext_safe_return:
    cmpq $4096,.Lgraph_count(%rip)
    ja .Lgraph_test_fail
    cmpq $128,.Lfailure_count(%rip)
    ja .Lgraph_test_fail
    cmpq $32,.Lhandler_count(%rip)
    ja .Lgraph_test_fail
''',1)
        self.assertNotEqual(bounded,self.runtime)
        result=self.run_probe('graph-application',app+r'''
.text
.globl _start
_start:
    xorl %ebp,%ebp
    call erist_entry
    call erist_rt_slots_live
    cmpq $2,%rax
    ja .Lgraph_test_fail
    jmp .Lgraph_finish
'''+FINISH,runtime=bounded,types=False)
        self.assertEqual((result.returncode,result.stdout,result.stderr),(0,expected,b''))

    def test_interior_and_saved_failure_roots_are_validated_and_collected(self):
        result=self.run_probe('graph-roots',r'''
.text
.globl _start
_start:
    xorl %ebp,%ebp
    call evn_scope_enter
    movq %rax,%r12
    movq %rax,%rdi
    leaq .Lgraph_keys(%rip),%rsi
    leaq .Lgraph_classes(%rip),%rdx
    movl $4,%ecx
    call evn_bind_roots
    leaq .Lgraph_root_text(%rip),%rdi
    movl $6,%esi
    call evn_text
    movq %rax,%r13
    movl $6,%edi
    movl $1,%esi
    call evn_object
    movq %rax,%r14
    movq %rax,%rdi
    xorl %esi,%esi
    movq %r13,%rdx
    call evn_init
    movq %r14,%rdi
    xorl %esi,%esi
    call evn_member_ref
    movq %rax,.Lgraph_keys(%rip)
    # Invalid exact keys and machine-class words must never be dereferenced.
    movq $1,.Lgraph_keys+8(%rip)
    movq %rax,.Lgraph_keys+16(%rip)
    movq $1,.Lgraph_keys+24(%rip)
    xorl %edi,%edi
    call erist_rt_slots_collect
    call erist_rt_text_collect
    call erist_rt_graph_live_objects
    cmpq $1,%rax
    jne .Lgraph_test_fail
    movq .Lgraph_keys(%rip),%rdi
    call evn_output
    # Clear the sole interior root; the machine copy must not retain its owner.
    movq $0,.Lgraph_keys(%rip)
    xorl %edi,%edi
    call erist_rt_slots_collect
    call erist_rt_text_collect
    call erist_rt_graph_live_objects
    testq %rax,%rax
    jne .Lgraph_test_fail
    call evn_frame
    movq %rax,%r13
    movq %rax,%rdi
    call setjmp
    testq %rax,%rax
    jne .Lgraph_caught
    movl $42,%edi
    call evn_int
    movq %rax,%r14
    leaq .Lgraph_root_text(%rip),%rdi
    movl $6,%esi
    call evn_text
    movq %rax,%r15
    movl $11,%edi
    movl $2,%esi
    call evn_object
    movq %rax,%rbx
    movq %rax,%rdi
    xorl %esi,%esi
    movq %r14,%rdx
    call evn_init
    movq %rbx,%rdi
    movl $1,%esi
    movq %r15,%rdx
    call evn_init
    movq %rbx,%rdi
    movl $1,%esi
    call evn_fail
    jmp .Lgraph_test_fail
.Lgraph_caught:
    movq %r13,%rdi
    call evn_pop
    call evn_saved
    movq %rax,.Lgraph_keys+8(%rip)
    call erist_rt_failure_clear
    xorl %edi,%edi
    call erist_rt_slots_collect
    call erist_rt_text_collect
    call erist_rt_live_failures
    cmpq $1,%rax
    jne .Lgraph_test_fail
    movq .Lgraph_keys+8(%rip),%rdi
    movl $11,%esi
    call evn_match
    cmpq $1,%rax
    jne .Lgraph_test_fail
    movq .Lgraph_keys+8(%rip),%rdi
    movl $12,%esi
    call evn_error
    movq %rax,%rdi
    xorl %esi,%esi
    call evn_member
    movq %rax,%rdi
    call evn_output
    call evn_void
    movq %r12,%rdi
    movq %rax,%rsi
    call evn_scope_leave
    jmp .Lgraph_finish
.bss
.p2align 3
.Lgraph_keys:
.zero 32
.section .rodata
.Lgraph_classes:
.byte 1,5,2,1
.Lgraph_root_text:
.ascii "rooted"
'''+FINISH)
        self.assertEqual((result.returncode,result.stdout,result.stderr),(0,b'rooted\nrooted\n',b''))

    def test_owned_context_restores_callee_registers_stack_and_fp_control(self):
        result=self.run_probe('graph-context',r'''
.text
.globl _start
_start:
    movq %rsp,.Lcontext_stack(%rip)
    movq $11,%rbx
    movq $22,%rbp
    movq $33,%r12
    movq $44,%r13
    movq $55,%r14
    movq $66,%r15
    ldmxcsr .Lcontext_mxcsr(%rip)
    fldcw .Lcontext_cw(%rip)
    leaq .Lcontext(%rip),%rdi
    call setjmp
    testq %rax,%rax
    jne .Lcontext_returned
    xorq %rbx,%rbx
    xorq %rbp,%rbp
    xorq %r12,%r12
    xorq %r13,%r13
    xorq %r14,%r14
    xorq %r15,%r15
    ldmxcsr .Lcontext_other_mxcsr(%rip)
    fldcw .Lcontext_other_cw(%rip)
    leaq .Lcontext(%rip),%rdi
    xorl %esi,%esi
    jmp longjmp
.Lcontext_returned:
    cmpq $1,%rax
    jne .Lgraph_test_fail
    cmpq .Lcontext_stack(%rip),%rsp
    jne .Lgraph_test_fail
    cmpq $11,%rbx
    jne .Lgraph_test_fail
    cmpq $22,%rbp
    jne .Lgraph_test_fail
    cmpq $33,%r12
    jne .Lgraph_test_fail
    cmpq $44,%r13
    jne .Lgraph_test_fail
    cmpq $55,%r14
    jne .Lgraph_test_fail
    cmpq $66,%r15
    jne .Lgraph_test_fail
    stmxcsr .Lcontext_actual(%rip)
    fnstcw .Lcontext_actual_cw(%rip)
    cmpl $0x1f80,.Lcontext_actual(%rip)
    jne .Lgraph_test_fail
    cmpw $0x37f,.Lcontext_actual_cw(%rip)
    jne .Lgraph_test_fail
    jmp .Lgraph_finish
.bss
.p2align 3
.Lcontext:
.zero 112
.Lcontext_stack:
.quad 0
.Lcontext_actual:
.zero 4
.Lcontext_actual_cw:
.zero 2
.section .rodata
.Lcontext_mxcsr:
.long 0x1f80
.Lcontext_other_mxcsr:
.long 0xffc0
.Lcontext_cw:
.word 0x37f
.Lcontext_other_cw:
.word 0x77f
'''+FINISH)
        self.assertEqual((result.returncode,result.stdout,result.stderr),(0,b'',b''))

    def test_bounds_absence_and_managed_administration_oom_are_terminal_faults(self):
        for name,source,message in (
            ('negative-index','let xs be [1]; output(xs[-1]);','List index out of bounds'),
            ('past-index','let xs be [1]; output(xs[1]);','List index out of bounds'),
            ('ref-index','let xs be [1]; xs[1]=2;','List index out of bounds'),
        ):
            with self.subTest(case=name):
                path=self.directory/(name+'.eri'); path.write_text(source)
                app=self.compile_application(path)
                result=self.run_probe(name,app+'\n.text\n.globl _start\n_start:\ncall erist_entry\n',types=False)
                self.assertEqual((result.returncode,result.stdout,result.stderr),
                                 (1,b'',f'Eristavi runtime fault: {message}\n'.encode()))
        for name,body,failure_at,count,message in (
            ('object-oom','movl $6,%edi\nmovl $1,%esi\ncall evn_object',1,0,'out of memory'),
            ('object-slot-oom','movl $6,%edi\nmovl $1,%esi\ncall evn_object',2,1,'out of memory'),
            ('handler-oom','call evn_frame',1,0,'out of memory'),
            ('handler-object-oom','call evn_frame\nmovq %rax,%rdi\ncall setjmp\ntestq %rax,%rax\njne .Lgraph_test_fail\nmovl $6,%edi\nmovl $1,%esi\ncall evn_object',2,0,'out of memory'),
            ('saved-oom','call evn_saved',1,0,'out of memory'),
            ('absent','movl $8,%edi\ncall evn_none\nmovq %rax,%rdi\ncall evn_get',0,0,'optional value is absent'),
            ('size-overflow','movl $6,%edi\nmovabsq $288230376151711743,%rsi\ncall evn_object',0,0,'value size overflow'),
        ):
            with self.subTest(case=name):
                runtime=self.runtime.replace('erist_rt_alloc:\n',f'''erist_rt_alloc:
    incq .Loom_calls(%rip)
    cmpq ${failure_at},.Loom_calls(%rip)
    jne .Loom_real_alloc
    xorl %eax,%eax
    ret
.Loom_real_alloc:
''',1)
                runtime=runtime.replace('erist_rt_exit:\n',f'''erist_rt_exit:
    cmpq ${count},.Lgraph_count(%rip)
    jne .Loom_bad_exit
''',1)
                result=self.run_probe(name,'.text\n.globl _start\n_start:\n'+body+
                    '\njmp .Lgraph_test_fail\n.Loom_bad_exit:\nmovl $99,%edi\nmovl $60,%eax\nsyscall\nud2\n.bss\n.Loom_calls:\n.quad 0\n'+FINISH,runtime)
                self.assertEqual((result.returncode,result.stdout,result.stderr),
                                 (1,b'',f'Eristavi runtime fault: {message}\n'.encode()))

    def test_deep_graph_marking_uses_bounded_stack_and_reclaims_every_cell(self):
        result=self.run_probe('graph-depth',r'''
.text
.globl _start
_start:
    xorl %ebp,%ebp
    call evn_scope_enter
    movq %rax,%r12
    movq %rax,%rdi
    leaq .Ldeep_key(%rip),%rsi
    leaq .Ldeep_class(%rip),%rdx
    movl $1,%ecx
    call evn_bind_roots
    # Private raw construction intentionally has no safe point until the root
    # is fully published. Each initialized cell has the compiler-described type.
    movl $1,%edi
    call erist_rt_graph_new_object
    movq %rax,%r13
    movq 8(%rax),%rdx
    movq $8,(%rdx)
    movl $20000,%r14d
.Ldeep_build:
    movl $1,%edi
    call erist_rt_graph_new_object
    movq %rax,%r15
    movl $1,%edi
    call erist_rt_graph_new_object
    movq %rax,%rbx
    movq 8(%rax),%rdx
    movq $10,(%rdx)
    movq %r13,8(%rdx)
    movl $1,%edi
    call erist_rt_graph_new_object
    movq %rax,%rcx
    movq 8(%rax),%rdx
    movq $9,(%rdx)
    movq %rbx,8(%rdx)
    movq 8(%r15),%rdx
    movq $8,(%rdx)
    movq %rcx,8(%rdx)
    movq %r15,%r13
    decq %r14
    jne .Ldeep_build
    movl $10,%edi
    movq %r13,%rsi
    call erist_rt_value_new
    movq %rax,.Ldeep_key(%rip)
    movq %rax,%rdi
    call erist_rt_slots_collect
    call erist_rt_text_collect
    call erist_rt_graph_live_objects
    cmpq $60001,%rax
    jne .Lgraph_test_fail
    movq $0,.Ldeep_key(%rip)
    xorl %edi,%edi
    call erist_rt_slots_collect
    call erist_rt_text_collect
    call erist_rt_graph_live_objects
    testq %rax,%rax
    jne .Lgraph_test_fail
    call evn_void
    movq %r12,%rdi
    movq %rax,%rsi
    call evn_scope_leave
    jmp .Lgraph_finish
.bss
.p2align 3
.Ldeep_key:
.quad 0
.section .rodata
.Ldeep_class:
.byte 1
'''+FINISH)
        self.assertEqual((result.returncode,result.stdout,result.stderr),(0,b'',b''))

    def test_uncaught_failure_keeps_nonfirst_message_field_and_embedded_nul(self):
        result=self.run_probe('graph-uncaught',r'''
.text
.globl _start
_start:
    xorl %ebp,%ebp
    movl $11,%edi
    movl $2,%esi
    call evn_object
    movq %rax,%r12
    movl $42,%edi
    call evn_int
    movq %r12,%rdi
    xorl %esi,%esi
    movq %rax,%rdx
    call evn_init
    leaq .Luncaught_message(%rip),%rdi
    movl $7,%esi
    call evn_text
    movq %r12,%rdi
    movl $1,%esi
    movq %rax,%rdx
    call evn_init
    movq %r12,%rdi
    movl $1,%esi
    call evn_fail
    jmp .Lgraph_test_fail
.section .rodata
.Luncaught_message:
.byte 98,111,111,109,0,206,178
'''+FINISH)
        self.assertEqual((result.returncode,result.stdout,result.stderr),
                         (1,b'',b'Eristavi runtime fault: boom\0\xce\xb2\n'))
