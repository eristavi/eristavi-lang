"""U1b opt-in matched source-accurate owned verification-storage poll pilot.

The candidate is a private overlay of compiler/u1_words.eri ONLY. The original
compiler module and the entire production compiler/runtime tree are not edited.
The proposed change preserves both owner-state polls when owners differ and
avoids repeating the exact same idempotent poll when the two owners match.
C-native bootstrap is the independent exact stdout/stderr/exit oracle. Both
owned-native programs use one identical generated native runtime.
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
OLD = "    try budget.poll(words.owner); try budget.poll(phase.owner);\n"
NEW = ("    try budget.poll(words.owner);\n"
       "    if words.owner != phase.owner { try budget.poll(phase.owner); }\n")


def change_poll_only(source):
    if source.count(OLD) != 1:
        raise AssertionError("words context double-owner-poll anchor changed")
    if "public function poll(owner identity Owner)" not in (
        ROOT / "src/compiler/u1_budget.eri"
    ).read_text():
        raise AssertionError("budget poll contract changed")
    return source.replace(OLD, NEW, 1)


def sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


def compile_owned(frontend, source, root):
    r = subprocess.run(
        [str(frontend), "emit-asm", str(source), "--source-root",
         str(root), "--target", "x86_64-linux"],
        capture_output=True, text=True, timeout=240,
    )
    if (r.returncode, r.stderr) != (0, ""):
        raise AssertionError(f"owned emit failed: {r.returncode} {r.stderr[-2500:]}")
    return r.stdout


def prepare_source(directory, fixture, words=None):
    directory.mkdir()
    compiler = directory / "compiler"
    if words is None:
        compiler.symlink_to(ROOT / "src/compiler", target_is_directory=True)
    else:
        compiler.mkdir()
        for entry in (ROOT / "src/compiler").iterdir():
            if entry.name != "u1_words.eri":
                (compiler / entry.name).symlink_to(
                    entry, target_is_directory=entry.is_dir())
        (compiler / "u1_words.eri").write_text(words)
    source = directory / "linked.eri"
    source.write_text(fixture)
    return source


class U1BWordStorePollBenchmark(unittest.TestCase):
    def test_same_owned_runtime_both_phase_owner_checks_preserved(self):
        pairs = int(os.environ.get("ERISTAVI_U1B_WORDS_POLL_PAIRS", "0"))
        if pairs not in (1, 5):
            self.skipTest("focused opt-in one/five owned-native paired study only")
        if platform.system() != "Linux" or platform.machine().lower() not in (
            "x86_64", "amd64"
        ):
            self.skipTest("owned native linker is Linux x86-64 only")
        if not shutil.which("as") or not shutil.which("ld"):
            self.skipTest("as/ld unavailable")
        fixture = (ROOT / "tests/fixtures/u1_aggregate_calls.eri").read_text()
        original_words = (ROOT / "src/compiler/u1_words.eri").read_text()
        modified_words = change_poll_only(original_words)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline_root = root / "baseline"
            candidate_root = root / "candidate"
            baseline = prepare_source(baseline_root, fixture)
            candidate = prepare_source(candidate_root, fixture, modified_words)

            # The independent original C-bootstrap produces the external oracle.
            c_exe = root / "C-bootstrap"
            self.assertEqual(build_native(baseline, c_exe, baseline_root), 0)
            expected = subprocess.run([str(c_exe)], capture_output=True,
                                      text=True, timeout=120)
            self.assertEqual((expected.returncode, expected.stderr), (0, ""))
            self.assertIn("u1b-aggregate-calls:ok", expected.stdout)

            frontend, generator = shared_u1_compilers()
            original_asm = compile_owned(frontend, baseline, baseline_root)
            candidate_asm = compile_owned(frontend, candidate, candidate_root)
            self.assertNotEqual(sha(original_asm), sha(candidate_asm))
            generated_runtime = subprocess.run(
                [str(generator)], capture_output=True, text=True, timeout=120)
            self.assertEqual((generated_runtime.returncode,
                              generated_runtime.stderr), (0, ""))
            runtime_s = root / "owned-runtime.s"
            runtime_o = root / "owned-runtime.o"
            runtime_s.write_text(generated_runtime.stdout)
            subprocess.run(["as", "--64", str(runtime_s), "-o", str(runtime_o)],
                           check=True, capture_output=True, timeout=60)
            executables = {}
            for name, code in (("baseline", original_asm),
                               ("candidate", candidate_asm)):
                asm = root / (name + ".s")
                obj = root / (name + ".o")
                asm.write_text(code)
                subprocess.run(["as", "--64", str(asm), "-o", str(obj)],
                               check=True, capture_output=True, timeout=60)
                exe = root / name
                linking = subprocess.run(
                    ["ld", "-nostdlib", "-static", "-e", "_start",
                     str(obj), str(runtime_o), "-o", str(exe)],
                    check=False, capture_output=True, text=True, timeout=60)
                self.assertEqual(linking.returncode, 0,
                                 f"link {name}: {linking.stderr[-4500:]}")
                executables[name] = exe

            observations = {"baseline": [], "candidate": []}
            for i in range(pairs):
                order = (("baseline", "candidate") if i % 2 == 0
                         else ("candidate", "baseline"))
                for which in order:
                    before = time.perf_counter()
                    result = subprocess.run(
                        [str(executables[which])], capture_output=True,
                        text=True, timeout=240)
                    seconds = time.perf_counter() - before
                    self.assertEqual(
                        (result.returncode, result.stderr, result.stdout),
                        (expected.returncode, expected.stderr, expected.stdout),
                        f"invalid output parity for {which}, pair {i+1}")
                    observations[which].append(seconds)
            medians = {k: statistics.median(v) for k, v in observations.items()}
            print("U1B_WORDS_OWNER_POLL_PAIRED=" + json.dumps({
                "candidate": "same_owner_duplicate_budget_poll_elimination",
                "mutation": "test-only compiler/u1_words.eri context: second "
                    "budget.poll(phase.owner) retained if and only if the "
                    "phase owner differs from words.owner; all other "
                    "context/phase/frozen/work and memory checks unchanged",
                "input_fixture_sha256": sha(fixture),
                "original_words_sha256": sha(original_words),
                "candidate_words_sha256": sha(modified_words),
                "original_app_assembly_sha256": sha(original_asm),
                "candidate_app_assembly_sha256": sha(candidate_asm),
                "shared_owned_runtime_sha256": sha(generated_runtime.stdout),
                "pairs": pairs,
                "order": "AB" if pairs == 1 else "AB/BA/AB/BA/AB",
                "samples_seconds": observations,
                "median_seconds": medians,
                "candidate_over_original": medians["candidate"]/medians["baseline"],
                "original_over_candidate": medians["baseline"]/medians["candidate"],
                "exact_output_stderr_exit_C_bootstrap_parity": True,
                "production_files_changed": False,
                "limitation": "One exact full U1b fixture only; fresh native-process "
                              "wall times, not separate compilation time; no "
                              "qualification for all failure/ownership paths",
            }, sort_keys=True), flush=True)


if __name__ == "__main__":
    unittest.main()
