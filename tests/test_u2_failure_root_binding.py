"""Opt-in U2 canonical checked-failure edge root boundary, not physical GC proof."""
from pathlib import Path
import subprocess
import tempfile
import unittest
import platform
from u1_native_tools import shared_u1_compilers
from compiler.erist.cli import build_native

ROOT = Path(__file__).resolve().parents[1]

class U2FailureRootBindingTests(unittest.TestCase):
    def _program(self):
        source = (ROOT / "tests/fixtures/u2_scoped_owners.eri").read_text()
        source = source.replace(
            "import compiler.u2_scoped_owners as owners;",
            "import compiler.u2_scoped_owners as owners;\n"
            "import compiler.u2_failure_context as failure;\n"
            "import compiler.u2_failure_root_bind as roots;")
        helper = (
            'function rootRefused(fn identity build.Function,graph identity aggregate.Registry,'
            'phase identity budget.Phase,pair continuation.Pair,pin identity roots.Pin)'
            ' returns Bool fails budget.LimitError,continuation.InvalidBinding {\n'
            '    let accepted be roots.verify(fn,graph,phase,pair,pin)'
            ' else error roots.InvalidRoot { return true; }\n'
            ' else error budget.LimitError { fail error; }\n'
            ' else error continuation.InvalidBinding { fail error; };\n'
            '    return false;\n'
            '}\n'
        )
        self.assertIn("function run() fails",source)
        source = source.replace("function run() fails",helper+"function run() fails",1)
        before = "let firstCall be try invoke.emit(fn,graph,acquire,pair,[]);"
        replacement = (
            'let context be try failure.create(owner,phase,21,"body-primary",loc.index);\n'
            '    let failureParameter be try build.parameter(fn,failed,0);\n'
            '    let pin be try roots.create(fn,graph,phase,pair,failureParameter,context);\n'
            '    try check(try roots.verify(fn,graph,phase,pair,pin),"canonical root binding changed");\n'
            '    let savedType be pin.typeIndex; pin.typeIndex=0;\n'
            '    try check(try rootRefused(fn,graph,phase,pair,pin),"wrong root type accepted");\n'
            '    pin.typeIndex=savedType;\n'
            '    try check(try roots.verify(fn,graph,phase,pair,pin),"restored root refused");\n'
            '    try roots.close(pin);\n'
            '    try check(try rootRefused(fn,graph,phase,pair,pin),"closed root accepted");\n'
            '    try check(pin.context == none and pin.closed,"released reference pin kept context alive");\n'
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
        return source

    def test_checked_failure_payload_pins_full_typed_context(self):
        source = self._program()
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

    @unittest.skipUnless(platform.system() == "Linux" and
        platform.machine().lower() in ("x86_64", "amd64"),
        "owned runtime failure-context pressure probe is Linux x86-64 only")
    def test_owned_failure_root_reference_survives_allocation_pressure(self):
        source = self._program()
        marker = "    try roots.close(pin);\n"
        self.assertIn(marker, source)
        pressure = (
            '    let pressureIndex be 0;\n'
            '    while pressureIndex < 384 {\n'
            '        let temporary be try failure.create(owner,phase,31,"temporary",loc.index);\n'
            '        try failure.append(temporary,phase,32,"secondary",loc.index);\n'
            '        try failure.close(temporary);\n'
            '        pressureIndex=pressureIndex+1;\n'
            '    }\n'
            '    try check(try roots.verify(fn,graph,phase,pair,pin),'
            '"reference pin lost under allocation pressure");\n'
        )
        source = source.replace(marker, pressure + marker, 1)
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            (directory / "compiler").symlink_to(ROOT / "src/compiler",target_is_directory=True)
            file = directory / "probe.eri"
            file.write_text(source, encoding="utf-8")
            frontend, generator = shared_u1_compilers()
            app = subprocess.run(
                [str(frontend), "emit-asm", str(file), "--source-root", str(directory)],
                capture_output=True, text=True, timeout=120)
            runtime = subprocess.run(
                [str(generator)], capture_output=True, text=True, timeout=120)
            for result in (app, runtime):
                self.assertEqual((result.returncode, result.stderr), (0, ""), result.stdout[-1500:])
            for name, text in (("app", app.stdout), ("runtime", runtime.stdout)):
                asm = directory / (name + ".s")
                asm.write_text(text, encoding="utf-8")
                subprocess.run(
                    ["as", "--64", str(asm), "-o", str(directory / (name + ".o"))],
                    check=True, capture_output=True, timeout=60)
            binary = directory / "owned"
            subprocess.run(
                ["ld", "-nostdlib", "-static", "-e", "_start",
                 str(directory / "app.o"), str(directory / "runtime.o"), "-o", str(binary)],
                check=True, capture_output=True, timeout=60)
            outcome = subprocess.run([str(binary)],capture_output=True,text=True,timeout=120)
            self.assertEqual((outcome.returncode,outcome.stdout,outcome.stderr),
                             (0,"u2-scoped-owners:ok\n",""))
