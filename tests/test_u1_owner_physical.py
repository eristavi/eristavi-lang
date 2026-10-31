"""Issue #77: exact U1a owner-specific owned-runtime backing acceptance.

The structural observer is intentionally separate from logical budget charges.
It walks the concrete U1 graph objects, while this test independently predicts
radix backing and pins the owned allocator/header contract. Existing PR #103
C-runtime physical samples remain a separate allocator/GC observation rather
than being converted into a guessed per-owner multiplier.

For the owned runtime, a private diagnostic build also proves that no graph
allocation in the measured process receives an oversized free-list block. That
turns the independently derived graph request + allocator-header totals into
actual block capacities for this acceptance run. After the fixture releases its
U1 owners, the diagnostic forces collection and requires at least the complete
65,536-word stress store's 8,469 graph objects to disappear before process
teardown. The production runtime source and resource policy are unchanged.
"""
from pathlib import Path
import json
import platform
import shutil
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native
from u1_native_tools import shared_u1_compilers

ROOT = Path(__file__).resolve().parents[1]
STRESS_OBJECTS = 8469


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


def _instrument_owned_runtime(runtime):
    """Acceptance-only proof of exact graph capacity and post-close GC progress."""
    state = '.Lalloc_regions:\n.quad 0\n'
    assert runtime.count(state) == 1
    runtime = runtime.replace(
        state,
        '.Ltest_graph_alloc_active:\n.quad 0\n'
        '.Ltest_oversized_graph_reuse:\n.quad 0\n'
        '.Ltest_graph_before:\n.quad 0\n' + state,
        1,
    )

    graph_alloc = '    addq $64,%rdi\n    call erist_rt_alloc\n    testq %rax,%rax\n'
    assert runtime.count(graph_alloc) == 1
    runtime = runtime.replace(
        graph_alloc,
        '    addq $64,%rdi\n'
        '    movq $1,.Ltest_graph_alloc_active(%rip)\n'
        '    call erist_rt_alloc\n'
        '    movq $0,.Ltest_graph_alloc_active(%rip)\n'
        '    testq %rax,%rax\n',
        1,
    )

    reuse = '.Lfreelist_reuse:\n    movq %r14,%rdx\n'
    assert runtime.count(reuse) == 1
    runtime = runtime.replace(
        reuse,
        '.Lfreelist_reuse:\n'
        '    pushfq\n'
        '    pushq %rax\n'
        '    cmpq $0,.Ltest_graph_alloc_active(%rip)\n'
        '    je .Ltest_graph_reuse_checked\n'
        '    movq -96(%rbp),%rax\n'
        '    cmpq %r12,%rax\n'
        '    je .Ltest_graph_reuse_checked\n'
        '    incq .Ltest_oversized_graph_reuse(%rip)\n'
        '.Ltest_graph_reuse_checked:\n'
        '    popq %rax\n'
        '    popfq\n'
        '    movq %r14,%rdx\n',
        1,
    )

    startup = (
        '    call erist_entry\n'
        '    call erist_rt_allocator_release_all\n'
        '    testq %rax,%rax\n'
        '    jne .Lscalar_app_fail\n'
    )
    assert runtime.count(startup) == 1
    runtime = runtime.replace(
        startup,
        '    call erist_entry\n'
        '    cmpq $0,.Ltest_oversized_graph_reuse(%rip)\n'
        '    jne .Ltest_u1_physical_fail\n'
        '    call erist_rt_graph_live_objects\n'
        '    movq %rax,.Ltest_graph_before(%rip)\n'
        '    call erist_rt_text_collect\n'
        '    call erist_rt_graph_live_objects\n'
        '    movq .Ltest_graph_before(%rip),%rcx\n'
        '    subq %rax,%rcx\n'
        f'    cmpq ${STRESS_OBJECTS},%rcx\n'
        '    jb .Ltest_u1_physical_fail\n'
        '    call erist_rt_allocator_release_all\n'
        '    testq %rax,%rax\n'
        '    jne .Lscalar_app_fail\n'
        '    jmp .Ltest_u1_physical_done\n'
        '.Ltest_u1_physical_fail:\n'
        '    movl $77,%edi\n'
        '    jmp erist_rt_exit\n'
        '.Ltest_u1_physical_done:\n',
        1,
    )
    return runtime


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
        allocator = (ROOT / 'src/runtime/allocator_x86_64.eri').read_text()
        self.assertRegex(graph, r'shlq\s+\$5,%rdi')
        self.assertRegex(graph, r'addq\s+\$64,%rdi')
        self.assertIn('call erist_rt_alloc', graph)
        self.assertIn('public function blockHeaderSize() returns Int { return 32; }', memory)
        self.assertIn('public function regionHeaderSize() returns Int { return 48; }', memory)
        # Oversized reuse is possible in production, so the owned acceptance run
        # below must explicitly prove it did not occur before calling the structural
        # totals exact actual block capacities.
        self.assertIn('cmpq %r12,%rax', allocator)
        self.assertIn('.Lfreelist_reuse:', allocator)

        physical, logical = self._run(self.bootstrap)
        self.assertEqual(physical['stress'], _word_backing(65536))
        self.assertEqual(physical['stress'][0], STRESS_OBJECTS)
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
    def test_owned_exact_capacity_gc_and_c_partition_parity(self):
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

        obj = self.root / 'owner-physical.o'
        subprocess.run(['as', '--64', str(assembly), '-o', str(obj)], check=True,
                       capture_output=True, timeout=30)

        def link_runtime(name, source_text):
            source = self.root / f'{name}.s'; source.write_text(source_text)
            runtime_obj = self.root / f'{name}.o'
            subprocess.run(['as', '--64', str(source), '-o', str(runtime_obj)], check=True,
                           capture_output=True, timeout=30)
            executable = self.root / name
            subprocess.run(['ld', '-nostdlib', '-static', '-e', '_start', str(obj), str(runtime_obj), '-o', str(executable)],
                           check=True, capture_output=True, timeout=30)
            return executable

        owned = link_runtime('owner-physical-owned', runtime.stdout)
        diagnostic = link_runtime('owner-physical-owned-diagnostic', _instrument_owned_runtime(runtime.stdout))
        c_physical, c_logical = self._run(self.bootstrap)
        owned_physical, owned_logical = self._run(owned)
        self.assertEqual(owned_physical, c_physical)
        self.assertEqual(owned_logical, c_logical)
        # A zero exit from the diagnostic proves both conditions encoded in the
        # private runtime: no graph allocation reused an oversized block, and a
        # forced collection after logical owner cleanup reclaimed at least every
        # graph object in the 65,536-word stress store.
        diagnostic_physical, diagnostic_logical = self._run(diagnostic)
        self.assertEqual(diagnostic_physical, owned_physical)
        self.assertEqual(diagnostic_logical, owned_logical)


if __name__ == '__main__':
    unittest.main()
