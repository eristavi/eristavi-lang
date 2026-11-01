#!/usr/bin/env python3
"""Bounded #51 current compiler-source profiling, NOT owned B→C self-build.

A C-bootstrap frontend emits one owned frontend B; B compiles only the two
named modules, once each under a 90s cap. Never request B to compile frontend.
The U1 word adapter is outside this compiler's import closure: this is a
current-runtime diagnostic, not a before/after claim for the U1 optimization.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tests"), str(ROOT / "tools")]
from build_events import BuildJournal
from u1_native_tools import shared_u1_compilers

MEASURE = '''import json,os,subprocess,sys,time
started=time.monotonic()
p=subprocess.Popen(sys.argv[2:])
_,status,usage=os.wait4(p.pid,0)
p.returncode=os.waitstatus_to_exitcode(status)
with open(sys.argv[1],'w') as stream:
 json.dump(dict(wall_seconds=time.monotonic()-started,user_seconds=usage.ru_utime,
                system_seconds=usage.ru_stime,peak_rss_KiB=usage.ru_maxrss),stream)
sys.exit(p.returncode)
'''


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot():
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted((ROOT / "src").rglob("*.eri"))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--runtime-object", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    original = snapshot()
    journal = BuildJournal(output / "journal", timeout=90)
    frontend, _ = shared_u1_compilers()
    started = time.monotonic()
    assembly = output / "compiler-b.s"
    journal.run([frontend, "emit-asm", ROOT / "src/frontend.eri", "--source-root", ROOT / "src",
                 "--target", "x86_64-linux", "--trace-phases"], stdout_path=assembly)
    journal.run(["as", "--64", assembly, "-o", output / "compiler-b.o"])
    owned = output / "owned-frontend-b"
    journal.run(["ld", "-nostdlib", "-static", "-e", "_start", output / "compiler-b.o",
                 args.runtime_object.resolve(), "-o", owned])
    summary = {
        "scope": "current old production compiler on owned runtime, one run per module; no candidate-versus-baseline source-compiler claim",
        "owned_full_self_build_requested": False,
        "compiler_b_sha256": sha(owned), "runtime_object_sha256": sha(args.runtime_object),
        "build_b_wall_seconds": time.monotonic() - started,
        "cc": os.environ.get("CC", "cc"), "cflags": os.environ.get("CFLAGS", ""),
        "workloads": {},
    }
    for module in ("typed_ir.eri", "ir_verify.eri"):
        source = ROOT / "src/compiler" / module
        reference, actual = output / (module + ".reference.s"), output / (module + ".owned.s")
        journal.run([frontend, "emit-asm", source, "--source-root", ROOT / "src",
                     "--target", "x86_64-linux"], stdout_path=reference)
        before = time.monotonic()
        usage = output / (module + ".usage")
        number = journal.number + 1
        try:
            result = journal.run([sys.executable, "-c", MEASURE, usage,
                                  owned, "emit-asm", source, "--source-root", ROOT / "src",
                                  "--target", "x86_64-linux", "--trace-phases"], stdout_path=actual)
            if result.returncode or actual.read_bytes() != reference.read_bytes():
                raise AssertionError("source assembly parity failed: " + module)
            values = json.loads(usage.read_text())
            row = {"status": "completed", "assembly_parity": True,
                   "output_sha256": sha(actual), **values,
                   "rss_scope": "whole child wait4 high-water RSS, may include pre-exec launcher pages; not owner attribution"}
        except subprocess.TimeoutExpired:
            row = {"status": "censored-at-90s", "assembly_parity": None,
                   "observed_wall_seconds": time.monotonic() - before}
        events = [json.loads(line) for line in (output / "journal/events.jsonl").read_text().splitlines()]
        stack, phases = [], []
        for event in events:
            if event.get("command") != number or event["kind"] != "compiler_phase":
                continue
            key = (event["phase"], event["subject"])
            if event["event"] == "begin":
                stack.append((key, event["elapsed_seconds"]))
            else:
                if not stack or stack[-1][0] != key:
                    raise AssertionError("unbalanced compiler phase stream")
                _, began = stack.pop()
                phases.append({"phase": key[0], "subject": key[1],
                               "wall_seconds_inclusive": event["elapsed_seconds"] - began})
        row.update(source_sha256=sha(source), phases=phases,
                   unfinished_phases=[key for key, _ in stack],
                   phase_scope="inclusive streaming observations; nested phases overlap and are not additive")
        summary["workloads"][module] = row
        (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    summary["source_snapshot_unchanged"] = snapshot() == original
    if not summary["source_snapshot_unchanged"]:
        raise AssertionError("compiler inputs changed during profile")
    (output / "source-manifest.json").write_text(json.dumps(original, indent=2) + "\n")
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
