"""Canonical optional List-i64 profile -> emitted native code -> owned GC."""
from pathlib import Path
import subprocess
import unittest
import platform
import re
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
                self.assertEqual(result.returncode,1)
                self.assertIn(b'List index out of bounds' if not oom else b'out of memory',result.stderr)
                if not oom: self.assertIn(b'list-probe:1:1: ',result.stderr)

    def test_malformed_profile_emits_no_native_assembly(self):
        root=self.directory/'canonical-list-negative';root.mkdir()
        (root/'compiler').symlink_to(ROOT/'src/compiler',target_is_directory=True)
        fixture=(ROOT/'tests/fixtures/u2_list_i64.eri').read_text()
        fixture='import compiler.u1_words as words;\n'+fixture
        for mutation in [
            'managedList=managed.text(managedTable);',
            'managedTable.version=2;',
            'data.declarations.frozen=false; try words.set(data.declarations,read,5,2); data.declarations.frozen=true;',
            'data.declarations.frozen=false; try words.set(data.declarations,read,4,0); data.declarations.frozen=true;',
            'fn.instructions.frozen=false; try words.set(fn.instructions,read,0,43); fn.instructions.frozen=true;',
        ]:
            with self.subTest(mutation=mutation):
                source=fixture.replace(' try lists.emitManaged(', ' '+mutation+'\n try lists.emitManaged(')
                src=root/'app.eri';binary=root/'generator';src.write_text(source)
                self.assertEqual(build_native(src,binary,root),0)
                emit=subprocess.run([str(binary)],capture_output=True,text=True,timeout=60)
                self.assertEqual(emit.returncode,1)
                self.assertNotIn('.text',emit.stdout)
                self.assertNotIn('.section',emit.stdout)

    def test_loop_carried_snapshots_and_parallel_swap(self):
        root=self.directory/'canonical-list-cfg';root.mkdir()
        (root/'compiler').symlink_to(ROOT/'src/compiler',target_is_directory=True)
        for fixture_name,expression,expected in [
            ('loop','oldCount',1),('loop','newCount',3),
            ('swap','left',20),('swap','right',10),
        ]:
            with self.subTest(fixture=fixture_name,expression=expression):
                fixture=(ROOT/f'tests/fixtures/u2_list_i64_{fixture_name}.eri').read_text()
                original='oldCount' if fixture_name=='loop' else 'left'
                fixture=fixture.replace('fn,done,['+original+'],loc','fn,done,['+expression+'],loc')
                src=root/'app.eri';binary=root/'generator';src.write_text(fixture)
                self.assertEqual(build_native(src,binary,root),0)
                emit=subprocess.run([str(binary)],capture_output=True,text=True,timeout=60)
                self.assertEqual((emit.returncode,emit.stderr),(0,''),emit.stdout)
                self.assertIn('erist_u2_edge_',emit.stdout)
                # A CFG edge must clear at least one dead managed slot only
                # after its simultaneous captures/stores and before jumping.
                if fixture_name == 'loop' and expression == 'oldCount':
                    parts=re.split(r'erist_u2_edge_\\d+_\\d+:\\n',emit.stdout)[1:]
                    edge_bodies=[part.split('jmp erist_u2_block_',1)[0]
                                 for part in parts if 'jmp erist_u2_block_' in part]
                    self.assertTrue(edge_bodies)
                    self.assertTrue(any(re.search(r'movq \\$0,\\d+\\(%rsp\\)',p)
                                        for p in edge_bodies),
                                    'no dead List roots retired on CFG edges')
                    self.assertIn('call erist_rt_text_collect',emit.stdout)
                starter=f'\n.text\n.globl _start\n_start:\n call erist_u2_list_entry\n cmpq ${expected},%rax\n jne .Lgraph_test_fail\n jmp .Lgraph_finish\n'
                result=self.run_probe('cfg-'+fixture_name+'-'+expression,emit.stdout+starter+graph_tests.FINISH)
                self.assertEqual((result.returncode,result.stdout,result.stderr),(0,b'',b''))

    def test_runtime_descriptors_and_independent_frame_layout(self):
        root=self.directory/'canonical-list-layout';root.mkdir()
        (root/'compiler').symlink_to(ROOT/'src/compiler',target_is_directory=True)
        src=root/'app.eri';binary=root/'generator'
        src.write_text((ROOT/'tests/fixtures/u2_list_i64.eri').read_text())
        self.assertEqual(build_native(src,binary,root),0)
        emit=subprocess.run([str(binary)],capture_output=True,text=True,timeout=60)
        self.assertEqual((emit.returncode,emit.stderr),(0,''))
        classes=emit.stdout.split('.text',1)[0]
        self.assertEqual(classes.count('.byte 1\n'),14)
        entry=emit.stdout.split('erist_u2_list_entry:',1)[1].split('call evn_scope_enter',1)[0]
        zeros=[int(x) for x in re.findall(r'movq \$0,(\d+)\(%rsp\)',entry)]
        self.assertEqual(zeros,list(range(0,14*8,8)))
        frame=int(re.search(r'subq \$(\d+),%rsp',entry)[1])
        self.assertEqual(frame%16,8)
        self.assertGreaterEqual(frame,14*16+16)
        starter='\n.text\n.globl _start\n_start:\n call erist_u2_list_entry\n movl $99,%edi\n jmp erist_rt_exit\n'
        wrong=graph_tests.descriptors().replace('.long 7,1\n','.long 7,4\n')
        self.assertNotEqual(wrong,graph_tests.descriptors())
        result=self.run_probe('wrong-runtime-descriptor',emit.stdout+starter+wrong,types=False)
        self.assertEqual(result.returncode,1)
        self.assertIn(b'internal',result.stderr)

    def test_malformed_cfg_edge_emits_nothing(self):
        root=self.directory/'canonical-list-bad-edge';root.mkdir()
        (root/'compiler').symlink_to(ROOT/'src/compiler',target_is_directory=True)
        fixture='import compiler.u1_words as words;\n'+(ROOT/'tests/fixtures/u2_list_i64_loop.eri').read_text()
        mutation='fn.arguments.frozen=false; try words.set(fn.arguments,read,0,0); fn.arguments.frozen=true;'
        source=fixture.replace(' try lists.emitManaged(', ' '+mutation+'\n try lists.emitManaged(')
        src=root/'app.eri';binary=root/'generator';src.write_text(source)
        self.assertEqual(build_native(src,binary,root),0)
        emit=subprocess.run([str(binary)],capture_output=True,text=True,timeout=60)
        self.assertEqual(emit.returncode,1)
        self.assertNotIn('.section',emit.stdout)
