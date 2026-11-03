"""U2 optional managed Text/List/identity descriptor metadata and refusals."""
from pathlib import Path
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native

ROOT=Path(__file__).resolve().parents[1]

class U2ManagedTypesTests(unittest.TestCase):
    def test_versioned_text_list_identity_descriptors_and_corruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/"compiler").symlink_to(ROOT/"src/compiler",target_is_directory=True)
            source=root/"managed_types.eri"
            source.write_text(
                (ROOT/"tests/fixtures/u2_managed_types.eri").read_text(encoding="utf-8"),
                encoding="utf-8")
            binary=root/"managed_types"
            self.assertEqual(build_native(source,binary,root),0)
            run=subprocess.run([str(binary)],capture_output=True,text=True,timeout=120)
            self.assertEqual((run.returncode,run.stdout,run.stderr),
                             (0,"u2-managed-types:ok\n",""))
