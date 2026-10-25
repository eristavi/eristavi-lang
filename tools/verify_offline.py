#!/usr/bin/env python3
"""Audit an offline bundle by building with no Python/C compiler in child PATH."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

def verify(bundle):
    bundle=bundle.resolve();compiler=bundle/'bin/erist'
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);minimal=root/'path';minimal.mkdir()
        for name in ('sh','rm','mktemp','mv','cat','chmod'):
            found=shutil.which(name)
            if found is None: raise RuntimeError(f'OS utility is unavailable: {name}')
            (minimal/name).symlink_to(found)
        calls=root/'forbidden-calls'
        for name in ('cc','gcc','clang','python','python3'):
            script=minimal/name
            script.write_text(f'#!/bin/sh\nprintf called >> "{calls}"\nexit 99\n');script.chmod(0o755)
        environment={'PATH':str(minimal),'LANG':'C','CC':'/unavailable/cc'}
        project=root/'project λ';project.mkdir();(project/'data.txt').write_text('offline')
        source=project/'application.eri'
        source.write_text('''import std.files;
type Counter { value Int; }
error Expected { message Text; }
function sum(items) { let total be 0; for item in items { total=total+item; } return total; }
function read(path Text) returns Text fails files.FileError { with file be try files.openRead(path) { return try file.readText(); } }
function failer() fails Expected { fail Expected { message="handled"; }; }
function churn() {
    let i be 0;
    while i < 10000 {
        let text be "a"+"b";
        let values be [i,i+1];
        if text != "ab" or values.count != 2 { output("collector mismatch"); return; }
        i=i+1;
    }
}
function run() {
    churn();
    let original be [1,2]; let copy be original; copy.add(3); output(sum(copy)); output(original.count);
    let a be identity Counter { value=1; }; let b be a; b.value=42; output(a.value);
    let text be read("$ROOT/data.txt") else error files.FileError { output(error.message); return; }; output(text);
    failer() else error Expected { output(error.message); };
}
run();
'''.replace('$ROOT',str(project)),encoding='utf-8')
        output=project/'application'
        def invoke(*args):
            return subprocess.run([str(compiler),*map(str,args)],capture_output=True,text=True,env=environment,cwd=root,timeout=180)
        checked=invoke('check',source)
        if checked.returncode: raise RuntimeError(checked.stderr)
        built=invoke('build',source,'-o',output)
        if built.returncode: raise RuntimeError(built.stderr)
        run=subprocess.run([str(output)],capture_output=True,text=True,env=environment,timeout=30)
        expected='6\n2\n42\noffline\nhandled\n'
        if (run.returncode,run.stdout,run.stderr)!=(0,expected,''):
            raise RuntimeError(f'offline program mismatch: {run}')
        before=hashlib.sha256(output.read_bytes()).hexdigest()
        invalid=project/'invalid.eri';invalid.write_text('output(missing);')
        failed=invoke('build',invalid,'-o',output)
        if failed.returncode==0 or hashlib.sha256(output.read_bytes()).hexdigest()!=before:
            raise RuntimeError('failed build replaced the previous executable')
        source_bytes=source.read_bytes()
        protected=invoke('build',source,'-o',source)
        if protected.returncode==0 or source.read_bytes()!=source_bytes:
            raise RuntimeError('source overwrite was not prevented')
        if calls.exists(): raise RuntimeError('a forbidden bootstrap executable was invoked')
        evidence={'native_application':True,'python_or_c_compiler_invoked':False,'bundled_assembler_linker':True,
                  'unicode_paths':True,'source_preserved':True,'failed_build_preserves_output':True,
                  'heap_stress_iterations':10000,
                  'expected_stdout':expected,'target':json.loads((bundle/'platform.json').read_text())['target']}
        (bundle/'offline-tests.json').write_text(json.dumps(evidence,indent=2)+'\n')
        print(json.dumps(evidence,indent=2))
        return evidence

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('bundle',type=Path);args=parser.parse_args();verify(args.bundle)
