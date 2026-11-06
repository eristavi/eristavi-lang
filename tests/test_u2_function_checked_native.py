"""Canonical checked Function recursion: native branches, typed failures and roots."""
from pathlib import Path
import os
import platform
import select
import shutil
import subprocess
import time
import unittest

from compiler.erist.cli import build_native, compile_entry
from compiler.erist.runtime_ext import Interpreter
import test_freestanding_graph_values as graph
import test_u2_text_unicode17 as unicodeTests
import test_u2_scoped_owners as ownerTests
import test_u2_function_managed_native as managedTests
from test_freestanding_text_lifetimes import audit_slot_count

ROOT=Path(__file__).resolve().parents[1]



def capture_traced_owned_generator(command,env,timeout):
    """Read static owned-generator output, timestamping original phase markers.

    The elapsed watchdog remains unchanged; captured bytes and exit status
    remain available for the exact independent C-generator comparison.
    """
    begun=time.monotonic()
    stdout=bytearray()
    stderr=bytearray()
    pending=b""
    process=subprocess.Popen(command,env=env,stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    streams={process.stdout:stdout,process.stderr:stderr}
    try:
        while streams:
            remaining=timeout-(time.monotonic()-begun)
            if remaining<=0:
                raise subprocess.TimeoutExpired(command,timeout,
                                                bytes(stdout),bytes(stderr))
            ready,_,_=select.select(list(streams),[],[],remaining)
            if not ready:
                raise subprocess.TimeoutExpired(command,timeout,
                                                bytes(stdout),bytes(stderr))
            for stream in ready:
                chunk=os.read(stream.fileno(),8192)
                if not chunk:
                    del streams[stream]
                    continue
                if stream is process.stdout:
                    stdout.extend(chunk)
                    pending+=chunk
                    lines=pending.split(b"\n")
                    pending=lines.pop()
                    for line in lines:
                        if b"U2_GENERATOR_TRACE:" in line or b"U2_NATIVE_TRACE:" in line:
                            print("U2_GENERATOR_PHASE_SECONDS="+
                                  format(time.monotonic()-begun,".3f")+
                                  " marker="+line.decode(errors="replace"),flush=True)
                else:
                    stderr.extend(chunk)
        remaining=max(0,timeout-(time.monotonic()-begun))
        status=process.wait(timeout=remaining)
        return subprocess.CompletedProcess(command,status,
                                           bytes(stdout),bytes(stderr))
    finally:
        if process.poll() is None:
            process.kill()
        process.wait()
        process.stdout.close()
        process.stderr.close()


@unittest.skipUnless(platform.system()=="Linux" and
                     platform.machine().lower() in ("x86_64","amd64"),
                     "owned native checked Function requires Linux x86-64")
class U2FunctionCheckedNativeTests(unittest.TestCase):
    setUpClass=classmethod(graph.FreestandingGraphValueTests.setUpClass.__func__)
    run_probe=graph.FreestandingGraphValueTests.run_probe
    generator=managedTests.U2FunctionManagedNativeTests.generator
    recursive_caller=managedTests.U2FunctionManagedNativeTests.recursive_caller

    def source(self):
        return (ROOT/"tests/fixtures/u2_function_checked_recursive.eri").read_text(
            encoding="utf-8")

    def checked_caller(self,depth,failed,handled=False,arity=2):
        body=self.recursive_caller(depth,6+depth)
        body=body.replace("movl $2,%ecx\n    call evn_bind_roots",
                          "movl $4,%ecx\n    call evn_bind_roots",1)
        begin=body.index("    movq $"+str(depth)+",.Lrecursive_inputs+16(%rip)")
        end=body.index("    cmpq $"+str(2*depth+2)+",.Lrecursive_gc_calls",begin)
        prefix=r'''
    # Only this test setup uses the established runtime failure adapter.
    # The generated recursive Function below has explicit typed outcomes.
    call evn_frame
    movq %rax,%r13
    movq %rax,%rdi
    call setjmp
    testq %rax,%rax
    jne .Lchecked_saved
    movl $42,%edi
    call evn_int
    movq %rax,%r14
    leaq .Lchecked_message(%rip),%rdi
    movl $10,%esi
    call evn_text
    movq %rax,%rbx
    movl $11,%edi
    movl $2,%esi
    call evn_object
    movq %rax,%r12
    movq %rax,%rdi
    xorl %esi,%esi
    movq %r14,%rdx
    call evn_init
    movq %r12,%rdi
    movl $1,%esi
    movq %rbx,%rdx
    call evn_init
    movq %r12,%rdi
    movl $1,%esi
    call evn_fail
    jmp .Lgraph_test_fail
.Lchecked_saved:
    movq %r13,%rdi
    call evn_pop
    call evn_saved
    movq %rax,.Lrecursive_inputs+16(%rip)
    movq %rax,.Lrecursive_roots+16(%rip)
    call erist_rt_failure_clear
    movq $DEPTH,.Lrecursive_inputs+24(%rip)
    movq $FAILED,.Lrecursive_inputs+32(%rip)
    leaq .Lrecursive_inputs(%rip),%rdi
    leaq .Lrecursive_roots(%rip),%rsi
    movl $2,%edx
    leaq .Lrecursive_roots+24(%rip),%rcx
    call erist_u2_rooted_function_92
'''.replace("DEPTH",str(depth)).replace("FAILED",str(int(failed)))
        returns_failure=failed and not handled
        if returns_failure:
            prefix+=r'''
    cmpq $1,%r10
    jne .Lgraph_test_fail
    testq %rdx,%rdx
    jne .Lgraph_test_fail
    cmpq %rax,.Lrecursive_roots+24(%rip)
    jne .Lgraph_test_fail
    cmpq %rax,.Lrecursive_inputs+16(%rip)
    jne .Lgraph_test_fail
'''
        else:
            expected=(depth+5 if failed else depth+6)
            if arity == 0:
                prefix+=r'''
    testq %r10,%r10
    jne .Lgraph_test_fail
    testq %rax,%rax
    jne .Lgraph_test_fail
    testq %rdx,%rdx
    jne .Lgraph_test_fail
    cmpq $0,.Lrecursive_roots+24(%rip)
    jne .Lgraph_test_fail
'''
            elif arity == 1:
                prefix+=r'''
    testq %r10,%r10
    jne .Lgraph_test_fail
    cmpq $EXPECTED,%rax
    jne .Lgraph_test_fail
    testq %rdx,%rdx
    jne .Lgraph_test_fail
    cmpq $0,.Lrecursive_roots+24(%rip)
    jne .Lgraph_test_fail
'''.replace("EXPECTED",str(expected))
            else:
                prefix+=f'''
    testq %r10,%r10
    jne .Lgraph_test_fail
    cmpq ${expected},%rdx
    jne .Lgraph_test_fail
    cmpq %rax,.Lrecursive_inputs(%rip)
    jne .Lgraph_test_fail
    cmpq %rax,.Lrecursive_roots(%rip)
    jne .Lgraph_test_fail
    cmpq $0,.Lrecursive_roots+24(%rip)
    jne .Lgraph_test_fail
'''
        body=body[:begin]+prefix+body[end:]
        body=body.replace("cmpq $3,%rax",f"cmpq ${4 if returns_failure else 3},%rax",1)
        body=body.replace("cmpq $1,%rax",f"cmpq ${2 if returns_failure else 1},%rax",1)
        # Inspect the exact primary Text through the same runtime adapter.
        marker="    movq $0,.Lrecursive_roots(%rip)"
        inspect=r'''
    call erist_rt_live_failures
    cmpq $FAILURES,%rax
    jne .Lgraph_test_fail
'''.replace("FAILURES",str(int(returns_failure)))
        if returns_failure:
            inspect+=r'''
    movq .Lrecursive_roots+24(%rip),%rdi
    movl $12,%esi
    call evn_error
    movq %rax,%rdi
    xorl %esi,%esi
    call evn_member
    movq %rax,%rdi
    call evn_output
'''
        inspect+="    movq $0,.Lrecursive_roots+24(%rip)\n"
        body=body.replace(marker,inspect+marker,1)
        body=body.replace(".Lrecursive_inputs:\n.zero 24", ".Lrecursive_inputs:\n.zero 40",1)
        body=body.replace(".Lrecursive_roots:\n.zero 16", ".Lrecursive_roots:\n.zero 32",1)
        body=body.replace(".byte 1,1", ".byte 1,1,5,5",1)
        body+='\n.section .rodata\n.Lchecked_message:\n.ascii "primary-\\316\\262"\n'
        return body

    def run_checked(self,name,source,cases,dual=False,arity=2):
        generated=self.generator(name,source)
        self.assertEqual((generated.returncode,generated.stderr),(0,""),
                         generated.stdout[-3500:])
        asm=generated.stdout
        self.assertIn("call erist_u2_rooted_function_92",asm)
        self.assertIn("movl $1,%r10d",asm)
        self.assertIn(".byte 5",asm)
        self.assertNotIn("call setjmp",asm)
        self.assertNotIn("call evn_fail",asm)
        # Retire only the external ingress root after the generated frame has
        # published its own canonical roots, immediately before its first GC.
        # Internal recursive frames and all failure returns are compiler-owned.
        asm=asm.replace("    call erist_rt_slots_collect",
            "    movq $0,.Lrecursive_roots+16(%rip)\n"
            "    call erist_rt_slots_collect")
        runtime=self.runtime.replace("erist_rt_slots_collect:\n",
            "erist_rt_slots_collect:\n    incq .Lrecursive_gc_calls(%rip)\n",1)
        outcomes=[]
        for depth,failed,handled in cases:
            with self.subTest(depth=depth,failed=failed,handled=handled):
                caller=self.checked_caller(depth,failed,handled,arity)
                returns_failure=failed and not handled
                expected="primary-β\n".encode() if returns_failure else b""
                if not returns_failure and arity != 0:
                    count=depth+5 if failed else depth+6
                    if dual:
                        caller=caller.replace(f"cmpq ${count},%rdx",
                            "cmpq %rdx,.Lrecursive_roots+8(%rip)",1)
                        output="    movq .Lrecursive_roots+8(%rip),%rdi\n    call evn_output\n"
                        expected=b"parent\ntrue\n"
                    else:
                        result_register="%rax" if arity == 1 else "%rdx"
                        output="    movq "+result_register+",%rdi\n    call evn_int\n    movq %rax,%rdi\n    call evn_output\n"
                        expected=(str(count)+"\n"+("" if arity == 1 else "true\n")).encode()
                    if arity != 1:
                        output+="    movq .Lrecursive_roots(%rip),%rax\n    cmpq .Lrecursive_inputs(%rip),%rax\n    sete %dil\n    movzbq %dil,%rdi\n    call evn_bool\n    movq %rax,%rdi\n    call evn_output\n"
                    marker=f"    cmpq ${2*depth+2},.Lrecursive_gc_calls"
                    caller=caller.replace(marker,output+marker,1)
                executed=self.run_probe(f"{name}-{depth}-{int(failed)}-{int(handled)}",
                    asm+caller+graph.FINISH+unicodeTests.unicode_descriptors(),
                    runtime=runtime,types=False)
                self.assertEqual((executed.returncode,executed.stdout,executed.stderr),
                                 (0,expected,b""))
                outcomes.append(executed.stdout)
        return b"".join(outcomes)

    def test_checked_recursive_normal_failure_edges_roots_and_reclamation(self):
        observed=self.run_checked("checked-recursive",self.source(),
            [(depth,failed,False) for depth in (0,1,5,32,64)
             for failed in (False,True)])
        reference=ROOT/"tests/fixtures/u2_function_checked_recursive_reference.eri"
        module=compile_entry(reference,reference.parent)
        stage0=[]
        Interpreter(output=stage0.append,module_id=module.module_id,
                    imported_modules=module.imports).run(module.program)
        expected="".join(f"{6+depth}\ntrue\nprimary-β\n" for depth in (0,1,5,32,64))
        self.assertEqual("\n".join(stage0)+"\n",expected)
        binary=self.directory/"checked-source-reference"
        self.assertEqual(build_native(reference,binary,reference.parent),0)
        old_native=subprocess.run([str(binary)],capture_output=True,timeout=30)
        self.assertEqual((old_native.returncode,old_native.stdout,old_native.stderr),
                         (0,expected.encode(),b""))
        self.assertEqual(observed,old_native.stdout)

    def test_checked_failure_handler_returns_normal_through_parent_frames(self):
        source=self.source().replace(
            "let propagated be try body.returnFailure(fn,graph,table,failed,failedResult,loc);",
            "try ab.returnValues(fn,graph,failed,[managedInput,failedCount],loc);",1)
        self.run_checked("checked-recursive-handler",source,
                         [(1,True,True),(32,True,True)])

    def test_malformed_body_and_dead_failure_returns_refuse_before_emission(self):
        anchor="    let phase be try budget.constructionPhase(owner);"
        mutations={
            "unbound": "fn.definedTarget=0;",
            "import-binding": "fn.definedTarget=createText.index;",
            "wrong-payload": "fn.operands.frozen=false; try words.set(fn.operands,phase,try words.get(fn.instructions,phase,(raised.index-1)*10+2),zero.index); fn.operands.frozen=true;",
            "dead-no-origin": "fn.instructions.frozen=false; try words.set(fn.instructions,phase,(deadRaised.index-1)*10+6,0); fn.instructions.frozen=true;",
            "dead-extra": "fn.instructions.frozen=false; try words.set(fn.instructions,phase,(deadRaised.index-1)*10+8,1); fn.instructions.frozen=true;",
            "fake-result": "fn.instructions.frozen=false; try words.set(fn.instructions,phase,(raised.index-1)*10+5,1); fn.instructions.frozen=true;",
            "bad-normal-ordinal": "let edge be try words.get(fn.instructions,phase,(checkedCall.index-1)*10+8); let at be try words.get(fn.edges,phase,(edge-1)*3+1); fn.arguments.frozen=false; try words.set(fn.arguments,phase,at,-2); fn.arguments.frozen=true;",
            "bad-failure-ordinal": "let edge be try words.get(fn.instructions,phase,(checkedCall.index-1)*10+8); let at be try words.get(fn.edges,phase,edge*3+1); fn.arguments.frozen=false; try words.set(fn.arguments,phase,at,-2); fn.arguments.frozen=true;",
            "legacy-profile": "let legacy be try canonical.verifyAggregates(fn,graph,try budget.verificationPhase(owner));",
        }
        for name,mutation in mutations.items():
            with self.subTest(case=name):
                source=self.source().replace(anchor,anchor+"\n    "+mutation,1)
                generated=self.generator("checked-negative-"+name,source)
                self.assertEqual(generated.returncode,1,generated.stdout[-2500:])
                self.assertTrue(any(x in generated.stdout for x in
                    ("invalid:","roots:","body:")),generated.stdout[-2500:])
                self.assertNotIn(".section",generated.stdout)

    def test_checked_two_managed_normal_results_and_failed_result_are_disjoint(self):
        source=self.source().replace(
            "[carrier,textCarrier,failureCarrier,i64,pred],[carrier,i64]);",
            "[carrier,textCarrier,failureCarrier,i64,pred],[carrier,textCarrier]);",1)
        source=source.replace("[],[carrier,i64,textCarrier]);",
                              "[],[carrier,textCarrier,textCarrier]);",1)
        source=source.replace("let normal be try ab.block(fn,graph,[carrier,i64,textCarrier]);",
                              "let normal be try ab.block(fn,graph,[carrier,textCarrier,textCarrier]);",1)
        source=source.replace("let total be try build.wrapAdd(fn,normal,returnedCount,ownCount,loc);", "")
        source=source.replace("[returnedIdentity,total],loc);", "[returnedIdentity,normalText],loc);",1)
        source=source.replace("[managedInput,baseCount],loc);", "[managedInput,textInput],loc);",1)
        source=source.replace("[managedInput,deadValue],loc);", "[managedInput,textInput],loc);",1)
        self.run_checked("checked-two-managed",source,
            [(0,False,False),(32,False,False),(32,True,False)],dual=True)

    def test_checked_no_value_success_and_typed_failure_have_no_fake_result(self):
        source=self.source().replace(
            "[carrier,textCarrier,failureCarrier,i64,pred],[carrier,i64]);",
            "[carrier,textCarrier,failureCarrier,i64,pred],[]);",1)
        source=source.replace("[],[carrier,i64,textCarrier]);","[],[textCarrier]);",1)
        source=source.replace("let normal be try ab.block(fn,graph,[carrier,i64,textCarrier]);",
                              "let normal be try ab.block(fn,graph,[textCarrier]);",1)
        source=source.replace("    let returnedIdentity be try build.parameter(fn,normal,0);\n","",1)
        source=source.replace("    let returnedCount be try build.parameter(fn,normal,1);\n","",1)
        source=source.replace("let normalText be try build.parameter(fn,normal,2);",
                              "let normalText be try build.parameter(fn,normal,0);",1)
        source=source.replace("let total be try build.wrapAdd(fn,normal,returnedCount,ownCount,loc);","",1)
        source=source.replace("[returnedIdentity,total],loc);","[],loc);",1)
        source=source.replace("[managedInput,baseCount],loc);","[],loc);",1)
        source=source.replace("try ab.returnValues(fn,graph,deadDestination,[managedInput,deadValue],loc);",
                              "try ab.returnValues(fn,graph,deadDestination,[],loc);",1)
        self.run_checked("checked-no-value",source,
            [(0,False,False),(32,False,False),(32,True,False)],arity=0)

    def test_checked_one_scalar_result_and_failure_use_distinct_outcomes(self):
        source=self.source().replace(
            "[carrier,textCarrier,failureCarrier,i64,pred],[carrier,i64]);",
            "[carrier,textCarrier,failureCarrier,i64,pred],[i64]);",1)
        source=source.replace("[],[carrier,i64,textCarrier]);","[],[i64,textCarrier]);",1)
        source=source.replace("let normal be try ab.block(fn,graph,[carrier,i64,textCarrier]);",
                              "let normal be try ab.block(fn,graph,[i64,textCarrier]);",1)
        source=source.replace("    let returnedIdentity be try build.parameter(fn,normal,0);\n","",1)
        source=source.replace("let returnedCount be try build.parameter(fn,normal,1);",
                              "let returnedCount be try build.parameter(fn,normal,0);",1)
        source=source.replace("let normalText be try build.parameter(fn,normal,2);",
                              "let normalText be try build.parameter(fn,normal,1);",1)
        source=source.replace("[returnedIdentity,total],loc);","[total],loc);",1)
        source=source.replace("[managedInput,baseCount],loc);","[baseCount],loc);",1)
        source=source.replace("[managedInput,deadValue],loc);","[deadValue],loc);",1)
        self.run_checked("checked-one-scalar",source,
            [(0,False,False),(32,False,False),(32,True,False)],arity=1)

    def test_missing_native_failure_handoff_or_payload_is_a_terminal_defect(self):
        generated=self.generator("checked-invalid-abi",self.source())
        self.assertEqual((generated.returncode,generated.stderr),(0,""),
                         generated.stdout[-2500:])
        runtime=self.runtime.replace("erist_rt_slots_collect:\n",
            "erist_rt_slots_collect:\n    incq .Lrecursive_gc_calls(%rip)\n",1)
        for label,old,new in (
            ("handoff","leaq .Lrecursive_roots+24(%rip),%rcx","xorl %ecx,%ecx"),
            ("payload","movq %rax,.Lrecursive_inputs+16(%rip)",
                       "movq $0,.Lrecursive_inputs+16(%rip)"),
        ):
            with self.subTest(missing=label):
                caller=self.checked_caller(1,True).replace(old,new,1)
                result=self.run_probe("checked-abi-"+label,
                    generated.stdout+caller+graph.FINISH+unicodeTests.unicode_descriptors(),
                    runtime=runtime,types=False)
                self.assertEqual(result.returncode,1)
                self.assertEqual(result.stdout,b"")
                self.assertIn(b"invalid internal scalar value operation",result.stderr)

    def test_failure_return_cannot_bypass_an_active_file_owner(self):
        source=(ROOT/"tests/fixtures/u2_scoped_owners.eri").read_text()
        source=source.replace("import compiler.u2_scoped_owners as owners;",
            "import compiler.u2_scoped_owners as owners;\nimport compiler.u2_function_contract as body;",1)
        source=source.replace("    let source be try meta.source",
            '    let bodyTarget be try meta.declaration(data,mp,caller,"u2.checked.owner",1,63,0);\n    let source be try meta.source',1)
        source=source.replace("    try contracts.freeze(table);",
            "    let bodyContract be contracts.Contract { version=1; target=bodyTarget; failure=failedSig; };\n"
            "    try contracts.register(table,data,graph,mp,bodyContract);\n"
            "    try contracts.freeze(table);",1)
        source=source.replace("    let fn be try build.create(data,caller,owner,phase);",
            "    let fn be try build.create(data,caller,owner,phase);\n"
            "    try body.bind(fn,graph,table,bodyTarget);",1)
        source=source.replace("    let outerClose be try invoke.emit(fn,graph,consume,pair,[afterValue]);",
            "    let code be try build.integer(fn,afterInner,42,loc);\n"
            "    let payload be try ab.make(fn,graph,afterInner,failure,[code],loc);\n"
            "    let premature be try body.returnFailure(fn,graph,table,afterInner,payload,loc);",1)
        start=source.index("    let report be try owners.verify(")
        end=source.index("    try budget.finishPhase(mutate);",start)
        source=source[:start]+"""
    try check(try rejects(profile,fn,graph,table),"failure return bypassed cleanup");
    let mutate be try budget.constructionPhase(owner);
"""+source[end:]
        source=source.replace("continuation.InvalidBinding,owners.InvalidOwnership,ProbeError {",
                              "continuation.InvalidBinding,owners.InvalidOwnership,body.InvalidBody,ProbeError {",1)
        source=source.replace('else error ProbeError { output("probe:"+error.message);',
            'else error body.InvalidBody { output("body:"+error.message); process.setExitCode(1); }\n'
            'else error ProbeError { output("probe:"+error.message);',1)
        # Reuse the existing owner probe and its scratch reclamation assertion.
        ownerTests.U2ScopedOwnerTests.compile_probe(self,source)

    def test_checked_recursion_retains_complete_ordered_secondary_context(self):
        generated=self.generator("checked-secondary",self.source())
        self.assertEqual((generated.returncode,generated.stderr),(0,""),
                         generated.stdout[-2500:])
        executable=self.directory/"checked-resource-runtime"
        self.assertEqual(build_native(ROOT/"src/resource_value_runtime.eri",
                                     executable,ROOT/"src"),0)
        emitted=subprocess.run([str(executable)],capture_output=True,text=True,
                               timeout=60)
        self.assertEqual((emitted.returncode,emitted.stderr),(0,""))
        runtime=audit_slot_count(emitted.stdout).replace("erist_rt_slots_collect:\n",
            "erist_rt_slots_collect:\n    incq .Lrecursive_gc_calls(%rip)\n",1)
        asm=generated.stdout.replace("    call erist_rt_slots_collect",
            "    movq $0,.Lrecursive_roots+16(%rip)\n    call erist_rt_slots_collect")
        caller=self.checked_caller(64,True)
        begin=caller.index("    call evn_frame")
        end=caller.index("    call erist_rt_failure_clear",begin)+len("    call erist_rt_failure_clear")
        setup=caller[begin:end]
        stores="    movq %rax,.Lrecursive_inputs+16(%rip)\n    movq %rax,.Lrecursive_roots+16(%rip)"
        self.assertEqual(setup.count(stores),1)
        # Reuse real saved-error construction and the production append adapter.
        setup=setup.replace(stores,
            "    movq %rax,%rsi\n    movq .Lrecursive_inputs+16(%rip),%rdi\n"
            "    call erist_rt_failure_append",1)
        additions=""
        for number,name in ((43,"A"),(44,"B")):
            additions+=setup.replace(".Lchecked_saved",".Lchecked_saved_"+name).replace(
                ".Lchecked_message",".Lchecked_secondary_"+name).replace(
                "movl $10,%esi","movl $11,%esi",1).replace(
                "movl $42,%edi","movl $"+str(number)+",%edi",1)+"\n"
        at=caller.index("    movq $64,.Lrecursive_inputs+24(%rip)")
        caller=caller[:at]+additions+caller[at:]
        caller=caller.replace("cmpq $4,%rax","cmpq $6,%rax",1).replace(
            "cmpq $2,%rax","cmpq $4,%rax",1)
        caller=caller.replace("call erist_rt_live_failures\n    cmpq $1,%rax",
                              "call erist_rt_live_failures\n    cmpq $3,%rax",1)
        inspection="    movq .Lrecursive_roots+24(%rip),%r12\n    movq 80(%r12),%r12\n"
        for _ in range(2):
            inspection+="""
    testq %r12,%r12
    je .Lgraph_test_fail
    movq %r12,%rdi
    movl $12,%esi
    call evn_error
    movq %rax,%rdi
    xorl %esi,%esi
    call evn_member
    movq %rax,%rdi
    call evn_output
    movq 88(%r12),%r12
"""
        inspection+="    testq %r12,%r12\n    jne .Lgraph_test_fail\n"
        caller=caller.replace("    movq $0,.Lrecursive_roots+24(%rip)",
                              inspection+"    movq $0,.Lrecursive_roots+24(%rip)",1)
        caller+='\n.section .rodata\n.Lchecked_secondary_A:\n.ascii "secondary-A"\n.Lchecked_secondary_B:\n.ascii "secondary-B"\n'
        executed=self.run_probe("checked-secondary-depth64",
            asm+caller+graph.FINISH+unicodeTests.unicode_descriptors(),
            runtime=runtime,types=False)
        self.assertEqual((executed.returncode,executed.stdout,executed.stderr),
                         (0,"primary-β\nsecondary-A\nsecondary-B\n".encode(),b""))

    def test_owned_and_c_bootstrap_generators_emit_identical_checked_function(self):
        folder=self.directory/"checked-owned-generator"
        folder.mkdir()
        # Isolate profiling annotations from the original compiler sources.
        # Both owned and C generators below use this exact temporary copy.
        shutil.copytree(ROOT/"src/compiler",folder/"compiler")
        traced_emitter=folder/"compiler/u2_function_managed_x86_64.eri"
        traced_code=traced_emitter.read_text(encoding="utf-8")
        phases=(
            ("    let proof be try ssa.verify(plan,routine,graph,table,phase);",
             "ssa-verified"),
            ("    let managedReturn be false;", "signature-admitted"),
            ("    // Snapshot the frozen canonical Function tables before emitting any code.",
             "snapshot"),
            ("    // Build the publication product in two bounded sweeps per canonical block,",
             "publication-build"),
            ("    // Verify the entire immutable publication product at one boundary instead",
             "publication-verify"),
            ("    // Precharge ALL output work. From here only pure string/array operations.",
             "publication-done"),
            ('    output(".section .rodata");', "assembly-begin"),
        )
        for needle,checkpoint in phases:
            self.assertEqual(traced_code.count(needle),1)
            traced_code=traced_code.replace(
                needle,'    output("# U2_NATIVE_TRACE:'+checkpoint+'");\n'+needle,1)
        # Supplemental TEST-ONLY markers identify per-block root-production
        # progress without altering original compiler sources.
        progress_marks=(
            ("    let rowCount be (instructions.count/10)*selected.count;",
             '    output("# U2_NATIVE_TRACE:buffer-start");\n'),
            ("        // Preserve the original linked instruction order;",
             '        output("# U2_NATIVE_TRACE:entry:"+format.integer(block));\n'),
            ("        let terminator be blocks[(block-1)*5+4];",
             '        output("# U2_NATIVE_TRACE:chain:"+format.integer(block));\n'),
            ("            let liveOut be (try words.get(plan.outputs,phase,",
             '            if j == 0 { output("# U2_NATIVE_TRACE:first-suffix:"+format.integer(block)); }\n'),
            ("        block=block+1;\n    }\n    output(\"# U2_NATIVE_TRACE:publication-verify\");\n    // Verify the entire immutable publication product at one boundary instead",
             '        output("# U2_NATIVE_TRACE:block-done:"+format.integer(block));\n'),
        )
        for needle,marker in progress_marks:
            self.assertEqual(traced_code.count(needle),1)
            traced_code=traced_code.replace(needle,marker+needle,1)
        traced_emitter.write_text(traced_code,encoding="utf-8")
        source=folder/"generator.eri"
        # Test-only GAS comment markers make a timed-out generator observable.
        # The independent C generator receives the same annotated source.
        traced_source=self.source()
        checkpoints=(
            ("    let root be try budget.developmentRequest();", "begin"),
            ("    try budget.finishPhase(mp);", "metadata"),
            ("    try ab.complete(fn,graph);", "function"),
            ("    let phase be try budget.constructionPhase(owner);", "native-phase"),
            ("    try native.emitChecked(fn,graph,table,phase,registry,", "native-emit"),
            ("    try budget.finishPhase(phase);", "after-emit"),
        )
        for needle,checkpoint in checkpoints:
            self.assertEqual(traced_source.count(needle),1)
            traced_source=traced_source.replace(
                needle,'    output("# U2_GENERATOR_TRACE:'+checkpoint+'");\n'+needle,1)
        source.write_text(traced_source,encoding="utf-8")
        application=subprocess.run(
            [str(self.frontend),"emit-asm",str(source),"--source-root",str(folder)],
            capture_output=True,text=True,timeout=120)
        self.assertEqual((application.returncode,application.stderr),(0,""),
                         application.stdout[-2500:])
        executable=folder/"resource-runtime"
        self.assertEqual(build_native(ROOT/"src/resource_value_runtime.eri",
                                     executable,ROOT/"src"),0)
        emitted=subprocess.run([str(executable)],capture_output=True,text=True,
                               timeout=60)
        self.assertEqual((emitted.returncode,emitted.stderr),(0,""))
        runtime=audit_slot_count(emitted.stdout)
        # This runs the individual source fixture and code generator on the
        # existing owned runtime; it is not a compiler self-build.
        assembly=folder/"owned-generator.s"
        obj=folder/"owned-generator.o"
        binary=folder/"owned-generator.bin"
        assembly.write_text(runtime+"\n"+application.stdout+
            "\n.text\n.globl _start\n_start:\n"
            "    xorl %ebp,%ebp\n    call erist_entry\n"
            "    jmp .Lgraph_finish\n"+graph.FINISH+
            '\n.section .note.GNU-stack,"",@progbits\n',encoding="utf-8")
        subprocess.run(["as","--64",str(assembly),"-o",str(obj)],
                       check=True,capture_output=True,timeout=20)
        subprocess.run(["ld","-nostdlib","-static","-e","_start",
                        str(obj),"-o",str(binary)],
                       check=True,capture_output=True,timeout=20)
        headers=subprocess.check_output(["readelf","-lW",str(binary)],text=True)
        self.assertNotIn("INTERP",headers)
        self.assertNotIn("DYNAMIC",headers)
        self.assertNotIn("RWE",next(line for line in headers.splitlines()
                                  if "GNU_STACK" in line))
        self.assertEqual(subprocess.check_output(["nm","-u",str(binary)],
                                                text=True).strip(),"")
        # The established 20-second small-application helper is not the
        # selected source-generator gate. Use U2's existing 120-second
        # qualification watchdog, without relaxing memory/work budgets.
        started=time.monotonic()
        try:
            owned=capture_traced_owned_generator(
                [str(binary)],env={"PATH":"/unavailable"},timeout=120)
        except subprocess.TimeoutExpired as error:
            partial=error.stdout or b""
            markers=[line.decode("utf-8",errors="replace")
                     for line in partial.splitlines()
                     if b"U2_GENERATOR_TRACE:" in line or
                        b"U2_NATIVE_TRACE:" in line]
            print("U2_GENERATOR_TIMEOUT_PARTIAL_BYTES="+str(len(partial)),
                  "U2_GENERATOR_PHASES="+repr(markers),flush=True)
            raise
        print("U2_CHECKED_OWNED_GENERATOR_SECONDS="+str(time.monotonic()-started),
              flush=True)
        self.assertEqual((owned.returncode,owned.stderr),(0,b""),
                         owned.stdout[-2000:].decode(errors="replace"))
        c_folder=self.directory/"checked-c-generator"
        c_folder.mkdir()
        (c_folder/"compiler").symlink_to(folder/"compiler",target_is_directory=True)
        c_source=c_folder/"generator.eri"
        c_source.write_text(traced_source,encoding="utf-8")
        c_generator=c_folder/"generator"
        self.assertEqual(build_native(c_source,c_generator,c_folder),0)
        bootstrap=subprocess.run([str(c_generator)],capture_output=True,
                                 text=True,timeout=150)
        self.assertEqual((bootstrap.returncode,bootstrap.stderr),(0,""),
                         bootstrap.stdout[-2000:])
        self.assertEqual(owned.stdout,bootstrap.stdout.encode())
        # Execute the identical generated code with the independent failure
        # payload oracle after relinquishing the external ingress root.
        asm=owned.stdout.decode().replace("    call erist_rt_slots_collect",
            "    movq $0,.Lrecursive_roots+16(%rip)\n    call erist_rt_slots_collect")
        instrumented=runtime.replace("erist_rt_slots_collect:\n",
            "erist_rt_slots_collect:\n    incq .Lrecursive_gc_calls(%rip)\n",1)
        executed=self.run_probe("checked-from-owned-generator-depth32",
            asm+self.checked_caller(32,True)+graph.FINISH+
            unicodeTests.unicode_descriptors(),runtime=instrumented,types=False)
        self.assertEqual((executed.returncode,executed.stdout,executed.stderr),
                         (0,"primary-β\n".encode(),b""))

    def test_whole_publication_table_refuses_corruption_and_releases_on_refusal(self):
        source=self.source()
        helper="""
function publicationRejected(plan identity ssa.Plan,fn identity build.Function,
    graph identity aggregate.Registry,table identity contracts.Registry,
    phase identity budget.Phase,ids,entries,before,after)
    returns Bool fails budget.LimitError,canonical.InvalidIR {
    let proof be ssa.verifyPublications(plan,fn,graph,table,phase,ids,entries,before,after)
        else error ssa.InvalidLiveness { return true; }
        else error budget.LimitError { fail error; }
        else error canonical.InvalidIR { fail error; };
    return false;
}
function publicationRefused(plan identity ssa.Plan,fn identity build.Function,
    graph identity aggregate.Registry,table identity contracts.Registry,
    phase identity budget.Phase,ids,entries,before,after)
    returns Bool fails canonical.InvalidIR,ssa.InvalidLiveness {
    let proof be ssa.verifyPublications(plan,fn,graph,table,phase,ids,entries,before,after)
        else error budget.LimitError { return error.category == "resource-limit"; }
        else error ssa.InvalidLiveness { fail error; }
        else error canonical.InvalidIR { fail error; };
    return false;
}
"""
        source=source.replace("function run()",helper+"function run()",1)
        original="""    try native.emitChecked(fn,graph,table,phase,registry,
        [carrier,textCarrier],[identityType,managed.text(registry)],true,92);"""
        body="""
    let baselineLive be owner.live;
    let plan be try roots.create(fn,graph,table,phase,registry,
        [carrier,textCarrier],[identityType,managed.text(registry)]);
    let ids be []; let entries be []; let before be []; let after be [];
    let r be 0;
    while r < plan.values.length/4 {
        ids.add(try words.get(plan.values,phase,r*4)); r=r+1;
    }
    let b be 1;
    while b <= fn.blocks.length/5 {
        r=0;
        while r < ids.count {
            let v be build.ValueId { owner=fn.key; index=ids[r]; };
            let target be build.BlockId { owner=fn.key; index=b; };
            let flag be 0; if try ssa.liveEntry(plan,fn,phase,target,v) { flag=1; }
            entries.add(flag); r=r+1;
        }
        b=b+1;
    }
    let inst be 1;
    while inst <= fn.instructions.length/10 {
        r=0;
        while r < ids.count {
            let v be build.ValueId { owner=fn.key; index=ids[r]; };
            let at be build.InstId { owner=fn.key; index=inst; };
            let pre be 0; let post be 0;
            if try ssa.liveBefore(plan,fn,phase,at,v) { pre=1; }
            if try ssa.liveAfter(plan,fn,phase,at,v) { post=1; }
            before.add(pre); after.add(post); r=r+1;
        }
        inst=inst+1;
    }
    let positive be try ssa.verifyPublications(plan,fn,graph,table,phase,ids,entries,before,after);
    try check(positive > 0,"empty whole publication proof");
    let stable be owner.live;
    let saved be ids[0]; ids[0]=ids[1];
    try check(try publicationRejected(plan,fn,graph,table,phase,ids,entries,before,after),"duplicate root ID accepted");
    ids[0]=0;
    try check(try publicationRejected(plan,fn,graph,table,phase,ids,entries,before,after),"foreign root ID accepted");
    ids[0]=saved;
    let missing be 0;
    while before[missing] == 0 { missing=missing+1; }
    before[missing]=0;
    try check(try publicationRejected(plan,fn,graph,table,phase,ids,entries,before,after),"missing root accepted");
    before[missing]=1;
    let deadBit be 0;
    while after[deadBit] == 1 { deadBit=deadBit+1; }
    after[deadBit]=1;
    try check(try publicationRejected(plan,fn,graph,table,phase,ids,entries,before,after),"dead root accepted");
    after[deadBit]=0;
    let last be entries.count-1; let oldEntry be entries[last];
    entries[last]=1-oldEntry;
    try check(try publicationRejected(plan,fn,graph,table,phase,ids,entries,before,after),"dead-block entry corruption accepted");
    entries[last]=oldEntry;
    let oldFlag be before[0]; before[0]=2;
    try check(try publicationRejected(plan,fn,graph,table,phase,ids,entries,before,after),"non-binary flag accepted");
    before[0]=oldFlag;
    let oldInput be try words.get(plan.inputs,phase,0);
    plan.inputs.frozen=false; try words.set(plan.inputs,phase,0,1-oldInput); plan.inputs.frozen=true;
    try check(try publicationRejected(plan,fn,graph,table,phase,ids,entries,before,after),"forged liveness backing accepted");
    plan.inputs.frozen=false; try words.set(plan.inputs,phase,0,oldInput); plan.inputs.frozen=true;
    plan.revision=fn.revision+1;
    try check(try publicationRejected(plan,fn,graph,table,phase,ids,entries,before,after),"stale plan accepted");
    plan.revision=fn.revision;
    positive=try ssa.verifyPublications(plan,fn,graph,table,phase,ids,entries,before,after);
    after.add(0);
    try check(try publicationRejected(plan,fn,graph,table,phase,ids,entries,before,after),"extra publication row accepted");
    try check(owner.live == stable and owner.pending == 0,"publication rejection leaked backing");
    phase.limit=phase.used+1;
    try check(try publicationRefused(plan,fn,graph,table,phase,ids,entries,before,after),"work refusal was not enforced");
    try ssa.close(plan);
    try check(owner.live == baselineLive and owner.pending == 0,"work refusal leaked plan backing");
    output("whole-publications:ok");
"""
        self.assertEqual(source.count(original),1)
        source=source.replace(original,body,1)
        generated=self.generator("whole-publication-negatives",source)
        self.assertEqual((generated.returncode,generated.stderr),(0,""),generated.stdout[-2500:])
        self.assertEqual(generated.stdout,"whole-publications:ok\n")
