#!/usr/bin/env python3
"""Explicit current-baseline versus fixed-depth word-read pilot; no self-build.

The private candidate preserves all six current path reads/work charges. It
removes the runtime divisor loop and creation branches from noncreating reads.
The directory/page layout, public ABI and fresh canonical records stay intact.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]
from compiler.erist.cli import build_native
from u1_native_tools import shared_u1_compilers
from test_u1b_words_owner_poll_benchmark import prepare_source, compile_owned

BASE = "c2423d5b6211c4999a116e541fb11c67dfa2357d"
ANCHOR = "function pageAt(words identity Words,phase identity budget.Phase,index Int,create Bool)"


def candidate_words(original):
    # Exact six-level radix adapter; no persistent handle/page cache or new
    # charge. work() precedes each current child read, including on refusal.
    body = ("// Fixed-depth noncreating traversal. Preserve each charged current child read.\n"
            "function readPath(words identity Words,phase identity budget.Phase,index Int) "
            "returns identity Page fails budget.LimitError {\n"
            "    let node be try needNode(words.root); let pageIndex be index/16;\n")
    for divisor in (1048576, 65536, 4096, 256, 16, 1):
        offset = "pageIndex%16" if divisor == 1 else f"pageIndex/{divisor}%16"
        body += ("    try budget.work(phase,1);\n"
                 f"    node=try needNode(readChild(node,{offset}));\n")
    body += "    return try needPage(node.page);\n}\n"
    if original.count(ANCHOR) != 1:
        raise AssertionError("word-path anchor changed")
    result = original.replace(ANCHOR, body + ANCHOR)
    old = "let page be try pageAt(words,phase,index,false);"
    if result.count(old) != 2:
        raise AssertionError("noncreating read/write callsites changed")
    return result.replace(old, "let page be try readPath(words,phase,index);")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def checked(args, timeout=240):
    result = subprocess.run(list(map(str, args)), capture_output=True, timeout=timeout)
    if result.returncode or result.stderr:
        raise AssertionError((args, result.returncode, result.stderr[-3000:]))
    return result.stdout


def prepare(output):
    fixture = (ROOT / "tests/fixtures/u1_aggregate_calls.eri").read_text()
    original = subprocess.check_output(
        ["git", "show", BASE + ":src/compiler/u1_words.eri"], cwd=ROOT).decode()
    candidate = candidate_words(original)
    sources = {}
    for name, words in (("baseline", original), ("candidate", candidate)):
        directory = output / (name + "-source")
        sources[name] = prepare_source(directory, fixture, words)
    oracle = output / "oracle"
    if build_native(sources["baseline"], oracle, sources["baseline"].parent) != 0:
        raise AssertionError("bootstrap oracle failed to compile")
    expected = checked([oracle], 120)
    if b"u1b-aggregate-calls:ok" not in expected:
        raise AssertionError("missing independent fixture acceptance")
    (output / "expected.stdout").write_bytes(expected)
    frontend, generator = shared_u1_compilers()
    runtime = checked([generator], 120)
    (output / "runtime.s").write_bytes(runtime)
    checked(["as", "--64", output / "runtime.s", "-o", output / "runtime.o"], 60)
    identities = {
        "baseline_commit": BASE, "fixture_sha256": sha(fixture.encode()),
        "baseline_words_sha256": sha(original.encode()),
        "candidate_words_sha256": sha(candidate.encode()),
        "shared_runtime_sha256": sha(runtime), "expected_stdout_sha256": sha(expected),
        "cc": os.environ.get("CC", "cc"), "cflags": os.environ.get("CFLAGS", ""),
        "host": platform.platform(), "machine": platform.machine(),
        "compiler": subprocess.check_output([os.environ.get("CC", "cc"), "--version"], text=True).splitlines()[0],
    }
    for name, source in sources.items():
        asm = compile_owned(frontend, source, source.parent).encode()
        (output / (name + ".s")).write_bytes(asm)
        checked(["as", "--64", output / (name + ".s"), "-o", output / (name + ".o")], 60)
        checked(["ld", "-nostdlib", "-static", "-e", "_start", output / (name + ".o"),
                 output / "runtime.o", "-o", output / name], 60)
        identities[name + "_assembly_sha256"] = sha(asm)
        identities[name + "_binary_sha256"] = sha((output / name).read_bytes())
    (output / "identities.json").write_text(json.dumps(identities, indent=2) + "\n")
    return identities


def measure(binary, expected, directory):
    directory.mkdir()
    started = time.monotonic()
    with (directory / "stdout").open("wb") as out, (directory / "stderr").open("wb") as err:
        child = subprocess.Popen([str(binary)], stdout=out, stderr=err,
                                 env={"PATH": "/unavailable", "LANG": "C", "LC_ALL": "C"})
        while True:
            pid, status, usage = os.wait4(child.pid, os.WNOHANG)
            if pid:
                child.returncode = os.waitstatus_to_exitcode(status)
                break
            if time.monotonic() - started > 240:
                child.kill()
                _, status, _ = os.wait4(child.pid, 0)
                child.returncode = os.waitstatus_to_exitcode(status)
                raise TimeoutError("unchanged 240-second linked benchmark watchdog")
            time.sleep(0.01)
    wall = time.monotonic() - started
    stdout, stderr = (directory / "stdout").read_bytes(), (directory / "stderr").read_bytes()
    if (child.returncode, stdout, stderr) != (0, expected, b""):
        raise AssertionError((binary, child.returncode, stdout[-1000:], stderr[-1000:]))
    return {"wall_seconds": wall, "user_seconds": usage.ru_utime,
            "system_seconds": usage.ru_stime, "peak_rss_KiB": usage.ru_maxrss,
            "stdout_sha256": sha(stdout), "correct": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pairs", type=int, choices=(1, 5), default=1)
    parser.add_argument("--reuse", action="store_true")
    args = parser.parse_args()
    if platform.system() != "Linux" or platform.machine().lower() not in ("x86_64", "amd64"):
        raise SystemExit("requires Linux x86-64")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    identities = json.loads((output / "identities.json").read_text()) if args.reuse else prepare(output)
    expected = (output / "expected.stdout").read_bytes()
    if sha(expected) != identities["expected_stdout_sha256"]:
        raise AssertionError("oracle output changed")
    for name in ("baseline", "candidate"):
        if sha((output / name).read_bytes()) != identities[name + "_binary_sha256"]:
            raise AssertionError("timed binary changed")
    samples = {"baseline": [], "candidate": []}
    report = {"scope": "one full linked fixture, current optimized owned baseline versus private fixed-depth read; not whole-compiler speed",
              "identities": identities, "samples": samples, "pairs": args.pairs,
              "order": "AB" if args.pairs == 1 else "AB/BA/AB/BA/AB",
              "rss_scope": "whole child process; may include inherited launcher high-water pages, not owner backing",
              "source_semantics_ABI_budgets_unchanged": True}
    for i in range(args.pairs):
        order = ("baseline", "candidate") if i % 2 == 0 else ("candidate", "baseline")
        for name in order:
            sample = measure(output / name, expected, output / f"{args.pairs}-pair-{i + 1}-{name}")
            samples[name].append(sample)
            (output / f"{args.pairs}-pairs.json").write_text(json.dumps(report, indent=2) + "\n")
            print(name, i + 1, sample, flush=True)
    medians = {name: statistics.median(s["wall_seconds"] for s in rows) for name, rows in samples.items()}
    report.update(median_seconds=medians, candidate_over_baseline=medians["candidate"] / medians["baseline"],
                  pairwise_saved_percent=[100 * (1 - b["wall_seconds"] / a["wall_seconds"])
                                          for a, b in zip(samples["baseline"], samples["candidate"])])
    (output / f"{args.pairs}-pairs.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
