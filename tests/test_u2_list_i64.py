"""Canonical optional List-i64 profile -> emitted native code -> owned GC."""
from pathlib import Path
import subprocess
import unittest
import platform
from compiler.erist.cli import build_native
import test_freestanding_graph_values as graph_tests

ROOT=Path(__file__).resolve().parents[1]

@unittest.skipUnless(platform.system()=="Linux" and platform.machine().lower() in ("x86_64","amd64"), "owned List profile requires Linux x86-64")
class U2ListI64Tests(unittest.TestCase):
    setUpClass=classmethod(graph_tests.FreestandingGraphValueTests.setUpClass.__func__)
    run_probe=graph_tests.FreestandingGraphValueTests.run_probe
    def test_canonical_list_snapshots_native_roots_and_bounds(self):
        root=self.directory/'canonical-list';root.mkdir()
        (root/'compiler').symlink_to(ROOT/'src/compiler',target_is_directory=True)
        fixture=(ROOT/'tests/fixtures/u2_list_i64.eri').read_text()
        for expression,expected in [('old',10),('latest',20),('oldCount',1),('changedZero',20),('changedCount',2)]:
            with self.subTest(expression=expression):
                src=root/'app.eri';binary=root/'generator'
                src.write_text(fixture.replace('fn,b,[old],loc','fn,b,['+expression+'],loc'))
                self.assertEqual(build_native(src,binary,root),0)
                emit=subprocess.run([str(binary)],capture_output=True,text=True,timeout=60)
                self.assertEqual((emit.returncode,emit.stderr),(0,''))
                self.assertIn('call evn_bind_roots',emit.stdout)
                self.assertIn('call erist_rt_text_collect',emit.stdout)
                starter=f'''
.text
.globl _start
_start:
    call erist_u2_list_entry
    cmpq ${expected},%rax
    jne .Lgraph_test_fail
    jmp .Lgraph_finish
'''
                result=self.run_probe('canonical-list-'+expression,emit.stdout+starter+graph_tests.FINISH)
                self.assertEqual((result.returncode,result.stdout,result.stderr),(0,b'',b''))


    def test_native_bounds_and_allocation_failure_are_terminal(self):
        root=self.directory/'canonical-list-fault';root.mkdir()
        (root/'compiler').symlink_to(ROOT/'src/compiler',target_is_directory=True)
        fixture=(ROOT/'tests/fixtures/u2_list_i64.eri').read_text()
        for name,source,oom in [
            ('bounds',fixture.replace('fn,b,0,loc','fn,b,-1,loc'),False),
            ('oom',fixture,True),
        ]:
            with self.subTest(name=name):
                src=root/'app.eri';binary=root/'generator';src.write_text(source)
                self.assertEqual(build_native(src,binary,root),0)
                emit=subprocess.run([str(binary)],capture_output=True,text=True,timeout=60)
                self.assertEqual((emit.returncode,emit.stderr),(0,''))
                runtime=self.runtime
                if oom:
                    marker='erist_rt_graph_new_capacity:\n'
                    first,tail=runtime.split(marker,1)
                    self.assertIn('call erist_rt_alloc',tail)
                    runtime=first+marker+tail.replace('call erist_rt_alloc','xorq %rax,%rax',1)
                starter='\n.text\n.globl _start\n_start:\n call erist_u2_list_entry\n movl $99,%edi\n jmp erist_rt_exit\n'
                result=self.run_probe('canonical-list-'+name,emit.stdout+starter,runtime=runtime)
                self.assertNotIn(result.returncode,(0,99))
                self.assertIn(b'List index out of bounds' if not oom else b'out of memory',result.stderr)

    def test_malformed_profile_emits_no_native_assembly(self):
        root=self.directory/'canonical-list-negative';root.mkdir()
        (root/'compiler').symlink_to(ROOT/'src/compiler',target_is_directory=True)
        fixture=(ROOT/'tests/fixtures/u2_list_i64.eri').read_text()
        fixture='import compiler.u1_words as words;\n'+fixture
        for mutation in [
            'data.declarations.frozen=false; try words.set(data.declarations,read,5,2); data.declarations.frozen=true;',
            'data.declarations.frozen=false; try words.set(data.declarations,read,4,0); data.declarations.frozen=true;',
            'fn.instructions.frozen=false; try words.set(fn.instructions,read,0,43); fn.instructions.frozen=true;',
        ]:
            with self.subTest(mutation=mutation):
                source=fixture.replace(' try lists.emit(', ' '+mutation+'\n try lists.emit(')
                src=root/'app.eri';binary=root/'generator';src.write_text(source)
                self.assertEqual(build_native(src,binary,root),0)
                emit=subprocess.run([str(binary)],capture_output=True,text=True,timeout=60)
                self.assertEqual(emit.returncode,1)
                self.assertNotIn('.text',emit.stdout)
                self.assertNotIn('.section',emit.stdout)
