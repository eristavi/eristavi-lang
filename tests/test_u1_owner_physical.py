"""Issue #77: exact U1a owner-specific owned-runtime backing acceptance.

The structural observer is intentionally separate from logical budget charges.
It walks the concrete U1 graph objects, while this test independently predicts
radix backing and pins the owned allocator/header contract. Existing PR #103
C-runtime physical samples remain a separate allocator/GC observation rather
than being converted into a guessed per-owner multiplier.
"""
from pathlib import Path
import json
import platform
import re
import shutil
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native
from u1_native_tools import shared_u1_compilers

ROOT = Path(__file__).resolve().parents[1]


def _radix_counts(word_count):
    pages = (word_count + 15) // 16
    if not pages:
        return 0, 0
    # Root plus every distinct 1..6-hex-digit prefix of sequential page IDs.
    nodes = 1
    for prefix in range(1, 7):
        divisor = 16 ** (6 - prefix)
        nodes += (pages + divisor - 1) // divisor
    return nodes, pages


def _block(cells, count=1):
    payload = count * (64 + 32 * cells)
    headers = count * 32
    return count, payload, headers, payload + headers


def _word_backing(word_count):
    nodes, pages = _radix_counts(word_count)
    parts = (_block(7), _block(18, nodes), _block(17, pages))
    return tuple(sum(part[index] for part in parts) for index in range(4))


def _scratch_backing(blocks, edges):
    # u1_dominance.prepare: block rows + edge rows + traversal stack.
    words = (blocks + 1) * 11 + (edges + 1) * 4 + (blocks + 1)
    graph = _block(12)
    store = _word_backing(words)
    return tuple(graph[index] + store[index] for index in range(4))


def _parse(text):
    physical = {}
    logical = {}
    cleanup = False
    for line in text.splitlines():
        parts = line.split(':')
        if parts[0] == 'physical' and len(parts) == 6:
            physical[parts[1]] = tuple(map(int, parts[2:]))
        elif parts[0] == 'logical' and len(parts) == 7:
            logical[parts[1]] = tuple(map(int, parts[2:]))
        elif line == 'physical-owner-cleanup:ok':
            cleanup = True
    return physical, logical, cleanup


class U1OwnerPhysicalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.root = Path(cls.temporary.name)
        (cls.root / 'compiler').symlink_to(ROOT / 'src/compiler', target_is_directory=True)
        cls.source = cls.root / 'owner-physical.eri'
        cls.source.write_text((ROOT / 'tests/fixtures/u1_owner_physical.eri').read_text())
        cls.bootstrap = cls.root / 'owner-physical-c'
        if build_native(cls.source, cls.bootstrap, cls.root):
            raise AssertionError('U1a owner physical probe failed to compile')

    def _run(self, executable, timeout=180):
        completed = subprocess.run([str(executable)], capture_output=True, text=True, timeout=timeout)
        self.assertEqual((completed.returncode, completed.stderr), (0, ''), completed.stdout[-2000:])
        physical, logical, cleanup = _parse(completed.stdout)
        self.assertTrue(cleanup, completed.stdout[-2000:])
        self.assertEqual(set(physical), {
            'metadata', 'function', 'module', 'imports', 'publication-metadata',
            'publication-function', 'scratch', 'stress'})
        self.assertEqual(set(logical), {'metadata', 'function', 'scratch', 'stress'})
        for name, values in physical.items():
            objects, payload, headers, total = values
            self.assertGreater(objects, 0, name)
            self.assertEqual(headers, objects * 32, name)
            self.assertEqual(total, payload + headers, name)
            self.assertGreaterEqual(payload, objects * 64, name)
        return physical, logical

    def test_owned_layout_contract_and_independent_large_radix_oracle(self):
        graph = (ROOT / 'src/runtime/graph_heap_x86_64.eri').read_text()
        memory = (ROOT / 'src/compiler/runtime_memory.eri').read_text()
        self.assertRegex(graph, r'shlq\s+\$5,%rdi')
        self.assertRegex(graph, r'addq\s+\$64,%rdi')
        self.assertIn('call erist_rt_alloc', graph)
        self.assertIn('public function blockHeaderSize() returns Int { return 32; }', memory)
        self.assertIn('public function regionHeaderSize() returns Int { return 48; }', memory)

        physical, logical = self._run(self.bootstrap)
        self.assertEqual(physical['stress'], _word_backing(65536))
        self.assertEqual(physical['scratch'], _scratch_backing(513, 1024))
        # Publication copies are partitioned by the source table's exact owner.
        self.assertGreater(physical['publication-metadata'][3], physical['module'][3])
        self.assertGreater(physical['publication-function'][3], physical['function'][3])

        policy = json.loads((ROOT / 'UIR_U1A_BUDGETS.json').read_text())['memory']
        stress_live, stress_peak, stress_traffic, stress_limit, stress_traffic_limit = logical['stress']
        self.assertGreater(stress_live, 0)
        self.assertLessEqual(stress_live, stress_peak)
        self.assertLessEqual(stress_peak, stress_limit)
        self.assertLessEqual(stress_traffic, stress_traffic_limit)
        self.assertEqual(stress_limit, policy['function_peak_capacity_bytes'])
        self.assertEqual(stress_traffic_limit, policy['function_allocation_traffic_bytes'])

    def test_prior_c_heap_evidence_remains_independent_not_a_multiplier(self):
        evidence = json.loads((ROOT / 'docs/evidence/2026-10-31/u1a-c-physical-heap-samples.json').read_text())
        self.assertTrue(evidence['pass'])
        self.assertEqual(len(evidence['samples']), 20)
        fixtures = [sample['fixture'] for sample in evidence['samples']]
        for name in ('control', 'dense8', 'dense32', 'dense128'):
            self.assertEqual(fixtures.count(name), 5)
        self.assertIn('not individual UIR-owner allocation tagged', evidence['note'])
        self.assertIn('whole isolated C process managed heap', evidence['scope'])
        dense = [sample for sample in evidence['samples'] if sample['fixture'] == 'dense128']
        self.assertTrue(all(sample['actual_c_managed_heap']['peak_bytes'] >
                            sample['model_owner_peak_bytes'] for sample in dense))

    @unittest.skipUnless(platform.system() == 'Linux' and platform.machine().lower() in ('x86_64', 'amd64'),
                         'owned runtime execution requires Linux x86-64')
    def test_c_and_owned_execution_report_identical_owner_partition(self):
        for tool in ('as', 'ld'):
            if not shutil.which(tool):
                self.skipTest(f'{tool} unavailable')
        frontend, generator = shared_u1_compilers()
        emitted = subprocess.run([str(frontend), 'emit-asm', str(self.source), '--source-root', str(self.root),
                                  '--target', 'x86_64-linux'], capture_output=True, text=True, timeout=180)
        self.assertEqual((emitted.returncode, emitted.stderr), (0, ''))
        assembly = self.root / 'owner-physical.s'; assembly.write_text(emitted.stdout)
        runtime = subprocess.run([str(generator)], capture_output=True, text=True, timeout=90)
        self.assertEqual((runtime.returncode, runtime.stderr), (0, ''))
        runtime_source = self.root / 'owned-runtime.s'; runtime_source.write_text(runtime.stdout)
        obj, runtime_obj = self.root / 'owner-physical.o', self.root / 'runtime.o'
        for source, target in ((assembly, obj), (runtime_source, runtime_obj)):
            subprocess.run(['as', '--64', str(source), '-o', str(target)], check=True,
                           capture_output=True, timeout=30)
        owned = self.root / 'owner-physical-owned'
        subprocess.run(['ld', '-nostdlib', '-static', '-e', '_start', str(obj), str(runtime_obj), '-o', str(owned)],
                       check=True, capture_output=True, timeout=30)
        c_physical, c_logical = self._run(self.bootstrap)
        owned_physical, owned_logical = self._run(owned)
        self.assertEqual(owned_physical, c_physical)
        self.assertEqual(owned_logical, c_logical)


if __name__ == '__main__':
    unittest.main()
