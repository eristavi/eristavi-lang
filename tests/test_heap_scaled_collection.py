"""Safe-point budget scales with the retained heap and resets after reclamation."""
import test_runtime_lookup_caches as caches
class HeapScaledCollectionTests(caches.RuntimeLookupCacheTests):
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
    cmpq $100000,.Lgraph_safe_budget(%rip)
    jne .Lcache_fail
    # The first safe point is still below the new interval; the second collects.
    movq .Ltext_collections(%rip),%r13
    movq $1,.Ltext_heap_dirty(%rip)
    movq $99998,.Lgraph_safe_since(%rip)
    xorl %edi,%edi
    call erist_rt_text_safe_point
    cmpq .Ltext_collections(%rip),%r13
    jne .Lcache_fail
    cmpq $200000,.Lgraph_count(%rip)
    jne .Lcache_fail
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
    call erist_rt_allocator_release_all
    testq %rax,%rax
    jne .Lcache_fail
    xorl %edi,%edi
    jmp erist_rt_exit
.Lcache_fail:
    movl $99,%edi
    jmp erist_rt_exit
''')
