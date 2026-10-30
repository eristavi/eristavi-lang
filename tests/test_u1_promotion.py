"""Scalar-cell SSA promotion: independent execution, shape and failure checks."""
from pathlib import Path
import itertools
import math
import struct
from fractions import Fraction
import platform
import shutil
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native
from compiler.erist.diagnostics import SemanticError
from compiler.erist.project import compile_module

ROOT = Path(__file__).resolve().parents[1]
TABLES = ('blocks', 'values', 'instructions', 'operands', 'edges', 'arguments', 'cells', 'switches', 'cases')
MIN, MAX = -(1 << 63), (1 << 63) - 1



# Separate exact-rational expected-value oracle. The executable reference below
# uses Python host binary64; this oracle does NOT execute a host FP operation.
_U64 = (1 << 64) - 1
_SIGN = 1 << 63
_QNAN = 0x7ff8000000000000
_FLOAT_SAMPLES = (
    0, _SIGN, 1, _SIGN | 1, (1 << 52) - 1, 1 << 52,
    0x3ff0000000000000, 0xbff0000000000000,
    0x3ff0000000000001, 0x3fefffffffffffff,
    0x7fefffffffffffff, 0xffefffffffffffff,
    0x7ff0000000000000, 0xfff0000000000000, _QNAN,
)


def _word(bits):
    bits &= _U64
    return bits - (1 << 64) if bits >= _SIGN else bits


def _host_float(bits):
    return struct.unpack('>d', struct.pack('>Q', bits & _U64))[0]


def _host_bits(number):
    return _word(struct.unpack('>Q', struct.pack('>d', number))[0])


def _exact_float(bits):
    bits &= _U64
    sign = bool(bits & _SIGN)
    exponent = (bits >> 52) & 2047
    fraction = bits & ((1 << 52) - 1)
    if exponent == 2047:
        return ('nan' if fraction else 'inf', sign, None)
    mantissa = fraction if exponent == 0 else (1 << 52) | fraction
    shift = -1074 if exponent == 0 else exponent - 1075
    value = Fraction(mantissa << shift, 1) if shift >= 0 else Fraction(mantissa, 1 << -shift)
    return 'num', sign, -value if sign else value


def _round_binary64(value, negative_zero=False):
    """Exact round-to-nearest-ties-even rational -> IEEE754 binary64 bits."""
    if not value:
        return _SIGN if negative_zero else 0
    negative = value < 0
    numerator, denominator = abs(value.numerator), value.denominator
    exponent = numerator.bit_length() - denominator.bit_length()
    if ((numerator < (denominator << exponent)) if exponent >= 0
            else ((numerator << -exponent) < denominator)):
        exponent -= 1
    if exponent > 1023:
        return (_SIGN if negative else 0) | (0x7ff << 52)
    scale = 52 - exponent if exponent >= -1022 else 1074
    scaled_num = numerator << scale if scale >= 0 else numerator
    scaled_den = denominator if scale >= 0 else denominator << -scale
    mantissa, remainder = divmod(scaled_num, scaled_den)
    if 2 * remainder > scaled_den or (2 * remainder == scaled_den and mantissa & 1):
        mantissa += 1
    if exponent >= -1022:
        if mantissa >= (1 << 53):
            mantissa >>= 1
            exponent += 1
        if exponent > 1023:
            return (_SIGN if negative else 0) | (0x7ff << 52)
        body = ((exponent + 1023) << 52) | (mantissa - (1 << 52))
    else:
        body = mantissa
    return ((_SIGN if negative else 0) | body) & _U64


def _oracle_float_binary(a_bits, b_bits, op):
    """Independent bit-level semantics including exceptional cases and signed 0."""
    a_kind, a_negative, a = _exact_float(a_bits)
    b_kind, b_negative, b = _exact_float(b_bits)
    if a_kind == 'nan' or b_kind == 'nan':
        return _word(_QNAN)
    if op == 29:
        b_negative = not b_negative
        if b_kind == 'num':
            b = -b
    negative = a_negative != b_negative
    if op in (28, 29):
        if a_kind == 'inf' and b_kind == 'inf':
            return _word(_QNAN if a_negative != b_negative
                         else ((_SIGN if a_negative else 0) | (0x7ff << 52)))
        if a_kind == 'inf':
            return _word((_SIGN if a_negative else 0) | (0x7ff << 52))
        if b_kind == 'inf':
            return _word((_SIGN if b_negative else 0) | (0x7ff << 52))
        return _word(_round_binary64(a + b, negative_zero=a_negative and b_negative))
    if op == 30:
        if ((a_kind == 'inf' and b_kind == 'num' and not b)
                or (b_kind == 'inf' and a_kind == 'num' and not a)):
            return _word(_QNAN)
        if a_kind == 'inf' or b_kind == 'inf':
            return _word((_SIGN if negative else 0) | (0x7ff << 52))
        return _word(_round_binary64(a * b, negative_zero=negative))
    if op == 31:
        if a_kind == 'inf' and b_kind == 'inf':
            return _word(_QNAN)
        if a_kind == 'inf':
            return _word((_SIGN if negative else 0) | (0x7ff << 52))
        if b_kind == 'inf':
            return _word(_SIGN if negative else 0)
        if not b:
            return _word(_QNAN if not a else ((_SIGN if negative else 0) | (0x7ff << 52)))
        return _word(_round_binary64(a / b, negative_zero=negative))
    raise AssertionError(f'unsupported exact operation {op}')


def _oracle_float_cmp(a_bits, b_bits, relation):
    a_kind, a_neg, a = _exact_float(a_bits)
    b_kind, b_neg, b = _exact_float(b_bits)
    if a_kind == 'nan' or b_kind == 'nan':
        return relation == 2
    if a_kind == 'inf' and b_kind == 'inf':
        equal, less = a_neg == b_neg, a_neg and not b_neg
    elif a_kind == 'inf':
        equal, less = False, a_neg
    elif b_kind == 'inf':
        equal, less = False, not b_neg
    else:
        equal, less = a == b, a < b
    return (equal, not equal, less, equal or less,
            not equal and not less, not less)[relation-1]


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
            elif op == 36:
                width = {4: 8, 5: 16, 6: 32}[extra]
                outputs = [payload - (1 << width) if payload & (1 << (width-1)) else payload]
            elif op == 2: outputs = [bool(payload)]
            elif op == 3:
                mathematical = operands[0] + operands[1]
                outputs = [((mathematical + (1 << 63)) % (1 << 64)) - (1 << 63), not MIN <= mathematical <= MAX]
            elif op == 4: outputs = [not operands[0]]
            elif op == 13: outputs = [bool(operands[0]) and bool(operands[1])]
            elif op == 14: outputs = [bool(operands[0]) or bool(operands[1])]

            elif op in (15, 16, 17, 19, 20, 21, 22, 23):
                # Interpret i64 arguments as bits; unsigned overflow is computed
                # from unsigned mathematical operands, never Python signed order.
                a, b = operands
                ua, ub = a & ((1 << 64) - 1), b & ((1 << 64) - 1)
                unsigned = op in (21, 22, 23)
                x, y = (ua, ub) if unsigned else (a, b)
                if op in (15, 21): exact = x + y
                elif op in (16, 19, 22): exact = x - y
                else: exact = x * y
                wrapped = ((exact + (1 << 63)) % (1 << 64)) - (1 << 63)
                outputs = [wrapped]
                if op >= 19:
                    outputs.append(not (0 <= exact <= (1 << 64) - 1)
                                   if unsigned else not MIN <= exact <= MAX)
            elif op == 18:
                a, b = operands
                ua, ub = a & ((1 << 64) - 1), b & ((1 << 64) - 1)
                relations = (a == b, a != b, a < b, a <= b, a > b, a >= b,
                             ua < ub, ua <= ub, ua > ub, ua >= ub)
                outputs = [relations[payload - 1]]

            elif op in (24, 25, 26, 27):
                # Execute with exact integer arithmetic, never Float or host i64 division.
                # A fault returns no result/checked failure; it terminates at this LocId.
                a, b = operands
                signed = op in (24, 25)
                ua, ub = a & ((1 << 64) - 1), b & ((1 << 64) - 1)
                if b == 0:
                    trace.append((2, location, False))
                    return ('trap', (2, location)), tuple(trace)
                if signed and a == MIN and b == -1:
                    trace.append((1, location, False))
                    return ('trap', (1, location)), tuple(trace)
                if signed:
                    quotient = abs(a) // abs(b)
                    if (a < 0) != (b < 0):
                        quotient = -quotient
                    remainder = a - quotient * b
                    outputs = [quotient if op == 24 else remainder]
                else:
                    quotient, remainder = divmod(ua, ub)
                    raw = quotient if op == 26 else remainder
                    outputs = [((raw + (1 << 63)) % (1 << 64)) - (1 << 63)]

            elif op in (28, 29, 30, 31, 32, 33):
                # Python host binary64 is the reference *execution* path, not the
                # independent exact-rational expectation oracle below.
                a = _host_float(operands[0])
                if op == 32:
                    outputs = [_word((operands[0] & _U64) ^ _SIGN)]
                else:
                    b = _host_float(operands[1])
                    if op == 33:
                        relations = (a == b, a != b, a < b, a <= b, a > b, a >= b)
                        outputs = [relations[payload - 1]]
                    else:
                        if op == 28: number = a + b
                        elif op == 29: number = a - b
                        elif op == 30: number = a * b
                        else:
                            if b == 0.0:
                                if a == 0.0 or math.isnan(a):
                                    number = math.nan
                                else:
                                    polarity = math.copysign(1.0, a) * math.copysign(1.0, b)
                                    number = math.copysign(math.inf, polarity)
                            else:
                                number = a / b
                        # The U1a core does not expose NaN payloads or flags.
                        outputs = [_word(_QNAN) if math.isnan(number) else _host_bits(number)]

            elif op in (37, 38, 39, 40):
                # Width is an explicit, checked TypeId, not host Int width.
                width = {4: 8, 5: 16, 6: 32}[extra]
                mask = (1 << width) - 1
                a, b = operands
                ua, ub = a & mask, b & mask
                if op == 40:
                    relations = (a == b, a != b, a < b, a <= b, a > b, a >= b,
                                 ua < ub, ua <= ub, ua > ub, ua >= ub)
                    outputs = [relations[payload-1]]
                else:
                    unsigned = op == 39
                    x, y = (ua, ub) if unsigned else (a, b)
                    if payload == 1:
                        exact = x + y
                    elif payload == 2:
                        exact = x - y
                    else:
                        exact = x * y
                    raw = exact & mask
                    signed_value = raw if raw < (1 << (width-1)) else raw - (1 << width)
                    outputs = [signed_value]
                    if op in (38, 39):
                        overflow = (not 0 <= exact <= mask) if unsigned else (
                            not -(1 << (width-1)) <= exact < (1 << (width-1))
                        )
                        outputs.append(overflow)
            elif op == 5:
                trace.append((payload, location, bool(operands[0])))
                if not operands[0]: return ('trap', (payload, location)), tuple(trace)
            elif op in (6, 7, 35):
                if op == 35:
                    first_case, case_count, edge = ir['switches'][(payload-1)*3:payload*3]
                    for row in range(first_case, first_case + case_count):
                        value, successor = ir['cases'][row*2:row*2+2]
                        if value == operands[0]:
                            edge = successor
                            break
                else:
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
    elif name in ('pred-truth', 'pred-merge'):
        for left, right in itertools.product((False, True), repeat=2):
            chosen = right if left else left
            a = chosen if name == 'pred-merge' else left
            yield (left, right), ('return', (a and right, a or right))

    elif name in ('i64-arithmetic', 'i64-merge'):
        boundaries = (MIN, MIN+1, -(1 << 32), -2, -1, 0, 1, 2, (1 << 32), MAX-1, MAX)
        bits = (1 << 64) - 1

        def signed_bits(x):
            return ((x & bits) ^ (1 << 63)) - (1 << 63)

        for a, b in itertools.product(boundaries, repeat=2):
            ua, ub = a & bits, b & bits
            if name == 'i64-arithmetic':
                signed_exact = (a+b, a-b, a*b)
                unsigned_exact = (ua+ub, ua-ub, ua*ub)
                values = [signed_bits(x) for x in signed_exact]
                values.extend((signed_bits(x), x < MIN or x > MAX) for x in signed_exact)
                # Flatten three signed overflow pairs after the three wrap values.
                values = values[:3] + [item for pair in values[3:] for item in pair]
                values.extend(item for x in unsigned_exact
                              for item in (signed_bits(x), x < 0 or x > bits))
                values.extend((a == b, a != b, a < b, a <= b, a > b, a >= b,
                               ua < ub, ua <= ub, ua > ub, ua >= ub))
                yield (a, b), ('return', tuple(values))
            else:
                for flag in (False, True):
                    selected = b if flag else a
                    unsigned_selected = selected & bits
                    exact_multiply = selected * b
                    yield (a, b, flag), ('return', (
                        signed_bits(selected + b),
                        unsigned_selected < ub,
                        exact_multiply < MIN or exact_multiply > MAX,
                        unsigned_selected + ub > bits,
                    ))

    elif name in ('div-signed', 'rem-signed', 'div-unsigned', 'rem-unsigned',
                  'div-merge', 'div-fault-order'):
        # Independent expected values: divmod() of magnitudes, never Float.
        boundaries = (MIN, MIN + 1, -(1 << 48), -9, -7, -3, -1,
                      0, 1, 2, 3, 7, 9, (1 << 48), MAX - 1, MAX)
        mask = (1 << 64) - 1

        def signed_word(v):
            v &= mask
            return v - (1 << 64) if v >= (1 << 63) else v

        def expect_operation(a, b, signed, quotient):
            if b == 0:
                return ('trap', (2, 2))
            if signed and a == MIN and b == -1:
                return ('trap', (1, 2))
            if not signed:
                q, r = divmod(a & mask, b & mask)
                return ('return', (signed_word(q if quotient else r),))
            q_magnitude, r_magnitude = divmod(abs(a), abs(b))
            q = -q_magnitude if (a < 0) != (b < 0) else q_magnitude
            r = -r_magnitude if a < 0 else r_magnitude
            return ('return', (q if quotient else r,))

        for a, b in itertools.product(boundaries, repeat=2):
            if name in ('div-signed', 'div-unsigned', 'rem-signed', 'rem-unsigned'):
                signed = name.endswith('signed') and not name.endswith('unsigned')
                quotient = name.startswith('div')
                yield (a, b), expect_operation(a, b, signed, quotient)
            elif name == 'div-merge':
                for flag in (False, True):
                    selected = b if flag else a
                    first = expect_operation(selected, b, True, True)
                    if first[0] == 'trap':
                        yield (a, b, flag), first
                    else:
                        second = expect_operation(selected, b, False, False)
                        yield (a, b, flag), ('return', (first[1][0], second[1][0]))
            else:  # Guard precedes unused signed remainder and unsigned divide.
                for allowed in (False, True):
                    if not allowed:
                        expected = ('trap', (4, 1))
                    else:
                        earlier = expect_operation(a, b, True, False)
                        if earlier[0] == 'trap':
                            expected = earlier
                        else:
                            expected = expect_operation(a, b, False, True)
                            if expected[0] == 'trap':
                                expected = ('trap', (2, 1))
                    yield (a, b, allowed), expected

    elif name == 'switch-flow':
        for value in (MIN, MIN+1, -1, 0, 1, MAX-1, MAX):
            chosen = 10 if value == 0 else 20 if value == MAX else 30 if value == MIN else 40
            yield (value,), ('return', (chosen,))
    elif name == 'switch-multi-edge':
        for select, a, b, default in itertools.product((0, 1, MAX), (1, -1), (3,), (5,)):
            expected = a if select == 0 else b if select == MAX else default
            yield (select, a, b, default), ('return', (expected,))
    elif name == 'narrow-constants':
        yield (), ('return', (-1, -1, -1))
    elif name == 'narrow-cell':
        for a, b, flag in itertools.product((-128, -1, 0, 1, 127), (-128, 0, 127), (False, True)):
            yield (a, b, flag), ('return', (b if flag else a,))
    elif name == 'float-nonfma':
        # A*b rounds to 1 before adding -1; contraction would give -2^-54.
        triples = ((0x3ff0000002000000, 0x3feffffffc000000, 0xbff0000000000000),
                   (0xbff0000000000000, 0x3ff0000000000000, 0x3ff0000000000000))
        for a, b, c in triples:
            rounded_mul = _oracle_float_binary(a, b, 30)
            yield (_word(a), _word(b), _word(c)), ('return', (_oracle_float_binary(rounded_mul, c, 28),))
    elif name in ('float-arithmetic', 'float-merge'):
        for a, b in itertools.product(_FLOAT_SAMPLES, repeat=2):
            if name == 'float-arithmetic':
                values = [_oracle_float_binary(a, b, op) for op in (28, 29, 30, 31)]
                values.append(_word(a ^ _SIGN))
                values.extend(_oracle_float_cmp(a, b, relation) for relation in range(1, 7))
                yield (_word(a), _word(b)), ('return', tuple(values))
            else:
                for flag in (False, True):
                    chosen = b if flag else a
                    yield (_word(a), _word(b), flag), ('return', (
                        _oracle_float_binary(chosen, b, 28),
                        _word(chosen ^ _SIGN),
                        _oracle_float_cmp(chosen, b, 3),
                    ))

    elif name in ('narrow-i8', 'narrow-i16', 'narrow-i32', 'narrow-ops-merge'):
        width = {'narrow-i8': 8, 'narrow-i16': 16, 'narrow-i32': 32,
                 'narrow-ops-merge': 8}[name]
        mask = (1 << width) - 1
        lowest, highest = -(1 << (width-1)), (1 << (width-1))-1

        def exact_signed(v):
            return (v + (1 << (width-1))) % (1 << width) - (1 << (width-1))

        for a, b in itertools.product((lowest, lowest+1, -1, 0, 1, highest-1, highest), repeat=2):
            ua, ub = a & mask, b & mask
            if name == 'narrow-ops-merge':
                for flag in (False, True):
                    selected = b if flag else a
                    us = selected & mask
                    yield (a, b, flag), ('return', (
                        exact_signed(selected + b),
                        us < ub,
                        not lowest <= selected * b <= highest,
                        us + ub > mask,
                    ))
            else:
                signed_exact = (a+b, a-b, a*b)
                unsigned_exact = (ua+ub, ua-ub, ua*ub)
                outputs = [exact_signed(v) for v in signed_exact]
                for v in signed_exact:
                    outputs.extend((exact_signed(v), not lowest <= v <= highest))
                for v in unsigned_exact:
                    outputs.extend((exact_signed(v), not 0 <= v <= mask))
                outputs.extend((a == b, a != b, a < b, a <= b, a > b, a >= b,
                                ua < ub, ua <= ub, ua > ub, ua >= ub))
                yield (a, b), ('return', tuple(outputs))
    else: raise AssertionError(f'unknown fixture {name}')


class U1PromotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(); cls.addClassCleanup(cls.temporary.cleanup)
        cls.root = Path(cls.temporary.name)
        (cls.root / 'compiler').symlink_to(ROOT / 'src/compiler', target_is_directory=True)
        cls.calls = [f'{family}({width}{",false" if family == "diamond" else ""})'
                     for family in ('diamond', 'loop', 'sequential') for width in (8, 32, 128)]
        cls.calls += ['diamond(2,true)', 'swap()', 'reset()', 'irreducible()', 'dead(false)', 'faults(false)', 'faults(true)', 'floatCell()', 'passthrough()', 'predicateTruth()', 'predicateMerge()', 'integerArithmetic()', 'integerMerge()', 'divideSigned()', 'remainderSigned()', 'divideUnsigned()', 'remainderUnsigned()', 'divisionMerge()', 'divisionFaultOrder()', 'floatArithmetic()', 'floatMerge()', 'floatNonContraction()', 'narrowCell()', 'narrowConstants()', 'narrowArithmetic(meta.i8(),"narrow-i8")',
                     'narrowArithmetic(meta.i16(),"narrow-i16")',
                     'narrowArithmetic(meta.i32(),"narrow-i32")',
                     'narrowArithmeticMerge()', 'switchFlow()', 'switchDistinctEdges()',
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
            self.assertTrue(all(op not in (10, 11, 12) for op in after['instructions'][::10]), name)
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
        self.assertEqual(len(snapshots), 39)
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
