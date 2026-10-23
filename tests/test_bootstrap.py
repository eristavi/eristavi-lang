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
        self.assertEqual(
            self.execute("let x be 40; let y be 2; output(x + y);"),
            ["42"],
        )

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

    def test_explicit_return_function(self):
        self.assertEqual(
            self.execute(
                "function add(a Int, b Int) returns Int { return a + b; } "
                "output(add(20, 22));"
            ),
            ["42"],
        )

    def test_inferred_return_function(self):
        self.assertEqual(
            self.execute(
                "function double(value Int) { return value * 2; } "
                "output(double(21));"
            ),
            ["42"],
        )

    def test_no_value_function(self):
        self.assertEqual(
            self.execute(
                'function greet(name Text) { output(name); } greet("Hello");'
            ),
            ["Hello"],
        )

    def test_bare_return_in_no_value_function(self):
        self.assertEqual(
            self.execute(
                "function greet(active Bool) { "
                "if not active { return; } output(\"Hello\"); } "
                "greet(false); greet(true);"
            ),
            ["Hello"],
        )

    def test_no_value_call_in_value_context_is_rejected(self):
        with self.assertRaises(SemanticError):
            compile_frontend(
                'function greet() { output("x"); } let x be greet();'
            )

    def test_missing_return_path_is_rejected(self):
        with self.assertRaises(SemanticError):
            compile_frontend(
                "function choose(flag Bool) { if flag { return 1; } }"
            )

    def test_incompatible_inferred_returns_are_rejected(self):
        with self.assertRaises(SemanticError):
            compile_frontend(
                'function choose(flag Bool) { '
                'if flag { return 1; } else { return "one"; } }'
            )

    def test_bare_return_in_value_function_is_rejected(self):
        with self.assertRaises(SemanticError):
            compile_frontend(
                "function choose(flag Bool) returns Int { "
                "if flag { return 1; } return; }"
            )

    def test_recursive_explicit_return(self):
        source = (
            "function factorial(n Int) returns Int { "
            "if n <= 1 { return 1; } "
            "return n * factorial(n - 1); } "
            "output(factorial(5));"
        )
        self.assertEqual(self.execute(source), ["120"])

    def test_recursive_inferred_return_is_rejected(self):
        source = (
            "function factorial(n Int) { "
            "if n <= 1 { return 1; } "
            "return n * factorial(n - 1); }"
        )
        with self.assertRaises(SemanticError):
            compile_frontend(source)

    def test_function_declarations_are_order_independent(self):
        source = (
            "function first() returns Int { return second(); } "
            "function second() returns Int { return 42; } "
            "output(first());"
        )
        self.assertEqual(self.execute(source), ["42"])

    def test_forward_inferred_function(self):
        source = (
            "function first() { return second(); } "
            "function second() { return 42; } "
            "output(first());"
        )
        self.assertEqual(self.execute(source), ["42"])

    def test_mutual_recursive_inferred_return_is_rejected(self):
        source = (
            "function a(n Int) { if n == 0 { return 0; } return b(n - 1); } "
            "function b(n Int) { if n == 0 { return 0; } return a(n - 1); }"
        )
        with self.assertRaises(SemanticError):
            compile_frontend(source)

    def test_recursive_no_value_function_needs_no_return_contract(self):
        source = (
            "function countdown(n Int) { "
            "if n > 0 { output(n); countdown(n - 1); } } "
            "countdown(3);"
        )
        self.assertEqual(self.execute(source), ["3", "2", "1"])

    def test_duplicate_parameter_is_rejected(self):
        with self.assertRaises(SemanticError):
            compile_frontend(
                "function f(x Int, x Int) returns Int { return x; }"
            )

    def test_parameter_shadowing_is_rejected(self):
        with self.assertRaises(SemanticError):
            compile_frontend(
                "function f(x Int) returns Int { let x be 1; return x; }"
            )

    def test_parameter_is_mutable_local_value(self):
        source = (
            "function increment(value Int) returns Int { "
            "value = value + 1; return value; } "
            "let original be 1; "
            "output(increment(original)); output(original);"
        )
        self.assertEqual(self.execute(source), ["2", "1"])

    def test_wrong_argument_type_is_rejected(self):
        with self.assertRaises(SemanticError):
            compile_frontend(
                'function f(x Int) returns Int { return x; } output(f("x"));'
            )

    def test_wrong_arity_is_rejected(self):
        with self.assertRaises(SemanticError):
            compile_frontend(
                "function f(x Int) returns Int { return x; } output(f());"
            )

    def test_function_after_entry_statement_is_rejected(self):
        with self.assertRaises(SemanticError):
            compile_frontend('output("start"); function f() { }')

    def test_top_level_return_is_rejected(self):
        with self.assertRaises(SemanticError):
            compile_frontend("return;")


if __name__ == "__main__":
    unittest.main()
