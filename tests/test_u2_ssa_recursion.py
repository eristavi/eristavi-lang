"""Recursive-call SSA safe-point liveness using canonical multi-function UIR."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from compiler.erist.cli import build_native

ROOT=Path(__file__).resolve().parents[1]

class U2SSARecursionTests(unittest.TestCase):
    def test_recursive_managed_value_live_at_call_safepoint(self):
        source=(ROOT/"tests/fixtures/u1_aggregate_calls.eri").read_text()
        source=source.replace("import compiler.u1_verify as verify;",
            "import compiler.u1_verify as verify;\n"
            "import compiler.u2_invoke_contract as contracts;\n"
            "import compiler.u2_ssa_liveness as ssa;",1)
        anchor="try aggregate.freeze(graph); try meta.freeze(data); try budget.finishPhase(mp);"
        self.assertIn(anchor,source)
        source=source.replace(anchor,
            "try aggregate.freeze(graph); try meta.freeze(data);\n"
            "    let table be try contracts.create(data,graph,mp);\n"
            "    try contracts.freeze(table); try budget.finishPhase(mp);",1)
        marker="try ab.complete(copy,graph); try budget.finishPhase(cp);"
        self.assertIn(marker,source)
        source=source.replace(marker,
            marker+"\n"
            "    let lp be try budget.constructionPhase(copyOwner);\n"
            "    let roots be try ssa.create(copy,graph,table,lp,[pair]);\n"
            "    let report be try ssa.verify(roots,copy,graph,table,lp);\n"
            "    try check(report.tracked >= 5 and report.blocks == 5,"
            "\"recursive function SSA metadata\");\n"
            "    try check(try ssa.liveEntry(roots,copy,lp,recurse,recursiveInput),"
            "\"recursive input dead at block entry\");\n"
            "    try check(try ssa.liveBefore(roots,copy,lp,recursiveCall,stopped),"
            "\"recursive call argument not rooted at safe point\");\n"
            "    try check(not (try ssa.liveAfter(roots,copy,lp,recursiveCall,stopped)),"
            "\"dead recursive input incorrectly rooted after call\");\n"
            "    try check(not (try ssa.liveBefore(roots,copy,lp,recursiveCall,recursiveResult)),"
            "\"recursive return live before definition\");\n"
            "    try check(try ssa.liveAfter(roots,copy,lp,recursiveCall,recursiveResult),"
            "\"recursive result not live after call\");\n"
            "    try check(try ssa.liveExit(roots,copy,lp,recurse,recursiveResult),"
            "\"recursive result not live on return edge\");\n"
            "    let live be []; let slot be 0;\n"
            "    while slot < roots.values.length/4 {\n"
            "        let value be build.ValueId { owner=copy.key;"
            " index=try words.get(roots.values,lp,slot*4); };\n"
            "        if try ssa.liveBefore(roots,copy,lp,recursiveCall,value) { live.add(value); }\n"
            "        slot=slot+1;\n"
            "    }\n"
            "    let covered be try ssa.requirePublished(roots,copy,graph,table,lp,"
            "recursiveCall,live,true);\n"
            "    try check(covered == live.count and covered > 0,"
            "\"recursive call live roots before collection\");\n"
            "    try ssa.close(roots); try budget.finishPhase(lp);",1)
        end="try aggregate.close(graph); try meta.close(data);"
        self.assertIn(end,source)
        source=source.replace(end,
            "try contracts.close(table); "+end,1)
        source=source.replace(
            "returns Bool fails budget.LimitError,verify.InvalidIR,ProbeError {",
            "returns Bool fails budget.LimitError,verify.InvalidIR,ssa.InvalidLiveness,ProbeError {",1)
        # Preserve the original fixture unmodified on disk while limiting
        # this augmented test to its ordinary successful execution profile.
        start=source.index("function all() returns Bool")
        end=source.index("function main()",start)
        self.assertGreaterEqual(start,0)
        self.assertGreater(end,start)
        source=source[:start]+(
            "function all() returns Bool fails budget.LimitError,"
            "verify.InvalidIR,ssa.InvalidLiveness,ProbeError {\n"
            "    return try exercise(-1);\n"
            "}\n"
        )+source[end:]
        source=source.replace(
            "function all() returns Bool fails budget.LimitError,verify.InvalidIR,ProbeError {",
            "function all() returns Bool fails budget.LimitError,verify.InvalidIR,ssa.InvalidLiveness,ProbeError {",1)
        exit_anchor="else error ProbeError {"
        self.assertIn(exit_anchor,source)
        source=source.replace(exit_anchor,
            "else error ssa.InvalidLiveness { "
            "output(\"liveness:\"+error.message); process.setExitCode(1); return; }\n"
            +exit_anchor,1)
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            (folder/"compiler").symlink_to(
                ROOT/"src/compiler",target_is_directory=True)
            file=folder/"liveness_recursive.eri"
            file.write_text(source,encoding="utf-8")
            exe=folder/"liveness_recursive"
            self.assertEqual(build_native(file,exe,folder),0)
            run=subprocess.run([str(exe)],capture_output=True,
                               text=True,timeout=120)
            self.assertEqual(run.returncode,0,(run.stdout,run.stderr))
            self.assertIn("u1b-aggregate-calls:ok",run.stdout)
            self.assertEqual(run.stderr,"")
