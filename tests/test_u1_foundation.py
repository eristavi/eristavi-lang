"""Focused U1a construction/accounting checks, not full compiler qualification."""
from pathlib import Path
import json
import platform
import shutil
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native
from compiler.erist.diagnostics import SemanticError
from compiler.erist.project import compile_module

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = ''.join(name + ':ok\n' for name in (
    'reservations', 'capacity', 'parent', 'traffic', 'transfer', 'transfer-reject', 'transfer-kind',
    'commit-once', 'release-once', 'work', 'request-work', 'cancel', 'abandon',
    'counter-boundary', 'pages', 'metadata', 'signature-collision', 'source-spans', 'builder',
    'immutable', 'loop-edges', 'foreign-id', 'structural-rejections', 'construction-failure'))


class U1FoundationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.root = Path(cls.temporary.name)
        (cls.root / 'compiler').symlink_to(ROOT / 'src/compiler', target_is_directory=True)
        cls.source = cls.root / 'probe.eri'
        cls.source.write_text((ROOT / 'tests/fixtures/u1_foundation.eri').read_text())
        cls.binary = cls.root / 'probe-c'
        if build_native(cls.source, cls.binary, cls.root):
            raise AssertionError('U1a C-bootstrap probe failed to compile')

    def test_accounting_metadata_and_builder_on_c_bootstrap(self):
        p = subprocess.run([str(self.binary)], capture_output=True, text=True, timeout=120)
        self.assertEqual((p.returncode, p.stdout, p.stderr), (0, EXPECTED, ''))


    def test_opcode_categories_and_inline_edges_are_explicit(self):
        """Future opcodes must never be mistaken for construction cells or CFG edges."""
        source = self.root / 'opcode-classes.eri'
        source.write_text('''
import compiler.u1_ops as ops;
let opcode be -1;
while opcode <= 37 {
    let flags be 0;
    if ops.known(opcode) { flags=flags+1; }
    if ops.isCell(opcode) { flags=flags+2; }
    if ops.terminal(opcode) { flags=flags+4; }
    if ops.mayTrap(opcode) { flags=flags+32; }
    flags=flags+8*ops.inlineEdges(opcode);
    output(flags);
    opcode=opcode+1;
}
''')
        binary = self.root / 'opcode-classes'
        self.assertEqual(build_native(source, binary, self.root), 0)
        completed = subprocess.run([str(binary)], capture_output=True, text=True, timeout=30)
        expected = ''.join(str(
            (1 if 1 <= op <= 33 or op == 36 else 0)
            + (2 if op in (10, 11, 12) else 0)
            + (4 if op in (6, 7, 8) else 0)
            + (32 if op in (5, 24, 25, 26, 27) else 0)
            + (8 if op == 6 else 16 if op == 7 else 0)
        ) + '\n' for op in range(-1, 38))
        self.assertEqual((completed.returncode, completed.stdout, completed.stderr),
                         (0, expected, ''))

        for relative in ('src/compiler/u1_builder.eri', 'src/compiler/u1_verify.eri',
                         'src/compiler/u1_promote.eri'):
            source_text = (ROOT / relative).read_text()
            self.assertNotRegex(source_text, r'\bop\s*(?:>=\s*10|<\s*10)\b')
            # Do not let a direct instruction opcode read become a numeric cell category.
            self.assertNotRegex(source_text,
                                r'\binstruction\s*\([^\n]*,\s*0\)\s*(?:>=\s*10\b|<\s*10\b)')

    def test_nominal_ids_do_not_accept_a_block_as_a_value(self):
        source = self.root / 'bad.eri'
        source.write_text('''
import compiler.u1_builder as build;
import compiler.u1_budget as budget;
public function bad(routine identity build.Function,block build.BlockId) fails budget.LimitError {
    let ignored be try build.valueType(routine,block);
}
''')
        with self.assertRaises(SemanticError) as caught:
            compile_module(source, self.root)
        self.assertIn('BlockId', str(caught.exception))
        self.assertIn('ValueId', str(caught.exception))

    def test_default_factories_match_selected_budget_profile(self):
        policy = json.loads((ROOT / 'UIR_U1A_BUDGETS.json').read_text())
        source = self.root / 'profile.eri'
        source.write_text('''
import compiler.u1_budget as budget;
import std.process;
function show() returns Bool fails budget.LimitError {
    let root be try budget.developmentRequest();
    let shared be try budget.metadataOwner(root);
    let normal be try budget.functionOwner(root,false); let qualified be try budget.functionOwner(root,true);
    let construct be try budget.constructionPhase(normal); let verify be try budget.verificationPhase(normal); let promote be try budget.promotionPhase(normal);
    output(root.limit); output(root.trafficLimit); output(root.workLimit); output(shared.limit);
    output(normal.limit); output(normal.trafficLimit); output(qualified.limit); output(qualified.trafficLimit);
    output(construct.limit); output(verify.limit); output(promote.limit);
    try budget.finishPhase(construct); try budget.finishPhase(verify); try budget.finishPhase(promote);
    try budget.close(normal); try budget.close(qualified); try budget.close(shared); try budget.close(root); return true;
}
function main() { let done be show() else error budget.LimitError { output(error.category); process.setExitCode(1); return; }; }
main();
''')
        binary = self.root / 'profile-c'
        self.assertEqual(build_native(source, binary, self.root), 0)
        memory, work = policy['memory'], policy['work']
        expected = [memory['request_peak_capacity_bytes'], memory['request_allocation_traffic_bytes'],
                    work['request_visit_limit'], memory['shared_metadata_peak_capacity_bytes'],
                    memory['function_peak_capacity_bytes'], memory['function_allocation_traffic_bytes'],
                    memory['qualification_function_peak_capacity_bytes'],
                    memory['qualification_function_allocation_traffic_bytes'],
                    work['construction_visit_limit_per_function'], work['verification_visit_limit_per_call'],
                    work['promotion_visit_limit_per_function']]
        p = subprocess.run([str(binary)], capture_output=True, text=True, timeout=30)
        self.assertEqual((p.returncode, p.stdout, p.stderr), (0, ''.join(f'{v}\n' for v in expected), ''))

    @unittest.skipUnless(platform.system() == 'Linux' and platform.machine().lower() in ('x86_64', 'amd64'),
                         'owned runtime execution requires Linux x86-64')
    def test_eristavi_emitted_probe_with_bootstrap_and_owned_runtime(self):
        for tool in ('as', 'ld', 'cc', 'readelf', 'nm'):
            if not shutil.which(tool):
                self.skipTest(f'{tool} unavailable')
        frontend, generator = self.root / 'frontend', self.root / 'runtime-generator'
        self.assertEqual(build_native(ROOT / 'src/frontend.eri', frontend, ROOT / 'src'), 0)
        self.assertEqual(build_native(ROOT / 'src/owned_runtime.eri', generator, ROOT / 'src'), 0)
        emitted = subprocess.run([str(frontend), 'emit-asm', str(self.source), '--source-root', str(self.root),
                                  '--target', 'x86_64-linux'], capture_output=True, text=True, timeout=120)
        self.assertEqual((emitted.returncode, emitted.stderr), (0, ''))
        assembly = self.root / 'probe.s'; assembly.write_text(emitted.stdout)
        runtime = subprocess.run([str(generator)], capture_output=True, text=True, timeout=60)
        self.assertEqual((runtime.returncode, runtime.stderr), (0, ''))
        runtime_source = self.root / 'owned-runtime.s'; runtime_source.write_text(runtime.stdout)
        obj, runtime_obj = self.root / 'probe.o', self.root / 'runtime.o'
        for src, target in ((assembly, obj), (runtime_source, runtime_obj)):
            subprocess.run(['as', '--64', str(src), '-o', str(target)], check=True, capture_output=True, timeout=30)
        owned, bootstrap = self.root / 'probe-owned', self.root / 'probe-bootstrap'
        subprocess.run(['ld', '-nostdlib', '-static', '-e', '_start', str(obj), str(runtime_obj), '-o', str(owned)],
                       check=True, capture_output=True, timeout=30)
        subprocess.run(['cc', '-std=c11', '-O2', '-DERIST_NATIVE_RUNTIME', '-DERIST_HEAP_GC_INTERVAL=65536',
                        str(assembly), str(ROOT / 'runtime/native_gc_runtime.c'), '-lm', '-o', str(bootstrap)],
                       check=True, capture_output=True, timeout=60)
        headers = subprocess.check_output(['readelf', '-lW', str(owned)], text=True)
        self.assertNotIn('INTERP', headers); self.assertNotIn('DYNAMIC', headers)
        self.assertNotIn('RWE', next(line for line in headers.splitlines() if 'GNU_STACK' in line))
        self.assertEqual(subprocess.check_output(['nm', '-u', str(owned)], text=True).strip(), '')
        for executable in (bootstrap, owned):
            with self.subTest(runtime=executable.name):
                p = subprocess.run([str(executable)], env={'PATH': '/unavailable', 'LANG': 'C'},
                                   capture_output=True, text=True, timeout=120)
                self.assertEqual((p.returncode, p.stdout, p.stderr), (0, EXPECTED, ''))


if __name__ == '__main__':
    unittest.main()
