import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GRAMMAR_PATH = ROOT / "syntax" / "eristavi.tmLanguage.json"
CONFIG_PATH = ROOT / "syntax" / "language-configuration.json"

RESERVED_KEYWORDS = {
    "let",
    "fixed",
    "be",
    "function",
    "returns",
    "return",
    "if",
    "else",
    "for",
    "in",
    "while",
    "type",
    "identity",
    "maybe",
    "error",
    "fails",
    "fail",
    "try",
    "with",
    "import",
    "as",
    "public",
    "and",
    "or",
    "not",
    "true",
    "false",
    "none",
}

NON_ERISTAVI_FORMS = {
    "fn",
    "var",
    "record",
    "resource",
    "private",
    "mutable",
    "checked",
    "break",
    "continue",
    "match",
    "case",
    "catch",
    "handle",
    "defer",
    "null",
    "Void",
    "None",
}


def regex_text(node):
    parts = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key in {"match", "begin", "end"} and isinstance(value, str):
                parts.append(value)
            else:
                parts.extend(regex_text(value))
    elif isinstance(node, list):
        for item in node:
            parts.extend(regex_text(item))
    return parts


class TextMateGrammarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.grammar = json.loads(GRAMMAR_PATH.read_text(encoding="utf-8"))
        cls.config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        cls.regexes = "\n".join(regex_text(cls.grammar))

    def test_identity(self):
        self.assertEqual(self.grammar["name"], "Eristavi")
        self.assertEqual(self.grammar["scopeName"], "source.eristavi")
        self.assertEqual(self.grammar["fileTypes"], ["eri"])

    def test_locked_keywords_are_represented(self):
        for keyword in RESERVED_KEYWORDS:
            with self.subTest(keyword=keyword):
                self.assertIn(keyword, self.regexes)

    def test_rejected_aliases_are_not_highlighted_as_language_forms(self):
        for token in NON_ERISTAVI_FORMS:
            with self.subTest(token=token):
                self.assertNotIn(token, self.regexes)
        self.assertNotIn("&&", self.regexes)
        self.assertNotIn("||", self.regexes)
        self.assertNotIn("->", self.regexes)
        self.assertNotIn("=>", self.regexes)

    def test_comment_configuration_matches_language(self):
        self.assertEqual(self.config["comments"]["lineComment"], "//")
        self.assertEqual(self.config["comments"]["blockComment"], ["/*", "*/"])
        block = self.grammar["repository"]["block-comment"]
        self.assertEqual(block["begin"], "/\\*")
        self.assertEqual(block["end"], "\\*/")
        self.assertIn({"include": "#block-comment"}, block["patterns"])

    def test_predeclared_types_and_output_are_scoped_without_becoming_keywords(self):
        builtins = json.dumps(self.grammar["repository"]["builtins"], ensure_ascii=False)
        for type_name in ("Int", "Float", "Bool", "Text", "List"):
            self.assertIn(type_name, builtins)
        self.assertIn("output", builtins)
        keyword_rules = json.dumps(self.grammar["repository"]["keywords"], ensure_ascii=False)
        self.assertNotIn("output", keyword_rules)


if __name__ == "__main__":
    unittest.main()
