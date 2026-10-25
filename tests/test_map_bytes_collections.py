from __future__ import annotations

import unittest

from compiler.erist.cli import compile_frontend
from compiler.erist.diagnostics import RuntimeFault, SemanticError
from compiler.erist.runtime import Interpreter


class MapBytesCollectionTests(unittest.TestCase):
    def execute(self, source):
        output = []
        program = compile_frontend(source)
        Interpreter(output=output.append).run(program)
        return output

    def bad(self, source):
        with self.assertRaises(SemanticError):
            compile_frontend(source)

    def test_map_literal_lookup_count_and_output(self):
        source = '''
        let ages be [
            "Anna" : 32;
            "John" : 41;
        ];
        output(ages.count);
        output(ages["John"]);
        output(ages);
        '''
        self.assertEqual(self.execute(source), ["2", "41", '["Anna" : 32; "John" : 41;]'])

    def test_map_assignment_updates_and_inserts(self):
        source = '''
        let ages be ["Anna" : 32;];
        ages["Anna"] = 33;
        ages["John"] = 41;
        output(ages["Anna"]);
        output(ages["John"]);
        output(ages.count);
        '''
        self.assertEqual(self.execute(source), ["33", "41", "2"])

    def test_empty_map_infers_from_index_assignment(self):
        self.assertEqual(
            self.execute('let values be [:]; values["answer"] = 42; output(values["answer"]);'),
            ["42"],
        )

    def test_map_value_semantics(self):
        source = '''
        let first be ["a" : 1;];
        let second be first;
        second["a"] = 2;
        second["b"] = 3;
        output(first["a"]);
        output(first.count);
        output(second["a"]);
        output(second.count);
        '''
        self.assertEqual(self.execute(source), ["1", "1", "2", "2"])

    def test_map_literal_rejects_duplicate_static_key(self):
        self.bad('let values be ["a" : 1; "a" : 2;];')

    def test_map_requires_homogeneous_keys_and_values(self):
        self.bad('let values be ["a" : 1; 2 : 3;];')
        self.bad('let values be ["a" : 1; "b" : "two";];')

    def test_map_float_key_is_rejected(self):
        self.bad('let values be [1.0 : "one";];')

    def test_missing_map_key_is_runtime_fault(self):
        with self.assertRaises(RuntimeFault):
            self.execute('let values be ["a" : 1;]; output(values["missing"]);')

    def test_bytes_use_list_literal_only_with_bytes_context(self):
        source = '''
        let data Bytes be [72, 101, 108, 108, 111];
        output(data);
        output(data.count);
        output(data[1]);
        data[1] = 97;
        output(data);
        '''
        self.assertEqual(self.execute(source), ["[72, 101, 108, 108, 111]", "5", "101", "[72, 97, 108, 108, 111]"])

    def test_plain_byte_sized_integers_still_infer_list(self):
        self.assertEqual(
            self.execute('let data be [72,101]; data.add(108); output(data.count);'),
            ["3"],
        )

    def test_bytes_literal_rejects_out_of_range_value(self):
        self.bad('let data Bytes be [0, 256];')
        self.bad('let data Bytes be [-1, 2];')

    def test_bytes_parameter_provides_literal_context(self):
        source = '''
        function first(data Bytes) returns Int { return data[0]; }
        output(first([65, 66]));
        '''
        self.assertEqual(self.execute(source), ["65"])

    def test_bytes_return_provides_literal_context(self):
        source = '''
        function greeting() returns Bytes { return [72, 105]; }
        let data be greeting();
        output(data);
        '''
        self.assertEqual(self.execute(source), ["[72, 105]"])


if __name__ == "__main__":
    unittest.main()
