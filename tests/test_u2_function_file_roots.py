"""Opt-in whole-Function File owner root emission and consumption probes.

This checks original canonical ownership -> native GC root helpers only.
It deliberately does not claim integrated File acquire, close, handler, or
automatic whole-Function resource cleanup in the production emitter.
"""
from pathlib import Path
import platform
import re
import shutil
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(
    platform.system() == "Linux" and platform.machine().lower() in ("x86_64", "amd64"),
    "private x86-64 File roots require Linux x86-64",
)
class U2WholeFunctionFileRootTests(unittest.TestCase):
    def test_verified_lexical_owner_roots_cover_every_original_block_and_consumption(self):
        source = (ROOT / "tests/fixtures/u2_scoped_owners.eri").read_text(
            encoding="utf-8")
        imports = "import compiler.u2_scoped_owners as owners;"
        self.assertEqual(source.count(imports), 1)
        source = source.replace(
            imports,
            imports + "\nimport compiler.u2_function_file_roots_x86_64 as fileRoots;",
            1)
        marker = (
            "let mutate be try budget.constructionPhase(owner); "
            "let revision be fn.revision;"
        )
        self.assertEqual(source.count(marker), 1)
        source = source.replace(
            marker,
            marker + "\n    try fileRoots.emit(fn,graph,profile,table,mutate,717);",
            1)
        failures = "continuation.InvalidBinding,owners.InvalidOwnership,ProbeError {"
        self.assertEqual(source.count(failures), 1)
        source = source.replace(
            failures,
            "continuation.InvalidBinding,owners.InvalidOwnership,"
            "fileRoots.Unsupported,ProbeError {",
            1)
        handler = 'else error ProbeError { output("probe:"+error.message);'
        self.assertEqual(source.count(handler), 1)
        source = source.replace(
            handler,
            'else error fileRoots.Unsupported { output("file-roots:"+error.message); '
            'process.setExitCode(1); }\n' + handler,
            1)
        for tool in ("as", "nm"):
            if not shutil.which(tool):
                self.skipTest(tool + " unavailable")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "compiler").symlink_to(
                ROOT / "src/compiler", target_is_directory=True)
            entry = root / "probe.eri"
            entry.write_text(source, encoding="utf-8")
            binary = root / "generator"
            self.assertEqual(build_native(entry, binary, root), 0)
            result = subprocess.run(
                [str(binary)], capture_output=True, text=True, timeout=120)
            self.assertEqual(
                (result.returncode, result.stderr), (0, ""), result.stdout[-1600:])
            suffix = "u2-scoped-owners:ok\n"
            self.assertTrue(result.stdout.endswith(suffix), result.stdout[-1200:])
            emitted = result.stdout[:-len(suffix)]
            base = "erist_u2_file_717"
            self.assertIn(base + "_bind:", emitted)
            self.assertEqual(len(re.findall(
                "^    \\.byte 1$", emitted, re.M)), 2)
            blocks = re.findall(
                r"^" + base + r"_publish_(\d+):$", emitted, re.M)
            self.assertEqual(blocks, [str(i) for i in range(1, 12)])
            closes = re.findall(
                r"^" + base + r"_poison_(\d+):$", emitted, re.M)
            self.assertEqual(len(closes), 3)
            self.assertEqual(len(set(closes)), 3)
            # Acquisition does not begin with a live owner and the nested
            # signature publishes both outer and inner owners.
            block1 = emitted.split(base + "_publish_1:", 1)[1].split(
                ".size " + base + "_publish_1", 1)[0]
            self.assertIn("movq $0,0(%rsi)", block1)
            self.assertIn("movq $0,8(%rsi)", block1)
            block3 = emitted.split(base + "_publish_3:", 1)[1].split(
                ".size " + base + "_publish_3", 1)[0]
            self.assertIn("movq %rax,0(%rsi)", block3)
            self.assertIn("movq %rax,8(%rsi)", block3)
            # Assemble only the emitted helpers; unresolved external
            # runtime references are permitted at the .o stage.
            asm = root / "roots.s"
            asm.write_text(emitted, encoding="utf-8")
            obj = root / "roots.o"
            assembled = subprocess.run(
                ["as", "--64", str(asm), "-o", str(obj)],
                capture_output=True, text=True, timeout=60)
            self.assertEqual(
                (assembled.returncode, assembled.stderr), (0, ""),
                assembled.stdout + assembled.stderr)
            symbols = subprocess.run(
                ["nm", str(obj)], capture_output=True, text=True,
                check=True, timeout=60).stdout
            self.assertIn(base + "_publish_3", symbols)
            self.assertIn(base + "_poison_", symbols)


if __name__ == "__main__":
    unittest.main()
