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
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_events import BuildJournal, record_finally

def require_expected_failure(result, exit_code, diagnostic):
    if result.returncode!=exit_code or diagnostic not in result.stderr:
        raise RuntimeError(f'expected controlled rejection (exit {exit_code}, {diagnostic!r}); got {result.returncode}: {result.stderr}')

def verify(bundle, *, command_timeout=180):
    bundle=Path(bundle).resolve()
    if command_timeout<=0:raise ValueError('command timeout must be positive')
    journal=BuildJournal(bundle/'evidence'/'offline-audit',timeout=command_timeout)
    try:
        result=_verify(bundle,journal)
        journal.state.update(status='success',**result)
        return result
    except BaseException as error:
        status='timeout' if isinstance(error,subprocess.TimeoutExpired) else ('interrupted' if isinstance(error,KeyboardInterrupt) else 'failed')
        journal.state.update(status=status,error=str(error),error_type=type(error).__name__)
        raise
    finally:
        record_finally(journal.save)

def _verify(bundle,journal):
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
    while i < 100000 {
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
            return journal.run([compiler,*args],env=environment,cwd=root,check=False,echo_stdout=True)
        with journal.stage('check-application'):
            checked=invoke('check',source)
            if checked.returncode: raise RuntimeError(checked.stderr)
        with journal.stage('trace-application'):
            traced=invoke('check',source,'--trace-phases')
            if traced.returncode or traced.stdout:
                raise RuntimeError(f'offline traced check failed: {traced}')
            phases=[]
            for line in traced.stderr.split("\n"):
                if not line:continue
                if not line.startswith('[erist-phase] '):raise RuntimeError(f'unexpected trace diagnostic: {line}')
                phases.append(json.loads(line[len('[erist-phase] '):]))
            if not any(row.get('event')=='end' and row.get('phase')=='analyze-project' for row in phases):
                raise RuntimeError('offline trace did not finish semantic analysis')
        with journal.stage('build-application'):
            built=invoke('build',source,'-o',output)
            if built.returncode: raise RuntimeError(built.stderr)
        expected='6\n2\n42\noffline\nhandled\n'
        with journal.stage('execute-application'):
            run=journal.run([output],env=environment,timeout=min(30,journal.timeout),check=False)
            if (run.returncode,run.stdout,run.stderr)!=(0,expected,''):
                raise RuntimeError(f'offline program mismatch: {run}')
        before=hashlib.sha256(output.read_bytes()).hexdigest()
        invalid=project/'invalid.eri';invalid.write_text('output(missing);')
        print('[offline-audit] expected semantic rejection: invalid source',file=sys.stderr,flush=True)
        with journal.stage('expected-invalid-source'):
            failed=invoke('build',invalid,'-o',output)
            require_expected_failure(failed,1,'semantic error [')
            if hashlib.sha256(output.read_bytes()).hexdigest()!=before:
                raise RuntimeError('failed build replaced the previous executable')
        source_bytes=source.read_bytes()
        print('[offline-audit] expected usage rejection: source overwrite',file=sys.stderr,flush=True)
        with journal.stage('expected-source-overwrite'):
            protected=invoke('build',source,'-o',source)
            require_expected_failure(protected,2,'output must be a file distinct from the source')
            if source.read_bytes()!=source_bytes:
                raise RuntimeError('source overwrite was not prevented')
        if calls.exists(): raise RuntimeError('a forbidden bootstrap executable was invoked')
        evidence={'native_application':True,'python_or_c_compiler_invoked':False,'bundled_assembler_linker':True,
                  'unicode_paths':True,'source_preserved':True,'failed_build_preserves_output':True,
                  'heap_stress_iterations':100000,'compiler_phase_trace':True,
                  'expected_stdout':expected,'target':json.loads((bundle/'platform.json').read_text())['target']}
        (bundle/'offline-tests.json').write_text(json.dumps(evidence,indent=2)+'\n')
        print(json.dumps(evidence,indent=2))
        return evidence

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('bundle',type=Path);args=parser.parse_args();verify(args.bundle)
