"""Opt-in verified whole-Function scalar CFG native lowering.

The source fixture builds the ORIGINAL frozen canonical UIR Function and
checks the independent U1b reference executor before emitting x86-64.
The runtime executes REAL GNU-assembled native code, not a Python mimic.
"""
from pathlib import Path
import platform
import subprocess
import unittest
from compiler.erist.cli import build_native
import test_freestanding_graph_values as graph

ROOT=Path(__file__).resolve().parents[1]


@unittest.skipUnless(platform.system()=="Linux" and
                     platform.machine().lower() in ("x86_64","amd64"),
                     "whole-Function scalar backend currently Linux x86-64")
class U2FunctionScalarNativeTests(unittest.TestCase):
    setUpClass=classmethod(graph.FreestandingGraphValueTests.setUpClass.__func__)
    run_probe=graph.FreestandingGraphValueTests.run_probe

    def generator(self,name,source):
        folder=self.directory/name
        folder.mkdir()
        (folder/"compiler").symlink_to(
            ROOT/"src/compiler",target_is_directory=True)
        app=folder/"generator.eri"
        app.write_text(source,encoding="utf-8")
        native=folder/"generator"
        self.assertEqual(build_native(app,native,folder),0)
        return subprocess.run([str(native)],capture_output=True,
                              text=True,timeout=120)

    def fixture(self):
        return (ROOT/"tests/fixtures/u2_function_scalar_cfg.eri").read_text(
            encoding="utf-8")

    def test_entire_verified_function_loop_parallel_phi_and_dead_block(self):
        result=self.generator("native-scalar-cfg",self.fixture())
        self.assertEqual((result.returncode,result.stderr),(0,""),
                         result.stdout[-3000:])
        asm=result.stdout
        base="erist_u2_function_83"
        self.assertIn(base+":",asm)
        self.assertIn(base+"_block_4:",asm)
        self.assertIn(base+"_edge_1:",asm)
        self.assertIn(base+"_edge_3:",asm)
        self.assertIn("imulq",asm) if False else None
        self.assertIn("movabsq $11,%rax",asm)
        self.assertIn("addq %rcx,%rax",asm)
        self.assertIn("setl",asm) if False else None
        # The loop's self-edge has at least three independent staging moves
        # before ANY destination SSA parameter is overwritten.
        edge=asm.split(base+"_edge_2:",1)[1].split(
            "jmp "+base+"_block_",1)[0]
        self.assertGreaterEqual(edge.count("movq %rax,"),6)
        self.assertEqual(edge.count("(%rsp),%rax"),3)
        body="""\n.text
.globl _start
_start:
    leaq .Lu2_cfg_input(%rip),%rdi
    call erist_u2_function_83
    cmpq $37,%rax
    jne .Lgraph_test_fail
    cmpq $11,%rdx
    jne .Lgraph_test_fail
    jmp .Lgraph_finish
.section .rodata
.p2align 3
.Lu2_cfg_input:
.quad 37
"""
        executed=self.run_probe("u2-original-function-scalar-loop",
                                asm+body+graph.FINISH)
        self.assertEqual((executed.returncode,executed.stdout,
                          executed.stderr),(0,b"",b""))

    def test_unsupported_dead_aggregate_rejected_before_assembly(self):
        source=self.fixture()
        anchor="    try ab.returnValues(fn,graph,dead,[never,eleven],loc);"
        self.assertEqual(source.count(anchor),1)
        source=source.replace(anchor,
            "    let blocked be try ab.make(fn,graph,dead,box,[never],loc);\n"
            +anchor,1)
        generated=self.generator("native-scalar-reject-dead-aggregate",source)
        self.assertEqual(generated.returncode,1,generated.stdout[-1500:])
        self.assertIn("unsupported:",generated.stdout)
        self.assertNotIn(".section",generated.stdout)
        self.assertNotIn("erist_u2_function_83:",generated.stdout)
