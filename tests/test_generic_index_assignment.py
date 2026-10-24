from __future__ import annotations

import unittest

from compiler.erist.cli import compile_frontend
from compiler.erist.runtime import Interpreter


class GenericListRelationshipTests(unittest.TestCase):
    def execute(self, source: str) -> list[str]:
        output: list[str] = []
        program = compile_frontend(source)
        Interpreter(output=output.append).run(program)
        return output

    def test_generic_index_assignment_infers_list_element_relationship(self):
        source = (
            'function replace(values, index Int, value) { '
            'values[index] = value; '
            'return values; '
            '} '
            'let ints be replace([1,2], 1, 9); '
            'let texts be replace(["a","b"], 0, "z"); '
            'output(ints[1]); '
            'output(texts[0]);'
        )
        self.assertEqual(self.execute(source), ['9', 'z'])

    def test_generic_for_infers_list_element_relationship(self):
        source = (
            'function sum(values) returns Int { '
            'let total be 0; '
            'for value in values { total = total + value; } '
            'return total; '
            '} '
            'output(sum([1,2,3]));'
        )
        self.assertEqual(self.execute(source), ['6'])

    def test_optional_identity_snapshot_survives_alias_write(self):
        source = (
            'type Node { value Int; next maybe identity Node; } '
            'let tail be identity Node { value=2; next=none; }; '
            'let head be identity Node { value=1; next=tail; }; '
            'let snapshot be head.next; '
            'if snapshot != none { head.next = none; output(snapshot.value); }'
        )
        self.assertEqual(self.execute(source), ['2'])


if __name__ == '__main__':
    unittest.main()
