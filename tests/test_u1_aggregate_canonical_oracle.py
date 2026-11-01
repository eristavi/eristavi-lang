"""Independent Python tuple oracle for canonical, verified U1b SSA aggregates.

Covers 2/9/32 fields, immutable original/updated snapshots, nested projection,
and both branches through simultaneous verified CFG block argument transfer.
The standalone fixture uses Eristavi as the UIR producer/interpreter, never
as the source of its oracle's expected values.
"""
from pathlib import Path
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native

ROOT=Path(__file__).resolve().parents[1]
SIZES=(2,9,32)


def program():
    s=[
        "import std.process;\n",
        "import compiler.u1_budget as budget;\n",
        "import compiler.u1_meta as meta;\n",
        "import compiler.u1_builder as build;\n",
        "import compiler.u1_aggregate as aggregate;\n",
        "import compiler.u1_aggregate_build as ab;\n",
        "import compiler.u1_aggregate_execute as run;\n",
        "import compiler.u1_verify as verify;\n",
        "error ProbeError { message Text; }\n",
        "function check(okay Bool,message Text) fails ProbeError {\n",
        "    if not okay { fail ProbeError { message=message; }; }\n}\n",
        "function exercise() returns Bool fails budget.LimitError,verify.InvalidIR,ProbeError {\n",
        "    let root be try budget.developmentRequest();\n",
        "    let owner be try budget.metadataOwner(root);\n",
        "    let mp be try budget.constructionPhase(owner);\n",
        "    let metadata be try meta.create(owner,mp);\n",
        "    let sig be try meta.signature(metadata,mp,[meta.i64()],[",
        ",".join("meta.i64()" for _ in range(8)),
        "]);\n",
        '    let source be try meta.source(metadata,mp,"canonical-oracle","0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",128);\n',
        "    let loc be try meta.location(metadata,mp,source,0,8,1,1,1);\n",
        "    let graph be try aggregate.create(owner,mp);\n",
        "    let integer be try aggregate.primitive(graph,meta.i64());\n",
    ]
    for n in SIZES:
        s.append(f"    let shape{n} be try aggregate.aggregate(graph,mp,["
                 +",".join("integer" for _ in range(n))+"]);\n")
    s.extend([
        "    let nestedShape be try aggregate.aggregate(graph,mp,[shape9,integer]);\n",
        "    try aggregate.freeze(graph); try meta.freeze(metadata);\n",
        "    try budget.finishPhase(mp);\n",
        "    let fnOwner be try budget.functionOwner(root,false);\n",
        "    let cp be try budget.constructionPhase(fnOwner);\n",
        "    let fn be try build.create(metadata,sig,fnOwner,cp);\n",
        "    let entry be try build.block(fn,[meta.i64()]);\n",
        "    let selector be try build.parameter(fn,entry,0);\n",
        "    let zero be try build.integer(fn,entry,0,loc);\n",
        "    let condition be try build.compareInteger(fn,entry,selector,zero,1,loc);\n",
    ])
    expected=[]
    for n in SIZES:
        original=tuple(100+n*7+i for i in range(n))
        inputs=[]
        for i,num in enumerate(original):
            key=f"c{n}_{i}"
            s.append(f"    let {key} be try build.integer(fn,entry,{num},loc);\n")
            inputs.append(key)
        s.append(f"    let original{n} be try ab.make(fn,graph,entry,shape{n},["
                 +",".join(inputs)+"],loc);\n")
        mid=n//2
        s.append(f"    let update{n} be try build.integer(fn,entry,{900+n},loc);\n")
        s.append(f"    let modified{n} be try ab.set(fn,graph,entry,original{n},{mid},update{n},loc);\n")
        s.append(f"    let before{n} be try ab.get(fn,graph,entry,original{n},{mid},loc);\n")
        s.append(f"    let after{n} be try ab.get(fn,graph,entry,modified{n},{mid},loc);\n")
        expected.extend([original[mid],900+n])
    s.extend([
        "    let endScalar be try build.integer(fn,entry,1234,loc);\n",
        "    let outerOld be try ab.make(fn,graph,entry,nestedShape,[original9,endScalar],loc);\n",
        "    let outerNew be try ab.set(fn,graph,entry,outerOld,0,modified9,loc);\n",
        "    let nestedBefore be try ab.get(fn,graph,entry,outerOld,0,loc);\n",
        "    let nestedAfter be try ab.get(fn,graph,entry,outerNew,0,loc);\n",
        "    let snapshotBefore be try ab.get(fn,graph,entry,nestedBefore,4,loc);\n",
        "    let snapshotAfter be try ab.get(fn,graph,entry,nestedAfter,4,loc);\n",
    ])
    expected.extend([100+9*7+4,909])
    operands=[f"before{n}" for n in SIZES]+[f"after{n}" for n in SIZES]+["snapshotBefore","snapshotAfter"]
    # Oracle above is ordered before/after per size. Instruction return slots
    # deliberately choose the same interleaved order as Python's tuple model.
    operands=[]
    for n in SIZES: operands.extend([f"before{n}",f"after{n}"])
    operands.extend(["snapshotBefore","snapshotAfter"])
    s.extend([
        "    let yes be try build.block(fn,["+",".join("meta.i64()" for _ in operands)+"]);\n",
        "    let no be try build.block(fn,["+",".join("meta.i64()" for _ in operands)+"]);\n",
        "    try build.branch(fn,entry,condition,yes,["+",".join(operands)+"],no,["
        +",".join(reversed(operands))+"],loc);\n",
        "    let yesResults be []; let noResults be [];\n"
    ])
    for i in range(len(operands)):
        s.append(f"    let yes{i} be try build.parameter(fn,yes,{i});\n")
        s.append(f"    let no{i} be try build.parameter(fn,no,{i});\n")
    s.extend([
        "    try build.returnValues(fn,yes,["+",".join(f"yes{i}" for i in range(8))+"],loc);\n",
        "    try build.returnValues(fn,no,["+",".join(f"no{i}" for i in range(8))+"],loc);\n",
        "    try build.complete(fn); try budget.finishPhase(cp);\n",
        "    let resultTrue be try run.run(fn,graph,fnOwner,[0],2048);\n",
        "    let resultFalse be try run.run(fn,graph,fnOwner,[1],2048);\n",
        "    try check(resultTrue.kind == 0 and resultFalse.kind == 0 and resultTrue.count == 8 and resultFalse.count == 8,\"CFG outcomes\");\n",
    ])
    for i in range(8):
        s.append(f"    output(try run.result(resultTrue,{i}));\n")
    for i in range(8):
        s.append(f"    output(try run.result(resultFalse,{i}));\n")
    s.extend([
        "    try build.close(fn); try aggregate.close(graph); try meta.close(metadata);\n",
        '    try check(root.live == 0 and root.pending == 0,"owner bytes fully reclaimed");\n',
        "    try budget.close(fnOwner); try budget.close(owner); try budget.close(root);\n",
        '    output("canonical-aggregate-oracle:ok");\n',
        "    return true;\n}\n",
        "function main() {\n",
        "    let done be exercise()\n",
        '    else error budget.LimitError { output("limit:"+error.message); process.setExitCode(1); return; }\n',
        '    else error verify.InvalidIR { output("invalid:"+error.message); process.setExitCode(1); return; }\n',
        '    else error ProbeError { output("probe:"+error.message); process.setExitCode(1); return; };\n',
        "}\nmain();\n",
    ])
    expected_output="".join(f"{v}\n" for v in expected+list(reversed(expected)))+"canonical-aggregate-oracle:ok\n"
    return "".join(s),expected_output


class U1CanonicalAggregateOracleTests(unittest.TestCase):
    def test_native_verified_canonical_aggregate_oracle(self):
        code,oracle=program()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/"compiler").symlink_to(ROOT/"src/compiler",target_is_directory=True)
            source=root/"oracle.eri"
            source.write_text(code,encoding="utf-8")
            exe=root/"oracle"
            self.assertEqual(build_native(source,exe,root),0)
            completed=subprocess.run([str(exe)],capture_output=True,text=True,
                                     timeout=120,check=False)
            self.assertEqual((completed.returncode,completed.stdout,completed.stderr),
                             (0,oracle,""))


if __name__ == "__main__":
    unittest.main()
