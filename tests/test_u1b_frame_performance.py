"""Opt-in U1b dynamic-frame physical attribution and paired execution evidence.

A private interpreter copy assigns a unique 101..164 diagnostic tag to each
invocation. Real owned-runtime graph allocator/GC hooks account for those tags.
The unmodified linked fixture is separately timed AB/BA on C-bootstrap and
owned-native execution. No production implementation, ABI or budget is changed.
"""
import json
import os
from pathlib import Path
import shutil
import platform
import statistics
import struct
import subprocess
import tempfile
import time
import unittest

from compiler.erist.cli import build_native
from u1_native_tools import shared_u1_compilers
from test_u1_owner_physical import _instrument_owned_runtime, STAT_FIELDS

ROOT = Path(__file__).resolve().parents[1]
MAX_FRAMES = 64
OWNER_STATS_BYTES = MAX_FRAMES * 48
SNAPSHOT_BYTES = 8 + OWNER_STATS_BYTES + 200


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise AssertionError(f"diagnostic source anchor changed: {old[:90]!r}")
    return text.replace(old, new, 1)


def frame_fixture(original):
    """Preserve one complete recursive aggregate loop, omit refusal repetitions."""
    result = replace_once(
        original, "    if mode != -1 {", "    if mode != -1 and mode != -4 {")
    result = replace_once(
        result, "    // Refuse at every dynamic instruction boundary",
        "    if mode == -1 {\n    // Refuse at every dynamic instruction boundary")
    result = replace_once(
        result,
        '        failure.location == trapLoc.index,"original callee guard location");\n\n    }',
        '        failure.location == trapLoc.index,"original callee guard location");\n'
        '    }\n    }')
    old_all = (
        "function all() returns Bool fails budget.LimitError,verify.InvalidIR,ProbeError {\n"
        "    let normal be try exercise(-1);\n"
        "    let cancelled be try exercise(-2);\n"
        "    let limits be [0,128,512,1024,2048,4096,8192];\n"
        "    for limit in limits { let denied be try exercise(limit); }\n"
        "    let work be [0,1,16,64,128];\n"
        "    for amount in work { let denied be try exercise(10000+amount); }\n"
        "    return true;\n"
        "}"
    )
    new_all = (
        "function all() returns Bool fails budget.LimitError,verify.InvalidIR,ProbeError {\n"
        "    let normal be try exercise(-4);\n"
        "    return true;\n"
        "}"
    )
    return replace_once(result, old_all, new_all)


def frame_module(original):
    """Only a temporary compiler module adds frame-identity diagnostic tags."""
    result = replace_once(original, "import compiler.u1_budget as budget;",
                          "import std.process as process;\nimport compiler.u1_budget as budget;")
    result = replace_once(
        result,
        "    owner identity budget.Owner; fuel Int; steps Int; depthLimit Int;\n}",
        "    owner identity budget.Owner; fuel Int; steps Int; depthLimit Int;\n"
        "    traceSerial Int; traceActive Int;\n}")
    result = replace_once(
        result, "        fuel=fuel; steps=0; depthLimit=depthLimit; };",
        "        fuel=fuel; steps=0; depthLimit=depthLimit;\n"
        "        traceSerial=0; traceActive=0; };")
    start = result.index("function invoke(")
    end = result.index("function enter(", start)
    invocation = result[start:end]
    invocation = replace_once(
        invocation, "    let rp be try budget.verificationPhase(routine.owner);",
        "    let rp be try budget.verificationPhase(routine.owner);\n"
        "    let parentTag be machine.traceActive;\n"
        "    machine.traceSerial=machine.traceSerial+1;\n"
        f'    if machine.traceSerial > {MAX_FRAMES} {{\n'
        '        try budget.finishPhase(rp);\n'
        '        try budget.reject("frame diagnostic exceeds fixed tag capacity");\n'
        '    }\n'
        "    let ownTag be 100+machine.traceSerial;\n"
        "    process.setExitCode(0);\n"
        '    output("u1b-frame");\n'
        "    output(machine.traceSerial);\n"
        "    output(depth);\n"
        "    output(target.index);\n"
        "    machine.traceActive=ownTag;\n"
        "    process.setExitCode(ownTag);")
    if invocation.count("try budget.finishPhase(rp); fail error;") != 3:
        raise AssertionError("frame-refusal cleanup structure changed")
    invocation = invocation.replace(
        "try budget.finishPhase(rp); fail error;",
        "try budget.finishPhase(rp); machine.traceActive=parentTag;\n"
        "            process.setExitCode(parentTag); fail error;")
    invocation = replace_once(
        invocation,
        "    try words.close(scratch); try words.close(slots); try budget.finishPhase(rp);\n"
        "    return finished;",
        "    try words.close(scratch); try words.close(slots); try budget.finishPhase(rp);\n"
        "    machine.traceActive=parentTag;\n"
        "    process.setExitCode(parentTag);\n"
        "    return finished;")
    return result[:start] + invocation + result[end:]


def widen_diagnostic(instrumented):
    """64 frame rows while preserving the existing allocator/free hook semantics."""
    from test_u1_owner_physical import RECORD_BYTES
    instrumented = replace_once(
        instrumented,
        "    cmpq $105,%rax\n    ja .Ltest_owner_alloc_ret",
        f"    cmpq $164,%rax\n    ja .Ltest_owner_alloc_ret")
    instrumented = replace_once(
        instrumented, ".Ltest_owner_stats:\n    .zero 240",
        f".Ltest_owner_stats:\n    .zero {OWNER_STATS_BYTES}")
    instrumented = replace_once(
        instrumented, f"    movq ${RECORD_BYTES},%rdx",
        f"    movq ${SNAPSHOT_BYTES},%rdx")
    return instrumented


def decode_records(raw):
    if len(raw) != SNAPSHOT_BYTES * 2:
        raise AssertionError(f"frame diagnostic byte count {len(raw)}")
    snapshots = []
    for offset in (0, SNAPSHOT_BYTES):
        values = struct.unpack_from(
            "<" + "Q" * (SNAPSHOT_BYTES // 8), raw, offset)
        rows = [dict(zip(STAT_FIELDS,
                         values[1 + i * 6:1 + (i + 1) * 6]))
                for i in range(MAX_FRAMES)]
        snapshots.append((values[0], rows))
    return snapshots


def parse_frame_markers(output):
    lines = output.splitlines()
    frames = []
    for pos, value in enumerate(lines):
        if value == "u1b-frame":
            if len(lines) < pos + 4:
                raise AssertionError("truncated frame marker")
            serial, depth, function_id = map(int, lines[pos + 1:pos + 4])
            frames.append({"serial": serial, "depth": depth,
                           "function_id": function_id})
    return frames


class U1BLinkedFramePerformanceTests(unittest.TestCase):
    def test_dynamic_frame_allocation_and_paired_native_performance(self):
        if platform.system() != "Linux" or platform.machine().lower() not in ("x86_64", "amd64"):
            self.skipTest("freestanding x86-64 assembly and linker require Linux x86-64")
        if os.environ.get("ERISTAVI_U1B_FRAME_PROBE") != "1":
            self.skipTest("expensive U1b frame probe is opt-in only")
        for executable in ("as", "ld"):
            if shutil.which(executable) is None:
                self.skipTest(f"{executable} unavailable")
        original = (ROOT / "tests/fixtures/u1_aggregate_calls.eri").read_text()
        module = (ROOT / "src/compiler/u1_aggregate_calls.eri").read_text()
        with tempfile.TemporaryDirectory() as tmp:
            temp = Path(tmp)
            standard = temp / "standard"
            standard.mkdir()
            (standard / "compiler").symlink_to(
                ROOT / "src/compiler", target_is_directory=True)
            source = standard / "linked.eri"
            source.write_text(original)
            bootstrap = standard / "bootstrap"
            begin = time.perf_counter()
            self.assertEqual(build_native(source, bootstrap, standard), 0)
            bootstrap_build_seconds = time.perf_counter() - begin

            begin = time.perf_counter()
            frontend, generator = shared_u1_compilers()
            shared_compiler_seconds = time.perf_counter() - begin
            begin = time.perf_counter()
            runtime = subprocess.run([str(generator)], capture_output=True,
                                     text=True, timeout=120)
            self.assertEqual((runtime.returncode, runtime.stderr), (0, ""))
            runtime_generation_seconds = time.perf_counter() - begin

            def emit(path, source_root):
                start = time.perf_counter()
                result = subprocess.run(
                    [str(frontend), "emit-asm", str(path), "--source-root",
                     str(source_root), "--target", "x86_64-linux"],
                    capture_output=True, text=True, timeout=240)
                self.assertEqual((result.returncode, result.stderr), (0, ""))
                return result.stdout, time.perf_counter() - start

            def link(source_asm, runtime_asm, target_dir, name):
                app = target_dir / (name + "-app.s")
                rt = target_dir / (name + "-runtime.s")
                app.write_text(source_asm)
                rt.write_text(runtime_asm)
                executable = target_dir / name
                for asm in (app, rt):
                    subprocess.run(
                        ["as", "--64", str(asm), "-o",
                         str(asm.with_suffix(".o"))],
                        check=True, capture_output=True, timeout=60)
                subprocess.run(
                    ["ld", "-nostdlib", "-static", "-e", "_start",
                     str(app.with_suffix(".o")), str(rt.with_suffix(".o")),
                     "-o", str(executable)],
                    check=True, capture_output=True, timeout=60)
                return executable

            original_asm, standard_emit_seconds = emit(source, standard)
            owned = link(original_asm, runtime.stdout, standard, "owned")
            expected = subprocess.run(
                [str(bootstrap)], capture_output=True, text=True, timeout=240)
            self.assertEqual((expected.returncode, expected.stderr), (0, ""))
            self.assertIn("u1b-aggregate-calls:ok", expected.stdout)
            actual = subprocess.run(
                [str(owned)], capture_output=True, text=True, timeout=240)
            self.assertEqual(
                (actual.returncode, actual.stderr, actual.stdout),
                (0, "", expected.stdout))

            timings = {"bootstrap_c": [], "owned_native": []}
            for order in (("bootstrap_c", "owned_native"),
                          ("owned_native", "bootstrap_c"),
                          ("bootstrap_c", "owned_native"),
                          ("owned_native", "bootstrap_c"),
                          ("bootstrap_c", "owned_native")):
                for label in order:
                    binary = bootstrap if label == "bootstrap_c" else owned
                    started = time.perf_counter()
                    run = subprocess.run(
                        [str(binary)], capture_output=True, text=True,
                        timeout=240)
                    elapsed = time.perf_counter() - started
                    self.assertEqual(
                        (run.returncode, run.stderr, run.stdout),
                        (0, "", expected.stdout))
                    timings[label].append(elapsed)
            medians = {name: statistics.median(samples)
                       for name, samples in timings.items()}
            print("U1B_LINKED_PERF=" + json.dumps({
                "scope": "Paired complete linked-fixture process time for "
                         "unmodified bootstrap-C/native versus owned/native; "
                         "NOT an isolated verification/execution measurement "
                         "or a compiler optimization speedup",
                "orders": ["AB", "BA", "AB", "BA", "AB"],
                "runtime_seconds": timings,
                "median_runtime_seconds": medians,
                "min_runtime_seconds": {name: min(values) for name, values in timings.items()},
                "max_runtime_seconds": {name: max(values) for name, values in timings.items()},
                "owned_over_bootstrap_ratio":
                    medians["owned_native"] / medians["bootstrap_c"],
                "cold_build_seconds": {
                    "bootstrap": bootstrap_build_seconds,
                    "shared_compiler": shared_compiler_seconds,
                    "runtime_generator": runtime_generation_seconds,
                    "emit_asm": standard_emit_seconds,
                },
            }, sort_keys=True), flush=True)

            # All module changes and diagnostic tags are confined to this
            # private copy, never the real compiler or its public interfaces.
            trace_root = temp / "trace"
            trace_root.mkdir()
            trace_compiler = trace_root / "compiler"
            trace_compiler.mkdir()
            for entry in (ROOT / "src/compiler").iterdir():
                if entry.name != "u1_aggregate_calls.eri":
                    (trace_compiler / entry.name).symlink_to(
                        entry, target_is_directory=entry.is_dir())
            (trace_compiler / "u1_aggregate_calls.eri").write_text(
                frame_module(module))
            trace_source = trace_root / "linked-trace.eri"
            trace_source.write_text(frame_fixture(original))
            trace_asm, trace_emit_seconds = emit(trace_source, trace_root)
            with (trace_root / "frames.bin").open("wb") as dump:
                diagnostic = _instrument_owned_runtime(
                    runtime.stdout, dump.fileno(),
                    force_identity_collisions=True)
                diagnostic = widen_diagnostic(diagnostic)
                executable = link(trace_asm, diagnostic,
                                  trace_root, "linked-frames")
                observed = subprocess.run(
                    [str(executable)], pass_fds=(dump.fileno(),),
                    capture_output=True, text=True, timeout=240)
            self.assertEqual((observed.returncode, observed.stderr), (0, ""),
                             observed.stdout[-1500:])
            self.assertEqual(observed.stdout.splitlines()[-2:], ["11", "17"])
            frames = parse_frame_markers(observed.stdout)
            self.assertGreaterEqual(len(frames), 4)
            self.assertEqual([f["serial"] for f in frames],
                             list(range(1, len(frames) + 1)))
            self.assertLessEqual(len(frames), MAX_FRAMES)
            self.assertEqual(frames[0]["depth"], 1)
            self.assertGreaterEqual(max(f["depth"] for f in frames), 4)

            (before_error, before), (after_error, after) = decode_records(
                (trace_root / "frames.bin").read_bytes())
            self.assertEqual((before_error, after_error), (0, 0))
            observed_frames = []
            for frame in frames:
                index = frame["serial"] - 1
                row, final = before[index], after[index]
                self.assertGreater(row["allocations"], 0, frame)
                self.assertGreater(row["traffic"], 0, frame)
                self.assertLessEqual(row["peak"], row["traffic"])
                self.assertEqual(final["live"], 0, (frame, final))
                self.assertEqual(final["reclaimed_bytes"], row["traffic"])
                self.assertEqual(final["reclaimed_objects"], row["allocations"])
                observed_frames.append({
                    **frame, "before_gc": row, "after_gc": final})
            for row in before[len(frames):]:
                self.assertEqual(row["allocations"], 0)
            print("U1B_DYNAMIC_FRAME_PHYSICAL=" + json.dumps({
                "scope": "Actual owned-runtime graph capacity by unique "
                         "dynamic invocation, exclusive of nested calls and "
                         "untagged setup/teardown, not whole-process RSS",
                "frames": observed_frames,
                "frame_count": len(observed_frames),
                "forced_identity_collisions": True,
                "trace_source_emit_seconds": trace_emit_seconds,
                "diagnostic_error": after_error,
                "original_modeled_owner_gates": {
                    "peak_bytes": 8388608,
                    "traffic_bytes": 67108864,
                },
            }, sort_keys=True), flush=True)


if __name__ == "__main__":
    unittest.main()
