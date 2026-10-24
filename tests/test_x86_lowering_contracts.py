from __future__ import annotations

import unittest

from compiler.erist.x86_64_lowering_contracts import (
    GP_CALLER_SAVED,
    XMM_CALLER_SAVED,
    x86_lowering_contract,
)


class X86LoweringContractTests(unittest.TestCase):
    def test_unknown_operation_is_conservative(self):
        contract = x86_lowering_contract("future_unknown_op")
        self.assertTrue(contract.may_call)
        self.assertFalse(contract.operands_before_clobber)
        self.assertFalse(contract.scalar_result_register_safe)
        self.assertEqual(contract.gp_clobbers, GP_CALLER_SAVED)
        self.assertEqual(contract.xmm_clobbers, XMM_CALLER_SAVED)

    def test_checked_add_is_audited_call_free_scalar_lowering(self):
        contract = x86_lowering_contract("add_checked")
        self.assertFalse(contract.may_call)
        self.assertTrue(contract.operands_before_clobber)
        self.assertTrue(contract.scalar_result_register_safe)
        self.assertEqual(contract.gp_clobbers, frozenset({"%rax", "%rcx"}))
        self.assertEqual(contract.xmm_clobbers, frozenset())

    def test_store_local_consumes_operand_before_gc_clobber(self):
        contract = x86_lowering_contract("store_local")
        self.assertTrue(contract.may_call)
        self.assertTrue(contract.operands_before_clobber)
        self.assertFalse(contract.scalar_result_register_safe)
        self.assertIn("%r10", contract.gp_clobbers)
        self.assertIn("%xmm8", contract.xmm_clobbers)

    def test_call_result_is_safe_only_after_caller_saved_clobber(self):
        contract = x86_lowering_contract("call")
        self.assertTrue(contract.may_call)
        self.assertTrue(contract.operands_before_clobber)
        self.assertTrue(contract.scalar_result_register_safe)
        self.assertEqual(contract.gp_clobbers, GP_CALLER_SAVED)
        self.assertEqual(contract.xmm_clobbers, XMM_CALLER_SAVED)


if __name__ == "__main__":
    unittest.main()
