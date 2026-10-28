from __future__ import annotations

import platform
import contextlib
import io
import os
import shutil
from unittest.mock import patch
import subprocess
import tempfile
import unittest
from pathlib import Path

from compiler.erist.cli import build_direct, emit_direct_asm

DIRECT_HOST = platform.system() == "Linux" and platform.machine().lower() in ("x86_64", "amd64")


class DirectGCTests(unittest.TestCase):
    def test_assembly_contains_typed_compiler_roots_and_mark_sweep_runtime(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "app.eri"
            asm = root / "app.s"
            src.write_text(
                'type Item { name Text; count Int; } '
                'let values be [Item { name="A"; count=1; }]; '
                'output(values[0].name);',
                encoding="utf-8",
            )
            self.assertEqual(emit_direct_asm(src, asm, root, "x86_64-linux"), 0)
            text = asm.read_text(encoding="utf-8")
            self.assertIn(".Leri_gc_root_head", text)
            self.assertIn(".Leri_gc_collect", text)
            self.assertIn(".Leri_gc_mark_typed", text)
            self.assertIn(".Leri_gc_mark_allocation_only", text)
            self.assertIn(".Leri_gc_desc_", text)
            self.assertIn(".Leri_gc_sweep_loop", text)
            self.assertIn("call .Leri_gc_alloc", text)

    @unittest.skipUnless(DIRECT_HOST, "direct GC stress execution currently targets x86-64 Linux")
    def test_repeated_heap_replacement_survives_collection(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "app.eri"
            exe = root / "app"
            src.write_text(
                'let i be 0; let text be ""; '
                'while i < 3000 { text = text + "x"; i = i + 1; } '
                'output(text.bytes.count);',
                encoding="utf-8",
            )
            self.assertEqual(build_direct(src, exe, root), 0)
            p = subprocess.run([str(exe)], capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(p.stdout, "3000\n")

    @unittest.skipUnless(DIRECT_HOST, "direct GC graph execution currently targets x86-64 Linux")
    def test_nested_lists_and_values_remain_reachable(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "app.eri"
            exe = root / "app"
            src.write_text(
                'type Item { name Text; } '
                'let values be [Item { name="A"; }]; '
                'let i be 0; while i < 200 { values.add(Item { name="B"; }); i = i + 1; } '
                'output(values.count); output(values[0].name); output(values[200].name);',
                encoding="utf-8",
            )
            self.assertEqual(build_direct(src, exe, root), 0)
            p = subprocess.run([str(exe)], capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(p.stdout, "201\nA\nB\n")

    @unittest.skipUnless(DIRECT_HOST, "typed direct GC graph execution currently targets x86-64 Linux")
    def test_typed_gc_preserves_nested_maybe_identity_and_list_graph(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "app.eri"
            exe = root / "app"
            src.write_text(
                'type Node { label Text; } '
                'let node be Node { label="root"; }; '
                'let shared be identity node; '
                'let items be [shared]; '
                'let i be 0; let text be ""; '
                'while i < 500 { text = text + "x"; i = i + 1; } '
                'output(items[0].label); output(text.bytes.count);',
                encoding="utf-8",
            )
            self.assertEqual(build_direct(src, exe, root), 0)
            p = subprocess.run([str(exe)], capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(p.stdout, "root\n500\n")

    @unittest.skipUnless(DIRECT_HOST, "PIE GC descriptors require native x86-64 Linux")
    def test_gc_pointer_descriptors_link_as_pie_without_text_relocations(self):
        if not shutil.which('readelf'):self.skipTest('readelf unavailable')
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);source=root/'app.eri';binary=root/'app'
            source.write_text('type Item { name Text; } let values be [Item { name="A"; }]; output(values[0].name);')
            diagnostics=io.StringIO()
            with patch.dict(os.environ,{'CFLAGS':'-fPIE -pie -Wl,-z,text -Wl,-z,relro,-z,now'}),contextlib.redirect_stderr(diagnostics):
                self.assertEqual(build_direct(source,binary,root),0,diagnostics.getvalue())
            self.assertEqual(diagnostics.getvalue(),'')
            dynamic=subprocess.check_output(['readelf','-dW',binary],text=True)
            self.assertNotIn('TEXTREL',dynamic)
            self.assertIn('GNU_RELRO',subprocess.check_output(['readelf','-lW',binary],text=True))
            self.assertIn('.data.rel.ro',subprocess.check_output(['readelf','-SW',binary],text=True))
            result=subprocess.run([binary],capture_output=True,text=True,timeout=10)
            self.assertEqual((result.returncode,result.stdout,result.stderr),(0,'A\n',''))


if __name__ == "__main__":
    unittest.main()
