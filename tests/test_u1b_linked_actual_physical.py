"""Opt-in actual allocator/GC evidence for linked U1b recursive frames.

This observes real owned-runtime graph allocations made during the complete
linked fixture, not merely the modeled owner ledger. The 103 diagnostic tag
covers setup, linked frame allocation, aggregate execution, and teardown;
it does NOT isolate individual frame bytes or process RSS.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native
from u1_native_tools import shared_u1_compilers
from test_u1_owner_physical import _decode_owner_records, _instrument_owned_runtime

ROOT = Path(__file__).resolve().parents[1]


class U1BLinkedActualPhysicalTests(unittest.TestCase):
    def test_linked_recursive_actual_allocator_reclamation(self):
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
                observed = link("linked-observed", _instrument_owned_runtime(
                    runtime.stdout, dump.fileno(), force_identity_collisions=True))
                result = subprocess.run([str(observed)], pass_fds=(dump.fileno(),),
                                        capture_output=True, text=True, timeout=180,
                                        check=False)
            self.assertEqual((result.returncode, result.stderr, result.stdout),
                             (0, "", baseline.stdout))
            before, after = _decode_owner_records((root / "actual.bin").read_bytes())
            self.assertEqual((before["error"], after["error"]), (0, 0))
            # The diagnostic tag is active for every linked request, including
            # recursive execution and all bounded failure paths.
            function = before["owners"]["function"]
            final = after["owners"]["function"]
            self.assertGreater(function["allocations"], 0)
            self.assertGreater(function["traffic"], 0)
            self.assertGreater(function["peak"], 0)
            self.assertLessEqual(function["peak"], function["traffic"])
            self.assertEqual(final["live"], 0)
            self.assertEqual(final["reclaimed_bytes"], function["traffic"])
            self.assertEqual(final["reclaimed_objects"], function["allocations"])
            print("U1B_LINKED_ACTUAL=" + __import__("json").dumps({
                "scope": "Actual diagnostic-tagged allocator activity over linked setup, recursive frames, aggregate execution and cleanup; not isolated frame attribution or RSS",
                "before_gc": function,
                "after_gc": final,
                "original_owner_gates": {"peak_bytes": 8388608, "traffic_bytes": 67108864},
            }, sort_keys=True), flush=True)


if __name__ == "__main__":
    unittest.main()
