"""Nonowning caches preserve validation, collision handling and invalidation."""
from pathlib import Path
import platform,shutil,subprocess,tempfile,unittest
from compiler.erist.cli import build_native
import test_freestanding_text_lifetimes as lifetime
from test_freestanding_graph_values import descriptors
ROOT=Path(__file__).resolve().parents[1]
FINISH='''
    call erist_rt_allocator_release_all
    testq %rax,%rax
    jne .Lcache_fail
    xorl %edi,%edi
    jmp erist_rt_exit
.Lcache_fail:
    movl $99,%edi
    jmp erist_rt_exit
'''
@unittest.skipUnless(platform.system()=='Linux' and platform.machine().lower() in ('x86_64','amd64'),'owned Linux x86-64 caches')
class RuntimeLookupCacheHarness:
 @classmethod
 def setUpClass(cls):
  if not all(shutil.which(t) for t in ('as','ld','nm','readelf')):raise unittest.SkipTest('native tools unavailable')
  cls.temp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.temp.cleanup);cls.directory=Path(cls.temp.name)
  gen=cls.directory/'gen';assert build_native(ROOT/'src/graph_value_runtime.eri',gen,ROOT/'src')==0
  v=subprocess.run([gen],capture_output=True,text=True,timeout=30);assert (v.returncode,v.stderr)==(0,'');cls.runtime=v.stdout
 def probe(self,name,asm,runtime=None):
  v=lifetime.FreestandingTextLifetimeTests._link_run(self,self.directory,name,self.runtime if runtime is None else runtime,descriptors()+asm)
  self.assertEqual((v.returncode,v.stdout,v.stderr),(0,b'',b''))
class RuntimeLookupCacheTests(RuntimeLookupCacheHarness,unittest.TestCase):
  def test_owned_graph_exact_slot_roots_preserve_interior_and_fallback(self):
   # Independent observed owner-call count: exact slots were already traced,
   # but a true interior cell must still reach the original owner validation.
   old='erist_rt_graph_owner:\n'
   self.assertEqual(self.runtime.count(old),1)
   runtime=self.runtime.replace(old,old+'    incq .Lprobe_owner_calls(%rip)\n',1)
   self.probe('graph-exact-root-dedup',r'''
.text
.globl _start
_start:
    call evn_scope_enter
    movq %rax,%r12
    movl $1,%edi
    call erist_rt_graph_new_object
    movq %rax,%r14
    movl $7,%edi
    call evn_int
    movq %rax,%r13
    movq %r13,.Lprobe_roots(%rip)
    movq 8(%r14),%rax
    movq %rax,.Lprobe_roots+8(%rip)
    movq %r13,.Lprobe_roots+16(%rip)
    movq %r12,%rdi
    leaq .Lprobe_roots(%rip),%rsi
    leaq .Lprobe_classes(%rip),%rdx
    movl $3,%ecx
    call evn_bind_roots
    call erist_rt_graph_mark_roots
    cmpq $1,24(%r14)
    jne .Lcache_fail
    cmpq $1,.Lprobe_owner_calls(%rip)
    jne .Lcache_fail
    # If the index refuses an oversized slot set, run the original safe path.
    movq $4097,.Lvalue_slot_count(%rip)
    call erist_rt_graph_mark_roots
    cmpq $3,.Lprobe_owner_calls(%rip)
    jne .Lcache_fail
    movq $1,.Lvalue_slot_count(%rip)
    # Release the true interior key: object must now be unreachable.
    movq $0,.Lprobe_roots+8(%rip)
    call erist_rt_graph_mark_roots
    cmpq $0,24(%r14)
    jne .Lcache_fail
    cmpq $3,.Lprobe_owner_calls(%rip)
    jne .Lcache_fail
    call erist_rt_graph_sweep
    cmpq $0,.Lgraph_count(%rip)
    jne .Lcache_fail
'''+FINISH+'''
.bss
.p2align 3
.Lprobe_owner_calls:
.quad 0
.Lprobe_roots:
.zero 24
.section .rodata
.Lprobe_classes:
.byte 1,1,1
''',runtime=runtime)

 def test_region_page_cache_reuse_validation_and_release_all(self):
  rt=self.runtime.replace('.Lfree_region_scan:\n','.Lfree_region_scan:\n    incq .Lcache_scans(%rip)\n',1)
  asm='''
.text
.globl _start
_start:
    leaq .Lcache_allocations(%rip),%r13
    xorl %r12d,%r12d
.Lcache_allocate:
    movl $70000,%edi
    call erist_rt_alloc
    testq %rax,%rax
    je .Lcache_fail
    movq %rax,(%r13,%r12,8)
    incq %r12
    cmpq $128,%r12
    jb .Lcache_allocate
    xorl %r12d,%r12d
.Lcache_cold_free:
    movq (%r13,%r12,8),%rdi
    call erist_rt_free
    testq %rax,%rax
    jne .Lcache_fail
    incq %r12
    cmpq $128,%r12
    jb .Lcache_cold_free
    xorl %r12d,%r12d
.Lcache_reallocate:
    movl $70000,%edi
    call erist_rt_alloc
    testq %rax,%rax
    je .Lcache_fail
    movq %rax,(%r13,%r12,8)
    incq %r12
    cmpq $128,%r12
    jb .Lcache_reallocate
    movq $0,.Lcache_scans(%rip)
    xorl %r12d,%r12d
.Lcache_warm_free:
    # Bypass the single-region shortcut to exercise the page cache itself.
    movq $0,.Lalloc_free_cache_region(%rip)
    movq (%r13,%r12,8),%rdi
    call erist_rt_free
    testq %rax,%rax
    jne .Lcache_fail
    incq %r12
    cmpq $128,%r12
    jb .Lcache_warm_free
    cmpq $512,.Lcache_scans(%rip)
    ja .Lcache_fail
    # A cached region must not permit double free or damaged block metadata.
    movq (%r13),%rdi
    call erist_rt_free
    cmpq $-1,%rax
    jne .Lcache_fail
    movl $70000,%edi
    call erist_rt_alloc
    movq %rax,%r14
    movq -32(%r14),%r15
    movq $0,-32(%r14)
    movq $0,.Lalloc_free_cache_region(%rip)
    movq %r14,%rdi
    call erist_rt_free
    cmpq $-1,%rax
    jne .Lcache_fail
    movq %r15,-32(%r14)
    movq %r14,%rdi
    call erist_rt_free
    testq %rax,%rax
    jne .Lcache_fail
    # A different cached page tag must take the checked fallback.
    leaq .Lalloc_page_keys(%rip),%rdi
    movl $4096,%ecx
    movq $1,%rax
    rep stosq
    movl $70000,%edi
    call erist_rt_alloc
    movq %rax,%r14
    movq $0,.Lalloc_free_cache_region(%rip)
    movq %rax,%rdi
    call erist_rt_free
    testq %rax,%rax
    jne .Lcache_fail
    call erist_rt_allocator_release_all
    testq %rax,%rax
    jne .Lcache_fail
    leaq .Lalloc_page_keys(%rip),%rdi
    movl $12288,%ecx
    xorl %eax,%eax
    repe scasq
    jne .Lcache_fail
    movl $128,%edi
    call erist_rt_alloc
    testq %rax,%rax
    je .Lcache_fail
    movq %rax,%rdi
    call erist_rt_free
    testq %rax,%rax
    jne .Lcache_fail
'''+FINISH+'''
.bss
.p2align 3
.Lcache_allocations:
.zero 1024
.Lcache_scans:
.quad 0
'''
  self.probe('region-cache',asm,rt)
 def test_graph_index_geometric_growth_owner_validation_and_reclamation(self):
  rt=self.runtime.replace('.Lg_index_allocate:\n','.Lg_index_allocate:\n    incq .Lcache_index_allocations(%rip)\n',1)
  asm='''
.text
.globl _start
_start:
    movl $100,%r14d
.Lcache_growing_index:
    movl $1,%edi
    call erist_rt_graph_new_object
    movq %rax,%r12
    call erist_rt_graph_prepare_index
    leaq 64(%r12),%rdi
    call erist_rt_graph_owner
    cmpq %r12,%rax
    jne .Lcache_fail
    decq %r14
    jne .Lcache_growing_index
    cmpq $12,.Lcache_index_allocations(%rip)
    ja .Lcache_fail
    call erist_rt_text_collect
    call erist_rt_graph_live_objects
    testq %rax,%rax
    jne .Lcache_fail
    cmpq $0,.Lgraph_index(%rip)
    jne .Lcache_fail
    cmpq $0,.Lgraph_index_capacity(%rip)
    jne .Lcache_fail
    leaq 64(%r12),%rdi
    call erist_rt_graph_owner
    testq %rax,%rax
    jne .Lcache_fail
'''+FINISH+'''
.bss
.Lcache_index_allocations:
.quad 0
'''
  self.probe('graph-index-growth',asm,rt)

 def test_pooled_text_bases_distribute_without_page_clustering(self):
  asm='''
.text
.globl _start
_start:
    leaq .Lhash_keys(%rip),%r13
    xorl %r12d,%r12d
.Lhash_construct:
    leaq .Lhash_text(%rip),%rdi
    movl $4,%esi
    call evn_text
    movq 16(%rax),%rax
    movq %rax,(%r13,%r12,8)
    incq %r12
    cmpq $256,%r12
    jb .Lhash_construct
    movq $0,.Ltext_registry_probes(%rip)
    xorl %r12d,%r12d
.Lhash_find:
    movq (%r13,%r12,8),%rdi
    call erist_rt_text_registry_find
    testq %rax,%rax
    je .Lcache_fail
    movq (%r13,%r12,8),%rcx
    cmpq %rcx,8(%rax)
    jne .Lcache_fail
    incq %r12
    cmpq $256,%r12
    jb .Lhash_find
    # Page-only hashing chains about fifteen pooled slices together per page.
    # This generous bound measures lookup work without a wall-clock threshold.
    cmpq $1024,.Ltext_registry_probes(%rip)
    ja .Lcache_fail
.Lhash_drop:
    movq .Lvalue_slots(%rip),%rdi
    testq %rdi,%rdi
    je .Lhash_sweep
    movq 32(%rdi),%rax
    movq %rax,.Lvalue_slots(%rip)
    decq .Lvalue_slot_count(%rip)
    call erist_rt_free
    testq %rax,%rax
    jne .Lcache_fail
    jmp .Lhash_drop
.Lhash_sweep:
    call erist_rt_text_collect
    call erist_rt_text_live_buffers
    testq %rax,%rax
    jne .Lcache_fail
'''+FINISH+'''
.bss
.p2align 3
.Lhash_keys:
.zero 2048
.section .rodata
.Lhash_text:
.ascii "hash"
'''
  self.probe('text-slice-hash',asm)
