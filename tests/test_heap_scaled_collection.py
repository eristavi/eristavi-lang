"""Allocation-pressure GC respects retention, byte caps and forced deferral."""
import unittest
import test_runtime_lookup_caches as caches
class HeapScaledCollectionTests(caches.RuntimeLookupCacheHarness,unittest.TestCase):
 def test_large_heap_interval_and_empty_heap_reset(self):
  self.probe('heap-scaled-collection', '''
.text
.globl _start
_start:
    call erist_rt_graph_sweep
    cmpq $128,.Lgraph_safe_budget(%rip)
    jne .Lcache_fail
    xorl %r12d,%r12d
.Lbudget_new:
    xorl %edi,%edi
    call erist_rt_graph_new_object
    movq $1,24(%rax)
    incq %r12
    cmpq $200000,%r12
    jb .Lbudget_new
    call erist_rt_graph_sweep
    cmpq $200000,.Lgraph_count(%rip)
    jne .Lcache_fail
    cmpq $4096,.Lgraph_safe_budget(%rip)
    jne .Lcache_fail
    # All three counts were reset by the preceding explicit sweep.
    cmpq $0,.Lgraph_since_gc(%rip)
    jne .Lcache_fail
    cmpq $0,.Lgraph_alloc_since_gc(%rip)
    jne .Lcache_fail
    # Reclamation is paced by fresh allocation counts, NOT scalar visits.
    movq .Ltext_collections(%rip),%r13
    movq $1,.Ltext_heap_dirty(%rip)
    movq $4095,.Lgraph_since_gc(%rip)
    xorl %edi,%edi
    call erist_rt_text_safe_point
    cmpq .Ltext_collections(%rip),%r13
    jne .Lcache_fail
    cmpq $200000,.Lgraph_count(%rip)
    jne .Lcache_fail
    movq $4096,.Lgraph_since_gc(%rip)
    xorl %edi,%edi
    call erist_rt_text_safe_point
    incq %r13
    cmpq .Ltext_collections(%rip),%r13
    jne .Lcache_fail
    cmpq $0,.Lgraph_count(%rip)
    jne .Lcache_fail
    cmpq $0,.Lgraph_table(%rip)
    jne .Lcache_fail
    cmpq $128,.Lgraph_safe_budget(%rip)
    jne .Lcache_fail
    # Bound an allocation cycle by committed backing bytes too.
    movq .Ltext_collections(%rip),%r13
    movq $1,.Ltext_heap_dirty(%rip)
    movq $8388607,.Lgraph_alloc_since_gc(%rip)
    xorl %edi,%edi
    call erist_rt_text_safe_point
    cmpq .Ltext_collections(%rip),%r13
    jne .Lcache_fail
    movq $8388608,.Lgraph_alloc_since_gc(%rip)
    xorl %edi,%edi
    call erist_rt_text_safe_point
    incq %r13
    cmpq .Ltext_collections(%rip),%r13
    jne .Lcache_fail
    cmpq $0,.Lgraph_alloc_since_gc(%rip)
    jne .Lcache_fail
    # Even after pure root invalidation, periodic polling is bounded.
    movq $1,.Ltext_heap_dirty(%rip)
    movq $1048575,.Lgraph_safe_since(%rip)
    xorl %edi,%edi
    call erist_rt_text_safe_point
    incq %r13
    cmpq .Ltext_collections(%rip),%r13
    jne .Lcache_fail
    call erist_rt_allocator_release_all
    testq %rax,%rax
    jne .Lcache_fail
    xorl %edi,%edi
    jmp erist_rt_exit
.Lcache_fail:
    movl $99,%edi
    jmp erist_rt_exit
''')
