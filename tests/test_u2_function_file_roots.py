"""Opt-in whole-Function File owner root emission and consumption probes.

This checks original canonical ownership -> native GC root helpers only.
It deliberately does not claim integrated File acquire, close, handler, or
automatic whole-Function resource cleanup in the production emitter.
"""
from pathlib import Path
import platform
import re
import shutil
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native
import test_freestanding_resource_values as resource

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(
    platform.system() == "Linux" and platform.machine().lower() in ("x86_64", "amd64"),
    "private x86-64 File roots require Linux x86-64",
)
class U2WholeFunctionFileRootTests(unittest.TestCase):
    setUpClass=classmethod(resource.FreestandingResourceValueTests.setUpClass.__func__)
    run_probe=resource.FreestandingResourceValueTests.run_probe
    def test_verified_lexical_owner_roots_cover_every_original_block_and_consumption(self):
        source = (ROOT / "tests/fixtures/u2_scoped_owners.eri").read_text(
            encoding="utf-8")
        imports = "import compiler.u2_scoped_owners as owners;"
        self.assertEqual(source.count(imports), 1)
        source = source.replace(
            imports,
            imports + "\nimport compiler.u2_function_file_roots_x86_64 as fileRoots;",
            1)
        marker = (
            "let mutate be try budget.constructionPhase(owner); "
            "let revision be fn.revision;"
        )
        self.assertEqual(source.count(marker), 1)
        source = source.replace(
            marker,
            marker + "\n    try fileRoots.emit(fn,graph,profile,table,mutate,717);",
            1)
        failures = "continuation.InvalidBinding,owners.InvalidOwnership,ProbeError {"
        self.assertEqual(source.count(failures), 1)
        source = source.replace(
            failures,
            "continuation.InvalidBinding,owners.InvalidOwnership,"
            "fileRoots.Unsupported,ProbeError {",
            1)
        handler = 'else error ProbeError { output("probe:"+error.message);'
        self.assertEqual(source.count(handler), 1)
        source = source.replace(
            handler,
            'else error fileRoots.Unsupported { output("file-roots:"+error.message); '
            'process.setExitCode(1); }\n' + handler,
            1)
        for tool in ("as", "nm"):
            if not shutil.which(tool):
                self.skipTest(tool + " unavailable")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "compiler").symlink_to(
                ROOT / "src/compiler", target_is_directory=True)
            entry = root / "probe.eri"
            entry.write_text(source, encoding="utf-8")
            binary = root / "generator"
            self.assertEqual(build_native(entry, binary, root), 0)
            result = subprocess.run(
                [str(binary)], capture_output=True, text=True, timeout=120)
            self.assertEqual(
                (result.returncode, result.stderr), (0, ""), result.stdout[-1600:])
            suffix = "u2-scoped-owners:ok\n"
            self.assertTrue(result.stdout.endswith(suffix), result.stdout[-1200:])
            emitted = result.stdout[:-len(suffix)]
            base = "erist_u2_file_717"
            self.assertIn(base + "_bind:", emitted)
            self.assertEqual(len(re.findall(
                "^    \\.byte 1$", emitted, re.M)), 2)
            blocks = re.findall(
                r"^" + base + r"_publish_(\d+):$", emitted, re.M)
            self.assertEqual(blocks, [str(i) for i in range(1, 12)])
            closes = re.findall(
                r"^" + base + r"_poison_(\d+):$", emitted, re.M)
            self.assertEqual(len(closes), 3)
            self.assertEqual(len(set(closes)), 3)
            # Acquisition does not begin with a live owner and the nested
            # signature publishes both outer and inner owners.
            block1 = emitted.split(base + "_publish_1:", 1)[1].split(
                ".size " + base + "_publish_1", 1)[0]
            self.assertIn("movq $0,0(%rsi)", block1)
            self.assertIn("movq $0,8(%rsi)", block1)
            block3 = emitted.split(base + "_publish_3:", 1)[1].split(
                ".size " + base + "_publish_3", 1)[0]
            self.assertIn("movq %rax,0(%rsi)", block3)
            self.assertIn("movq %rax,8(%rsi)", block3)
            # Assemble only the emitted helpers; unresolved external
            # runtime references are permitted at the .o stage.
            asm = root / "roots.s"
            asm.write_text(emitted, encoding="utf-8")
            obj = root / "roots.o"
            assembled = subprocess.run(
                ["as", "--64", str(asm), "-o", str(obj)],
                capture_output=True, text=True, timeout=60)
            self.assertEqual(
                (assembled.returncode, assembled.stderr), (0, ""),
                assembled.stdout + assembled.stderr)
            symbols = subprocess.run(
                ["nm", str(obj)], capture_output=True, text=True,
                check=True, timeout=60).stdout
            self.assertIn(base + "_publish_3", symbols)
            self.assertIn(base + "_poison_", symbols)
            # Execute real owned File.open/close with actual machine-produced
            # owner slots, live class-1 roots, forced collectors and post-scope
            # reclamation. These are test-controlled canonical transitions,
            # not automatic whole-Function File lowering.
            paths = [self.directory / ("u2-owned-file-" + str(i) + ".txt")
                     for i in range(2)]
            for file in paths:
                file.write_text("rooted", encoding="utf-8")
            data = ""
            for index, file in enumerate(paths):
                encoded = str(file).encode("utf-8")
                data += (".Lfile" + str(index) + ":\n.byte " +
                         ",".join(str(byte) for byte in encoded) +
                         "\n.Lfile" + str(index) + "_end:\n")
            test_asm = r"""
.text
.globl _start
_start:
    subq $176,%rsp
    movq $0,136(%rsp)
    call evn_scope_enter
    movq %rax,152(%rsp)
    movq %rax,%rdi
    leaq 112(%rsp),%rsi
    call erist_u2_file_717_bind
    # One registered class-5 root for the checked cleanup accumulator.
    call evn_scope_enter
    movq %rax,160(%rsp)
    movq %rax,%rdi
    leaq 136(%rsp),%rsi
    leaq .Lu2_failure_classes(%rip),%rdx
    movl $1,%ecx
    call evn_bind_roots
    call evn_empty_failure
    movq %rax,136(%rsp)
    # Block 1 acquires the outer File and transitions to owner block 2.
    leaq .Lfile0(%rip),%rdi
    movl $(.Lfile0_end-.Lfile0),%esi
    call evn_text
    movq %rax,%rsi
    movl $9,%edi
    xorl %edx,%edx
    call erist_rt_file_open
    movq %rax,0(%rsp)
    movq %rsp,%rdi
    leaq 112(%rsp),%rsi
    call erist_u2_file_717_publish_2
    xorl %edi,%edi
    call erist_rt_slots_collect
    call erist_rt_text_collect
    call erist_rt_open_resources
    cmpq $1,%rax
    jne .Lresource_test_fail
    # Block 2 acquires a nested File, moves the outer owner to block 3.
    movq 0(%rsp),%rax
    movq %rax,16(%rsp)
    movq $0,0(%rsp)
    leaq .Lfile1(%rip),%rdi
    movl $(.Lfile1_end-.Lfile1),%esi
    call evn_text
    movq %rax,%rsi
    movl $9,%edi
    xorl %edx,%edx
    call erist_rt_file_open
    movq %rax,8(%rsp)
    movq %rsp,%rdi
    leaq 112(%rsp),%rsi
    call erist_u2_file_717_publish_3
    xorl %edi,%edi
    call erist_rt_slots_collect
    call erist_rt_text_collect
    call erist_rt_open_resources
    cmpq $2,%rax
    jne .Lresource_test_fail
    # The inner original checked File.close consumes its canonical handle
    # and registered innermost lexical root before exiting block 3.
    movq 8(%rsp),%rdi
    movq 136(%rsp),%rsi
    call evn_cleanup_accumulate
    movq %rsp,%rdi
    leaq 112(%rsp),%rsi
    call erist_u2_file_717_poison___INNER__
    movq 16(%rsp),%rax
    movq %rax,24(%rsp)
    movq $0,16(%rsp)
    movq %rsp,%rdi
    leaq 112(%rsp),%rsi
    call erist_u2_file_717_publish_5
    xorl %edi,%edi
    call erist_rt_slots_collect
    call erist_rt_text_collect
    call erist_rt_open_resources
    cmpq $1,%rax
    jne .Lresource_test_fail
    # The final checked File.close consumes the remaining outer owner.
    movq 24(%rsp),%rdi
    movq 136(%rsp),%rsi
    call evn_cleanup_accumulate
    movq %rsp,%rdi
    leaq 112(%rsp),%rsi
    call erist_u2_file_717_poison___OUTER__
    movq %rsp,%rdi
    leaq 112(%rsp),%rsi
    call erist_u2_file_717_publish_7
    movq 136(%rsp),%rax
    cmpq $0,(%rax)
    jne .Lresource_test_fail
    xorl %edi,%edi
    call erist_rt_slots_collect
    call erist_rt_text_collect
    call erist_rt_open_resources
    testq %rax,%rax
    jne .Lresource_test_fail
    # Leave the failure-root scope followed by the File owner scope.
    movq $0,136(%rsp)
    call evn_void
    movq %rax,%rsi
    movq 160(%rsp),%rdi
    call evn_scope_leave
    call evn_void
    movq %rax,%rsi
    movq 152(%rsp),%rdi
    call evn_scope_leave
    addq $176,%rsp
    call .Lresource_finish
    xorl %edi,%edi
    jmp erist_rt_exit
.section .rodata
.Lu2_failure_classes:
.byte 5
"""
            test_asm = (test_asm.replace("__INNER__", closes[0])
                        .replace("__OUTER__", closes[1]))
            execution = self.run_probe(
                "u2-full-function-file-owner-roots",
                emitted + test_asm + data + resource.FINISH)
            self.assertEqual(
                (execution.returncode, execution.stdout, execution.stderr),
                (0, b"", b""))


if __name__ == "__main__":
    unittest.main()
