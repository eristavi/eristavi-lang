#!/usr/bin/env python3
"""Run inexpensive integration checks before compiler self-build qualification."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

FAST_TESTS=(
    'test_bootstrap.py','test_unicode.py','test_text_views.py',
    'test_project.py','test_interfaces.py','test_recursive_inference.py',
    'test_generic_index_assignment.py','test_map_bytes_collections.py',
    'test_collection_ir.py','test_collection_preflight.py',
    'test_heap_accounting.py','test_native_heap_gc.py',
)


def qualify_collections():
    """Require backend support before paying for full compiler self-builds.

    Do not invoke a system compiler here: source analysis, C emission and both
    native emitters must first accept small representative collection programs.
    Passing this smoke check does not replace execution, GC or self-build tests.
    """
    from compiler.erist.cli import lower_project,lower_universal_file
    from compiler.erist.project import compile_entry
    from compiler.erist.c_backend_views import CBackend
    from compiler.erist.x86_64_gc_precise import X86_64PreciseRootGCLinuxBackend
    from compiler.erist.arm64_direct_backend import ARM64DirectLinuxBackend
    samples={
        'Map':'let original be ["a" : "alive";]; let copy be original; copy["a"]="changed"; output(original["a"]); output(copy.count);',
        'Bytes':'let original Bytes be [0,255]; let copy be original; copy[0]=42; output(original[0]); output(copy[0]);',
    }
    failures=[]
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);entry=root/'app.eri'
        for name,source in samples.items():
            entry.write_text(source,encoding='utf-8')
            for backend,emit in (
                ('C',lambda:CBackend().emit(lower_project(compile_entry(entry,root)))),
                ('x86-64',lambda:X86_64PreciseRootGCLinuxBackend().emit(lower_universal_file(entry,root))),
                ('ARM64',lambda:ARM64DirectLinuxBackend().emit(lower_universal_file(entry,root))),
            ):
                try:
                    if not emit():
                        raise ValueError('emitter produced no output')
                except Exception as error:
                    failures.append(f'{name} / {backend}: {error}')
    if failures:
        print('Full qualification blocked before self-build:',file=sys.stderr)
        for failure in failures:
            print(f'  {failure}',file=sys.stderr)
        return False
    return True


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--qualify',action='store_true',help='also require collection backend support before the full matrix')
    args=parser.parse_args()
    suite=unittest.TestSuite();loader=unittest.TestLoader()
    for pattern in FAST_TESTS:
        if not (ROOT/'tests'/pattern).is_file():
            parser.error(f'missing required preflight test: {pattern}')
        suite.addTests(loader.discover(str(ROOT/'tests'),pattern=pattern))
    if not unittest.TextTestRunner(verbosity=1).run(suite).wasSuccessful():
        return 1
    if args.qualify and not qualify_collections():
        return 1
    return 0


if __name__=='__main__':
    raise SystemExit(main())
