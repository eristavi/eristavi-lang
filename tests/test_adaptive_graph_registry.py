"""Adaptive registry publication, exact membership and empty-heap reclamation."""
import unittest
import test_runtime_lookup_caches as caches
class AdaptiveGraphRegistryTests(caches.RuntimeLookupCacheHarness,unittest.TestCase):
 def scenario(self,fail_growth):
  rt=self.runtime
  if fail_growth:
   before='    leaq (,%r14,8),%rdi\n    call erist_rt_alloc\n'
   self.assertEqual(rt.count(before),1)
   rt=rt.replace(before,'    xorl %eax,%eax\n',1)
  mask=8191 if fail_growth else 131071
  self.probe('graph-growth-'+str(fail_growth),f'''
.text
.globl _start
_start:
    leaq .Ladaptive_objects(%rip),%r13
    xorl %r12d,%r12d
.Ladaptive_new:
    xorl %edi,%edi
    call erist_rt_graph_new_object
    movq %rax,(%r13,%r12,8)
    movq $1,24(%rax)
    incq %r12
    cmpq $70000,%r12
    jne .Ladaptive_continue
    call erist_rt_graph_sweep
.Ladaptive_continue:
    cmpq $140000,%r12
    jb .Ladaptive_new
    call erist_rt_graph_sweep
    cmpq ${mask},.Lgraph_mask(%rip)
    jne .Lcache_fail
    xorl %r12d,%r12d
.Ladaptive_find:
    movq (%r13,%r12,8),%rdi
    call erist_rt_graph_find
    cmpq (%r13,%r12,8),%rax
    jne .Lcache_fail
    movq %rax,%rdi
    incq %rdi
    call erist_rt_graph_find
    testq %rax,%rax
    jne .Lcache_fail
    movq (%r13,%r12,8),%rax
    movq $0,24(%rax)
    incq %r12
    cmpq $140000,%r12
    jb .Ladaptive_find
    call erist_rt_graph_sweep
    cmpq $0,.Lgraph_count(%rip)
    jne .Lcache_fail
    cmpq $0,.Lgraph_table(%rip)
    jne .Lcache_fail
    cmpq $8191,.Lgraph_mask(%rip)
    jne .Lcache_fail
    movq (%r13),%rdi
    call erist_rt_graph_find
    testq %rax,%rax
    jne .Lcache_fail
    xorl %edi,%edi
    call erist_rt_graph_new_object
    movq %rax,%rdi
    call erist_rt_graph_find
    testq %rax,%rax
    je .Lcache_fail
    call erist_rt_graph_sweep
    call erist_rt_allocator_release_all
    testq %rax,%rax
    jne .Lcache_fail
    xorl %edi,%edi
    jmp erist_rt_exit
.Lcache_fail:
    movl $99,%edi
    jmp erist_rt_exit
.bss
.p2align 3
.Ladaptive_objects:
.zero 1120000
''',rt)
 def test_growth_exact_membership_and_reclamation(self):self.scenario(False)
 def test_failed_growth_keeps_exact_registry(self):self.scenario(True)
