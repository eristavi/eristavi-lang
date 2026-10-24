from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from compiler.erist.project import compile_entry
from compiler.erist.runtime_ext import Interpreter


class ModuleMemberPrecedenceTests(unittest.TestCase):
    def test_public_module_add_is_not_treated_as_list_add(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "helpers.eri").write_text(
                "public function add(left Int, right Int) returns Int { return left + right; }\n",
                encoding="utf-8",
            )
            entry = root / "app.eri"
            entry.write_text(
                "import helpers;\noutput(helpers.add(40, 2));\n",
                encoding="utf-8",
            )
            mod = compile_entry(entry, root)
            output: list[str] = []
            Interpreter(output.append, mod.module_id, mod.imports).run(mod.program)
            self.assertEqual(output, ["42"])


if __name__ == "__main__":
    unittest.main()
