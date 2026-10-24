from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from compiler.erist.project import compile_entry, compile_module
from compiler.erist.runtime_ext import Interpreter


REPO_ROOT = Path(__file__).resolve().parents[1]
SELFHOST_ROOT = REPO_ROOT / "src"


class SelfHostingStage2Tests(unittest.TestCase):
    def test_identity_ast_and_parser_modules_compile(self):
        modules = (
            "compiler/ast.eri",
            "compiler/parser_state.eri",
            "compiler/parser.eri",
        )
        for relative in modules:
            with self.subTest(module=relative):
                compiled = compile_module(SELFHOST_ROOT / relative, SELFHOST_ROOT)
                self.assertFalse(compiled.interface_only)

    def run_self_host_parser(self, source: str) -> list[str]:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            compiler_dir = root / "compiler"
            compiler_dir.mkdir()
            for name in (
                "source.eri",
                "token.eri",
                "diagnostic.eri",
                "lexer.eri",
                "ast.eri",
                "parser_state.eri",
                "parser.eri",
            ):
                (compiler_dir / name).write_text(
                    (SELFHOST_ROOT / "compiler" / name).read_text(encoding="utf-8"),
                    encoding="utf-8",
                )

            literal = json.dumps(source)
            entry = root / "probe.eri"
            entry.write_text(
                "import compiler.lexer;\n"
                "import compiler.parser;\n"
                "import compiler.ast;\n"
                "function probe(source Text) returns Int {\n"
                "    let tokens be lexer.lex(source) else error { return -1; };\n"
                "    let tree be parser.parse(tokens) else error { return -2; };\n"
                "    if tree.kind != ast.program() { return -3; }\n"
                "    if tree.first == none { return -4; }\n"
                "    return 1;\n"
                "}\n"
                f"output(probe({literal}));\n",
                encoding="utf-8",
            )
            mod = compile_entry(entry, root)
            output: list[str] = []
            Interpreter(output.append, mod.module_id, mod.imports).run(mod.program)
            return output

    def test_self_host_parser_accepts_representative_frozen_program(self):
        source = (
            'type User { name Text; } '
            'function choose(value Int) returns Int { '
            'let items be [value, 2]; '
            'if value > 0 { return items[0]; } else { return 0; } '
            '} '
            'let user be User { name = "A"; }; '
            'output(choose(1));'
        )
        self.assertEqual(self.run_self_host_parser(source), ["1"])

    def test_self_host_parser_accepts_checked_error_resource_shape(self):
        source = (
            'import std.files; '
            'error ReadError { message Text; } '
            'function read(path Text) returns Text fails files.FileError { '
            'with file be try files.open(path) { '
            'return try file.readText(); '
            '} '
            '} '
        )
        self.assertEqual(self.run_self_host_parser(source), ["1"])


if __name__ == "__main__":
    unittest.main()
