"""Typed outcome destinations in the actual canonical metadata/SSA pools."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from compiler.erist.cli import build_native

ROOT = Path(__file__).resolve().parents[1]
SOURCE = '''
import std.process;
import compiler.u1_budget as budget;
import compiler.u1_words as words;
import compiler.u1_meta as meta;
import compiler.u1_builder as build;
import compiler.u1_aggregate as aggregate;
import compiler.u1_aggregate_verify as graphVerify;
import compiler.u1_aggregate_signature as sig;
import compiler.u1_aggregate_build as ab;
import compiler.u2_continuation_bind as continuation;
error ProbeError { message Text; }
function check(okay Bool,message Text) fails ProbeError { if not okay { fail ProbeError { message=message; }; } }
function rejects(fn identity build.Function,graph identity aggregate.Registry,
    phase identity budget.Phase,pair continuation.Pair) returns Bool fails budget.LimitError {
    let okay be continuation.verify(fn,graph,phase,pair)
        else error continuation.InvalidBinding { return true; }
        else error budget.LimitError { fail error; };
    return false;
}
function category(fn identity build.Function,graph identity aggregate.Registry,
    phase identity budget.Phase,pair continuation.Pair) returns Text {
    let okay be continuation.verify(fn,graph,phase,pair)
        else error budget.LimitError { return error.category; }
        else error continuation.InvalidBinding { return "invalid-binding"; };
    return "accepted";
}
function run() fails budget.LimitError,graphVerify.InvalidGraph,continuation.InvalidBinding,ProbeError {
    let root be try budget.developmentRequest(); let shared be try budget.metadataOwner(root);
    let mp be try budget.constructionPhase(shared); let data be try meta.create(shared,mp);
    let scalar be try meta.signature(data,mp,[meta.i64()],[meta.i64()]);
    let empty be try meta.signature(data,mp,[],[]);
    let normalSig be try meta.signature(data,mp,[],[meta.i64(),meta.pred()]);
    let graph be try aggregate.create(shared,mp);
    let i64 be try aggregate.primitive(graph,meta.i64());
    let pred be try aggregate.primitive(graph,meta.pred());
    let payload be try aggregate.aggregate(graph,mp,[i64,pred]);
    let failureSig be try sig.signature(data,graph,mp,[],[payload]);
    let scalarFailure be try sig.signature(data,graph,mp,[],[i64]);
    let source be try meta.source(data,mp,"continuation.eri","0000000000000000000000000000000000000000000000000000000000000000",64);
    let loc be try meta.location(data,mp,source,0,8,0,1,1);
    let alternate be try meta.location(data,mp,source,9,16,9,2,1);
    try aggregate.freeze(graph); try meta.freeze(data); try budget.finishPhase(mp);
    let gp be try budget.verificationPhase(shared); let checked be try graphVerify.verify(graph,gp); try budget.finishPhase(gp);
    let owner be try budget.functionOwner(root,true); let phase be try budget.constructionPhase(owner);
    let fn be try build.create(data,empty,owner,phase);
    let entry be try build.block(fn,[]);
    let normal be try ab.block(fn,graph,[i64,pred]);
    let failure be try ab.block(fn,graph,[payload]);
    let emptyTarget be try build.block(fn,[]);
    // Existing bootstrap requires an analyzed scalar edge specialization.
    let dead be try build.block(fn,[]);
    let scalarTarget be try build.block(fn,[meta.i64()]);
    let parameter be try build.integer(fn,dead,0,loc);
    try build.jump(fn,dead,scalarTarget,[parameter],loc);
    let before be root.live; let traffic be root.traffic; let revision be fn.revision;
    let pair be try continuation.bind(fn,graph,phase,entry,normal,failure,normalSig,failureSig,loc);
    let zero be try continuation.bind(fn,graph,phase,entry,emptyTarget,failure,empty,failureSig,loc);
    try check(try continuation.verify(fn,graph,phase,zero),"zero normal results");
    try check(root.live == before and root.traffic == traffic and fn.revision == revision,"binding mutates canonical pools");
    let bad be pair; bad.version=3; try check(try rejects(fn,graph,phase,bad),"unknown version accepted");
    bad=pair; bad.revision=revision-1; try check(try rejects(fn,graph,phase,bad),"stale revision accepted");
    bad=pair; bad.functionKey=identity meta.Key { marker=0; }; try check(try rejects(fn,graph,phase,bad),"foreign function accepted");
    bad=pair; bad.typeOwner=identity meta.Key { marker=0; }; try check(try rejects(fn,graph,phase,bad),"foreign type graph accepted");
    bad=pair; bad.normal=entry; try check(try rejects(fn,graph,phase,bad),"entry outcome accepted");
    bad=pair; bad.failure=normal; try check(try rejects(fn,graph,phase,bad),"merged outcomes accepted");
    bad=pair; bad.failurePayload=scalarFailure; try check(try rejects(fn,graph,phase,bad),"scalar failure accepted");
    bad=pair; bad.normalPayload=empty; try check(try rejects(fn,graph,phase,bad),"wrong result arity accepted");
    bad=pair; bad.normal.owner=identity meta.Key { marker=0; }; try check(try rejects(fn,graph,phase,bad),"foreign destination accepted");
    bad=pair; bad.location.owner=identity meta.Key { marker=0; };
    try check(category(fn,graph,phase,bad) == "invalid-state","foreign location accepted");
    // Same-revision mutations of BOTH destination blocks, whether selected or
    // not. The binding grants no stamp and must reread current canonical pools.
    let targets be [normal,failure]; let t be 0; let mutations be 0;
    while t < targets.count {
        let target be targets[t]; let base be (target.index-1)*5;
        let first be try words.get(fn.blocks,phase,base);
        let counts be try words.get(fn.blocks,phase,base+1);
        let field be 0;
        while field < 2 {
            let saved be try words.get(fn.blocks,phase,base+field);
            try words.set(fn.blocks,phase,base+field,9223372036854775807);
            try check(try rejects(fn,graph,phase,pair),"overflowed destination range accepted");
            try words.set(fn.blocks,phase,base+field,saved); field=field+1; mutations=mutations+1;
        }
        let item be 0;
        while item < counts {
            field=0;
            while field < 4 {
                let slot be (first+item-1)*4+field;
                let saved be try words.get(fn.values,phase,slot);
                try words.set(fn.values,phase,slot,999999);
                try check(try rejects(fn,graph,phase,pair),"same-revision payload corruption accepted");
                try words.set(fn.values,phase,slot,saved); field=field+1; mutations=mutations+1;
            }
            item=item+1;
        }
        t=t+1;
    }
    try check(mutations == 16 and fn.revision == revision,"mutation matrix/revision changed");
    try check(try continuation.verify(fn,graph,phase,pair),"restored binding rejected");
    let exhausted be try budget.phase(owner,0);
    try check(category(fn,graph,exhausted,pair) == "resource-limit","wrong refusal kind");
    try budget.finishPhase(exhausted);
    try build.close(fn); try budget.finishPhase(phase); try budget.close(owner);
    try aggregate.close(graph); try meta.close(data); try budget.close(shared);
    try check(root.live == 0 and root.pending == 0,"binding lifecycle leak"); try budget.close(root);
    output("typed-continuation-binding:ok");
}
function main() {
    run() else error budget.LimitError { output("limit:"+error.message); process.setExitCode(1); return; }
    else error graphVerify.InvalidGraph { output("graph:"+error.message); process.setExitCode(1); return; }
    else error continuation.InvalidBinding { output("binding:"+error.message); process.setExitCode(1); return; }
    else error ProbeError { output("probe:"+error.message); process.setExitCode(1); return; };
}
main();
'''


class U2ContinuationBindingTests(unittest.TestCase):
    def test_cleanup_links_require_matching_typed_destinations_and_origins(self):
        text=SOURCE.replace('error ProbeError', '''
import compiler.u2_cleanup_link as link;
import compiler.u2_cleanup_plan as cleanup;
import compiler.u2_cleanup_verify as planVerify;
error ProbeError''',1)
        text=text.replace('continuation.InvalidBinding,ProbeError {','continuation.InvalidBinding,planVerify.InvalidPlan,ProbeError {',1)
        text=text.replace('    let zero be', '''
    let scopes be [cleanup.Scope { scope=1; contract=1; value=parameter.index; close=loc; }];
    let linked be try link.prepare(fn,graph,phase,scopes,0,loc,false,pair);
    try check(try link.verify(fn,graph,phase,linked,scopes,0,loc,false),"typed cleanup link rejected");
    let wrongOrigin be linked; wrongOrigin.continuations.location=alternate;
    try check(linkCategory(fn,graph,phase,wrongOrigin,scopes,loc) == "invalid-binding","different valid link origin accepted");
    let broken be linked; broken.continuations.location.index=999999;
    try check(linkCategory(fn,graph,phase,broken,scopes,loc) == "invalid-state","forged link origin accepted");
    let originalEntry be linked.plan.entry; linked.plan.entry=0;
    try check(linkCategory(fn,graph,phase,linked,scopes,loc) == "invalid-plan","forged plan route accepted by link");
    linked.plan.entry=originalEntry;
    try cleanup.close(linked.plan);
    traffic=root.traffic;
    let zero be''',1)
        helper='''
function linkCategory(fn identity build.Function,graph identity aggregate.Registry,
    phase identity budget.Phase,value link.LinkedExit,active,loc meta.LocId) returns Text {
    let okay be link.verify(fn,graph,phase,value,active,0,loc,false)
        else error budget.LimitError { return error.category; }
        else error planVerify.InvalidPlan { return "invalid-plan"; }
        else error continuation.InvalidBinding { return "invalid-binding"; };
    return "accepted";
}
'''
        text=text.replace('function run()',helper+'\nfunction run()',1)
        text=text.replace('    else error ProbeError {','    else error planVerify.InvalidPlan { output("plan:"+error.message); process.setExitCode(1); return; }\n    else error ProbeError {',1)
        self.compile_probe(text)

    def test_typed_destinations_and_same_revision_negative_matrix(self):
        self.compile_probe(SOURCE)

    def compile_probe(self,text):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            (root/'compiler').symlink_to(ROOT/'src/compiler',target_is_directory=True)
            source=root/'probe.eri'; source.write_text(text,encoding='utf-8')
            binary=root/'probe'
            self.assertEqual(build_native(source,binary,root),0)
            run=subprocess.run([str(binary)],capture_output=True,text=True,timeout=120)
            self.assertEqual((run.returncode,run.stdout,run.stderr),(0,'typed-continuation-binding:ok\n',''))


if __name__ == '__main__': unittest.main()
