#!/usr/bin/env python3
"""Same-host AB/BA owned-runtime A/B benchmark; independent exact worker oracle.

Uses Git worktrees pinned to the pre-optimization commit and to the qualified
post-optimization commit. Builds a single unchanged application assembly, then
links it to independently generated owned runtime assemblies. No compiler
self-build, frozen language changes, production runtime modifications, or CI
test replacement. This is an opt-in profiling tool, not normal PR smoke.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import shutil
import statistics
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from compiler.erist.cli import build_native
from test_u1_integer_execution import (
    BOUNDARIES, MAX, MIN, MODES, OVERFLOW, expected_lines, source_for,
)

BASE = "4f876009c9786d4e47807d42fe91d922f147a2b4"
OPT = "388bfb6da42a6c0c1de307a0aa72ea987b63bbb0"


def checked(cmd, *, cwd=None, timeout=120, env=None):
    result = subprocess.run(
        [str(x) for x in cmd], cwd=cwd, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout,
    )
    if result.returncode:
        raise RuntimeError(
            f"command failed ({result.returncode}): {cmd}\n"
            + result.stderr.decode("utf-8", "replace")[-3000:]
        )
    return result.stdout


def identity(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_workers():
    # Same recipes and all eight worker groups as the qualified test.
    recipes = [
        (mode, [(MIN, MIN), (MIN, -1)] if mode in (24, 25) else [(MIN, MIN)], False, 0)
        for mode in MODES
    ]
    recipes += [(mode, [(-1, 3)], False, 0) for mode in OVERFLOW + (26, 27)]
    recipes += [
        (mode, [(-2, MAX), (MAX, 0)], True, 2)
        for mode in (203, 220, 26, 127)
    ]
    groups = [
        (recipes[:13], False), (recipes[13:26], False),
        (recipes[26:34], False),
    ]
    groups += [(recipes[i:i + 1], False) for i in range(34, len(recipes))]
    groups += [([], True)]
    assert len(groups) == 8, len(groups)
    return groups


def make_executables(workdir: Path, compiler: str):
    baseline_dir = workdir / "before"
    # The worktree uses only the pre-PR99 runtime, never an unrelated PR.
    checked(["git", "worktree", "add", "--detach", baseline_dir, BASE], cwd=ROOT)
    try:
        # Require identical compiler and fixtures between both endpoints.
        unmodified = [
            "src/compiler", "src/frontend.eri", "src/owned_runtime.eri",
            "tests/fixtures/u1_integer_execution.eri",
        ]
        checked(["git", "diff", "--exit-code", BASE, OPT, "--", *unmodified], cwd=ROOT)
        checked(["git", "diff", "--exit-code", OPT, "HEAD", "--",
                 "src/runtime", "src/owned_runtime.eri"], cwd=ROOT)
        from u1_native_tools import shared_u1_compilers
        frontend, generator_after = shared_u1_compilers()

        generated_source = workdir / "worker.eri"
        generated_source.write_text(source_for([], groups=build_workers()), encoding="utf-8")
        (workdir / "compiler").symlink_to(ROOT / "src/compiler", target_is_directory=True)
        application_assembly = checked([
            frontend, "emit-asm", generated_source, "--source-root", workdir,
            "--target", "x86_64-linux",
        ], timeout=120)
        (workdir / "program.s").write_bytes(application_assembly)
        checked(["as", "--64", workdir / "program.s", "-o", workdir / "program.o"],
                timeout=30)
        # Baseline generator is compiled from the immutable pre-PR99 source.
        baseline_generator = workdir / "generator-before"
        result = build_native(
            baseline_dir / "src/owned_runtime.eri", baseline_generator,
            baseline_dir / "src", cc=compiler,
        )
        if result != 0:
            raise RuntimeError(f"baseline runtime generator failed: {result}")
        builds = {}
        for label, gen in (("before", baseline_generator),
                           ("after", generator_after)):
            asm = checked([gen], timeout=90)
            (workdir / f"runtime-{label}.s").write_bytes(asm)
            checked(["as", "--64", workdir / f"runtime-{label}.s", "-o",
                     workdir / f"runtime-{label}.o"], timeout=45)
            binary = workdir / label
            checked(["ld", "-nostdlib", "-static", "-e", "_start",
                     workdir / "program.o", workdir / f"runtime-{label}.o",
                     "-o", binary], timeout=45)
            hdr = checked(["readelf", "-lW", binary]).decode()
            if "INTERP" in hdr or "DYNAMIC" in hdr:
                raise RuntimeError("owned binary unexpectedly uses dynamic linking")
            builds[label] = {
                "runtime_assembly_sha256": identity(asm),
                "binary_sha256": identity(binary.read_bytes()),
                "binary": str(binary),
            }
        return builds, identity(application_assembly)
    finally:
        # Baseline worktree source remains available until all generators
        # have finished; it may be dropped after the successful build.
        checked(["git", "worktree", "remove", "--force", baseline_dir], cwd=ROOT)


def run_one(binary: str, expected: list[str], timeout: float, trial_dir: Path):
    # Single child at a time, with exact per-process wait4 usage. Linux RSS
    # is KiB. No timers/signals/ptrace or instrumentation in timed executables.
    trial_dir.mkdir(parents=True, exist_ok=True)
    out_path, err_path = trial_dir / "stdout", trial_dir / "stderr"
    started = time.monotonic()
    with out_path.open("wb") as output, err_path.open("wb") as error:
        child = subprocess.Popen([binary, "0"], stdout=output, stderr=error,
                                 env={"PATH": "/unavailable", "LANG": "C", "LC_ALL": "C"})
        while True:
            pid, status, usage = os.wait4(child.pid, os.WNOHANG)
            if pid == child.pid:
                code = os.waitstatus_to_exitcode(status)
                break
            if time.monotonic() - started > timeout:
                child.kill()
                os.wait4(child.pid, 0)
                raise RuntimeError(f"timed out after {timeout}s: {binary}")
            time.sleep(0.02)
    wall = time.monotonic() - started
    data, stderr = out_path.read_bytes(), err_path.read_bytes()
    lines = data.decode("utf-8").splitlines()
    if code != 0 or stderr or lines != expected:
        raise AssertionError(
            f"independent worker oracle failed for {binary} code={code}, "
            f"stderr={stderr[-200:]!r}, stdout tail={lines[-6:]!r}, "
            f"expected tail={expected[-6:]!r}"
        )
    return {
        "wall_seconds": round(wall, 6), "user_cpu_seconds": round(usage.ru_utime, 6),
        "system_cpu_seconds": round(usage.ru_stime, 6),
        "peak_rss_KiB": usage.ru_maxrss, "output_sha256": identity(data),
        "output_lines": len(lines), "return_code": code,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--pairs", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args()
    if not (1 <= args.pairs <= 5):
        parser.error("paired run count must be 1..5")
    if platform.system() != "Linux" or platform.machine().lower() not in ("x86_64", "amd64"):
        parser.error("benchmark requires Linux x86-64 because owned runtime is target-specific")

    for tool in ("git", "cc", "clang", "as", "ld", "readelf"):
        if not shutil.which(tool):
            parser.error(f"missing required {tool} executable")

    actual_base = checked(["git", "rev-parse", BASE], cwd=ROOT).decode().strip()
    actual_opt = checked(["git", "rev-parse", OPT], cwd=ROOT).decode().strip()
    if (actual_base, actual_opt) != (BASE, OPT):
        raise RuntimeError("historical revisions do not match pinned endpoints")
    tracked = checked(["git", "status", "--porcelain", "--", "src/runtime"], cwd=ROOT)
    if tracked:
        raise RuntimeError("dirty source runtime is not a valid benchmark candidate")

    original = build_workers()[0][0]
    expected = expected_lines(original)
    series = []
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="eristavi-owned-paired-") as temp:
        workdir = Path(temp)
        builds, asm_digest = make_executables(workdir, "clang")
        for pair in range(args.pairs):
            # Alternating AB / BA orders guard against monotone cache or
            # runner-load drift. Never concurrently execute measured children.
            order = ("before", "after") if pair % 2 == 0 else ("after", "before")
            observations = []
            for j, label in enumerate(order):
                observation = run_one(builds[label]["binary"], expected,
                                      args.timeout, workdir / f"pair-{pair}-{j}")
                observation.update(pair=pair + 1, order_position=j + 1, variant=label)
                observations.append(observation)
                print(f"[pair {pair + 1}] {label}: {observation['wall_seconds']:.3f}s, "
                      f"CPU {observation['user_cpu_seconds']:.3f}s, "
                      f"RSS {observation['peak_rss_KiB']} KiB", flush=True)
            if observations[0]["output_sha256"] != observations[1]["output_sha256"]:
                raise AssertionError("the baseline and optimized output digests disagree")
            series.extend(observations)
    base_wall = [x["wall_seconds"] for x in series if x["variant"] == "before"]
    opt_wall = [x["wall_seconds"] for x in series if x["variant"] == "after"]
    record = {
        "status": "success",
        "scope": "production owned runtime worker 0 only; one unchanged native app assembly",
        "baseline": BASE, "optimized": OPT,
        "checkout": checked(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
        "platform": platform.platform(), "processor": platform.processor(),
        "ci_run_id": os.environ.get("GITHUB_RUN_ID"),
        "host_os": platform.uname()._asdict(),
        "cc": checked(["clang", "--version"]).decode(errors="replace").splitlines()[0],
        "application_assembly_sha256": asm_digest,
        "expected_oracle": "independent test_u1_integer_execution.expected_lines(worker0)",
        "builds": {
            k: {kk: vv for kk, vv in v.items() if kk != "binary"}
            for k, v in builds.items()
        },
        "pairs": args.pairs,
        "order": "AB, BA alternating, one process at a time",
        "cache": "not flushed; source/app generated once before samples",
        "measurements": series,
        "medians": {
            "baseline_wall_seconds": round(statistics.median(base_wall), 6),
            "optimized_wall_seconds": round(statistics.median(opt_wall), 6),
            "wall_ratio": round(statistics.median(base_wall) / statistics.median(opt_wall), 4),
        },
        "limitations": [
            "Comparing worker0 runtime execution, not compilation or full CI",
            "Each process includes non-UIR runtime; RSS not UIR ownership attribution",
            "Linux ru_maxrss is KiB; does not isolate BSS from allocator/GC",
            "No full owned self-build or U2/U3/U4 qualification",
        ],
        "total_benchmark_seconds": round(time.monotonic() - started, 3),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("PAIRED_OWNED_RUNTIME=" + json.dumps(record["medians"], sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
