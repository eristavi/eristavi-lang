"""Private U2 exit planning vs an independent direct unwind-stack oracle."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import tempfile
import time
import unittest

from compiler.erist.cli import build_native

ROOT = Path(__file__).resolve().parents[1]
SOURCE = '''
import std.process;
import compiler.u1_budget as budget;
import compiler.u1_words as words;
import compiler.u1_meta as meta;
import compiler.u2_cleanup_plan as cleanup;
error ProbeError { message Text; }
function check(okay Bool,message Text) fails ProbeError {
    if not okay { fail ProbeError { message=message; }; }
}
function refused(data identity meta.Metadata,owner identity budget.Owner,phase identity budget.Phase,
    active,survive Int,exit meta.LocId) returns Text {
    let plan be cleanup.create(data,owner,phase,active,survive,exit,false)
        else error budget.LimitError { return error.category; };
    cleanup.close(plan) else error budget.LimitError { return "close-error"; };
    return "accepted";
}
function run() fails budget.LimitError,ProbeError {
    let root be try budget.developmentRequest(); let shared be try budget.metadataOwner(root);
    let metadataPhase be try budget.constructionPhase(shared); let data be try meta.create(shared,metadataPhase);
    let signature be try meta.signature(data,metadataPhase,[meta.i64()],[meta.i64()]);
    let source be try meta.source(data,metadataPhase,"u2.eri","0000000000000000000000000000000000000000000000000000000000000000",100);
    let close be try meta.location(data,metadataPhase,source,0,10,0,1,1);
    let exit be try meta.location(data,metadataPhase,source,20,30,20,2,1);
    try meta.freeze(data); try budget.finishPhase(metadataPhase);
    let depths be [0,2,8,32,128]; let chosen be 0;
    while chosen < depths.count {
        let depth be depths[chosen]; let active be []; let index be 0;
        while index < depth {
            active.add(cleanup.Scope { scope=index*3+1; contract=index+11; value=index+21; close=close; });
            index=index+1;
        }
        let owner be try budget.functionOwner(root,true); let phase be try budget.constructionPhase(owner);
        let prefixes be [0,depth/2,depth]; let prefix be 0;
        while prefix < prefixes.count {
            let survive be prefixes[prefix]; let mode be 0;
            while mode < 2 {
                let plan be try cleanup.create(data,owner,phase,active,survive,exit,mode == 1);
                output("plan"); output(depth); output(survive); output(mode); output(plan.entry);
                try check(plan.records.length == (depth-survive)*16 and plan.records.frozen,"bounded frozen plan");
                index=0;
                while index < plan.records.length {
                    output(try words.get(plan.records,phase,index)); index=index+1;
                }
                try cleanup.close(plan);
                try check(owner.live == 0 and owner.pending == 0,"plan backing reclaimed");
                mode=mode+1;
            }
            prefix=prefix+1;
        }
        if depth == 2 {
            let before be root.live; let bad be active; let damaged be bad[1];
            damaged.scope=bad[0].scope; bad[1]=damaged;
            try check(refused(data,owner,phase,bad,0,exit) == "invalid-state","duplicate owner scope");
            bad=active; damaged=bad[0]; damaged.value=0; bad[0]=damaged;
            try check(refused(data,owner,phase,bad,0,exit) == "invalid-state","zero owner value");
            try check(refused(data,owner,phase,active,3,exit) == "invalid-state","invalid surviving prefix");
            let foreign be meta.LocId { owner=identity meta.Key { marker=0; }; index=exit.index; };
            try check(refused(data,owner,phase,active,0,foreign) == "invalid-state","foreign exit origin");
            try check(root.live == before and owner.pending == 0,"invalid input does not publish storage");
            let limits be [0,1,2,8,32,128]; let trial be 0;
            while trial < limits.count {
                let attempt be try budget.functionOwner(root,true); let narrow be try budget.phase(attempt,limits[trial]);
                let traffic be root.traffic;
                try check(refused(data,attempt,narrow,active,0,exit) == "resource-limit","work exhaustion");
                try check(attempt.live == 0 and attempt.pending == 0 and root.live == before and root.traffic >= traffic,"failed plan cleanup/monotonic traffic");
                try budget.finishPhase(narrow); try budget.close(attempt); trial=trial+1;
            }
            let cancelled be try budget.functionOwner(root,true); let cancellation be try budget.constructionPhase(cancelled);
            budget.cancel(cancelled);
            try check(refused(data,cancelled,cancellation,active,0,exit) == "cancelled" and cancelled.live == 0,"cancelled plan");
            try budget.finishPhase(cancellation); try budget.close(cancelled);
            let tiny be try budget.child(root,2,8388608,0,268435456);
            let tinyPhase be try budget.constructionPhase(tiny);
            try check(refused(data,tiny,tinyPhase,active,0,exit) == "resource-limit" and tiny.live == 0 and tiny.pending == 0,"traffic refusal cleanup");
            try budget.finishPhase(tinyPhase); try budget.close(tiny);
            let ended be try budget.constructionPhase(owner); try budget.finishPhase(ended);
            try check(refused(data,owner,ended,active,2,exit) == "invalid-state","finished phase cannot build even an empty exit");
        }
        if depth == 128 {
            let tooDeep be active;
            tooDeep.add(cleanup.Scope { scope=1000; contract=1; value=1; close=close; });
            let attempt be try budget.functionOwner(root,true); let narrow be try budget.constructionPhase(attempt);
            try check(refused(data,attempt,narrow,tooDeep,0,exit) == "resource-limit" and attempt.live == 0,"predeclared depth limit");
            try budget.finishPhase(narrow); try budget.close(attempt);
        }
        output("owner"); output(depth); output(owner.peak); output(owner.traffic);
        try budget.finishPhase(phase); try budget.close(owner); chosen=chosen+1;
    }
    try meta.close(data); try budget.close(shared);
    try check(root.live == 0 and root.pending == 0,"complete request cleanup"); try budget.close(root);
    output("contracts:ok");
}
function main() {
    run()
    else error budget.LimitError { output("limit:"+error.category+":"+error.message); process.setExitCode(1); return; }
    else error ProbeError { output("probe:"+error.message); process.setExitCode(1); return; };
}
main();
'''


def walk(records, entry, failed, failure_mask):
    primary = 'body' if failed else None
    secondary, closed = [], []
    cursor = entry
    while cursor > 0:
        if len(closed) > len(records):
            raise AssertionError('cyclic cleanup plan')
        scope, contract, value, close, exit, mode, normal, error = records[cursor - 1]
        index = (scope - 1) // 3
        if mode != int(primary is not None) or (contract, value, close, exit) != (index + 11, index + 21, 1, 2):
            raise AssertionError('wrong failure mode, owner or provenance')
        if index in closed:
            raise AssertionError('owner closed twice')
        closed.append(index)
        failure = bool(failure_mask & (1 << index))
        if failure:
            if primary is None: primary = f'close-{index}'
            else: secondary.append(f'close-{index}')
        cursor = error if failure else normal
    if cursor != (-1 if primary else 0):
        raise AssertionError('wrong final continuation')
    return closed, primary, secondary


class U2CleanupPlanTests(unittest.TestCase):
    def test_actual_planner_matches_independent_unwind_and_refusal_oracles(self):
        started = time.perf_counter()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'compiler').symlink_to(ROOT / 'src/compiler', target_is_directory=True)
            source = root / 'probe.eri'
            source.write_text(SOURCE, encoding='utf-8')
            binary = root / 'probe'
            self.assertEqual(build_native(source, binary, root), 0)
            run = subprocess.run([str(binary)], capture_output=True, text=True, timeout=120)
            self.assertEqual((run.returncode, run.stderr), (0, ''), run.stdout[-1000:])
            lines = iter(run.stdout.splitlines())
            count, plans, owner_metrics, negative_controls = 0, 0, [], 0
            for line in lines:
                if line == 'contracts:ok': break
                if line == 'owner':
                    depth, peak, traffic = (int(next(lines)) for _ in range(3))
                    self.assertLessEqual(peak, 8388608)
                    self.assertLessEqual(traffic, 67108864)
                    owner_metrics.append({'depth': depth, 'modeled_peak': peak, 'modeled_traffic': traffic})
                    continue
                self.assertEqual(line, 'plan')
                depth, survive, failed, entry = (int(next(lines)) for _ in range(4))
                records = [tuple(int(next(lines)) for _ in range(8)) for _ in range(2 * (depth - survive))]
                plans += 1
                masks = range(1 << depth) if depth <= 8 else (0, (1 << depth) - 1, sum(1 << i for i in range(0, depth, 2)))
                for mask in masks:
                    closes = list(reversed(range(survive, depth)))
                    failures = [f'close-{i}' for i in closes if mask & (1 << i)]
                    primary = 'body' if failed else (failures.pop(0) if failures else None)
                    self.assertEqual(walk(records, entry, failed, mask), (closes, primary, failures))
                    count += 1
                if depth == 2 and survive == 0 and failed == 0:
                    # A failed close must consume the owner before its error
                    # edge. This deliberately broken private plan retries it.
                    broken = list(records)
                    broken[0] = (*broken[0][:7], 1)
                    with self.assertRaises(AssertionError):
                        walk(broken, entry, failed, 3)
                    negative_controls += 1
            else: self.fail('missing lifecycle/refusal completion marker')
            self.assertEqual(list(lines), [])
            self.assertGreater(count, 1500)
            self.assertEqual(negative_controls, 1)
            evidence_dir = os.environ.get('ERISTAVI_U2_EVIDENCE_DIR')
            if evidence_dir:
                evidence = Path(evidence_dir)
                evidence.mkdir(parents=True, exist_ok=True)
                (evidence / 'u2-cleanup-planner.json').write_text(json.dumps({
                    'status': 'pass', 'profile': 'private exit planner; not canonical U2',
                    'plans': plans, 'independent_paths': count, 'negative_controls': negative_controls,
                    'seconds': time.perf_counter() - started, 'owners': owner_metrics,
                    'cc': os.environ.get('CC', 'cc'), 'cflags': os.environ.get('CFLAGS', ''),
                    'module_sha256': hashlib.sha256((ROOT / 'src/compiler/u2_cleanup_plan.eri').read_bytes()).hexdigest(),
                    'fixture_sha256': hashlib.sha256(SOURCE.encode()).hexdigest(),
                    'memory_scope': 'budget-ledger admission, not allocator capacity or RSS'
                }, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__': unittest.main()
