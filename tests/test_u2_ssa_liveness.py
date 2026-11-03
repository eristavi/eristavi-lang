"""U2 canonical SSA liveness: checked cleanup, dead blocks and forged facts."""
from pathlib import Path
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native

ROOT=Path(__file__).resolve().parents[1]

class U2SSALivenessTests(unittest.TestCase):
    def test_checked_cleanup_ssa_liveness_and_adversarial_mutations(self):
        source=(ROOT/"tests/fixtures/u2_scoped_owners.eri").read_text()
        point="import compiler.u2_scoped_owners as owners;"
        self.assertIn(point,source)
        source=source.replace(point,point+"\n"
            "import compiler.u2_ssa_liveness as ssa;",1)
        helper=(
            "function livenessRejected(plan identity ssa.Plan,"
            "fn identity build.Function,graph identity aggregate.Registry,"
            "table identity contracts.Registry,phase identity budget.Phase)"
            " returns Bool fails budget.LimitError,canonical.InvalidIR {\n"
            "    let result be ssa.verify(plan,fn,graph,table,phase)"
            " else error ssa.InvalidLiveness { return true; }"
            " else error budget.LimitError { fail error; }"
            " else error canonical.InvalidIR { fail error; };\n"
            "    return false;\n"
            "}\n"
        )
        publication_helper=(
            "function publicationRejected(plan identity ssa.Plan,"
            "fn identity build.Function,graph identity aggregate.Registry,"
            "table identity contracts.Registry,phase identity budget.Phase,"
            "call build.InstId,roots)"
            " returns Bool fails budget.LimitError,canonical.InvalidIR {\n"
            "    let proof be ssa.requirePublished(plan,fn,graph,table,phase,"
            "call,roots,true)"
            " else error ssa.InvalidLiveness { return true; }"
            " else error budget.LimitError { fail error; }"
            " else error canonical.InvalidIR { fail error; };\n"
            "    return false;\n"
            "}\n"
        )
        helper=helper+publication_helper
        source=source.replace("function run() fails",helper+"function run() fails",1)
        insertion=(
            "let mutate be try budget.constructionPhase(owner); "
            "let revision be fn.revision;"
        )
        self.assertIn(insertion,source)
        proof=(
            insertion+"\n"
            "    let baselineLive be owner.live;\n"
            "    let plan be try ssa.create(fn,graph,table,mutate,[handle,failure]);\n"
            "    let liveness be try ssa.verify(plan,fn,graph,table,mutate);\n"
            "    try check(liveness.blocks == 11 and liveness.tracked >= 6 and "
            "liveness.revision == revision,\"canonical liveness counts\");\n"
            "    try check(try ssa.liveEntry(plan,fn,mutate,outer,outerValue),"
            "\"outer owner live on entry\");\n"
            "    try check(try ssa.liveExit(plan,fn,mutate,outer,outerValue),"
            "\"outer owner carried across both checked edges\");\n"
            "    try check(try ssa.liveBefore(plan,fn,mutate,innerClose,innerValue),"
            "\"inner close operand must be rooted during invoke\");\n"
            "    try check(not (try ssa.liveAfter(plan,fn,mutate,innerClose,innerValue)),"
            "\"consumed owner incorrectly live after checked invoke\");\n"
            "    let live be []; let slot be 0;\n"
            "    while slot < plan.values.length/4 {\n"
            "        let v be build.ValueId { owner=fn.key;"
            " index=try words.get(plan.values,mutate,slot*4); };\n"
            "        if try ssa.liveBefore(plan,fn,mutate,innerClose,v) { live.add(v); }\n"
            "        slot=slot+1;\n"
            "    }\n"
            "    let count be try ssa.requirePublished(plan,fn,graph,table,mutate,"
            "innerClose,live,true);\n"
            "    try check(count == live.count and count >= 2,"
            "\"checked cleanup publishes all managed SSA roots\");\n"
            "    let missing be []; slot=1;\n"
            "    while slot < live.count { missing.add(live[slot]); slot=slot+1; }\n"
            "    try check(try publicationRejected(plan,fn,graph,table,mutate,"
            "innerClose,missing),\"premature GC-root release accepted\");\n"
            "    let row be 0; let savedLive be try words.get(plan.inputs,mutate,row);\n"
            "    plan.inputs.frozen=false; try words.set(plan.inputs,mutate,row,1-savedLive);"
            " plan.inputs.frozen=true;\n"
            "    try check(try livenessRejected(plan,fn,graph,table,mutate),"
            "\"forged live-in state accepted\");\n"
            "    plan.inputs.frozen=false; try words.set(plan.inputs,mutate,row,savedLive);"
            " plan.inputs.frozen=true;\n"
            "    plan.revision=revision+1;\n"
            "    try check(try livenessRejected(plan,fn,graph,table,mutate),"
            "\"stale liveness revision accepted\"); plan.revision=revision;\n"
            "    let oldLen be plan.outputs.length; plan.outputs.length=oldLen-1;\n"
            "    try check(try livenessRejected(plan,fn,graph,table,mutate),"
            "\"missing live-out state accepted\"); plan.outputs.length=oldLen;\n"
            "    let restored be try ssa.verify(plan,fn,graph,table,mutate);\n"
            "    try check(restored.tracked == liveness.tracked,"
            "\"restored liveness refused\");\n"
            "    try ssa.close(plan);\n"
            "    try check(owner.live == baselineLive,"
            "\"SSA liveness owner backing leaked\");\n"
        )
        source=source.replace(insertion,proof,1)
        source=source.replace(
            "continuation.InvalidBinding,owners.InvalidOwnership,ProbeError {",
            "continuation.InvalidBinding,owners.InvalidOwnership,ssa.InvalidLiveness,ProbeError {",1)
        error_marker='else error ProbeError { output("probe:"+error.message);'
        self.assertIn(error_marker,source)
        source=source.replace(error_marker,
            'else error ssa.InvalidLiveness { output("liveness:"+error.message);'
            ' process.setExitCode(1); }\n'+error_marker,1)
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            (folder/"compiler").symlink_to(
                ROOT/"src/compiler",target_is_directory=True)
            input_file=folder/"u2_liveness.eri"
            input_file.write_text(source,encoding="utf-8")
            output_file=folder/"u2_liveness"
            self.assertEqual(build_native(input_file,output_file,folder),0)
            result=subprocess.run([str(output_file)],capture_output=True,
                                  text=True,timeout=120)
            self.assertEqual(
                (result.returncode,result.stdout,result.stderr),
                (0,"u2-scoped-owners:ok\n",""))
