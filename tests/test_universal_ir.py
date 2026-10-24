from __future__ import annotations

import platform
import subprocess
import tempfile
import unittest
from pathlib import Path

from compiler.erist.cli import build_direct, lower_universal_file
from compiler.erist.universal_ir import UBranch, UJump, format_program


DIRECT_HOST = platform.system() == "Linux" and platform.machine().lower() in ("x86_64", "amd64")


class UniversalIRTests(unittest.TestCase):
    def source(self, text: str):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        src = root / "app.eri"
        src.write_text(text, encoding="utf-8")
        return td, root, src

    def test_universal_ir_has_explicit_checked_arithmetic_and_control_flow(self):
        td, root, src = self.source(
            "let x be 1; let y be 2; let z be x + y; "
            "if z == 3 { output(z); } else { output(0); }"
        )
        try:
            program = lower_universal_file(src, root)
            text = format_program(program)
            self.assertIn("add_checked", text)
            self.assertIn("cmp_eq", text)
            self.assertIn("branch", text)
            self.assertTrue(any(isinstance(block.terminator, UBranch) for block in program.function("__entry").blocks))
        finally:
            td.cleanup()

    def test_universal_ir_while_uses_basic_blocks(self):
        td, root, src = self.source("let n be 0; while n < 3 { n = n + 1; } output(n);")
        try:
            program = lower_universal_file(src, root)
            names = [block.name for block in program.function("__entry").blocks]
            self.assertTrue(any(name.startswith("while.cond") for name in names))
            self.assertTrue(any(isinstance(block.terminator, UJump) for block in program.function("__entry").blocks))
        finally:
            td.cleanup()

    def test_universal_ir_contains_function_contract_and_call(self):
        td, root, src = self.source(
            "function add(a Int, b Int) returns Int { return a + b; } output(add(20, 22));"
        )
        try:
            text = format_program(lower_universal_file(src, root))
            self.assertIn("function @add($0 a: i64, $1 b: i64) -> i64", text)
            self.assertIn("call 'add'", text)
            self.assertIn("return %", text)
        finally:
            td.cleanup()

    @unittest.skipUnless(DIRECT_HOST, "direct x86-64 backend executes on x86-64 Linux")
    def test_direct_x86_64_hello(self):
        p = self.compile_run("let x be 40; let y be 2; output(x + y);")
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout, "42\n")

    @unittest.skipUnless(DIRECT_HOST, "direct x86-64 backend executes on x86-64 Linux")
    def test_direct_x86_64_if_while_and_bool(self):
        p = self.compile_run(
            "let n be 0; while n < 3 { n = n + 1; } "
            "if n == 3 { output(true); output(n); } else { output(false); }"
        )
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout, "true\n3\n")

    @unittest.skipUnless(DIRECT_HOST, "direct x86-64 backend executes on x86-64 Linux")
    def test_direct_x86_64_function_call_and_recursion(self):
        p = self.compile_run(
            "function factorial(value Int) returns Int { "
            "if value <= 1 { return 1; } return value * factorial(value - 1); } "
            "function calculate(value Int) returns Int { return factorial(value) + 10; } "
            "output(calculate(5));"
        )
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout, "130\n")

    @unittest.skipUnless(DIRECT_HOST, "direct x86-64 backend executes on x86-64 Linux")
    def test_direct_x86_64_stack_arguments_beyond_six(self):
        p = self.compile_run(
            "function sum8(a Int,b Int,c Int,d Int,e Int,f Int,g Int,h Int) returns Int { "
            "return a+b+c+d+e+f+g+h; } output(sum8(1,2,3,4,5,6,7,8));"
        )
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout, "36\n")

    @unittest.skipUnless(DIRECT_HOST, "direct x86-64 backend executes on x86-64 Linux")
    def test_direct_x86_64_float_calls_and_arithmetic(self):
        p = self.compile_run(
            "function average(a Float, b Float) returns Float { return (a + b) / 2.0; } "
            "output(average(3.0, 4.0)); output(0.0 / 0.0 == 0.0 / 0.0);"
        )
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout, "3.5\nfalse\n")

    @unittest.skipUnless(DIRECT_HOST, "direct x86-64 backend executes on x86-64 Linux")
    def test_direct_x86_64_text_length_aware_operations(self):
        p = self.compile_run(
            'function greet(name Text) returns Text { return "Hello, " + name; } '
            'let text be greet("A\\0B"); output(text); output(text == "Hello, A\\0B");'
        )
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout.encode(), b"Hello, A\x00B\ntrue\n")

    @unittest.skipUnless(DIRECT_HOST, "direct x86-64 backend executes on x86-64 Linux")
    def test_direct_x86_64_signed_division_and_remainder(self):
        p = self.compile_run("output(-10 / 3); output(-10 % 3); output(10 % -3);")
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout, "-3\n-1\n1\n")

    @unittest.skipUnless(DIRECT_HOST, "direct x86-64 backend executes on x86-64 Linux")
    def test_direct_x86_64_overflow_inside_function_terminates(self):
        p = self.compile_run(
            "function overflow(value Int) returns Int { return value + 1; } "
            "output(overflow(9223372036854775807));"
        )
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("Int arithmetic overflow", p.stderr)

    @unittest.skipUnless(DIRECT_HOST, "direct x86-64 backend executes on x86-64 Linux")
    def test_direct_x86_64_division_by_zero_fault(self):
        p = self.compile_run("let zero be 0; output(10 / zero);")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("Int division by zero", p.stderr)

    def compile_run(self, source: str):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "app.eri"
            exe = root / "app"
            src.write_text(source, encoding="utf-8")
            self.assertEqual(build_direct(src, exe, root), 0)
            return subprocess.run([str(exe)], capture_output=True, text=False)


if __name__ == "__main__":
    unittest.main()
