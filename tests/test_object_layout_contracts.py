from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from compiler.erist.cli import emit_interface, emit_object
from compiler.erist.direct_project import lower_direct_entry


class ObjectLayoutContractTests(unittest.TestCase):
    def test_imported_nominal_layout_and_field_access_order_match_object(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            module = root / "lib.eri"
            module.write_text(
                'public type User { name Text; score Int; } '
                'public function promote(user User) returns User { user.score = user.score + 1; return user; }',
                encoding="utf-8",
            )
            (root / "app.eri").write_text(
                'import lib; let original be lib.User { name="Anna"; score=5; }; '
                'let changed be lib.promote(original); '
                'output(original.score); output(changed.name); output(changed.score);',
                encoding="utf-8",
            )
            self.assertEqual(emit_interface(module, None, root), 0)
            self.assertEqual(emit_object(module, None, root), 0)
            module.unlink()
            program = lower_direct_entry(root / "app.eri", root)
            user = program.type("lib.User")
            self.assertEqual([(f.name, f.type_name) for f in user.fields], [("name", "text"), ("score", "i64")])
            entry = program.function("__entry")
            accesses = [
                ins.immediate
                for block in entry.blocks
                for ins in block.instructions
                if ins.op == "get_field"
            ]
            self.assertEqual(
                [(item["field"], item["index"]) for item in accesses],
                [("score", 1), ("name", 0), ("score", 1)],
            )


if __name__ == "__main__":
    unittest.main()
