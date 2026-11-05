"""Optional canonical U2 Text/Unicode17 native runtime tests."""
from pathlib import Path
import platform
import subprocess
import unittest
from compiler.erist.cli import build_native
import test_freestanding_graph_values as graph

ROOT=Path(__file__).resolve().parents[1]

def unicode_descriptors():
    original=graph.descriptors()
    marker='.section .rodata\n'
    assert original.count(marker)==1
    views=''.join(f'.long 12,0\n.quad .Lu2_view_{n},0,0\n'
                  for n in ('bytes','scalars','characters'))
    names=''.join(f'.Lu2_view_{n}:\n.asciz "{n}"\n'
                  for n in ('bytes','scalars','characters'))
    return original.replace(marker,views+marker+names,1)

@unittest.skipUnless(platform.system()=='Linux' and
    platform.machine().lower() in ('x86_64','amd64'),
    'owned Unicode17 Text native slice requires Linux x86-64')
class U2TextUnicode17Tests(unittest.TestCase):
    setUpClass=classmethod(graph.FreestandingGraphValueTests.setUpClass.__func__)
    run_probe=graph.FreestandingGraphValueTests.run_probe

    def generator(self,folder,source):
        root=self.directory/folder
        root.mkdir()
        (root/'compiler').symlink_to(ROOT/'src/compiler',target_is_directory=True)
        app=root/'app.eri'
        app.write_text(source,encoding='utf-8')
        binary=root/'generator'
        self.assertEqual(build_native(app,binary,root),0)
        return subprocess.run([str(binary)],capture_output=True,text=True,timeout=90)

    def test_unicode17_text_counts_copy_scalar_equality_and_gc(self):
        original=(ROOT/'tests/fixtures/u2_text_unicode17.eri').read_text(encoding='utf-8')
        cases=[
            ('accentBytes',3,False),('accentScalars',2,False),
            ('accentCharacters',1,False),('emojiBytes',11,False),
            ('emojiScalars',3,False),('emojiCharacters',1,False),
            ('unequal',0,True),('equal',1,True),
            ('accentByte0',101,False),('accentByte1',204,False),
            ('accentScalarMatches',1,True),('accentGraphemeMatches',1,True),
            ('emojiByte0',240,False),('emojiScalarMatches',1,True),
            ('emojiGraphemeMatches',1,True),('normalizedMatches',1,True),
            ('normalizedOriginalMatches',0,True),
        ]
        for expression,expected,boolean in cases:
            with self.subTest(expression=expression):
                source=original.replace('[accentCharacters],loc);',
                                        '['+expression+'],loc);')
                if boolean:
                    source=source.replace(
                        'let entrySig be try meta.signature(data,p,[],[meta.i64()]);',
                        'let entrySig be try meta.signature(data,p,[],[meta.pred()]);')
                emitted=self.generator('text-'+expression,source)
                self.assertEqual((emitted.returncode,emitted.stderr),
                                 (0,''),emitted.stdout)
                # Prevent a comment or output-boundary bug from swallowing the
                # first native ABI guard and leaving an unconditional jne.
                self.assertIn('    cmpl $1,ev_types+32(%rip)',emitted.stdout)
                for symbol in ('erist_rt_unicode_from_scalar',
                               'erist_rt_text_concat','erist_rt_view_count',
                               'erist_rt_view_index','erist_rt_unicode_normalize_nfc',
                               'erist_rt_text_collect','evn_bind_roots'):
                    self.assertIn('call '+symbol,emitted.stdout)
                start=f'''
.text
.globl _start
_start:
    call erist_u2_text_entry
    cmpq ${expected},%rax
    jne .Lgraph_test_fail
    jmp .Lgraph_finish
'''
                try:
                    result=self.run_probe('text-'+expression,
                        emitted.stdout+start+graph.FINISH+unicode_descriptors(),
                        types=False)
                except subprocess.CalledProcessError as exc:
                    self.fail('native linker error: '+(exc.stderr or b'').decode(
                        'utf-8',errors='replace'))
                self.assertEqual((result.returncode,result.stdout,result.stderr),
                                 (0,b'',b''))

    def test_malformed_descriptor_and_import_refuse_before_assembly(self):
        original=(ROOT/'tests/fixtures/u2_text_unicode17.eri').read_text(encoding='utf-8')
        for name,mutation in (
            ('type','registry.version=2;'),
            ('import','data.declarations.frozen=false;'),
        ):
            with self.subTest(name=name):
                source=original.replace('    try textNative.emitManaged(',
                    '    '+mutation+'\n    try textNative.emitManaged(')
                emitted=self.generator('bad-'+name,source)
                self.assertEqual(emitted.returncode,1,emitted.stdout)
                self.assertNotIn('.text',emitted.stdout)
                self.assertNotIn('.section',emitted.stdout)

    def test_conservative_text_roots_survive_cfg_loop_backedges_and_gc(self):
        original=(ROOT/'tests/fixtures/u2_text_unicode17_cfg.eri').read_text(encoding='utf-8')
        for expression,expected in (('oldCount',1),('newCount',3)):
            with self.subTest(expression=expression):
                source=original.replace('[oldCount],loc);','['+expression+'],loc);')
                emitted=self.generator('text-cfg-'+expression,source)
                self.assertEqual((emitted.returncode,emitted.stderr),(0,''),emitted.stdout)
                self.assertIn('erist_u2_text_block_4:',emitted.stdout)
                self.assertIn('erist_u2_text_edge_',emitted.stdout)
                self.assertIn('call erist_rt_text_collect',emitted.stdout)
                start=f'''
.text
.globl _start
_start:
    call erist_u2_text_entry
    cmpq ${expected},%rax
    jne .Lgraph_test_fail
    jmp .Lgraph_finish
'''
                result=self.run_probe('text-cfg-'+expression,
                    emitted.stdout+start+graph.FINISH+unicode_descriptors(),
                    types=False)
                self.assertEqual((result.returncode,result.stdout,result.stderr),
                                 (0,b'',b''))

    def test_precise_cfg_text_root_retirement_before_collection(self):
        original=(ROOT/'tests/fixtures/u2_text_unicode17_cfg.eri').read_text(encoding='utf-8')
        # Annotate the actual canonical ValueIds; no hardcoded frame offsets.
        source=original.replace('import compiler.u1_meta as meta;',
            'import compiler.u1_meta as meta;\nimport compiler.format as format;',1)
        anchor='    try textNative.emitManaged(fn,graph,carrier,read,registry,textType);'
        self.assertIn(anchor,source)
        source=source.replace(anchor,anchor+
            '\n    output(".set erist_u2_text_growing_slot, "+format.integer((growing.index-1)*8));'+
            '\n    output(".set erist_u2_text_snapshot_slot, "+format.integer((snapshot.index-1)*8));'+
            '\n    output(".set erist_u2_text_accent_slot, "+format.integer((accent.index-1)*8));',1)
        emitted=self.generator('precise-text-cfg-roots',source)
        self.assertEqual((emitted.returncode,emitted.stderr),(0,''),emitted.stdout)
        import re
        def offset(label):
            match=re.search(r'^\.set '+label+r', (\d+)
        original=(ROOT/'tests/fixtures/u2_text_unicode17_recursive.eri').read_text(encoding='utf-8')
        emitted=self.generator('recursive-text',original)
        self.assertEqual((emitted.returncode,emitted.stderr),(0,''),emitted.stdout)
        for fragment in ('call erist_u2_text_entry',
                         'erist_u2_text_depth:',
                         'incq erist_u2_text_depth(%rip)',
                         'decq erist_u2_text_depth(%rip)',
                         'call evn_bind_roots',
                         'call erist_rt_text_collect'):
            self.assertIn(fragment,emitted.stdout)
        # Outer scope retains the initial Text while boxing the depth
        # argument. Recursion then owns a separate registered native frame
        # per invocation; all levels trigger collection and remain live.
        # Bottom frame has 1+depth scalars; unwinding adds the Text
        # length from every parent frame: sum(1..depth).
        for depth in (0,1,3,8,31):
            with self.subTest(depth=depth):
                start=f'''
.text
.globl _start
_start:
    subq $48,%rsp
    movq $0,0(%rsp)
    call evn_scope_enter
    movq %rax,8(%rsp)
    movq %rax,%rdi
    movq %rsp,%rsi
    leaq .Lu2_recursive_classes(%rip),%rdx
    movl $1,%ecx
    call evn_bind_roots
    movl $101,%edi
    call erist_rt_unicode_from_scalar
    movq %rax,0(%rsp)
    movl ${depth},%edi
    call evn_int
    movq %rax,%rsi
    movq 0(%rsp),%rdi
    call erist_u2_text_entry
    cmpq ${1+depth+depth*(depth+1)//2},%rax
    jne .Lgraph_test_fail
    call evn_void
    movq %rax,%rsi
    movq 8(%rsp),%rdi
    call evn_scope_leave
    addq $48,%rsp
    cmpq $0,erist_u2_text_depth(%rip)
    jne .Lgraph_test_fail
    jmp .Lgraph_finish
.section .rodata
.Lu2_recursive_classes:
.byte 1
'''
                result=self.run_probe('recursive-text-'+str(depth),
                    emitted.stdout+start+graph.FINISH+unicode_descriptors(),
                    types=False)
                self.assertEqual((result.returncode,result.stdout,result.stderr),
                                 (0,b'',b''))
        fault_start=r'''
.text
.globl _start
_start:
    subq $48,%rsp
    movq $0,0(%rsp)
    call evn_scope_enter
    movq %rax,8(%rsp)
    movq %rax,%rdi
    movq %rsp,%rsi
    leaq .Lu2_recursive_classes(%rip),%rdx
    movl $1,%ecx
    call evn_bind_roots
    movl $101,%edi
    call erist_rt_unicode_from_scalar
    movq %rax,0(%rsp)
    movl $32,%edi
    call evn_int
    movq %rax,%rsi
    movq 0(%rsp),%rdi
    call erist_u2_text_entry
    movl $99,%edi
    jmp erist_rt_exit
.section .rodata
.Lu2_recursive_classes:
.byte 1
'''
        limit=self.run_probe('recursive-text-ceiling',
            emitted.stdout+fault_start+unicode_descriptors(),types=False)
        self.assertEqual(limit.returncode,1)
        self.assertIn(b'Eristavi runtime fault:',limit.stderr)

    def test_all_text_view_bounds_are_terminal_and_exact(self):
        original=(ROOT/'tests/fixtures/u2_text_unicode17.eri').read_text(encoding='utf-8')
        # Each invalid lookup must preserve the established terminal bounds
        # fault, not silently clamp or return a checked-failure value.
        cases=(
            ('bytes-negative','f9,[decomposed,one]','f9,[decomposed,negative]'),
            ('bytes-end','f9,[decomposed,one]','f9,[decomposed,three]'),
            ('scalars-negative','f10,[decomposed,one]','f10,[decomposed,negative]'),
            ('scalars-end','f10,[decomposed,one]','f10,[decomposed,two]'),
            ('graphemes-negative','f11,[decomposed,zero]','f11,[decomposed,negative]'),
            ('graphemes-end','f11,[decomposed,zero]','f11,[decomposed,one]'),
        )
        for label,old,new in cases:
            with self.subTest(label=label):
                self.assertIn(old,original)
                emitted=self.generator('view-bounds-'+label,original.replace(old,new,1))
                self.assertEqual((emitted.returncode,emitted.stderr),(0,''),emitted.stdout)
                start='''
.text
.globl _start
_start:
    call erist_u2_text_entry
    movl $99,%edi
    jmp erist_rt_exit
'''
                result=self.run_probe('view-bounds-'+label,
                    emitted.stdout+start+unicode_descriptors(),types=False)
                self.assertEqual((result.returncode,result.stdout,result.stderr),
                    (1,b'',b'Eristavi runtime fault: Text view index out of bounds\n'))

    def test_surrogate_scalar_terminal_fault(self):
        original=(ROOT/'tests/fixtures/u2_text_unicode17.eri').read_text(encoding='utf-8')
        source=original.replace(
            'let composed be try build.integer(fn,block,233,loc);',
            'let composed be try build.integer(fn,block,55296,loc);')
        emitted=self.generator('bad-scalar',source)
        self.assertEqual((emitted.returncode,emitted.stderr),(0,''),emitted.stdout)
        start='''
.text
.globl _start
_start:
    call erist_u2_text_entry
    movl $99,%edi
    jmp erist_rt_exit
'''
        result=self.run_probe('text-invalid-unicode',
            emitted.stdout+start+unicode_descriptors(),types=False)
        self.assertEqual(result.returncode,1)
        self.assertIn(b'invalid Unicode scalar value',result.stderr)
,emitted.stdout,re.M)
            self.assertIsNotNone(match,label)
            return int(match.group(1))
        grow=offset('erist_u2_text_growing_slot')
        kept=offset('erist_u2_text_snapshot_slot')
        accent=offset('erist_u2_text_accent_slot')
        self.assertEqual(len({grow,kept,accent}),3)
        body=emitted.stdout.split('erist_u2_text_block_3:',1)[1].split(
            'erist_u2_text_block_4:',1)[0]
        concat=body.index('call erist_rt_text_concat')
        retired=body.index(f'movq $0,{grow}(%rsp)',concat)
        collect=body.index('call erist_rt_slots_collect',retired)
        self.assertLess(concat,retired)
        self.assertLess(retired,collect)
        self.assertNotIn(f'movq $0,{kept}(%rsp)',body[concat:collect])
        self.assertNotIn(f'movq $0,{accent}(%rsp)',body[concat:collect])
        # Direct physical read of the registered native frame at the first
        # collection safepoint, then execute the REAL owned collector.
        # A dead concat input must be unrooted; both a phi-carried
        # snapshot and a cross-block captured accent must remain registered.
        inspection='\n'.join((
            f'cmpq $0,{grow}(%rsp)',
            'jne .Lgraph_test_fail',
            f'cmpq $0,{kept}(%rsp)',
            'je .Lgraph_test_fail',
            f'cmpq $0,{accent}(%rsp)',
            'je .Lgraph_test_fail',
            'call erist_rt_slots_collect'))
        assembly=emitted.stdout.replace('call erist_rt_slots_collect',
                                         inspection,1)
        self.assertNotEqual(assembly,emitted.stdout)
        start='''
.text
.globl _start
_start:
    call erist_u2_text_entry
    cmpq $1,%rax
    jne .Lgraph_test_fail
    jmp .Lgraph_finish
'''
        result=self.run_probe('precise-text-cfg-roots',
            assembly+start+graph.FINISH+unicode_descriptors(),types=False)
        self.assertEqual((result.returncode,result.stdout,result.stderr),
                         (0,b'',b''))

    def test_recursive_text_frames_keep_caller_roots_across_gc(self):
        original=(ROOT/'tests/fixtures/u2_text_unicode17_recursive.eri').read_text(encoding='utf-8')
        emitted=self.generator('recursive-text',original)
        self.assertEqual((emitted.returncode,emitted.stderr),(0,''),emitted.stdout)
        for fragment in ('call erist_u2_text_entry',
                         'erist_u2_text_depth:',
                         'incq erist_u2_text_depth(%rip)',
                         'decq erist_u2_text_depth(%rip)',
                         'call evn_bind_roots',
                         'call erist_rt_text_collect'):
            self.assertIn(fragment,emitted.stdout)
        # Outer scope retains the initial Text while boxing the depth
        # argument. Recursion then owns a separate registered native frame
        # per invocation; all levels trigger collection and remain live.
        # Bottom frame has 1+depth scalars; unwinding adds the Text
        # length from every parent frame: sum(1..depth).
        for depth in (0,1,3,8,31):
            with self.subTest(depth=depth):
                start=f'''
.text
.globl _start
_start:
    subq $48,%rsp
    movq $0,0(%rsp)
    call evn_scope_enter
    movq %rax,8(%rsp)
    movq %rax,%rdi
    movq %rsp,%rsi
    leaq .Lu2_recursive_classes(%rip),%rdx
    movl $1,%ecx
    call evn_bind_roots
    movl $101,%edi
    call erist_rt_unicode_from_scalar
    movq %rax,0(%rsp)
    movl ${depth},%edi
    call evn_int
    movq %rax,%rsi
    movq 0(%rsp),%rdi
    call erist_u2_text_entry
    cmpq ${1+depth+depth*(depth+1)//2},%rax
    jne .Lgraph_test_fail
    call evn_void
    movq %rax,%rsi
    movq 8(%rsp),%rdi
    call evn_scope_leave
    addq $48,%rsp
    cmpq $0,erist_u2_text_depth(%rip)
    jne .Lgraph_test_fail
    jmp .Lgraph_finish
.section .rodata
.Lu2_recursive_classes:
.byte 1
'''
                result=self.run_probe('recursive-text-'+str(depth),
                    emitted.stdout+start+graph.FINISH+unicode_descriptors(),
                    types=False)
                self.assertEqual((result.returncode,result.stdout,result.stderr),
                                 (0,b'',b''))
        fault_start=r'''
.text
.globl _start
_start:
    subq $48,%rsp
    movq $0,0(%rsp)
    call evn_scope_enter
    movq %rax,8(%rsp)
    movq %rax,%rdi
    movq %rsp,%rsi
    leaq .Lu2_recursive_classes(%rip),%rdx
    movl $1,%ecx
    call evn_bind_roots
    movl $101,%edi
    call erist_rt_unicode_from_scalar
    movq %rax,0(%rsp)
    movl $32,%edi
    call evn_int
    movq %rax,%rsi
    movq 0(%rsp),%rdi
    call erist_u2_text_entry
    movl $99,%edi
    jmp erist_rt_exit
.section .rodata
.Lu2_recursive_classes:
.byte 1
'''
        limit=self.run_probe('recursive-text-ceiling',
            emitted.stdout+fault_start+unicode_descriptors(),types=False)
        self.assertEqual(limit.returncode,1)
        self.assertIn(b'Eristavi runtime fault:',limit.stderr)

    def test_all_text_view_bounds_are_terminal_and_exact(self):
        original=(ROOT/'tests/fixtures/u2_text_unicode17.eri').read_text(encoding='utf-8')
        # Each invalid lookup must preserve the established terminal bounds
        # fault, not silently clamp or return a checked-failure value.
        cases=(
            ('bytes-negative','f9,[decomposed,one]','f9,[decomposed,negative]'),
            ('bytes-end','f9,[decomposed,one]','f9,[decomposed,three]'),
            ('scalars-negative','f10,[decomposed,one]','f10,[decomposed,negative]'),
            ('scalars-end','f10,[decomposed,one]','f10,[decomposed,two]'),
            ('graphemes-negative','f11,[decomposed,zero]','f11,[decomposed,negative]'),
            ('graphemes-end','f11,[decomposed,zero]','f11,[decomposed,one]'),
        )
        for label,old,new in cases:
            with self.subTest(label=label):
                self.assertIn(old,original)
                emitted=self.generator('view-bounds-'+label,original.replace(old,new,1))
                self.assertEqual((emitted.returncode,emitted.stderr),(0,''),emitted.stdout)
                start='''
.text
.globl _start
_start:
    call erist_u2_text_entry
    movl $99,%edi
    jmp erist_rt_exit
'''
                result=self.run_probe('view-bounds-'+label,
                    emitted.stdout+start+unicode_descriptors(),types=False)
                self.assertEqual((result.returncode,result.stdout,result.stderr),
                    (1,b'',b'Eristavi runtime fault: Text view index out of bounds\n'))

    def test_surrogate_scalar_terminal_fault(self):
        original=(ROOT/'tests/fixtures/u2_text_unicode17.eri').read_text(encoding='utf-8')
        source=original.replace(
            'let composed be try build.integer(fn,block,233,loc);',
            'let composed be try build.integer(fn,block,55296,loc);')
        emitted=self.generator('bad-scalar',source)
        self.assertEqual((emitted.returncode,emitted.stderr),(0,''),emitted.stdout)
        start='''
.text
.globl _start
_start:
    call erist_u2_text_entry
    movl $99,%edi
    jmp erist_rt_exit
'''
        result=self.run_probe('text-invalid-unicode',
            emitted.stdout+start+unicode_descriptors(),types=False)
        self.assertEqual(result.returncode,1)
        self.assertIn(b'invalid Unicode scalar value',result.stderr)
