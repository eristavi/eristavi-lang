"""Reuse pre-existing U2 Text and List native runtime imports in whole UIR.

No duplicate Text/List semantic fixture: adapt their original frozen canonical
programs and compare native results with the previously qualified adapters.
Every allocating operation uses independently proven SSA-managed roots.
"""
from pathlib import Path
import platform
import subprocess
import unittest

from compiler.erist.cli import build_native
import test_freestanding_graph_values as graph

ROOT=Path(__file__).resolve().parents[1]
REF=ROOT/"tests/fixtures"


@unittest.skipUnless(platform.system()=="Linux" and
                     platform.machine().lower() in ("x86_64","amd64"),
                     "Text/List whole-Function integration is Linux x86-64")
class U2FunctionImportIntegrationTests(unittest.TestCase):
    setUpClass=classmethod(graph.FreestandingGraphValueTests.setUpClass.__func__)
    run_probe=graph.FreestandingGraphValueTests.run_probe

    def generator(self,name,source):
        folder=self.directory/name
        folder.mkdir(exist_ok=True)
        (folder/"compiler").symlink_to(ROOT/"src/compiler",
                                        target_is_directory=True)
        source_file=folder/"generated.eri"
        source_file.write_text(source,encoding="utf-8")
        executable=folder/"generated"
        self.assertEqual(build_native(source_file,executable,folder),0)
        return subprocess.run([str(executable)],capture_output=True,
                              text=True,timeout=180)

    def text_source(self,bad_contract=False):
        source=(REF/"u2_text_unicode17_cfg.eri").read_text(
            encoding="utf-8")
        def replace(old,new):
            nonlocal source
            self.assertEqual(source.count(old),1,old)
            source=source.replace(old,new,1)
        replace("import compiler.u2_text_native as textNative;",
                "import compiler.u2_text_native as textNative;\n"
                "import compiler.u2_function_managed_x86_64 as integrated;\n"
                "import compiler.u2_invoke_contract as contracts;\n"
                "import compiler.u2_managed_root_gate as roots;\n"
                "import compiler.u2_ssa_liveness as ssa;")
        replace("try meta.freeze(data); try budget.finishPhase(p);",
                "try meta.freeze(data);\n"
                "    let table be try contracts.create(data,graph,p);\n"
                "    try contracts.freeze(table);\n"
                "    try budget.finishPhase(p);")
        replace("try textNative.emitManaged(fn,graph,carrier,read,registry,textType);",
                "try integrated.emit(fn,graph,table,read,registry,"
                "[carrier],[textType],true,95);")
        replace("try managed.close(registry); try aggregate.close(graph);",
                "try contracts.close(table);\n"
                "    try managed.close(registry); try aggregate.close(graph);")
        replace("    textNative.Unsupported,managed.InvalidManagedTypes,"
                "graphVerify.InvalidGraph {",
                "    textNative.Unsupported,integrated.Unsupported,"
                "roots.InvalidManagedRoots,ssa.InvalidLiveness,"
                "managed.InvalidManagedTypes,graphVerify.InvalidGraph {")
        replace("} else error textNative.Unsupported {",
                "} else error integrated.Unsupported {\n"
                "    output(\"native:\"+error.message); process.setExitCode(1);\n"
                "} else error roots.InvalidManagedRoots {\n"
                "    output(\"roots:\"+error.message); process.setExitCode(1);\n"
                "} else error ssa.InvalidLiveness {\n"
                "    output(\"ssa:\"+error.message); process.setExitCode(1);\n"
                "} else error textNative.Unsupported {")
        if bad_contract:
            replace("textNative.name(2),2,63,1);",
                    "textNative.name(2),1,63,1);")
        return source

    def list_source(self,bad_contract=False):
        source=(REF/"u2_list_i64_loop.eri").read_text(encoding="utf-8")
        def replace(old,new):
            nonlocal source
            self.assertEqual(source.count(old),1,old)
            source=source.replace(old,new,1)
        replace("import compiler.u2_list_i64 as lists;",
                "import compiler.u2_list_i64 as lists;\n"
                "import compiler.u2_function_managed_x86_64 as integrated;\n"
                "import compiler.u2_invoke_contract as contracts;\n"
                "import compiler.u2_managed_root_gate as roots;\n"
                "import compiler.u2_ssa_liveness as ssa;")
        replace("try managed.freeze(managedTable); try meta.freeze(data); "
                "try budget.finishPhase(p);",
                "try managed.freeze(managedTable); try meta.freeze(data);\n"
                " let table be try contracts.create(data,g,p);\n"
                " try contracts.freeze(table); try budget.finishPhase(p);")
        replace("try lists.emitManaged(fn,g,carrier,read,managedTable,managedList);",
                "try integrated.emit(fn,g,table,read,managedTable,"
                "[carrier],[managedList],true,96);")
        replace("try managed.close(managedTable); try aggregate.close(g);",
                "try contracts.close(table);\n"
                " try managed.close(managedTable); try aggregate.close(g);")
        replace("lists.Unsupported,managed.InvalidManagedTypes,"
                "graphVerify.InvalidGraph {",
                "lists.Unsupported,integrated.Unsupported,"
                "roots.InvalidManagedRoots,ssa.InvalidLiveness,"
                "managed.InvalidManagedTypes,graphVerify.InvalidGraph {")
        replace("else error lists.Unsupported { output(error.message); "
                "process.setExitCode(1); };",
                "else error integrated.Unsupported {"
                " output(\"native:\"+error.message); process.setExitCode(1); }\n"
                "else error roots.InvalidManagedRoots {"
                " output(\"roots:\"+error.message); process.setExitCode(1); }\n"
                "else error ssa.InvalidLiveness {"
                " output(\"ssa:\"+error.message); process.setExitCode(1); }\n"
                "else error lists.Unsupported { output(error.message); "
                "process.setExitCode(1); };")
        if bad_contract:
            replace("lists.name(3),2,63,1);",
                    "lists.name(3),2,0,1);")
        return source

    def run_native(self,asm,name,expected,suffix):
        body=("\n.text\n.globl _start\n_start:\n"
              "    xorl %edi,%edi\n"
              "    xorl %esi,%esi\n"
              "    call erist_u2_rooted_function_"+suffix+"\n"
              "    cmpq $"+str(expected)+",%rax\n"
              "    jne .Lgraph_test_fail\n"
              "    jmp .Lgraph_finish\n")
        result=self.run_probe(name,asm+body+graph.FINISH)
        if result.returncode != 0 and suffix == "95":
            # First-fault placement is native-only diagnostic code; the
            # original full program remains mandatory for acceptance.
            checkpoints={}
            for index,symbol in enumerate((
                    "erist_rt_unicode_from_scalar",
                    "evn_view",
                    "erist_rt_view_count",
                    "erist_rt_text_concat",
                    "erist_rt_slots_collect",
                    "erist_rt_text_collect")):
                needle="    call "+symbol
                if needle not in asm:
                    continue
                short=asm.replace(needle,
                    "    xorl %edi,%edi\n    jmp erist_rt_exit\n"+needle,1)
                probe=self.run_probe(name+"-before-"+str(index),
                                     short+body+graph.FINISH)
                checkpoints[symbol]=(
                    probe.returncode,probe.stderr.decode("utf-8",
                                                         errors="replace")[:100])
            before="    call evn_view"
            if before in asm:
                probeAsm=asm.replace(before,
                    "    movq 0(%rsi),%rdi\n    jmp erist_rt_exit\n"+before,1)
                tag=self.run_probe(name+"-text-value-tag",
                                   probeAsm+body+graph.FINISH)
                checkpoints["before_view_value_type"]=tag.returncode
            self.fail("Text whole-Function native result=%r; "
                      "checkpoints=%r; stderr=%r" %
                      (result.returncode,checkpoints,result.stderr))
        self.assertEqual((result.returncode,result.stdout,result.stderr),
                         (0,b"",b""))

    def test_existing_unicode17_text_concat_counts_gc_in_whole_function(self):
        result=self.generator("u2-text-existing-loop",self.text_source())
        self.assertEqual((result.returncode,result.stderr),(0,""),
                         result.stdout[-3200:])
        self.assertIn("call erist_rt_unicode_from_scalar",result.stdout)
        self.assertIn("call erist_rt_text_concat",result.stdout)
        self.assertIn("call erist_rt_view_count",result.stdout)
        self.assertIn("call erist_rt_text_collect",result.stdout)
        self.run_native(result.stdout,"u2-text-original-function-imports",1,
                        "95")

    def test_text_without_forced_block_gc_is_still_valid(self):
        # Differential diagnostic: distinguish native ABI/integer-boxing
        # problems from a generated safe-point root publication error.
        source=self.text_source().replace(
            "[carrier],[textType],true,95);",
            "[carrier],[textType],false,95);")
        generated=self.generator("u2-text-no-block-gc",source)
        self.assertEqual((generated.returncode,generated.stderr),
                         (0,""),generated.stdout[-2100:])
        self.run_native(generated.stdout,
                        "u2-text-no-forced-block-gc",1,"95")

    def test_existing_list_snapshot_append_count_gc_in_whole_function(self):
        result=self.generator("u2-list-existing-loop",self.list_source())
        self.assertEqual((result.returncode,result.stderr),(0,""),
                         result.stdout[-3200:])
        for snippet in ("call evn_object","call evn_copy","call evn_add",
                        "call evn_count","call erist_rt_text_collect"):
            self.assertIn(snippet,result.stdout)
        self.run_native(result.stdout,"u2-list-original-function-imports",1,
                        "96")

    def test_wrong_text_import_version_refused_before_native_assembly(self):
        result=self.generator("u2-text-bad-import",
                              self.text_source(bad_contract=True))
        self.assertEqual(result.returncode,1,result.stdout[-2300:])
        # The frozen builder rejects invalid import versions even before
        # our bridge sees them; the fail-closed outcome is still required.
        self.assertIn("budget:invalid U1a import contract version",
                      result.stdout)
        self.assertNotIn("erist_u2_rooted_function_95:",result.stdout)
        self.assertNotIn(".section",result.stdout)

    def test_wrong_list_effects_refused_before_native_assembly(self):
        result=self.generator("u2-list-bad-import",
                              self.list_source(bad_contract=True))
        self.assertEqual(result.returncode,1,result.stdout[-2300:])
        self.assertIn("native:",result.stdout)
        self.assertNotIn("erist_u2_rooted_function_96:",result.stdout)
        self.assertNotIn(".section",result.stdout)
