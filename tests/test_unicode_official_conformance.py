from __future__ import annotations

import os
import unittest
from pathlib import Path

from compiler.erist.unicode_support import UNICODE_VERSION, grapheme_clusters


class UnicodeOfficialConformanceTests(unittest.TestCase):
    def test_official_unicode_17_grapheme_break_vectors(self):
        fixture = os.environ.get("ERISTAVI_GRAPHEME_BREAK_TEST")
        if not fixture:
            self.skipTest("official Unicode grapheme fixture is supplied by CI")

        path = Path(fixture)
        text = path.read_text(encoding="utf-8")
        self.assertIn(f"GraphemeBreakTest-{UNICODE_VERSION}", text.splitlines()[0])

        cases = 0
        for line_number, raw in enumerate(text.splitlines(), 1):
            body = raw.split("#", 1)[0].strip()
            if not body:
                continue

            expected: list[str] = []
            current: list[str] = []
            for token in body.split():
                if token == "÷":
                    if current:
                        expected.append("".join(current))
                        current = []
                elif token == "×":
                    continue
                else:
                    current.append(chr(int(token, 16)))
            if current:
                expected.append("".join(current))

            source = "".join(expected)
            actual = grapheme_clusters(source)
            self.assertEqual(
                actual,
                expected,
                f"Unicode {UNICODE_VERSION} GraphemeBreakTest mismatch on fixture line {line_number}",
            )
            cases += 1

        self.assertGreater(cases, 500, "official grapheme fixture unexpectedly contains too few cases")


if __name__ == "__main__":
    unittest.main()
