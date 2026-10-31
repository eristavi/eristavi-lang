"""Integer U1a execution against unbounded mathematics, including call/SSA traces.

The oracle uses Python big integers/divmod. It shares no arithmetic helpers,
overflow thresholds, limb loops or instruction evaluation code with u1_execute.
"""
import itertools
from pathlib import Path
import platform
import random
import shutil
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native
from u1_native_tools import shared_u1_compilers, timed_native_step

ROOT = Path(__file__).resolve().parents[1]
MIN, MAX = -(1 << 63), (1 << 63) - 1
MASK = (1 << 64) - 1
OVERFLOW = (3, 19, 20, 21, 22, 23)
MODES = OVERFLOW + (15, 16, 17, 24, 25, 26, 27) + tuple(range(101, 114))
BOUNDARIES = (MIN, MIN + 1, -(1 << 32), -3037000500, -3037000499,
              -2, -1, 0, 1, 2, 3037000499, 3037000500, 1 << 32, MAX - 1, MAX)


def word(number):
    return (number + (1 << 63)) % (1 << 64) - (1 << 63)


def expected(mode, a, b, nested=False, flow=0):
    original_a = a
    if flow:
        a = word((b if a in (0, MIN, -1) else a) + 3)
    checked, unused = mode >= 200, 124 <= mode <= 127
    op = mode - 200 if checked else mode - 100 if unused else mode
    unsigned = op in (21, 22, 23, 26, 27)
    x, y = (a & MASK, b & MASK) if unsigned else (a, b)
    trap, result, flag = 0, 0, 0
    if op in (3, 15, 21):
        result = x + y
    elif op in (16, 19, 22):
        result = x - y
    elif op in (17, 20, 23):
        result = x * y
    elif op in (24, 25, 26, 27):
        if y == 0:
            trap = 2
        elif not unsigned and x == MIN and y == -1:
            trap = 1
        else:
            q, r = divmod(abs(x), abs(y))
            if not unsigned:
                q *= -1 if (x < 0) != (y < 0) else 1
                r *= -1 if x < 0 else 1
            result = q if op in (24, 26) else r
    elif 101 <= mode <= 110:
        ua, ub = a & MASK, b & MASK
        flag = int((a == b, a != b, a < b, a <= b, a > b, a >= b,
                    ua < ub, ua <= ub, ua > ub, ua >= ub)[mode - 101])
    elif mode == 111:
        flag = int(a != 0)
    elif mode == 112:
        flag = int(a == 0 and b == 0)
    elif mode == 113:
        flag = int(a == 0 or b == 0)
    else:
        raise AssertionError(f'unknown fixture recipe {mode}')
    if op in OVERFLOW:
        flag = int(not (0 <= result <= MASK if unsigned else MIN <= result <= MAX))
    if checked and flag:
        trap = 1
    if unused and not trap:
        trap = 3  # The later guard runs only after a successful unused div/rem.
    trace = f'trace:{original_a};' if nested else ''
    if trap:
        return (1, trap, 2, 0), trace
    if nested:
        trace += f'trace:{b};'
    return (0, 0, 0, 2, word(result), flag), trace


def literal(value):
    return '-9223372036854775807-1' if value == MIN else str(value)


def call_statements(recipes, limits=False):
    calls = []
    for mode, pairs, nested, flow in recipes:
        first = ','.join(literal(a) for a, _ in pairs)
        second = ','.join(literal(b) for _, b in pairs)
        calls.append(f'try cases({mode},[{first}],[{second}],'
                     f'{str(nested).lower()},{flow});')
    if limits:
        calls += ['try limits();', 'try frameLimit();',
                  'try executionWorkLimit();', 'try malformedExecution();']
    return '\n'.join(calls)


def source_for(recipes, limits=False, groups=None):
    declarations = ''
    calls = call_statements(recipes, limits)
    if groups is not None:
        declarations = '\n'.join(
            f'function worker{index}() returns Bool fails budget.LimitError,verify.InvalidIR,ProbeError {{\n'
            + call_statements(group, check_limits) + '\nreturn true;\n}'
            for index, (group, check_limits) in enumerate(groups))
        calls = 'let args be process.arguments();\n'
        calls += 'if args.count != 1 { fail ProbeError { message="missing worker selection"; }; }\n'
        calls += '\n'.join(f'if args[0] == "{index}" {{ return try worker{index}(); }}'
                           for index in range(len(groups)))
        calls += '\nfail ProbeError { message="invalid worker selection"; };'
    return (ROOT / 'tests/fixtures/u1_integer_execution.eri').read_text() + declarations + '''
function run() returns Bool fails budget.LimitError,verify.InvalidIR,ProbeError {
''' + calls + '''
    return true;
}
function main() {
    let success be run()
    else error budget.LimitError { output(error.category+":"+error.message); process.setExitCode(1); return; }
    else error verify.InvalidIR { output(error.category+":"+error.message); process.setExitCode(1); return; }
    else error ProbeError { output(error.message); process.setExitCode(1); return; };
}
main();
'''


def expected_lines(recipes, limits=False):
    lines = []
    for mode, pairs, nested, flow in recipes:
        for index, (a, b) in enumerate(pairs):
            fields, trace = expected(mode, a, b, nested, flow)
            lines.append(':'.join(map(str, (mode, index, *fields))) + ':' + trace)
    if limits:
        lines += ['execution-limits:ok', 'execution-cancelled:ok',
                  'partial-frame-quota:ok', 'execution-work-quota:ok',
                  'fresh-integer-verification:ok']
    return lines


class U1IntegerExecutionTests(unittest.TestCase):
    def compile_and_run(self, recipes, limits=False):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'compiler').symlink_to(ROOT / 'src/compiler', target_is_directory=True)
            source, binary = root / 'integer.eri', root / 'integer'
            source.write_text(source_for(recipes, limits))
            self.assertEqual(build_native(source, binary, root), 0)
            result = subprocess.run([str(binary)], capture_output=True, text=True, timeout=120)
            self.assertEqual((result.returncode, result.stderr), (0, ''), result.stdout[-1000:])
            self.assertEqual(result.stdout.splitlines(), expected_lines(recipes, limits))

    def test_integer_opcode_boundary_and_generated_oracle(self):
        rng = random.Random(0xE7157A)
        pairs = list(itertools.product(BOUNDARIES, repeat=2))
        pairs += [(word(rng.getrandbits(64)), word(rng.getrandbits(64))) for _ in range(48)]
        # Add exact multiplication boundaries and near-boundary divisors,
        # independently derived using unbounded division rather than thresholds
        # copied from the evaluator implementation.
        for b in (3, 7, 65535, 65536, (1 << 31) - 1, 1 << 32, MAX):
            q = MASK // b
            pairs += [(word(q + d), b) for d in (-1, 0, 1)]
            q = MAX // b
            pairs += [(q + d, b) for d in (-1, 0, 1)]
        self.compile_and_run([(mode, pairs, False, 0) for mode in MODES])

    def test_integer_recursion_switch_promotion_and_fault_traces(self):
        pairs = [(MAX, 1), (MIN, -1), (-1, -1), (0, 0), (MIN, 2),
                 (MAX, -1), (-7, 3), (0, MAX), (-1, MIN), (1, 0)]
        modes = OVERFLOW + (24, 25, 26, 27) + tuple(200 + op for op in OVERFLOW) + (124, 125, 126, 127)
        recipes = [(mode, pairs, True, flow) for mode in modes for flow in (0, 1, 2)]
        self.compile_and_run(recipes, limits=True)

    @unittest.skipUnless(platform.system() == 'Linux' and platform.machine().lower() in ('x86_64', 'amd64'),
                         'owned runtime execution requires Linux x86-64')
    def test_integer_executor_on_both_native_runtimes(self):
        for tool in ('as', 'ld', 'cc', 'readelf', 'nm'):
            if not shutil.which(tool):
                self.skipTest(f'{tool} unavailable')
        # All admitted integer/predicate modes, then hard unsigned and nested
        # promoted fault cases. This is focused runtime parity, not the large
        # physical-resource qualification or the experimental compiler self-build.
        recipes = [(mode, [(MIN, MIN), (MIN, -1)] if mode in (24, 25) else [(MIN, MIN)], False, 0)
                   for mode in MODES]
        recipes += [(mode, [(-1, 3)], False, 0) for mode in OVERFLOW + (26, 27)]
        recipes += [(mode, [(-2, MAX), (MAX, 0)], True, 2)
                    for mode in (203, 220, 26, 127)]
        # Independent worker groups retain EVERY case and the existing 120s
        # per-worker watchdog. The first single-process 42-case owned run
        # exceeded that watchdog; it is not a completed performance sample.
        groups = [(recipes[:13], False), (recipes[13:26], False), (recipes[26:], True)]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'compiler').symlink_to(ROOT / 'src/compiler', target_is_directory=True)
            source = root / 'integer-native.eri'
            source.write_text(source_for([], groups=groups))
            frontend, generator = shared_u1_compilers()
            emitted = subprocess.run(
                [str(frontend), 'emit-asm', str(source), '--source-root', str(root), '--target', 'x86_64-linux'],
                capture_output=True, text=True, timeout=120)
            self.assertEqual((emitted.returncode, emitted.stderr), (0, ''), emitted.stdout[-1000:])
            runtime = subprocess.run([str(generator)], capture_output=True, text=True, timeout=60)
            self.assertEqual((runtime.returncode, runtime.stderr), (0, ''))
            assembly, runtime_source = root / 'integer.s', root / 'runtime.s'
            assembly.write_text(emitted.stdout)
            runtime_source.write_text(runtime.stdout)
            obj, runtime_obj = root / 'integer.o', root / 'runtime.o'
            for path, target in ((assembly, obj), (runtime_source, runtime_obj)):
                subprocess.run(['as', '--64', str(path), '-o', str(target)],
                               check=True, capture_output=True, timeout=30)
            owned, bootstrap = root / 'owned', root / 'bootstrap'
            subprocess.run(['ld', '-nostdlib', '-static', '-e', '_start', str(obj), str(runtime_obj), '-o', str(owned)],
                           check=True, capture_output=True, timeout=30)
            subprocess.run(['cc', '-std=c11', '-O2', '-DERIST_NATIVE_RUNTIME', '-DERIST_HEAP_GC_INTERVAL=65536',
                            str(assembly), str(ROOT / 'runtime/native_gc_runtime.c'), '-lm', '-o', str(bootstrap)],
                           check=True, capture_output=True, timeout=60)
            headers = subprocess.check_output(['readelf', '-lW', str(owned)], text=True)
            self.assertNotIn('INTERP', headers)
            self.assertNotIn('DYNAMIC', headers)
            self.assertNotIn('RWE', next(line for line in headers.splitlines() if 'GNU_STACK' in line))
            self.assertEqual(subprocess.check_output(['nm', '-u', str(owned)], text=True).strip(), '')
            observations = []
            for binary in (bootstrap, owned):
                complete = ''
                for index, (group, check_limits) in enumerate(groups):
                    result = timed_native_step(
                        f'integer {binary.name} worker {index}', subprocess.run,
                        [str(binary), str(index)], capture_output=True, text=True, timeout=120,
                        env={'PATH': '/unavailable', 'LANG': 'C'})
                    self.assertEqual((result.returncode, result.stderr), (0, ''),
                                     f'{binary.name} worker {index}: {result.stdout[-1000:]}')
                    self.assertEqual(result.stdout.splitlines(), expected_lines(group, check_limits))
                    complete += result.stdout
                observations.append(complete)
            self.assertEqual(*observations)
            # Direct deterministic ABI regression, including scratch-reserve
            # refusal: neither abandoned roots nor raw integer-class bits may
            # be mistaken for live value slots after checked unwinding.
            prefix = runtime.stdout.split('.text\n.globl _start\n.type _start,@function\n_start:', 1)
            self.assertEqual(len(prefix), 2, 'owned startup marker missing')
            probe = (ROOT / 'tests/fixtures/owned_unwind_roots.s').read_text()
            for fallback in (False, True):
                text = prefix[0]
                if fallback:
                    before, after = text.split('.Lunwind_index_allocate:', 1)
                    allocation, after = after.split('.Lunwind_index_fallback:', 1)
                    self.assertEqual(allocation.count('call erist_rt_reserve'), 1)
                    allocation = allocation.replace('call erist_rt_reserve', 'xorl %eax,%eax')
                    text = before + '.Lunwind_index_allocate:' + allocation + '.Lunwind_index_fallback:' + after
                path, obj, binary = root / 'unwind.s', root / 'unwind.o', root / 'unwind'
                path.write_text(text + probe)
                subprocess.run(['as', '--64', str(path), '-o', str(obj)], check=True, capture_output=True, timeout=30)
                subprocess.run(['ld', '-nostdlib', '-static', '-e', '_start', str(obj), '-o', str(binary)],
                               check=True, capture_output=True, timeout=30)
                result = subprocess.run([str(binary)], capture_output=True, text=True, timeout=10,
                                        env={'PATH': '/unavailable', 'LANG': 'C'})
                self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''), fallback)


if __name__ == '__main__':
    unittest.main()
