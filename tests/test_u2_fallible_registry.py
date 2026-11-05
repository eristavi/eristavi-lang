"""Compile and execute actual canonical multi-target U2 verification."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from compiler.erist.cli import build_native

ROOT = Path(__file__).resolve().parents[1]


class U2FallibleRegistryTests(unittest.TestCase):
    def test_multiple_targets_unused_contract_mutations_and_exact_cleanup(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'compiler').symlink_to(ROOT / 'src/compiler', target_is_directory=True)
            source = root / 'probe.eri'
            source.write_text((ROOT / 'tests/fixtures/u2_fallible_registry.eri').read_text())
            binary = root / "probe"
            self.assertEqual(build_native(source, binary, root), 0)
            result = subprocess.run([str(binary)], capture_output=True, text=True, timeout=120)
            self.assertEqual((result.returncode, result.stdout, result.stderr),
                             (0, 'u2-fallible-registry:ok\n', ''))
