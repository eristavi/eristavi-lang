"""Fact indexing retains AST identity, newest fact and synthetic-node fallback."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from compiler.erist.cli import build_native
ROOT=Path(__file__).resolve().parents[1]

class SourceFactIndexTests(unittest.TestCase):
    def test_identity_collisions_reanalysis_and_synthetic_nodes(self):
        source='''import compiler.semantic_model as m; import compiler.ast;
function kind(owner identity m.Module,node identity ast.Node) returns Int {
    let fact be m.expressionFact(owner,node); if fact!=none { return fact.value.kind; } return -1;
}
let loc be identity m.Location { path="probe"; line=1; column=1; next=none; ordinal=0; left=none; right=none; facts=none; };
let a be ast.make(0,0,none,none,none,"",0,false);
let b be ast.make(0,0,none,none,none,"",0,false);
let c be ast.make(0,-1,none,none,none,"",0,false);
let owner be identity m.Module { name="probe"; path="probe"; root=a; locations=loc; locationIndex=loc; imports=none; declarations=none; facts=none; state=2; entry=true; next=none; };
m.remember(owner,a,m.result(m.makeType(1,"")));
m.remember(owner,b,m.result(m.makeType(2,"")));
output(kind(owner,a)); output(kind(owner,b));
m.remember(owner,a,m.result(m.makeType(3,""))); output(kind(owner,a));
m.remember(owner,c,m.result(m.makeType(4,""))); output(kind(owner,c));
output(kind(owner,ast.make(0,0,none,none,none,"",0,false)));
'''
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);shutil.copytree(ROOT/'src/compiler',root/'compiler')
            entry=root/'main.eri';entry.write_text(source);binary=root/'probe'
            self.assertEqual(build_native(entry,binary,root),0)
            r=subprocess.run([binary],capture_output=True,text=True,timeout=10)
            self.assertEqual((r.returncode,r.stdout,r.stderr),(0,'1\n2\n3\n4\n-1\n',''))
