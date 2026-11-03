"""Focused U3 ingress gate tests; no compiler build required."""
import hashlib
import unittest
from compiler.erist.u3_shadow_gate import SourceRevision, ScalarSignature, validate_shadow_ingress

class U3ShadowGateTests(unittest.TestCase):
    def test_exact_scalar_source(self):
        data = b"function main() returns Int { return 1; }"
        rev = SourceRevision("main.eri", hashlib.sha256(data).hexdigest(), len(data))
        validate_shadow_ingress((rev,), {"main.eri": data}, (ScalarSignature((), ("i64",)),))

    def test_stale_digest_and_unsupported_managed_type(self):
        data = b"abc"
        rev = SourceRevision("main.eri", "0"*64, len(data))
        with self.assertRaises(ValueError):
            validate_shadow_ingress((rev,), {"main.eri": data}, (ScalarSignature((), ("i64",)),))
        rev = SourceRevision("main.eri", hashlib.sha256(data).hexdigest(), len(data))
        with self.assertRaises(ValueError):
            validate_shadow_ingress((rev,), {"main.eri": data}, (ScalarSignature(("Text",), ()),))

    def test_duplicate_and_traversal_rejected(self):
        data = b"x"
        rev = SourceRevision("../x.eri", hashlib.sha256(data).hexdigest(), 1)
        with self.assertRaises(ValueError):
            validate_shadow_ingress((rev,), {"../x.eri": data}, (ScalarSignature((), ()),))
        rev = SourceRevision("x.eri", hashlib.sha256(data).hexdigest(), 1)
        with self.assertRaises(ValueError):
            validate_shadow_ingress((rev, rev), {"x.eri": data}, (ScalarSignature((), ()),))

if __name__ == "__main__":
    unittest.main()
