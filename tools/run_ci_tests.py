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
    'test_u2_cleanup_plan.U2CleanupPlanTests',
    'test_u2_cleanup_verify.U2CleanupVerifierTests',
    'test_u2_continuation_bind.U2ContinuationBindingTests',
    'test_u2_invoke.U2InvokeTests',
    'test_u2_fallible_registry.U2FallibleRegistryTests',
    'test_u2_invoke_transfers.U2InvokeTransferTests',
    'test_u2_scoped_owners.U2ScopedOwnerTests',
    'test_u2_function_file_roots.U2WholeFunctionFileRootTests',
    'test_u2_function_file_checked.U2FunctionFileCheckedTests',
    'test_u2_function_file_primary.U2FunctionFilePrimaryTests',
    'test_u2_function_list_text.U2FunctionListTextTests',
    'test_u2_typed_failure_context.U2TypedFailureContextTests',
    'test_u2_failure_order.U2FailureOrderTests',
    'test_u2_failure_trace.U2FailureTraceTests',
    'test_u2_failure_root_binding.U2FailureRootBindingTests',
    'test_u2_root_map.U2RootMapTests',
    'test_u2_ssa_liveness.U2SSALivenessTests',
    'test_u2_ssa_loops.U2SSALoopsTests',
    'test_u2_ssa_recursion.U2SSARecursionTests',
    'test_u2_managed_types.U2ManagedTypesTests',
    'test_u2_identity_root_gate.U2IdentityRootGateTests',
    'test_u2_identity_native_publication.U2IdentityNativePublicationTests',
    'test_u2_checked_identity_ssa.U2CheckedIdentitySSATests',
    'test_u2_checked_identity_edge.U2CheckedIdentityEdgeTests',
    'test_u2_checked_identity_close.U2CheckedIdentityCloseTests',
    'test_u2_function_scalar_native.U2FunctionScalarNativeTests',
    'test_u2_function_managed_native.U2FunctionManagedNativeTests',
    'test_u2_function_checked_native.U2FunctionCheckedNativeTests',
    'test_u2_function_checked_group.U2FunctionCheckedGroupTests',
    'test_u2_function_import_integration.U2FunctionImportIntegrationTests',
    'test_u2_identity_gc_cleanup.U2IdentityGCCleanupTests',
    'test_u2_identity_file_cleanup.U2IdentityFileCleanupTests',
    'test_u2_list_i64.U2ListI64Tests',
    'test_u2_text_unicode17.U2TextUnicode17Tests',
    # #51 semantic location-index optimization must retain AST identity,
    # duplicate-token collision handling and synthetic negative-token fallback.
    'test_source_fact_index.SourceFactIndexTests.test_identity_collisions_reanalysis_and_synthetic_nodes',
    'test_universal_ir.UniversalIRTests.test_universal_ir_contains_function_contract_and_call',
    'test_universal_ir.UniversalIRTests.test_universal_ir_has_explicit_checked_arithmetic_and_control_flow',
    'test_u1_foundation.U1FoundationTests.test_accounting_metadata_and_builder_on_c_bootstrap',
    'test_u1_foundation.U1FoundationTests.test_opcode_categories_and_inline_edges_are_explicit',
    'test_u1_words_path.U1WordPathTests',
    'test_u1b_profile_decoder.U1BProfileDecoderTests',
    'test_u1_calls.U1CallContracts.test_direct_call_declarations_and_verifier',
    'test_u1_module.U1ModuleBindingTests.test_declarations_bind_exact_verified_bodies',
    'test_u1_execution.U1CallExecutionTests.test_recursive_frames_effects_and_versioned_imports',
    'test_u1_native.U1NativeTests',
    'test_u1_integer_execution.U1IntegerExecutionTests.test_integer_recursion_switch_promotion_and_fault_traces',
    'test_u1_narrow_execution.U1NarrowExecutionTests.test_independent_canonical_narrow_execution_and_faults',
    'test_u1_aggregate_graph.U1AggregateTypeGraphTests.test_native_owned_type_graph_and_independent_verifier',
    'test_u1_aggregate_values.U1AggregateValuesTests.test_immutable_make_get_set_against_python_value_copy_oracle',
    'test_u1_aggregate_ssa.U1AggregateSSATests.test_canonical_aggregate_operations_and_independent_dead_code_verifier',
    'test_u1_aggregate_execution.U1AggregateExecutionTests.test_verified_canonical_ssa_immutable_execution',
    'test_u1_aggregate_canonical_oracle.U1CanonicalAggregateOracleTests.test_native_verified_canonical_aggregate_oracle',
    'test_u1_aggregate_signatures.U1AggregateSignatureTests.test_canonical_aggregate_signature_cfg_and_promotion',
    'test_u1_aggregate_loops.U1AggregateLoopTests.test_canonical_aggregate_loop_reentry_and_fuel',
    'test_u1_aggregate_calls.U1AggregateCallTests.test_linked_canonical_aggregate_calls_and_first_fault',
    'test_u1b_actual_physical.U1BAggregatePhysicalTests.test_actual_aggregate_owner_backing_and_gc_reclamation',
    # U1a #77 acceptance: exact owner-partition backing under both the C bootstrap
    # and freestanding owned runtime, independently predicted large radix/scratch
    # shapes, and the retained PR #103 C-heap evidence boundary.
    'test_u1_owner_physical.U1OwnerPhysicalTests',
    'test_native_runtime_lifetimes.NativeRuntimeLifetimeTests.test_native_handler_and_abandoned_call_allocations_are_reclaimed',
    # Owned runtime GC optimization conformance: real graph, interior/slot roots,
    # bounded static scratch, forced pressure, and allocation-refusal fallbacks.
    'test_heap_scaled_collection.HeapScaledCollectionTests.test_large_heap_interval_and_empty_heap_reset',
    'test_runtime_lookup_caches.IdentityBackingCacheTests',
    'test_freestanding_graph_values.FreestandingGraphValueTests.test_optional_identity_updates_preserve_aliases_rebinding_and_nested_snapshots',
    'test_freestanding_graph_values.FreestandingGraphValueTests.test_u2_managed_unicode17_list_value_and_identity_alias_parity',
    'test_runtime_lookup_caches.RuntimeLookupCacheTests.test_owned_graph_exact_slot_roots_preserve_interior_and_fallback',
    'test_runtime_lookup_caches.RuntimeLookupCacheTests.test_owned_slot_scratch_reuse_zeroing_nesting_and_refusal',
    'test_freestanding_text_roots.FreestandingTextRootTests.test_registered_roots_bound_loop_slots_and_preserve_pending_results',
    'test_freestanding_graph_values.FreestandingGraphValueTests.test_interior_and_saved_failure_roots_are_validated_and_collected',
    'test_freestanding_graph_values.FreestandingGraphValueTests.test_u2_saved_failure_root_survives_explicit_gc_and_releases',
    'test_freestanding_graph_values.FreestandingGraphValueTests.test_u2_primary_and_secondary_survive_forced_gc_in_order',
    'test_u2_native_root_publish.U2NativeRootPublishTests.test_generated_scoped_bind_publish_release_survives_forced_gc',
    'test_u2_native_cleanup.U2NativeCleanupTests',
    'test_u2_checked_rooted.U2CheckedRootedTests',
    'test_u2_checked_ssa.U2CheckedSSATests',
    'test_u2_checked_ssa_prefix.U2CheckedSSAPrefixTests',
    'test_u2_recursive_native_cleanup.U2RecursiveNativeCleanupTests',
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
