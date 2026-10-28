from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from compiler.erist.cli import build_native

ROOT = Path(__file__).resolve().parents[1]

HARNESS = r'''
import compiler.ast;
import compiler.typed_ir as ir;
import compiler.ir_types;
import compiler.semantic_model as m;

function run() {
    let location be identity m.Location {
        path="type-index.eri"; line=1; column=1; next=none; ordinal=-1;
        left=none; right=none; facts=none;
    };
    let root be ast.make(ast.program(),0,none,none,none,"",0,false);
    let owner be identity m.Module {
        name="test"; path="type-index.eri"; root=root; locations=none;
        locationIndex=none; imports=none; declarations=none; facts=none;
        state=1; entry=true; trace=false; next=none;
    };
    let entry be identity ir.Function {
        index=-1; name="test"; result=5; locals=none; body=ir.node(0,5,location);
        failures=none; next=none;
    };

    // T0 and T27 intentionally collide in the private 257-bucket hash for
    // nominal kind 6 / inner -1. Exact-key checks must keep them distinct.
    let first be identity ir.Type {
        index=6; kind=6; name="T0"; inner=-1; fields=none; checked=false; next=none;
    };
    let second be identity ir.Type {
        index=7; kind=6; name="T27"; inner=-1; fields=none; checked=false; next=first;
    };
    let program be identity ir.Program { functions=none; entry=entry; types=second; };
    let indexer be ir_types.registry(program);

    let a be ir_types.registerIndexed(indexer,program,owner,m.makeType(6,"T0"),location)
        else error m.SemanticError { output(error.message); return; };
    let b be ir_types.registerIndexed(indexer,program,owner,m.makeType(6,"T27"),location)
        else error m.SemanticError { output(error.message); return; };
    let legacyA be ir_types.register(program,owner,m.makeType(6,"T0"),location)
        else error m.SemanticError { output(error.message); return; };
    let legacyB be ir_types.register(program,owner,m.makeType(6,"T27"),location)
        else error m.SemanticError { output(error.message); return; };

    // A new wrapper must receive the same count-based next index as the legacy
    // table would have assigned, become the public list head, and then cache-hit.
    let optionalInt be m.wrap(8,m.makeType(1,""));
    let created be ir_types.registerIndexed(indexer,program,owner,optionalInt,location)
        else error m.SemanticError { output(error.message); return; };
    let repeated be ir_types.registerIndexed(indexer,program,owner,optionalInt,location)
        else error m.SemanticError { output(error.message); return; };

    output(a); output(b); output(legacyA); output(legacyB);
    output(created); output(repeated);
    let head be program.types;
    if head == none { output(-1); } else { output(head.index); }
}
run();
'''


class TypeRegistrationIndexTests(unittest.TestCase):
    def test_collision_exactness_and_public_index_order(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'compiler').symlink_to(ROOT / 'src/compiler', target_is_directory=True)
            entry = root / 'app.eri'
            entry.write_text(HARNESS, encoding='utf-8')
            binary = root / 'type-index'
            self.assertEqual(build_native(entry, binary, root), 0)
            result = subprocess.run([str(binary)], capture_output=True, text=True, timeout=20)
            self.assertEqual((result.returncode, result.stdout, result.stderr),
                             (0, '6\n7\n6\n7\n8\n8\n8\n', ''))


if __name__ == '__main__':
    unittest.main()
