"""Independent canonical resource-state rejection fixtures."""
from pathlib import Path
import subprocess
import tempfile
import unittest
import os
import platform
import hashlib
import json
import time
from compiler.erist.cli import build_native
from u1_native_tools import shared_u1_compilers

ROOT = Path(__file__).resolve().parents[1]


class U2ScopedOwnerTests(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('ERISTAVI_U2_OWNERS_NATIVE') == '1' and
        platform.system() == 'Linux' and platform.machine().lower() in ('x86_64', 'amd64'),
        'opt-in Linux x86-64 owned scoped-owner proof')
    def test_owned_runtime_scoped_owner_proof_and_refusals(self):
        started = time.monotonic()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'compiler').symlink_to(ROOT / 'src/compiler', target_is_directory=True)
            text = (ROOT / 'tests/fixtures/u2_scoped_owners.eri').read_text()
            source = root / 'probe.eri'; source.write_text(text)
            frontend, generator = shared_u1_compilers()
            app = subprocess.run([str(frontend), 'emit-asm', str(source), '--source-root', str(root)],
                                 capture_output=True, text=True, timeout=120)
            runtime = subprocess.run([str(generator)], capture_output=True, text=True, timeout=120)
            for result in (app, runtime):
                self.assertEqual((result.returncode, result.stderr), (0, ''), result.stdout[-1500:])
            for name, code in (('app', app.stdout), ('runtime', runtime.stdout)):
                assembly = root / (name + '.s'); assembly.write_text(code)
                subprocess.run(['as', '--64', str(assembly), '-o', str(root / (name + '.o'))],
                               check=True, capture_output=True, timeout=60)
            binary = root / 'owned'
            subprocess.run(['ld', '-nostdlib', '-static', '-e', '_start', str(root / 'app.o'),
                            str(root / 'runtime.o'), '-o', str(binary)],
                           check=True, capture_output=True, timeout=60)
            result = subprocess.run([str(binary)], capture_output=True, text=True, timeout=120)
            self.assertEqual((result.returncode, result.stdout, result.stderr),
                             (0, 'u2-scoped-owners:ok\n', ''))
            destination = os.environ.get('ERISTAVI_U2_EVIDENCE_DIR')
            if destination:
                path = Path(destination); path.mkdir(parents=True, exist_ok=True)
                (path / 'u2-scoped-owners-owned.json').write_text(json.dumps({
                    'status': 'pass', 'scope': 'owned execution of the ownership verifier; not resource adapter execution',
                    'seconds': time.monotonic() - started, 'stdout': result.stdout,
                    'stderr': result.stderr, 'exit': result.returncode,
                    'fixture_sha256': hashlib.sha256(text.encode()).hexdigest(),
                    'app_assembly_sha256': hashlib.sha256(app.stdout.encode()).hexdigest(),
                    'runtime_assembly_sha256': hashlib.sha256(runtime.stdout.encode()).hexdigest(),
                    'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
                    'cc': os.environ.get('CC', 'cc'), 'cflags': os.environ.get('CFLAGS', '')
                }, indent=2) + '\n')

    def test_nested_acquire_failure_close_consumption_and_origin(self):
        self.compile_probe((ROOT / 'tests/fixtures/u2_scoped_owners.eri').read_text())

    def test_live_owner_loop_signature_and_dead_block_rejection(self):
        text = (ROOT / 'tests/fixtures/u2_scoped_owners.eri').read_text()
        text = text.replace('let outerClose be try invoke.emit(fn,graph,consume,pair,[afterValue]);',
                            'try ab.jump(fn,graph,afterInner,afterInner,[afterValue],loc);')
        # A live owner can remain active on a nonterminating loop. Every
        # backedge must preserve its exact scope/value signature.
        self.compile_probe(text)

    def test_return_cannot_bypass_cleanup(self):
        text = (ROOT / 'tests/fixtures/u2_scoped_owners.eri').read_text()
        text = text.replace('let outerClose be try invoke.emit(fn,graph,consume,pair,[afterValue]);',
                            'try finish(fn,graph,afterInner,loc);')
        start = text.index('    let report be try owners.verify(')
        end = text.index('    try budget.finishPhase(mutate);', start)
        text = text[:start] + '''
    try check(try rejects(profile,fn,graph,table),"return bypassed cleanup");
    let mutate be try budget.constructionPhase(owner);
''' + text[end:]
        self.compile_probe(text)

    def test_ordinary_resource_construction_is_rejected(self):
        text = (ROOT / 'tests/fixtures/u2_scoped_owners.eri').read_text()
        text = text.replace('    try finish(fn,graph,failed,loc);',
                            '    let fake be try ab.make(fn,graph,done,handle,[],loc);\n'
                            '    try finish(fn,graph,failed,loc);', 1)
        start = text.index('    let report be try owners.verify(')
        end = text.index('    try budget.finishPhase(mutate);', start)
        text = text[:start] + '''
    try check(try rejects(profile,fn,graph,table),"ordinary resource copy/constructor accepted");
    let mutate be try budget.constructionPhase(owner);
''' + text[end:]
        self.compile_probe(text)

    def test_resource_cannot_escape_through_an_ordinary_call(self):
        text = (ROOT / 'tests/fixtures/u2_scoped_owners.eri').read_text()
        text = text.replace('    let source be try meta.source',
                            '    let observer be try meta.declaration(data,mp,closeSig,"unselected.observer",2,1,1);\n'
                            '    let source be try meta.source', 1)
        text = text.replace('    pair=try continuation.bind(fn,graph,phase,afterInner,done',
                            '    let escaped be try ab.call(fn,graph,afterInner,observer,[afterValue],loc);\n'
                            '    pair=try continuation.bind(fn,graph,phase,afterInner,done', 1)
        start = text.index('    let report be try owners.verify(')
        end = text.index('    try budget.finishPhase(mutate);', start)
        text = text[:start] + '''
    try check(try rejects(profile,fn,graph,table),"resource escaped through unselected observation call");
    let mutate be try budget.constructionPhase(owner);
''' + text[end:]
        self.compile_probe(text)

    def compile_probe(self, text):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'compiler').symlink_to(ROOT / 'src/compiler', target_is_directory=True)
            source = root / 'probe.eri'; source.write_text(text)
            binary = root / 'probe'
            self.assertEqual(build_native(source, binary, root), 0)
            result = subprocess.run([str(binary)], capture_output=True, text=True, timeout=120)
            self.assertEqual((result.returncode, result.stdout, result.stderr),
                             (0, 'u2-scoped-owners:ok\n', ''))
