"""Private failure injection into actual compiled linked aggregate execution.

Cancellation changes only a temporary executor copy. Allocator refusal changes
only emitted bootstrap C. Neither hook is part of the production UIR/runtime.
"""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest
from compiler.erist.cli import build_native, build_c_file

ROOT = Path(__file__).resolve().parents[1]


class U1AggregateInterruptionTests(unittest.TestCase):
    def prepare(self, root):
        compiler = root / "compiler"
        compiler.mkdir()
        for item in (ROOT / "src/compiler").iterdir():
            (compiler / item.name).symlink_to(item)
        return (ROOT / "tests/fixtures/u1_aggregate_calls.eri").read_text()

    def test_cancellation_during_recursive_loop_execution(self):
        for boundary in (1, 8, 20):
            with self.subTest(boundary=boundary), tempfile.TemporaryDirectory() as d:
                root = Path(d)
                fixture = self.prepare(root)
                executor = (ROOT / "src/compiler/u1_aggregate_calls.eri").read_text()
                anchor = "    if machine.steps >= machine.fuel { return false; }"
                self.assertEqual(executor.count(anchor), 1)
                executor = executor.replace(anchor, f"""    if machine.steps == {boundary} {{
        budget.cancel(machine.owner);
        try budget.poll(machine.owner);
    }}
""" + anchor)
                target = root / "compiler/u1_aggregate_calls.eri"
                target.unlink()
                target.write_text(executor)
                # Arm cancellation only inside step(); run one fresh request.
                fixture = fixture.replace("budget.cancel(mainOwner);", "")
                fixture = fixture.replace("let done be all()", "let done be exercise(-2)")
                source = root / "interrupt.eri"
                source.write_text(fixture)
                binary = root / "interrupt"
                self.assertEqual(build_native(source, binary, root), 0)
                result = subprocess.run([str(binary)], capture_output=True, text=True, timeout=120)
                self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))

    def test_bootstrap_allocator_refusal_is_terminal(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            fixture = self.prepare(root)
            fixture = fixture.replace("    let success be try call.run", '    output("u1b-oom-armed");\n    let success be try call.run')
            source = root / "oom.eri"
            source.write_text(fixture)
            cpath = root / "oom.c"
            self.assertEqual(build_c_file(source, cpath, root), 0)
            original = cpath.read_text()
            anchor = "static void *eri_alloc(size_t n){ void *p=malloc(n?n:1);"
            self.assertEqual(original.count(anchor), 1)
            encoded = ", ".join(f"0x{b:02x}" for b in b"u1b-oom-armed")
            marker = "eri_out_text(eri_text_from_bytes((const unsigned char[]){" + encoded + "}, 13));"
            self.assertEqual(original.count(marker), 1)
            for allocation in (1, 32, 128):
                with self.subTest(allocation=allocation):
                    c = original.replace(anchor, f"""static int test_armed=0;
static unsigned test_allocations=0;
static void *test_allocate(size_t n) {{
    if(test_armed && ++test_allocations == {allocation}) return NULL;
    return malloc(n);
}}
static void *eri_alloc(size_t n){{ void *p=test_allocate(n?n:1);""")
                    c = c.replace(marker, marker + " test_armed=1;")
                    cpath.write_text(c)
                    binary = root / "oom"
                    cc = subprocess.run([os.environ.get("CC", "cc"), "-std=c11", str(cpath), "-lm", "-o", str(binary)], capture_output=True, text=True)
                    self.assertEqual(cc.returncode, 0, cc.stderr)
                    result = subprocess.run([str(binary)], capture_output=True, text=True, timeout=120)
                    self.assertEqual(result.returncode, 1)
                    self.assertEqual(result.stdout, "u1b-oom-armed\n")
                    self.assertEqual(result.stderr, "Eristavi runtime fault: out of memory\n")
