"""U1a C-native physical managed-heap observations, separated from owner budgets.

This is an incremental *measurement* gate for #77, NOT proof of exact
U1a-owner GC attribution. The baseline controls for runtime startup and
independent UIR switch fixtures; stdout/counter checks remain unchanged.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
import time
import unittest

from test_u1_promotion import cases_for, evaluate, parse_snapshots, probe_source
from u1_native_tools import shared_u1_compilers

ROOT = Path(__file__).resolve().parents[1]
CASES = (
    ("control", None, None),
    ("dense8", "switchDense8()", "switch-dense-8"),
    ("dense32", "switchDense()", "switch-dense"),
    ("dense128", "switchDense128()", "switch-dense-128"),
)


def make_driver():
    # Private instrumentation only; compiled unmodified production C runtime.
    # Emitting at normal process exit uses the existing native heap telemetry
    # API, not random observations from the Python process allocator.
    native = str((ROOT / "runtime/native_gc_runtime.c").resolve())
    return (
        '#include <stdio.h>\n'
        f'#include "{native}"\n'
        '__attribute__((destructor)) static void u1a_physical_snapshot(void){\n'
        '  fprintf(stderr,"U1A_C_GC={\\"live_bytes\\":%zu,'
        '\\"peak_bytes\\":%zu,\\"live_blocks\\":%zu,'
        '\\"collections\\":%zu,\\"reclaimed_blocks\\":%zu,'
        '\\"reclaimed_bytes\\":%zu}\\n",\n'
        '    eri_native_heap_live_bytes(),eri_native_heap_peak_bytes(),'
        '    eri_native_heap_live_blocks(),eri_native_heap_collections(),'
        '    eri_native_heap_reclaimed_blocks(),eri_native_heap_reclaimed_bytes());\n'
        '}\n'
    )


def run_child(binary, deadline=40.0):
    with tempfile.TemporaryFile(mode="w+t") as output, tempfile.TemporaryFile(
        mode="w+t"
    ) as error:
        started = time.monotonic()
        child = subprocess.Popen([str(binary)], stdout=output, stderr=error)
        while True:
            pid, status, usage = os.wait4(child.pid, os.WNOHANG)
            if pid == child.pid:
                code = os.waitstatus_to_exitcode(status)
                break
            if time.monotonic() - started > deadline:
                child.kill()
                os.wait4(child.pid, 0)
                raise AssertionError("physical native C sample timed out")
            time.sleep(0.01)
        elapsed = time.monotonic() - started
        output.seek(0)
        error.seek(0)
        return code, output.read(), error.read(), round(elapsed, 6), usage


@unittest.skipUnless(
    platform.system() == "Linux"
    and platform.machine().lower() in ("x86_64", "amd64")
    and hasattr(os, "wait4"),
    "physical C-native samples require Linux x86-64 wait4",
)
class U1aPhysicalCManagedHeapTests(unittest.TestCase):
    def test_five_matched_native_gc_heap_samples_across_switch_sizes(self):
        for tool in ("cc", "as", "ld", "readelf"):
            if not shutil.which(tool):
                self.skipTest(f"{tool} unavailable")
        frontend, _ = shared_u1_compilers()
        evidence = []
        with tempfile.TemporaryDirectory(prefix="u1a-c-heap-") as temporary:
            root = Path(temporary)
            (root / "compiler").symlink_to(
                ROOT / "src/compiler", target_is_directory=True
            )
            driver = root / "u1a-physical-driver.c"
            driver.write_text(make_driver(), encoding="utf-8")
            for label, call, expected_name in CASES:
                source = root / f"{label}.eri"
                source.write_text(
                    probe_source([call] if call is not None else []),
                    encoding="utf-8",
                )
                assembly = root / f"{label}.s"
                generated = subprocess.run(
                    [
                        str(frontend), "emit-asm", str(source), "--source-root",
                        str(root), "--target", "x86_64-linux",
                    ],
                    capture_output=True, text=True, timeout=120,
                )
                self.assertEqual(
                    (generated.returncode, generated.stderr),
                    (0, ""), generated.stdout[-700:],
                )
                assembly.write_text(generated.stdout, encoding="utf-8")
                binary = root / label
                compile_result = subprocess.run(
                    [
                        "cc", "-std=c11", "-O2", "-DERIST_NATIVE_RUNTIME",
                        "-DERIST_HEAP_GC_INTERVAL=65536",
                        str(assembly), str(driver), "-lm", "-o", str(binary),
                    ],
                    capture_output=True, text=True, timeout=60,
                )
                self.assertEqual(
                    compile_result.returncode, 0, compile_result.stderr[-900:],
                )
                first_output = None
                for trial in range(5):
                    code, stdout, stderr, wall, usage = run_child(binary)
                    self.assertEqual(code, 0, (label, trial, stdout[-500:]))
                    self.assertTrue(
                        stderr.startswith("U1A_C_GC="), (label, stderr[-500:]),
                    )
                    measured = json.loads(stderr.removeprefix("U1A_C_GC=").strip())
                    self.assertGreaterEqual(
                        measured["peak_bytes"], measured["live_bytes"],
                    )
                    self.assertGreaterEqual(
                        measured["peak_bytes"], 0,
                    )
                    if first_output is None:
                        first_output = stdout
                    else:
                        self.assertEqual(first_output, stdout)
                    snapshots, labels = parse_snapshots(stdout)
                    self.assertEqual(labels, [])
                    if expected_name is None:
                        self.assertEqual(snapshots, [])
                    else:
                        self.assertEqual(len(snapshots), 1)
                        name, counts, original, promoted = snapshots[0]
                        self.assertEqual(name, expected_name)
                        self.assertLessEqual(counts[3], 8 * 1024 * 1024)
                        self.assertLessEqual(counts[4], 64 * 1024 * 1024)
                        self.assertLessEqual(counts[5], 33554432)
                        self.assertEqual(promoted["cells"], [])
                        for values, independent in cases_for(name, original):
                            before, first_trace = evaluate(original, values)
                            after, after_trace = evaluate(promoted, values)
                            self.assertEqual(before, independent)
                            self.assertEqual(
                                (after, after_trace), (before, first_trace)
                            )
                    evidence.append({
                        "fixture": label, "trial": trial + 1,
                        "model_owner_peak_bytes":
                        snapshots[0][1][3] if snapshots else None,
                        "model_owner_traffic_bytes":
                        snapshots[0][1][4] if snapshots else None,
                        "owner_work_visits":
                        snapshots[0][1][5] if snapshots else None,
                        "actual_c_managed_heap": measured,
                        "actual_process_rss_KiB": usage.ru_maxrss,
                        "wall_seconds": wall,
                        "output_sha256": hashlib.sha256(stdout.encode()).hexdigest(),
                    })
        self.assertEqual(len(evidence), len(CASES) * 5)
        print("U1A_C_HEAP_PHYSICAL=" + json.dumps(
            {
                "status": "pass", "scope": "whole isolated C process managed heap",
                "attribution": (
                    "C-managed heap includes UIR and bootstrap; UIR owner-only "
                    "allocation site attribution is NOT established"
                ),
                "samples": evidence,
            }, sort_keys=True,
        ))


if __name__ == "__main__":
    unittest.main()
