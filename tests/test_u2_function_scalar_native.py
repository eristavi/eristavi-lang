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
        self.assertIn("movabsq $11,%rax",asm)
        self.assertIn("addq %rcx,%rax",asm)
        # The loop's self-edge has at least three independent staging moves
        # before ANY destination SSA parameter is overwritten.
        edge=asm.split(base+"_edge_2:",1)[1].split(
            "jmp "+base+"_block_",1)[0]
        self.assertGreaterEqual(edge.count("movq %rax,"),6)
        self.assertGreaterEqual(edge.count("(%rsp),%rax"),6)
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

    def test_sparse_unsigned_switch_parallel_edges(self):
        source=self.fixture()
        original=("    try ab.branch(fn,graph,loop,again,loop,[second,first,off],\n"
                  "        exit,[second,first],loc);")
        self.assertEqual(source.count(original),1)
        replacement=(
            "    let repeatEdge be try build.edge(fn,loop,[second,first,off]);\n"
            "    let negativeEdge be try build.edge(fn,exit,[first,second]);\n"
            "    let defaultEdge be try build.edge(fn,exit,[second,first]);\n"
            "    try build.switchInteger(fn,loop,first,[37,-1],"
            "[repeatEdge,negativeEdge],defaultEdge,loc);")
        source=source.replace(original,replacement,1)
        created=self.generator("native-scalar-switch",source)
        self.assertEqual((created.returncode,created.stderr),(0,""),
                         created.stdout[-2400:])
        asm=created.stdout
        self.assertIn("movabsq $-1,%rcx",asm)
        self.assertIn("movabsq $37,%rcx",asm)
        self.assertIn("erist_u2_function_83_edge_5:",asm)
        checks=((37,37,11),(8,11,8),(-1,-1,11))
        for index,(value,first,second) in enumerate(checks):
            body=(
                "\n.text\n.globl _start\n_start:\n"
                "    leaq .Lu2_cfg_input(%rip),%rdi\n"
                "    call erist_u2_function_83\n"
                "    movabsq $"+str(first)+",%rcx\n"
                "    cmpq %rcx,%rax\n"
                "    jne .Lgraph_test_fail\n"
                "    movabsq $"+str(second)+",%rcx\n"
                "    cmpq %rcx,%rdx\n"
                "    jne .Lgraph_test_fail\n"
                "    jmp .Lgraph_finish\n"
                ".section .rodata\n.p2align 3\n.Lu2_cfg_input:\n"
                ".quad "+str(value)+"\n")
            done=self.run_probe("u2-native-switch-"+str(index),
                                asm+body+graph.FINISH)
            self.assertEqual((done.returncode,done.stdout,done.stderr),
                             (0,b"",b""), (value,done.stderr))

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
