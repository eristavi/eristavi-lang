from __future__ import annotations

import unittest

from compiler.erist.cli import compile_frontend
from compiler.erist.diagnostics import RuntimeFault, SemanticError
from compiler.erist.runtime_ext import Interpreter
from compiler.erist.unicode_support import UNICODE_VERSION


class TextViewTests(unittest.TestCase):
    def execute(self, source: str):
        out = []
        program = compile_frontend(source)
        Interpreter(output=out.append).run(program)
        return out

    def bad(self, source: str):
        with self.assertRaises(SemanticError):
            compile_frontend(source)

    def test_unicode_version_is_pinned(self):
        self.assertEqual(UNICODE_VERSION, "17.0.0")

    def test_combining_sequence_counts_are_explicit(self):
        # A + COMBINING ACUTE ACCENT is one grapheme, two scalars, three UTF-8 bytes.
        self.assertEqual(
            self.execute('let text be "A\\u{301}"; output(text.characters.count); output(text.scalars.count); output(text.bytes.count);'),
            ["1", "2", "3"],
        )

    def test_zwj_emoji_is_one_extended_grapheme_cluster(self):
        self.assertEqual(
            self.execute('let text be "👨‍👩‍👧‍👦"; output(text.characters.count); output(text.scalars.count); output(text.bytes.count);'),
            ["1", "7", "25"],
        )

    def test_character_scalar_and_byte_indexing(self):
        self.assertEqual(
            self.execute('let text be "A\\u{301}B"; output(text.characters[0]); output(text.characters[1]); output(text.scalars[0]); output(text.bytes[0]);'),
            ["Á", "B", "A", "65"],
        )

    def test_views_can_be_bound_and_fixed(self):
        self.assertEqual(
            self.execute('let text be "abc"; let fixed view be text.characters; output(view.count); output(view[2]);'),
            ["3", "c"],
        )

    def test_direct_text_indexing_remains_invalid(self):
        self.bad('let text be "abc"; output(text[0]);')

    def test_text_view_index_requires_int(self):
        self.bad('let text be "abc"; output(text.characters[0.0]);')

    def test_text_views_are_read_only(self):
        self.bad('let text be "abc"; text.characters[0] = "x";')

    def test_text_view_bounds_fault_is_runtime_defined(self):
        with self.assertRaises(RuntimeFault):
            self.execute('let text be "a"; let i be 1; output(text.characters[i]);')


if __name__ == "__main__":
    unittest.main()
