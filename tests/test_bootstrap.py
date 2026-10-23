from __future__ import annotations

import unittest

from compiler.erist.cli import compile_frontend
from compiler.erist.diagnostics import SemanticError
from compiler.erist.runtime import Interpreter


class BootstrapTests(unittest.TestCase):
    def execute(self, source: str) -> list[str]:
        lines: list[str] = []
        program = compile_frontend(source)
        Interpreter(output=lines.append).run(program)
        return lines

    def test_hello(self):
        self.assertEqual(self.execute("let x be 40; let y be 2; output(x + y);"), ["42"])

    def test_fixed_reassignment_is_rejected(self):
        with self.assertRaises(SemanticError):
            compile_frontend("let fixed x be 1; x = 2;")

    def test_no_implicit_int_float_mixing(self):
        with self.assertRaises(SemanticError):
            compile_frontend("output(1 + 2.0);")

    def test_float_percent_is_rejected(self):
        with self.assertRaises(SemanticError):
            compile_frontend("output(10.0 % 3.0);")

    def test_signed_int_remainder(self):
        self.assertEqual(self.execute("output(-10 % 3);"), ["-1"])

    def test_nested_block_comments(self):
        self.assertEqual(self.execute("/* a /* nested */ comment */ output(2 + 2);"), ["4"])

    def test_boolean_precedence(self):
        self.assertEqual(self.execute("output(not 1 == 2 and true or false);"), ["true"])


if __name__ == "__main__":
    unittest.main()
