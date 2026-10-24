from __future__ import annotations

import unittest

from compiler.erist.cli import compile_frontend
from compiler.erist.runtime import Interpreter


class GenericIndexAssignmentTests(unittest.TestCase):
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


if __name__ == '__main__':
    unittest.main()
