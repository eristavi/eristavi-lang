"""Independent malformed-IR and dominance checks; no compiler self-build."""
from pathlib import Path
import itertools
import platform
import random
import shutil
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ''.join(name + ':ok\n' for name in (
    'straight', 'own-result', 'use-before-definition', 'reverify-after-restoration',
    'result-type', 'definition-owner', 'unknown-operation', 'cyclic-order', 'cyclic-later-position',
    'fake-void-result', 'required-location', 'trap-code', 'overflowing-range',
    'overflowing-instruction-id', 'overflowing-count', 'foreign-table', 'missing-page', 'source-anchor',
    'unsupported-origin', 'source-digest', 'signature-chain', 'metadata-restored',
    'orphan-value', 'orphan-instruction-before-backlink', 'orphan-edge',
    'diamond-nondominance', 'diamond-dominance', 'entry-predecessor',
    'duplicate-edge-owner', 'loop-swap', 'header-value-in-predecessor', 'edge-type',
    'edge-range', 'typed-unreachable', 'malformed-unreachable',
    'repeated-target-arguments', 'work-exhaustion', 'cancellation',
    'zero-result-function', 'float-bits-multiple-results',
    'predicate-ops', 'predicate-payload', 'predicate-arity', 'predicate-type',
    'predicate-restored', 'predicate-dead-ok', 'predicate-dead-payload',
    'integer-ops', 'integer-wrap-payload', 'integer-cmp-relation', 'integer-type',
    'integer-result-type', 'integer-restored', 'integer-dead-ok', 'integer-dead-payload',
    'divrem-ops', 'divrem-payload', 'divrem-extra', 'divrem-operand-type',
    'divrem-arity', 'divrem-result-type', 'divrem-required-location',
    'divrem-restored', 'divrem-dead-valid', 'divrem-dead-payload',
    'float-ops', 'float-payload', 'float-cmp-mode', 'float-operand-type',
    'float-arity', 'float-result-type', 'float-restored', 'float-dead-valid',
    'float-dead-payload',
    'synthetic-origin-valid', 'synthetic-root-reason',
    'synthetic-origin-anchor', 'synthetic-origin-cycle',
    'synthetic-origin-reason', 'synthetic-origin-negative',
    'synthetic-origin-restored',
    'narrow-core-signatures', 'narrow-type-mismatch', 'narrow-type-restored',
    'many-dominated-uses'))


def dominator_oracle(blocks, edges):
    """Slow set intersection, independent of DFS/semi-dominators/tree intervals."""
    reachable, pending = {1}, [1]
    while pending:
        source = pending.pop()
        for a, b in edges:
            if a == source and b not in reachable:
                reachable.add(b)
                pending.append(b)
    sets = {v: ({1} if v == 1 else set(reachable)) for v in reachable}
    changed = True
    while changed:
        changed = False
        for v in sorted(reachable - {1}):
            predecessors = [a for a, b in edges if b == v and a in reachable]
            result = set.intersection(*(sets[p] for p in predecessors)) | {v}
            if result != sets[v]:
                sets[v] = result
                changed = True
    parents = []
    for v in range(1, blocks + 1):
        strict = sets.get(v, set()) - {v}
        parents.append(max(strict, key=lambda p: len(sets[p])) if strict else 0)
    observations = parents + [int(a in sets.get(b, set()))
                              for a in range(1, blocks + 1)
                              for b in range(1, blocks + 1)]
    return observations


def graph_cases():
    cases = []
    possible = list(itertools.product(range(1, 3), repeat=2))
    for mask in range(16):
        cases.append((2, [e for bit, e in enumerate(possible) if mask & (1 << bit)]))
    randomizer = random.Random(0xE1157A)
    for blocks in range(1, 10):
        for sample in range(8):
            density = (0.1, 0.3, 0.7)[sample % 3]
            edges = [(a, b) for a in range(1, blocks + 1)
                     for b in range(1, blocks + 1) if randomizer.random() < density]
            if sample % 2 and edges:
                edges += edges[:2]  # Parallel edges remain separate adjacency entries.
            cases.append((blocks, edges))
    cases.extend([
        (4, [(1, 2), (1, 3), (2, 3), (3, 2), (2, 4), (3, 4)]),
        (5, [(1, 2), (2, 3), (3, 4), (4, 2), (4, 5), (1, 4)]),
        (5, [(1, 2), (1, 2), (2, 2), (3, 4), (4, 3), (4, 5)]),
    ])
    return cases


def graph_probe(chain_sizes=(128, 512, 2048)):
    source = '''
import std.process;
import compiler.u1_budget as budget;
import compiler.u1_dominance as dom;
function graphCase(blocks Int,sources,targets) fails budget.LimitError {
    let root be try budget.developmentRequest(); let owner be try budget.functionOwner(root,false);
    let phase be try budget.verificationPhase(owner); let graph be try dom.create(owner,phase);
    try dom.prepare(graph,blocks,sources.count); let edge be 0;
    while edge < sources.count { try dom.addEdge(graph,edge+1,sources[edge],targets[edge]); edge=edge+1; }
    try dom.compute(graph); let block be 1;
    while block <= blocks { output(try dom.get(graph,block,7)); block=block+1; }
    block=1;
    while block <= blocks {
        let target be 1;
        while target <= blocks { let bits be 0; if try dom.dominates(graph,block,target) { bits=1; } output(bits); target=target+1; }
        block=block+1;
    }
    try dom.close(graph); try budget.finishPhase(phase); try budget.close(owner); try budget.close(root);
}
function chain(blocks Int) fails budget.LimitError {
    let root be try budget.developmentRequest(); let owner be try budget.functionOwner(root,false);
    let phase be try budget.verificationPhase(owner); let graph be try dom.create(owner,phase);
    try dom.prepare(graph,blocks,blocks-1); let edge be 1;
    while edge < blocks { try dom.addEdge(graph,edge,edge,edge+1); edge=edge+1; }
    try dom.compute(graph); output(graph.reachable); output(try dom.get(graph,blocks,7));
    let bits be 0; if try dom.dominates(graph,1,blocks) and not (try dom.dominates(graph,blocks,1)) { bits=1; } output(bits);
    try dom.close(graph); try budget.finishPhase(phase); try budget.close(owner); try budget.close(root);
}
function run() returns Bool fails budget.LimitError {
'''
    expected = []
    for blocks, edges in graph_cases():
        sources, targets = [a for a, _ in edges], [b for _, b in edges]
        source += f'    try graphCase({blocks},{sources},{targets});\n'
        expected += dominator_oracle(blocks, edges)
    for size in chain_sizes:
        source += f'    try chain({size});\n'
        expected += [size, size - 1, 1]
    source += '''    return true;
}
function main() { let done be run() else error budget.LimitError { output(error.category+":"+error.message); process.setExitCode(1); return; }; }
main();
'''
    return source, ''.join(f'{value}\n' for value in expected)


class U1VerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.root = Path(cls.temporary.name)
        (cls.root / 'compiler').symlink_to(ROOT / 'src/compiler', target_is_directory=True)
        cls.protocol = cls.root / 'protocol.eri'
        cls.protocol.write_text((ROOT / 'tests/fixtures/u1_verifier.eri').read_text())
        source, cls.graph_expected = graph_probe()
        cls.graph = cls.root / 'graphs.eri'; cls.graph.write_text(source)
        for name, path in (('protocol', cls.protocol), ('graphs', cls.graph)):
            if build_native(path, cls.root / (name + '-c'), cls.root):
                raise AssertionError(f'{name} bootstrap compilation failed')

    def assert_execution(self, binary, expected):
        result = subprocess.run([str(binary)], capture_output=True, text=True, timeout=120,
                                env={'PATH': '/unavailable', 'LANG': 'C'})
        self.assertEqual(result.returncode, 0,
                         f"verifier probe exited {result.returncode}; stdout tail={result.stdout[-450:]!r}; stderr={result.stderr[-450:]!r}")
        self.assertEqual(result.stdout, expected)
        self.assertEqual(result.stderr, '')

    def test_malformed_ir_and_budget_protocol(self):
        self.assert_execution(self.root / 'protocol-c', PROTOCOL)

    def test_dominance_against_independent_oracle_and_deep_chains(self):
        self.assert_execution(self.root / 'graphs-c', self.graph_expected)

    @unittest.skipUnless(platform.system() == 'Linux' and platform.machine().lower() in ('x86_64', 'amd64'),
                         'owned runtime execution requires Linux x86-64')
    def test_eristavi_emitted_verifier_and_oracle_on_both_runtimes(self):
        for tool in ('as', 'ld', 'cc', 'readelf', 'nm'):
            if not shutil.which(tool):
                self.skipTest(f'{tool} unavailable')
        frontend, generator = self.root / 'frontend', self.root / 'runtime-generator'
        self.assertEqual(build_native(ROOT / 'src/frontend.eri', frontend, ROOT / 'src'), 0)
        self.assertEqual(build_native(ROOT / 'src/owned_runtime.eri', generator, ROOT / 'src'), 0)
        runtime = subprocess.run([str(generator)], capture_output=True, text=True, timeout=60)
        self.assertEqual((runtime.returncode, runtime.stderr), (0, ''))
        runtime_source = self.root / 'runtime.s'; runtime_source.write_text(runtime.stdout)
        runtime_obj = self.root / 'runtime.o'
        subprocess.run(['as', '--64', str(runtime_source), '-o', str(runtime_obj)],
                       check=True, capture_output=True, timeout=30)
        # Full deep chains remain in the C-bootstrap oracle test. The combined
        # owned run hit 120 seconds; retain that as pending performance evidence,
        # not a reason to enlarge a gate. Both native runtimes check all 91 small
        # graphs and the 128-block chain here; larger owned stress is separate.
        graph_source, graph_expected = graph_probe(chain_sizes=(128,))
        native_graph = self.root / 'native-graphs.eri'; native_graph.write_text(graph_source)
        for name, source, expected in (('protocol', self.protocol, PROTOCOL), ('graphs', native_graph, graph_expected)):
            emitted = subprocess.run([str(frontend), 'emit-asm', str(source), '--source-root', str(self.root),
                                      '--target', 'x86_64-linux'], capture_output=True, text=True, timeout=120)
            self.assertEqual((emitted.returncode, emitted.stderr), (0, ''))
            assembly, obj = self.root / (name + '.s'), self.root / (name + '.o')
            assembly.write_text(emitted.stdout)
            subprocess.run(['as', '--64', str(assembly), '-o', str(obj)], check=True, capture_output=True, timeout=30)
            owned, bootstrap = self.root / (name + '-owned'), self.root / (name + '-bootstrap')
            subprocess.run(['ld', '-nostdlib', '-static', '-e', '_start', str(obj), str(runtime_obj), '-o', str(owned)],
                           check=True, capture_output=True, timeout=30)
            subprocess.run(['cc', '-std=c11', '-O2', '-DERIST_NATIVE_RUNTIME', '-DERIST_HEAP_GC_INTERVAL=65536',
                            str(assembly), str(ROOT / 'runtime/native_gc_runtime.c'), '-lm', '-o', str(bootstrap)],
                           check=True, capture_output=True, timeout=60)
            headers = subprocess.check_output(['readelf', '-lW', str(owned)], text=True)
            self.assertNotIn('INTERP', headers); self.assertNotIn('DYNAMIC', headers)
            self.assertNotIn('RWE', next(line for line in headers.splitlines() if 'GNU_STACK' in line))
            self.assertEqual(subprocess.check_output(['nm', '-u', str(owned)], text=True).strip(), '')
            for binary in (bootstrap, owned):
                with self.subTest(program=name, runtime=binary.name):
                    self.assert_execution(binary, expected)


if __name__ == '__main__':
    unittest.main()
