"""Opt-in actual allocator/GC evidence for linked U1b recursive frames.

This observes actual owned-runtime graph allocation capacity and reclamation
under diagnostic allocation tag 103. The 201..205 semantic backing counters
are populated only by a separate graph-equality observer, not by tag 103.
The tag spans setup, linked execution and teardown, not isolated frame bytes
or process RSS. A reachable 4-cell graph remains marked at process exit;
only unreachable tagged allocations are required to be reclaimed.
"""
from pathlib import Path
import shutil
import platform
import struct
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native
from u1_native_tools import shared_u1_compilers
from test_u1_owner_physical import _decode_owner_records, _instrument_owned_runtime

ROOT = Path(__file__).resolve().parents[1]


class U1BLinkedActualPhysicalTests(unittest.TestCase):
    def test_linked_recursive_actual_allocator_reclamation(self):
        if platform.system() != "Linux" or platform.machine().lower() not in ("x86_64", "amd64"):
            self.skipTest("freestanding x86-64 assembler and runtime require Linux x86-64")
        for command in ("as", "ld"):
            if shutil.which(command) is None:
                self.skipTest(f"{command} unavailable")
        original = (ROOT / "tests/fixtures/u1_aggregate_calls.eri").read_text()
        self.assertIn("import std.process;", original)
        anchor = "    let root be try budget.developmentRequest();"
        close = "    try budget.close(shared); try budget.close(root);"
        self.assertEqual(original.count(anchor), 1)
        self.assertEqual(original.count(close), 1)
        # Tag actual allocator activity across every normal, fault and bounded
        # refusal request; restore exit status before the program terminates.
        fixture = original.replace(anchor, "    process.setExitCode(103);\n" + anchor, 1)
        fixture = fixture.replace(close, close + "\n    process.setExitCode(0);", 1)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "compiler").symlink_to(ROOT / "src/compiler", target_is_directory=True)
            source = root / "linked-physical.eri"
            source.write_text(fixture)
            bootstrap = root / "linked-bootstrap"
            self.assertEqual(build_native(source, bootstrap, root), 0)
            baseline = subprocess.run([str(bootstrap)], capture_output=True,
                                      text=True, timeout=180, check=False)
            self.assertEqual((baseline.returncode, baseline.stderr), (0, ""))
            self.assertIn("u1b-aggregate-calls:ok", baseline.stdout)
            frontend, generator = shared_u1_compilers()
            emitted = subprocess.run(
                [str(frontend), "emit-asm", str(source), "--source-root",
                 str(root), "--target", "x86_64-linux"],
                capture_output=True, text=True, timeout=180, check=False)
            self.assertEqual((emitted.returncode, emitted.stderr), (0, ""))
            runtime = subprocess.run([str(generator)], capture_output=True,
                                     text=True, timeout=90, check=False)
            self.assertEqual((runtime.returncode, runtime.stderr), (0, ""))
            app = root / "app.s"
            app.write_text(emitted.stdout)
            subprocess.run(["as", "--64", str(app), "-o", str(root / "app.o")],
                           check=True, capture_output=True, timeout=30)

            def link(name, assembly):
                path = root / (name + ".s")
                path.write_text(assembly)
                obj = root / (name + ".o")
                subprocess.run(["as", "--64", str(path), "-o", str(obj)],
                               check=True, capture_output=True, timeout=30)
                exe = root / name
                subprocess.run(["ld", "-nostdlib", "-static", "-e", "_start",
                                str(root / "app.o"), str(obj), "-o", str(exe)],
                               check=True, capture_output=True, timeout=30)
                return exe

            owned = subprocess.run([str(link("linked-owned", runtime.stdout))],
                                   capture_output=True, text=True, timeout=180, check=False)
            self.assertEqual((owned.returncode, owned.stderr, owned.stdout),
                             (0, "", baseline.stdout))
            with (root / "actual.bin").open("wb") as dump:
                instrumented = _instrument_owned_runtime(
                    runtime.stdout, dump.fileno(), force_identity_collisions=True)
                # Diagnose whether the final 224-byte survivor is a stale
                # conservative root released by one more quiescent collection.
                tail = ("    call erist_rt_text_collect\n"
                        "    call .Ltest_owner_write\n"
                        "    movq .Lprocess_exit_code")
                self.assertEqual(instrumented.count(tail), 1)
                instrumented = instrumented.replace(tail,
                    "    call erist_rt_text_collect\n"
                    "    call erist_rt_text_collect\n"
                    "    call .Ltest_owner_write\n"
                    "    movq .Lprocess_exit_code", 1)
                # Diagnostic-only survivor scan: record each live tag-103
                # allocation pointer, allocator capacity, graph cell count,
                # and graph capacity after the final collection.
                anchor = "    call .Ltest_owner_write\n    movq .Lprocess_exit_code"
                self.assertEqual(instrumented.count(anchor), 1)
                instrumented = instrumented.replace(anchor,
                    "    call .Ltest_owner_write\n    call .Ltest_linked_survivor_write\n    movq .Lprocess_exit_code", 1)
                instrumented += f"""\n.text\n.Ltest_linked_survivor_write:\n    xorq %r12,%r12\n    leaq .Ltest_owner_tags(%rip),%r13\n    leaq .Ltest_owner_keys(%rip),%r14\n    leaq .Ltest_owner_sizes(%rip),%r15\n.Ltest_linked_survivor_loop:\n    cmpq $262144,%r12\n    jae .Ltest_linked_survivor_done\n    cmpq $3,(%r13,%r12,8)\n    jne .Ltest_linked_survivor_next\n    movq (%r14,%r12,8),%rbx\n    subq $48,%rsp\n    movq %rbx,0(%rsp)\n    movq (%r15,%r12,8),%rax\n    movq %rax,8(%rsp)\n    movq 0(%rbx),%rax\n    movq %rax,16(%rsp)\n    movq 48(%rbx),%rax\n    movq %rax,24(%rsp)\n    movq 24(%rbx),%rax\n    movq %rax,32(%rsp)\n    movq 8(%rbx),%rax\n    movq %rax,40(%rsp)\n    movq $1,%rax\n    movq ${dump.fileno()},%rdi\n    movq %rsp,%rsi\n    movq $48,%rdx\n    syscall\n    addq $48,%rsp\n.Ltest_linked_survivor_next:\n    incq %r12\n    jmp .Ltest_linked_survivor_loop\n.Ltest_linked_survivor_done:\n    ret\n"""
                observed = link("linked-observed", instrumented)
                result = subprocess.run([str(observed)], pass_fds=(dump.fileno(),),
                                        capture_output=True, text=True, timeout=180,
                                        check=False)
            self.assertEqual((result.returncode, result.stderr, result.stdout),
                             (0, "", baseline.stdout))
            from test_u1_owner_physical import RECORD_BYTES
            raw = (root / "actual.bin").read_bytes()
            before, after = _decode_owner_records(raw[:2 * RECORD_BYTES])
            tail = raw[2 * RECORD_BYTES:]
            self.assertEqual(len(tail) % 48, 0)
            survivors = [dict(zip(("pointer", "allocator_bytes", "cells", "capacity", "marked", "cell_pointer"),
                        struct.unpack_from("<QQQQQQ", tail, i)))
                         for i in range(0, len(tail), 48)]
            print("U1B_LINKED_SURVIVORS=" + __import__("json").dumps(survivors), flush=True)
            self.assertEqual((before["error"], after["error"]), (0, 0))
            # The diagnostic tag is active for every linked request, including
            # recursive execution and all bounded failure paths.
            function = before["owners"]["function"]
            final = after["owners"]["function"]
            self.assertGreater(function["allocations"], 0)
            self.assertGreater(function["traffic"], 0)
            self.assertGreater(function["peak"], 0)
            self.assertLessEqual(function["peak"], function["traffic"])
            print("U1B_LINKED_DIAGNOSTIC=" + __import__("json").dumps({"before": before, "after": after}, sort_keys=True), flush=True)
            # This complete-program fixture retains one reachable 4-cell
            # graph at process exit (GC mark=1). Do not mistake a live root
            # for an unreachable leak, or silently exempt any other object.
            self.assertEqual(len(survivors), 1)
            self.assertEqual((survivors[0]["allocator_bytes"],
                              survivors[0]["cells"], survivors[0]["capacity"],
                              survivors[0]["marked"]), (224, 4, 4, 1))
            self.assertEqual(final["live"], sum(item["allocator_bytes"] for item in survivors))
            self.assertEqual(final["reclaimed_bytes"] + final["live"], function["traffic"])
            self.assertEqual(final["reclaimed_objects"] + len(survivors), function["allocations"])
            # Semantic backing requires independent 201..205 equality tagging.
            # Never mistake its zero counters for zero allocator activity.
            self.assertEqual(before["backing"]["function"]["objects"], 0)
            print("U1B_LINKED_ACTUAL=" + __import__("json").dumps({
                "scope": "Actual allocation-history capacity (tag 103) over linked setup, recursive frames, aggregate execution and cleanup; not semantic backing (tags 201..205), isolated frame attribution or RSS",
                "before_gc": function,
                "after_gc": final,
                "original_owner_gates": {"peak_bytes": 8388608, "traffic_bytes": 67108864},
            }, sort_keys=True), flush=True)


if __name__ == "__main__":
    unittest.main()
