"""Canonical invoke and edge-only SSA payload availability; no runtime adapter."""
from pathlib import Path
import os
import platform
import hashlib
import json
import time
import subprocess
import tempfile
import unittest
from compiler.erist.cli import build_native
from u1_native_tools import shared_u1_compilers

ROOT=Path(__file__).resolve().parents[1]
SOURCE='''
import std.process;
import compiler.u1_budget as budget;
import compiler.u1_words as words;
import compiler.u1_meta as meta;
import compiler.u1_builder as build;
import compiler.u1_aggregate as aggregate;
import compiler.u1_aggregate_signature as sig;
import compiler.u1_aggregate_build as ab;
import compiler.u1_verify as verify;
import compiler.u1_successors as succ;
import compiler.u2_invoke_contract as contracts;
import compiler.u2_invoke_build as invoke;
import compiler.u2_continuation_bind as continuation;
error ProbeError { message Text; }
function check(okay Bool,message Text) fails ProbeError { if not okay { fail ProbeError { message=message; }; } }
function rejected(fn identity build.Function,graph identity aggregate.Registry,
    contract contracts.Contract,stage Int) returns Bool fails budget.LimitError,ProbeError {
    let live be fn.owner.live; let pending be fn.owner.pending;
    let phase be try budget.verificationPhase(fn.owner);
    let report be verify.verifyFallible(fn,graph,phase,contract)
        else error verify.InvalidIR {
            try check(error.stage == stage,"wrong rejection stage");
            try check(phase.state == 1 and fn.owner.live == live and fn.owner.pending == pending,"rejection leaked scratch");
            return true;
        } else error budget.LimitError { fail error; };
    return false;
}
function legacyRejected(fn identity build.Function,graph identity aggregate.Registry)
    returns Bool fails budget.LimitError {
    let phase be try budget.verificationPhase(fn.owner);
    let report be verify.verifyAggregates(fn,graph,phase)
        else error verify.InvalidIR { return error.message == "invoke requires explicit U2 fallible profile"; }
        else error budget.LimitError { fail error; };
    return false;
}
function run() fails budget.LimitError,ProbeError,verify.InvalidIR,continuation.InvalidBinding {
    let root be try budget.developmentRequest(); let shared be try budget.metadataOwner(root);
    let mp be try budget.constructionPhase(shared); let data be try meta.create(shared,mp);
    let callerSig be try meta.signature(data,mp,[meta.i64()],[meta.i64()]);
    let targetSig be try meta.signature(data,mp,[meta.i64()],[meta.i64(),meta.pred()]);
    let normalSig be try meta.signature(data,mp,[],[meta.i64(),meta.pred()]);
    let graph be try aggregate.create(shared,mp);
    let i64 be try aggregate.primitive(graph,meta.i64()); let pred be try aggregate.primitive(graph,meta.pred());
    let payload be try aggregate.aggregate(graph,mp,[i64,pred]);
    let failureSig be try sig.signature(data,graph,mp,[],[payload]);
    let target be try meta.declaration(data,mp,targetSig,"u2.test.structural_outcome",2,0,1);
    let source be try meta.source(data,mp,"invoke.eri","0000000000000000000000000000000000000000000000000000000000000000",128);
    let loc be try meta.location(data,mp,source,0,8,0,1,1);
    try aggregate.freeze(graph); try meta.freeze(data); try budget.finishPhase(mp);
    let owner be try budget.functionOwner(root,true); let phase be try budget.constructionPhase(owner);
    let fn be try build.create(data,callerSig,owner,phase);
    let entry be try build.block(fn,[meta.i64()]); let input be try build.parameter(fn,entry,0);
    let normal be try ab.block(fn,graph,[i64,pred]); let failure be try ab.block(fn,graph,[payload]);
    let normalValue be try build.parameter(fn,normal,0); let errorValue be try build.parameter(fn,failure,0);
    let contract be contracts.Contract { version=1; target=target; failure=failureSig; };
    let pair be try continuation.bind(fn,graph,phase,entry,normal,failure,normalSig,failureSig,loc);
    let instruction be try invoke.emit(fn,graph,contract,pair,[input]);
    try ab.returnValues(fn,graph,normal,[normalValue],loc);
    let failedValue be try ab.get(fn,graph,failure,errorValue,0,loc);
    try ab.returnValues(fn,graph,failure,[failedValue],loc);
    // Ordinary dead component retains legacy scalar generic edge specialization.
    let dead be try build.block(fn,[]); let deadTarget be try build.block(fn,[meta.i64()]);
    let constant be try build.integer(fn,dead,0,loc); try build.jump(fn,dead,deadTarget,[constant],loc);
    let deadParameter be try build.parameter(fn,deadTarget,0); try build.returnValues(fn,deadTarget,[deadParameter],loc);
    // A dead invoke must be checked with the same structural/type rigor.
    let uncalled be try build.block(fn,[]);
    let uncalledPair be try continuation.bind(fn,graph,phase,uncalled,normal,failure,normalSig,failureSig,loc);
    let deadInvoke be try invoke.emit(fn,graph,contract,uncalledPair,[input]);
    try ab.complete(fn,graph); try budget.finishPhase(phase);
    let report be try verify.verifyFallible(fn,graph,try budget.verificationPhase(owner),contract);
    try check(report.reachableBlocks == 3,"invoke does not contribute two CFG edges");
    try check(try legacyRejected(fn,graph),"legacy profile accepted invoke");
    let rp be try budget.constructionPhase(owner);
    try check((try words.get(fn.instructions,rp,(instruction.index-1)*10+5)) == 0,"invoke leaks pre-edge result values");
    let revision be fn.revision;
    let normalEdge be try succ.edge(fn,rp,instruction.index,0);
    let failedEdge be try succ.edge(fn,rp,instruction.index,1);
    try check(failedEdge == normalEdge+1,"wrong outcome edge identities");
    let first be try words.get(fn.edges,rp,(normalEdge-1)*3+1);
    let normalReturn be try words.get(fn.blocks,rp,(normal.index-1)*5+4);
    let failedReturn be try words.get(fn.blocks,rp,(failure.index-1)*5+4);
    let offsets be [try words.get(fn.instructions,rp,(normalReturn-1)*10+2),
        try words.get(fn.instructions,rp,(failedReturn-1)*10+2),
        try words.get(fn.instructions,rp,(instruction.index-1)*10+2)];
    let leaks be [failedValue.index,normalValue.index,normalValue.index];
    let i be 0;
    while i < offsets.count {
        let slot be offsets[i]; let old be try words.get(fn.operands,rp,slot);
        fn.operands.frozen=false; try words.set(fn.operands,rp,slot,leaks[i]); fn.operands.frozen=true;
        try check(try rejected(fn,graph,contract,4),"cross-outcome or pre-call result use accepted");
        fn.operands.frozen=false; try words.set(fn.operands,rp,slot,old); fn.operands.frozen=true; i=i+1;
    }
    let marker be try words.get(fn.arguments,rp,first);
    fn.arguments.frozen=false; try words.set(fn.arguments,rp,first,input.index); fn.arguments.frozen=true;
    try check(try rejected(fn,graph,contract,2),"ordinary SSA value substituted for edge result");
    fn.arguments.frozen=false; try words.set(fn.arguments,rp,first,marker); fn.arguments.frozen=true;
    let oldTarget be try words.get(fn.instructions,rp,(deadInvoke.index-1)*10+7);
    fn.instructions.frozen=false; try words.set(fn.instructions,rp,(deadInvoke.index-1)*10+7,999999); fn.instructions.frozen=true;
    try check(try rejected(fn,graph,contract,2),"dead malformed invoke accepted");
    fn.instructions.frozen=false; try words.set(fn.instructions,rp,(deadInvoke.index-1)*10+7,oldTarget); fn.instructions.frozen=true;
    let bad be contract; bad.version=2; try check(try rejected(fn,graph,bad,0),"unknown contract version accepted");
    bad=contract; bad.target.index=0; try check(try rejected(fn,graph,bad,0),"zero FunctionId accepted");
    let restored be try verify.verifyFallible(fn,graph,try budget.verificationPhase(owner),contract);
    try check(restored.reachableBlocks == 3 and fn.revision == revision,"restored same-revision invoke rejected");
    try budget.finishPhase(rp); try build.close(fn); try budget.close(owner);
    try aggregate.close(graph); try meta.close(data); try budget.close(shared);
    try check(root.live == 0 and root.pending == 0,"invoke lifecycle leak"); try budget.close(root);
    output("canonical-invoke-availability:ok");
}
function main() {
    run() else error budget.LimitError { output("limit:"+error.category+":"+error.message); process.setExitCode(1); return; }
    else error verify.InvalidIR { output("ir:"+error.message); process.setExitCode(1); return; }
    else error continuation.InvalidBinding { output("binding:"+error.message); process.setExitCode(1); return; }
    else error ProbeError { output("probe:"+error.message); process.setExitCode(1); return; };
}
main();
'''


class U2InvokeTests(unittest.TestCase):
    def test_zero_normal_results_have_no_fake_ssa_value(self):
        text=SOURCE.replace('[meta.i64()],[meta.i64(),meta.pred()]','[meta.i64()],[]',1)
        text=text.replace('[],[meta.i64(),meta.pred()]','[],[]',1)
        text=text.replace('ab.block(fn,graph,[i64,pred])','ab.block(fn,graph,[])',1)
        text=text.replace('build.parameter(fn,normal,0)','build.integer(fn,normal,123,loc)',1)
        self.compile_probe(text)

    def test_partial_invoke_construction_cannot_publish_and_closes_backing(self):
        helpers='''
function interrupted(fn identity build.Function,graph identity aggregate.Registry,
    contract contracts.Contract,pair continuation.Pair,input build.ValueId)
    returns Bool fails continuation.InvalidBinding {
    let value be invoke.emit(fn,graph,contract,pair,[input])
        else error budget.LimitError { return error.category == "resource-limit"; }
        else error continuation.InvalidBinding { fail error; };
    return false;
}
function completionRefused(fn identity build.Function,graph identity aggregate.Registry) returns Bool {
    ab.complete(fn,graph) else error budget.LimitError { return true; };
    return false;
}
'''
        text=SOURCE.replace('function run()',helpers+'\nfunction run()',1)
        text=text.replace('    let instruction be try invoke.emit(fn,graph,contract,pair,[input]);','''
    // Keep an analyzed concrete legacy-edge specialization before the
    // deliberately poisoned builder and early return below.
    let anchor be try build.block(fn,[]);
    let anchorTarget be try build.block(fn,[meta.i64()]);
    try build.jump(fn,anchor,anchorTarget,[input],loc);
    pair=try continuation.bind(fn,graph,phase,entry,normal,failure,normalSig,failureSig,loc);
    let originalInstructions be fn.instructions.length;
    fn.instructions.limit=originalInstructions+1;
    try check(try interrupted(fn,graph,contract,pair,input),"partial invoke not refused");
    try check(fn.state == 3 and fn.instructions.length == originalInstructions+1 and completionRefused(fn,graph),"partial invoke remained publishable");
    try build.close(fn); try budget.finishPhase(phase); try budget.close(owner);
    try aggregate.close(graph); try meta.close(data); try budget.close(shared);
    try check(root.live == 0 and root.pending == 0,"partial invoke leaked backing"); try budget.close(root);
    output("canonical-invoke-availability:ok"); return;
    let instruction be try invoke.emit(fn,graph,contract,pair,[input]);''',1)
        # This probe ends at refusal; do not leave unreachable generic
        # construction calls for the bootstrap's specialization pass.
        text=text[:text.index('    let instruction be try invoke.emit')]+'}\n'+text[text.index('function main()'):]
        self.compile_probe(text)

    def test_reference_execution_selects_typed_outcome_and_preserves_fuel(self):
        self.compile_probe(self.reference_source())

    def reference_source(self):
        text=SOURCE.replace('error ProbeError', '''
import compiler.u2_invoke_reference as reference;
import compiler.u1_aggregate_verify as graphVerify;
error ProbeError''',1)
        text=text.replace('verify.InvalidIR,continuation.InvalidBinding {',
            'verify.InvalidIR,continuation.InvalidBinding,reference.Unsupported,graphVerify.InvalidGraph {',1)
        hook='''
    let samples be [0,7,9223372036854775807,-1,-19,(0-9223372036854775807-1)]; let sample be 0;
    let retained be owner.live; let pending be owner.pending; let setupWork be 0;
    while sample < samples.count {
        let inputBits be samples[sample]; let fuel be 0;
        while fuel <= 3 {
            let beforeWork be owner.work;
            let result be try reference.execute(fn,graph,contract,inputBits,fuel);
            if sample == 0 and fuel == 0 { setupWork=owner.work-beforeWork; }
            let needed be 2; let expectedTarget be normal.index;
            if inputBits < 0 { needed=3; expectedTarget=failure.index; }
            if fuel < needed {
                try check(result.kind == 2 and result.steps == fuel and result.location == loc.index,"exact reference fuel refusal");
            } else {
                try check(result.kind == 0 and result.value == inputBits and result.steps == needed and
                    result.destination == expectedTarget,"wrong reference outcome or value");
            }
            try check(owner.live == retained and owner.pending == pending,"reference execution leaked backing");
            fuel=fuel+1;
        }
        sample=sample+1;
    }
    let mutateMetadata be try budget.constructionPhase(shared);
    let symbolStart be try words.get(data.declarations,mutateMetadata,(target.index-1)*6+1);
    let oldByte be try words.get(data.symbolBytes,mutateMetadata,symbolStart);
    data.symbolBytes.frozen=false; try words.set(data.symbolBytes,mutateMetadata,symbolStart,118); data.symbolBytes.frozen=true;
    try check(try untrusted(fn,graph,contract),"reference accepted an untrusted import symbol");
    data.symbolBytes.frozen=false; try words.set(data.symbolBytes,mutateMetadata,symbolStart,oldByte); data.symbolBytes.frozen=true;
    try budget.finishPhase(mutateMetadata);
    try check(owner.live == retained and owner.pending == pending,"untrusted adapter refusal leaked");
'''
        helpers='''
function runtimeRejected(fn identity build.Function,graph identity aggregate.Registry,contract contracts.Contract)
    returns Bool fails budget.LimitError,reference.Unsupported,graphVerify.InvalidGraph {
    let result be reference.execute(fn,graph,contract,1,3)
        else error verify.InvalidIR { return error.stage == 4; }
        else error budget.LimitError { fail error; }
        else error reference.Unsupported { fail error; }
        else error graphVerify.InvalidGraph { fail error; };
    return false;
}
function untrusted(fn identity build.Function,graph identity aggregate.Registry,contract contracts.Contract)
    returns Bool fails budget.LimitError,verify.InvalidIR,graphVerify.InvalidGraph {
    let result be reference.execute(fn,graph,contract,1,3)
        else error reference.Unsupported { return error.message == "untrusted U2 reference import symbol"; }
        else error budget.LimitError { fail error; }
        else error verify.InvalidIR { fail error; }
        else error graphVerify.InvalidGraph { fail error; };
    return false;
}
function resourceRefused(fn identity build.Function,graph identity aggregate.Registry,contract contracts.Contract)
    returns Bool fails verify.InvalidIR,reference.Unsupported,graphVerify.InvalidGraph {
    let result be reference.execute(fn,graph,contract,0,0)
        else error budget.LimitError { return error.category == "resource-limit"; }
        else error verify.InvalidIR { fail error; }
        else error reference.Unsupported { fail error; }
        else error graphVerify.InvalidGraph { fail error; };
    return false;
}
'''
        text=text.replace('function run()',helpers+'\nfunction run()',1)
        text=text.replace('    let revision be fn.revision;',hook+'\n    let revision be fn.revision;',1)
        text=text.replace('        try check(try rejected(fn,graph,contract,4),',
            '        try check(try runtimeRejected(fn,graph,contract),"runtime skipped fresh ingress verification");\n'
            '        try check(try rejected(fn,graph,contract,4),',1)
        text=text.replace('    try budget.finishPhase(rp); try build.close(fn);', '''
    owner.workLimit=owner.work+setupWork-1;
    try check(try resourceRefused(fn,graph,contract),"reference ignored work exhaustion");
    try check(owner.live == retained and owner.pending == pending,"reference work refusal leaked backing");
    try budget.finishPhase(rp); try build.close(fn);''',1)
        text=text.replace('    else error ProbeError {',
            '    else error reference.Unsupported { output("unsupported:"+error.message); process.setExitCode(1); return; }\n'
            '    else error graphVerify.InvalidGraph { output("graph:"+error.message); process.setExitCode(1); return; }\n'
            '    else error ProbeError {',1)
        return text

    @unittest.skipUnless(os.environ.get('ERISTAVI_U2_INVOKE_NATIVE') == '1' and
        platform.system() == 'Linux' and platform.machine().lower() in ('x86_64','amd64'),
        'opt-in Linux x86-64 owned-runtime invoke reference probe')
    def test_owned_native_reference_outcomes_and_ingress(self):
        text=self.reference_source().replace(
            '[0,7,9223372036854775807,-1,-19,(0-9223372036854775807-1)]','[7,-1]')
        self.owned_probe(text, 'u2-invoke-owned-reference.json')

    def owned_probe(self, text, evidence_name):
        started=time.monotonic()
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); (root/'compiler').symlink_to(ROOT/'src/compiler',target_is_directory=True)
            source=root/'probe.eri'; source.write_text(text,encoding='utf-8')
            frontend,generator=shared_u1_compilers()
            emitted=subprocess.run([str(frontend),'emit-asm',str(source),'--source-root',str(root)],capture_output=True,text=True,timeout=120)
            runtime=subprocess.run([str(generator)],capture_output=True,text=True,timeout=120)
            for result in (emitted,runtime): self.assertEqual((result.returncode,result.stderr),(0,''),result.stdout[-1200:])
            for name,code in (('app',emitted.stdout),('runtime',runtime.stdout)):
                assembly=root/(name+'.s'); assembly.write_text(code,encoding='utf-8')
                subprocess.run(['as','--64',str(assembly),'-o',str(root/(name+'.o'))],check=True,capture_output=True,timeout=60)
            binary=root/'owned'
            subprocess.run(['ld','-nostdlib','-static','-e','_start',str(root/'app.o'),str(root/'runtime.o'),'-o',str(binary)],check=True,capture_output=True,timeout=60)
            run=subprocess.run([str(binary)],capture_output=True,text=True,timeout=120)
            self.assertEqual((run.returncode,run.stdout,run.stderr),(0,'canonical-invoke-availability:ok\n',''))
            evidence=os.environ.get('ERISTAVI_U2_EVIDENCE_DIR')
            if evidence:
                destination=Path(evidence); destination.mkdir(parents=True,exist_ok=True)
                (destination/evidence_name).write_text(json.dumps({
                    'status':'pass','runtime':'owned Linux x86-64, opt-in closed adapter',
                    'seconds':time.monotonic()-started,'input_cases':[7,-1],'fuel_cases':[0,1,2,3],
                    'stdout':run.stdout,'stderr':run.stderr,'exit':run.returncode,
                    'fixture_sha256':hashlib.sha256(text.encode()).hexdigest(),
                    'app_assembly_sha256':hashlib.sha256(emitted.stdout.encode()).hexdigest(),
                    'runtime_assembly_sha256':hashlib.sha256(runtime.stdout.encode()).hexdigest(),
                    'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),
                    'cc':os.environ.get('CC','cc'),'cflags':os.environ.get('CFLAGS','')
                },indent=2)+'\n',encoding='utf-8')

    def test_canonical_invoke_and_outcome_only_payload_availability(self):
        self.compile_probe(SOURCE)

    def compile_probe(self,text):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); (root/'compiler').symlink_to(ROOT/'src/compiler',target_is_directory=True)
            source=root/'probe.eri'; source.write_text(text,encoding='utf-8'); binary=root/'probe'
            self.assertEqual(build_native(source,binary,root),0)
            run=subprocess.run([str(binary)],capture_output=True,text=True,timeout=120)
            self.assertEqual((run.returncode,run.stdout,run.stderr),(0,'canonical-invoke-availability:ok\n',''))


if __name__ == '__main__': unittest.main()
