from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from compiler.erist.cli import lower_universal_file
from compiler.erist.js_backend import JavaScriptBackend


class JavaScriptBackendTests(unittest.TestCase):
    def emit(self, source: str):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        src = root / "app.eri"
        src.write_text(source, encoding="utf-8")
        return td, JavaScriptBackend().emit(lower_universal_file(src, root))

    def test_int_uses_bigint_and_checked_helpers(self):
        td, js = self.emit('let x be 40; output(x + 2);')
        try:
            self.assertIn("BigInt", js)
            self.assertIn("ERI_MAX", js)
            self.assertIn("eriI64", js)
        finally:
            td.cleanup()

    @unittest.skipUnless(shutil.which("node"), "Node.js is required to execute the JavaScript target")
    def test_functions_float_text_and_control_flow_execute(self):
        td, js = self.emit(
            'function factorial(n Int) returns Int { if n <= 1 { return 1; } return n * factorial(n - 1); } '
            'let i be 0; while i < 2 { output(i); i = i + 1; } '
            'output(factorial(5)); output(1.5 + 2.0); output("A" + "B");'
        )
        try:
            path = Path(td.name) / "app.js"
            path.write_text(js, encoding="utf-8")
            p = subprocess.run([shutil.which("node"), str(path)], capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(p.stdout, "0\n1\n120\n3.5\nAB\n")
        finally:
            td.cleanup()

    @unittest.skipUnless(shutil.which("node"), "Node.js is required to execute the JavaScript target")
    def test_value_lists_maybe_and_identity_preserve_eristavi_semantics(self):
        td, js = self.emit(
            'type Inner { value Int; } type Box { inner Inner; name Text; } '
            'let original be Box { inner = Inner { value = 1; }; name = "A"; }; '
            'let copy be original; copy.inner.value = 9; '
            'let values be [original]; values.add(copy); '
            'let maybeValue maybe Int be 5; '
            'let first be identity Inner { value = 3; }; let second be first; second.value = 7; '
            'output(original.inner.value); output(copy.inner.value); output(values.count); '
            'output(original == copy); output(maybeValue != none); '
            'if maybeValue != none { output(maybeValue); } output(first.value); output(first == second);'
        )
        try:
            path = Path(td.name) / "values.js"
            path.write_text(js, encoding="utf-8")
            p = subprocess.run([shutil.which("node"), str(path)], capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(p.stdout, "1\n9\n2\nfalse\ntrue\n5\n7\ntrue\n")
        finally:
            td.cleanup()

    @unittest.skipUnless(shutil.which("node"), "Node.js is required to execute the JavaScript target")
    def test_javascript_list_bounds_fault_is_eristavi_defined(self):
        td, js = self.emit('let values be [1]; let i be 1; output(values[i]);')
        try:
            path = Path(td.name) / "bounds.js"
            path.write_text(js, encoding="utf-8")
            p = subprocess.run([shutil.which("node"), str(path)], capture_output=True, text=True)
            self.assertNotEqual(p.returncode, 0)
            self.assertIn("List index out of bounds", p.stderr)
        finally:
            td.cleanup()

    @unittest.skipUnless(shutil.which("node"), "Node.js is required to execute the JavaScript target")
    def test_runtime_int_overflow_is_not_javascript_wrapping(self):
        td, js = self.emit('let x be 9223372036854775807; let one be 1; output(x + one);')
        try:
            path = Path(td.name) / "overflow.js"
            path.write_text(js, encoding="utf-8")
            p = subprocess.run([shutil.which("node"), str(path)], capture_output=True, text=True)
            self.assertNotEqual(p.returncode, 0)
            self.assertIn("Int arithmetic overflow", p.stderr)
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
