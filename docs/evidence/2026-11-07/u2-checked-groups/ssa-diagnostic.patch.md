# Temporary diagnostic patch

Applied only in a scratch checkout of `6635e8e`; not a production change.

````diff
diff --git a/src/compiler/u2_ssa_liveness.eri b/src/compiler/u2_ssa_liveness.eri
index 392a378..6a99b18 100644
--- a/src/compiler/u2_ssa_liveness.eri
+++ b/src/compiler/u2_ssa_liveness.eri
@@ -209,13 +209,18 @@ function flow(plan identity Plan,routine identity build.Function,
 function construct(plan identity Plan,routine identity build.Function,
     graph identity aggregate.Registry,phase identity budget.Phase,chosen)
     fails budget.LimitError,InvalidLiveness {
+    output("# U2_SSA_TRACE:select-start");
     try select(plan,routine,graph,phase,chosen);
+    output("# U2_SSA_TRACE:select-done");
     let total be plan.blocks*(plan.values.length/4);
     try zero(plan.uses,phase,total);
     try zero(plan.inputs,phase,total);
     try zero(plan.outputs,phase,total);
+    output("# U2_SSA_TRACE:uses-start");
     try markUses(plan,routine,phase);
+    output("# U2_SSA_TRACE:flow-start");
     try flow(plan,routine,phase);
+    output("# U2_SSA_TRACE:flow-done");
     try words.freeze(plan.types); try words.freeze(plan.values);
     try words.freeze(plan.uses); try words.freeze(plan.inputs);
     try words.freeze(plan.outputs);
@@ -239,8 +244,10 @@ public function create(routine identity build.Function,
     // structure, all invoke contracts and the aggregate graph. This result is
     // not a reused stamp, and consumes its own fresh verification phase.
     let verification be try budget.verificationPhase(routine.owner);
+    output("# U2_SSA_TRACE:canonical-start");
     let checked be try canonical.verifyFallibleRegistry(
         routine,graph,verification,contractsTable);
+    output("# U2_SSA_TRACE:canonical-done");
     let pending be try budget.reserve(routine.owner,512);
     let selected be words.create(routine.owner,8)
         else error budget.LimitError { try budget.cancelReservation(pending); fail error; };
@@ -263,6 +270,7 @@ public function create(routine identity build.Function,
     construct(plan,routine,graph,phase,managedTypes)
         else error InvalidLiveness { try close(plan); fail error; }
         else error budget.LimitError { try close(plan); fail error; };
+    output("# U2_SSA_TRACE:plan-done");
     return plan;
 }
 function same(first identity words.Words,second identity words.Words,
````
