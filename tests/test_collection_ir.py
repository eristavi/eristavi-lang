from __future__ import annotations

import unittest

from compiler.erist.cli import analyze_frontend
from compiler.erist.ir import IRCount, IRIndex, IRIndexAssign, IRLet
from compiler.erist.ir_collections import IRBytes, IRMap, Lowerer


class CollectionIRTests(unittest.TestCase):
    def lower(self, source):
        program, analyzer = analyze_frontend(source)
        return Lowerer(analyzer).lower(program)

    def test_map_remains_distinct_in_typed_ir(self):
        program = self.lower('''
            let ages be ["Anna" : 32; "John" : 41;];
            let john be ages["John"];
            let count be ages.count;
            ages["Anna"] = 33;
        ''')
        self.assertIsInstance(program.entry[0], IRLet)
        self.assertIsInstance(program.entry[0].value, IRMap)
        self.assertEqual(program.entry[0].type_name, "Map from Text to Int")
        self.assertIsInstance(program.entry[1].value, IRIndex)
        self.assertEqual(program.entry[1].type_name, "Int")
        self.assertIsInstance(program.entry[2].value, IRCount)
        self.assertIsInstance(program.entry[3], IRIndexAssign)

    def test_bytes_remains_distinct_in_typed_ir(self):
        program = self.lower('''
            let data Bytes be [72, 101, 108];
            let middle be data[1];
            let count be data.count;
            data[1] = 97;
        ''')
        self.assertIsInstance(program.entry[0], IRLet)
        self.assertIsInstance(program.entry[0].value, IRBytes)
        self.assertEqual(program.entry[0].type_name, "Bytes")
        self.assertIsInstance(program.entry[1].value, IRIndex)
        self.assertEqual(program.entry[1].type_name, "Int")
        self.assertIsInstance(program.entry[2].value, IRCount)
        self.assertIsInstance(program.entry[3], IRIndexAssign)

    def test_plain_int_literal_sequence_is_still_list_ir(self):
        program = self.lower('let data be [72, 101, 108];')
        self.assertEqual(program.entry[0].type_name, "List of Int")
        self.assertNotIsInstance(program.entry[0].value, IRBytes)


if __name__ == "__main__":
    unittest.main()
