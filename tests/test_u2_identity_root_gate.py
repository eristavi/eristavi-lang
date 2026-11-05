"""Bounded managed identity descriptor -> canonical SSA publication proof.

This is metadata admission, not native identity lowering; physical alias/cycle
GC and checked File cleanup are separately tested using the owned runtime.
"""
from pathlib import Path
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native

ROOT=Path(__file__).resolve().parents[1]


class U2IdentityRootGateTests(unittest.TestCase):
    def test_verified_identity_descriptor_and_cfg_safe_point_refusals(self):
        source=(ROOT/"tests/fixtures/u1_aggregate_loops.eri").read_text(encoding="utf-8")
        imports="import compiler.u1_meta as meta;"
        self.assertIn(imports,source)
        source=source.replace(imports,imports+"\n"
            "import compiler.u1_words as words;\n"
            "import compiler.u1_aggregate_verify as graphVerify;\n"
            "import compiler.u2_invoke_contract as contracts;\n"
            "import compiler.u2_managed_types as managed;\n"
            "import compiler.u2_ssa_liveness as ssa;\n"
            "import compiler.u2_identity_root_gate as identityRoots;",1)
        helper=(
            "function rejectedIdentity(fn identity build.Function,"
            "graph identity aggregate.Registry,table identity contracts.Registry,"
            "phase identity budget.Phase,registry identity managed.Registry,"
            "carrier aggregate.TypeId,handle managed.TypeId)"
            " returns Bool fails budget.LimitError,verify.InvalidIR,"
            "ssa.InvalidLiveness,managed.InvalidManagedTypes,"
            "graphVerify.InvalidGraph {\n"
            "    let plan be identityRoots.create(fn,graph,table,phase,"
            "registry,carrier,handle)"
            " else error identityRoots.InvalidIdentityRoot { return true; }"
            " else error budget.LimitError { fail error; }"
            " else error verify.InvalidIR { fail error; }"
            " else error ssa.InvalidLiveness { fail error; }"
            " else error managed.InvalidManagedTypes { fail error; }"
            " else error graphVerify.InvalidGraph { fail error; };\n"
            "    try ssa.close(plan); return false;\n"
            "}\n"
            "function missingRoots(plan identity ssa.Plan,"
            "fn identity build.Function,graph identity aggregate.Registry,"
            "table identity contracts.Registry,phase identity budget.Phase,"
            "at build.InstId)"
            " returns Bool fails budget.LimitError,verify.InvalidIR {\n"
            "    let proof be ssa.requirePublished(plan,fn,graph,table,phase,"
            "at,[],false)"
            " else error ssa.InvalidLiveness { return true; }"
            " else error budget.LimitError { fail error; }"
            " else error verify.InvalidIR { fail error; };\n"
            "    return false;\n"
            "}\n"
            "function publicationRejected(plan identity ssa.Plan,"
            "fn identity build.Function,graph identity aggregate.Registry,"
            "table identity contracts.Registry,phase identity budget.Phase,"
            "at build.InstId,roots)"
            " returns Bool fails budget.LimitError,verify.InvalidIR {\n"
            "    let proof be ssa.requirePublished(plan,fn,graph,table,phase,"
            "at,roots,false)"
            " else error ssa.InvalidLiveness { return true; }"
            " else error budget.LimitError { fail error; }"
            " else error verify.InvalidIR { fail error; };\n"
            "    return false;\n"
            "}\n"
        )
        source=source.replace("function run() returns Bool",helper+
            "function run() returns Bool",1)
        target="try aggregate.freeze(graph); try meta.freeze(data);"
        self.assertIn(target,source)
        source=source.replace(target,
            "try aggregate.freeze(graph);\n"
            "    let registry be try managed.create(graph,mp);\n"
            "    let identityType be try managed.identityOfBase(registry,mp,pair);\n"
            "    try managed.freeze(registry);\n"
            "    try meta.freeze(data);\n"
            "    let table be try contracts.create(data,graph,mp);\n"
            "    try contracts.freeze(table);",1)
        self.assertIn("    try budget.finishPhase(cp);",source)
        probe=(
            "    let read be try budget.constructionPhase(fnOwner);\n"
            "    let plan be try identityRoots.create(fn,graph,table,read,"
            "registry,pair,identityType);\n"
            "    let verified be try ssa.verify(plan,fn,graph,table,read);\n"
            "    try check(verified.tracked == 4 and verified.blocks == 5,"
            "\"managed identity carrier SSA inventory\");\n"
            "    try check(try ssa.liveEntry(plan,fn,read,loop,current),"
            "\"identity handle lost at loop entry\");\n"
            "    try check(try ssa.liveExit(plan,fn,read,loop,next),"
            "\"identity successor handle lost on CFG backedge\");\n"
            "    let def be try words.get(fn.values,read,(next.index-1)*4+2);\n"
            "    let at be build.InstId { owner=fn.key; index=def; };\n"
            "    try check(try ssa.liveAfter(plan,fn,read,at,next),"
            "\"new handle unavailable after instruction\");\n"
            "    try check(not (try ssa.liveAfter(plan,fn,read,at,current)),"
            "\"dead handle retained past final use\");\n"
            "    let live be []; let idx be 0;\n"
            "    while idx < plan.values.length/4 {\n"
            "        let candidate be build.ValueId { owner=fn.key;"
            " index=try words.get(plan.values,read,idx*4); };\n"
            "        if try ssa.liveAfter(plan,fn,read,at,candidate) { live.add(candidate); }\n"
            "        idx=idx+1;\n"
            "    }\n"
            "    try check(live.count >= 1 and "
            "(try ssa.requirePublished(plan,fn,graph,table,read,"
            "at,live,false)) == live.count,"
            "\"exact identity-root publication declined\");\n"
            "    try check(try missingRoots(plan,fn,graph,table,read,at),"
            "\"missing identity publication was accepted\");\n"
            "    let deadPublication be []; let all be 0;\n"
            "    while all < live.count { deadPublication.add(live[all]); all=all+1; }\n"
            "    deadPublication.add(current);\n"
            "    try check(try publicationRejected(plan,fn,graph,table,read,at,"
            "deadPublication),\"dead identity root publication accepted\");\n"
            "    let duplicate be []; duplicate.add(live[0]); duplicate.add(live[0]);\n"
            "    try check(try publicationRejected(plan,fn,graph,table,read,at,"
            "duplicate),\"duplicated identity root publication accepted\");\n"
            "    let foreign be []; foreign.add(build.ValueId { owner=data.key;"
            " index=live[0].index; });\n"
            "    try check(try publicationRejected(plan,fn,graph,table,read,at,"
            "foreign),\"foreign identity root publication accepted\");\n"
            "    try check(try rejectedIdentity(fn,graph,table,read,registry,"
            "pair,managed.text(registry)),"
            "\"ordinary Text descriptor impersonated identity\");\n"
            "    let forged be managed.TypeId { owner=data.key;"
            " index=identityType.index; };\n"
            "    try check(try rejectedIdentity(fn,graph,table,read,registry,"
            "pair,forged),\"foreign identity registry was accepted\");\n"
            "    try check(try rejectedIdentity(fn,graph,table,read,registry,"
            "i64,identityType),\"wrong canonical identity payload accepted\");\n"
            "    let identityBaselineLive be fnOwner.live;\n"
            "    try ssa.close(plan); try budget.finishPhase(read);\n"
            "    try check(fnOwner.live <= identityBaselineLive,"
            "\"identity liveness backing was not released\");\n"
        )
        source=source.replace("    try budget.finishPhase(cp);",
            "    try budget.finishPhase(cp);\n"+probe,1)
        source=source.replace("    try build.close(fn); try aggregate.close(graph);",
            "    try contracts.close(table); try managed.close(registry);\n"
            "    try build.close(fn); try aggregate.close(graph);",1)
        source=source.replace(
            "function run() returns Bool fails budget.LimitError,verify.InvalidIR,ProbeError {",
            "function run() returns Bool fails budget.LimitError,verify.InvalidIR,"
            "ProbeError,identityRoots.InvalidIdentityRoot,ssa.InvalidLiveness,"
            "managed.InvalidManagedTypes,graphVerify.InvalidGraph {",1)
        source=source.replace(
            "} else error ProbeError {",
            "} else error identityRoots.InvalidIdentityRoot {"
            ' output("identity:"+error.message); process.setExitCode(1); return;'
            " } else error ssa.InvalidLiveness {"
            ' output("liveness:"+error.message); process.setExitCode(1); return;'
            " } else error managed.InvalidManagedTypes {"
            ' output("managed:"+error.message); process.setExitCode(1); return;'
            " } else error graphVerify.InvalidGraph {"
            ' output("graph:"+error.message); process.setExitCode(1); return;'
            " } else error ProbeError {",1)
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            (folder/"compiler").symlink_to(
                ROOT/"src/compiler",target_is_directory=True)
            input_file=folder/"u2_identity_root_gate.eri"
            input_file.write_text(source,encoding="utf-8")
            binary=folder/"u2_identity_root_gate"
            self.assertEqual(build_native(input_file,binary,folder),0)
            outcome=subprocess.run([str(binary)],capture_output=True,text=True,timeout=120)
            self.assertEqual((outcome.returncode,outcome.stdout,outcome.stderr),
                (0,"11\n17\nu1b-aggregate-loop:ok\n",""))
