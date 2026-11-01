#!/usr/bin/env python3
"""Issue #51: paired baseline/candidate Universal verifier validation and timing.

Five paired, uninstrumented same-host runs. Real production owned compiler B
compiled by the C bootstrap, plus independent C and owned validator corpus.
The only candidate change is semantic_model.at's short-circuit branch order.
Never invoke an owned frontend to build frontend. Exact output and errors win
over timing; no assertion that an optimization must be faster.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT/"tests")]
from compiler.erist.cli import build_native
from u1_native_tools import shared_u1_compilers
from universal_verifier_cases import regression_program, benchmark_program


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(command, cap=60, output_file=None):
    start=time.monotonic()
    args=list(map(str,command))
    if output_file is not None:
        with Path(output_file).open("wb") as dest:
            child=subprocess.run(args,stdout=dest,stderr=subprocess.PIPE,timeout=cap)
        data=b""
    else:
        child=subprocess.run(args,capture_output=True,timeout=cap)
        data=child.stdout
    elapsed=time.monotonic()-start
    if child.returncode or child.stderr:
        raise AssertionError(f"nonzero/diagnostic: {args} status={child.returncode} stderr={child.stderr[-1000:]!r}")
    return elapsed,data


def overlay(root, baseline_source):
    # Frozen Eristavi source resolution canonicalizes symlinks, so a
    # linked entry escapes its source root. Use private byte-for-byte copies.
    shutil.copytree(ROOT/"src",root,symlinks=False)
    (root/"compiler/semantic_model.eri").write_bytes(baseline_source)
    return root


def build_reference(source, output, source_root):
    start=time.monotonic()
    code=build_native(source,output,source_root,cc=os.environ.get("CC","clang"))
    if code:
        raise AssertionError("C-bootstrap build failed: "+str(source))
    return time.monotonic()-start


def owned_link(asm, runtime, directory, name):
    app=directory/(name+".s")
    obj=directory/(name+".o")
    runtime_obj=directory/"runtime.o"
    exe=directory/name
    app.write_bytes(asm)
    run(["as","--64",app,"-o",obj])
    if not runtime_obj.exists():
        runtime_asm=directory/"runtime.s"
        runtime_asm.write_bytes(runtime)
        run(["as","--64",runtime_asm,"-o",runtime_obj])
    run(["ld","-nostdlib","-static","-e","_start",obj,runtime_obj,"-o",exe])
    return exe


def c_emit(frontend, source, root, out):
    return run([frontend,"emit-asm",source,"--source-root",root,
                "--target","x86_64-linux"],cap=90,output_file=out)[0]


def expected_run(binary, expected, cap=75):
    elapsed,stdout=run([binary],cap=cap)
    if stdout!=expected:
        raise AssertionError(f"stdout oracle differs on {binary}; got {stdout[-300:]!r}")
    return elapsed


def paired(baseline, candidate, expected, count=5, cap=75):
    pairs=[]
    for number in range(count):
        results={}
        for label in (("baseline","candidate") if number%2==0 else
                      ("candidate","baseline")):
            results[label]=expected_run(baseline if label=="baseline" else candidate,
                                        expected,cap=cap)
        pairs.append(results)
    before=[p["baseline"] for p in pairs]
    after=[p["candidate"] for p in pairs]
    return {"pairs":pairs,"baseline_median_seconds":statistics.median(before),
            "candidate_median_seconds":statistics.median(after),
            "median_reduction_percent":100*(1-statistics.median(after)/statistics.median(before)),
            "candidate_faster_pairs":sum(p["candidate"]<p["baseline"] for p in pairs),
            "exact_output_parity_all":True}


def paired_compilers(base_binary,candidate_binary,base_c,candidate_c,
                     source,base_root,candidate_root,work, cap=75):
    reference={}
    for name,frontend,root in (("baseline",base_c,base_root),
                               ("candidate",candidate_c,candidate_root)):
        output=work/(name+".reference.s")
        c_emit(frontend,root/"compiler/typed_ir.eri",root,output)
        reference[name]=sha(output)
    pairs=[]
    for index in range(5):
        results={}
        for name in (("baseline","candidate") if index%2==0 else
                     ("candidate","baseline")):
            root=base_root if name=="baseline" else candidate_root
            binary=base_binary if name=="baseline" else candidate_binary
            output=work/(f"{name}-{index}.s")
            duration=run([binary,"emit-asm",root/"compiler/typed_ir.eri","--source-root",root,
                          "--target","x86_64-linux"],cap=cap,output_file=output)[0]
            if sha(output)!=reference[name]:
                raise AssertionError(f"independent compiler output parity failed: {name}, pair {index}")
            results[name]=duration
        pairs.append(results)
    before=[p["baseline"] for p in pairs]
    after=[p["candidate"] for p in pairs]
    return {"reference_sha256":reference,
            "cross_revision_sha_identical":len(set(reference.values()))==1,
            "source_sha256":sha(source),
            "pairs":pairs,"baseline_median_seconds":statistics.median(before),
            "candidate_median_seconds":statistics.median(after),
            "median_reduction_percent":100*(1-statistics.median(after)/statistics.median(before)),
            "candidate_faster_pairs":sum(p["candidate"]<p["baseline"] for p in pairs),
            "independent_assembly_parity_all":True}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output",required=True,type=Path)
    args=ap.parse_args()
    if platform.system()!="Linux" or platform.machine().lower() not in ("x86_64","amd64"):
        raise RuntimeError("Linux x86-64 benchmark only")
    output=args.output.resolve()
    output.mkdir(parents=True,exist_ok=True)
    source=ROOT/"src/compiler/semantic_model.eri"
    original_sha=sha(source)
    old=subprocess.run(["git","show","HEAD^1:src/compiler/semantic_model.eri"],
                       capture_output=True,check=True).stdout
    old_sha=hashlib.sha256(old).hexdigest()
    if old_sha==original_sha:
        raise AssertionError("candidate source unexpectedly identical to baseline")
    summary={"scope":"issue #51 current production semantic location lookup, short-circuit left-first branch; "
                     "five uninstrumented paired Linux Clang trials; not full compiler self-build",
             "baseline_source_sha256":old_sha,"candidate_source_sha256":original_sha,
             "compiler_owned_self_build":False,"benchmarks":{}}
    with tempfile.TemporaryDirectory(prefix="issue51-paired-") as d:
        work=Path(d)
        base_root=overlay(work/"baseline_src",old)
        candidate_root=overlay(work/"candidate_src",source.read_bytes())
        candidate_frontend, generator=shared_u1_compilers()
        baseline_frontend=work/"baseline_c_frontend"
        summary["baseline_frontend_build_seconds"]=build_reference(
            base_root/"frontend.eri",baseline_frontend,base_root)
        runtime=run([generator],cap=90)[1]
        baseline_b_asm=work/"baseline_b.s"
        candidate_b_asm=work/"candidate_b.s"
        summary["bootstrap_emission_seconds"]={
            "baseline":c_emit(baseline_frontend,base_root/"frontend.eri",base_root,baseline_b_asm),
            "candidate":c_emit(candidate_frontend,candidate_root/"frontend.eri",candidate_root,candidate_b_asm)}
        runtime_asm=runtime
        baseline_b=owned_link(baseline_b_asm.read_bytes(),runtime_asm,work,"baseline_b")
        candidate_b=owned_link(candidate_b_asm.read_bytes(),runtime_asm,work,"candidate_b")
        summary["compiler_binary_sha256"]={"baseline":sha(baseline_b),"candidate":sha(candidate_b)}
        print("built two real owned B compilers; no owned self build",flush=True)
        # Compare generated code for an unchanged neutral source at the SAME
        # physical source path/root. Compiler module typed_ir.eri itself imports
        # semantic_model, so changing that module legitimately changes its
        # compiled assembly; its cross-revision SHA is not a semantic oracle.
        neutral=ROOT/"examples/hello.eri"
        neutral_root=neutral.parent
        neutral_digests={}
        for name,comp in (("baseline_C",baseline_frontend),
                          ("candidate_C",candidate_frontend),
                          ("baseline_owned",baseline_b),
                          ("candidate_owned",candidate_b)):
            neutral_assembly=work/(name+".neutral.s")
            c_emit(comp,neutral,neutral_root,neutral_assembly)
            neutral_digests[name]=sha(neutral_assembly)
        if len(set(neutral_digests.values()))!=1:
            raise AssertionError("unchanged neutral source emitted different assembly")
        summary["neutral_source_parity"]={"source":str(neutral.relative_to(ROOT)),
                                           "assembly_sha256":next(iter(neutral_digests.values())),
                                           "C_and_owned_both_revisions_identical":True}
        print("neutral source byte-exact C/owned baseline/candidate assembler: PASS",flush=True)
        # Verify the complete *public* Universal verifier malformed/CFG/bit
        # boundary contract against its separate frozen expected strings.
        regression, expected=regression_program()
        truth=expected.encode()
        for label,root,cc in (("baseline",base_root,baseline_frontend),
                              ("candidate",candidate_root,candidate_frontend)):
            reg=root/"__issue51_regression.eri"
            reg.write_text(regression)
            c_obj=work/(label+"-regression-C")
            build_reference(reg,c_obj,root)
            expected_run(c_obj,truth,cap=75)
            asm=work/(label+"-regression.s")
            c_emit(cc,reg,root,asm)
            executable=owned_link(asm.read_bytes(),runtime,work,label+"-regression-owned")
            expected_run(executable,truth,cap=75)
        summary["regression_oracle"]={"cases":"full existing public verifier regression_program",
                                       "baseline_C":"PASS","candidate_C":"PASS",
                                       "baseline_owned":"PASS","candidate_owned":"PASS",
                                       "exact_stdout_stderr_exit":True}
        (output/"regression.json").write_text(json.dumps(summary["regression_oracle"],indent=2)+"\n")
        print("public verifier regression corpus: C+owned baseline/candidate PASS",flush=True)
        # Same controlled branch joins, definite-initialization, and 62-bit
        # intersections as production verify, repeated to amplify the candidate.
        benchmark_text=benchmark_program(width=512,chains=12,rounds=4)
        for label,root,cc in (("baseline",base_root,baseline_frontend),
                              ("candidate",candidate_root,candidate_frontend)):
            benchmark=root/"__issue51_benchmark.eri"
            benchmark.write_text(benchmark_text)
            c_obj=work/(label+"-benchmark-C")
            build_reference(benchmark,c_obj,root)
            expected_run(c_obj,b"4\n",cap=75)
            asm=work/(label+"-benchmark.s")
            c_emit(cc,benchmark,root,asm)
            owned_link(asm.read_bytes(),runtime,work,label+"-benchmark-owned")
        summary["benchmarks"]["verifier_repeated_owned"]=paired(
            work/"baseline-benchmark-owned",work/"candidate-benchmark-owned",b"4\n")
        (output/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
        print("verifier five paired owned samples complete",flush=True)
        summary["benchmarks"]["production_typed_ir_compilation"]=paired_compilers(
            baseline_b,candidate_b,baseline_frontend,candidate_frontend,
            ROOT/"src/compiler/typed_ir.eri",base_root,candidate_root,work)
        print("production compiler five paired typed_ir source samples complete",flush=True)
        summary["source_snapshot_unchanged"]=sha(source)==original_sha
    if not summary["source_snapshot_unchanged"]:
        raise AssertionError("compiler source mutated during benchmark")
    (output/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print("ISSUE51_PAIRED="+json.dumps(summary,sort_keys=True),flush=True)


if __name__=="__main__":
    main()
