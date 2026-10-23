from __future__ import annotations
import argparse, os, subprocess, tempfile
from pathlib import Path
import sys
from .diagnostics import EristaviError
from .lexer import Lexer
from .parser import Parser
from .semantic import Analyzer
from .runtime import Interpreter
from .project import compile_entry
from .ir import Lowerer
from .c_backend import CBackend

def analyze_frontend(source:str):
    program=Parser(Lexer(source).lex()).parse(); analyzer=Analyzer(); analyzer.analyze(program); return program,analyzer

def compile_frontend(source:str): return analyze_frontend(source)[0]

def run_file(path:Path,source_root:Path|None=None)->int:
    try:
        mod=compile_entry(path,source_root); Interpreter(module_id=mod.module_id,imported_modules=mod.imports).run(mod.program); return 0
    except EristaviError as e: print(e.format(),file=sys.stderr); return 1
    except OSError as e: print(f'error: {e}',file=sys.stderr); return 1

def check_file(path:Path,source_root:Path|None=None)->int:
    try: compile_entry(path,source_root); return 0
    except EristaviError as e: print(e.format(),file=sys.stderr); return 1
    except OSError as e: print(f'error: {e}',file=sys.stderr); return 1

def build_c_file(path:Path,output:Path,source_root:Path|None=None)->int:
    try:
        mod=compile_entry(path,source_root); ir=Lowerer(mod.analyzer).lower(mod.program); output.write_text(CBackend().emit(ir),encoding='utf-8'); return 0
    except (EristaviError,OSError) as e:
        print(e.format() if isinstance(e,EristaviError) else f'error: {e}',file=sys.stderr); return 1

def build_native(path:Path,output:Path,source_root:Path|None=None,cc:str='cc')->int:
    try:
        mod=compile_entry(path,source_root); ir=Lowerer(mod.analyzer).lower(mod.program); c=CBackend().emit(ir)
        with tempfile.TemporaryDirectory() as td:
            cp=Path(td)/'program.c'; cp.write_text(c,encoding='utf-8')
            proc=subprocess.run([cc,'-std=c11',str(cp),'-lm','-o',str(output)],capture_output=True,text=True)
            if proc.returncode!=0:
                if proc.stdout: print(proc.stdout,file=sys.stderr,end='')
                if proc.stderr: print(proc.stderr,file=sys.stderr,end='')
                return proc.returncode or 1
        return 0
    except (EristaviError,OSError) as e:
        print(e.format() if isinstance(e,EristaviError) else f'error: {e}',file=sys.stderr); return 1

def build_parser():
    p=argparse.ArgumentParser(prog='erist',description='Eristavi bootstrap toolchain'); sub=p.add_subparsers(dest='command',required=True)
    for name in ('run','check'):
        c=sub.add_parser(name); c.add_argument('entry',type=Path); c.add_argument('--source-root',type=Path,default=None)
    bc=sub.add_parser('build-c',help='lower the currently supported typed IR subset to C source'); bc.add_argument('entry',type=Path); bc.add_argument('-o','--output',type=Path,required=True); bc.add_argument('--source-root',type=Path,default=None)
    b=sub.add_parser('build',help='compile the currently supported typed IR subset through the system C toolchain'); b.add_argument('entry',type=Path); b.add_argument('-o','--output',type=Path,required=True); b.add_argument('--source-root',type=Path,default=None); b.add_argument('--cc',default=os.environ.get('CC','cc'))
    return p

def main(argv=None):
    a=build_parser().parse_args(argv)
    if a.command=='run': return run_file(a.entry,a.source_root)
    if a.command=='check': return check_file(a.entry,a.source_root)
    if a.command=='build-c': return build_c_file(a.entry,a.output,a.source_root)
    if a.command=='build': return build_native(a.entry,a.output,a.source_root,a.cc)
    return 2
if __name__=='__main__': raise SystemExit(main())
