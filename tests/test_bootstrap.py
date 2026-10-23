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
        self.assertEqual(
            self.execute("/* a /* nested */ comment */ output(2 + 2);"),
            ["4"],
        )

    def test_boolean_precedence(self):
        self.assertEqual(
            self.execute("output(not 1 == 2 and true or false);"),
            ["true"],
        )

    def test_basic_type_annotations(self):
        self.assertEqual(
            self.execute(
                'let count Int be 3; let message Text be "ready"; '
                "output(count); output(message);"
            ),
            ["3", "ready"],
        )

    def test_annotation_mismatch_is_rejected(self):
        with self.assertRaises(SemanticError):
            compile_frontend("let count Float be 3;")

    def test_if_else_executes_selected_branch(self):
        self.assertEqual(
            self.execute(
                'let x be 1; if x == 1 { output("yes"); } '
                'else { output("no"); }'
            ),
            ["yes"],
        )

    def test_if_requires_bool_condition(self):
        with self.assertRaises(SemanticError):
            compile_frontend("if 1 { output(1); }")

    def test_block_binding_does_not_leak(self):
        with self.assertRaises(SemanticError):
            compile_frontend("if true { let x be 1; } output(x);")

    def test_nested_shadowing_is_rejected(self):
        with self.assertRaises(SemanticError):
            compile_frontend("let x be 1; if true { let x be 2; }")

    def test_block_can_assign_visible_outer_binding(self):
        self.assertEqual(
            self.execute("let x be 1; if true { x = 2; } output(x);"),
            ["2"],
        )

    def test_while_loop(self):
        self.assertEqual(
            self.execute(
                "let i Int be 0; while i < 3 { output(i); i = i + 1; }"
            ),
            ["0", "1", "2"],
        )

    def test_sibling_blocks_may_reuse_local_name(self):
        self.assertEqual(
            self.execute(
                "if true { let x be 1; output(x); } "
                "if true { let x be 2; output(x); }"
            ),
            ["1", "2"],
        )


if __name__ == "__main__":
    unittest.main()
