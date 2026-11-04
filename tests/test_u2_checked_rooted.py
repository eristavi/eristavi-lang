"""Live class-5 canonical checked root through actual File cleanup and forced GC."""
from pathlib import Path
import platform
import subprocess
import unittest
from compiler.erist.cli import build_native
import test_freestanding_resource_values as resource

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(platform.system() == "Linux" and
    platform.machine().lower() in ("x86_64", "amd64"),
    "private U2 native checked-root profile needs Linux x86-64")
class U2CheckedRootedTests(unittest.TestCase):
    setUpClass = classmethod(resource.FreestandingResourceValueTests.setUpClass.__func__)
    run_probe = resource.FreestandingResourceValueTests.run_probe

    def emit(self):
        source = (ROOT / "tests/fixtures/u2_scoped_owners.eri").read_text(encoding="utf-8")
        marker = "import compiler.u2_scoped_owners as owners;"
        self.assertIn(marker, source)
        source = source.replace(marker, marker + "\n" +
            "import compiler.u2_cleanup_plan as cleanup;\n"
            "import compiler.u2_cleanup_verify as planVerify;\n"
            "import compiler.u2_root_map as roots;\n"
            "import compiler.u2_native_slots_x86_64 as slots;\n"
            "import compiler.u2_native_root_x86_64 as rootEmit;\n"
            "import compiler.u2_cleanup_canonical_x86_64 as canonicalCleanup;\n"
            "import compiler.u2_checked_rooted_x86_64 as native;\n", 1)
        old = "continuation.InvalidBinding,owners.InvalidOwnership,ProbeError {"
        self.assertIn(old, source)
        source = source.replace(old, "continuation.InvalidBinding,"
            "owners.InvalidOwnership,planVerify.InvalidPlan,roots.InvalidRoots,"
            "slots.InvalidSlots,rootEmit.Unsupported,canonicalCleanup.Unsupported,"
            "native.Unsupported,ProbeError {", 1)
        catcher = 'else error ProbeError { output("probe:"+error.message);'
        self.assertIn(catcher, source)
        source = source.replace(catcher,
            'else error planVerify.InvalidPlan { output("plan:"+error.message); process.setExitCode(1); }\n'
            'else error roots.InvalidRoots { output("root:"+error.message); process.setExitCode(1); }\n'
            'else error slots.InvalidSlots { output("slot:"+error.message); process.setExitCode(1); }\n'
            'else error rootEmit.Unsupported { output("rootEmit:"+error.message); process.setExitCode(1); }\n'
            'else error canonicalCleanup.Unsupported { output("canonical:"+error.message); process.setExitCode(1); }\n'
            'else error native.Unsupported { output("native:"+error.message); process.setExitCode(1); }\n'
            + catcher, 1)
        point = "let mutate be try budget.constructionPhase(owner); let revision be fn.revision;"
        self.assertIn(point, source)
        injection = point + "\n" + (
            "    let checkedPair be try continuation.bind(fn,graph,mutate,afterInner,done,failed,emptySig,failedSig,loc);\n"
            "    let selected be [cleanup.Scope { scope=outerScope; contract=consumption.index; value=afterValue.index; close=loc; }];\n"
            "    let plan be try planVerify.prepare(data,owner,mutate,selected,0,loc,false);\n"
            "    let map be try roots.create(fn,graph,mutate);\n"
            "    let placement be try slots.create(map,fn,graph,mutate);\n"
            "    let bounds be try slots.verify(placement,map,fn,graph,mutate);\n"
            '    try check(bounds.roots == 5 and bounds.rootBytes == 40,"wrong canonical root frame");\n'
            "    try native.emit(fn,graph,profile,table,mutate,map,placement,checkedPair,outerClose,plan,selected,0,loc,51);\n"
            "    try slots.close(placement); try roots.close(map); try cleanup.close(plan);"
        )
        source = source.replace(point, injection, 1)
        source = source.replace('output("u2-scoped-owners:ok");', "", 1)
        folder = self.directory / "u2-checked-rooted-generator"
        folder.mkdir(exist_ok=True)
        (folder / "compiler").symlink_to(ROOT / "src/compiler", target_is_directory=True)
        file = folder / "app.eri"
        file.write_text(source, encoding="utf-8")
        generator = folder / "generator"
        self.assertEqual(build_native(file, generator, folder), 0)
        result = subprocess.run([str(generator)], capture_output=True, text=True, timeout=120)
        self.assertEqual((result.returncode, result.stderr), (0, ""), result.stdout[-1500:])
        return result.stdout

    def native_assembly(self, emitted, path, close_fails):
        expect = "-1" if close_fails else "0"
        lines = [
            ".text", ".globl _start", "_start:",
            "    subq $96,%rsp",
            "    movq $0,0(%rsp)", "    movq $0,48(%rsp)",
            "    call evn_scope_enter", "    movq %rax,56(%rsp)",
            "    movq %rax,%rdi", "    movq %rsp,%rsi",
            "    leaq .Lowner_class(%rip),%rdx", "    movl $1,%ecx",
            "    call evn_bind_roots",
            "    call evn_scope_enter", "    movq %rax,64(%rsp)",
            "    movq %rax,%rdi", "    leaq 8(%rsp),%rsi",
            "    call erist_u2_bind_51",
            "    leaq .Lfile(%rip),%rdi",
            "    movl $(.Lfile_end-.Lfile),%esi",
            "    call evn_text", "    movq %rax,%rsi",
            "    movl $9,%edi", "    xorl %edx,%edx",
            "    call erist_rt_file_open", "    movq %rax,0(%rsp)",
            "    call evn_empty_failure", "    movq %rax,48(%rsp)",
            "    movq %rsp,%rdi", "    movq %rax,%rsi",
            "    leaq 8(%rsp),%rdx", "    call erist_u2_checked_51",
            "    cmpq $" + expect + ",%rax", "    jne .Lresource_test_fail",
            "    cmpq $0,0(%rsp)", "    jne .Lresource_test_fail",
        ]
        if close_fails:
            lines += [
                "    movq 32(%rsp),%rax", "    testq %rax,%rax",
                "    je .Lresource_test_fail", "    cmpq %rax,48(%rsp)",
                "    jne .Lresource_test_fail",
                "    cmpq $0,(%rax)", "    je .Lresource_test_fail",
            ]
        else:
            lines += ["    cmpq $0,32(%rsp)", "    jne .Lresource_test_fail"]
        lines += [
            "    xorl %edi,%edi", "    call erist_rt_slots_collect",
            "    call erist_rt_text_collect",
            "    call erist_rt_open_resources", "    testq %rax,%rax",
            "    jne .Lresource_test_fail",
            "    call erist_rt_live_failures",
            "    testq %rax,%rax" if close_fails else "    cmpq $0,%rax",
            "    je .Lresource_test_fail" if close_fails else "    jne .Lresource_test_fail",
            "    movq $0,32(%rsp)", "    movq $0,48(%rsp)",
            "    call evn_void", "    movq %rax,%rsi",
            "    movq 64(%rsp),%rdi", "    call evn_scope_leave",
            "    call evn_void", "    movq %rax,%rsi",
            "    movq 56(%rsp),%rdi", "    call evn_scope_leave",
            "    addq $96,%rsp", "    call .Lresource_finish",
            "    xorl %edi,%edi", "    jmp erist_rt_exit",
            ".section .rodata", ".Lowner_class:", ".byte 1",
            ".Lfile:", ".byte " + ",".join(str(v) for v in str(path).encode("utf-8")),
            ".Lfile_end:",
        ]
        return emitted + "\n".join(lines) + "\n" + resource.FINISH

    def test_file_checked_failure_publishes_typed_root_through_forced_gc(self):
        emitted = self.emit()
        self.assertIn("erist_u2_checked_51:", emitted)
        self.assertIn("erist_u2_bind_51:", emitted)
        self.assertIn("call erist_u2_publish_51_4", emitted)
        self.assertIn("call erist_u2_release_51_4", emitted)
        self.assertIn("cmpq $0,24(%r14)", emitted)
        path = self.directory / "u2-checked-failure-file.txt"
        path.write_text("file", encoding="utf-8")
        for close_fails in (False, True):
            with self.subTest(close_fails=close_fails):
                runtime = (resource.close_failures(self.runtime) if close_fails
                           else self.runtime)
                assembly = self.native_assembly(emitted, path, close_fails)
                run = self.run_probe("u2-checked-roots-" + str(int(close_fails)),
                                     assembly, runtime=runtime)
                self.assertEqual((run.returncode, run.stdout, run.stderr),
                                 (0, b"", b""))
