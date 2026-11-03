"""Loop backedges, phi transport and interleaved canonical SSA safe points."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from compiler.erist.cli import build_native

ROOT=Path(__file__).resolve().parents[1]

class U2SSALoopsTests(unittest.TestCase):
    def test_backedge_parallel_phi_and_safe_point_liveness(self):
        source=(ROOT/"tests/fixtures/u1_aggregate_loops.eri").read_text()
        for anchor in (
            "import compiler.u1_verify as verify;",
            "try budget.finishPhase(mp);",
            "try budget.finishPhase(cp);",
            "try build.close(fn);",
            "returns Bool fails budget.LimitError,verify.InvalidIR,ProbeError {",
            "} else error ProbeError {",
        ):
            self.assertIn(anchor,source)
        source=source.replace("import compiler.u1_verify as verify;",
            "import compiler.u1_verify as verify;\n"
            "import compiler.u1_words as words;\n"
            "import compiler.u2_invoke_contract as contracts;\n"
            "import compiler.u2_ssa_liveness as ssa;",1)
        source=source.replace("try budget.finishPhase(mp);",
            "let table be try contracts.create(data,graph,mp);\n"
            "    try contracts.freeze(table); try budget.finishPhase(mp);",1)
        source=source.replace("try budget.finishPhase(cp);",
            "try budget.finishPhase(cp);\n"
            "    let phase be try budget.constructionPhase(fnOwner);\n"
            "    let plan be try ssa.create(fn,graph,table,phase,[pair]);\n"
            "    let report be try ssa.verify(plan,fn,graph,table,phase);\n"
            "    try check(report.tracked == 4 and report.blocks == 5,"
            "\"self-loop managed SSA slots\");\n"
            "    try check(try ssa.liveEntry(plan,fn,phase,loop,current),"
            "\"self-edge phi not alive at entry\");\n"
            "    try check(try ssa.liveExit(plan,fn,phase,loop,next),"
            "\"self-edge replacement not alive at exit\");\n"
            "    try check(not (try ssa.liveExit(plan,fn,phase,loop,current)),"
            "\"previous loop value should not leave body\");\n"
            "    let nextDefinition be try words.get(fn.values,phase,(next.index-1)*4+2);\n"
            "    let setInstruction be build.InstId { owner=fn.key; index=nextDefinition; };\n"
            "    try check(not (try ssa.liveBefore(plan,fn,phase,setInstruction,next)),"
            "\"SSA next value live before its definition\");\n"
            "    try check(try ssa.liveAfter(plan,fn,phase,setInstruction,next),"
            "\"SSA next value lost after its definition\");\n"
            "    let termIndex be try words.get(fn.blocks,phase,(loop.index-1)*5+4);\n"
            "    let term be build.InstId { owner=fn.key; index=termIndex; };\n"
            "    try check(try ssa.liveBefore(plan,fn,phase,term,next),"
            "\"backedge/exiting branch needs managed value\");\n"
            "    try ssa.close(plan); try budget.finishPhase(phase);",1)
        source=source.replace("try build.close(fn);",
            "try contracts.close(table); try build.close(fn);",1)
        source=source.replace(
            "returns Bool fails budget.LimitError,verify.InvalidIR,ProbeError {",
            "returns Bool fails budget.LimitError,verify.InvalidIR,ssa.InvalidLiveness,ProbeError {",1)
        source=source.replace("} else error ProbeError {",
            "} else error ssa.InvalidLiveness {\n"
            "        output(\"liveness:\"+error.message); process.setExitCode(1); return;\n"
            "    } else error ProbeError {",1)
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            (folder/"compiler").symlink_to(
                ROOT/"src/compiler",target_is_directory=True)
            file=folder/"liveness_loop.eri"
            file.write_text(source,encoding="utf-8")
            exe=folder/"liveness_loop"
            self.assertEqual(build_native(file,exe,folder),0)
            run=subprocess.run([str(exe)],capture_output=True,
                               text=True,timeout=120)
            self.assertEqual(
                (run.returncode,run.stdout,run.stderr),
                (0,"11\n17\nu1b-aggregate-loop:ok\n",""))
