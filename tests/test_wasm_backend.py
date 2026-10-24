from __future__ import annotations

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

    def test_text_uses_explicit_externref_utf8_host_contract(self):
        td, wat = self.emit('let value be "A" + "β"; output(value); output(value == "Aβ");')
        try:
            self.assertIn('(import "eristavi" "text_from_utf8"', wat)
            self.assertIn('(import "eristavi" "text_concat"', wat)
            self.assertIn('(import "eristavi" "text_eq"', wat)
            self.assertIn('(import "eristavi" "output_text"', wat)
            self.assertIn('(result externref)', wat)
            self.assertIn('(memory (export "memory")', wat)
            self.assertIn('(data (i32.const 1024)', wat)
            self.assertIn('call $eri_text_concat', wat)
            self.assertIn('call $eri_text_eq', wat)
            self.assertIn('call $eri_out_text', wat)
        finally:
            td.cleanup()

    def test_bool_equality_uses_i32_not_i64_comparison(self):
        td, wat = self.emit('let a be true; let b be false; output(a != b);')
        try:
            self.assertIn('i32.ne', wat)
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
