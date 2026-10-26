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

    def test_self_host_parser_accepts_map_literals(self):
        source = (
            'let ages be ["Anna" : 32; "John" : 41;]; '
            'let empty be [:]; '
            'output(1);'
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

    def test_parser_rejects_invalid_frozen_syntax(self):
        from compiler.erist.lexer import Lexer
        from compiler.erist.parser import Parser
        from compiler.erist.diagnostics import ParseError
        cases = ['output(1 < 2 < 3);', 'function f(x,) {}', 'let x be [1,];',
                 'let x be 1; x = x = 2;', 'type U { x Int }', 'if true {']
        for source in cases:
            with self.subTest(source=source):
                with self.assertRaises(ParseError):
                    Parser(Lexer(source).lex()).parse()
                self.assertEqual(self.run_self_host_parser(source), ["-2"])

    def test_expression_precedence_matches_stage0_structure(self):
        from compiler.erist.lexer import Lexer
        from compiler.erist.parser import Parser
        from compiler.erist.syntax import BinaryExpr, UnaryExpr, LiteralExpr
        from selfhost_support import literal, prepare, execute

        def render(node):
            if isinstance(node, BinaryExpr):
                return f"({node.operator} {render(node.left)} {render(node.right)})"
            if isinstance(node, UnaryExpr):
                return f"({node.operator} {render(node.operand)})"
            if isinstance(node, LiteralExpr):
                return str(node.value).lower() if isinstance(node.value, bool) else str(node.value)
            raise AssertionError(type(node))

        helper = (
            'import compiler.lexer; import compiler.parser; import compiler.ast; '
            'function render(node identity ast.Node) returns Text { '
            'if node.kind == ast.literalExpr() { return node.text; } '
            'let first be node.first; let second be node.second; '
            'let left be ""; let right be ""; '
            'if first != none { left = render(first); } '
            'if second != none { right = render(second); } '
            'if node.kind == ast.unaryExpr() { return "(" + node.text + " " + left + ")"; } '
            'if node.kind == ast.binaryExpr() { return "(" + node.text + " " + left + " " + right + ")"; } '
            'return "unexpected"; } '
            'function probe(source Text) { '
            'let tokens be lexer.lex(source) else error { output("lex-error"); return; }; '
            'let tree be parser.parse(tokens) else error { output("parse-error"); return; }; '
            'let statement be tree.first; if statement == none { return; } '
            'let expression be statement.second; if expression != none { output(render(expression)); } } '
        )
        for expression in ['1 + 2 * 3 - 4', '-(1 + 2) * 3', 'not true and false or true',
                           '1 + 2 == 3 and 4 > 2', '8 / 2 / 2', 'true or false and false']:
            source = 'let result be ' + expression + ';'
            expected = render(Parser(Lexer(source).lex()).parse().statements[0].initializer)
            with self.subTest(expression=expression), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                entry = prepare(root, helper + f'probe({literal(source)});')
                self.assertEqual(execute(entry, root), [expected])

    def test_portable_c_executes_eristavi_parser(self):
        import subprocess
        from compiler.erist.cli import build_native
        from selfhost_support import literal, prepare
        source = ('import compiler.lexer; import compiler.parser; import compiler.ast; '
                  'function probe(source Text) { '
                  'let tokens be lexer.lex(source) else error { output("lexer-error"); return; }; '
                  'let tree be parser.parse(tokens) else error { output("parser-error"); return; }; '
                  'output(tree.kind == ast.program()); } '
                  f'probe({literal("let café be 1 + 2 * 3;")});')
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            entry = prepare(root, source)
            binary = root / 'parser'
            self.assertEqual(build_native(entry, binary, root), 0)
            result = subprocess.run([str(binary)], capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, 'true\n')


if __name__ == "__main__":
    unittest.main()
