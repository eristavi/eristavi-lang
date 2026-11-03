"""Opt-in U2 canonical checked-failure edge root boundary, not physical GC proof."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from compiler.erist.cli import build_native

ROOT = Path(__file__).resolve().parents[1]

class U2FailureRootBindingTests(unittest.TestCase):
    def test_checked_failure_payload_pins_full_typed_context(self):
        source = (ROOT / "tests/fixtures/u2_scoped_owners.eri").read_text()
        source = source.replace(
            "import compiler.u2_scoped_owners as owners;",
            "import compiler.u2_scoped_owners as owners;\n"
            "import compiler.u2_failure_context as failure;\n"
            "import compiler.u2_failure_root_bind as roots;")
        before = "let firstCall be try invoke.emit(fn,graph,acquire,pair,[]);"
        replacement = (
            'let context be try failure.create(owner,phase,21,"body-primary",loc.index);\n'
            '    let failureParameter be try build.parameter(fn,failed,0);\n'
            '    let pin be try roots.create(fn,graph,phase,pair,failureParameter,context);\n'
            '    try check(try roots.verify(fn,graph,phase,pair,pin),"canonical root binding changed");\n'
            '    try roots.close(pin);\n'
            '    try failure.close(context);\n'
            '    let firstCall be try invoke.emit(fn,graph,acquire,pair,[]);'
        )
        self.assertIn(before,source)
        source = source.replace(before,replacement,1)
        source = source.replace(
            "continuation.InvalidBinding,owners.InvalidOwnership,ProbeError {",
            "continuation.InvalidBinding,owners.InvalidOwnership,"
            "failure.InvalidContext,roots.InvalidRoot,ProbeError {")
        source = source.replace(
            'else error ProbeError { output("probe:"+error.message);',
            'else error failure.InvalidContext { output("context:"+error.message); process.setExitCode(1); }\n'
            'else error roots.InvalidRoot { output("root:"+error.message); process.setExitCode(1); }\n'
            'else error ProbeError { output("probe:"+error.message);')
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            (directory / "compiler").symlink_to(ROOT / "src/compiler",target_is_directory=True)
            file = directory / "probe.eri"
            file.write_text(source,encoding="utf-8")
            binary = directory / "probe"
            self.assertEqual(build_native(file,binary,directory),0)
            execution = subprocess.run([str(binary)],capture_output=True,text=True,timeout=120)
            self.assertEqual((execution.returncode,execution.stdout,execution.stderr),
                             (0,"u2-scoped-owners:ok\n",""))
