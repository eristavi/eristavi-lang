#!/usr/bin/env python3
"""Build a host-specific experimental offline x86-64/Linux Eristavi toolchain.

Python/C are bootstrap build dependencies only. The resulting toolchain emits
native assembly and invokes its packaged assembler/linker, without Python or a
C compiler during normal application builds. No system installation is modified.
"""
from __future__ import annotations
import argparse
from contextvars import ContextVar
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_events import BuildJournal, write_json, record_finally
from verify_offline import verify as verify_offline

_ACTIVE_JOURNAL=ContextVar('erist_build_journal',default=None)
OFFLINE_HEAP_GC_INTERVAL=65536
RUNTIME_FLAGS=['-std=c11','-O2','-DERIST_NATIVE_RUNTIME',f'-DERIST_HEAP_GC_INTERVAL={OFFLINE_HEAP_GC_INTERVAL}']

def run(args,**kwargs):
    journal=_ACTIVE_JOURNAL.get()
    return (journal if journal is not None else BuildJournal()).run(args,**kwargs)

def emit_assembly(compiler,source,source_root,target,output,trace_phases=False):
    args=[compiler,'emit-asm',source,'--source-root',source_root,'--target',target]
    if trace_phases:
        help_result=run([compiler,'--help'],check=False)
        if help_result.returncode==0 and '--trace-phases' in help_result.stdout:
            args.append('--trace-phases')
        else:
            print(f'[build] seed {compiler} lacks phase tracing; build-stage logs remain enabled',flush=True)
    partial=output.with_suffix('.partial.s')
    run(args,stdout_path=partial,cwd=ROOT)
    shutil.copyfile(partial,output)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def compiler_file(cc,name):
    result=Path(run([*cc,'-print-file-name='+name]).stdout.strip())
    if not result.is_file():
        raise RuntimeError(f'bootstrap compiler cannot locate {name}: {result}')
    return result.resolve()

def copy_file(source,destination,inventory):
    destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,destination)
    inventory.append({'file':str(destination),'source':str(source),'sha256':digest(destination)})

def dependencies(binary):
    text=run(['ldd',binary]).stdout
    return {Path(name).resolve() for name in re.findall(r'(?:=>\s*)?(/[^\s]+)',text) if Path(name).is_file()}

def link(bundle,assembly,output,runtime):
    environment={**os.environ,'LD_LIBRARY_PATH':str(bundle/'tool-libs')}
    metadata=json.loads((bundle/'platform.json').read_text())
    assembler_flags=['--64'] if metadata['target']=='x86_64-linux' else []
    libraries=bundle/'lib'
    # GNU ld can synthesize a FILE symbol from the input object's basename.
    # Keep that name stable across B/C and caller-selected executable names.
    with tempfile.TemporaryDirectory() as td:
        obj=Path(td)/'program.o'
        run([bundle/'bin/as',*assembler_flags,assembly,'-o',obj],env=environment,echo_stdout=True)
        if metadata.get('runtime')=='owned':
            run([bundle/'bin/ld','-nostdlib','-static','-e','_start','-o',output,obj,runtime],env=environment,echo_stdout=True)
            audit_owned(output)
            return
        run([bundle/'bin/ld','-o',output,'-dynamic-linker',metadata['loader'],
             libraries/'crt1.o',libraries/'crti.o',libraries/'crtbegin.o',obj,runtime,
             libraries/'libm.so.6',libraries/'libc.so.6',libraries/'crtend.o',libraries/'crtn.o'],env=environment,echo_stdout=True)

def audit_owned(binary):
    headers=run(['readelf','-lW',binary]).stdout
    if 'INTERP' in headers or 'DYNAMIC' in headers:
        raise RuntimeError('owned executable unexpectedly requires a dynamic runtime')
    stack=next((line for line in headers.splitlines() if 'GNU_STACK' in line),'')
    if not stack or 'RWE' in stack or run(['nm','-u',binary]).stdout.strip():
        raise RuntimeError('owned executable has imports or an executable/missing stack declaration')

def build_owned_runtime(bootstrap,destination,trace_phases=False):
    """Bootstrap the Eristavi emitter once; the emitted runtime has no C imports."""
    destination.mkdir(parents=True,exist_ok=True)
    assembly=destination/'owned-runtime.s'
    generator_assembly=destination/'runtime-generator.s'
    generator=destination/'runtime-generator'
    cc=shlex.split(os.environ.get('CC','cc'))
    emit_assembly(bootstrap,ROOT/'src/owned_runtime.eri',ROOT/'src','x86_64-linux',generator_assembly,trace_phases)
    # The emitter is the final bootstrap program here; it uses the qualified C
    # runtime. Neither the resulting owned object nor its executables link it.
    run([*cc,*RUNTIME_FLAGS,generator_assembly,ROOT/'runtime/native_gc_runtime.c','-lm','-o',generator],echo_stdout=True)
    partial=assembly.with_suffix('.partial.s')
    run([generator],cwd=ROOT,stdout_path=partial)
    shutil.copyfile(partial,assembly)
    obj=destination/'erist-runtime.o'
    run(['as','--64',assembly,'-o',obj],echo_stdout=True)
    return obj

WRAPPER=r'''#!/bin/sh
set -eu
bundle=$(CDPATH= cd -- "${0%/*}/.." && pwd -P)
original=$(pwd -P)
if [ "$#" = 0 ] || [ "${1:-}" = --help ]; then
    printf '%s\n' 'Usage: erist build SOURCE.eri -o PROGRAM [--source-root DIRECTORY] [--trace-phases]' '       erist check|ir|uir|build-asm|build-c SOURCE.eri [-o FILE] [--source-root DIRECTORY]' 'Experimental x86-64/ARM64 Linux native toolchain; --trace-phases writes progress to stderr.'
    exit 0
fi
command=$1; shift
if [ "$command" = version ]; then
    printf '%s\n' 'Eristavi experimental offline Linux toolchain'
    exit 0
fi
if [ "$#" = 0 ]; then printf '%s\n' 'erist: missing source file' >&2; exit 2; fi
source=$1; shift
case "$source" in /*) ;; *) source=$original/$source;; esac
root=${source%/*}
trace=
output=
while [ "$#" -gt 0 ]; do
    case "$1" in
        -o|--output) [ "$#" -ge 2 ] || exit 2; output=$2; shift 2;;
        --source-root) [ "$#" -ge 2 ] || exit 2; root=$2; shift 2;;
        --trace-phases) [ -z "$trace" ] || exit 2; trace=--trace-phases; shift;;
        *) printf '%s\n' "erist: unknown argument $1" >&2; exit 2;;
    esac
done
case "$root" in /*) ;; *) root=$original/$root;; esac
if [ -n "$output" ]; then case "$output" in /*) ;; *) output=$original/$output;; esac; fi
if [ -n "$output" ] && { [ -d "$output" ] || [ "$source" -ef "$output" ]; }; then
    printf '%s\n' 'erist: output must be a file distinct from the source' >&2
    exit 2
fi
cd "$bundle"
compiler=$bundle/bin/erist-compiler
set --
if [ -n "$trace" ]; then set -- "$trace"; fi
case "$command" in
    check) exec "$compiler" analyze "$source" --source-root "$root" "$@";;
    ir|uir) if [ -z "$output" ]; then exec "$compiler" "$command" "$source" --source-root "$root" "$@"; fi; mode=$command;;
    build-asm) mode=emit-asm;;
    build-c) mode=emit-c;;
    build) mode=emit-asm;;
    *) printf '%s\n' "erist: unknown command $command" >&2; exit 2;;
esac
if [ -z "$output" ]; then printf '%s\n' 'erist: -o FILE is required for this command' >&2; exit 2; fi
temporary=$(mktemp -d "${TMPDIR:-/tmp}/erist.XXXXXXXX")
trap 'rm -rf -- "$temporary"' EXIT HUP INT TERM
if [ "$mode" = emit-asm ]; then
    target=$(cat "$bundle/target")
    "$compiler" "$mode" "$source" --source-root "$root" --target "$target" "$@" > "$temporary/program.s"
else
    "$compiler" "$mode" "$source" --source-root "$root" "$@" > "$temporary/program.s"
fi
if [ "$command" != build ]; then mv -f -- "$temporary/program.s" "$output"; exit 0; fi
if [ "$target" = x86_64-linux ]; then
    LD_LIBRARY_PATH=$bundle/tool-libs "$bundle/bin/as" --64 "$temporary/program.s" -o "$temporary/program.o"
else
    LD_LIBRARY_PATH=$bundle/tool-libs "$bundle/bin/as" "$temporary/program.s" -o "$temporary/program.o"
fi
if [ "$(cat "$bundle/runtime-profile")" = owned ]; then
    LD_LIBRARY_PATH=$bundle/tool-libs "$bundle/bin/ld" -nostdlib -static -e _start \
        -o "$temporary/program" "$temporary/program.o" "$bundle/lib/erist-runtime.o"
else
loader=$(cat "$bundle/loader-path")
LD_LIBRARY_PATH=$bundle/tool-libs "$bundle/bin/ld" -o "$temporary/program" -dynamic-linker "$loader" \
    "$bundle/lib/crt1.o" "$bundle/lib/crti.o" "$bundle/lib/crtbegin.o" \
    "$temporary/program.o" "$bundle/lib/erist-runtime.o" "$bundle/lib/libm.so.6" "$bundle/lib/libc.so.6" \
    "$bundle/lib/crtend.o" "$bundle/lib/crtn.o"
fi
mv -f -- "$temporary/program" "$output"
chmod +x "$output"
'''

def source_hashes():
    paths=set()
    for folder,patterns in [('src',('*.eri',)),('compiler',('*.py',)),('tools',('*.py',)),
                            ('runtime',('*.c','*.h')),('.github/workflows',('*.yml',))]:
        for pattern in patterns:paths.update((ROOT/folder).rglob(pattern))
    paths.update(ROOT/name for name in ('pyproject.toml','LICENSE','DESIGN_PHILOSOPHY.md','LANGUAGE_SEMANTICS.md','FLOAT.md'))
    return {str(path.relative_to(ROOT)):digest(path) for path in sorted(paths)}

def build(destination,compiler=None,self_build=True,runtime_profile='bootstrap',*,trace_phases=False,command_timeout=900):
    destination=Path(destination).resolve()
    if command_timeout<=0:raise ValueError('command timeout must be positive')
    if destination.exists():raise RuntimeError(f'choose a new output directory: {destination}')
    destination.mkdir(parents=True)
    evidence=destination/'evidence'
    journal=BuildJournal(evidence,timeout=command_timeout)
    journal.state.update(runtime=runtime_profile,self_build_requested=self_build,trace_phases=trace_phases,
                         command_timeout_seconds=command_timeout,compiler_C_completed=False,compiler_D_completed=False)
    token=_ACTIVE_JOURNAL.set(journal)
    snapshot=None
    try:
        snapshot=source_hashes()
        write_json(destination/'source-manifest.json',snapshot)
        commit=run(['git','rev-parse','HEAD'],cwd=ROOT,check=False,timeout=10) if shutil.which('git') else None
        journal.state['source_commit']=commit.stdout.strip() if commit is not None and commit.returncode==0 else None
        journal.state['ci_run']={key:os.environ.get(key) for key in ('GITHUB_SHA','GITHUB_RUN_ID','GITHUB_RUN_ATTEMPT')}
        journal.save()
        result=_build(destination,compiler,self_build,runtime_profile,trace_phases,journal,snapshot)
        if source_hashes()!=snapshot:raise RuntimeError('build inputs changed during qualification')
        journal.state.update(status='success',repeatable=json.loads((destination/'self-build.json').read_text())['repeatable'],
                             offline_audit_completed=True)
        return result
    except BaseException as error:
        status='timeout' if isinstance(error,subprocess.TimeoutExpired) else ('interrupted' if isinstance(error,KeyboardInterrupt) else 'failed')
        journal.state.update(status=status,error=str(error),error_type=type(error).__name__)
        raise
    finally:
        _ACTIVE_JOURNAL.reset(token)
        def finish():
            if snapshot is not None:
                try:journal.state['source_snapshot_unchanged']=source_hashes()==snapshot
                except OSError:journal.state['source_snapshot_unchanged']=False
            journal.save()
            summary={key:journal.state.get(key) for key in ('status','stage','repeatable','compiler_C_completed','compiler_D_completed','offline_audit_completed','source_snapshot_unchanged')}
            print('[build] qualification '+json.dumps(summary),flush=True)
            summary_path=os.environ.get('GITHUB_STEP_SUMMARY')
            if summary_path:
                try:
                    with open(summary_path,'a',encoding='utf-8') as stream:
                        stream.write('## Eristavi qualification\n\n')
                        stream.write('\n'.join('    '+line for line in json.dumps(summary,indent=2).splitlines())+'\n')
                except OSError as error:
                    print(f'[build] warning: could not write GitHub summary: {error}',file=sys.stderr,flush=True)
        record_finally(finish)

def _build(destination,compiler,self_build,runtime_profile,trace_phases,journal,snapshot):
    if platform.system()!='Linux' or platform.machine().lower() not in ('x86_64','amd64','aarch64','arm64'):
        raise RuntimeError('offline native packaging currently supports x86-64/ARM64 Linux only')
    target='x86_64-linux' if platform.machine().lower() in ('x86_64','amd64') else 'arm64-linux'
    if runtime_profile not in ('bootstrap','owned'):raise RuntimeError(f'unknown runtime profile: {runtime_profile}')
    if runtime_profile=='owned' and target!='x86_64-linux':raise RuntimeError('the owned runtime currently supports Linux x86-64 only')
    inventory=[]
    cc=shlex.split(os.environ.get('CC','cc'))
    with journal.stage('package-tools'):
        for name in ('as','ld'):
            found=shutil.which(name)
            if found is None:raise RuntimeError(f'bootstrap requires {name}')
            path=Path(found).resolve()
            copy_file(path,destination/'bin'/name,inventory)
            for library in sorted(dependencies(path)):
                cached_library=destination/'tool-libs'/library.name
                if not cached_library.exists():copy_file(library,cached_library,inventory)
        loader=None
        if runtime_profile=='bootstrap':
            for name in ('crt1.o','crti.o','crtbegin.o','crtend.o','crtn.o','libm.so.6','libc.so.6'):
                copy_file(compiler_file(cc,name),destination/'lib'/name,inventory)
            loader=compiler_file(cc,'ld-linux-x86-64.so.2' if target=='x86_64-linux' else 'ld-linux-aarch64.so.1')
            (destination/'loader-path').write_text(str(loader)+'\n')
        write_json(destination/'platform.json',{'target':target,'runtime':runtime_profile,'loader':str(loader) if loader else None,'host_glibc':platform.libc_ver()})
        (destination/'runtime-profile').write_text(runtime_profile+'\n')
        (destination/'target').write_text(target+'\n')
        copy_file(ROOT/'runtime/value_runtime.c',destination/'runtime/value_runtime.c',inventory)
        copy_file(ROOT/'runtime/native_gc_runtime.c',destination/'runtime/native_gc_runtime.c',inventory)
        runtime=destination/'lib/erist-runtime.o'
        if runtime_profile=='bootstrap':run([*cc,*RUNTIME_FLAGS,'-c',ROOT/'runtime/native_gc_runtime.c','-o',runtime],echo_stdout=True)
        runtime_source='src/owned_runtime.eri' if runtime_profile=='owned' else 'runtime/native_gc_runtime.c'
        write_json(destination/'build-toolchain.json',{'compiler':run([*cc,'--version']).stdout.splitlines()[0],
                   'runtime_flags':RUNTIME_FLAGS if runtime_profile=='bootstrap' else [],'runtime_source':runtime_source,'target':target,
                   'bootstrap_cc':cc,'bootstrap_cflags':shlex.split(os.environ.get('CFLAGS','')),
                   'generator_bootstrap_flags':RUNTIME_FLAGS if runtime_profile=='owned' else []})
    def fixed_snapshot():
        if source_hashes()!=snapshot:raise RuntimeError('build inputs changed during self-build; rerun on a fixed snapshot')
    with tempfile.TemporaryDirectory() as td:
        scratch=Path(td)
        bootstrap=Path(compiler).resolve() if compiler is not None else scratch/'bootstrap'
        if compiler is None:
            with journal.stage('stage0-bootstrap'):
                run([sys.executable,'-m','compiler.erist','build',ROOT/'src/frontend.eri','--source-root',ROOT/'src','-o',bootstrap],cwd=ROOT,echo_stdout=True)
        with journal.stage('bootstrap-seed'):
            seed_hash=digest(bootstrap)
            write_json(journal.directory/'bootstrap-seed.json',{'path':str(bootstrap),'sha256':seed_hash,'provided':compiler is not None})
        if runtime_profile=='owned':
            with journal.stage('generate-owned-runtime'):
                owned=build_owned_runtime(bootstrap,journal.directory/'owned-runtime',trace_phases)
                runtime.parent.mkdir(exist_ok=True)
                shutil.copy2(owned,runtime)
        inventory.append({'file':str(runtime),'sha256':digest(runtime),'source':runtime_source})
        assembly=journal.directory/'compiler-b.s'
        started=time.perf_counter()
        with journal.stage('bootstrap-to-B-assembly'):
            emit_assembly(bootstrap,ROOT/'src/frontend.eri',ROOT/'src',target,assembly,trace_phases)
            fixed_snapshot()
            if digest(bootstrap)!=seed_hash:raise RuntimeError('bootstrap compiler changed during build')
        binary=destination/'bin/erist-compiler'
        with journal.stage('link-B'):
            link(destination,assembly,binary,runtime)
            shutil.copy2(binary,journal.directory/'compiler-b')
            journal.state['compiler_B_sha256']=digest(binary)
        evidence={'bootstrap_native_assembly_sha256':digest(assembly),'runtime':runtime_profile,
                  'bootstrap_emit_seconds':time.perf_counter()-started,'repeatable':False}
        write_json(destination/'self-build.json',evidence)
        if self_build:
            started=time.perf_counter();c_assembly=journal.directory/'compiler-c.s'
            with journal.stage('native-B-to-C-assembly'):
                emit_assembly(binary,ROOT/'src/frontend.eri',ROOT/'src',target,c_assembly,trace_phases)
                journal.state['compiler_C_completed']=True;fixed_snapshot()
                if assembly.read_bytes()!=c_assembly.read_bytes():raise RuntimeError('self-build assembly differs between bootstrap and B')
                journal.state['assembly_BC_match']=True
            evidence['owned_B_emit_seconds' if runtime_profile=='owned' else 'native_B_emit_seconds']=time.perf_counter()-started
            c_binary=journal.directory/'compiler-c'
            with journal.stage('link-and-compare-C'):
                link(destination,c_assembly,c_binary,runtime)
                journal.state['compiler_C_sha256']=digest(c_binary)
                journal.save()
                if binary.read_bytes()!=c_binary.read_bytes():raise RuntimeError('self-build binary differs between B and C')
                journal.state['binary_BC_match']=True
            started=time.perf_counter();d_assembly=journal.directory/'compiler-d.s'
            with journal.stage('native-C-to-D-assembly'):
                emit_assembly(c_binary,ROOT/'src/frontend.eri',ROOT/'src',target,d_assembly,trace_phases)
                journal.state['compiler_D_completed']=True;fixed_snapshot()
                if c_assembly.read_bytes()!=d_assembly.read_bytes():raise RuntimeError('self-build assembly differs between B and C')
                journal.state['assembly_CD_match']=True
            evidence['owned_C_emit_seconds' if runtime_profile=='owned' else 'native_C_emit_seconds']=time.perf_counter()-started
            evidence.update(native_BC_assembly_sha256=digest(c_assembly),native_BC_binary_sha256=digest(binary),repeatable=True)
        write_json(destination/'self-build.json',evidence)
        journal.state['repeatable']=evidence['repeatable']
        journal.save()
    with journal.stage('package-metadata'):
        wrapper=destination/'bin/erist';wrapper.write_text(WRAPPER);wrapper.chmod(0o755)
        for name in ('LICENSE','DESIGN_PHILOSOPHY.md','LANGUAGE_SEMANTICS.md','FLOAT.md'):
            copy_file(ROOT/name,destination/'docs'/name,inventory)
        notices=destination/'licenses';notices.mkdir()
        for name in ('binutils','libc6','libgcc-s1','gcc-12-base','gcc-13-base','gcc-14-base'):
            source=Path('/usr/share/doc')/name/'copyright'
            if source.is_file():copy_file(source,notices/(name+'.copyright'),inventory)
        fixed_snapshot()
        for item in inventory:item['file']=str(Path(item['file']).relative_to(destination))
        write_json(destination/'inventory.json',inventory)
        runtime_note=('Owned Linux x86-64 runtime: compiler and applications are static ELF executables without C runtime, libc, CRT objects or a dynamic loader. Bootstrap creation still uses Python/C; packaged GNU tools and shell utilities retain host dependencies.\n' if runtime_profile=='owned' else 'The runtime remains a prebuilt C bootstrap artifact; a compatible host dynamic loader is required.\n')
        (destination/'README.txt').write_text('Eristavi offline compiler for this Linux host.\nRun bin/erist --help. Normal builds use the bundled assembler, linker and native runtime, with no Python or C compiler.\n'+runtime_note+'POSIX shell and ordinary shell utilities remain prerequisites. This is not a cross-platform production release.\nSee inventory.json, licenses/ and self-build.json for provenance and repeatability evidence.\n')
    with journal.stage('offline-audit'):
        # Keep the audit in this process: its journal owns each subprocess group
        # and deadline. Killing an outer audit subprocess could orphan a compiler
        # that the nested journal had launched in a separate session.
        verify_offline(destination,command_timeout=min(180,journal.timeout))
    print(destination,flush=True)
    return destination

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--compiler',type=Path)
    parser.add_argument('--runtime',choices=('bootstrap','owned'),default='bootstrap',help='owned is the Linux x86-64 runtime qualification path')
    parser.add_argument('--trace-phases',action='store_true',help='stream native compiler phase diagnostics to stderr and evidence logs')
    parser.add_argument('--command-timeout',type=float,default=900,help='per-command timeout in seconds (default: 900)')
    parser.add_argument('--skip-self-build',action='store_true',help='development only: package without a repeatability claim')
    args=parser.parse_args()
    try: build(args.output.resolve(),args.compiler.resolve() if args.compiler else None,not args.skip_self_build,args.runtime,trace_phases=args.trace_phases,command_timeout=args.command_timeout)
    except (RuntimeError,OSError,ValueError,subprocess.SubprocessError) as error:
        print(f'error: {error}',file=sys.stderr);raise SystemExit(1)
