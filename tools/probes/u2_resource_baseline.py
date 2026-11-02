"""Opt-in U2 prerequisite: legacy cleanup expansion and independent behavior.

This measures existing Stage-0/C-native paths, never a new U2 implementation.
Diagnostic cleanup failures are injected only after real handles have closed.
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
import subprocess
import sys
import tempfile
import time
import zipfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from compiler.erist.cli import CBackend, compile_entry, lower_project
from compiler.erist.c_backend import mangle
from compiler.erist.runtime import CheckedFailure, FileResource, file_error
from compiler.erist.runtime_ext import Interpreter


def source_for(depth: int) -> str:
    if not 1 <= depth <= 128:
        raise ValueError("baseline depth must be in 1..128")
    lines = [
        'import std.files;',
        'error BodyError { message Text; }',
        'function work(root Text, mode Int) returns Int fails BodyError, files.FileError {',
    ]
    for index in range(depth):
        lines += [
            f'with resource{index} be try files.open(root+"/r{index}") {{',
            f'if mode == {index} {{ return {index}; }}',
        ]
    lines += [f'if mode == {depth + 1} {{ fail BodyError {{ message="body"; }}; }}',
              f'return {depth};', *('}' for _ in range(depth)), '}',
              # Analyzed but replaced by the private native driver; Stage-0
              # invokes this same declared function through its normal API.
              'work("unused",0) else error { output(error.message); };']
    return '\n'.join(lines) + '\n'


def expected(depth: int, mode: int, failures: int, missing: int = -1) -> dict:
    acquired = min(mode + 1, depth)
    primary = "body" if mode == depth + 1 else None
    if 0 <= missing < acquired:
        acquired = missing
        primary = "open"
    closes = list(reversed(range(acquired)))
    failed = [i for i in closes if failures == 1 or failures == 2 and i % 2 == 0]
    secondary = [f'close-{i}' for i in failed]
    if primary is None and secondary:
        primary, *secondary = secondary
    return {"closes": closes, "primary": primary, "secondary": secondary,
            "result": None if primary else min(mode, depth)}


def stage0_case(module, root: Path, depth: int, mode: int, failures: int) -> dict:
    observed = []
    cleanup = FileResource.cleanup

    def injected(resource):
        index = int(Path(resource.path).name[1:])
        if resource.closed:
            raise AssertionError("double cleanup attempt")
        cleanup(resource)
        observed.append(index)
        if failures == 1 or failures == 2 and index % 2 == 0:
            raise CheckedFailure(file_error(f'close-{index}', resource.path))

    interpreter = Interpreter(module_id=module.module_id, imported_modules=module.imports)
    interpreter._prepare(module.program)
    primary, secondary, result = None, [], None
    with patch.object(FileResource, "cleanup", injected):
        try:
            result = interpreter._call_function(interpreter.functions['work'], [str(root), mode])
        except CheckedFailure as failure:
            message = failure.error.fields['message']
            primary = "open" if message not in ("body",) and not message.startswith("close-") else message
            secondary = [e.fields['message'] for e in failure.secondary]
    return {"closes": observed, "primary": primary, "secondary": secondary, "result": result}


DRIVER = r'''
static int u2_failure_mode;
static bool u2_observed_cleanup(eri_file *f, eri_failure_value *failure) {
    if (!f || f->closed) { fputs("DOUBLE-CLOSE\n",stderr); exit(125); }
    int id=-1;
    for(size_t i=0;i<f->path.len;i++) if(f->path.data[i]=='/' && i+1<f->path.len && f->path.data[i+1]=='r') {
        id=0; for(size_t j=i+2;j<f->path.len;j++) {
            if(f->path.data[j]<'0'||f->path.data[j]>'9') { fputs("BAD-PATH\n",stderr); exit(125); }
            id=id*10+f->path.data[j]-'0';
        }
    }
    if(id<0) exit(125);
    bool failed=u2_original_cleanup(f,failure);
    fprintf(stderr,"close:%d\n",id);
    if(failed) return true;
    if(u2_failure_mode==1 || (u2_failure_mode==2 && id%2==0)) {
        char message[40]; snprintf(message,sizeof(message),"close-%d",id);
        *failure=eri_make_file_failure(message,f->path);
        return true;
    }
    return false;
}
'''

MAIN = r'''
int main(int argc,char **argv) {
    if(argc!=4) return 125;
    int mode=atoi(argv[1]); u2_failure_mode=atoi(argv[3]);
    eri_handler_frame frame; frame.prev=eri_handler_top; eri_handler_top=&frame;
    if(setjmp(frame.env)==0) {
        int64_t result=U2_WORK(eri_text_from_cstr(argv[2]),mode);
        printf("result:%" PRId64 "\n",result);
    } else {
        fputs("primary:",stdout); fwrite(eri_failure.message.data,1,eri_failure.message.len,stdout); fputc('\n',stdout);
        for(eri_secondary_failure *p=eri_failure.secondary;p;p=p->next) {
            fputs("secondary:",stdout); fwrite(p->message.data,1,p->message.len,stdout); fputc('\n',stdout);
        }
    }
    eri_handler_top=frame.prev;
    return 0;
}
'''


def native_probe(c_source: str, work: str) -> str:
    # Exact-schema anchors fail closed on compiler/runtime drift.
    pattern = r'static bool eri_file_cleanup\(eri_file \*f,eri_failure_value \*failure\)\{[^\n]*\}'
    matches = list(re.finditer(pattern, c_source))
    if len(matches) != 1 or c_source.count('int main(int argc,char **argv)') != 1:
        raise AssertionError("C cleanup/entry schema changed; review diagnostic")
    match = matches[0]
    original = match.group().replace('eri_file_cleanup(', 'u2_original_cleanup(', 1)
    wrapper = DRIVER.replace('u2_observed_cleanup', 'eri_file_cleanup')
    modified = c_source[:match.start()] + original + '\n' + wrapper + c_source[match.end():]
    modified = modified.replace('int main(int argc,char **argv)',
                                'int u2_unused_main(int argc,char **argv)', 1)
    return modified + MAIN.replace('U2_WORK', work)


def decode_native(process: subprocess.CompletedProcess) -> dict:
    if process.returncode:
        raise AssertionError((process.returncode, process.stdout, process.stderr))
    closes = []
    for line in process.stderr.splitlines():
        if not re.fullmatch(r'close:\d+', line):
            raise AssertionError(f'unexpected diagnostic: {line}')
        closes.append(int(line.split(':')[1]))
    result, primary, secondary = None, None, []
    for line in process.stdout.splitlines():
        key, value = line.split(':', 1)
        if key == 'result': result = int(value)
        elif key == 'primary': primary = value if value == 'body' or value.startswith('close-') else 'open'
        elif key == 'secondary': secondary.append(value)
        else: raise AssertionError(f'unexpected output: {line}')
    return {"closes": closes, "primary": primary, "secondary": secondary, "result": result}


def measure(depths: tuple[int, ...], compiler: str, flags: tuple[str, ...]) -> dict:
    manifest = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted((ROOT / 'compiler').rglob('*.py'))}
    records = []
    with tempfile.TemporaryDirectory(prefix='eristavi-u2-baseline-') as temporary:
        root = Path(temporary)
        for depth in depths:
            directory = root / str(depth)
            directory.mkdir()
            for i in range(depth): (directory / f'r{i}').write_text('x', encoding='utf-8')
            source = directory / 'probe.eri'
            text = source_for(depth)
            source.write_text(text, encoding='utf-8')
            started = time.perf_counter()
            module = compile_entry(source, directory)
            lowered = lower_project(module)
            c_source = CBackend().emit(lowered)
            emission = time.perf_counter() - started
            work = next(f.name for f in lowered.functions if f.name.endswith('.work') or f.name == 'work')
            observed_c = native_probe(c_source, 'fn_' + mangle(work))
            cp, binary = directory / 'probe.c', directory / 'probe'
            cp.write_text(observed_c, encoding='utf-8')
            command = [compiler, '-std=c11', *flags, str(cp), '-lm', '-o', str(binary)]
            started = time.perf_counter()
            build = subprocess.run(command, capture_output=True, text=True, timeout=90)
            if build.returncode: raise AssertionError(build.stderr)
            compilation = time.perf_counter() - started
            cases = []
            for failure_mode in (0, 1, 2):
                for mode in range(depth + 2):
                    wanted = expected(depth, mode, failure_mode)
                    interpreted = stage0_case(module, directory, depth, mode, failure_mode)
                    started = time.perf_counter()
                    process = subprocess.run([str(binary), str(mode), str(directory), str(failure_mode)],
                                             capture_output=True, text=True, timeout=10)
                    elapsed = time.perf_counter() - started
                    actual = decode_native(process)
                    if interpreted != wanted or actual != wanted:
                        raise AssertionError((depth, mode, failure_mode, wanted, interpreted, actual))
                    cases.append({"mode": mode, "failure_mode": failure_mode, "expected": wanted,
                                  "stage0": interpreted, "native": actual, "native_seconds": elapsed})
            # A failed acquisition must introduce no owner for that resource.
            missing = depth // 2
            (directory / f'r{missing}').unlink()
            for failure_mode in (0, 1):
                mode = depth
                wanted = expected(depth, mode, failure_mode, missing)
                interpreted = stage0_case(module, directory, depth, mode, failure_mode)
                process = subprocess.run([str(binary), str(mode), str(directory), str(failure_mode)],
                                         capture_output=True, text=True, timeout=10)
                actual = decode_native(process)
                if interpreted != wanted or actual != wanted:
                    raise AssertionError(("acquisition", depth, wanted, interpreted, actual))
                cases.append({"mode": mode, "failure_mode": failure_mode, "missing": missing,
                              "expected": wanted, "stage0": interpreted, "native": actual})
            records.append({"depth": depth, "source_sha256": hashlib.sha256(text.encode()).hexdigest(),
                            "c_sha256": hashlib.sha256(c_source.encode()).hexdigest(),
                            "c_bytes": len(c_source.encode()), "binary_bytes": binary.stat().st_size,
                            "static_cleanup_calls": len(re.findall(r'eri_file_cleanup\(&', c_source)),
                            "exit_plan_unwind_sum": depth * (depth + 1) // 2 + 2 * depth,
                            "emission_seconds": emission, "native_build_seconds": compilation,
                            "cases": cases})
    if any(hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest
           for path, digest in manifest.items()):
        raise AssertionError('production source changed during measurement')
    version = subprocess.run([compiler, '--version'], capture_output=True, text=True, timeout=10)
    version.check_returncode()
    revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT,
                              capture_output=True, text=True, check=True, timeout=10).stdout.strip()
    return {"schema": 1, "baseline": "existing Stage-0 and C-native; not new U2",
            "base_commit": revision, "compiler_version": version.stdout.splitlines()[0],
            "production_source_sha256": manifest, "production_sources_unchanged": True,
            "compiler": compiler, "flags": list(flags), "platform": platform.platform(),
            "python": sys.version.split()[0], "measurements": records,
            "limits": "no RSS/owner attribution, new-U2 speedup or release qualification claimed"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--depths', type=int, nargs='+', default=[2, 8, 32])
    parser.add_argument('--cc', default=os.environ.get('CC', 'cc'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--archive', type=Path,
                        help='retain lossless raw records and write a compact JSON index')
    args = parser.parse_args()
    result = measure(tuple(args.depths), args.cc, tuple(shlex.split(os.environ.get('CFLAGS', '-O2'))))
    total_cases = sum(len(r['cases']) for r in result['measurements'])
    if args.archive:
        args.archive.parent.mkdir(parents=True, exist_ok=True)
        raw = json.dumps(result, indent=2).encode() + b'\n'
        payloads = {'baseline.json': raw, 'u2_resource_baseline.py': Path(__file__).read_bytes()}
        payloads['SHA256.json'] = json.dumps({name: hashlib.sha256(data).hexdigest()
                                            for name, data in payloads.items()}, indent=2).encode() + b'\n'
        with zipfile.ZipFile(args.archive, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            for name, data in payloads.items(): archive.writestr(name, data)
        with zipfile.ZipFile(args.archive) as archive:
            if archive.testzip() is not None: raise AssertionError('raw archive CRC failure')
            for name, data in payloads.items():
                if archive.read(name) != data: raise AssertionError('raw archive payload mismatch')
        result['raw_archive'] = {'file': args.archive.name,
                                 'sha256': hashlib.sha256(args.archive.read_bytes()).hexdigest()}
        for record in result['measurements']:
            cases = record.pop('cases')
            record['case_count'] = len(cases)
            record['cases_sha256'] = hashlib.sha256(json.dumps(cases, sort_keys=True).encode()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({"depths": args.depths, "cases": total_cases,
                      "status": "pass"}))


if __name__ == '__main__': main()
