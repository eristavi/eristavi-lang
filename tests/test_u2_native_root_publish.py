"""Focused U2 canonical verified-root -> owned x86-64 GC publication proof."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest
import platform

from compiler.erist.cli import build_native
from test_freestanding_graph_values import FINISH, descriptors
from test_freestanding_text_lifetimes import (
    FreestandingTextLifetimeTests, audit_slot_count,
)

ROOT=Path(__file__).resolve().parents[1]


@unittest.skipUnless(
    platform.system() == "Linux"
    and platform.machine().lower() in ("x86_64", "amd64"),
    "opt-in owned machine-root test requires Linux x86-64",
)
class U2NativeRootPublishTests(unittest.TestCase):
    def test_generated_scoped_bind_publish_release_survives_forced_gc(self):
        for program in ("as", "ld", "nm", "readelf"):
            if not shutil.which(program):
                self.skipTest(program+" unavailable")
        with tempfile.TemporaryDirectory() as temp:
            directory=Path(temp)
            (directory/"compiler").symlink_to(
                ROOT/"src/compiler", target_is_directory=True)
            source=(ROOT/"tests/fixtures/u2_scoped_owners.eri").read_text()
            imports="import compiler.u2_scoped_owners as owners;"
            self.assertIn(imports,source)
            source=source.replace(
                imports, imports+"\n"
                "import compiler.u2_root_map as rootMap;\n"
                "import compiler.u2_native_root_x86_64 as nativeRoot;\n"
                "import compiler.u2_native_slots_x86_64 as machineSlots;",1)
            insertion=(
                "let mutate be try budget.constructionPhase(owner); "
                "let revision be fn.revision;"
            )
            self.assertIn(insertion,source)
            source=source.replace(
                insertion, insertion+"\n"
                "    let map be try rootMap.create(fn,graph,mutate);\n"
                "    let baseline be owner.live;\n"
                "    let placement be try machineSlots.create(map,fn,graph,mutate);\n"
                "    let slots be try machineSlots.verify(placement,map,fn,graph,mutate);\n"
                "    try check(slots.roots == 5 and slots.rootBytes == 40 and slots.scopeOffset == 40 and slots.frameBytes == 48,\"native slot frame bounds\");\n"
                "    let saved be try words.get(placement.records,mutate,1);\n"
                "    placement.records.frozen=false; try words.set(placement.records,mutate,1,saved+1); placement.records.frozen=true;\n"
                "    try check(try slotRejected(placement,map,fn,graph,mutate),\"misaligned native root accepted\");\n"
                "    placement.records.frozen=false; try words.set(placement.records,mutate,1,saved); placement.records.frozen=true;\n"
                "    let overlap be try words.get(placement.records,mutate,4);\n"
                "    placement.records.frozen=false; try words.set(placement.records,mutate,4,saved); placement.records.frozen=true;\n"
                "    try check(try slotRejected(placement,map,fn,graph,mutate),\"overlapping native roots accepted\");\n"
                "    placement.records.frozen=false; try words.set(placement.records,mutate,4,overlap); placement.records.frozen=true;\n"
                "    let rootClass be try words.get(placement.records,mutate,2);\n"
                "    placement.records.frozen=false; try words.set(placement.records,mutate,2,4); placement.records.frozen=true;\n"
                "    try check(try slotRejected(placement,map,fn,graph,mutate),\"wrong native root class accepted\");\n"
                "    placement.records.frozen=false; try words.set(placement.records,mutate,2,rootClass); placement.records.frozen=true;\n"
                "    let first be try words.get(placement.records,mutate,0);\n"
                "    placement.records.frozen=false; try words.set(placement.records,mutate,0,first+1); placement.records.frozen=true;\n"
                "    try check(try slotRejected(placement,map,fn,graph,mutate),\"forged instruction placement accepted\");\n"
                "    placement.records.frozen=false; try words.set(placement.records,mutate,0,first); placement.records.frozen=true;\n"
                "    let originalLength be placement.records.length; placement.records.length=originalLength-3;\n"
                "    try check(try slotRejected(placement,map,fn,graph,mutate),\"missing native root accepted\");\n"
                "    placement.records.length=originalLength;\n"
                "    placement.revision=fn.revision+1;\n"
                "    try check(try slotRejected(placement,map,fn,graph,mutate),\"stale slot revision accepted\");\n"
                "    placement.revision=fn.revision;\n"
                "    let foreign be try rootMap.create(fn,graph,mutate);\n"
                "    try check(try slotRejected(placement,foreign,fn,graph,mutate),\"foreign root map accepted\");\n"
                "    try rootMap.close(foreign);\n"
                "    slots=try machineSlots.verify(placement,map,fn,graph,mutate);\n"
                "    try nativeRoot.emitWithSlots(placement,map,fn,graph,mutate,7);\n"
                "    try machineSlots.close(placement);\n"
                "    try check(try slotRejected(placement,map,fn,graph,mutate),\"closed native root slots accepted\");\n"
                "    try check(owner.live == baseline,\"slot-plan backing not released\");\n"
                "    try rootMap.close(map);",1)
            helper=(
                "function slotRejected(plan identity machineSlots.Plan,"
                "map identity rootMap.Map,fn identity build.Function,"
                "graph identity aggregate.Registry,phase identity budget.Phase)"
                " returns Bool fails budget.LimitError,rootMap.InvalidRoots {\\n"
                "    let proof be machineSlots.verify(plan,map,fn,graph,phase)"
                " else error machineSlots.InvalidSlots { return true; };\\n"
                "    return false;\\n"
                "}\\n"
            )
            self.assertIn("function run() fails",source)
            source=source.replace("function run() fails",helper+"function run() fails",1)
            marker="continuation.InvalidBinding,owners.InvalidOwnership,ProbeError {"
            self.assertIn(marker,source)
            source=source.replace(
                marker,"continuation.InvalidBinding,owners.InvalidOwnership,"
                "rootMap.InvalidRoots,machineSlots.InvalidSlots,nativeRoot.Unsupported,ProbeError {",1)
            errors='else error ProbeError { output("probe:"+error.message);'
            self.assertIn(errors,source)
            source=source.replace(
                errors,
                'else error rootMap.InvalidRoots { output("roots:"+error.message); process.setExitCode(1); }\n'
                'else error machineSlots.InvalidSlots { output("slots:"+error.message); process.setExitCode(1); }\\n'
                'else error nativeRoot.Unsupported { output("native:"+error.message); process.setExitCode(1); }\n'
                +errors,1)
            closing='output("u2-scoped-owners:ok");'
            self.assertIn(closing,source)
            source=source.replace(closing,"",1)
            file=directory/"root_emitter.eri"
            file.write_text(source,encoding="utf-8")
            generator=directory/"root_emitter"
            self.assertEqual(build_native(file,generator,directory),0)
            result=subprocess.run(
                [str(generator)],capture_output=True,text=True,timeout=120)
            self.assertEqual(
                (result.returncode,result.stderr),(0,""),result.stdout[-1200:])
            emission=result.stdout
            matches=re.findall(
                r"^\.globl erist_u2_publish_7_(\d+)$",emission,re.M)
            self.assertEqual(len(matches),5)
            self.assertEqual(len(set(matches)),5)
            self.assertEqual(
                len(re.findall(r"^    \.byte 5$",emission,re.M)),5)
            self.assertIn(".globl erist_u2_bind_7",emission)
            self.assertIn("    movq $0,32(%rsi)",emission)
            publish=re.findall(
                r"^erist_u2_publish_7_(\\d+):\\n    movq %rsi,(\\d+)\\(%rdi\\)\\n    ret$",
                emission,re.M)
            release=re.findall(
                r"^erist_u2_release_7_(\\d+):\\n    movq \\$0,(\\d+)\\(%rdi\\)\\n    ret$",
                emission,re.M)
            expected=list(zip(matches,[str(i*8) for i in range(5)]))
            self.assertEqual(publish,expected)
            self.assertEqual(release,expected)
            self.assertEqual(
                re.findall(r"^    movq \\$0,(\\d+)\\(%rsi\\)$",emission,re.M),
                [str(i*8) for i in range(5)])
            first=matches[0]
            native=(ROOT/"tests/fixtures/u2_root_publish_native.s").read_text()
            self.assertEqual(native.count("@INSTRUCTION@"),2)
            native=native.replace("@INSTRUCTION@",first)
            runner=directory/"graph_runtime"
            self.assertEqual(build_native(
                ROOT/"src/graph_value_runtime.eri",runner,ROOT/"src"),0)
            generated=subprocess.run(
                [str(runner)],capture_output=True,text=True,timeout=60)
            self.assertEqual((generated.returncode,generated.stderr),(0,""))
            runtime=audit_slot_count(generated.stdout)
            marker="erist_rt_text_collect:\n"
            self.assertEqual(runtime.count(marker),1)
            runtime=runtime.replace(
                marker,
                marker+"    incq erist_rt_u2_generated_gc_visits(%rip)\n",1)
            runtime+=(
                "\n.bss\n.p2align 3\n"
                ".globl erist_rt_u2_generated_gc_visits\n"
                "erist_rt_u2_generated_gc_visits:\n.quad 0\n")
            execution=FreestandingTextLifetimeTests._link_run(
                self,directory,"u2-verified-native-root",runtime,
                descriptors()+emission+native+FINISH)
            self.assertEqual(
                (execution.returncode,execution.stdout,execution.stderr),
                (0,b"u2-emitted-root\n",b""))
            # The same emitted frame must retain a second independent
            # checked-root slot after the first record is released.
            # No second compiler build or runtime generator is required.
            second=matches[1]
            original=(
                "    call erist_u2_publish_7_"+first+"\n"
                "    call erist_rt_failure_clear\n")
            replacement=(
                "    call erist_u2_publish_7_"+first+"\n"
                "    call evn_saved\n"
                "    movq %r15,%rdi\n"
                "    movq %rax,%rsi\n"
                "    call erist_u2_publish_7_"+second+"\n"
                "    call erist_rt_failure_clear\n")
            self.assertIn(original,native)
            multi=native.replace(original,replacement,1)
            self.assertIn("    cmpq $1,%rax\n    jne .Lgraph_test_fail\n",multi)
            multi=multi.replace(
                "    cmpq $1,%rax\n    jne .Lgraph_test_fail\n",
                "    cmpq $2,%rax\n    jne .Lgraph_test_fail\n",1)
            before=(
                "    cmpq $0,(%r15)\n"
                "    jne .Lgraph_test_fail\n"
                "    call evn_void\n")
            after=(
                "    cmpq $0,(%r15)\n"
                "    jne .Lgraph_test_fail\n"
                "    xorl %edi,%edi\n"
                "    call erist_rt_slots_collect\n"
                "    call erist_rt_text_collect\n"
                "    call erist_rt_live_failures\n"
                "    cmpq $1,%rax\n"
                "    jne .Lgraph_test_fail\n"
                "    movq 8(%r15),%rdi\n"
                "    movl $12,%esi\n"
                "    call evn_error\n"
                "    movq %rax,%rdi\n"
                "    xorl %esi,%esi\n"
                "    call evn_member\n"
                "    movq %rax,%rdi\n"
                "    call evn_output\n"
                "    movq %r15,%rdi\n"
                "    call erist_u2_release_7_"+second+"\n"
                "    cmpq $0,8(%r15)\n"
                "    jne .Lgraph_test_fail\n"
                "    call evn_void\n")
            self.assertIn(before,multi)
            multi=multi.replace(before,after,1)
            second_execution=FreestandingTextLifetimeTests._link_run(
                self,directory,"u2-two-emitted-roots",runtime,
                descriptors()+emission+multi+FINISH)
            self.assertEqual(
                (second_execution.returncode,second_execution.stdout,
                 second_execution.stderr),
                (0,b"u2-emitted-root\nu2-emitted-root\n",b""))
