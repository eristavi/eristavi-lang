from __future__ import annotations

import platform
import subprocess
import tempfile
import unittest
from pathlib import Path

from compiler.erist.cli import build_direct

DIRECT_HOST = platform.system() == "Linux" and platform.machine().lower() in ("x86_64", "amd64")


@unittest.skipUnless(DIRECT_HOST, "checked direct execution currently targets x86-64 Linux")
class DirectCheckedErrorTests(unittest.TestCase):
    def compile_run(self, source: str):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "app.eri"
            exe = root / "app"
            src.write_text(source, encoding="utf-8")
            self.assertEqual(build_direct(src, exe, root), 0)
            return subprocess.run([str(exe)], capture_output=True, text=True)

    def test_catch_all_handler_exposes_message(self):
        p = self.compile_run(
            'error E { message Text; code Int; } '
            'function risky() returns Int fails E { fail E { message="bad"; code=7; }; } '
            'risky() else error { output(error.message); };'
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout, "bad\n")

    def test_typed_handler_reads_error_fields(self):
        p = self.compile_run(
            'error E { message Text; code Int; } '
            'function risky() returns Int fails E { fail E { message="bad"; code=42; }; } '
            'risky() else error E { output(error.message); output(error.code); };'
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout, "bad\n42\n")

    def test_try_propagates_through_function(self):
        p = self.compile_run(
            'error E { message Text; } '
            'function risky() returns Int fails E { fail E { message="deep"; }; } '
            'function outer() returns Int fails E { return try risky(); } '
            'outer() else error { output(error.message); };'
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout, "deep\n")

    def test_typed_handlers_select_failure_type(self):
        p = self.compile_run(
            'error A { message Text; } error B { message Text; code Int; } '
            'function risky(which Bool) returns Int fails A,B { '
            'if which { fail A { message="A"; }; } fail B { message="B"; code=9; }; } '
            'function show(which Bool){ risky(which) else error A { output("caught A"); } '
            'else error B { output(error.message); output(error.code); }; } '
            'show(true); show(false);'
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout, "caught A\nB\n9\n")

    def test_success_bypasses_handler_and_cleared_failure_does_not_leak(self):
        p = self.compile_run(
            'error E { message Text; } '
            'function value(ok Bool) returns Int fails E { if ok { return 7; } fail E { message="no"; }; } '
            'function run() { '
            'value(false) else error { output(error.message); }; '
            'let x be value(true) else error { output("failure"); return; }; output(x); } '
            'run();'
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout, "no\n7\n")

    def test_handler_can_propagate_new_failure(self):
        p = self.compile_run(
            'error E { message Text; } '
            'function bad(message Text) returns Int fails E { fail E { message=message; }; } '
            'function middle() returns Int fails E { return bad("second") else error E { return try bad("third"); }; } '
            'middle() else error { output(error.message); };'
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout, "third\n")


if __name__ == "__main__":
    unittest.main()
