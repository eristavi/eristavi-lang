from __future__ import annotations

import unittest

from compiler.erist.lexer import Lexer, TokenKind
from compiler.erist.unicode_support import (
    UNICODE_VERSION,
    grapheme_clusters,
    normalize_nfc,
    scalar_texts,
    utf8_bytes,
)


class UnicodeTests(unittest.TestCase):
    def test_toolchain_unicode_version_is_pinned(self):
        self.assertEqual(UNICODE_VERSION, "17.0.0")

    def test_identifier_identity_uses_nfc(self):
        composed = Lexer("let café be 1;").lex()[1]
        decomposed = Lexer("let cafe\u0301 be 1;").lex()[1]
        self.assertEqual(composed.kind, TokenKind.IDENTIFIER)
        self.assertEqual(decomposed.kind, TokenKind.IDENTIFIER)
        self.assertEqual(composed.value, decomposed.value)
        self.assertEqual(composed.value, "café")

    def test_unicode_xid_identifier(self):
        token = Lexer("let Δοκιμή be 1;").lex()[1]
        self.assertEqual(token.kind, TokenKind.IDENTIFIER)
        self.assertEqual(token.value, "Δοκιμή")

    def test_extended_grapheme_clusters_follow_pinned_unicode(self):
        text = "A🇨🇾e\u0301👨‍👩‍👧‍👦"
        self.assertEqual(
            grapheme_clusters(text),
            ["A", "🇨🇾", "e\u0301", "👨‍👩‍👧‍👦"],
        )

    def test_scalar_and_utf8_views_are_distinct(self):
        text = "é"
        self.assertEqual(scalar_texts(text), ["é"])
        self.assertEqual(utf8_bytes(text), [0xC3, 0xA9])

    def test_nfc_normalization_uses_pinned_database(self):
        self.assertEqual(normalize_nfc("e\u0301"), "é")


if __name__ == "__main__":
    unittest.main()
