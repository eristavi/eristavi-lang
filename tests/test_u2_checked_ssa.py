"""Canonical U2 opcode-46 carried SSA File.close dispatch on the owned runtime."""
from pathlib import Path
import platform
import re
import subprocess
import unittest

from compiler.erist.cli import build_native
import test_freestanding_resource_values as resource

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(platform.system() == "Linux" and
                     platform.machine().lower() in ("x86_64", "amd64"),
                     "canonical checked SSA native regression needs Linux x86-64")
class U2CheckedSSATests(unittest.TestCase):
    setUpClass = classmethod(resource.FreestandingResourceValueTests.setUpClass.__func__)
    run_probe = resource.FreestandingResourceValueTests.run_probe

    def generator(self):
        folder = self.directory / "u2-canonical-ssa-generator"
        folder.mkdir(exist_ok=True)
        link = folder / "compiler"
        target = (ROOT / "src/compiler").resolve()
        if link.is_symlink():
            self.assertEqual(link.resolve(), target)
        else:
            self.assertFalse(link.exists())
            link.symlink_to(target, target_is_directory=True)
        file = folder / "app.eri"
        file.write_text(
            (ROOT / "tests/fixtures/u2_checked_ssa.eri").read_text(encoding="utf-8"),
            encoding="utf-8")
        binary = folder / "generator"
        self.assertEqual(build_native(file, binary, folder), 0)
        result = subprocess.run([str(binary)], capture_output=True,
                                text=True, timeout=120)
        self.assertEqual((result.returncode, result.stderr), (0, ""),
                         result.stdout[-2400:])
        emitted = result.stdout
        for symbol in ("erist_u2_ssa_61:", "erist_u2_cleanup_61:",
                       "erist_u2_bind_61:"):
            self.assertIn(symbol, emitted)
        self.assertNotIn("erist_u2_ssa_62:", emitted)
        self.assertNotIn("erist_u2_cleanup_62:", emitted)
        return emitted

    def offsets(self, emission):
        def first(pattern):
            result = re.search(pattern, emission, re.M)
            self.assertIsNotNone(result, pattern)
            return result
        source = int(first(r"^    movq (\d+)\(%r15\),%rbx$").group(1))
        normal = int(first(r"^    movq %rbx,(\d+)\(%r15\)$").group(1))
        failure_match = first(
            r"^    movq %r13,(\d+)\(%r15\)\n    movq %rbx,(\d+)\(%r15\)$")
        failure, failure_carry = map(int, failure_match.groups())
        root = int(first(r"^    cmpq \$0,(\d+)\(%r14\)$").group(1))
        published = re.findall(
            r"^\.globl erist_u2_publish_61_(\d+)$",emission,re.M)
        self.assertEqual(len(published),2)
        self.assertEqual(len(set(published)),2)
        self.assertIn("call erist_u2_publish_61_"+published[1],emission)
        self.assertIn("call erist_u2_release_61_"+published[1],emission)
        self.assertEqual(len({source,normal,failure,failure_carry}),4)
        for offset in (source,normal,failure,failure_carry):
            self.assertEqual(offset%8,0)
            self.assertGreaterEqual(offset,0)
            self.assertLess(offset,160)
        self.assertEqual(root,8)
        return source,normal,failure,failure_carry,root

    def assembly(self, emission, path, pending, failing, offsets):
        source,normal,failed,failed_carry,root=offsets
        frame=80
        status=-1 if failing else 0
        lines=[
            ".text", ".globl _start", "_start:",
            "    subq $256,%rsp",
            "    movq $0,0(%rsp)","    movq $0,48(%rsp)",
            "    call evn_scope_enter","    movq %rax,56(%rsp)",
            "    movq %rax,%rdi","    movq %rsp,%rsi",
            "    leaq .Lowner_classes(%rip),%rdx","    movl $1,%ecx",
            "    call evn_bind_roots",
            "    call evn_scope_enter","    movq %rax,64(%rsp)",
            "    movq %rax,%rdi","    leaq 8(%rsp),%rsi",
            "    call erist_u2_bind_61",
            "    leaq .Lfile(%rip),%rdi",
            "    movl $(.Lfile_end-.Lfile),%esi",
            "    call evn_text","    movq %rax,%rsi",
            "    movl $9,%edi","    xorl %edx,%edx",
            "    call erist_rt_file_open","    movq %rax,0(%rsp)",
            "    call evn_empty_failure","    movq %rax,48(%rsp)",
            "    movq $"+str(pending)+","+str(frame+source)+"(%rsp)",
            "    movq %rsp,%rdi","    movq 48(%rsp),%rsi",
            "    leaq 8(%rsp),%rdx","    leaq 80(%rsp),%rcx",
            "    call erist_u2_ssa_61",
            "    cmpq $"+str(status)+",%rax",
            "    jne .Lresource_test_fail",
            "    cmpq $0,0(%rsp)","    jne .Lresource_test_fail",
        ]
        if failing:
            lines += [
                "    cmpq $0,"+str(frame+normal)+"(%rsp)",
                "    jne .Lresource_test_fail",
                "    movq "+str(frame+failed)+"(%rsp),%rax",
                "    cmpq %rax,48(%rsp)","    jne .Lresource_test_fail",
                "    cmpq $"+str(pending)+","+str(frame+failed_carry)+"(%rsp)",
                "    jne .Lresource_test_fail",
                "    cmpq %rax,"+str(8+root)+"(%rsp)",
                "    jne .Lresource_test_fail",
                "    cmpq $0,(%rax)","    je .Lresource_test_fail",
            ]
        else:
            lines += [
                "    cmpq $"+str(pending)+","+str(frame+normal)+"(%rsp)",
                "    jne .Lresource_test_fail",
                "    cmpq $0,"+str(frame+failed)+"(%rsp)",
                "    jne .Lresource_test_fail",
                "    cmpq $0,"+str(frame+failed_carry)+"(%rsp)",
                "    jne .Lresource_test_fail",
                "    cmpq $0,"+str(8+root)+"(%rsp)",
                "    jne .Lresource_test_fail",
            ]
        lines += [
            "    xorl %edi,%edi","    call erist_rt_slots_collect",
            "    call erist_rt_text_collect",
            "    call erist_rt_open_resources",
            "    testq %rax,%rax","    jne .Lresource_test_fail",
            "    call erist_rt_live_failures",
            "    testq %rax,%rax",
            "    je .Lresource_test_fail" if failing else
            "    jne .Lresource_test_fail",
            "    movq $0,"+str(8+root)+"(%rsp)",
            "    movq $0,48(%rsp)",
            "    movq $0,"+str(frame+failed)+"(%rsp)",
            "    call evn_void","    movq %rax,%rsi",
            "    movq 64(%rsp),%rdi","    call evn_scope_leave",
            "    call evn_void","    movq %rax,%rsi",
            "    movq 56(%rsp),%rdi","    call evn_scope_leave",
            "    addq $256,%rsp",
            "    call .Lresource_finish",
            "    xorl %edi,%edi","    jmp erist_rt_exit",
            ".section .rodata",".Lowner_classes:",".byte 1",
            ".Lfile:",".byte "+
              ",".join(str(v) for v in str(path).encode("utf-8")),
            ".Lfile_end:"
        ]
        return emission+"\n".join(lines)+"\n"+resource.FINISH

    def test_verified_ssa_edges_dispatch_success_and_failure_with_forced_gc(self):
        emission=self.generator()
        offsets=self.offsets(emission)
        path=self.directory/"u2-ssa-dispatch.txt"
        path.write_text("file",encoding="utf-8")
        for pending in (0,74565,-19):
            for failing in (False,True):
                with self.subTest(pending=pending,failing=failing):
                    runtime=(resource.close_failures(self.runtime) if failing
                             else self.runtime)
                    native=self.assembly(emission,path,pending,failing,offsets)
                    result=self.run_probe(
                        "u2-ssa-"+str(pending)+"-"+str(int(failing)),
                        native,runtime=runtime)
                    self.assertEqual(
                        (result.returncode,result.stdout,result.stderr),
                        (0,b"",b""))
