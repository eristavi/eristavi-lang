"""Actual independent Eristavi ingress verifier, including unreachable rows."""
from pathlib import Path
import subprocess
import tempfile
import unittest

from compiler.erist.cli import build_native
from test_u2_cleanup_plan import SOURCE

ROOT = Path(__file__).resolve().parents[1]
IMPORT = 'import compiler.u2_cleanup_verify as verify;'
HELPER = '''
function prepareRefused(data identity meta.Metadata,owner identity budget.Owner,
    phase identity budget.Phase,active,exit meta.LocId) returns Text {
    let plan be verify.prepare(data,owner,phase,active,0,exit,false)
        else error verify.InvalidPlan { return "invalid-plan"; }
        else error budget.LimitError { return error.category; };
    cleanup.close(plan) else error budget.LimitError { return "close-error"; };
    return "accepted";
}
function rejected(data identity meta.Metadata,phase identity budget.Phase,
    plan identity cleanup.Plan,active,survive Int,exit meta.LocId,failed Bool)
    returns Bool fails budget.LimitError {
    let okay be verify.verify(data,phase,plan,active,survive,exit,failed)
        else error verify.InvalidPlan { return true; }
        else error budget.LimitError { fail error; };
    return false;
}
'''
CHECKS = '''
                let live be root.live; let traffic be root.traffic;
                try check(try verify.verify(data,phase,plan,active,survive,exit,mode == 1),"fresh independent verification");
                try check(root.live == live and root.traffic == traffic,"verifier allocates no owned storage");
                let oldEntry be plan.entry; plan.entry=999999;
                try check(try rejected(data,phase,plan,active,survive,exit,mode == 1),"forged entry accepted");
                plan.entry=oldEntry;
                let oldDepth be plan.depth; plan.depth=999999;
                try check(try rejected(data,phase,plan,active,survive,exit,mode == 1),"forged dimensions accepted");
                plan.depth=oldDepth;
                plan.records.frozen=false;
                try check(try rejected(data,phase,plan,active,survive,exit,mode == 1),"mutable record store accepted");
                plan.records.frozen=true;
                let originalOwner be plan.records.owner; plan.records.owner=shared;
                try check(try rejected(data,phase,plan,active,survive,exit,mode == 1),"foreign record owner accepted");
                plan.records.owner=originalOwner;
                plan.closed=true;
                try check(try rejected(data,phase,plan,active,survive,exit,mode == 1),"closed plan accepted");
                plan.closed=false;
                let originalState be phase.state; phase.state=1;
                try check(try rejected(data,phase,plan,active,survive,exit,mode == 1),"finished verification phase accepted");
                phase.state=originalState;
                // Every field of every record, including normal-mode records
                // unreachable from already-failed entry, is independently checked.
                let cell be 0;
                while cell < plan.records.length {
                    let saved be try words.get(plan.records,phase,cell);
                    plan.records.frozen=false;
                    try words.set(plan.records,phase,cell,999999);
                    plan.records.frozen=true;
                    try check(try rejected(data,phase,plan,active,survive,exit,mode == 1),"same-revision frozen record mutation accepted");
                    plan.records.frozen=false;
                    try words.set(plan.records,phase,cell,saved);
                    plan.records.frozen=true;
                    cell=cell+1;
                }
                try check(try verify.verify(data,phase,plan,active,survive,exit,mode == 1),"restored plan rejected");
'''


class U2CleanupVerifierTests(unittest.TestCase):
    def test_independent_verifier_rejects_mutated_frozen_and_unreachable_plans(self):
        # Keep full depth-128 positive coverage; mutation matrix uses depth 2/8
        # to avoid recurring native test cost proportional to thousands of plans.
        text = SOURCE.replace('error ProbeError', IMPORT + '\nerror ProbeError', 1)
        text = text.replace('function run()', HELPER + '\nfunction run()', 1)
        text = text.replace('let plan be try cleanup.create(data,owner,phase,active,survive,exit,mode == 1);',
                            'let plan be try verify.prepare(data,owner,phase,active,survive,exit,mode == 1);', 1)
        checks = CHECKS.replace('let cell be 0;', 'let cell be plan.records.length; if depth <= 8 { cell=0; }')
        text = text.replace('                output("plan");', checks + '\n                output("plan");', 1)
        text = text.replace('        if depth == 128 {', '''
        if depth == 2 {
            let meter be try budget.functionOwner(root,true); let measuring be try budget.constructionPhase(meter);
            let sample be try cleanup.create(data,meter,measuring,active,0,exit,false);
            let constructionCost be measuring.used; try cleanup.close(sample);
            try budget.finishPhase(measuring); try budget.close(meter);
            let baseline be root.live; let trafficBefore be root.traffic;
            let attempt be try budget.functionOwner(root,true); let exact be try budget.phase(attempt,constructionCost);
            try check(prepareRefused(data,attempt,exact,active,exit) == "resource-limit","verification-only exhaustion not refused");
            try check(exact.used == constructionCost and attempt.live == 0 and attempt.pending == 0 and root.live == baseline and root.traffic >= trafficBefore,"prepare leaked after verification exhaustion");
            try budget.finishPhase(exact); try budget.close(attempt);
        }
        if depth == 128 {''', 1)
        text = text.replace('fails budget.LimitError,ProbeError {\n    let root',
                            'fails budget.LimitError,ProbeError,verify.InvalidPlan {\n    let root', 1)
        text = text.replace('else error ProbeError {',
                            'else error verify.InvalidPlan { output("invalid:"+error.message); process.setExitCode(1); return; }\n    else error ProbeError {', 1)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'compiler').symlink_to(ROOT / 'src/compiler', target_is_directory=True)
            source, binary = root / 'probe.eri', root / 'probe'
            source.write_text(text, encoding='utf-8')
            self.assertEqual(build_native(source, binary, root), 0)
            run = subprocess.run([str(binary)], capture_output=True, text=True, timeout=120)
            self.assertEqual((run.returncode, run.stderr), (0, ''), run.stdout[-1200:])
            self.assertTrue(run.stdout.endswith('contracts:ok\n'), run.stdout[-1000:])


if __name__ == '__main__': unittest.main()
