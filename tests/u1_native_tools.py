"""Build U1 test-only native compiler tools once per immutable checkout/process.

This cache is *never* persisted between test runs or GitHub jobs. It retains
the original compiler and optimization flags, only avoiding identical rebuilds
in the foundation, promotion and verifier test classes. All actual UIR test
programs, C/owned runtime linking and expected-output checks remain separate.
"""
from __future__ import annotations

from functools import lru_cache
import os
from pathlib import Path
import sys
import tempfile
import time

from compiler.erist.cli import build_native

ROOT = Path(__file__).resolve().parents[1]


def timed_native_step(name, action, *args, **kwargs):
    """Optional per-phase evidence; never modifies execution or timeouts."""
    started = time.monotonic()
    try:
        return action(*args, **kwargs)
    finally:
        if os.environ.get("ERISTAVI_TEST_TIMING") == "1":
            duration = time.monotonic() - started
            print(f"\n[U1 native timing] {name}: {duration:.3f}s",
                  file=sys.stderr, flush=True)


@lru_cache(maxsize=2)
def _build_shared(cc: str, cflags: str):
    temporary = tempfile.TemporaryDirectory(prefix="eristavi-u1-test-tools-")
    root = Path(temporary.name)
    try:
        frontend, generator = root / "frontend", root / "owned-runtime-generator"
        for source, binary, label in (
            (ROOT / "src/frontend.eri", frontend, "compile frontend"),
            (ROOT / "src/owned_runtime.eri", generator, "compile runtime generator"),
        ):
            result = timed_native_step(
                label, build_native, source, binary, ROOT / "src", cc=cc
            )
            if result != 0:
                raise AssertionError(f"U1 shared test {label} failed: {result}")
        # Retain temporary ownership for the process lifetime; cleanup on exit.
        return temporary, frontend, generator
    except BaseException:
        temporary.cleanup()
        raise


def shared_u1_compilers():
    """Reuse binaries only when the C compiler/flags and process are identical."""
    _, frontend, generator = _build_shared(
        os.environ.get("CC", "cc"), os.environ.get("CFLAGS", "")
    )
    return frontend, generator
