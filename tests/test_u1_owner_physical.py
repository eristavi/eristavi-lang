"""Issue #77: exact U1a owner-specific owned-runtime backing acceptance.

The source observer reports concrete U1 object shape and independent requested
footprint. A private owned-runtime diagnostic separately attributes the allocator's
*actual* graph block capacity (including oversized free-list reuse and the 32-byte
block header) to acceptance-only owner tags 101..105. The diagnostic tracks live,
peak, cumulative traffic, allocation count and GC reclamation, then forces a final
collection after logical owner cleanup. Production runtime/source semantics remain
unchanged.
"""
from pathlib import Path
import json
import platform
import re
import shutil
import struct
import subprocess
import tempfile
import time
import unittest

from compiler.erist.cli import build_native
from u1_native_tools import shared_u1_compilers

ROOT = Path(__file__).resolve().parents[1]
STRESS_OBJECTS = 8469
TAG_NAMES = {101: 'request', 102: 'metadata', 103: 'function', 104: 'scratch', 105: 'stress'}
STAT_FIELDS = ('live', 'peak', 'traffic', 'allocations', 'reclaimed_bytes', 'reclaimed_objects')
SEMANTIC_FIELDS = ('observed_bytes', 'live', 'reclaimed_bytes', 'objects', 'reclaimed_objects')
RECORD_BYTES = 8 + len(TAG_NAMES) * (len(STAT_FIELDS) + len(SEMANTIC_FIELDS)) * 8
# Acceptance-only address map. It is deliberately much larger than the live U1
# object set so allocation-history bookkeeping cannot become the limiting factor.
# This BSS is diagnostic process overhead and is never charged as U1 owner memory.
ATTRIBUTION_SLOTS = 262144
ATTRIBUTION_MASK = ATTRIBUTION_SLOTS - 1
ATTRIBUTION_BYTES = ATTRIBUTION_SLOTS * 8


def _radix_counts(word_count):
    pages = (word_count + 15) // 16
    if not pages:
        return 0, 0
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
    words = (blocks + 1) * 11 + (edges + 1) * 4 + (blocks + 1)
    graph = _block(12)
    store = _word_backing(words)
    return tuple(graph[index] + store[index] for index in range(4))


def _parse(text):
    physical, logical, cleanup = {}, {}, False
    for line in text.splitlines():
        parts = line.split(':')
        if parts[0] == 'physical' and len(parts) == 6:
            physical[parts[1]] = tuple(map(int, parts[2:]))
        elif parts[0] == 'logical' and len(parts) == 7:
            logical[parts[1]] = tuple(map(int, parts[2:]))
        elif line == 'physical-owner-cleanup:ok':
            cleanup = True
    return physical, logical, cleanup


def _decode_owner_records(raw):
    if len(raw) != RECORD_BYTES * 2:
        raise AssertionError(f'owner diagnostic length {len(raw)} != {RECORD_BYTES * 2}')
    snapshots = []
    for at in (0, RECORD_BYTES):
        values = struct.unpack('<' + 'Q' * (RECORD_BYTES // 8), raw[at:at + RECORD_BYTES])
        snapshot = {'error': values[0], 'owners': {}}
        cursor = 1
        for tag in TAG_NAMES:
            row = values[cursor:cursor + len(STAT_FIELDS)]
            snapshot['owners'][TAG_NAMES[tag]] = dict(zip(STAT_FIELDS, row))
            cursor += len(STAT_FIELDS)
        snapshot['backing'] = {}
        for name in TAG_NAMES.values():
            row = values[cursor:cursor + len(SEMANTIC_FIELDS)]
            snapshot['backing'][name] = dict(zip(SEMANTIC_FIELDS, row))
            cursor += len(SEMANTIC_FIELDS)
        snapshots.append(snapshot)
    return snapshots


def _instrument_owned_runtime(runtime, diagnostic_fd, *, force_identity_collisions=False):
    """Track actual graph allocator capacity by source-selected owner tag."""
    if force_identity_collisions:
        # Exercise the entire real stress fixture with every initial cache hash
        # equal. Probe/invalidation/eviction bounds remain production code.
        lookup = '    xorq %rcx,%r14\n    andq $255,%r14\n    movq %r14,8(%rsp)'
        invalidation = ('    xorq %rdx,%rcx\n    andq $255,%rcx\n'
                        '    leaq .Lidentity_private_keys')
        assert runtime.count(lookup) == runtime.count(invalidation) == 1
        runtime = runtime.replace(lookup, '    xorq %r14,%r14\n    movq %r14,8(%rsp)', 1)
        runtime = runtime.replace(invalidation,
                                  '    xorq %rcx,%rcx\n    leaq .Lidentity_private_keys', 1)
    graph_alloc = (
        '    addq $64,%rdi\n'
        '    call erist_rt_alloc\n'
        '    testq %rax,%rax\n'
        '    je erist_rt_value_fault_oom\n'
        '    movq %rax,%r13\n'
    )
    assert runtime.count(graph_alloc) == 1
    runtime = runtime.replace(
        graph_alloc,
        '    addq $64,%rdi\n'
        '    call erist_rt_alloc\n'
        '    testq %rax,%rax\n'
        '    je erist_rt_value_fault_oom\n'
        '    pushq %rax\n'
        '    subq $8,%rsp\n'
        '    movq %rax,%rdi\n'
        '    call .Ltest_owner_alloc\n'
        '    addq $8,%rsp\n'
        '    popq %rax\n'
        '    movq %rax,%r13\n',
        1,
    )

    sweep = (
        '.Lg_sweep_dead:\n'
        '    movq 16(%r13),%r14\n'
        '    movq %r14,(%r12)\n'
        '    movq %r13,%rdi\n'
        '    call erist_rt_free\n'
    )
    assert runtime.count(sweep) == 1
    runtime = runtime.replace(
        sweep,
        '.Lg_sweep_dead:\n'
        '    movq 16(%r13),%r14\n'
        '    movq %r14,(%r12)\n'
        '    movq %r13,%rdi\n'
        '    call .Ltest_owner_free\n'
        '    movq %r13,%rdi\n'
        '    call erist_rt_free\n',
        1,
    )

    startup = '    call erist_entry\n    movq .Lprocess_exit_code'
    assert runtime.count(startup) == 1
    runtime = runtime.replace(
        startup,
        '    call erist_entry\n'
        '    call .Ltest_owner_write\n'
        '    call erist_rt_text_collect\n'
        '    call .Ltest_owner_write\n'
        '    movq .Lprocess_exit_code',
        1,
    )

    equality = 'erist_rt_graph_equal:\n'
    assert runtime.count(equality) == 1
    runtime = runtime.replace(equality, equality + (
        '    pushq %rdi\n    pushq %rsi\n    subq $8,%rsp\n'
        '    call .Ltest_semantic_observe\n'
        '    addq $8,%rsp\n    popq %rsi\n    popq %rdi\n'), 1)

    diagnostic = f'''
.bss
.p2align 3
.Ltest_owner_dump:
.Ltest_owner_error:
    .quad 0
.Ltest_owner_stats:
    .zero 240
.Ltest_semantic_stats:
    .zero 200
.Ltest_semantic_tags:
    .zero {ATTRIBUTION_BYTES}
.Ltest_owner_keys:
    .zero {ATTRIBUTION_BYTES}
.Ltest_owner_tags:
    .zero {ATTRIBUTION_BYTES}
.Ltest_owner_sizes:
    .zero {ATTRIBUTION_BYTES}
.text
.type .Ltest_owner_alloc,@function
.Ltest_owner_alloc:
    movq .Lprocess_exit_code(%rip),%rax
    cmpq $101,%rax
    jb .Ltest_owner_alloc_ret
    cmpq $105,%rax
    ja .Ltest_owner_alloc_ret
    movq %rdi,%r8
    movq %rdi,%r9
    shrq $4,%r9
    andq ${ATTRIBUTION_MASK},%r9
    leaq .Ltest_owner_keys(%rip),%r10
    leaq .Ltest_owner_tags(%rip),%r11
    movl ${ATTRIBUTION_SLOTS},%esi
.Ltest_owner_alloc_probe:
    cmpq $0,(%r11,%r9,8)
    je .Ltest_owner_alloc_slot
    movq (%r10,%r9,8),%rcx
    cmpq %r8,%rcx
    je .Ltest_owner_alloc_slot
    incq %r9
    andq ${ATTRIBUTION_MASK},%r9
    decq %rsi
    jne .Ltest_owner_alloc_probe
    movq $3,.Ltest_owner_error(%rip)
    ret
.Ltest_owner_alloc_slot:
    movq %r8,(%r10,%r9,8)
    cmpq $0,(%r11,%r9,8)
    je .Ltest_owner_alloc_store
    movq $1,.Ltest_owner_error(%rip)
    ret
.Ltest_owner_alloc_store:
    leaq .Ltest_semantic_tags(%rip),%rcx
    movq $0,(%rcx,%r9,8)
    movq %rax,%rcx
    subq $100,%rcx
    movq %rcx,(%r11,%r9,8)
    leaq .Ltest_owner_sizes(%rip),%r10
    movq -32(%r8),%rdx
    andq $-16,%rdx
    addq $32,%rdx
    movq %rdx,(%r10,%r9,8)
    subq $101,%rax
    imulq $48,%rax,%rax
    leaq .Ltest_owner_stats(%rip),%rcx
    addq %rax,%rcx
    addq %rdx,0(%rcx)
    addq %rdx,16(%rcx)
    incq 24(%rcx)
    movq 0(%rcx),%rax
    cmpq 8(%rcx),%rax
    jbe .Ltest_owner_alloc_ret
    movq %rax,8(%rcx)
.Ltest_owner_alloc_ret:
    ret
.size .Ltest_owner_alloc,.-.Ltest_owner_alloc

.type .Ltest_owner_free,@function
.Ltest_owner_free:
    movq %rdi,%r8
    movq %rdi,%r9
    shrq $4,%r9
    andq ${ATTRIBUTION_MASK},%r9
    leaq .Ltest_owner_keys(%rip),%r10
    leaq .Ltest_owner_tags(%rip),%r11
    movl ${ATTRIBUTION_SLOTS},%esi
.Ltest_owner_free_probe:
    movq (%r10,%r9,8),%rcx
    testq %rcx,%rcx
    je .Ltest_owner_free_ret
    cmpq %r8,%rcx
    je .Ltest_owner_free_found
.Ltest_owner_free_next:
    incq %r9
    andq ${ATTRIBUTION_MASK},%r9
    decq %rsi
    jne .Ltest_owner_free_probe
    movq $3,.Ltest_owner_error(%rip)
    ret
.Ltest_owner_free_found:
    call .Ltest_semantic_free
    movq (%r11,%r9,8),%rax
    testq %rax,%rax
    je .Ltest_owner_free_next
    leaq .Ltest_owner_sizes(%rip),%r10
    movq (%r10,%r9,8),%rdx
    decq %rax
    imulq $48,%rax,%rax
    leaq .Ltest_owner_stats(%rip),%rcx
    addq %rax,%rcx
    movq 0(%rcx),%r8
    cmpq %rdx,%r8
    jb .Ltest_owner_free_underflow
    subq %rdx,0(%rcx)
    addq %rdx,32(%rcx)
    incq 40(%rcx)
    movq $0,(%r11,%r9,8)
    movq $0,(%r10,%r9,8)
.Ltest_owner_free_ret:
    ret
.Ltest_owner_free_underflow:
    movq $2,.Ltest_owner_error(%rip)
    ret
.size .Ltest_owner_free,.-.Ltest_owner_free


# Observe exactly the wrapper/body addresses traversed by the semantic owner.
# Phase allocation history is separate: it includes transient bookkeeping.
.Ltest_semantic_observe:
    movq .Lprocess_exit_code(%rip),%rax
    cmpq $201,%rax
    jb .Ltest_semantic_observe_ret
    cmpq $205,%rax
    ja .Ltest_semantic_observe_ret
    pushq %rbx
    pushq %r12
    pushq %r13
    movq %rax,%r12
    movq 8(%rdi),%r13
    cmpq 8(%rsi),%r13
    jne .Ltest_semantic_bad_pair
    movq %r13,%rdi
    call .Ltest_semantic_capture
    movq 8(%r13),%rax
    movq 8(%rax),%rdi
    call .Ltest_semantic_capture
    jmp .Ltest_semantic_observe_done
.Ltest_semantic_bad_pair:
    movq $4,.Ltest_owner_error(%rip)
.Ltest_semantic_observe_done:
    popq %r13
    popq %r12
    popq %rbx
.Ltest_semantic_observe_ret:
    ret
.Ltest_semantic_capture:
    movq %rdi,%r8
    movq %rdi,%r9
    shrq $4,%r9
    andq ${ATTRIBUTION_MASK},%r9
    leaq .Ltest_owner_keys(%rip),%r10
    leaq .Ltest_owner_tags(%rip),%r11
    movl ${ATTRIBUTION_SLOTS},%esi
.Ltest_semantic_probe:
    movq (%r10,%r9,8),%rcx
    testq %rcx,%rcx
    je .Ltest_semantic_missing
    cmpq %r8,%rcx
    jne .Ltest_semantic_next
    cmpq $0,(%r11,%r9,8)
    jne .Ltest_semantic_found
.Ltest_semantic_next:
    incq %r9
    andq ${ATTRIBUTION_MASK},%r9
    decq %rsi
    jne .Ltest_semantic_probe
.Ltest_semantic_missing:
    movq $5,.Ltest_owner_error(%rip)
    ret
.Ltest_semantic_found:
    leaq .Ltest_semantic_tags(%rip),%r10
    movq (%r10,%r9,8),%rax
    testq %rax,%rax
    je .Ltest_semantic_new
    cmpq %r12,%rax
    je .Ltest_semantic_capture_ret
    movq $6,.Ltest_owner_error(%rip)
    ret
.Ltest_semantic_new:
    movq %r12,(%r10,%r9,8)
    leaq .Ltest_owner_sizes(%rip),%r10
    movq (%r10,%r9,8),%rdx
    movq %r12,%rax
    subq $201,%rax
    imulq $40,%rax,%rax
    leaq .Ltest_semantic_stats(%rip),%rcx
    addq %rax,%rcx
    addq %rdx,0(%rcx)
    addq %rdx,8(%rcx)
    incq 24(%rcx)
.Ltest_semantic_capture_ret:
    ret
.Ltest_semantic_free:
    leaq .Ltest_semantic_tags(%rip),%r10
    movq (%r10,%r9,8),%rax
    testq %rax,%rax
    je .Ltest_semantic_free_ret
    movq $0,(%r10,%r9,8)
    subq $201,%rax
    imulq $40,%rax,%rax
    leaq .Ltest_semantic_stats(%rip),%rcx
    addq %rax,%rcx
    leaq .Ltest_owner_sizes(%rip),%r10
    movq (%r10,%r9,8),%rdx
    subq %rdx,8(%rcx)
    addq %rdx,16(%rcx)
    incq 32(%rcx)
.Ltest_semantic_free_ret:
    ret

.type .Ltest_owner_write,@function
.Ltest_owner_write:
    movq $1,%rax
    movq ${diagnostic_fd},%rdi
    leaq .Ltest_owner_dump(%rip),%rsi
    movq ${RECORD_BYTES},%rdx
.Ltest_owner_write_loop:
    syscall
    cmpq $-4,%rax
    je .Ltest_owner_write_loop
    testq %rax,%rax
    jle .Ltest_owner_write_fail
    addq %rax,%rsi
    subq %rax,%rdx
    jne .Ltest_owner_write_loop
    ret
.Ltest_owner_write_fail:
    movq $60,%rax
    movq $79,%rdi
    syscall
    ud2
.size .Ltest_owner_write,.-.Ltest_owner_write
'''
    return runtime + diagnostic


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

    def _run(self, executable, timeout=180, pass_fds=()):
        started = time.monotonic()
        completed = subprocess.run(
            [str(executable)], capture_output=True, text=True, timeout=timeout, pass_fds=pass_fds)
        self.assertEqual((completed.returncode, completed.stderr), (0, ''), completed.stdout[-2000:])
        print('U1A_OWNER_TIMING=' + json.dumps({'stage': executable.name, 'wall_seconds': time.monotonic()-started}), flush=True)
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
        return physical, logical, completed.stdout

    def test_owned_layout_contract_and_independent_large_radix_oracle(self):
        graph = (ROOT / 'src/runtime/graph_heap_x86_64.eri').read_text()
        memory = (ROOT / 'src/compiler/runtime_memory.eri').read_text()
        allocator = (ROOT / 'src/runtime/allocator_x86_64.eri').read_text()
        self.assertRegex(graph, r'shlq\s+\$5,%rdi')
        self.assertRegex(graph, r'addq\s+\$64,%rdi')
        self.assertIn('call erist_rt_alloc', graph)
        self.assertIn('public function blockHeaderSize() returns Int { return 32; }', memory)
        self.assertIn('public function regionHeaderSize() returns Int { return 48; }', memory)
        self.assertIn('cmpq %r12,%rax', allocator)
        self.assertIn('.Lfreelist_reuse:', allocator)

        # Independent source-schema pins: adding an owning field must update
        # the physical observer rather than silently undercounting a new body.
        schemas = {
            'u1_words.eri': {'Words': 7, 'Node': 18, 'Page': 17},
            'u1_meta.eri': {'Metadata': 14},
            'u1_builder.eri': {'Function': 17},
            'u1_dominance.eri': {'Graph': 12},
            'u1_module.eri': {'Program': 6, 'Entry': 5},
            'u1_imports.eri': {'Policy': 5, 'Selection': 5},
            'u1_publication.eri': {'Publication': 9, 'Table': 4},
        }
        for filename, types in schemas.items():
            text = (ROOT / 'src/compiler' / filename).read_text()
            text = re.sub(r'//[^\n]*', '', text)
            for name, fields in types.items():
                found = re.search(r'\btype\s+' + name + r'\s*\{([^}]+)\}', text)
                self.assertIsNotNone(found, (filename, name))
                self.assertEqual(found.group(1).count(';'), fields, (filename, name))

        physical, logical, _ = self._run(self.bootstrap)
        self.assertEqual(physical['stress'], _word_backing(65536))
        self.assertEqual(physical['stress'][0], STRESS_OBJECTS)
        self.assertEqual(physical['scratch'], _scratch_backing(513, 1024))
        self.assertGreater(physical['publication-metadata'][3], physical['module'][3])
        self.assertGreater(physical['publication-function'][3], physical['function'][3])

        policy = json.loads((ROOT / 'UIR_U1A_BUDGETS.json').read_text())['memory']
        live, peak, traffic, limit, traffic_limit = logical['stress']
        self.assertGreater(live, 0)
        self.assertLessEqual(live, peak)
        self.assertLessEqual(peak, limit)
        self.assertLessEqual(traffic, traffic_limit)
        self.assertEqual(limit, policy['qualification_function_peak_capacity_bytes'])
        self.assertEqual(traffic_limit, policy['qualification_function_allocation_traffic_bytes'])

    def test_prior_c_heap_evidence_remains_independent_not_a_multiplier(self):
        evidence = json.loads((ROOT / 'docs/evidence/2026-10-31/u1a-c-physical-heap-samples.json').read_text())
        self.assertTrue(evidence['pass'])
        self.assertEqual(len(evidence['samples']), 20)
        fixtures = [sample['fixture'] for sample in evidence['samples']]
        for name in ('control', 'dense8', 'dense32', 'dense128'):
            self.assertEqual(fixtures.count(name), 5)
        self.assertIn('not individual UIR-owner allocation tagged', evidence['note'])
        self.assertIn('whole isolated C process managed heap', evidence['scope'])

    @unittest.skipUnless(platform.system() == 'Linux' and platform.machine().lower() in ('x86_64', 'amd64'),
                         'owned runtime execution requires Linux x86-64')
    def test_owned_actual_capacity_by_owner_and_gc_reclamation(self):
        for tool in ('as', 'ld'):
            if not shutil.which(tool):
                self.skipTest(f'{tool} unavailable')
        frontend, generator = shared_u1_compilers()
        emitted = subprocess.run(
            [str(frontend), 'emit-asm', str(self.source), '--source-root', str(self.root), '--target', 'x86_64-linux'],
            capture_output=True, text=True, timeout=180)
        self.assertEqual((emitted.returncode, emitted.stderr), (0, ''))
        assembly = self.root / 'owner-physical.s'
        assembly.write_text(emitted.stdout)
        runtime = subprocess.run([str(generator)], capture_output=True, text=True, timeout=90)
        self.assertEqual((runtime.returncode, runtime.stderr), (0, ''))

        obj = self.root / 'owner-physical.o'
        subprocess.run(['as', '--64', str(assembly), '-o', str(obj)], check=True, capture_output=True, timeout=30)

        def link_runtime(name, source_text):
            source = self.root / f'{name}.s'
            source.write_text(source_text)
            runtime_obj = self.root / f'{name}.o'
            subprocess.run(['as', '--64', str(source), '-o', str(runtime_obj)], check=True,
                           capture_output=True, timeout=30)
            executable = self.root / name
            subprocess.run(['ld', '-nostdlib', '-static', '-e', '_start', str(obj), str(runtime_obj), '-o', str(executable)],
                           check=True, capture_output=True, timeout=30)
            return executable

        owned = link_runtime('owner-physical-owned', runtime.stdout)
        c_physical, c_logical, _ = self._run(self.bootstrap)
        owned_physical, owned_logical, _ = self._run(owned)
        self.assertEqual(owned_physical, c_physical)
        self.assertEqual(owned_logical, c_logical)

        record_path = self.root / 'owner-actual.bin'
        with record_path.open('wb') as record:
            diagnostic = link_runtime(
                'owner-physical-owned-diagnostic',
                _instrument_owned_runtime(runtime.stdout, record.fileno(),
                                          force_identity_collisions=True))
            diagnostic_physical, diagnostic_logical, _ = self._run(
                diagnostic, pass_fds=(record.fileno(),))
        self.assertEqual(diagnostic_physical, owned_physical)
        self.assertEqual(diagnostic_logical, owned_logical)

        before, after = _decode_owner_records(record_path.read_bytes())
        self.assertEqual(before['error'], 0)
        self.assertEqual(after['error'], 0)
        for name in TAG_NAMES.values():
            first = before['owners'][name]
            final = after['owners'][name]
            self.assertGreater(first['allocations'], 0, name)
            self.assertGreater(first['traffic'], 0, name)
            self.assertGreater(first['peak'], 0, name)
            self.assertGreaterEqual(first['traffic'], first['peak'], name)
            self.assertGreaterEqual(first['peak'], first['live'], name)
            self.assertEqual(final['traffic'], first['traffic'], name)
            self.assertEqual(final['peak'], first['peak'], name)
            self.assertEqual(final['allocations'], first['allocations'], name)
            self.assertEqual(final['live'], 0, name)
            self.assertEqual(final['reclaimed_bytes'], final['traffic'], name)
            self.assertEqual(final['reclaimed_objects'], final['allocations'], name)

        print('U1A_OWNER_ACTUAL=' + json.dumps({'before_gc': before, 'after_gc': after}, sort_keys=True), flush=True)
        groups = {
            'metadata': ('metadata', 'module', 'imports', 'publication-metadata'),
            'function': ('function', 'publication-function'),
            'scratch': ('scratch',), 'stress': ('stress',),
        }
        for owner, structures in groups.items():
            first, final = before['backing'][owner], after['backing'][owner]
            objects = sum(owned_physical[name][0] for name in structures)
            requested = sum(owned_physical[name][3] for name in structures) + objects * 128
            # Each source identity owns one wrapper and one current body.
            # The size oracle is independent of observed allocator capacity.
            self.assertEqual(first['objects'], objects * 2, owner)
            self.assertGreaterEqual(first['observed_bytes'], requested, owner)
            self.assertEqual(final['observed_bytes'], first['observed_bytes'], owner)
            self.assertEqual(final['live'], 0, owner)
            self.assertEqual(final['reclaimed_bytes'], final['observed_bytes'], owner)
            self.assertEqual(final['reclaimed_objects'], final['objects'], owner)

        policy = json.loads((ROOT / 'UIR_U1A_BUDGETS.json').read_text())['memory']
        self.assertLessEqual(before['backing']['stress']['observed_bytes'],
                             policy['qualification_function_peak_capacity_bytes'])
        stress = before['owners']['stress']
        self.assertLessEqual(stress['peak'], policy['qualification_function_peak_capacity_bytes'])
        self.assertLessEqual(stress['traffic'], policy['qualification_function_allocation_traffic_bytes'])
        self.assertGreaterEqual(stress['traffic'], physical_requested := owned_physical['stress'][3])
        self.assertGreaterEqual(stress['peak'], min(stress['traffic'], physical_requested))



if __name__ == '__main__':
    unittest.main()
