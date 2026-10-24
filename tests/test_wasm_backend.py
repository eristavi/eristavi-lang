from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from compiler.erist.cli import lower_universal_file
from compiler.erist.wasm_backend import WebAssemblyTextBackend


class WebAssemblyBackendTests(unittest.TestCase):
    def emit(self, source: str):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        src = root / "app.eri"
        src.write_text(source, encoding="utf-8")
        return td, WebAssemblyTextBackend().emit(lower_universal_file(src, root))

    def test_checked_int_and_function_calls_are_direct_wasm_contracts(self):
        td, wat = self.emit(
            'function add(a Int, b Int) returns Int { return a + b; } '
            'let x be add(20,22); output(x);'
        )
        try:
            self.assertIn('(import "eristavi" "i64_add_checked"', wat)
            self.assertIn('call $eri_add', wat)
            self.assertIn('(export "_start"', wat)
            self.assertIn('i64.const 20', wat)
        finally:
            td.cleanup()

    def test_control_flow_uses_dispatch_loop_not_source_c(self):
        td, wat = self.emit('let i be 0; while i < 3 { i = i + 1; } output(i);')
        try:
            self.assertIn('(loop $dispatch', wat)
            self.assertIn('br $dispatch', wat)
            self.assertNotIn('#include', wat)
        finally:
            td.cleanup()

    def test_unsupported_text_is_explicitly_rejected(self):
        td = tempfile.TemporaryDirectory()
        try:
            root = Path(td.name)
            src = root / "app.eri"
            src.write_text('output("hello");', encoding="utf-8")
            with self.assertRaises(ValueError):
                WebAssemblyTextBackend().emit(lower_universal_file(src, root))
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
