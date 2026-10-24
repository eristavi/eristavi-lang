from __future__ import annotations

import platform
import subprocess
import tempfile
import unittest
from pathlib import Path

from compiler.erist.cli import build_direct

DIRECT_HOST = platform.system() == "Linux" and platform.machine().lower() in ("x86_64", "amd64")


@unittest.skipUnless(DIRECT_HOST, "aggregate direct execution currently targets x86-64 Linux")
class DirectAggregateTests(unittest.TestCase):
    def compile_run(self, source: str):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "app.eri"
            exe = root / "app"
            src.write_text(source, encoding="utf-8")
            self.assertEqual(build_direct(src, exe, root), 0)
            return subprocess.run([str(exe)], capture_output=True, text=True)

    def test_list_literal_add_index_assignment_and_value_copy(self):
        p = self.compile_run(
            "let original be [1,2]; let copy be original; "
            "copy.add(3); copy[0] = 9; "
            "output(original.count); output(original[0]); "
            "output(copy.count); output(copy[0]); output(original == [1,2]);"
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout, "2\n1\n3\n9\ntrue\n")

    def test_for_uses_stable_list_snapshot(self):
        p = self.compile_run(
            "let values be [1,2]; for value in values { output(value); values.add(9); } "
            "output(values.count);"
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout, "1\n2\n4\n")

    def test_nested_user_values_copy_deeply(self):
        p = self.compile_run(
            "type Inner { value Int; } type Box { inner Inner; name Text; } "
            'let original be Box { inner = Inner { value = 1; }; name = "A"; }; '
            "let copy be original; copy.inner.value = 9; "
            "output(original.inner.value); output(copy.inner.value); output(original == copy);"
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout, "1\n9\nfalse\n")

    def test_list_of_values_copy_is_deep(self):
        p = self.compile_run(
            "type User { name Text; } "
            'let original be [User { name = "A"; }]; let copy be original; '
            'copy[0].name = "B"; output(original[0].name); output(copy[0].name);'
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout, "A\nB\n")

    def test_identity_aliases_shared_value(self):
        p = self.compile_run(
            "type Counter { value Int; } "
            "let first be identity Counter { value = 1; }; let second be first; "
            "second.value = 7; output(first.value); output(first == second);"
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout, "7\ntrue\n")

    def test_maybe_presence_narrowing_and_equality(self):
        p = self.compile_run(
            "let value maybe Int be 5; output(value != none); "
            "if value != none { output(value); } let empty maybe Int be none; output(empty == none);"
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout, "true\n5\ntrue\n")

    def test_function_parameter_retains_value_semantics(self):
        p = self.compile_run(
            "type User { name Text; } "
            "function rename(user User) returns User { user.name = \"B\"; return user; } "
            'let original be User { name = "A"; }; let changed be rename(original); '
            "output(original.name); output(changed.name);"
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout, "A\nB\n")

    def test_list_bounds_fault_remains_defined(self):
        p = self.compile_run("let values be [1]; let i be 1; output(values[i]);")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("List index out of bounds", p.stderr)


if __name__ == "__main__":
    unittest.main()
