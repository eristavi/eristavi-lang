"""Observe identity updates made before a checked failure is rethrown."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from compiler.erist.cli import build_native

SOURCE = '''
error Failure { message Text; }
type Box { state Int; }
function cleanup(box identity Box) { box.state=42; }
function raising(box identity Box,failNow Bool) returns Int fails Failure {
    if failNow { box.state=7; fail Failure { message="failure"; }; } return 5;
}
function raisingVoid(box identity Box) fails Failure { let value be try raising(box,true); }
function handledLet(box identity Box) returns Int fails Failure {
    let value be raising(box,true) else error Failure { cleanup(box); fail error; }; return value;
}
function handledAssign(box identity Box) returns Int fails Failure {
    let value be 0; value=raising(box,true) else error Failure { cleanup(box); fail error; }; return value;
}
function handledReturn(box identity Box) returns Int fails Failure {
    return raising(box,true) else error Failure { cleanup(box); fail error; };
}
function handledExpression(box identity Box) returns Int fails Failure {
    raisingVoid(box) else error Failure { cleanup(box); fail error; }; return 0;
}
function run(kind Int) {
    let box be identity Box { state=0; };
    if kind == 0 { let value be handledLet(box) else error Failure { output(box.state); return; }; }
    if kind == 1 { let value be handledAssign(box) else error Failure { output(box.state); return; }; }
    if kind == 2 { let value be handledReturn(box) else error Failure { output(box.state); return; }; }
    if kind == 3 { let value be handledExpression(box) else error Failure { output(box.state); return; }; }
    let value be raising(box,false) else error Failure { output(-1); return; }; output(value); output(box.state);
}
run(0); run(1); run(2); run(3); run(4);
'''


class CFailureRecoveryTests(unittest.TestCase):
    def test_optimized_rethrows_preserve_identity_updates_for_all_handled_forms(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source, binary = root / 'recovery.eri', root / 'recovery'
            source.write_text(SOURCE)
            # Preserve CI's compiler choice; this must exercise optimized code.
            with patch.dict(os.environ, {'CFLAGS': '-O2'}):
                self.assertEqual(build_native(source, binary, root), 0)
            result = subprocess.run([str(binary)], capture_output=True, text=True, timeout=30)
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '42\n42\n42\n42\n5\n0\n', ''))


if __name__ == '__main__': unittest.main()
