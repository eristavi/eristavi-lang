"""Scalar-cell SSA promotion: independent execution, shape and failure checks."""
from pathlib import Path
import itertools
import platform
import shutil
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native
from compiler.erist.diagnostics import SemanticError
from compiler.erist.project import compile_module

ROOT = Path(__file__).resolve().parents[1]
TABLES = ('blocks', 'values', 'instructions', 'operands', 'edges', 'arguments', 'cells')
MIN, MAX = -(1 << 63), (1 << 63) - 1


def probe_source(calls, repetitions=8):
    return (ROOT / 'tests/fixtures/u1_promotion.eri').read_text() + f'''
function repetitions() returns Int {{ return {repetitions}; }}
function run() returns Bool fails budget.LimitError,verify.InvalidIR,ProbeError {{
    {' '.join('try ' + call + ';' for call in calls)} return true;
}}
function main() {{ let done be run()
    else error budget.LimitError {{ output(error.category+":"+error.message); process.setExitCode(1); return; }}
    else error verify.InvalidIR {{ output(error.message); output(error.stage); process.setExitCode(1); return; }}
    else error ProbeError {{ output(error.message); process.setExitCode(1); return; }};
}}
main();
'''


def parse_snapshots(text):
    lines, position, snapshots, labels = text.splitlines(), 0, [], []
    while position < len(lines):
        name = lines[position]; position += 1
        if name.endswith(':ok'):
            labels.append(name); continue
        counts = tuple(int(value) for value in lines[position:position+6]); position += 6
        pair = []
        for _ in range(2):
            ir = {}
            for table in TABLES:
                count = int(lines[position]); position += 1
                ir[table] = [int(value) for value in lines[position:position+count]]; position += count
                if len(ir[table]) != count:
                    raise AssertionError('truncated IR snapshot')
            pair.append(ir)
        snapshots.append((name, counts, pair[0], pair[1]))
    return snapshots, labels


def evaluate(ir, parameters, fuel=50000):
    """Independent executable semantics, including simultaneous arguments and traps.

    Mutable cell state is interpreted directly; this does not reproduce the
    promotion algorithm, liveness, frontiers, alias maps or dominator traversal.
    """
    values, cells, trace = {}, {}, []
    block, arguments = 1, tuple(parameters)
    while fuel:
        first, count, head, _, terminator = ir['blocks'][(block-1)*5:block*5]
        if len(arguments) != count:
            raise AssertionError('edge/entry argument arity')
        values.update((first+i, value) for i, value in enumerate(arguments))
        cursor = head or terminator
        while cursor:
            fuel -= 1
            if fuel < 0:
                raise AssertionError('evaluator fuel exhausted; behavior inconclusive')
            op, owner, start, count, result, results, location, payload, extra, following = ir['instructions'][(cursor-1)*10:cursor*10]
            if owner != block:
                raise AssertionError('instruction owner mismatch')
            operands = [values[v] for v in ir['operands'][start:start+count]]
            outputs = []
            if op in (1, 9): outputs = [payload]
            elif op == 2: outputs = [bool(payload)]
            elif op == 3:
                mathematical = operands[0] + operands[1]
                outputs = [((mathematical + (1 << 63)) % (1 << 64)) - (1 << 63), not MIN <= mathematical <= MAX]
            elif op == 4: outputs = [not operands[0]]
            elif op == 5:
                trace.append((payload, location, bool(operands[0])))
                if not operands[0]: return ('trap', (payload, location)), tuple(trace)
            elif op in (6, 7):
                edge = payload if op == 6 or operands[0] else extra
                block, first_argument, argument_count = ir['edges'][(edge-1)*3:edge*3]
                # Snapshot every argument before rebinding ANY destination parameter.
                arguments = tuple(values[v] for v in ir['arguments'][first_argument:first_argument+argument_count])
                break
            elif op == 8: return ('return', tuple(operands)), tuple(trace)
            elif op == 10: cells[payload] = operands[0]
            elif op == 11: outputs = [cells[payload]]
            elif op == 12:
                if payload not in cells: raise AssertionError('uninitialized cell write')
                cells[payload] = operands[0]
            else: raise AssertionError(f'unsupported reference operation {op}')
            if len(outputs) != results:
                raise AssertionError('reference result arity mismatch')
            values.update((result+i, value) for i, value in enumerate(outputs))
            cursor = following or (0 if cursor == terminator else terminator)
        else:
            raise AssertionError('block did not terminate')
    raise AssertionError('evaluator fuel exhausted; behavior inconclusive')


def cases_for(name, before):
    cells = len(before['cells']) // 2
    if name in ('diamond', 'sequential', 'redundant', 'loop'):
        for flag in (False, True):
            expected = cells*(cells-1)//2
            if name in ('diamond', 'sequential'): expected += cells * (1 if flag else 2)
            if name == 'loop': expected += cells * int(flag)
            yield (flag,), ('return', (expected,))
    elif name == 'swap':
        for a, b in ((3, 7), (MIN, MAX), (0, 0)):
            for flag in (False, True):
                yield (a, b, flag), ('return', (b, a) if flag else (a, b))
    elif name == 'reset': yield (), ('return', ())
    elif name == 'dead': yield (), ('return', (0,))
    elif name == 'irreducible':
        for start, p, q in itertools.product((False, True), repeat=3):
            if p and q: continue
            result, position = 0, (1 if start else 2)
            while True:
                result += position
                if not (p if position == 1 else q): break
                position = 3-position
            yield (start, p, q), ('return', (result,))
    elif name in ('faults', 'unused'):
        for value, flag, allowed in itertools.product((MIN, -1, 0, MAX-1, MAX), (False, True), (False, True)):
            result = value + (1 if flag else 2)
            expected = ('return', (0 if name == 'unused' else result,))
            if not allowed: expected = ('trap', (4, 1))
            elif result > MAX: expected = ('trap', (1, 2))
            yield (value, flag, allowed), expected
    elif name == 'float-cell':
        for bits, flag in itertools.product((0, MIN, 9221120237041090560, 9218868437227405312), (False, True)):
            yield (bits, flag), ('return', (bits if flag else MIN,))
    elif name == 'passthrough':
        for value, flag in itertools.product((MIN, 0, MAX), (False, True)):
            yield (value, flag), ('return', (value,))
    else: raise AssertionError(f'unknown fixture {name}')


class U1PromotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(); cls.addClassCleanup(cls.temporary.cleanup)
        cls.root = Path(cls.temporary.name)
        (cls.root / 'compiler').symlink_to(ROOT / 'src/compiler', target_is_directory=True)
        cls.calls = [f'{family}({width}{",false" if family == "diamond" else ""})'
                     for family in ('diamond', 'loop', 'sequential') for width in (8, 32, 128)]
        cls.calls += ['diamond(2,true)', 'swap()', 'reset()', 'irreducible()', 'dead(false)', 'faults(false)', 'faults(true)', 'floatCell()', 'passthrough()',
                      'invalidCell(0)', 'invalidCell(1)', 'invalidCell(2)', 'dead(true)', 'failedWork()', 'canonicalReject()', 'failedOutput()', 'cancelled()']
        cls.source = cls.root / 'promotion.eri'; cls.source.write_text(probe_source(cls.calls))
        cls.binary = cls.root / 'promotion-c'
        if build_native(cls.source, cls.binary, cls.root):
            raise AssertionError('promotion probe did not compile')

    def check_snapshots(self, text):
        snapshots, labels = parse_snapshots(text)
        for name, counts, before, after in snapshots:
            self.assertLessEqual(counts[3], 8*1024*1024, name)
            self.assertLessEqual(counts[4], 64*1024*1024, name)
            self.assertLessEqual(counts[5], 33554432, name)
            self.assertEqual(after['cells'], [], name)
            self.assertTrue(all(op < 10 for op in after['instructions'][::10]), name)
            for parameters, expected in cases_for(name, before):
                with self.subTest(fixture=name, cells=len(before['cells'])//2, parameters=parameters):
                    original, original_trace = evaluate(before, parameters)
                    transformed, transformed_trace = evaluate(after, parameters)
                    self.assertEqual(original, expected)
                    self.assertEqual((transformed, transformed_trace), (original, original_trace))
                    if name == 'reset': self.assertEqual(original_trace, ((4, 2, True), (4, 2, True)))
            if name == 'dead': self.assertEqual(counts[2], 1)
            if name == 'passthrough': self.assertTrue(all(count == 0 for count in after['blocks'][6::5]))
        return snapshots, labels

    def test_differential_execution_shapes_and_failure_cleanup(self):
        result = subprocess.run([str(self.binary)], capture_output=True, text=True, timeout=120)
        self.assertEqual((result.returncode, result.stderr), (0, ''), result.stdout[-300:])
        snapshots, labels = self.check_snapshots(result.stdout)
        self.assertEqual(len(snapshots), 18)
        self.assertEqual(labels, ['invalid-init:ok']*3 + ['malformed-dead:ok', 'promotion-limit:ok', 'canonical-reject:ok', 'partial-output:ok', 'cancelled:ok'])
        again = subprocess.run([str(self.binary)], capture_output=True, text=True, timeout=120)
        self.assertEqual((again.returncode, again.stdout, again.stderr), (0, result.stdout, ''))

    def test_nominal_cells_cannot_be_used_as_values(self):
        path = self.root / 'wrong-cell.eri'
        path.write_text('''import compiler.u1_builder as build;
import compiler.u1_budget as budget;
public function bad(routine identity build.Function,local build.CellId) fails budget.LimitError {
    let ignored be try build.valueType(routine,local);
}
''')
        with self.assertRaises(SemanticError) as caught: compile_module(path, self.root)
        self.assertIn('CellId', str(caught.exception)); self.assertIn('ValueId', str(caught.exception))

    @unittest.skipUnless(platform.system() == 'Linux' and platform.machine().lower() in ('x86_64', 'amd64'),
                         'owned runtime execution requires Linux x86-64')
    def test_eristavi_emitted_promotion_on_both_runtimes(self):
        for tool in ('as', 'ld', 'cc', 'readelf', 'nm'):
            if not shutil.which(tool): self.skipTest(f'{tool} unavailable')
        # Broad owned-runtime stress is still unqualified (see PR #59). This
        # focused test has one extra verification; bootstrap shape tests use 8.
        source = self.root / 'promotion-native.eri'
        source.write_text(probe_source(['diamond(2,false)', 'loop(2)', 'swap()', 'reset()'], repetitions=1))
        frontend, generator = self.root / 'frontend', self.root / 'generator'
        self.assertEqual(build_native(ROOT / 'src/frontend.eri', frontend, ROOT / 'src'), 0)
        self.assertEqual(build_native(ROOT / 'src/owned_runtime.eri', generator, ROOT / 'src'), 0)
        emitted = subprocess.run([str(frontend), 'emit-asm', str(source), '--source-root', str(self.root), '--target', 'x86_64-linux'],
                                 capture_output=True, text=True, timeout=120)
        self.assertEqual((emitted.returncode, emitted.stderr), (0, ''))
        runtime = subprocess.run([str(generator)], capture_output=True, text=True, timeout=60)
        self.assertEqual((runtime.returncode, runtime.stderr), (0, ''))
        assembly, runtime_source = self.root / 'probe.s', self.root / 'runtime.s'
        assembly.write_text(emitted.stdout); runtime_source.write_text(runtime.stdout)
        obj, runtime_obj = self.root / 'probe.o', self.root / 'runtime.o'
        for path, target in ((assembly, obj), (runtime_source, runtime_obj)):
            subprocess.run(['as', '--64', str(path), '-o', str(target)], check=True, capture_output=True, timeout=30)
        owned, bootstrap = self.root / 'owned', self.root / 'bootstrap'
        subprocess.run(['ld', '-nostdlib', '-static', '-e', '_start', str(obj), str(runtime_obj), '-o', str(owned)], check=True, capture_output=True, timeout=30)
        subprocess.run(['cc', '-std=c11', '-O2', '-DERIST_NATIVE_RUNTIME', '-DERIST_HEAP_GC_INTERVAL=65536', str(assembly),
                        str(ROOT / 'runtime/native_gc_runtime.c'), '-lm', '-o', str(bootstrap)], check=True, capture_output=True, timeout=60)
        headers = subprocess.check_output(['readelf', '-lW', str(owned)], text=True)
        self.assertNotIn('INTERP', headers); self.assertNotIn('DYNAMIC', headers)
        self.assertNotIn('RWE', next(line for line in headers.splitlines() if 'GNU_STACK' in line))
        self.assertEqual(subprocess.check_output(['nm', '-u', str(owned)], text=True).strip(), '')
        observations = []
        for binary in (bootstrap, owned):
            result = subprocess.run([str(binary)], capture_output=True, text=True, timeout=120, env={'PATH': '/unavailable', 'LANG': 'C'})
            self.assertEqual((result.returncode, result.stderr), (0, ''), result.stdout[-300:])
            snapshots, labels = self.check_snapshots(result.stdout)
            self.assertEqual(len(snapshots), 4); self.assertEqual(labels, [])
            observations.append(result.stdout)
        self.assertEqual(observations[0], observations[1])


if __name__ == '__main__': unittest.main()
