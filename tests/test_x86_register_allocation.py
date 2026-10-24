from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from compiler.erist.cli import lower_universal_file
from compiler.erist.universal_ir import F64, I64, UBlock, UFunction, UInstruction, ULocal, UReturn, UValue
from compiler.erist.x86_64_gc_precise import X86_64PreciseRootGCLinuxBackend
from compiler.erist.x86_64_register_backend import allocate_x86_registers


class X86RegisterAllocationTests(unittest.TestCase):
    def lower(self, source: str):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        src = root / "app.eri"
        src.write_text(source, encoding="utf-8")
        return td, lower_universal_file(src, root)

    def test_interfering_gp_values_do_not_share_single_register(self):
        left = UValue(0, I64)
        right = UValue(1, I64)
        result = UValue(2, I64)
        block = UBlock(
            "entry",
            [
                UInstruction("const_i64", left, (), None, 10),
                UInstruction("const_i64", right, (), None, 20),
                UInstruction("add_checked", result, (left, right), None, None),
            ],
            UReturn(result),
        )
        fn = UFunction("probe", I64, [], [], [block], 3)
        plan = allocate_x86_registers(fn, gp_registers=("%r10",), xmm_registers=())

        self.assertIn(2, plan.registers)
        self.assertEqual(plan.registers[2], "%r10")
        self.assertLessEqual(sum(value_id in plan.registers for value_id in (0, 1)), 1)

    def test_float_values_use_xmm_register_class(self):
        left = UValue(0, F64)
        right = UValue(1, F64)
        result = UValue(2, F64)
        block = UBlock(
            "entry",
            [
                UInstruction("const_f64", left, (), None, 1.5),
                UInstruction("const_f64", right, (), None, 2.5),
                UInstruction("f64_add", result, (left, right), None, None),
            ],
            UReturn(result),
        )
        fn = UFunction("probe", F64, [], [], [block], 3)
        plan = allocate_x86_registers(fn, gp_registers=(), xmm_registers=("%xmm8",))

        self.assertIn(2, plan.registers)
        self.assertEqual(plan.registers[2], "%xmm8")
        self.assertTrue(all(register.startswith("%xmm") for register in plan.registers.values()))

    def test_value_live_across_call_boundary_remains_spilled(self):
        value = UValue(0, I64)
        call_result = UValue(1, I64)
        one = UValue(2, I64)
        result = UValue(3, I64)
        block = UBlock(
            "entry",
            [
                UInstruction("const_i64", value, (), None, 10),
                UInstruction("call", call_result, (), None, "other"),
                UInstruction("const_i64", one, (), None, 1),
                UInstruction("add_checked", result, (value, one), None, None),
            ],
            UReturn(result),
        )
        fn = UFunction("probe", I64, [], [], [block], 4)
        plan = allocate_x86_registers(fn)
        self.assertNotIn(0, plan.registers)

    def test_value_live_across_gc_store_safepoint_remains_spilled(self):
        value = UValue(0, I64)
        one = UValue(1, I64)
        result = UValue(2, I64)
        local = ULocal(0, "saved", I64)
        block = UBlock(
            "entry",
            [
                UInstruction("const_i64", value, (), None, 10),
                UInstruction("store_local", None, (value,), 0, None),
                UInstruction("const_i64", one, (), None, 1),
                UInstruction("add_checked", result, (value, one), None, None),
            ],
            UReturn(result),
        )
        fn = UFunction("probe", I64, [], [local], [block], 3)
        plan = allocate_x86_registers(fn)
        self.assertNotIn(0, plan.registers)

    def test_operand_of_complex_clobber_region_remains_spilled(self):
        value = UValue(0, I64)
        values = UValue(1, "list<Int>")
        block = UBlock(
            "entry",
            [
                UInstruction("const_i64", value, (), None, 42),
                UInstruction("make_list", values, (value,), None, I64),
            ],
            UReturn(values),
        )
        fn = UFunction("probe", "list<Int>", [], [], [block], 2)
        plan = allocate_x86_registers(fn)
        self.assertNotIn(0, plan.registers)

    def test_complex_scalar_extraction_remains_spilled(self):
        aggregate = UValue(0, "nominal<Record>")
        field = UValue(1, I64)
        block = UBlock(
            "entry",
            [
                UInstruction("load_local", aggregate, (), 0, None),
                UInstruction("get_field", field, (aggregate,), None, {"index": 0}),
                UInstruction("output_i64", None, (field,), None, None),
            ],
            UReturn(),
        )
        local = ULocal(0, "record", "nominal<Record>")
        fn = UFunction("probe", "void", [], [local], [block], 2)
        plan = allocate_x86_registers(fn)
        self.assertNotIn(1, plan.registers)

    def test_composed_gc_backend_emits_register_resident_scalar_chain(self):
        td, program = self.lower("output((40 + 2) * 3);")
        try:
            assembly = X86_64PreciseRootGCLinuxBackend().emit(program)
            main_body = assembly.split(".globl main", 1)[1].split(".size main", 1)[0]
            self.assertIn("%r10", main_body)
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
