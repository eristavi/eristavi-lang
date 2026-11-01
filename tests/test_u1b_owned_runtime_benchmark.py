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


def candidate_lookup_runtime(runtime):
    """Inline the existing bucket computation at its hottest exact-find call.

    The original hash, dynamic bucket selection, collision chain, object
    identity comparison, and result are byte-for-byte algorithmically the same.
    Only one call/return and its stack adjustment are eliminated.
    """
    start = runtime.index(".Lg_bucket:\n")
    end = runtime.index(".Lg_insert:\n", start)
    bucket = runtime[start:end]
    if bucket.count("    ret\n") != 1 or not bucket.endswith("    ret\n"):
        raise AssertionError("bucket contains unexpected returns")
    if runtime.count(".Lg_bucket:\n") != 1:
        raise AssertionError("expected one graph bucket implementation")
    body = bucket.split("\n",1)[1].removesuffix("    ret\n")
    body = body.replace(".Lg_bucket_mask", ".Lprof_find_bucket_mask")
    body = body.replace(".Lg_bucket_table", ".Lprof_find_bucket_table")
    find = (
        "erist_rt_graph_find:\n"
        "    subq $8,%rsp\n"
        "    call .Lg_bucket\n"
        "    addq $8,%rsp\n"
        "    movq (%rax),%rax\n"
    )
    if runtime.count(find) != 1:
        raise AssertionError("graph find entrypoint changed")
    for marker in (".Lprof_find_bucket_mask", ".Lprof_find_bucket_table"):
        if marker in runtime:
            raise AssertionError("private inline label already defined")
    return runtime.replace(find, "erist_rt_graph_find:\n" + body
                           + "    movq (%rax),%rax\n", 1)


def candidate_cached_lookup_runtime(runtime):
    """Cache ONLY positive exact registered graph-object pointer lookups.

    Graph objects are freed exclusively by erist_rt_graph_sweep; invalidate
    before that sweep. A miss always traverses the existing hash/index chain
    unmodified, including forced collisions and dynamic hash tables. No
    negative results are cached, so future graph creation is unaffected.
    """
    name=".Lu1b_positive_find_cache"
    if name in runtime:
        raise AssertionError("private cache symbol already present")
    start=(
        "erist_rt_graph_find:\n"
        "    subq $8,%rsp\n"
        "    call .Lg_bucket\n"
        "    addq $8,%rsp\n"
    )
    if runtime.count(start) != 1:
        raise AssertionError("graph-find entrypoint changed")
    runtime = runtime.replace(start,
        "erist_rt_graph_find:\n"
        "    cmpq %rdi,.Lu1b_positive_find_cache(%rip)\n"
        "    jne .Lu1b_positive_find_miss\n"
        "    movq %rdi,%rax\n"
        "    ret\n"
        ".Lu1b_positive_find_miss:\n"
        "    subq $8,%rsp\n"
        "    call .Lg_bucket\n"
        "    addq $8,%rsp\n", 1)
    done = ".Lg_find_done:\n    ret\n"
    if runtime.count(done) != 1:
        raise AssertionError("graph-find return anchor changed")
    runtime = runtime.replace(done,
        ".Lg_find_done:\n"
        "    testq %rax,%rax\n"
        "    je .Lu1b_positive_find_return\n"
        "    movq %rax,.Lu1b_positive_find_cache(%rip)\n"
        ".Lu1b_positive_find_return:\n"
        "    ret\n", 1)
    sweep = "erist_rt_graph_sweep:\n"
    if runtime.count(sweep) != 1:
        raise AssertionError("GC sweep entrypoint changed")
    runtime = runtime.replace(sweep,
        sweep+"    movq $0,.Lu1b_positive_find_cache(%rip)\n", 1)
    runtime += (
        "\n.bss\n.p2align 3\n"
        ".Lu1b_positive_find_cache:\n.quad 0\n"
    )
    return runtime


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
            variant = os.environ.get("ERISTAVI_U1B_CANDIDATE", "safepoint")
            self.assertIn(variant, ("safepoint", "graph_find", "positive_cache"))
            candidate = (candidate_runtime(runtime.stdout) if variant == "safepoint"
                         else candidate_lookup_runtime(runtime.stdout) if variant == "graph_find"
                         else candidate_cached_lookup_runtime(runtime.stdout))
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
            print("U1B_OWNED_MATCHED_PAIRED=" + json.dumps({
                "candidate":variant,
                "scope":"Same exact generated source assembly, original owned runtime "
                        "versus one private, explicitly named runtime candidate. "
                        "Uninstrumented native process wall times; output and exit "
                        "match independent C-bootstrap. Candidate never changes "
                        "source semantics, 32-byte ABI, memory admission budgets, "
                        "collector schedule or root traversal policy.",
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
                "candidate_change":(
                    "inline readonly .Lvalue_slot_count load instead of "
                    "calling pure erist_rt_slots_live" if variant=="safepoint" else
                    "inline existing graph bucket hash and table selection "
                    "into erist_rt_graph_find, preserve all collisions/identity"
                    if variant == "graph_find" else
                    "cache positive exact graph pointer, invalidate at GC sweep; "
                    "fall back to original collision-safe lookup on misses"),
            },sort_keys=True),flush=True)


if __name__ == "__main__": unittest.main()
