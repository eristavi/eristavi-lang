from __future__ import annotations
import argparse, os, platform, shlex, subprocess, tempfile
from pathlib import Path
import sys
from .diagnostics import EristaviError
from .lexer import Lexer
from .parser import Parser
from .semantic_ext import Analyzer
from .runtime_ext import Interpreter
from .project import compile_entry, compile_module
from .ir import IRProgram
from .ir_text import Lowerer
from .c_backend_views import CBackend
from .universal_ir import format_program
from .x86_64_checked_backend import X86_64CheckedLinuxBackend
from .arm64_backend import ARM64LinuxBackend
from .direct_project import compile_module_object, lower_direct_entry, object_path

def analyze_frontend(source:str):
    program=Parser(Lexer(source).lex()).parse(); analyzer=Analyzer(); analyzer.analyze(program); return program,analyzer

def compile_frontend(source:str): return analyze_frontend(source)[0]

def _require_implementations(mod):
    seen=set()
    def visit(current):
        if current.module_id in seen: return
        seen.add(current.module_id)
        if current.interface_only:
            raise ValueError(f"module {current.module_id!r} is available only as an interface; this backend requires its implementation source")
        for child in current.imports.values(): visit(child)
    visit(mod)

def lower_project(entry_module):
    _require_implementations(entry_module)
    order=[]; seen=set()
    def visit(mod):
        key=mod.module_id or str(mod.file_path)
        if key in seen: return
        seen.add(key)
        for child in mod.imports.values(): visit(child)
        order.append(mod)
    visit(entry_module)
    structs=[]; functions=[]; entry=[]
    for mod in order:
        part=Lowerer(mod.analyzer,mod.module_id).lower(mod.program,mod is entry_module)
        structs.extend(part.structs); functions.extend(part.functions)
        if mod is entry_module: entry.extend(part.entry)
    return IRProgram(structs,functions,entry)

def lower_universal_file(path:Path,source_root:Path|None=None):
    return lower_direct_entry(path,source_root)

def run_file(path:Path,source_root:Path|None=None)->int:
    try:
        mod=compile_entry(path,source_root); _require_implementations(mod); Interpreter(module_id=mod.module_id,imported_modules=mod.imports).run(mod.program); return 0
    except EristaviError as e: print(e.format(),file=sys.stderr); return 1
    except (OSError,ValueError) as e: print(f'error: {e}',file=sys.stderr); return 1

def check_file(path:Path,source_root:Path|None=None)->int:
    try: compile_entry(path,source_root); return 0
    except EristaviError as e: print(e.format(),file=sys.stderr); return 1
    except OSError as e: print(f'error: {e}',file=sys.stderr); return 1

def emit_interface(path:Path,output:Path|None=None,source_root:Path|None=None)->int:
    try:
        mod=compile_module(path,source_root)
        target=output or path.with_suffix('.eri-interface.json')
        target.write_text(mod.interface.to_json(),encoding='utf-8')
        return 0
    except (EristaviError,OSError,ValueError) as e:
        print(e.format() if isinstance(e,EristaviError) else f'error: {e}',file=sys.stderr); return 1

def emit_object(path:Path,output:Path|None=None,source_root:Path|None=None)->int:
    try:
        artifact=compile_module_object(path,source_root)
        target=output or object_path(path)
        target.write_text(artifact.to_json(),encoding='utf-8')
        return 0
    except (EristaviError,OSError,ValueError) as e:
        print(e.format() if isinstance(e,EristaviError) else f'error: {e}',file=sys.stderr); return 1

def emit_uir(path:Path,output:Path,source_root:Path|None=None)->int:
    try:
        output.write_text(format_program(lower_universal_file(path,source_root)),encoding='utf-8')
        return 0
    except (EristaviError,OSError,ValueError) as e:
        print(e.format() if isinstance(e,EristaviError) else f'error: {e}',file=sys.stderr); return 1

def _direct_backend(target:str):
    if target=='x86_64-linux': return X86_64CheckedLinuxBackend()
    if target in ('arm64-linux','aarch64-linux'): return ARM64LinuxBackend()
    raise ValueError(f"unsupported direct backend target {target!r}")

def _native_direct_host(target:str)->bool:
    machine=platform.machine().lower(); system=platform.system()
    if target=='x86_64-linux': return system=='Linux' and machine in ('x86_64','amd64')
    if target in ('arm64-linux','aarch64-linux'): return system=='Linux' and machine in ('aarch64','arm64')
    return False

def emit_direct_asm(path:Path,output:Path,source_root:Path|None=None,target:str='x86_64-linux')->int:
    try:
        program=lower_universal_file(path,source_root)
        output.write_text(_direct_backend(target).emit(program),encoding='utf-8')
        return 0
    except (EristaviError,OSError,ValueError) as e:
        print(e.format() if isinstance(e,EristaviError) else f'error: {e}',file=sys.stderr); return 1

def build_direct(path:Path,output:Path,source_root:Path|None=None,target:str='x86_64-linux',cc:str|None=None)->int:
    try:
        backend=_direct_backend(target)
        if not _native_direct_host(target):
            raise ValueError(f"{target} direct linking currently requires a matching native Linux host")
        compiler=cc or os.environ.get('CC','cc')
        flags=shlex.split(os.environ.get('CFLAGS',''))
        program=lower_universal_file(path,source_root)
        assembly=backend.emit(program)
        with tempfile.TemporaryDirectory() as td:
            asm=Path(td)/'program.s'; asm.write_text(assembly,encoding='utf-8')
            proc=subprocess.run([compiler,*flags,str(asm),'-o',str(output)],capture_output=True,text=True)
            if proc.returncode!=0:
                if proc.stdout: print(proc.stdout,file=sys.stderr,end='')
                if proc.stderr: print(proc.stderr,file=sys.stderr,end='')
                return proc.returncode or 1
        return 0
    except (EristaviError,OSError,ValueError) as e:
        print(e.format() if isinstance(e,EristaviError) else f'error: {e}',file=sys.stderr); return 1

def build_c_file(path:Path,output:Path,source_root:Path|None=None)->int:
    try:
        mod=compile_entry(path,source_root); ir=lower_project(mod); output.write_text(CBackend().emit(ir),encoding='utf-8'); return 0
    except (EristaviError,OSError,ValueError) as e:
        print(e.format() if isinstance(e,EristaviError) else f'error: {e}',file=sys.stderr); return 1

def build_native(path:Path,output:Path,source_root:Path|None=None,cc:str|None=None)->int:
    try:
        compiler=cc or os.environ.get('CC','cc')
        cflags=shlex.split(os.environ.get('CFLAGS',''))
        mod=compile_entry(path,source_root); ir=lower_project(mod); c=CBackend().emit(ir)
        with tempfile.TemporaryDirectory() as td:
            cp=Path(td)/'program.c'; cp.write_text(c,encoding='utf-8')
            proc=subprocess.run([compiler,'-std=c11',*cflags,str(cp),'-lm','-o',str(output)],capture_output=True,text=True)
            if proc.returncode!=0:
                if proc.stdout: print(proc.stdout,file=sys.stderr,end='')
                if proc.stderr: print(proc.stderr,file=sys.stderr,end='')
                return proc.returncode or 1
        return 0
    except (EristaviError,OSError,ValueError) as e:
        print(e.format() if isinstance(e,EristaviError) else f'error: {e}',file=sys.stderr); return 1

def build_parser():
    p=argparse.ArgumentParser(prog='erist',description='Eristavi bootstrap toolchain'); sub=p.add_subparsers(dest='command',required=True)
    for name in ('run','check'):
        c=sub.add_parser(name); c.add_argument('entry',type=Path); c.add_argument('--source-root',type=Path,default=None)
    interface=sub.add_parser('interface',help='emit a deterministic versioned module interface artifact'); interface.add_argument('module',type=Path); interface.add_argument('-o','--output',type=Path,default=None); interface.add_argument('--source-root',type=Path,default=None)
    obj=sub.add_parser('object',help='emit a linkable Universal-IR module implementation artifact'); obj.add_argument('module',type=Path); obj.add_argument('-o','--output',type=Path,default=None); obj.add_argument('--source-root',type=Path,default=None)
    uir=sub.add_parser('uir',help='lower the direct-backend subset to Universal IR'); uir.add_argument('entry',type=Path); uir.add_argument('-o','--output',type=Path,required=True); uir.add_argument('--source-root',type=Path,default=None)
    asm=sub.add_parser('build-asm',help='emit direct CPU assembly from Universal IR'); asm.add_argument('entry',type=Path); asm.add_argument('-o','--output',type=Path,required=True); asm.add_argument('--source-root',type=Path,default=None); asm.add_argument('--target',default='x86_64-linux',choices=('x86_64-linux','arm64-linux','aarch64-linux'))
    direct=sub.add_parser('build-direct',help='compile without the C backend through a direct CPU backend'); direct.add_argument('entry',type=Path); direct.add_argument('-o','--output',type=Path,required=True); direct.add_argument('--source-root',type=Path,default=None); direct.add_argument('--target',default='x86_64-linux',choices=('x86_64-linux','arm64-linux','aarch64-linux')); direct.add_argument('--cc',default=os.environ.get('CC','cc'))
    bc=sub.add_parser('build-c',help='lower the typed IR subset to C source'); bc.add_argument('entry',type=Path); bc.add_argument('-o','--output',type=Path,required=True); bc.add_argument('--source-root',type=Path,default=None)
    b=sub.add_parser('build',help='compile the typed IR path through the system C toolchain'); b.add_argument('entry',type=Path); b.add_argument('-o','--output',type=Path,required=True); b.add_argument('--source-root',type=Path,default=None); b.add_argument('--cc',default=os.environ.get('CC','cc'))
    return p

def main(argv=None):
    a=build_parser().parse_args(argv)
    if a.command=='run': return run_file(a.entry,a.source_root)
    if a.command=='check': return check_file(a.entry,a.source_root)
    if a.command=='interface': return emit_interface(a.module,a.output,a.source_root)
    if a.command=='object': return emit_object(a.module,a.output,a.source_root)
    if a.command=='uir': return emit_uir(a.entry,a.output,a.source_root)
    if a.command=='build-asm': return emit_direct_asm(a.entry,a.output,a.source_root,a.target)
    if a.command=='build-direct': return build_direct(a.entry,a.output,a.source_root,a.target,a.cc)
    if a.command=='build-c': return build_c_file(a.entry,a.output,a.source_root)
    if a.command=='build': return build_native(a.entry,a.output,a.source_root,a.cc)
    return 2
if __name__=='__main__': raise SystemExit(main())
