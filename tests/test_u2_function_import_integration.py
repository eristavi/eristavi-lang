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
import test_u2_text_unicode17 as unicodeTests

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

    def text_source(self,bad_contract=False,fixture="u2_text_unicode17_cfg.eri"):
        source=(REF/fixture).read_text(encoding="utf-8")
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

    def list_source(self,bad_contract=False,fixture="u2_list_i64_loop.eri"):
        source=(REF/fixture).read_text(encoding="utf-8")
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

    def mixed_source(self,wrong_list_descriptor=False):
        # Start from the SAME verified Unicode17 canonical Function fixture.
        # Add only a List<i64> import and SSA-carried List value. There is no
        # second IR builder or duplicated Text/List runtime implementation.
        source=self.text_source()
        def change(old,new):
            nonlocal source
            self.assertEqual(source.count(old),1,old)
            source=source.replace(old,new,1)
        change("import compiler.u2_text_native as textNative;",
               "import compiler.u2_text_native as textNative;\n"
               "import compiler.u2_list_i64 as listNative;")
        change("    try aggregate.freeze(graph);",
               "    let listCarrier be try aggregate.aggregate(graph,p,[intType]);\n"
               "    let listEmptySig be try sig.signature(data,graph,p,[],[listCarrier]);\n"
               "    let listEmpty be try meta.declaration(data,p,listEmptySig,"
               "listNative.name(1),2,63,1);\n"
               "    let listAppendSig be try sig.signature(data,graph,p,"
               "[listCarrier,intType],[listCarrier]);\n"
               "    let listAppend be try meta.declaration(data,p,listAppendSig,"
               "listNative.name(3),2,63,1);\n"
               "    let listCountSig be try sig.signature(data,graph,p,"
               "[listCarrier],[intType]);\n"
               "    let listCount be try meta.declaration(data,p,listCountSig,"
               "listNative.name(5),2,63,1);\n"
               "    try aggregate.freeze(graph);")
        change("    let textType be managed.text(registry);",
               "    let textType be managed.text(registry);\n"
               "    let listType be try managed.listOfBase(registry,p,intType);")
        for block in ("loopBlock","bodyBlock","doneBlock"):
            change("let "+block+" be try ab.block(fn,graph,[carrier,carrier]);",
                   "let "+block+" be try ab.block(fn,graph,"
                   "[carrier,carrier,listCarrier]);")
        change("    try ab.jump(fn,graph,entryBlock,loopBlock,[original,original],loc);",
               "    let listCall be try ab.call(fn,graph,entryBlock,"
               "listEmpty,[],loc);\n"
               "    let emptyList be try build.result(fn,listCall,0);\n"
               "    listCall=try ab.call(fn,graph,entryBlock,"
               "listAppend,[emptyList,limit],loc);\n"
               "    let retainedList be try build.result(fn,listCall,0);\n"
               "    try ab.jump(fn,graph,entryBlock,loopBlock,"
               "[original,original,retainedList],loc);")
        change("    let held be try build.parameter(fn,loopBlock,1);",
               "    let held be try build.parameter(fn,loopBlock,1);\n"
               "    let loopList be try build.parameter(fn,loopBlock,2);")
        change("    try ab.branch(fn,graph,loopBlock,condition,bodyBlock,"
               "[current,held],\n"
               "        doneBlock,[current,held],loc);",
               "    try ab.branch(fn,graph,loopBlock,condition,bodyBlock,"
               "[current,held,loopList],\n"
               "        doneBlock,[current,held,loopList],loc);")
        change("    let snapshot be try build.parameter(fn,bodyBlock,1);",
               "    let snapshot be try build.parameter(fn,bodyBlock,1);\n"
               "    let bodyList be try build.parameter(fn,bodyBlock,2);")
        change("    try ab.jump(fn,graph,bodyBlock,loopBlock,[next,snapshot],loc);",
               "    try ab.jump(fn,graph,bodyBlock,loopBlock,"
               "[next,snapshot,bodyList],loc);")
        change("    let originalSnapshot be try build.parameter(fn,doneBlock,1);",
               "    let originalSnapshot be try build.parameter(fn,doneBlock,1);\n"
               "    let doneList be try build.parameter(fn,doneBlock,2);")
        change("    try build.returnValues(fn,doneBlock,[oldCount],loc);",
               "    listCall=try ab.call(fn,graph,doneBlock,listCount,"
               "[doneList],loc);\n"
               "    let listLength be try build.result(fn,listCall,0);\n"
               "    let answer be try build.wrapAdd(fn,doneBlock,"
               "oldCount,listLength,loc);\n"
               "    try build.returnValues(fn,doneBlock,[answer],loc);")
        change("[carrier],[textType],true,95);",
               "[carrier,listCarrier],[textType,listType],true,95);")
        if wrong_list_descriptor:
            change("let listType be try managed.listOfBase(registry,p,intType);",
                   "let listType be try managed.identityOfBase(registry,p,intType);")
        return source

    def test_existing_unicode17_full_operation_corpus_through_whole_function(self):
        # The OLD original canonical Text corpus already encodes all twelve
        # runtime imports. Only replace its final selected result and the
        # emitter: this adds no new Text operation implementation.
        cases=(
            ("accentByte1",204,False),
            ("emojiCharacters",1,False),
            ("accentGraphemeMatches",1,True),
            ("normalizedMatches",1,True),
        )
        for expression,expected,predicate in cases:
            with self.subTest(expression=expression):
                source=self.text_source(
                    fixture="u2_text_unicode17.eri")
                source=source.replace(
                    "[accentCharacters],loc);",
                    "["+expression+"],loc);")
                if predicate:
                    source=source.replace(
                        "let entrySig be try meta.signature(data,p,[],[meta.i64()]);",
                        "let entrySig be try meta.signature(data,p,[],[meta.pred()]);")
                created=self.generator("u2-text-entire-"+expression,source)
                self.assertEqual((created.returncode,created.stderr),
                                 (0,""),created.stdout[-3000:])
                for symbol in ("erist_rt_unicode_from_scalar",
                               "erist_rt_text_concat",
                               "erist_rt_text_binary",
                               "erist_rt_view_count",
                               "erist_rt_view_index",
                               "erist_rt_unicode_normalize_nfc"):
                    self.assertIn("call "+symbol,created.stdout)
                self.run_native(created.stdout,
                                "u2-text-original-full-"+expression,
                                expected,"95")

    def test_mixed_text_list_calls_share_exact_whole_function_root_map(self):
        created=self.generator("u2-text-and-list-same-function",
                               self.mixed_source())
        self.assertEqual((created.returncode,created.stderr),
                         (0,""),created.stdout[-3500:])
        for symbol in ("erist_rt_unicode_from_scalar","erist_rt_text_concat",
                       "erist_rt_view_count","evn_object","evn_copy",
                       "evn_int","evn_add","evn_count"):
            self.assertIn("call "+symbol,created.stdout)
        self.run_native(created.stdout,
                        "u2-text-list-combined-canonical-native",2,"95")

    def test_mixed_list_cannot_masquerade_as_identity_descriptor(self):
        created=self.generator("u2-mixed-wrong-list-type",
                               self.mixed_source(wrong_list_descriptor=True))
        self.assertEqual(created.returncode,1,created.stdout[-2500:])
        self.assertIn("roots:",created.stdout)
        self.assertNotIn("erist_u2_rooted_function_95:",created.stdout)
        self.assertNotIn(".section",created.stdout)

    def run_native(self,asm,name,expected,suffix):
        body=("\n.text\n.globl _start\n_start:\n"
              "    xorl %edi,%edi\n"
              "    xorl %esi,%esi\n"
              "    call erist_u2_rooted_function_"+suffix+"\n"
              "    cmpq $"+str(expected)+",%rax\n"
              "    jne .Lgraph_test_fail\n"
              "    jmp .Lgraph_finish\n")
        if suffix == "95":
            # The existing Unicode17 native fixture defines the required
            # three view descriptors (15, 16, 17) in the owned type table.
            # Reuse it unchanged; generic graph descriptors omit these.
            result=self.run_probe(name,asm+body+graph.FINISH+
                                  unicodeTests.unicode_descriptors(),
                                  types=False)
        else:
            result=self.run_probe(name,asm+body+graph.FINISH)
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

    def test_existing_list_copy_import_inside_original_loop(self):
        source=self.list_source()
        anchor=("call=try ab.call(fn,g,b,f3,[empty,ten],loc); "
                "let initial be try build.result(fn,call,0);")
        self.assertEqual(source.count(anchor),1)
        source=source.replace(anchor,anchor+
            "\n call=try ab.call(fn,g,b,f2,[initial],loc);"
            " let copied be try build.result(fn,call,0);",1)
        source=source.replace(
            "try ab.jump(fn,g,b,loop,[initial,initial],loc);",
            "try ab.jump(fn,g,b,loop,[copied,initial],loc);",1)
        created=self.generator("u2-list-native-copy-import",source)
        self.assertEqual((created.returncode,created.stderr),(0,""),
                         created.stdout[-2500:])
        self.assertGreaterEqual(created.stdout.count("call evn_copy"),3)
        self.run_native(created.stdout,
                        "u2-list-copy-through-Function",1,"96")

    def test_original_list_index_and_replace_snapshot_semantics(self):
        # Reuse the original bounded List fixture, including its sequence
        # of copy, append, replace and reads. No new List runtime semantics.
        for expression,expected in (("old",10),("latest",20),
                                    ("changedZero",20),("changedCount",2),
                                    ("oldCount",1)):
            with self.subTest(result=expression):
                source=self.list_source(fixture="u2_list_i64.eri")
                target="build.returnValues(fn,b,[old],loc);"
                self.assertEqual(source.count(target),1)
                source=source.replace(target,
                    "build.returnValues(fn,b,["+expression+"],loc);",1)
                generated=self.generator("u2-list-index-"+expression,source)
                self.assertEqual((generated.returncode,generated.stderr),
                                 (0,""),generated.stdout[-2400:])
                for symbol in ("erist_rt_graph_object_of","evn_index_ref",
                               "evn_store","evn_index","evn_copy",
                               "erist_rt_text_collect"):
                    self.assertIn("call "+symbol,generated.stdout)
                self.assertIn("erist_u2_rooted_function_96_bounds_",
                              generated.stdout)
                self.run_native(generated.stdout,
                                "u2-whole-list-index-"+expression,expected,"96")

    def test_original_list_index_bounds_faults_keep_source_location(self):
        for index in (-1,2):
            with self.subTest(index=index):
                source=self.list_source(fixture="u2_list_i64.eri")
                target="let zero be try build.integer(fn,b,0,loc);"
                self.assertEqual(source.count(target),1)
                source=source.replace(target,
                    "let zero be try build.integer(fn,b,"+str(index)+",loc);",1)
                generated=self.generator("u2-list-index-bounds-"+str(index),
                                         source)
                self.assertEqual((generated.returncode,generated.stderr),
                                 (0,""),generated.stdout[-2400:])
                starter=("\\n.text\\n.globl _start\\n_start:\\n"
                         " call erist_u2_rooted_function_96\\n"
                         " movl $99,%edi\\n jmp erist_rt_exit\\n")
                result=self.run_probe("u2-list-bounds-"+str(index),
                                      generated.stdout+starter)
                self.assertEqual(result.returncode,1,result.stderr)
                self.assertIn(b"List index out of bounds",result.stderr)
                self.assertIn(b"list-probe:1:1: ",result.stderr)

    def test_wrong_list_effects_refused_before_native_assembly(self):
        result=self.generator("u2-list-bad-import",
                              self.list_source(bad_contract=True))
        self.assertEqual(result.returncode,1,result.stdout[-2300:])
        self.assertIn("native:",result.stdout)
        self.assertNotIn("erist_u2_rooted_function_96:",result.stdout)
        self.assertNotIn(".section",result.stdout)
