"""Canonical checked-edge root metadata: exact all-invoke coverage and mutations."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from compiler.erist.cli import build_native

ROOT = Path(__file__).resolve().parents[1]

class U2RootMapTests(unittest.TestCase):
    def test_all_canonical_invoke_failure_roots_and_refusals(self):
        source = (ROOT / "tests/fixtures/u2_scoped_owners.eri").read_text()
        source = source.replace(
            'import compiler.u2_scoped_owners as owners;',
            'import compiler.u2_scoped_owners as owners;\n'
            'import compiler.u2_root_map as nativeRoots;')
        helper = (
            'function rootMapRejected(value identity nativeRoots.Map,'
            'fn identity build.Function,graph identity aggregate.Registry,'
            'phase identity budget.Phase)'
            ' returns Bool fails budget.LimitError {\n'
            '    let report be nativeRoots.verify(value,fn,graph,phase)\n'
            '    else error nativeRoots.InvalidRoots { return true; }\n'
            '    else error budget.LimitError { fail error; };\n'
            '    return false;\n'
            '}\n'
        )
        self.assertIn("function run() fails", source)
        source = source.replace("function run() fails", helper+"function run() fails",1)
        # Dead canonical instructions must be covered by the independent map.
        updates = (
            (
                'let dead be try build.block(fn,[]); let deadTarget be try build.block(fn,[meta.i64()]);',
                'let dead be try build.block(fn,[]); let deadTarget be try build.block(fn,[meta.i64()]);\n'
                '    let deadInvoke be try build.block(fn,[]);'
            ),
            (
                'try owners.block(profile,fn,phase,deadTarget,[]);',
                'try owners.block(profile,fn,phase,deadTarget,[]);\n'
                '    try owners.block(profile,fn,phase,deadInvoke,[]);'
            ),
            (
                'let pendingClose be try transfer.emit(fn,graph,consume,pair,[pendingOwner],[pendingError]);',
                'let pendingClose be try transfer.emit(fn,graph,consume,pair,[pendingOwner],[pendingError]);\n'
                '    let deadPair be try continuation.bind(fn,graph,phase,deadInvoke,outer,failed,acquireSig,failedSig,loc);\n'
                '    let deadChecked be try invoke.emit(fn,graph,acquire,deadPair,[]);'
            ),
        )
        for before, after in updates:
            self.assertIn(before,source)
            source=source.replace(before,after,1)
        source=source.replace('report.blocks == 11 and','report.blocks == 12 and')
        anchor='let mutate be try budget.constructionPhase(owner); let revision be fn.revision;'
        self.assertIn(anchor,source)
        injected = (
            anchor+'\n'
            '    let map be try nativeRoots.create(fn,graph,mutate);\n'
            '    let roots be try nativeRoots.verify(map,fn,graph,mutate);\n'
            '    try check(roots.invokes == 6 and roots.roots == 6 and '
            'roots.revision == revision,"incomplete canonical checked-root coverage");\n'
            '    let field be 0; while field < 6 {\n'
            '        let saved be try words.get(map.records,mutate,field);\n'
            '        map.records.frozen=false; try words.set(map.records,mutate,field,saved+1); '
            'map.records.frozen=true;\n'
            '        try check(try rootMapRejected(map,fn,graph,mutate),'
            '"corrupt canonical root-map field accepted");\n'
            '        map.records.frozen=false; try words.set(map.records,mutate,field,saved); '
            'map.records.frozen=true;\n'
            '        field=field+1;\n'
            '    }\n'
            '    let retainedLength be map.records.length; map.records.length=retainedLength-6;\n'
            '    try check(try rootMapRejected(map,fn,graph,mutate),'
            '"missing checked root accepted");\n'
            '    map.records.length=retainedLength;\n'
            '    map.revision=revision+1;\n'
            '    try check(try rootMapRejected(map,fn,graph,mutate),'
            '"stale root map accepted");\n'
            '    map.revision=revision;\n'
            '    let restoredRoots be try nativeRoots.verify(map,fn,graph,mutate);\n'
            '    try check(restoredRoots.roots == 6,"restored map rejected");\n'
            '    try nativeRoots.close(map);'
        )
        source=source.replace(anchor,injected,1)
        source=source.replace(
            'continuation.InvalidBinding,owners.InvalidOwnership,ProbeError {',
            'continuation.InvalidBinding,owners.InvalidOwnership,nativeRoots.InvalidRoots,ProbeError {')
        source=source.replace(
            'else error ProbeError { output("probe:"+error.message);',
            'else error nativeRoots.InvalidRoots { output("roots:"+error.message); process.setExitCode(1); }\n'
            'else error ProbeError { output("probe:"+error.message);')
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary)
            (directory/"compiler").symlink_to(ROOT/"src/compiler",target_is_directory=True)
            file=directory/"roots.eri"
            file.write_text(source,encoding="utf-8")
            binary=directory/"roots"
            self.assertEqual(build_native(file,binary,directory),0)
            run=subprocess.run([str(binary)],capture_output=True,text=True,timeout=120)
            self.assertEqual((run.returncode,run.stdout,run.stderr),
                             (0,"u2-scoped-owners:ok\n",""))
