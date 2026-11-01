"""Opt-in U1b full-fixture phase/collector/allocator instrumentation (Linux x86-64).

All edits are to disposable Eristavi module copies and generated runtime ASM.
Counters/clock snapshots go to a private fd; no production ABI/GC/compiler change.
Diagnostic clocks include observer overhead and must not be used as speedups.
"""
import json
import os
from pathlib import Path
import platform
import shutil
import struct
import subprocess
import tempfile
import time
import unittest
from compiler.erist.cli import build_native
from u1_native_tools import shared_u1_compilers

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ("tag", "time_ns", "gc", "gc_time_ns", "owners", "finds", "index",
          "alloc", "graphs", "slots", "safe", "sweeps", "live_graphs")
SIZE = len(FIELDS) * 8
PHASES = {0: "other_setup_refusals_teardown", 21: "seal_verification",
          22: "ingress_reverification", 23: "aggregate_engine_and_type_validation",
          24: "linked_aggregate_execution", 25: "engine_close"}


def patch(s, old, new):
    assert s.count(old) == 1, "diagnostic anchor changed: " + old[:85]
    return s.replace(old, new, 1)


def traced_source(fixture, mod):
    fixture = patch(
        fixture,
        '    try check((try call.seal(program)) == 4,"all canonical declarations verified");',
        '    process.setExitCode(21);\n'
        '    try check((try call.seal(program)) == 4,"all canonical declarations verified");\n'
        '    process.setExitCode(0);')
    fixture = patch(fixture,
        "    else error budget.LimitError { return error.category == expected; }",
        "    else error budget.LimitError { process.setExitCode(0); return error.category == expected; }")
    fixture = patch(fixture,
        "    else error verify.InvalidIR { fail error; };\n    return false;\n}",
        "    else error verify.InvalidIR { process.setExitCode(0); fail error; };\n    return false;\n}")
    mod = patch(mod, "import compiler.u1_budget as budget;",
                "import std.process as process;\nimport compiler.u1_budget as budget;")
    mod = patch(mod,
        "    try revalidate(program);\n    let phase be try budget.constructionPhase(owner);",
        "    process.setExitCode(22);\n    try revalidate(program);\n"
        "    process.setExitCode(23);\n    let phase be try budget.constructionPhase(owner);")
    mod = patch(mod,
        "            try budget.finishPhase(phase);\n"
        '            fail verify.InvalidIR { message=error.message; category="invalid-ir";',
        "            try budget.finishPhase(phase); process.setExitCode(0);\n"
        '            fail verify.InvalidIR { message=error.message; category="invalid-ir";')
    mod = patch(mod,
        "        } else error budget.LimitError {\n"
        "            try budget.finishPhase(phase); fail error;\n"
        "        };\n    let machine be identity Machine {",
        "        } else error budget.LimitError {\n"
        "            try budget.finishPhase(phase); process.setExitCode(0); fail error;\n"
        "        };\n    process.setExitCode(24);\n"
        "    let machine be identity Machine {")
    mod = patch(mod,
        "        else error budget.LimitError {\n"
        "            try av.close(engine); try budget.finishPhase(phase); fail error;\n"
        "        };\n    try av.close(engine); try budget.finishPhase(phase);\n"
        "    return completed;",
        "        else error budget.LimitError {\n"
        "            try av.close(engine); try budget.finishPhase(phase);\n"
        "            process.setExitCode(0); fail error;\n"
        "        };\n    process.setExitCode(25);\n"
        "    try av.close(engine); try budget.finishPhase(phase);\n"
        "    process.setExitCode(0);\n    return completed;")
    fixture = patch(fixture, "    };\n}\nmain();\n",
        "    };\n    process.setExitCode(0);\n}\nmain();\n")
    return fixture, mod


def observed_asm(s, fd):
    labels = {"erist_rt_graph_owner:": "owners", "erist_rt_graph_find:": "finds",
              "erist_rt_graph_prepare_index:": "index", "erist_rt_alloc:": "alloc",
              "erist_rt_graph_new_capacity:": "graphs",
              "erist_rt_slots_collect:": "slots",
              "erist_rt_text_safe_point:": "safe",
              "erist_rt_graph_sweep:": "sweeps"}
    for label, count in labels.items():
        s = patch(s, label + "\n",
                  label + "\n    incq .Lprof_" + count + "(%rip)\n")
    s = patch(s, "erist_rt_text_collect:\n",
        "erist_rt_text_collect:\n"
        "    subq $8,%rsp\n    call .Lprof_gc_begin\n"
        "    call .Lprof_real_gc\n    call .Lprof_gc_end\n"
        "    addq $8,%rsp\n    ret\n"
        ".Lprof_real_gc:\n    incq .Lprof_gc(%rip)\n")
    s = patch(s, "    movq %rax,.Lprocess_exit_code(%rip)\n    jmp evn_void",
        "    movq %rax,.Lprocess_exit_code(%rip)\n"
        "    call .Lprof_mark\n    jmp evn_void")
    s = patch(s, "    call erist_entry\n    movq .Lprocess_exit_code(%rip),%rdi",
        "    call erist_entry\n    call .Lprof_mark\n"
        "    movq .Lprocess_exit_code(%rip),%rdi")
    regs = ("rax","rbx","rcx","rdx","rdi","rsi","r8","r9","r10",
            "r11","r12","r13","r14","r15")
    bss = [".bss\n.p2align 3", ".Lprof_clock:\n.zero 16",
           ".Lprof_record:\n.zero " + str(SIZE), ".Lprof_gc_started:\n.quad 0",
           ".Lprof_gc_time_ns:\n.quad 0"]
    bss += [".Lprof_" + name + ":\n.quad 0"
            for name in ("gc","owners","finds","index","alloc",
                         "graphs","slots","safe","sweeps")]
    asm = [".text", ".Lprof_now:", "    movl $228,%eax",
           "    movl $1,%edi", "    leaq .Lprof_clock(%rip),%rsi",
           "    syscall", "    testq %rax,%rax",
           "    jne .Lprof_clock_fail", "    movq .Lprof_clock(%rip),%rax",
           "    imulq $1000000000,%rax,%rax",
           "    addq .Lprof_clock+8(%rip),%rax", "    ret",
           ".Lprof_clock_fail:", "    ud2",
           ".Lprof_gc_begin:", "    call .Lprof_now",
           "    movq %rax,.Lprof_gc_started(%rip)", "    ret",
           ".Lprof_gc_end:", "    call .Lprof_now",
           "    subq .Lprof_gc_started(%rip),%rax",
           "    addq %rax,.Lprof_gc_time_ns(%rip)", "    ret",
           ".Lprof_mark:", "    pushfq"]
    asm += ["    pushq %" + r for r in regs]
    asm += ["    call .Lprof_now",
            "    movq .Lprocess_exit_code(%rip),%rbx",
            "    movq %rbx,.Lprof_record(%rip)",
            "    movq %rax,.Lprof_record+8(%rip)"]
    for i, field in enumerate(FIELDS[2:], 2):
        sym = (".Lprof_gc_time_ns" if field == "gc_time_ns" else
               ".Lgraph_count" if field == "live_graphs" else ".Lprof_" + field)
        asm += ["    movq " + sym + "(%rip),%rax",
                "    movq %rax,.Lprof_record+" + str(i * 8) + "(%rip)"]
    asm += ["    movl $1,%eax", "    movl $" + str(fd) + ",%edi",
            "    leaq .Lprof_record(%rip),%rsi",
            "    movl $" + str(SIZE) + ",%edx", "    syscall"]
    asm += ["    popq %" + r for r in reversed(regs)]
    asm += ["    popfq", "    ret"]
    return s + "\n" + "\n".join(bss + asm) + "\n"


def decode(raw):
    if not raw or len(raw) % SIZE: raise AssertionError("bad profile byte count")
    rec = [dict(zip(FIELDS, struct.unpack_from("<" + "Q"*len(FIELDS), raw, i)))
           for i in range(0, len(raw), SIZE)]
    stages = {}
    for a, b in zip(rec, rec[1:]):
        label = PHASES.get(a["tag"], "unexpected_tag_"+str(a["tag"]))
        stage = stages.setdefault(label, {"intervals": 0, "wall_ns": 0})
        assert b["time_ns"] >= a["time_ns"]
        stage["intervals"] += 1
        stage["wall_ns"] += b["time_ns"]-a["time_ns"]
        for k in FIELDS[2:-1]:
            assert b[k] >= a[k], (k, a, b)
            stage[k] = stage.get(k, 0) + b[k]-a[k]
    for stage in stages.values():
        stage["wall_seconds"] = stage.pop("wall_ns")/1e9
        stage["gc_seconds_inclusive"] = stage.pop("gc_time_ns", 0)/1e9
    return rec, stages


class U1BHotspotProfiler(unittest.TestCase):
    def test_full_linked_fixture_phase_event_profile(self):
        if os.environ.get("ERISTAVI_U1B_HOTSPOT") != "1":
            self.skipTest("focused profiler is opt-in")
        if platform.system() != "Linux" or platform.machine().lower() not in ("x86_64","amd64"):
            self.skipTest("freestanding profiler requires Linux x86-64")
        if not shutil.which("as") or not shutil.which("ld"): self.skipTest("as/ld absent")
        fixture = (ROOT/"tests/fixtures/u1_aggregate_calls.eri").read_text()
        module = (ROOT/"src/compiler/u1_aggregate_calls.eri").read_text()
        trace_fixture, trace_module = traced_source(fixture, module)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            standard = root/"standard"
            standard.mkdir()
            (standard/"compiler").symlink_to(ROOT/"src/compiler", target_is_directory=True)
            orig = standard/"original.eri"
            orig.write_text(fixture)
            binary = standard/"bootstrap"
            self.assertEqual(build_native(orig, binary, standard), 0)
            expected = subprocess.run([str(binary)], capture_output=True,
                text=True, timeout=100)
            self.assertEqual((expected.returncode,expected.stderr),(0,""))
            frontend, generator = shared_u1_compilers()
            runtime = subprocess.run([str(generator)],capture_output=True,
                text=True,timeout=90)
            self.assertEqual((runtime.returncode,runtime.stderr),(0,""))
            trace = root/"trace"
            trace.mkdir()
            compiler = trace/"compiler"
            compiler.mkdir()
            for item in (ROOT/"src/compiler").iterdir():
                if item.name != "u1_aggregate_calls.eri":
                    (compiler/item.name).symlink_to(item,target_is_directory=item.is_dir())
            (compiler/"u1_aggregate_calls.eri").write_text(trace_module)
            source = trace/"linked.eri"
            source.write_text(trace_fixture)
            emitted = subprocess.run([str(frontend),"emit-asm",str(source),
                "--source-root",str(trace),"--target","x86_64-linux"],
                capture_output=True,text=True,timeout=240)
            self.assertEqual((emitted.returncode,emitted.stderr),(0,""))
            (trace/"app.s").write_text(emitted.stdout)
            subprocess.run(["as","--64",str(trace/"app.s"),"-o",str(trace/"app.o")],
                check=True,capture_output=True,timeout=60)
            def link(asm, name):
                (trace/(name+".s")).write_text(asm)
                subprocess.run(["as","--64",str(trace/(name+".s")),
                    "-o",str(trace/(name+".o"))],check=True,capture_output=True,timeout=60)
                result = trace/name
                subprocess.run(["ld","-nostdlib","-static","-e","_start",
                    str(trace/"app.o"),str(trace/(name+".o")),"-o",str(result)],
                    check=True,capture_output=True,timeout=60)
                return result
            plain = link(runtime.stdout, "plain")
            parity = subprocess.run([str(plain)],capture_output=True,
                text=True,timeout=240)
            self.assertEqual((parity.returncode,parity.stderr,parity.stdout),
                (0,"",expected.stdout))
            with (trace/"counts.bin").open("wb") as dump:
                observed = link(observed_asm(runtime.stdout,dump.fileno()),"profiled")
                began = time.perf_counter()
                measured = subprocess.run([str(observed)],
                    pass_fds=(dump.fileno(),),capture_output=True,text=True,timeout=240)
                observed_seconds = time.perf_counter()-began
            self.assertEqual((measured.returncode,measured.stderr,measured.stdout),
                (0,"",expected.stdout))
            records,stages = decode((trace/"counts.bin").read_bytes())
            for name in ("seal_verification","ingress_reverification",
                         "aggregate_engine_and_type_validation","linked_aggregate_execution"):
                self.assertIn(name,stages)
            self.assertGreater(stages["linked_aggregate_execution"]["intervals"],1)
            last=records[-1]
            for name in ("gc","alloc","owners","graphs","safe"):
                self.assertGreater(last[name],0)
            print("U1B_HOTSPOT_PROFILE="+json.dumps({
                "scope":"FULL linked fixture, real owned-runtime diagnostic only;"
                " phase wall from CLOCK_MONOTONIC; GC inclusive time overlaps phases;"
                " counters instrumented; profiler speed NOT comparable to production",
                "full_output_parity":True,"observed_process_seconds":observed_seconds,
                "stages":stages,"cumulative":last,"snapshots":len(records),
            },sort_keys=True),flush=True)


if __name__ == "__main__": unittest.main()
