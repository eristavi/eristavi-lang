#!/usr/bin/env python3
"""Issue #51: bounded current production-owned-compiler allocation/validation probe.

Only disposable emitted assembly is instrumented. The checked-in compiler, runtime,
ABI, verifier, resource limits and compiled source are unchanged. Compiler B is
built by the C bootstrap; B never compiles itself. Instrumented wall times are
NOT performance comparisons. Source counters are exact entries, not CPU samples.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]
from u1_native_tools import shared_u1_compilers
from test_u1b_runtime_hotspot import observed_asm, bump
import test_u1b_runtime_hotspot as u1b_hotspot

SOURCE_COUNTERS = {
    "compiler.universal_verify.verify": "verify",
    "compiler.universal_verify.routine": "verify_routine",
    "compiler.universal_verify.transfer": "verify_transfer",
    "compiler.universal_verify.intersect": "verify_intersect",
    "compiler.universal_verify.copy": "verify_copy",
    "compiler.universal_verify.defined": "verify_defined",
    "compiler.universal_verify.define": "verify_define",
    "compiler.universal_verify.flowAt": "verify_flow_lookup",
    "compiler.universal_verify.instruction": "verify_instruction",
    "compiler.universal_verify.operands": "verify_operands",
    "compiler.universal_optimize.optimize": "optimize",
    "compiler.universal_optimize.routine": "optimize_routine",
    "compiler.universal_optimize.visit": "optimize_visit",
}
MARKERS = {
    "compiler.universal_optimize.optimize": 10,
    "compiler.universal_verify.verify": 20,
    "compiler.universal_optimize.routine": 30,
}
STAGE = {1: "start", 10: "optimizer_entry", 20: "verify_entry",
         30: "reachable_block_pass", 90: "exit"}

# The existing owned-runtime observer is extended only in this disposable
# diagnostic process. All published U1b profile formats remain unchanged.
u1b_hotspot.EXTRA_COUNTERS += tuple(SOURCE_COUNTERS.values())
u1b_hotspot.FIELDS = u1b_hotspot.FIELDS[:-1] + tuple(SOURCE_COUNTERS.values()) + ("live_graphs",)
u1b_hotspot.SIZE = len(u1b_hotspot.FIELDS) * 8
FIELDS, SIZE = u1b_hotspot.FIELDS, u1b_hotspot.SIZE


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def replace_exact(value, old, new):
    if value.count(old) != 1:
        raise AssertionError("unstable diagnostic anchor: " + old[:80])
    return value.replace(old, new, 1)


def marked(tag):
    # .Lprof_mark saves all integer registers and flags; phase is private data.
    return ("    pushfq\n"
            "    movq $" + str(tag) + ",.Lprof_phase_code(%rip)\n"
            "    call .Lprof_mark\n"
            "    popfq\n")


def profile_application(assembly, trace):
    symbols = {}
    for line in trace.splitlines():
        if not line.startswith("[erist-phase] "):
            continue
        event = json.loads(line[len("[erist-phase] "):])
        if event.get("event") != "begin" or event.get("phase") != "universal-lower-function":
            continue
        symbol, _, signature = event["subject"].partition(" ")
        name = signature.split("$", 1)[0]
        if name not in SOURCE_COUNTERS:
            continue
        if name in symbols:
            raise AssertionError("multiple compiler verifier specializations: " + name)
        symbols[name] = symbol
        extra = bump(SOURCE_COUNTERS[name])
        if name in MARKERS:
            # Only the first optimizer-routine marker is needed; all routine
            # entries remain counted. No per-routine profile file explosion.
            if name == "compiler.universal_optimize.routine":
                extra += ("    cmpq $30,.Lprof_phase_code(%rip)\n"
                          "    je .Lissue51_routine_marked\n"
                          + marked(30) + ".Lissue51_routine_marked:\n")
            else:
                extra += marked(MARKERS[name])
        assembly = replace_exact(assembly, "\n" + symbol + ":\n",
                                 "\n" + symbol + ":\n" + extra)
    missing = set(MARKERS) - set(symbols)
    if missing:
        raise AssertionError("optimizer/verification boundaries absent: " + str(sorted(missing)))
    return assembly, symbols


def profile_runtime(assembly, fd):
    data = observed_asm(assembly, fd)
    data = replace_exact(
        data, ".Lprof_clock:\n.zero 16",
        ".Lprof_clock:\n.zero 16\n"
        ".globl .Lprof_phase_code\n.Lprof_phase_code:\n.quad 0")
    data = replace_exact(
        data, ".Lprof_mark:\n", ".globl .Lprof_mark\n.Lprof_mark:\n")
    data = replace_exact(
        data, "    movq .Lprocess_exit_code(%rip),%rbx\n"
              "    movq %rbx,.Lprof_record(%rip)",
        "    movq .Lprof_phase_code(%rip),%rbx\n"
        "    movq %rbx,.Lprof_record(%rip)")
    data = replace_exact(
        data, "    call erist_entry\n    call .Lprof_mark\n",
        marked(1) + "    call erist_entry\n" + marked(90))
    return data


def assemble_link(root, application, runtime, name):
    application_path = root / (name + ".app.s")
    runtime_path = root / (name + ".runtime.s")
    application_path.write_text(application)
    runtime_path.write_text(runtime)
    app_obj, runtime_obj, binary = (root / (name + ext) for ext in
                                    (".app.o", ".runtime.o", ".bin"))
    for source, obj in ((application_path, app_obj), (runtime_path, runtime_obj)):
        subprocess.run(["as", "--64", str(source), "-o", str(obj)],
                       check=True, capture_output=True, timeout=60)
    subprocess.run(["ld", "-nostdlib", "-static", "-e", "_start",
                    str(app_obj), str(runtime_obj), "-o", str(binary)],
                   check=True, capture_output=True, timeout=60)
    return binary


def invoke(command, output, error, cap, pass_fds=()):
    start = time.monotonic()
    with output.open("wb") as stdout, error.open("wb") as stderr:
        try:
            p = subprocess.run(list(map(str, command)), stdout=stdout,
                               stderr=stderr, timeout=cap,
                               pass_fds=pass_fds)
            return {"status": "completed" if p.returncode == 0 else "failed",
                    "returncode": p.returncode,
                    "wall_seconds": time.monotonic() - start}
        except subprocess.TimeoutExpired:
            return {"status": "censored-at-" + str(cap) + "s",
                    "wall_seconds_lower_bound": time.monotonic() - start}


def records_from(path):
    data = path.read_bytes()
    if len(data) % SIZE:
        raise AssertionError("truncated private counter record")
    rows = [dict(zip(FIELDS, struct.unpack_from("<" + "Q" * len(FIELDS), data, i)))
            for i in range(0, len(data), SIZE)]
    if any(row["tag"] not in STAGE for row in rows):
        raise AssertionError("unknown compiler boundary marker")
    return rows


def intervals(rows):
    result = []
    for before, after in zip(rows, rows[1:]):
        if after["time_ns"] < before["time_ns"]:
            raise AssertionError("nonmonotonic profile clock")
        diff = {}
        for field in FIELDS[2:-1]:
            if after[field] < before[field]:
                raise AssertionError("nonmonotonic " + field)
            diff[field] = after[field] - before[field]
        result.append({"from": STAGE[before["tag"]], "to": STAGE[after["tag"]],
                       "wall_seconds_observed": (after["time_ns"]-before["time_ns"])/1e9,
                       "counters": diff})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cap", type=int, default=90)
    args = parser.parse_args()
    if args.cap < 5 or args.cap > 90:
        raise ValueError("per-command cap must be from 5 to 90 seconds")
    if platform.system() != "Linux" or platform.machine().lower() not in ("x86_64","amd64"):
        raise RuntimeError("Linux x86-64 freestanding profile only")
    if not shutil.which("as") or not shutil.which("ld"):
        raise RuntimeError("assembler/linker missing")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    initial = {str(p.relative_to(ROOT)): digest(p) for p in
               sorted((ROOT / "src").rglob("*.eri"))}
    with tempfile.TemporaryDirectory(prefix="eristavi-issue51-") as d:
        work = Path(d)
        frontend, generator = shared_u1_compilers()
        runtime = subprocess.run([str(generator)], check=True,
                                 capture_output=True, text=True, timeout=90).stdout
        source = ROOT / "src/frontend.eri"
        asm_path, traces = work/"frontend.s", work/"frontend-trace.stderr"
        compiled = invoke([frontend, "emit-asm", source, "--source-root", ROOT/"src",
                           "--target", "x86_64-linux", "--trace-phases"],
                          asm_path, traces, 90)
        if compiled["status"] != "completed":
            raise AssertionError("bootstrap compiler B emission failed: " + str(compiled))
        app_asm = asm_path.read_text()
        instrumented, symbols = profile_application(app_asm, traces.read_text())
        plain = assemble_link(work, app_asm, runtime, "baseline")
        with (work/"counter-stream.bin").open("wb") as stream:
            profiled_runtime = profile_runtime(runtime, stream.fileno())
            observed = assemble_link(work, instrumented, profiled_runtime, "instrumented")
            summary = {
                "scope": "issue #51 current production frontend compiled by C bootstrap; "
                         "no B-to-C self build, no source or ABI modifications",
                "compiler_B_assembly_sha256": digest(asm_path),
                "runtime_generated_sha256": hashlib.sha256(runtime.encode()).hexdigest(),
                "diagnostic_app_sha256": hashlib.sha256(instrumented.encode()).hexdigest(),
                "counter_fields": list(FIELDS) + list(SOURCE_COUNTERS.values()),
                "source_symbols": symbols,
                "instrumented_time_is_not_a_speedup": True,
                "cap_seconds_each": args.cap,
                "workloads": {}
            }
            # Baseline first. Same immutable B binary, target and workloads.
            for module in ("typed_ir.eri", "ir_verify.eri"):
                target = ROOT/"src/compiler"/module
                reference_path = work/(module+".reference.s")
                reference = invoke([frontend, "emit-asm", target,
                                    "--source-root", ROOT/"src",
                                    "--target", "x86_64-linux"],
                                   reference_path, work/(module+".reference.stderr"), args.cap)
                if reference["status"] != "completed":
                    raise AssertionError("independent C-bootstrap output missing: " + module)
                root = output/module
                root.mkdir(parents=True, exist_ok=True)
                row = {"source_sha256": digest(target),
                       "reference_output_sha256": digest(reference_path),
                       "reference": reference}
                for name, executable in (("baseline",plain),("instrumented",observed)):
                    app_out, app_err = work/(module+"."+name+".s"), work/(module+"."+name+".stderr")
                    if name == "instrumented":
                        stream.seek(0)
                        stream.truncate(0)
                    result = invoke([executable, "emit-asm", target,
                                     "--source-root", ROOT/"src",
                                     "--target", "x86_64-linux", "--trace-phases"],
                                    app_out, app_err, args.cap,
                                    pass_fds=(stream.fileno(),) if name == "instrumented" else ())
                    if result["status"] == "completed":
                        result["output_sha256"] = digest(app_out)
                        result["exact_reference_parity"] = app_out.read_bytes() == reference_path.read_bytes()
                        if not result["exact_reference_parity"]:
                            raise AssertionError("assembler output parity failed: " + module+" "+name)
                    if name == "instrumented":
                        stream.flush()
                        samples = records_from(work/"counter-stream.bin")
                        result["samples"] = samples
                        result["intervals"] = intervals(samples)
                        result["snapshot_count"] = len(samples)
                        if not samples:
                            raise AssertionError("no counter snapshots on " + module)
                        (root/"profile.json").write_text(json.dumps(result, indent=2)+"\n")
                    else:
                        (root/"baseline.json").write_text(json.dumps(result, indent=2)+"\n")
                    row[name] = {k:v for k,v in result.items() if k!="samples" and k!="intervals"}
                    print(module, name, result["status"], result.get("wall_seconds",
                          result.get("wall_seconds_lower_bound")), flush=True)
                summary["workloads"][module] = row
                (output/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    final = {str(p.relative_to(ROOT)): digest(p) for p in sorted((ROOT/"src").rglob("*.eri"))}
    summary["source_snapshot_unchanged"] = initial == final
    if not summary["source_snapshot_unchanged"]:
        raise AssertionError("source tree changed during profile")
    (output/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print("ISSUE51="+json.dumps({"status":"done", "workloads":summary["workloads"]},
                                  sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
