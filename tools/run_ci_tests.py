#!/usr/bin/env python3
"""Run the ordinary suite and retain machine-readable outcomes, including skips."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import platform
import sys
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'tests'))

# Fast PR feedback only. The full test discovery below remains unchanged.
SMOKE_TESTS=(
    'test_universal_ir.UniversalIRTests.test_universal_ir_contains_function_contract_and_call',
    'test_universal_ir.UniversalIRTests.test_universal_ir_has_explicit_checked_arithmetic_and_control_flow',
    'test_u1_foundation.U1FoundationTests.test_accounting_metadata_and_builder_on_c_bootstrap',
    'test_u1_calls.U1CallContracts.test_direct_call_declarations_and_verifier',
    'test_u1_module.U1ModuleBindingTests.test_declarations_bind_exact_verified_bodies',
    'test_u1_execution.U1CallExecutionTests.test_recursive_frames_effects_and_versioned_imports',
    'test_u1_native.U1NativeTests',
    'test_u1_integer_execution.U1IntegerExecutionTests.test_integer_recursion_switch_promotion_and_fault_traces',
    'test_u1_narrow_execution.U1NarrowExecutionTests.test_independent_canonical_narrow_execution_and_faults',
    # U1a #77 acceptance: exact owner-partition backing under both the C bootstrap
    # and freestanding owned runtime, independently predicted large radix/scratch
    # shapes, and the retained PR #103 C-heap evidence boundary.
    'test_u1_owner_physical.U1OwnerPhysicalTests',
    'test_native_runtime_lifetimes.NativeRuntimeLifetimeTests.test_native_handler_and_abandoned_call_allocations_are_reclaimed',
    # Owned runtime GC optimization conformance: real graph, interior/slot roots,
    # bounded static scratch, forced pressure, and allocation-refusal fallbacks.
    'test_heap_scaled_collection.HeapScaledCollectionTests.test_large_heap_interval_and_empty_heap_reset',
    'test_runtime_lookup_caches.RuntimeLookupCacheTests.test_owned_graph_exact_slot_roots_preserve_interior_and_fallback',
    'test_runtime_lookup_caches.RuntimeLookupCacheTests.test_owned_slot_scratch_reuse_zeroing_nesting_and_refusal',
    'test_freestanding_text_roots.FreestandingTextRootTests.test_registered_roots_bound_loop_slots_and_preserve_pending_results',
    'test_freestanding_graph_values.FreestandingGraphValueTests.test_interior_and_saved_failure_roots_are_validated_and_collected',
    'test_owned_runtime_allocation_failures.OwnedRuntimeAllocationFailureTests.test_text_publication_and_shared_capacity_failure_boundaries',

    'test_u1_verifier.U1VerifierTests.test_malformed_ir_and_budget_protocol',
    'test_u1_promotion.U1PromotionTests.test_differential_execution_shapes_and_failure_cleanup',
    'test_u1_promotion.U1PromotionTests.test_switch_physical_samples',
    'test_u3_stage0_parity_baseline.U3Stage0ParityBaseline.test_frozen_successful_programs_match_existing_native_compilers',
)

class Result(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.passed=0
        self.timings=[]
        self.started_at={}
    def startTest(self,test):
        self.started_at[test.id()]=time.monotonic()
        super().startTest(test)
    def stopTest(self,test):
        started=self.started_at.pop(test.id(),None)
        if started is not None:
            self.timings.append({'test':test.id(),'seconds':round(time.monotonic()-started,3)})
        super().stopTest(test)
    def addSuccess(self,test):
        super().addSuccess(test)
        self.passed+=1

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--profile',choices=('smoke','full'),default='full')
    args=parser.parse_args()
    if args.profile=='full':
        suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
    else:
        suite=unittest.defaultTestLoader.loadTestsFromNames(SMOKE_TESTS)
    discovered=suite.countTestCases();started=time.monotonic()
    result=unittest.TextTestRunner(verbosity=2,resultclass=Result).run(suite)
    slowest=sorted(result.timings,key=lambda item:item['seconds'],reverse=True)[:10]
    report={'profile':args.profile,'status':'success' if result.wasSuccessful() else 'failed','discovered_tests':discovered,
            'tests_run':result.testsRun,'passed':result.passed,
            'unsuccessful_tests':result.testsRun-result.passed-len(result.skipped)-len(result.expectedFailures),
            'failure_records':len(result.failures),
            'skipped':[{'test':test.id(),'reason':reason} for test,reason in result.skipped],
            'failures':[{'test':test.id(),'traceback':trace} for test,trace in result.failures],
            'errors':[{'test':test.id(),'traceback':trace} for test,trace in result.errors],
            'expected_failures':[test.id() for test,_ in result.expectedFailures],
            'unexpected_successes':[test.id() for test in result.unexpectedSuccesses],
            'seconds':time.monotonic()-started,'slowest_tests':slowest,'platform':platform.platform(),
            'python':platform.python_version(),'cc':os.environ.get('CC')}
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('[CI timing] profile='+args.profile+' total='+format(report['seconds'],'.2f')+
          's slowest='+str([(t['test'],t['seconds']) for t in slowest[:5]]),flush=True)
    return 0 if result.wasSuccessful() else 1

if __name__=='__main__':raise SystemExit(main())