from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from compiler.erist.cli import lower_universal_file
from compiler.erist.universal_analysis import (
    cfg_liveness,
    coalesce_stack_slots,
    escape_analysis,
    heap_values_live_across_safepoints,
    interference_graph,
    live_ranges,
    register_candidates,
)
from compiler.erist.universal_ir import TEXT, UBlock, UFunction, UInstruction, ULocal, UReturn, UValue


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
            self.assertEqual(interference_graph(fn), interference_graph(fn))
        finally:
            td.cleanup()

    def test_excluded_register_values_omit_slots_but_pinned_values_win(self):
        left = UValue(0, "i64")
        right = UValue(1, "i64")
        result = UValue(2, "i64")
        block = UBlock(
            "entry",
            [
                UInstruction("const_i64", left, (), None, 10),
                UInstruction("const_i64", right, (), None, 20),
                UInstruction("add_checked", result, (left, right), None, None),
            ],
            UReturn(result),
        )
        fn = UFunction("probe", "i64", [], [], [block], 3)

        ordinary = coalesce_stack_slots(fn)
        compact = coalesce_stack_slots(fn, excluded_values={0, 1})
        pinned = coalesce_stack_slots(fn, pinned_values={0}, excluded_values={0, 1})

        self.assertIn(0, ordinary.slots)
        self.assertIn(1, ordinary.slots)
        self.assertNotIn(0, compact.slots)
        self.assertNotIn(1, compact.slots)
        self.assertLess(compact.slot_count, ordinary.slot_count)
        self.assertIn(0, pinned.slots)
        self.assertNotIn(1, pinned.slots)

    def test_cfg_liveness_marks_heap_value_across_store_safepoint(self):
        value = UValue(0, TEXT)
        local = ULocal(0, "saved", TEXT)
        block = UBlock(
            "entry",
            [
                UInstruction("const_text", value, (), None, "hello"),
                UInstruction("store_local", None, (value,), 0, None),
                UInstruction("output_text", None, (value,), None, None),
            ],
            UReturn(),
        )
        fn = UFunction("probe", "void", [], [local], [block], 1)
        liveness = cfg_liveness(fn)
        self.assertIn(0, liveness.live_after_instruction[("entry", 1)])
        self.assertEqual(heap_values_live_across_safepoints(fn), frozenset({0}))

    def test_pinned_heap_slots_are_never_reused(self):
        td, program = self.lower('let text be "A" + "B"; output(text); output(1 + 2); output(3 + 4);')
        try:
            fn = program.function("__entry")
            heap_ids = {
                item.value_id
                for item in live_ranges(fn)
                if item.type_name not in {"i64", "bool", "f64", "void"}
            }
            plan = coalesce_stack_slots(fn, heap_ids)
            heap_slots = [plan.slots[value_id] for value_id in sorted(heap_ids)]
            self.assertEqual(len(heap_slots), len(set(heap_slots)))
            scalar_slots = [slot for value_id, slot in plan.slots.items() if value_id not in heap_ids]
            if heap_slots and scalar_slots:
                self.assertGreaterEqual(min(scalar_slots), len(heap_slots))
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
