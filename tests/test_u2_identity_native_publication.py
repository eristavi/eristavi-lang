"""Canonical identity SSA -> native class-1 root-word publication.

Verifies a real emitted root binder and before/after retirement against the
existing x86-64 owned collector, not an alternate executable UIR or general
native identity instruction lowering. Preserve the private closed profile.
"""
from pathlib import Path
import platform
import re
import subprocess
import unittest

from compiler.erist.cli import build_native
import test_freestanding_graph_values as graph

ROOT=Path(__file__).resolve().parents[1]
LABEL=73


@unittest.skipUnless(platform.system()=="Linux" and
                     platform.machine().lower() in ("x86_64","amd64"),
                     "U2 native identity roots currently require Linux x86-64")
class U2IdentityNativePublicationTests(unittest.TestCase):
    setUpClass=classmethod(graph.FreestandingGraphValueTests.setUpClass.__func__)
    run_probe=graph.FreestandingGraphValueTests.run_probe

    def source(self):
        original=(ROOT/"tests/fixtures/u1_aggregate_loops.eri").read_text(
            encoding="utf-8")
        def unique(old,new):
            nonlocal original
            self.assertEqual(original.count(old),1,old)
            original=original.replace(old,new,1)
        unique("import compiler.u1_meta as meta;",
            "import compiler.u1_meta as meta;\n"
            "import compiler.u1_words as words;\n"
            "import compiler.u1_aggregate_verify as graphVerify;\n"
            "import compiler.u2_invoke_contract as contracts;\n"
            "import compiler.u2_managed_types as managed;\n"
            "import compiler.u2_ssa_liveness as ssa;\n"
            "import compiler.u2_identity_root_gate as identityRoots;\n"
            "import compiler.u2_identity_root_x86_64 as rootEmitter;\n"
            "import compiler.format as format;")
        unique("try aggregate.freeze(graph); try meta.freeze(data);",
            "try aggregate.freeze(graph);\n"
            "    let registry be try managed.create(graph,mp);\n"
            "    let identityType be try managed.identityOfBase(registry,mp,pair);\n"
            "    try managed.freeze(registry);\n"
            "    try meta.freeze(data);\n"
            "    let table be try contracts.create(data,graph,mp);\n"
            "    try contracts.freeze(table);")
        unique("    try budget.finishPhase(cp);",
            "    try budget.finishPhase(cp);\n"
            "    let read be try budget.constructionPhase(fnOwner);\n"
            "    let definition be try words.get(fn.values,read,(next.index-1)*4+2);\n"
            "    let at be build.InstId { owner=fn.key; index=definition; };\n"
            "    try rootEmitter.emit(fn,graph,table,read,registry,pair,"
            "identityType,at,73);\n"
            '    output(".set u2_identity_current, "+format.integer(current.index));\n'
            '    output(".set u2_identity_next, "+format.integer(next.index));\n'
            "    try budget.finishPhase(read);")
        unique("    try build.close(fn); try aggregate.close(graph);",
            "    try contracts.close(table); try managed.close(registry);\n"
            "    try build.close(fn); try aggregate.close(graph);")
        unique("function run() returns Bool fails budget.LimitError,verify.InvalidIR,ProbeError {",
            "function run() returns Bool fails budget.LimitError,verify.InvalidIR,"
            "ProbeError,rootEmitter.Unsupported,identityRoots.InvalidIdentityRoot,"
            "ssa.InvalidLiveness,managed.InvalidManagedTypes,"
            "graphVerify.InvalidGraph {")
        unique("} else error ProbeError {",
            "} else error rootEmitter.Unsupported {"
            ' output("native:"+error.message); process.setExitCode(1); return;'
            " } else error identityRoots.InvalidIdentityRoot {"
            ' output("identity:"+error.message); process.setExitCode(1); return;'
            " } else error ssa.InvalidLiveness {"
            ' output("liveness:"+error.message); process.setExitCode(1); return;'
            " } else error managed.InvalidManagedTypes {"
            ' output("managed:"+error.message); process.setExitCode(1); return;'
            " } else error graphVerify.InvalidGraph {"
            ' output("graph:"+error.message); process.setExitCode(1); return;'
            " } else error ProbeError {")
        # The generator's stdout must contain only a valid assembly fragment.
        unique("    output(try execute.result(completed,0));\n", "")
        unique("    output(try execute.result(completed,1));\n", "")
        unique('    output("u1b-aggregate-loop:ok");\n', "")
        return original

    def generator(self,folder,source):
        root=self.directory/folder
        root.mkdir()
        (root/"compiler").symlink_to(ROOT/"src/compiler",target_is_directory=True)
        input_file=root/"app.eri"
        input_file.write_text(source,encoding="utf-8")
        binary=root/"generator"
        self.assertEqual(build_native(input_file,binary,root),0)
        return subprocess.run([str(binary)],capture_output=True,text=True,
                              timeout=90)

    def test_verified_identity_ssa_root_before_after_and_native_gc(self):
        generated=self.generator("native-identity-ssa",self.source())
        self.assertEqual((generated.returncode,generated.stderr),
                         (0,""),generated.stdout)
        asm=generated.stdout
        def symbol(name):
            m=re.search(r"^\.set "+re.escape(name)+r", (\d+)$",asm,re.M)
            self.assertIsNotNone(m,name)
            return int(m.group(1))
        current=symbol("u2_identity_current")
        next_value=symbol("u2_identity_next")
        root_offsets={}
        for index,offset in re.findall(
            r"^\.set erist_u2_identity_slot_73_(\d+), (\d+)$",
            asm,re.M):
            root_offsets[int(index)]=int(offset)
        self.assertGreaterEqual(len(root_offsets),2)
        self.assertIn(current,root_offsets)
        self.assertIn(next_value,root_offsets)
        self.assertNotEqual(root_offsets[current],root_offsets[next_value])
        self.assertIn("    .byte 1",asm)
        for fn in ("bind","before","after","release"):
            self.assertIn("erist_u2_identity_"+fn+"_73:",asm)
        self.assertIn("jmp evn_bind_roots",asm)
        # Canonical ValueId -> frame offset, selected value -> compact root
        # offset. No hardcoded SSA indices or root-table positions are used.
        self.assertEqual(
            symbol("erist_u2_identity_ssa_73_"+str(current)),
            (current-1)*8)
        self.assertEqual(
            symbol("erist_u2_identity_ssa_73_"+str(next_value)),
            (next_value-1)*8)

        # Construct a genuine 3-node cycle; all three nodes are retained
        # only by class-1 roots, never by Python/test-global fake roots.
        before_current=root_offsets[current]
        before_next=root_offsets[next_value]
        body=r"""
.text
.globl _start
_start:
    xorl %ebp,%ebp
    call evn_scope_enter
    movq %rax,%r15
    movq %rax,%rdi
    leaq .Lu2_roots(%rip),%rsi
    call erist_u2_identity_bind_73

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

    # Deliberately use a separate unregistered full canonical SSA frame.
    # Its raw copies must NOT retain the graph once root release happens.
    leaq .Lu2_ssa(%rip),%rdi
    movl $512,%ecx
    rep stosq
    leaq .Lu2_roots(%rip),%rdi
    leaq .Lu2_ssa(%rip),%rsi
    call erist_u2_identity_before_73
"""
        body+=f"""    cmpq $0,.Lu2_roots+{before_current}(%rip)
    je .Lgraph_test_fail
    cmpq $0,.Lu2_roots+{before_next}(%rip)
    jne .Lgraph_test_fail
    xorl %edi,%edi
    call erist_rt_slots_collect
    call erist_rt_text_collect
    call erist_rt_graph_live_objects
    cmpq $3,%rax
    jne .Lgraph_test_fail
    leaq .Lu2_roots(%rip),%rdi
    leaq .Lu2_ssa(%rip),%rsi
    call erist_u2_identity_after_73
    cmpq $0,.Lu2_roots+{before_current}(%rip)
    jne .Lgraph_test_fail
    cmpq $0,.Lu2_roots+{before_next}(%rip)
    je .Lgraph_test_fail
"""
        body+=r"""
    xorl %edi,%edi
    call erist_rt_slots_collect
    call erist_rt_text_collect
    call erist_rt_graph_live_objects
    cmpq $3,%rax
    jne .Lgraph_test_fail
    leaq .Lu2_roots(%rip),%rdi
    call erist_u2_identity_release_73
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
.Lu2_roots:
"""
        body+=".zero "+str(8*len(root_offsets))+"\n"
        body+=".p2align 3\n.Lu2_ssa:\n.zero 4096\n"
        result=self.run_probe("u2-identity-verified-safepoints",
             asm+body+graph.FINISH)
        self.assertEqual((result.returncode,result.stdout,result.stderr),
                         (0,b"",b""))

    def test_more_than_32_selected_identity_roots_emit_exact_offsets(self):
        # A large dead-value cohort still belongs to the canonical Function.
        # No tracked identity may silently disappear from the native root
        # vector merely because its liveness bit happens to be zero.
        source=self.source()
        marker="    try build.jump(fn,dead,deadDestination,[input],loc);"
        self.assertEqual(source.count(marker),1)
        extra=(
            "    let deadRootLeft be try build.integer(fn,dead,11,loc);\n"
            "    let deadRootRight be try build.integer(fn,dead,17,loc);\n"
        )+"".join(
            "    let rootCandidate%d be try ab.make(fn,graph,dead,pair,"
            "[deadRootLeft,deadRootRight],loc);\n"%index
            for index in range(40))
        source=source.replace(marker,extra+marker,1)
        generated=self.generator("native-identity-ssa-wide",source)
        self.assertEqual((generated.returncode,generated.stderr),
                         (0,""),generated.stdout[-3500:])
        roots=re.findall(
            r"^\.set erist_u2_identity_slot_73_(\d+), (\d+)$",
            generated.stdout,re.M)
        count=len(roots)
        self.assertGreater(count,32)
        self.assertLessEqual(count,64)
        ids=[int(item[0]) for item in roots]
        self.assertEqual(len(set(ids)),count)
        self.assertEqual([int(item[1]) for item in roots],
                         list(range(0,count*8,8)))
        self.assertIn("    movl $"+str(count)+",%ecx",generated.stdout)
        self.assertIn("erist_u2_identity_before_73:",generated.stdout)
        self.assertIn("erist_u2_identity_after_73:",generated.stdout)
        self.assertIn("erist_u2_identity_release_73:",generated.stdout)

    def mixed_source(self,invalid=False):
        source=self.source()
        def once(old,new):
            nonlocal source
            self.assertEqual(source.count(old),1,old)
            source=source.replace(old,new,1)
        once("import compiler.u2_identity_root_x86_64 as rootEmitter;",
             "import compiler.u2_identity_root_x86_64 as rootEmitter;\n"
             "import compiler.u2_managed_root_gate as managedRoots;\n"
             "import compiler.u2_managed_root_x86_64 as mixedRoot;")
        once("    try aggregate.freeze(graph);",
             "    let empty be try aggregate.aggregate(graph,mp,[]);\n"
             "    let triple be try aggregate.aggregate(graph,mp,[i64,i64,i64]);\n"
             "    try aggregate.freeze(graph);")
        once("    let identityType be try managed.identityOfBase(registry,mp,pair);",
             "    let identityType be try managed.identityOfBase(registry,mp,pair);\n"
             "    let listType be try managed.listOfBase(registry,mp,triple);")
        once("    try build.jump(fn,dead,deadDestination,[input],loc);",
             "    let deadA be try build.integer(fn,dead,3,loc);\n"
             "    let deadB be try build.integer(fn,dead,5,loc);\n"
             "    let opaqueText be try ab.make(fn,graph,dead,empty,[],loc);\n"
             "    let opaqueList be try ab.make(fn,graph,dead,triple,"
             "[deadA,deadB,deadA],loc);\n"
             "    try build.jump(fn,dead,deadDestination,[input],loc);")
        marker='    output(".set u2_identity_current, "+format.integer(current.index));'
        carriers="[empty,triple,pair]"
        types=("[managed.text(registry),identityType,listType]" if invalid
               else "[managed.text(registry),listType,identityType]")
        once(marker,
             "    try mixedRoot.emit(fn,graph,table,read,registry,"+
             carriers+","+types+",at,74);\n"+marker)
        once("ProbeError,rootEmitter.Unsupported,",
             "ProbeError,rootEmitter.Unsupported,mixedRoot.Unsupported,"
             "managedRoots.InvalidManagedRoots,")
        marker=" } else error graphVerify.InvalidGraph {"
        once(marker,
             ' } else error mixedRoot.Unsupported {'
             ' output("mixed-native:"+error.message);'
             ' process.setExitCode(1); return;'
             ' } else error managedRoots.InvalidManagedRoots {'
             ' output("mixed-roots:"+error.message);'
             ' process.setExitCode(1); return;'+marker)
        return source

    def test_mixed_text_list_identity_root_publication(self):
        result=self.generator("mixed-managed-native",self.mixed_source())
        self.assertEqual((result.returncode,result.stderr),(0,""),
                         result.stdout[-2000:])
        slots=re.findall(
            r"^\.set erist_u2_managed_slot_74_(\d+), (\d+)$",
            result.stdout,re.M)
        self.assertGreaterEqual(len(slots),6)
        self.assertEqual(len(set(int(v) for v,_ in slots)),len(slots))
        self.assertEqual([int(o) for _,o in slots],
                         list(range(0,len(slots)*8,8)))
        for name in ("bind","before","after","release"):
            self.assertIn("erist_u2_managed_"+name+"_74:",result.stdout)
        self.assertIn("erist_u2_managed_classes_74:",result.stdout)
        self.assertIn("    movl $"+str(len(slots))+",%ecx",
                      result.stdout)

    def test_mismatched_mixed_managed_descriptor_refuses_before_emission(self):
        result=self.generator("mixed-managed-invalid",
                              self.mixed_source(invalid=True))
        self.assertEqual(result.returncode,1,result.stdout[-1800:])
        self.assertIn("mixed-roots:",result.stdout)
        self.assertNotIn("erist_u2_managed_bind_74:",result.stdout)
        self.assertNotIn("erist_u2_managed_classes_74:",result.stdout)

    def test_invalid_identity_descriptor_rejected_without_assembly(self):
        source=self.source()
        before="identityType,at,73);"
        self.assertEqual(source.count(before),1)
        source=source.replace(before,"managed.text(registry),at,73);",1)
        invalid=self.generator("foreign-identity-publication",source)
        self.assertEqual(invalid.returncode,1,invalid.stdout)
        self.assertIn("identity:",invalid.stdout)
        self.assertNotIn("erist_u2_identity_bind_73:",invalid.stdout)
        self.assertNotIn(".section",invalid.stdout)
