import hashlib
import unittest
from compiler.erist.u3_shadow_gate import SourceRevision, ScalarSignature, validate_shadow_ingress
from compiler.erist.u3_semantic_bridge import FrozenNodeFact, FrozenFunction, freeze_scalar_facts
from compiler.erist.u3_metadata_plan import plan_metadata
from compiler.erist.u3_scalar_construction import ScalarOperation, construct_scalar_plan

class U3ConstructionPilotTests(unittest.TestCase):
    def fixture(self):
        source = b"function main() returns Int { return 7; }"
        revision = SourceRevision("main.eri", hashlib.sha256(source).hexdigest(), len(source))
        signature = ScalarSignature((), ("i64",))
        validate_shadow_ingress((revision,), {"main.eri": source}, (signature,))
        facts = (
            FrozenNodeFact(1, 0, "i64", 0, "main.eri", 0, len(source), 1, 1),
            FrozenNodeFact(2, 5, "i64", 0, "main.eri", 30, 31, 1, 31),
            FrozenNodeFact(3, 6, "i64", 0, "main.eri", 30, 32, 1, 31),
        )
        plan = freeze_scalar_facts((FrozenFunction("main", 1, signature, (2, 3)),), facts, {"main.eri": len(source)})
        return (revision,), plan

    def test_direct_scalar_plan_and_stable_anchors(self):
        revisions, semantic = self.fixture()
        metadata = plan_metadata(revisions, semantic)
        self.assertEqual(metadata.declarations[0].function_id, 1)
        self.assertEqual(metadata.anchors[1].node_id, 2)
        result = construct_scalar_plan(semantic, metadata, {
            "main": (ScalarOperation(2, "const.i64", "i64", 7), ScalarOperation(3, "return", None))
        })
        self.assertEqual(result[0].operations[0].payload, 7)

    def test_reject_unknown_nodes_unsupported_op_and_unterminated(self):
        revisions, semantic = self.fixture()
        metadata = plan_metadata(revisions, semantic)
        for seq in (
            (ScalarOperation(99, "const.i64", "i64", 7), ScalarOperation(3, "return", None)),
            (ScalarOperation(2, "managed.text", "i64", 7), ScalarOperation(3, "return", None)),
            (ScalarOperation(2, "const.i64", "i64", 7),),
        ):
            with self.subTest(seq=seq), self.assertRaises(ValueError):
                construct_scalar_plan(semantic, metadata, {"main": seq})

    def test_reject_missing_source_and_unresolved_fact(self):
        revisions, semantic = self.fixture()
        with self.assertRaises(ValueError):
            plan_metadata((SourceRevision("other.eri", "0"*64, 100),), semantic)
        with self.assertRaises(ValueError):
            freeze_scalar_facts(
                (FrozenFunction("main", 1, ScalarSignature((), ("i64",)), (2, 99)),),
                tuple(semantic.facts.values()), {"main.eri": revisions[0].size}
            )

if __name__ == "__main__":
    unittest.main()
