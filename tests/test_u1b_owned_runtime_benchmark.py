"""Opt-in matched owned-runtime baseline versus isolated safe-point candidate.

One original unmodified U1b linked fixture, one frontend/assembly, two separately
linked native runtimes. Candidate replaces only a pure live-slot accessor call
inside the safe point with an exact direct load of the SAME private counter.
No collection frequency, safety rule, object layout, budget or ABI is changed.
Pilot 1 pair then final 5 alternating fresh-process pairs; exact oracle parity.
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import statistics
import subprocess
import tempfile
import time
import unittest
from compiler.erist.cli import build_native
from u1_native_tools import shared_u1_compilers

ROOT = Path(__file__).resolve().parents[1]
OLD = ("    call erist_rt_slots_live\n"
       "    movq %rax,%rcx\n"
       "    addq $256,%rcx")
NEW = ("    movq .Lvalue_slot_count(%rip),%rax\n"
       "    movq %rax,%rcx\n"
       "    addq $256,%rcx")


def candidate_runtime(runtime):
    if runtime.count(OLD) != 1:
        raise AssertionError("safe-point exact accessor anchor changed")
    if runtime.count("erist_rt_slots_live:") != 1:
        raise AssertionError("live-slot accessor symbol changed")
    if runtime.count(".Lvalue_slot_count:") != 1:
        raise AssertionError("private slot counter layout changed")
    return runtime.replace(OLD, NEW, 1)


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


class U1BOwnedRuntimeBenchmark(unittest.TestCase):
    def test_same_assembly_original_vs_single_safe_point_optimization(self):
        pairs = int(os.environ.get("ERISTAVI_U1B_BENCH_PAIRS", "0"))
        if pairs not in (1,5):
            self.skipTest("opt-in U1b pilot 1 pair or qualification 5 pairs")
        if platform.system() != "Linux" or platform.machine().lower() not in ("x86_64","amd64"):
            self.skipTest("owned native runtime requires Linux x86-64")
        if not shutil.which("as") or not shutil.which("ld"):
            self.skipTest("as and ld required")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/"compiler").symlink_to(ROOT/"src/compiler", target_is_directory=True)
            original = (ROOT/"tests/fixtures/u1_aggregate_calls.eri").read_text()
            source = root/"program.eri"
            source.write_text(original)
            bootstrap = root/"bootstrap"
            self.assertEqual(build_native(source, bootstrap, root), 0)
            reference = subprocess.run([str(bootstrap)],capture_output=True,
                text=True,timeout=120)
            self.assertEqual((reference.returncode,reference.stderr),(0,""))
            self.assertIn("u1b-aggregate-calls:ok",reference.stdout)

            frontend, generator = shared_u1_compilers()
            compiled = subprocess.run([str(frontend),"emit-asm",str(source),
                "--source-root",str(root),"--target","x86_64-linux"],
                capture_output=True,text=True,timeout=240)
            self.assertEqual((compiled.returncode,compiled.stderr),(0,""))
            runtime = subprocess.run([str(generator)],capture_output=True,
                text=True,timeout=120)
            self.assertEqual((runtime.returncode,runtime.stderr),(0,""))
            candidate = candidate_runtime(runtime.stdout)
            (root/"app.s").write_text(compiled.stdout)
            subprocess.run(["as","--64",str(root/"app.s"),"-o",str(root/"app.o")],
                capture_output=True,check=True,timeout=60)
            binaries = {}
            for label, assembly in (("baseline",runtime.stdout),("optimized",candidate)):
                asm = root/(label+".s")
                asm.write_text(assembly)
                subprocess.run(["as","--64",str(asm),"-o",str(root/(label+".o"))],
                    capture_output=True,check=True,timeout=60)
                exe = root/label
                subprocess.run(["ld","-nostdlib","-static","-e","_start",
                    str(root/"app.o"),str(root/(label+".o")),"-o",str(exe)],
                    capture_output=True,check=True,timeout=60)
                binaries[label] = exe
            samples = {"baseline":[],"optimized":[]}
            for pair in range(pairs):
                order = ("baseline","optimized") if pair%2 == 0 else ("optimized","baseline")
                for name in order:
                    started = time.perf_counter()
                    result = subprocess.run([str(binaries[name])],
                        capture_output=True,text=True,timeout=240)
                    seconds = time.perf_counter()-started
                    self.assertEqual((result.returncode,result.stderr,result.stdout),
                        (reference.returncode,reference.stderr,reference.stdout),
                        f"{name} pair={pair+1}")
                    samples[name].append(seconds)
            medians = {k:statistics.median(v) for k,v in samples.items()}
            print("U1B_OWNED_SAFEPOINT_PAIRED=" + json.dumps({
                "scope":"Same exact generated source assembly; original owned runtime "
                        "vs one safe-point exact counter load. Uninstrumented process "
                        "wall times include startup/OS noise. No source semantics, "
                        "ABI, memory budget, collector thresholds, or root changes.",
                "pairs":pairs,"order":"AB" if pairs == 1 else "AB/BA/AB/BA/AB",
                "duration_seconds":samples,"median_seconds":medians,
                "ratio_candidate_over_baseline":
                     medians["optimized"]/medians["baseline"],
                "speedup_baseline_over_candidate":
                     medians["baseline"]/medians["optimized"],
                "runtime_source_sha256":digest(runtime.stdout),
                "candidate_assembly_sha256":digest(candidate),
                "application_assembly_sha256":digest(compiled.stdout),
                "fixture_sha256":digest(original),
                "strict_C_bootstrap_stdout_and_exit_parity":True,
                "candidate_change":"inline readonly .Lvalue_slot_count load "
                                   "instead of calling pure erist_rt_slots_live",
            },sort_keys=True),flush=True)


if __name__ == "__main__": unittest.main()
