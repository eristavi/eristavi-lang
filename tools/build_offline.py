#!/usr/bin/env python3
"""Build a host-specific experimental offline x86-64/Linux Eristavi toolchain.

Python/C are bootstrap build dependencies only. The resulting toolchain emits
native assembly and invokes its packaged assembler/linker, without Python or a
C compiler during normal application builds. No system installation is modified.
"""
from __future__ import annotations
import argparse
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
OFFLINE_HEAP_GC_INTERVAL=65536
RUNTIME_FLAGS=['-std=c11','-O2','-DERIST_NATIVE_RUNTIME',f'-DERIST_HEAP_GC_INTERVAL={OFFLINE_HEAP_GC_INTERVAL}']

def run(args,**kwargs):
    result=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=900,**kwargs)
    if result.returncode:
        raise RuntimeError(f'{shlex.join(list(map(str,args)))}\n{result.stderr}')
    return result

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
        run([bundle/'bin/as',*assembler_flags,assembly,'-o',obj],env=environment)
        if metadata.get('runtime')=='owned':
            run([bundle/'bin/ld','-nostdlib','-static','-e','_start','-o',output,obj,runtime],env=environment)
            audit_owned(output)
            return
        run([bundle/'bin/ld','-o',output,'-dynamic-linker',metadata['loader'],
             libraries/'crt1.o',libraries/'crti.o',libraries/'crtbegin.o',obj,runtime,
             libraries/'libm.so.6',libraries/'libc.so.6',libraries/'crtend.o',libraries/'crtn.o'],env=environment)

def audit_owned(binary):
    headers=run(['readelf','-lW',binary]).stdout
    if 'INTERP' in headers or 'DYNAMIC' in headers:
        raise RuntimeError('owned executable unexpectedly requires a dynamic runtime')
    stack=next((line for line in headers.splitlines() if 'GNU_STACK' in line),'')
    if not stack or 'RWE' in stack or run(['nm','-u',binary]).stdout.strip():
        raise RuntimeError('owned executable has imports or an executable/missing stack declaration')

def build_owned_runtime(bootstrap,destination):
    """Bootstrap the Eristavi emitter once; the emitted runtime has no C imports."""
    destination.mkdir(parents=True,exist_ok=True)
    assembly=destination/'owned-runtime.s'
    generator_assembly=destination/'runtime-generator.s'
    generator=destination/'runtime-generator'
    cc=shlex.split(os.environ.get('CC','cc'))
    generated=run([bootstrap,'emit-asm',ROOT/'src/owned_runtime.eri','--source-root',ROOT/'src',
                   '--target','x86_64-linux'],cwd=ROOT)
    generator_assembly.write_text(generated.stdout)
    # The emitter is the final bootstrap program here; it uses the qualified C
    # runtime. Neither the resulting owned object nor its executables link it.
    run([*cc,*RUNTIME_FLAGS,generator_assembly,ROOT/'runtime/native_gc_runtime.c','-lm','-o',generator])
    assembly.write_text(run([generator],cwd=ROOT).stdout)
    obj=destination/'erist-runtime.o'
    run(['as','--64',assembly,'-o',obj])
    return obj

WRAPPER=r'''#!/bin/sh
set -eu
bundle=$(CDPATH= cd -- "${0%/*}/.." && pwd -P)
original=$(pwd -P)
if [ "$#" = 0 ] || [ "${1:-}" = --help ]; then
    printf '%s\n' 'Usage: erist build SOURCE.eri -o PROGRAM [--source-root DIRECTORY]' '       erist check|ir|uir|build-asm|build-c SOURCE.eri [-o FILE] [--source-root DIRECTORY]' 'Experimental x86-64/ARM64 Linux native toolchain; source modules and the packaged runtime are supported.'
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
output=
while [ "$#" -gt 0 ]; do
    case "$1" in
        -o|--output) [ "$#" -ge 2 ] || exit 2; output=$2; shift 2;;
        --source-root) [ "$#" -ge 2 ] || exit 2; root=$2; shift 2;;
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
case "$command" in
    check) exec "$compiler" analyze "$source" --source-root "$root";;
    ir|uir) if [ -z "$output" ]; then exec "$compiler" "$command" "$source" --source-root "$root"; fi; mode=$command;;
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
    "$compiler" "$mode" "$source" --source-root "$root" --target "$target" > "$temporary/program.s"
else
    "$compiler" "$mode" "$source" --source-root "$root" > "$temporary/program.s"
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

def build(destination,compiler=None,self_build=True,runtime_profile='bootstrap'):
    if platform.system()!='Linux' or platform.machine().lower() not in ('x86_64','amd64','aarch64','arm64'):
        raise RuntimeError('offline native packaging currently supports x86-64/ARM64 Linux only')
    target='x86_64-linux' if platform.machine().lower() in ('x86_64','amd64') else 'arm64-linux'
    if runtime_profile not in ('bootstrap','owned'):
        raise RuntimeError(f'unknown runtime profile: {runtime_profile}')
    if runtime_profile=='owned' and target!='x86_64-linux':
        raise RuntimeError('the owned runtime currently supports Linux x86-64 only')
    if destination.exists():
        raise RuntimeError(f'choose a new output directory: {destination}')
    destination.mkdir(parents=True)
    inventory=[]
    cc=shlex.split(os.environ.get('CC','cc'))
    for name in ('as','ld'):
        found=shutil.which(name)
        if found is None: raise RuntimeError(f'bootstrap requires {name}')
        path=Path(found).resolve()
        copy_file(path,destination/'bin'/name,inventory)
        for library in dependencies(path):
            cached_library=destination/'tool-libs'/library.name
            if not cached_library.exists(): copy_file(library,cached_library,inventory)
    loader=None
    if runtime_profile=='bootstrap':
        for name in ('crt1.o','crti.o','crtbegin.o','crtend.o','crtn.o','libm.so.6','libc.so.6'):
            copy_file(compiler_file(cc,name),destination/'lib'/name,inventory)
        loader=compiler_file(cc,'ld-linux-x86-64.so.2' if target=='x86_64-linux' else 'ld-linux-aarch64.so.1')
        (destination/'loader-path').write_text(str(loader)+'\n')
    (destination/'platform.json').write_text(json.dumps({'target':target,'runtime':runtime_profile,'loader':str(loader) if loader else None,'host_glibc':platform.libc_ver()},indent=2)+'\n')
    (destination/'runtime-profile').write_text(runtime_profile+'\n')
    (destination/'target').write_text(target+'\n')
    copy_file(ROOT/'runtime/value_runtime.c',destination/'runtime/value_runtime.c',inventory)
    copy_file(ROOT/'runtime/native_gc_runtime.c',destination/'runtime/native_gc_runtime.c',inventory)
    runtime=destination/'lib/erist-runtime.o'
    if runtime_profile=='bootstrap':
        run([*cc,*RUNTIME_FLAGS,'-c',ROOT/'runtime/native_gc_runtime.c','-o',runtime])
    source_hashes={str(path.relative_to(ROOT)):digest(path) for path in sorted((ROOT/'src').rglob('*.eri'))}
    source_hashes['runtime/value_runtime.c']=digest(ROOT/'runtime/value_runtime.c')
    source_hashes['runtime/native_gc_runtime.c']=digest(ROOT/'runtime/native_gc_runtime.c')
    (destination/'source-manifest.json').write_text(json.dumps(source_hashes,indent=2)+'\n')
    evidence_directory=destination/'evidence';evidence_directory.mkdir()
    def fixed_snapshot():
        actual={name:digest(ROOT/name) for name in source_hashes}
        if actual!=source_hashes:
            raise RuntimeError('compiler source changed during self-build; rerun on a fixed snapshot')
    runtime_source='src/owned_runtime.eri' if runtime_profile=='owned' else 'runtime/native_gc_runtime.c'
    (destination/'build-toolchain.json').write_text(json.dumps({'compiler':run([*cc,'--version']).stdout.splitlines()[0],'runtime_flags':RUNTIME_FLAGS if runtime_profile=='bootstrap' else [],'runtime_source':runtime_source,'target':target},indent=2)+'\n')
    with tempfile.TemporaryDirectory() as td:
        scratch=Path(td)
        bootstrap=compiler
        if bootstrap is None:
            sys.path.insert(0,str(ROOT))
            from compiler.erist.cli import build_native
            bootstrap=scratch/'bootstrap'
            if build_native(ROOT/'src/frontend.eri',bootstrap,ROOT/'src'):
                raise RuntimeError('Stage-0 bootstrap build failed')
        if runtime_profile=='owned':
            owned=build_owned_runtime(bootstrap,evidence_directory/'owned-runtime')
            runtime.parent.mkdir(exist_ok=True)
            shutil.copy2(owned,runtime)
        inventory.append({'file':str(runtime),'sha256':digest(runtime),'source':runtime_source})
        assembly=scratch/'compiler-b.s'
        print('Emit native compiler B',flush=True)
        started=time.perf_counter()
        result=run([bootstrap,'emit-asm',ROOT/'src/frontend.eri','--source-root',ROOT/'src','--target',target],cwd=ROOT)
        assembly.write_text(result.stdout)
        shutil.copy2(assembly,evidence_directory/'compiler-b.s');fixed_snapshot()
        binary=destination/'bin/erist-compiler'
        link(destination,assembly,binary,runtime)
        evidence={'bootstrap_native_assembly_sha256':digest(assembly),'runtime':runtime_profile,
                  'bootstrap_emit_seconds':time.perf_counter()-started}
        if self_build:
            print('Native compiler B emits compiler C',flush=True)
            started=time.perf_counter()
            c_assembly=scratch/'compiler-c.s'
            c_assembly.write_text(run([binary,'emit-asm',ROOT/'src/frontend.eri','--source-root',ROOT/'src','--target',target],cwd=ROOT).stdout)
            evidence['owned_B_emit_seconds' if runtime_profile=='owned' else 'native_B_emit_seconds']=time.perf_counter()-started
            shutil.copy2(c_assembly,evidence_directory/'compiler-c.s');fixed_snapshot()
            if assembly.read_bytes()!=c_assembly.read_bytes():
                raise RuntimeError('self-build assembly differs between bootstrap and B')
            c_binary=scratch/'compiler-c';link(destination,c_assembly,c_binary,runtime)
            if binary.read_bytes()!=c_binary.read_bytes():
                raise RuntimeError('self-build binary differs between B and C')
            print('Native compiler C reproduces the next assembly',flush=True)
            started=time.perf_counter()
            d_assembly=scratch/'compiler-d.s'
            d_assembly.write_text(run([c_binary,'emit-asm',ROOT/'src/frontend.eri','--source-root',ROOT/'src','--target',target],cwd=ROOT).stdout)
            evidence['owned_C_emit_seconds' if runtime_profile=='owned' else 'native_C_emit_seconds']=time.perf_counter()-started
            shutil.copy2(d_assembly,evidence_directory/'compiler-d.s');fixed_snapshot()
            if c_assembly.read_bytes()!=d_assembly.read_bytes():
                raise RuntimeError('self-build assembly differs between B and C')
            evidence.update({'native_BC_assembly_sha256':digest(c_assembly),'native_BC_binary_sha256':digest(binary),'repeatable':True})
        else:
            evidence['repeatable']=False
        (destination/'self-build.json').write_text(json.dumps(evidence,indent=2)+'\n')
    wrapper=destination/'bin/erist';wrapper.write_text(WRAPPER);wrapper.chmod(0o755)
    for name in ('LICENSE','DESIGN_PHILOSOPHY.md','LANGUAGE_SEMANTICS.md','FLOAT.md'):
        copy_file(ROOT/name,destination/'docs'/name,inventory)
    notices=destination/'licenses';notices.mkdir()
    for name in ('binutils','libc6','libgcc-s1','gcc-12-base','gcc-13-base','gcc-14-base'):
        source=Path('/usr/share/doc')/name/'copyright'
        if source.is_file(): copy_file(source,notices/(name+'.copyright'),inventory)
    fixed_snapshot()
    for item in inventory:
        item['file']=str(Path(item['file']).relative_to(destination))
    (destination/'inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
    runtime_note=('Owned Linux x86-64 runtime: compiler and applications are static ELF executables without C runtime, libc, CRT objects or a dynamic loader. Bootstrap creation still uses Python/C; packaged GNU tools and shell utilities retain host dependencies.\n' if runtime_profile=='owned' else 'The runtime remains a prebuilt C bootstrap artifact; a compatible host dynamic loader is required.\n')
    (destination/'README.txt').write_text('Eristavi offline compiler for this Linux host.\nRun bin/erist --help. Normal builds use the bundled assembler, linker and native runtime, with no Python or C compiler.\n'+runtime_note+'POSIX shell and ordinary shell utilities remain prerequisites. This is not a cross-platform production release.\nSee inventory.json, licenses/ and self-build.json for provenance and repeatability evidence.\n')
    print('Audit builds without Python or a C compiler in child PATH',flush=True)
    audit=run([sys.executable,ROOT/'tools/verify_offline.py',destination],cwd=ROOT)
    print(audit.stdout,end='',flush=True)
    print(destination,flush=True)
    return destination

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--compiler',type=Path)
    parser.add_argument('--runtime',choices=('bootstrap','owned'),default='bootstrap',help='owned is the Linux x86-64 runtime qualification path')
    parser.add_argument('--skip-self-build',action='store_true',help='development only: package without a repeatability claim')
    args=parser.parse_args()
    try: build(args.output.resolve(),args.compiler.resolve() if args.compiler else None,not args.skip_self_build,args.runtime)
    except (RuntimeError,OSError,subprocess.SubprocessError) as error:
        print(f'error: {error}',file=sys.stderr);raise SystemExit(1)
