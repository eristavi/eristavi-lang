"""Closed checked native groups: original UIR, mutual frames and exact roots."""
from pathlib import Path
import platform
import time
import re
import json
import subprocess
import unittest

from compiler.erist.cli import build_native, compile_entry
from compiler.erist.runtime_ext import Interpreter
import test_freestanding_graph_values as graph
import test_u2_function_managed_native as managedTests
import test_u2_function_checked_native as checkedTests
import test_u2_text_unicode17 as unicodeTests
from test_freestanding_text_lifetimes import audit_slot_count

ROOT=Path(__file__).resolve().parents[1]


@unittest.skipUnless(platform.system()=="Linux" and
                     platform.machine().lower() in ("x86_64","amd64"),
                     "owned native checked group requires Linux x86-64")
class U2FunctionCheckedGroupTests(unittest.TestCase):
    setUpClass=classmethod(graph.FreestandingGraphValueTests.setUpClass.__func__)
    run_probe=graph.FreestandingGraphValueTests.run_probe
    generator=managedTests.U2FunctionManagedNativeTests.generator
    recursive_caller=managedTests.U2FunctionManagedNativeTests.recursive_caller
    checked_caller=checkedTests.U2FunctionCheckedNativeTests.checked_caller
    run_checked=checkedTests.U2FunctionCheckedNativeTests.run_checked

    def source(self):
        return (ROOT/"tests/fixtures/u2_function_checked_mutual.eri").read_text()

    def test_mutual_checked_frames_gc_and_independent_source_outcomes(self):
        observed=self.run_checked("checked-mutual",self.source(),
            [(depth,failed,False) for depth in (0,1,5,32,64)
             for failed in (False,True)])
        reference=ROOT/"tests/fixtures/u2_function_checked_mutual_reference.eri"
        module=compile_entry(reference,reference.parent)
        stage0=[]
        Interpreter(output=stage0.append,module_id=module.module_id,
                    imported_modules=module.imports).run(module.program)
        binary=self.directory/"mutual-source-reference"
        self.assertEqual(build_native(reference,binary,reference.parent),0)
        old=subprocess.run([str(binary)],capture_output=True,timeout=30)
        self.assertEqual((old.returncode,old.stderr),(0,b""))
        self.assertEqual(observed,old.stdout)
        self.assertEqual(observed,("\n".join(stage0)+"\n").encode())

    def test_different_member_recovers_failure_into_normal_parent_result(self):
        source=self.source().replace(
            "let propagated be try body.returnFailure(fn,graph,table,failed,failedResult,loc);",
            """if member == 1 {
        try ab.returnValues(fn,graph,failed,[managedInput,failedCount],loc);
    } else {
        let propagated be try body.returnFailure(fn,graph,table,failed,failedResult,loc);
    }""",1)
        self.run_checked("checked-mutual-handler",source,
            [(1,True,False),(2,True,True),(32,True,True)])

    def test_two_managed_results_cross_member_handoff(self):
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
        self.run_checked("checked-mutual-two-managed",source,
            [(0,False,False),(1,False,False),(32,False,False),(32,True,False)],dual=True)

    def test_mutual_frames_preserve_primary_and_ordered_secondary_context(self):
        checkedTests.U2FunctionCheckedNativeTests.test_checked_recursion_retains_complete_ordered_secondary_context(self)

    def test_missing_sibling_handoff_roots_are_terminal_defects(self):
        generated=self.generator("mutual-missing-handoff",self.source())
        self.assertEqual((generated.returncode,generated.stderr),(0,""),generated.stdout[-2500:])
        runtime=self.runtime.replace("erist_rt_slots_collect:\n",
            "erist_rt_slots_collect:\n    incq .Lrecursive_gc_calls(%rip)\n",1)
        for name,register in (("normal","%esi"),("failure","%ecx")):
            bad=generated.stdout.replace("    call erist_u2_rooted_function_93",
                f"    xorl {register},{register}\n    call erist_u2_rooted_function_93",1)
            self.assertNotEqual(bad,generated.stdout)
            result=self.run_probe("mutual-bad-handoff-"+name,
                bad+self.checked_caller(1,True)+graph.FINISH+unicodeTests.unicode_descriptors(),
                runtime=runtime,types=False)
            self.assertEqual(result.returncode,1)
            self.assertEqual(result.stdout,b"")
            self.assertIn(b"invalid internal scalar value operation",result.stderr)

    def test_distinct_normal_signatures_and_result_positions(self):
        source=self.source().replace("    let otherTarget be", """    let otherSignature be try sig.signature(data,graph,mp,
        [carrier,textCarrier,failureCarrier,i64,pred],[i64,carrier]);
    let otherCarry be try sig.signature(data,graph,mp,[],[i64,carrier,textCarrier]);
    let otherTarget be""",1)
        source=source.replace('meta.declaration(data,mp,signature,"u2.mutual.other"',
                              'meta.declaration(data,mp,otherSignature,"u2.mutual.other"',1)
        source=source.replace("    let fn be try build.create(data,signature,owner,cp);", """    let selectedSignature be signature;
    if member == 1 { selectedSignature=otherSignature; }
    let fn be try build.create(data,selectedSignature,owner,cp);""",1)
        source=source.replace("    let normal be try ab.block(fn,graph,[carrier,i64,textCarrier]);", """    let normalTypes be [carrier,i64,textCarrier];
    let selectedCarry be normalCarry;
    let identityIndex be 0; let countIndex be 1;
    if member == 0 {
        normalTypes=[i64,carrier,textCarrier]; selectedCarry=otherCarry;
        identityIndex=1; countIndex=0;
    }
    let normal be try ab.block(fn,graph,normalTypes);""",1)
        source=source.replace("build.parameter(fn,normal,0)","build.parameter(fn,normal,identityIndex)",1)
        source=source.replace("build.parameter(fn,normal,1)","build.parameter(fn,normal,countIndex)",1)
        source=source.replace("normalCarry,failedCarry,loc);", "selectedCarry,failedCarry,loc);",1)
        for block,values in (("normal","returnedIdentity,total"),
                             ("successfulBase","managedInput,baseCount"),
                             ("deadDestination","managedInput,deadValue")):
            a,b=values.split(",")
            original=f"try ab.returnValues(fn,graph,{block},[{values}],loc);"
            replacement=f"""let results_{block} be [{values}];
    if member == 1 {{ results_{block}=[{b},{a}]; }}
    try ab.returnValues(fn,graph,{block},results_{block},loc);"""
            self.assertIn(original,source)
            source=source.replace(original,replacement,1)
        self.run_checked("checked-distinct-signatures",source,
            [(1,False,False),(5,False,False),(32,False,False),(32,True,False)])

    def test_mutual_native_frame_stack_bound_and_reclamation(self):
        generated=self.generator("mutual-stack",self.source())
        self.assertEqual((generated.returncode,generated.stderr),(0,""),generated.stdout[-2500:])
        asm=generated.stdout
        # Test-only watermark at the actual generated frame bottom. No calls,
        # extra stack bytes or production instrumentation are introduced.
        pattern=r"(erist_u2_rooted_function_(92|93):\n    pushq %rbx\n    subq \$[0-9]+,%rsp\n)"
        def instrument(match):
            return match[1]+f"""    movq .Lgroup_stack_top(%rip),%rax
    subq %rsp,%rax
    cmpq .Lgroup_stack_peak(%rip),%rax
    jbe .Lgroup_stack_done_{match[2]}
    movq %rax,.Lgroup_stack_peak(%rip)
.Lgroup_stack_done_{match[2]}:
"""
        asm,count=re.subn(pattern,instrument,asm)
        self.assertEqual(count,2)
        asm=asm.replace("    call erist_rt_slots_collect",
            "    movq $0,.Lrecursive_roots+16(%rip)\n    call erist_rt_slots_collect")
        runtime=self.runtime.replace("erist_rt_slots_collect:\n",
            "erist_rt_slots_collect:\n    incq .Lrecursive_gc_calls(%rip)\n",1)
        samples=[]
        # Admission caps give an independent upper bound, not a decoded copy
        # of the emitted frame size. This measures Function frames, not RSS
        # or transient collector/adapter stack usage.
        bound_per_frame=((8*256+8*64+320+15)//16)*16+16
        for depth in (0,1,5,32,64):
            caller=self.checked_caller(depth,False)
            caller=caller.replace("    call erist_u2_rooted_function_92",
                "    movq %rsp,.Lgroup_stack_top(%rip)\n    call erist_u2_rooted_function_92",1)
            caller=caller.replace("    jmp .Lgraph_finish", """    movq .Lgroup_stack_peak(%rip),%rdi
    call evn_int
    movq %rax,%rdi
    call evn_output
    jmp .Lgraph_finish""",1)
            caller+="\n.bss\n.Lgroup_stack_top:\n.zero 8\n.Lgroup_stack_peak:\n.zero 8\n"
            result=self.run_probe("mutual-stack-"+str(depth),
                asm+caller+graph.FINISH+unicodeTests.unicode_descriptors(),
                runtime=runtime,types=False)
            self.assertEqual((result.returncode,result.stderr),(0,b""))
            measured=int(result.stdout.strip())
            self.assertGreater(measured,0)
            self.assertLessEqual(measured,(depth+1)*bound_per_frame)
            samples.append({"depth":depth,"function_stack_bytes":measured})
        self.assertEqual([x["function_stack_bytes"] for x in samples],
                         [(x["depth"]+1)*samples[0]["function_stack_bytes"] for x in samples])
        print("U2_MUTUAL_STACK="+json.dumps(samples),flush=True)

    def test_preflight_work_and_capacity_refusal_release_owned_plans(self):
        original="""    try native.emitCheckedGroup(routines,[92,93],graph,table,registry,
        [carrier,textCarrier],[identityType,managed.text(registry)],true);"""
        cleanup="""    member=0;
    while member < routines.count {
        try build.close(routines[member]); try budget.close(owners[member]);
        member=member+1;
    }
    try contracts.close(table); try managed.close(registry);
    try aggregate.close(graph); try meta.close(data);
    try budget.close(shared); try budget.close(root);"""
        for name,limit in (("work","lastOwner.workLimit=lastOwner.work+1000;"),
                           ("capacity","lastOwner.limit=lastOwner.live+2000;")):
            source=self.source()
            self.assertIn(original,source)
            replacement="""    let firstOwner identity budget.Owner be owners[0];
    let lastOwner identity budget.Owner be owners[1];
    let firstLive be firstOwner.live; let lastLive be lastOwner.live;
    LIMIT
    native.emitCheckedGroup(routines,[92,93],graph,table,registry,
        [carrier,textCarrier],[identityType,managed.text(registry)],true)
    else error budget.LimitError {
        try check(error.category == "resource-limit","wrong refusal category");
        try check(firstOwner.live == firstLive and lastOwner.live == lastLive and
            firstOwner.pending == 0 and lastOwner.pending == 0 and
            firstOwner.pendingTraffic == 0 and lastOwner.pendingTraffic == 0,
            "group preflight refusal leaked owned plan backing");
        CLEANUP
        output("group-refusal-reclaimed:ok"); return;
    } else error { fail ProbeError { message=error.message; }; };
    fail ProbeError { message="preflight budget was not enforced"; };""".replace("LIMIT",limit).replace("CLEANUP",cleanup)
            source=source.replace(original,replacement,1)
            generated=self.generator("group-budget-"+name,source)
            self.assertEqual((generated.returncode,generated.stderr),(0,""),generated.stdout[-2500:])
            self.assertEqual(generated.stdout,"group-refusal-reclaimed:ok\n")

    def test_owned_and_c_generators_agree_on_direct_group(self):
        folder=self.directory/"direct-owned-group"
        folder.mkdir()
        (folder/"compiler").symlink_to(ROOT/"src/compiler",target_is_directory=True)
        source=folder/"generator.eri"
        source.write_text((ROOT/"tests/fixtures/u2_function_checked_group_direct.eri").read_text())
        emitted=subprocess.run([str(self.frontend),"emit-asm",str(source),
                                "--source-root",str(folder)],
                               capture_output=True,text=True,timeout=120)
        self.assertEqual((emitted.returncode,emitted.stderr),(0,""),emitted.stdout[-2500:])
        runtime_generator=folder/"resource-runtime"
        self.assertEqual(build_native(ROOT/"src/resource_value_runtime.eri",
                                     runtime_generator,ROOT/"src"),0)
        runtime=subprocess.run([str(runtime_generator)],capture_output=True,
                               text=True,timeout=60)
        self.assertEqual((runtime.returncode,runtime.stderr),(0,""))
        assembly=folder/"generator.s"
        obj=folder/"generator.o"
        binary=folder/"generator.bin"
        assembly.write_text(audit_slot_count(runtime.stdout)+emitted.stdout+
            "\n.text\n.globl _start\n_start:\n    xorl %ebp,%ebp\n"
            "    call erist_entry\n    jmp .Lgraph_finish\n"+graph.FINISH+
            '\n.section .note.GNU-stack,"",@progbits\n')
        subprocess.run(["as","--64",str(assembly),"-o",str(obj)],
                       check=True,capture_output=True,timeout=20)
        subprocess.run(["ld","-nostdlib","-static","-e","_start",
                        str(obj),"-o",str(binary)],check=True,capture_output=True,timeout=20)
        headers=subprocess.check_output(["readelf","-lW",str(binary)],text=True)
        self.assertNotIn("INTERP",headers)
        self.assertNotIn("DYNAMIC",headers)
        self.assertNotIn("RWE",next(x for x in headers.splitlines() if "GNU_STACK" in x))
        self.assertEqual(subprocess.check_output(["nm","-u",str(binary)],text=True).strip(),"")
        begun=time.monotonic()
        owned=subprocess.run([str(binary)],env={"PATH":"/unavailable"},
                             capture_output=True,timeout=120)
        print("U2_DIRECT_GROUP_OWNED_GENERATOR_SECONDS="+
              format(time.monotonic()-begun,".3f"),flush=True)
        self.assertEqual((owned.returncode,owned.stderr),(0,b""),owned.stdout[-2500:])
        bootstrap=self.generator("direct-c-group",source.read_text())
        self.assertEqual((bootstrap.returncode,bootstrap.stderr),(0,""),bootstrap.stdout[-2500:])
        self.assertEqual(owned.stdout,bootstrap.stdout.encode())
        self.assertIn(b"call erist_u2_rooted_function_93",owned.stdout)
        runtime=self.runtime.replace("erist_rt_slots_collect:\n",
            "erist_rt_slots_collect:\n    incq .Lrecursive_gc_calls(%rip)\n",1)
        for failed in (False,True):
            caller=self.checked_caller(0,failed).replace(
                "cmpq $2,.Lrecursive_gc_calls","cmpq $4,.Lrecursive_gc_calls",1)
            result=self.run_probe("direct-owned-group-"+str(failed),
                owned.stdout.decode()+caller+graph.FINISH+unicodeTests.unicode_descriptors(),
                runtime=runtime,types=False)
            self.assertEqual((result.returncode,result.stdout,result.stderr),
                             (0,"primary-β\n".encode() if failed else b"",b""))

    def test_closed_group_refusals_precede_all_assembly(self):
        anchor="    try native.emitCheckedGroup(routines,[92,93],graph,table,registry,"
        mutations={
            "missing-body": (anchor,"    let selected be []; selected.add(routines[0]);\n"+anchor.replace("routines,[92,93]","selected,[92]")),
            "duplicate-target": (anchor,"    routines[1]=routines[0];\n"+anchor),
            "duplicate-label": (anchor,anchor.replace("[92,93]","[92,92]")),
            "zero-label": (anchor,anchor.replace("[92,93]","[92,0]")),
            "large-label": (anchor,anchor.replace("[92,93]","[92,2147483648]")),
            "label-arity": (anchor,anchor.replace("[92,93]","[92]")),
            "empty": (anchor,"    let selected be []; if false { selected.add(routines[0]); }\n"+anchor.replace("routines,[92,93]","selected,[]")),
            "foreign-metadata": (anchor,"""    let foreignPhase be try budget.constructionPhase(shared);
    let foreignData be try meta.create(shared,foreignPhase);
    let foreignBody identity build.Function be routines[1];
    foreignBody.metadata=foreignData;
"""+anchor),
            "missing-managed-type": ("[carrier,textCarrier],[identityType,managed.text(registry)],true);",
                                     "[carrier],[identityType],true);"),
            "foreign-binding": ("try ab.complete(fn,graph);", "try ab.complete(fn,graph);\n    if member == 1 { fn.definedTarget=createText.index; }"),
            "wrong-signature": ("try ab.complete(fn,graph);", "try ab.complete(fn,graph);\n    if member == 1 { fn.signature=createSig; }"),
            "dead-no-origin": ("try ab.complete(fn,graph);", """try ab.complete(fn,graph);
    if member == 1 {
        fn.instructions.frozen=false;
        try words.set(fn.instructions,cp,(deadRaised.index-1)*10+6,0);
        fn.instructions.frozen=true;
    }"""),
        }
        for name,(before,after) in mutations.items():
            with self.subTest(case=name):
                source=self.source().replace(before,after,1)
                if name == "dead-no-origin":
                    source=source.replace("let calleeContract be otherContract;",
                                          "let calleeContract be selfContract;",1)
                generated=self.generator("group-refusal-"+name,source)
                self.assertEqual(generated.returncode,1,generated.stdout[-2500:])
                self.assertTrue(any(x in generated.stdout for x in
                    ("unsupported:","invalid:","roots:","body:")),generated.stdout[-2500:])
                self.assertNotIn(".section",generated.stdout)
