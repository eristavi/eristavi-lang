from __future__ import annotations
import unittest
from compiler.erist.cli import analyze_frontend
from compiler.erist.diagnostics import SemanticError
from compiler.erist.runtime_ext import Interpreter
from compiler.erist.typesys import INT, ListType, TypeVar, specialization_key


class RecursiveInferenceTests(unittest.TestCase):
    def execute(self, source):
        program, _ = analyze_frontend(source)
        output = []
        Interpreter(output.append).run(program)
        return output

    def test_specialization_keys_preserve_relationships_not_variable_ids(self):
        a, b, c = TypeVar('a'), TypeVar('b'), TypeVar('c')
        self.assertEqual(specialization_key([a, ListType(a), b]),
                         specialization_key([b, ListType(b), c]))
        self.assertNotEqual(specialization_key([a, a]), specialization_key([a, b]))
        self.assertEqual(specialization_key([INT, ListType(INT)]), ('Int', 'List of Int'))

    def test_direct_generic_recursion_with_explicit_result(self):
        source = ('function depth(value, n Int) returns Int { '
                  'if n == 0 { return 0; } return depth(value, n - 1) + 1; } '
                  'output(depth("A", 4)); output(depth(42, 3));')
        self.assertEqual(self.execute(source), ['4', '3'])

    def test_mutual_generic_recursion_with_explicit_result(self):
        source = ('function even(value, n Int) returns Bool { '
                  'if n == 0 { return true; } return odd(value, n - 1); } '
                  'function odd(value, n Int) returns Bool { '
                  'if n == 0 { return false; } return even(value, n - 1); } '
                  'output(even("A", 4)); output(odd(42, 3));')
        self.assertEqual(self.execute(source), ['true', 'true'])

    def test_recursive_result_inference_still_requires_explicit_contract(self):
        with self.assertRaisesRegex(SemanticError, 'circular result inference'):
            analyze_frontend('function loop(value) { return loop(value); }')

    def test_try_allows_no_value_calls_as_statements_and_preserves_failures(self):
        source = ('error E { message Text; } '
                  'function failNow() fails E { fail E { message = "expected"; }; } '
                  'function outer() fails E { try failNow(); } '
                  'outer() else error E { output(error.message); };')
        self.assertEqual(self.execute(source), ['expected'])
        with self.assertRaises(SemanticError):
            analyze_frontend('function noValue() {} function value() { return try noValue(); }')
