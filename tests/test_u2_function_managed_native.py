"""Exact canonical managed-identity SSA -> whole-Function native roots.

This constructs the actual frozen UIR Function, checks independent SSA
liveness, and physically executes its machine code using the owned collector.
The program only accepts boxed managed arguments and transfers a boxed
identity return into an already registered caller root.
"""
from pathlib import Path
import platform
import re
import subprocess
import unittest
from compiler.erist.cli import build_native, compile_entry
from compiler.erist.runtime_ext import Interpreter
import test_freestanding_graph_values as graph
import test_u2_text_unicode17 as unicodeTests

ROOT=Path(__file__).resolve().parents[1]


@unittest.skipUnless(platform.system()=="Linux" and
                     platform.machine().lower() in ("x86_64","amd64"),
                     "native managed Function/GC requires Linux x86-64")
class U2FunctionManagedNativeTests(unittest.TestCase):
    setUpClass=classmethod(graph.FreestandingGraphValueTests.setUpClass.__func__)
    run_probe=graph.FreestandingGraphValueTests.run_probe

    def source(self):
        return (ROOT/"tests/fixtures/u2_function_managed_cfg.eri").read_text(
            encoding="utf-8")

    def generator(self,name,source):
        folder=self.directory/name
        folder.mkdir(exist_ok=True)
        (folder/"compiler").symlink_to(
            ROOT/"src/compiler",target_is_directory=True)
        path=folder/"generator.eri"
        path.write_text(source,encoding="utf-8")
        native=folder/"generator"
        self.assertEqual(build_native(path,native,folder),0)
        return subprocess.run([str(native)],capture_output=True,
                              text=True,timeout=150)

    def test_whole_function_identity_phi_and_gc_with_rooted_return(self):
        generated=self.generator("managed-native-function",self.source())
        self.assertEqual((generated.returncode,generated.stderr),(0,""),
                         generated.stdout[-3000:])
        asm=generated.stdout
        base="erist_u2_rooted_function_91"
        self.assertIn(base+":",asm)
        for i in range(1,6):
            self.assertIn(base+"_block_"+str(i)+":",asm)
        self.assertIn("call evn_bind_roots",asm)
        self.assertGreaterEqual(asm.count("call erist_rt_slots_collect"),5)
        slots=re.findall(r"^\.set "+base+r"_root_(\d+), (\d+)$",asm,re.M)
        self.assertGreaterEqual(len(slots),3)
        self.assertEqual(len({int(value) for value,_ in slots}),len(slots))
        # The caller-owned registered output root must be published before
        # the callee's rooted scope gets retired.
        ret=asm.split(base+"_block_3:",1)[1].split(
            base+"_block_4:",1)[0]
        self.assertIn("call evn_scope_leave",ret)
        self.assertIn("movq %rax,(%rdi)",ret)
        self.assertLess(ret.index("movq %rax,(%rdi)"),
                        ret.index("call evn_scope_leave"))
        body=r"""
.text
.globl _start
_start:
    xorl %ebp,%ebp
    # Enter the parent scope BEFORE creating the managed producer.
    # The caller's destination class-1 root is already registered but
    # initially empty; the child must publish its own roots before GC.
    call evn_scope_enter
    movq %rax,%r15
    movq %rax,%rdi
    leaq .Lu2_managed_caller_root(%rip),%rsi
    leaq .Lu2_managed_caller_class(%rip),%rdx
    movl $1,%ecx
    call evn_bind_roots

    movl $1,%edi
    call erist_rt_graph_new_object
    movq %rax,%r12
    movl $1,%edi
    call erist_rt_graph_new_object
    movq %rax,%r13
    movl $1,%edi
    call erist_rt_graph_new_object
    movq %rax,%r14
    movq 8(%r12),%rax
    movq $8,(%rax)
    movq %r13,8(%rax)
    movq 8(%r13),%rax
    movq $9,(%rax)
    movq %r14,8(%rax)
    movq 8(%r14),%rax
    movq $10,(%rax)
    movq %r12,8(%rax)
    movl $10,%edi
    movq %r12,%rsi
    call erist_rt_value_new
    movq %rax,.Lu2_managed_input(%rip)
    movq $37,.Lu2_managed_input+8(%rip)

    leaq .Lu2_managed_input(%rip),%rdi
    leaq .Lu2_managed_caller_root(%rip),%rsi
    call erist_u2_rooted_function_91
    cmpq $37,%rdx
    jne .Lgraph_test_fail
    testq %rax,%rax
    je .Lgraph_test_fail
    cmpq %rax,.Lu2_managed_caller_root(%rip)
    jne .Lgraph_test_fail
    xorl %edi,%edi
    call erist_rt_slots_collect
    call erist_rt_text_collect
    call erist_rt_graph_live_objects
    cmpq $3,%rax
    jne .Lgraph_test_fail
    # All callee SSA/root words and scope are gone. Only the caller's
    # single explicitly registered root retains the three-node cycle.
    movq $0,.Lu2_managed_caller_root(%rip)
    xorl %edi,%edi
    call erist_rt_slots_collect
    call erist_rt_text_collect
    call erist_rt_graph_live_objects
    testq %rax,%rax
    jne .Lgraph_test_fail
    call evn_void
    movq %rax,%rsi
    movq %r15,%rdi
    call evn_scope_leave
    jmp .Lgraph_finish
.bss
.p2align 3
.Lu2_managed_input:
.zero 16
.Lu2_managed_caller_root:
.zero 8
.section .rodata
.Lu2_managed_caller_class:
.byte 1
"""
        executed=self.run_probe(
            "u2-function-managed-identity-loop-gc",asm+body+graph.FINISH)
        self.assertEqual((executed.returncode,executed.stdout,
                          executed.stderr),(0,b"",b""))

    def mixed_source(self):
        source=self.source()
        def unique(old,new):
            nonlocal source
            self.assertEqual(source.count(old),1,old)
            source=source.replace(old,new,1)
        unique("    let carrier be try aggregate.aggregate(graph,mp,[i64,i64]);",
               "    let carrier be try aggregate.aggregate(graph,mp,[i64,i64]);\n"
               "    let textCarrier be try aggregate.aggregate(graph,mp,[]);")
        unique("[carrier,i64],[carrier,i64]);",
               "[carrier,textCarrier,i64],[carrier,textCarrier]);")
        unique("    let entry be try ab.block(fn,graph,[carrier,i64]);",
               "    let entry be try ab.block(fn,graph,[carrier,textCarrier,i64]);")
        unique("    let input be try build.parameter(fn,entry,1);",
               "    let textInput be try build.parameter(fn,entry,1);\n"
               "    let input be try build.parameter(fn,entry,2);")
        unique("    let loop be try ab.block(fn,graph,[carrier,i64,pred]);",
               "    let loop be try ab.block(fn,graph,"
               "[carrier,textCarrier,i64,pred]);")
        unique("    let exit be try ab.block(fn,graph,[carrier,i64]);",
               "    let exit be try ab.block(fn,graph,[carrier,textCarrier]);")
        unique("[managedInput,input,on],loc);",
               "[managedInput,textInput,input,on],loc);")
        unique("    let carried be try build.parameter(fn,loop,1);",
               "    let textCurrent be try build.parameter(fn,loop,1);\n"
               "    let carried be try build.parameter(fn,loop,2);")
        unique("    let once be try build.parameter(fn,loop,2);",
               "    let once be try build.parameter(fn,loop,3);")
        unique("    try ab.branch(fn,graph,loop,once,loop,[current,carried,off],\n"
               "        exit,[current,carried],loc);",
               "    try ab.branch(fn,graph,loop,once,loop,"
               "[current,textCurrent,carried,off],\n"
               "        exit,[current,textCurrent],loc);")
        unique("    let scalarResult be try build.parameter(fn,exit,1);",
               "    let textResult be try build.parameter(fn,exit,1);")
        unique("[managedResult,scalarResult],loc);",
               "[managedResult,textResult],loc);")
        unique("[managedInput,deadValue],loc);",
               "[managedInput,textInput],loc);")
        unique("[carrier],[identityType],true,91);",
               "[carrier,textCarrier],[identityType,managed.text(registry)],true,91);")
        return source

    def test_mixed_text_and_identity_roots_across_loop_and_return(self):
        generated=self.generator("managed-text-identity",self.mixed_source())
        self.assertEqual((generated.returncode,generated.stderr),
                         (0,""),generated.stdout[-2800:])
        asm=generated.stdout
        base="erist_u2_rooted_function_91"
        slots=re.findall(r"^\.set "+base+r"_root_(\d+), (\d+)$",
                         asm,re.M)
        self.assertGreaterEqual(len(slots),6)
        self.assertIn("movq %rdx,8(%rdi)",asm)
        self.assertIn("cmpq $2,%rdx",asm)
        body=r"""
.text
.globl _start
_start:
    xorl %ebp,%ebp
    # Two distinct, already-registered caller roots. No graph or Text
    # allocation precedes the initial scope mark.
    call evn_scope_enter
    movq %rax,%r15
    movq %rax,%rdi
    leaq .Lu2_managed_caller_roots(%rip),%rsi
    leaq .Lu2_managed_caller_classes(%rip),%rdx
    movl $2,%ecx
    call evn_bind_roots

    movl $1,%edi
    call erist_rt_graph_new_object
    movq %rax,%r12
    movl $1,%edi
    call erist_rt_graph_new_object
    movq %rax,%r13
    movl $1,%edi
    call erist_rt_graph_new_object
    movq %rax,%r14
    movq 8(%r12),%rax
    movq $8,(%rax)
    movq %r13,8(%rax)
    movq 8(%r13),%rax
    movq $9,(%rax)
    movq %r14,8(%rax)
    movq 8(%r14),%rax
    movq $10,(%rax)
    movq %r12,8(%rax)
    movl $10,%edi
    movq %r12,%rsi
    call erist_rt_value_new
    movq %rax,.Lu2_managed_mixed_inputs(%rip)

    leaq .Lu2_mixed_text(%rip),%rdi
    movl $7,%esi
    call evn_text
    movq %rax,.Lu2_managed_mixed_inputs+8(%rip)
    movq $37,.Lu2_managed_mixed_inputs+16(%rip)

    leaq .Lu2_managed_mixed_inputs(%rip),%rdi
    leaq .Lu2_managed_caller_roots(%rip),%rsi
    movl $2,%edx
    call erist_u2_rooted_function_91
    cmpq %rax,.Lu2_managed_caller_roots(%rip)
    jne .Lgraph_test_fail
    cmpq %rdx,.Lu2_managed_caller_roots+8(%rip)
    jne .Lgraph_test_fail
    xorl %edi,%edi
    call erist_rt_slots_collect
    call erist_rt_text_collect
    call erist_rt_graph_live_objects
    cmpq $3,%rax
    jne .Lgraph_test_fail
    call erist_rt_text_live_buffers
    testq %rax,%rax
    je .Lgraph_test_fail

    # Retire identity while Text remains rooted.
    movq $0,.Lu2_managed_caller_roots(%rip)
    xorl %edi,%edi
    call erist_rt_slots_collect
    call erist_rt_text_collect
    call erist_rt_graph_live_objects
    testq %rax,%rax
    jne .Lgraph_test_fail
    call erist_rt_text_live_buffers
    testq %rax,%rax
    je .Lgraph_test_fail

    # Then retire the remaining Text root and reclaim the backing.
    movq $0,.Lu2_managed_caller_roots+8(%rip)
    xorl %edi,%edi
    call erist_rt_slots_collect
    call erist_rt_text_collect
    call erist_rt_text_live_buffers
    testq %rax,%rax
    jne .Lgraph_test_fail
    call evn_void
    movq %rax,%rsi
    movq %r15,%rdi
    call evn_scope_leave
    jmp .Lgraph_finish
.bss
.p2align 3
.Lu2_managed_mixed_inputs:
.zero 24
.Lu2_managed_caller_roots:
.zero 16
.section .rodata
.Lu2_managed_caller_classes:
.byte 1,1
.Lu2_mixed_text:
.ascii "managed"
"""
        executed=self.run_probe("u2-mixed-text-identity-rooted-function",
                                asm+body+graph.FINISH)
        self.assertEqual((executed.returncode,executed.stdout,
                          executed.stderr),(0,b"",b""))

    def test_reject_mismatched_identity_descriptor_before_emission(self):
        source=self.source()
        original="[carrier],[identityType],true,91);"
        self.assertEqual(source.count(original),1)
        source=source.replace(original,
                              "[carrier],[managed.text(registry)],true,91);",1)
        generated=self.generator("managed-wrong-descriptor",source)
        self.assertEqual(generated.returncode,1,generated.stdout[-2000:])
        self.assertIn("roots:",generated.stdout)
        self.assertNotIn("erist_u2_rooted_function_91:",generated.stdout)
        self.assertNotIn(".section",generated.stdout)

    def test_reject_managed_producer_in_dead_block_before_emission(self):
        source=self.source()
        original="    try build.jump(fn,dead,deadDestination,[deadValue],loc);"
        self.assertEqual(source.count(original),1)
        source=source.replace(original,
            "    let unsupportedProducer be try ab.make("
            "fn,graph,dead,carrier,[deadValue,deadValue],loc);\n"
            +original,1)
        generated=self.generator("managed-dead-producer",source)
        self.assertEqual(generated.returncode,1,generated.stdout[-2200:])
        self.assertIn("unsupported:",generated.stdout)
        self.assertNotIn("erist_u2_rooted_function_91:",generated.stdout)
        self.assertNotIn(".section",generated.stdout)

    def recursive_source(self):
        return (ROOT/"tests/fixtures/u2_function_managed_recursive.eri").read_text(
            encoding="utf-8")

    def test_recursive_function_parent_only_text_roots_and_scalar_result(self):
        generated=self.generator("managed-recursive",self.recursive_source())
        self.assertEqual((generated.returncode,generated.stderr),(0,""),
                         generated.stdout[-3000:])
        asm=generated.stdout
        self.assertIn("call erist_u2_rooted_function_91",asm)
        # Count physical collector entries and check post-return Text reclamation.
        # Parent-only Text differs at every level and is read after the child
        # returns. No handwritten native recursion or external per-frame roots.
        runtime=self.runtime.replace("erist_rt_slots_collect:\n",
            "erist_rt_slots_collect:\n    incq .Lrecursive_gc_calls(%rip)\n",1)
        self.assertNotEqual(runtime,self.runtime)
        depths=(0,1,5,32,64)
        # Frozen source -> Stage-0 and the existing native compiler are
        # independent of this hand-built original canonical UIR Function.
        reference=ROOT/"tests/fixtures/u2_function_managed_recursive_reference.eri"
        module=compile_entry(reference,ROOT/"tests/fixtures")
        observed=[]
        interpreter=Interpreter(output=observed.append,module_id=module.module_id,
                                imported_modules=module.imports)
        interpreter.run(module.program)
        expected=[str(6+depth) for depth in depths]
        self.assertEqual(observed,expected)
        binary=self.directory/"recursive-source-reference"
        self.assertEqual(build_native(reference,binary,ROOT/"tests/fixtures"),0)
        reference_run=subprocess.run([str(binary)],capture_output=True,text=True,
                                     timeout=30)
        self.assertEqual((reference_run.returncode,reference_run.stderr),(0,""))
        self.assertEqual(reference_run.stdout.splitlines(),expected)
        for depth in depths:
            with self.subTest(depth=depth):
                body=self.recursive_caller(depth,6+depth)
                # Emit the new native result only after checking the returned
                # identity. Compare all three executions against one oracle.
                body=body.replace("    xorl %edi,%edi\n    call erist_rt_slots_collect",
                    "    movq %rdx,%rdi\n    call evn_int\n"
                    "    movq %rax,%rdi\n    call evn_output\n"
                    "    xorl %edi,%edi\n    call erist_rt_slots_collect",1)
                result=self.run_probe(f"u2-managed-recursive-{depth}",
                    asm+body+graph.FINISH+unicodeTests.unicode_descriptors(),
                    runtime=runtime,types=False)
                self.assertEqual((result.returncode,result.stdout,result.stderr),
                                 (0,(str(6+depth)+"\n").encode(),b""))

    def test_recursive_import_or_mismatched_signature_rejected_before_emission(self):
        original=self.recursive_source()
        for name,replacement in (
            ("import",'signature,"u2.recursive.managed",2,63,1);'),
            ("effects",'signature,"u2.recursive.managed",1,31,0);'),
        ):
            with self.subTest(case=name):
                source=original.replace(
                    'signature,"u2.recursive.managed",1,63,0);',replacement,1)
                generated=self.generator("managed-recursive-bad-"+name,source)
                self.assertEqual(generated.returncode,1,generated.stdout[-2500:])
                self.assertIn("unsupported:",generated.stdout)
                self.assertNotIn(".section",generated.stdout)
        # A defined target with the wrong canonical signature is invalid
        # even when the body never calls it (no prevalidated-flag shortcut).
        source=original.replace('signature,"u2.recursive.managed",1,63,0);',
            'scalarSpecialization,"u2.recursive.managed",1,63,0);',1)
        # Remove the now ill-typed recursive instruction so the boundary,
        # rather than builder arity checks, must refuse the wrong binding.
        begin=source.index("    let call be try ab.call(fn,graph,recurse,selfTarget,")
        end=source.index("    // This Text",begin)
        source=source[:begin]+"    let returnedIdentity be managedInput;\n    let returnedCount be zero;\n"+source[end:]
        generated=self.generator("managed-recursive-wrong-signature",source)
        self.assertEqual(generated.returncode,1,generated.stdout[-2500:])
        self.assertIn("unsupported:",generated.stdout)
        self.assertNotIn(".section",generated.stdout)
        for label,target in (
            ("zero", "meta.FunctionId { owner=data.key; index=0; }"),
            ("foreign", "meta.FunctionId { owner=graph.key; index=selfTarget.index; }"),
        ):
            with self.subTest(target=label):
                source=original.replace("true,91,selfTarget);",
                                        "true,91,"+target+");",1)
                generated=self.generator("managed-recursive-target-"+label,source)
                self.assertEqual(generated.returncode,1,generated.stdout[-2500:])
                self.assertIn("unsupported:",generated.stdout)
                self.assertNotIn(".section",generated.stdout)

    def recursive_caller(self,depth,expected):
        body=r'''
.text
.globl _start
_start:
    xorl %ebp,%ebp
    call evn_scope_enter
    movq %rax,%r15
    movq %rax,%rdi
    leaq .Lrecursive_roots(%rip),%rsi
    leaq .Lrecursive_classes(%rip),%rdx
    movl $2,%ecx
    call evn_bind_roots
    # Create a three-node identity cycle retained by every live call frame.
    movl $1,%edi
    call erist_rt_graph_new_object
    movq %rax,%r12
    movl $1,%edi
    call erist_rt_graph_new_object
    movq %rax,%r13
    movl $1,%edi
    call erist_rt_graph_new_object
    movq %rax,%r14
    movq 8(%r12),%rax
    movq $8,(%rax)
    movq %r13,8(%rax)
    movq 8(%r13),%rax
    movq $9,(%rax)
    movq %r14,8(%rax)
    movq 8(%r14),%rax
    movq $10,(%rax)
    movq %r12,8(%rax)
    movl $10,%edi
    movq %r12,%rsi
    call erist_rt_value_new
    movq %rax,.Lrecursive_roots(%rip)
    movq %rax,.Lrecursive_inputs(%rip)
    leaq .Lrecursive_text(%rip),%rdi
    movl $6,%esi
    call evn_text
    movq %rax,.Lrecursive_roots+8(%rip)
    movq %rax,.Lrecursive_inputs+8(%rip)
    movq $DEPTH,.Lrecursive_inputs+16(%rip)
    leaq .Lrecursive_inputs(%rip),%rdi
    leaq .Lrecursive_roots(%rip),%rsi
    movl $2,%edx
    call erist_u2_rooted_function_91
    cmpq $EXPECTED,%rdx
    jne .Lgraph_test_fail
    cmpq %rax,.Lrecursive_roots(%rip)
    jne .Lgraph_test_fail
    cmpq %rax,.Lrecursive_inputs(%rip)
    jne .Lgraph_test_fail
    cmpq $MIN_GC,.Lrecursive_gc_calls(%rip)
    jb .Lgraph_test_fail
    xorl %edi,%edi
    call erist_rt_slots_collect
    call erist_rt_text_collect
    call erist_rt_graph_live_objects
    cmpq $3,%rax
    jne .Lgraph_test_fail
    # Only the original caller Text survives; all child frames are gone.
    call erist_rt_text_live_buffers
    cmpq $1,%rax
    jne .Lgraph_test_fail
    movq $0,.Lrecursive_roots(%rip)
    movq $0,.Lrecursive_roots+8(%rip)
    xorl %edi,%edi
    call erist_rt_slots_collect
    call erist_rt_text_collect
    call evn_void
    movq %rax,%rsi
    movq %r15,%rdi
    call evn_scope_leave
    jmp .Lgraph_finish
.bss
.p2align 3
.Lrecursive_inputs:
.zero 24
.Lrecursive_roots:
.zero 16
.Lrecursive_gc_calls:
.zero 8
.section .rodata
.Lrecursive_classes:
.byte 1,1
.Lrecursive_text:
.ascii "parent"
'''
        return body.replace("DEPTH",str(depth)).replace(
            "EXPECTED",str(expected)).replace("MIN_GC",str(2*depth+2))

    def test_recursive_two_managed_results_handoff_before_child_scope_leave(self):
        source=self.recursive_source()
        source=source.replace("[carrier,textCarrier,i64],[carrier,i64]);",
                              "[carrier,textCarrier,i64],[textCarrier,carrier]);",1)
        source=source.replace("let returnedIdentity be try build.result(fn,call,0);",
                              "let returnedIdentity be try build.result(fn,call,1);",1)
        source=source.replace("let returnedCount be try build.result(fn,call,1);",
                              "let returnedText be try build.result(fn,call,0);",1)
        source=source.replace("let total be try build.wrapAdd(fn,recurse,returnedCount,ownCount,loc);", "")
        source=source.replace("[returnedIdentity,total],loc);", "[textInput,returnedIdentity],loc);",1)
        source=source.replace("[managedInput,baseCount],loc);", "[textInput,managedInput],loc);",1)
        source=source.replace("[managedInput,deadValue],loc);", "[textInput,managedInput],loc);",1)
        generated=self.generator("managed-recursive-two-returns",source)
        self.assertEqual((generated.returncode,generated.stderr),(0,""),
                         generated.stdout[-3000:])
        self.assertIn("movq %rdx,8(%rdi)",generated.stdout)
        body=self.recursive_caller(32,0).replace(
            "cmpq $0,%rdx", "cmpq %rdx,.Lrecursive_roots+8(%rip)",1)
        body=body.replace("cmpq %rax,.Lrecursive_inputs(%rip)",
                          "cmpq %rdx,.Lrecursive_inputs(%rip)",1)
        runtime=self.runtime.replace("erist_rt_slots_collect:\n",
            "erist_rt_slots_collect:\n    incq .Lrecursive_gc_calls(%rip)\n",1)
        result=self.run_probe("u2-recursive-two-managed-returns",
            generated.stdout+body+graph.FINISH+unicodeTests.unicode_descriptors(),
            runtime=runtime,types=False)
        self.assertEqual((result.returncode,result.stdout,result.stderr),(0,b"",b""))
