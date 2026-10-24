from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from compiler.erist.cli import lower_universal_file
from compiler.erist.universal_analysis import coalesce_stack_slots, escape_analysis, live_ranges, register_candidates


class UniversalAnalysisTests(unittest.TestCase):
    def lower(self, source: str):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        src = root / "app.eri"
        src.write_text(source, encoding="utf-8")
        return td, lower_universal_file(src, root)

    def test_live_ranges_and_stack_slots_are_deterministic(self):
        td, program = self.lower('let a be 1 + 2; let b be 3 + 4; output(a + b);')
        try:
            fn = program.function("__entry")
            ranges = live_ranges(fn)
            self.assertTrue(ranges)
            first = coalesce_stack_slots(fn)
            second = coalesce_stack_slots(fn)
            self.assertEqual(first, second)
            self.assertLessEqual(first.slot_count, fn.value_count)
        finally:
            td.cleanup()

    def test_escape_analysis_marks_return_and_call_transfer(self):
        td, program = self.lower(
            'function preserve(value Text) returns Text { return value; } '
            'let text be "A" + "B"; output(preserve(text));'
        )
        try:
            preserve = next(fn for fn in program.functions if fn.name.endswith("preserve"))
            entry = program.function("__entry")
            self.assertTrue(any("returned" in reasons for reasons in escape_analysis(preserve).reasons.values()))
            self.assertTrue(any("passed-to-call" in reasons for reasons in escape_analysis(entry).reasons.values()))
        finally:
            td.cleanup()

    def test_register_candidates_are_scalar_and_short_lived(self):
        td, program = self.lower('let x be 10; output((x + 2) * 3);')
        try:
            fn = program.function("__entry")
            candidates = register_candidates(fn)
            types = {item.value_id: item.type_name for item in live_ranges(fn)}
            self.assertTrue(candidates)
            self.assertTrue(all(types[value] in {"i64", "bool", "f64"} for value in candidates))
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
