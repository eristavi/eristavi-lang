"""Linked ingress rejects stale and same-revision corruption, including dead IR."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from compiler.erist.cli import build_native
ROOT = Path(__file__).resolve().parents[1]

CHECKS = '''
    let preservedLive be root.live;
    let oldRevision be copy.revision;
    copy.revision=copy.revision+1;
    try check((try deniedLinked(program,mainId,mainOwner)),"stale uncalled/callee body accepted");
    copy.revision=oldRevision;
    let oldSignature be copy.signature;
    copy.signature=entrySig;
    try check((try deniedLinked(program,mainId,mainOwner)),"changed callee signature accepted");
    copy.signature=oldSignature;
    let foreign be meta.FunctionId { owner=identity meta.Key { marker=0; }; index=mainId.index; };
    try check((try deniedLinked(program,foreign,mainOwner)),"foreign function owner accepted");
    try check((try deniedLinked(program,mainId,copyOwner)),"foreign execution owner accepted");
    let wp be try budget.constructionPhase(copyOwner);
    let deadFirst be try words.get(copy.blocks,wp,(dead.index-1)*5+2);
    let at be (deadFirst-1)*10;
    let originalOp be try words.get(copy.instructions,wp,at);
    copy.instructions.frozen=false;
    try words.set(copy.instructions,wp,at,999);
    copy.instructions.frozen=true;
    try budget.finishPhase(wp);
    try check((try deniedLinked(program,mainId,mainOwner)),"same-revision malformed dead callee accepted");
    wp=try budget.constructionPhase(copyOwner);
    copy.instructions.frozen=false;
    try words.set(copy.instructions,wp,at,originalOp);
    copy.instructions.frozen=true;
    try budget.finishPhase(wp);
    wp=try budget.constructionPhase(failOwner);
    let failFirst be try words.get(failing.blocks,wp,2);
    let failAt be (failFirst-1)*10;
    let failOp be try words.get(failing.instructions,wp,failAt);
    failing.instructions.frozen=false;
    try words.set(failing.instructions,wp,failAt,999);
    failing.instructions.frozen=true;
    try budget.finishPhase(wp);
    try check((try deniedLinked(program,mainId,mainOwner)),"malformed uncalled body accepted");
    wp=try budget.constructionPhase(failOwner);
    failing.instructions.frozen=false;
    try words.set(failing.instructions,wp,failAt,failOp);
    failing.instructions.frozen=true;
    try budget.finishPhase(wp);
    try check(root.live == preservedLive and root.pending == 0,"linked rejection leaked storage");
'''
HELPER = '''
function deniedLinked(program identity call.Program,target meta.FunctionId,owner identity budget.Owner)
    returns Bool {
    let result be call.run(program,target,owner,[0],64,8)
    else error budget.LimitError { return error.category == "invalid-state"; }
    else error verify.InvalidIR { return error.category == "invalid-ir"; };
    return false;
}
'''

class U1AggregateLinkedRejectionTests(unittest.TestCase):
    def test_stale_signature_foreign_owner_and_malformed_dead_callee(self):
        fixture=(ROOT/'tests/fixtures/u1_aggregate_calls.eri').read_text()
        fixture=fixture.replace('import std.process;', 'import std.process;\nimport compiler.u1_words as words;')
        anchor='    if mode != -1 {'
        self.assertEqual(fixture.count(anchor),1)
        fixture=fixture.replace(anchor,CHECKS+anchor)
        fixture=fixture.replace('function main() {',HELPER+'\nfunction main() {')
        fixture=fixture.replace('let done be all()', 'let done be exercise(-1)')
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/'compiler').symlink_to(ROOT/'src/compiler',target_is_directory=True)
            source=root/'reject.eri'; source.write_text(fixture)
            binary=root/'reject'
            self.assertEqual(build_native(source,binary,root),0)
            result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=120)
            self.assertEqual((result.returncode,result.stdout,result.stderr),
                (0,'11\n17\nu1b-aggregate-calls:ok\n',''))
