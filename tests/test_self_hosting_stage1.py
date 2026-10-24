from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from compiler.erist.project import compile_entry, compile_module
from compiler.erist.runtime_ext import Interpreter


REPO_ROOT = Path(__file__).resolve().parents[1]
SELFHOST_ROOT = REPO_ROOT / "src"


class SelfHostingStage1Tests(unittest.TestCase):
    def test_foundation_modules_compile_as_importable_eristavi(self):
        modules = (
            "compiler/source.eri",
            "compiler/span.eri",
            "compiler/token.eri",
            "compiler/diagnostic.eri",
            "compiler/lexer.eri",
        )
        for relative in modules:
            with self.subTest(module=relative):
                compiled = compile_module(SELFHOST_ROOT / relative, SELFHOST_ROOT)
                self.assertFalse(compiled.interface_only)

    def test_eristavi_lexer_tokenizes_stage1_ascii_program(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            compiler_dir = root / "compiler"
            compiler_dir.mkdir()
            for name in ("source.eri", "token.eri", "diagnostic.eri", "lexer.eri"):
                (compiler_dir / name).write_text((SELFHOST_ROOT / "compiler" / name).read_text(encoding="utf-8"), encoding="utf-8")

            entry = root / "probe.eri"
            entry.write_text(
                "import compiler.lexer;\n"
                "function probe() returns Int {\n"
                "    let tokens be lexer.lex(\"let answer be 40 + 2;\") else error { return -1; };\n"
                "    return tokens.count;\n"
                "}\n"
                "output(probe());\n",
                encoding="utf-8",
            )
            mod = compile_entry(entry, root)
            output: list[str] = []
            Interpreter(output.append, mod.module_id, mod.imports).run(mod.program)
            self.assertEqual(output, ["8"])


if __name__ == "__main__":
    unittest.main()
