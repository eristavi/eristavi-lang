"""Independent U1b narrow-bit reference execution on real hand-built UIR.

Python uses unbounded integers and an arithmetic oracle separate from the
Eristavi-written executor. Tests all three canonical widths, signed overflow,
wraparound, signed/unsigned comparison and MIN/-1 div AND remainder traps.
This is U1b isolated execution, not frontend or production backend migration.
"""
from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native

ROOT = Path(__file__).resolve().parents[1]
OPERATIONS = (
    (37, 1), (37, 3), (38, 3), (39, 3),
    (40, 3), (40, 7), (41, 1), (41, 2), (42, 1), (42, 2),
)
WIDTHS = ((8, "i8"), (16, "i16"), (32, "i32"))


def signed(bits: int, width: int) -> int:
    half = 1 << (width - 1)
    return bits - (1 << width) if bits >= half else bits


def arithmetic_oracle(width: int, opcode: int, mode: int, a: int, b: int):
    """(kind, fault_code, location, result bits, overflow) with true big ints."""
    modulus = 1 << width
    mask, half = modulus - 1, modulus // 2
    x, y = signed(a, width), signed(b, width)
    if opcode in (37, 38, 39):
        if mode == 1:
            unsigned_exact, signed_exact = a + b, x + y
        elif mode == 2:
            unsigned_exact, signed_exact = a - b, x - y
        else:
            unsigned_exact, signed_exact = a * b, x * y
        bits = unsigned_exact & mask
        flag = 0
        if opcode == 38:
            flag = int(not (-half <= signed_exact <= half - 1))
        if opcode == 39:
            flag = int(not (0 <= unsigned_exact <= mask))
        return (0, 0, 0, bits, flag)
    if opcode == 40:
        if mode == 3:
            result = int(x < y)
        elif mode == 7:
            result = int(a < b)
        else:
            raise AssertionError("unrecognized comparison relation")
        return (0, 0, 0, result, 0)
    if b == 0:
        return (1, 2, 1, 0, 0)
    dividend, divisor = (x, y) if mode == 1 else (a, b)
    if mode == 1 and dividend == -half and divisor == -1:
        return (1, 1, 1, 0, 0)
    quotient = abs(dividend) // abs(divisor)
    if (dividend < 0) != (divisor < 0):
        quotient = -quotient
    remainder = dividend - quotient * divisor
    return (0, 0, 0, (quotient if opcode == 41 else remainder) & mask, 0)


def cases_for(width):
    mask = (1 << width) - 1
    half = 1 << (width - 1)
    return (
        (0, 0), (1, 1), (half - 1, 2), (half, mask),
        (mask, 1), (mask, mask), (half, 0),
    )


def generate():
    declarations, bodies, bindings, requests, closures = [], [], [], [], []
    index = 0
    for width, type_name in WIDTHS:
        ty = f"meta.{type_name}()"
        for op, mode in OPERATIONS:
            suffix = str(index)
            signature = f"sig{suffix}"
            declared = f"fn{suffix}"
            owner = f"owner{suffix}"
            phase = f"phase{suffix}"
            routine = f"body{suffix}"
            entry = f"entry{suffix}"
            first = f"first{suffix}"
            second = f"second{suffix}"
            results = f"[{ty},meta.pred()]" if op in (38, 39) else (
                "[meta.pred()]" if op == 40 else f"[{ty}]"
            )
            effects = 16 if op in (41, 42) else 0
            declarations.extend((
                f"let {signature} be try meta.signature(data,metadataPhase,[{ty},{ty}],{results});",
                f'let {declared} be try meta.declaration(data,metadataPhase,{signature},'
                f'"u1b.narrow.{width}.{op}.{mode}",1,{effects},0);',
            ))
            bodies.extend((
                f"let {owner} be try budget.functionOwner(root,false);",
                f"let {phase} be try budget.constructionPhase({owner});",
                f"let {routine} be try build.create(data,{signature},{owner},{phase});",
                f"let {entry} be try build.block({routine},[{ty},{ty}]);",
                f"let {first} be try build.parameter({routine},{entry},0);",
                f"let {second} be try build.parameter({routine},{entry},1);",
            ))
            if op == 37:
                code = f"let v{suffix} be try build.narrowWrap({routine},{entry},{first},{second},{mode},{ty},loc);"
            elif op == 38:
                code = f"let v{suffix} be try build.narrowSignedOverflow({routine},{entry},{first},{second},{mode},{ty},loc);"
            elif op == 39:
                code = f"let v{suffix} be try build.narrowUnsignedOverflow({routine},{entry},{first},{second},{mode},{ty},loc);"
            elif op == 40:
                code = f"let v{suffix} be try build.narrowCompare({routine},{entry},{first},{second},{mode},{ty},loc);"
            elif op == 41:
                code = f"let v{suffix} be try build.narrowDivide({routine},{entry},{first},{second},{mode},{ty},loc);"
            else:
                code = f"let v{suffix} be try build.narrowRemainder({routine},{entry},{first},{second},{mode},{ty},loc);"
            bodies.append(code)
            expression = f"[v{suffix}.value,v{suffix}.overflow]" if op in (38, 39) else f"[v{suffix}]"
            bodies.extend((
                f"try build.returnValues({routine},{entry},{expression},loc);",
                f"try build.complete({routine}); try budget.finishPhase({phase});",
            ))
            bindings.append(f"let ignored{suffix} be try link.bind(program,{declared},{routine});")
            closures.append(f"try build.close({routine}); try budget.close({owner});")
            for case_number, (a, b) in enumerate(cases_for(width)):
                result = f"result{suffix}_{case_number}"
                label = f"{width}:{op}:{mode}:{a}:{b}"
                requests.append(
                    f"let {result} be try exec.run(program,policy,{declared},[{a},{b}],500,8);\n"
                    f'if {result}.kind == 0 {{\n'
                    f'    output("{label}:"+format.integer({result}.kind)+":"+'
                    f'format.integer({result}.code)+":"+format.integer({result}.location)+":"+'
                    f'format.integer(try exec.value({result},0))+":"'
                    f'+format.integer({("try exec.value("+result+",1)") if op in (38,39) else "0"}));\n'
                    f'}} else {{ output("{label}:"+format.integer({result}.kind)+":"+'
                    f'format.integer({result}.code)+":"+format.integer({result}.location)+":0:0"); }}'
                )
            index += 1

    return """// Hand-built narrow UIR, isolated from source frontend and runtime ABI.
import std.process;
import compiler.format as format;
import compiler.u1_budget as budget;
import compiler.u1_meta as meta;
import compiler.u1_builder as build;
import compiler.u1_module as link;
import compiler.u1_imports as imports;
import compiler.u1_execute as exec;
import compiler.u1_verify as verify;

error ProbeError { message Text; }
function run() returns Bool fails budget.LimitError,verify.InvalidIR,ProbeError {
    let root be try budget.developmentRequest();
    let shared be try budget.metadataOwner(root);
    let metadataPhase be try budget.constructionPhase(shared);
    let data be try meta.create(shared,metadataPhase);
""" + "\n".join(declarations) + """
    let source be try meta.source(data,metadataPhase,"u1b-narrow",
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",2048);
    let loc be try meta.location(data,metadataPhase,source,10,18,10,1,1);
    try meta.freeze(data); try budget.finishPhase(metadataPhase);
""" + "\n".join(bodies) + """
    let program be try link.create(data);
""" + "\n".join(bindings) + """
    let bound be try link.seal(program);
    let policy be try imports.create(program);
    let frozen be try imports.freeze(policy);
""" + "\n".join(requests) + """
    try imports.close(policy); try link.close(program);
""" + "\n".join(closures) + """
    try meta.close(data);
    if root.live != 0 or root.pending != 0 {
        fail ProbeError { message="narrow reference owner leaked charges"; };
    }
    try budget.close(shared); try budget.close(root);
    return true;
}
function main() {
    let result be run()
    else error budget.LimitError {
        output(error.category+":"+error.message); process.setExitCode(1); return;
    } else error verify.InvalidIR {
        output(error.category+":"+error.message); process.setExitCode(1); return;
    } else error ProbeError {
        output(error.message); process.setExitCode(1); return;
    };
}
main();
"""


class U1NarrowExecutionTests(unittest.TestCase):
    def test_independent_canonical_narrow_execution_and_faults(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "compiler").symlink_to(ROOT / "src/compiler", target_is_directory=True)
            source = root / "narrow.eri"
            source.write_text(generate(), encoding="utf-8")
            binary = root / "narrow"
            self.assertEqual(build_native(source, binary, root), 0)
            process = subprocess.run(
                [str(binary)], capture_output=True, text=True, timeout=120
            )
            expected = []
            for width, _ in WIDTHS:
                for opcode, mode in OPERATIONS:
                    for a, b in cases_for(width):
                        result = arithmetic_oracle(width, opcode, mode, a, b)
                        expected.append(f"{width}:{opcode}:{mode}:{a}:{b}:"
                                        + ":".join(map(str, result)))
            self.assertEqual((process.returncode, process.stderr), (0, ""), process.stdout[-1000:])
            self.assertEqual(process.stdout.splitlines(), expected)
            self.assertEqual(len(expected), 210)


if __name__ == "__main__":
    unittest.main()
