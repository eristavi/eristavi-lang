"""Packaging reproducibility must not depend on the requested output basename."""
import importlib.util
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('offline_builder', ROOT/'tools/build_offline.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class OfflinePackagingTests(unittest.TestCase):
    @unittest.skipUnless(platform.system() == 'Linux' and platform.machine().lower()
                         in ('x86_64', 'amd64', 'aarch64', 'arm64'), 'Linux ELF host required')
    def test_identical_assembly_links_identically_under_different_output_names(self):
        cc = shlex.split(os.environ.get('CC', 'cc'))
        if not all(shutil.which(name) for name in (cc[0], 'as', 'ld')):
            self.skipTest('native bootstrap tools unavailable')
        x86 = platform.machine().lower() in ('x86_64', 'amd64')
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root/'bin').mkdir(); (root/'lib').mkdir()
            for name in ('as', 'ld'):
                (root/'bin'/name).symlink_to(shutil.which(name))
            for name in ('crt1.o', 'crti.o', 'crtbegin.o', 'crtend.o', 'crtn.o', 'libm.so.6', 'libc.so.6'):
                (root/'lib'/name).symlink_to(builder.compiler_file(cc, name))
            loader = builder.compiler_file(cc, 'ld-linux-x86-64.so.2' if x86 else 'ld-linux-aarch64.so.1')
            (root/'platform.json').write_text(json.dumps({
                'target': 'x86_64-linux' if x86 else 'arm64-linux', 'loader': str(loader)}))
            runtime_source = root/'runtime.c'; runtime_source.write_text('int packaging_test_runtime;\n')
            runtime = root/'lib/runtime.o'
            builder.run([*cc, '-c', runtime_source, '-o', runtime])
            assembly = root/'application.s'
            assembly.write_text('.text\n.globl main\nmain:\n' +
                ('xor %eax, %eax\nret\n' if x86 else 'mov w0, #0\nret\n') +
                '.section .note.GNU-stack,"",' + ('@progbits\n' if x86 else '%progbits\n'))
            outputs = [root/'compiler-b', root/'different-compiler-c']
            for output in outputs:
                builder.link(root, assembly, output, runtime)
                self.assertEqual(subprocess.run([str(output)], timeout=10).returncode, 0)
            self.assertEqual(outputs[0].read_bytes(), outputs[1].read_bytes())
