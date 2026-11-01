"""Opt-in three-scale aggregate owner-memory evidence; no routine CI cost."""
import argparse
import contextlib
import io
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
import test_u1b_actual_physical as probe


def measure(width,depth):
    fixture=(ROOT/'tests/fixtures/u1b_aggregate_physical.eri').read_text()
    fixture=fixture.replace('    try aggregate.freeze(graph);',f'''
    let fields be [];
    let ordinal be 0;
    while ordinal < {width} {{ fields.add(i64); ordinal=ordinal+1; }}
    let wide be try aggregate.aggregate(graph,mp,fields);
    let shapes be [];
    let deep be pair;
    ordinal=0;
    while ordinal < {depth} {{
        deep=try aggregate.aggregate(graph,mp,[deep,i64]);
        shapes.add(deep); ordinal=ordinal+1;
    }}
    try aggregate.freeze(graph);''')
    fixture=fixture.replace('    process.setExitCode(0);\n    let graphBacking',f'''
    let components be [];
    let index be 0;
    while index < {width} {{ components.add(left); index=index+1; }}
    let wideOld be try values.make(engine,wide,components);
    let wideNew be try values.set(engine,wideOld,{width-1},right);
    try check((try values.bits(engine,try values.get(engine,wideOld,{width-1}))) == 11
        and (try values.bits(engine,try values.get(engine,wideNew,{width-1}))) == 17,
        "wide immutable snapshots");
    let deepValue be old;
    for shape in shapes {{ deepValue=try values.make(engine,shape,[deepValue,left]); }}
    index=0;
    while index < {depth} {{ deepValue=try values.get(engine,deepValue,0); index=index+1; }}
    try check((try values.bits(engine,try values.get(engine,deepValue,1))) == 11,
        "deep immutable projection");
    process.setExitCode(0);
    let graphBacking''')
    with tempfile.TemporaryDirectory() as d:
        root=Path(d)
        (root/'src').mkdir(); (root/'src/compiler').symlink_to(ROOT/'src/compiler',target_is_directory=True)
        (root/'tests/fixtures').mkdir(parents=True)
        (root/'tests/fixtures/u1b_aggregate_physical.eri').write_text(fixture)
        previous=probe.ROOT
        probe.ROOT=root
        output=io.StringIO(); started=time.monotonic()
        try:
            suite=unittest.defaultTestLoader.loadTestsFromTestCase(probe.U1BAggregatePhysicalTests)
            with contextlib.redirect_stdout(output):
                result=unittest.TextTestRunner(stream=sys.stderr,verbosity=1).run(suite)
        finally:
            probe.ROOT=previous
        if not result.wasSuccessful() or result.skipped:
            raise RuntimeError(f'incomplete physical scale width={width} depth={depth}')
        records=[line.split('=',1)[1] for line in output.getvalue().splitlines() if line.startswith('U1B_OWNER_PHYSICAL=')]
        if len(records)!=1: raise AssertionError('missing physical measurement')
        data=json.loads(records[0])
        for peak,traffic in data['owner_request_peak_traffic'].values():
            if peak>8388608 or traffic>67108864: raise AssertionError('original owner gates exceeded')
        return {'width':width,'depth':depth,'probe_wall_seconds':time.monotonic()-started,'evidence':data}

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--output',required=True)
    parser.add_argument('--independent',action='store_true',
                        help='vary width at fixed depth, then depth at fixed width')
    args=parser.parse_args()
    scales=((8,2),(32,2),(128,2),(8,8),(8,32)) if args.independent else ((8,2),(32,8),(128,32))
    samples=[measure(w,d) for w,d in scales]
    Path(args.output).write_text(json.dumps({'scope':'Actual tagged aggregate graph/value engine backing, forced identity hash collisions; no linked whole-program or RSS attribution, no paired speedup claim',
        'dimensions':'width 8/32/128 at depth 2; depth 2/8/32 at width 8' if args.independent else 'width and depth increase jointly',
        'words_sha256':hashlib.sha256((ROOT/'src/compiler/u1_words.eri').read_bytes()).hexdigest(),
        'samples':samples},indent=2)+'\n')
