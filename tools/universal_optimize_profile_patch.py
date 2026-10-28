from pathlib import Path

verify_path = Path("src/compiler/universal_verify.eri")
s = verify_path.read_text()

s = s.replace(
    "import compiler.format;\n",
    "import compiler.format;\nimport std.process;\n",
    1,
)
s = s.replace(
    "type Flow { block identity u.Block; reachable Bool; incoming Int; outgoing Int; first maybe identity Flow; second maybe identity Flow; next maybe identity Flow; }\n",
    "type Flow { block identity u.Block; reachable Bool; incoming Int; outgoing Int; first maybe identity Flow; second maybe identity Flow; next maybe identity Flow; }\ntype Profile { flowCalls Int; flowSteps Int; copyWords Int; intersectWords Int; transferCalls Int; instructionVisits Int; }\n",
    1,
)
s = s.replace(
    "function flowAt(flows maybe identity Flow,index Int) returns maybe identity Flow { let cursor be flows; while cursor != none { if cursor.block.index == index { return cursor; } cursor=cursor.next; } return none; }",
    "function flowAt(flows maybe identity Flow,index Int,profile identity Profile) returns maybe identity Flow { profile.flowCalls=profile.flowCalls+1; let cursor be flows; while cursor != none { profile.flowSteps=profile.flowSteps+1; if cursor.block.index == index { return cursor; } cursor=cursor.next; } return none; }",
    1,
)
s = s.replace(
    "function copy(values,target Int,source Int,count Int) returns Bool {\n    let changed be false; let index be 0;\n    while index<count { let word identity Word be values[target+index]; let other identity Word be values[source+index]; let value be other.value; if word.value != value { word.value=value; changed=true; } index=index+1; } return changed;\n}",
    "function copy(values,target Int,source Int,count Int,profile identity Profile) returns Bool {\n    let changed be false; let index be 0;\n    while index<count { profile.copyWords=profile.copyWords+1; let word identity Word be values[target+index]; let other identity Word be values[source+index]; let value be other.value; if word.value != value { word.value=value; changed=true; } index=index+1; } return changed;\n}",
    1,
)
s = s.replace(
    "function intersect(values,target Int,source Int,count Int) returns Bool {\n    let changed be false; let word be 0;\n    while word<count {",
    "function intersect(values,target Int,source Int,count Int,profile identity Profile) returns Bool {\n    let changed be false; let word be 0;\n    while word<count { profile.intersectWords=profile.intersectWords+1;",
    1,
)
s = s.replace(
    "function successors(program identity u.Program,flow identity Flow,value identity u.Instruction,flows maybe identity Flow) returns Bool fails m.SemanticError {\n    if value.op == 6 or value.op == 7 or value.op == 9 { flow.first=flowAt(flows,value.first); try require(program,flow.first != none,\"missing first successor\"); }\n    if value.op == 7 or value.op == 9 { flow.second=flowAt(flows,value.second); try require(program,flow.second != none,\"missing second successor\"); } return true;\n}",
    "function successors(program identity u.Program,flow identity Flow,value identity u.Instruction,flows maybe identity Flow,profile identity Profile) returns Bool fails m.SemanticError {\n    if value.op == 6 or value.op == 7 or value.op == 9 { flow.first=flowAt(flows,value.first,profile); try require(program,flow.first != none,\"missing first successor\"); }\n    if value.op == 7 or value.op == 9 { flow.second=flowAt(flows,value.second,profile); try require(program,flow.second != none,\"missing second successor\"); } return true;\n}",
    1,
)
s = s.replace(
    "function transfer(program identity u.Program,routine identity u.Function,flow identity Flow,classes,masks,wordCount Int,flags,functions,validate Bool,checkDefinitions Bool) returns Bool fails m.SemanticError {\n    copy(masks,0,flow.incoming,wordCount); let cursor be flow.block.instructions; let count be 0;\n    while cursor != none { try require(program,count<10*(classes.count+1),\"cyclic/excess instruction list\"); if validate { try instruction(program,routine,cursor,classes,masks,flags,functions,checkDefinitions); } define(masks,0,cursor.result,flags); count=count+1; cursor=cursor.next; }",
    "function transfer(program identity u.Program,routine identity u.Function,flow identity Flow,classes,masks,wordCount Int,flags,functions,validate Bool,checkDefinitions Bool,profile identity Profile) returns Bool fails m.SemanticError {\n    profile.transferCalls=profile.transferCalls+1; copy(masks,0,flow.incoming,wordCount,profile); let cursor be flow.block.instructions; let count be 0;\n    while cursor != none { profile.instructionVisits=profile.instructionVisits+1; try require(program,count<10*(classes.count+1),\"cyclic/excess instruction list\"); if validate { try instruction(program,routine,cursor,classes,masks,flags,functions,checkDefinitions); } define(masks,0,cursor.result,flags); count=count+1; cursor=cursor.next; }",
    1,
)
s = s.replace(
    "    } } return copy(masks,flow.outgoing,0,wordCount);\n}\nfunction propagate(source identity Flow,target maybe identity Flow,masks,wordCount Int) returns Bool {\n    if target == none { return false; } let current be target; let changed be false;\n    if not current.reachable { current.reachable=true; changed=true; }\n    if intersect(masks,current.incoming,source.outgoing,wordCount) { changed=true; } return changed;\n}",
    "    } } return copy(masks,flow.outgoing,0,wordCount,profile);\n}\nfunction propagate(source identity Flow,target maybe identity Flow,masks,wordCount Int,profile identity Profile) returns Bool {\n    if target == none { return false; } let current be target; let changed be false;\n    if not current.reachable { current.reachable=true; changed=true; }\n    if intersect(masks,current.incoming,source.outgoing,wordCount,profile) { changed=true; } return changed;\n}",
    1,
)
s = s.replace(
    "function routine(program identity u.Program,routine identity u.Function,flags,functions) returns Bool fails m.SemanticError {\n    let classes be []; let register be routine.registers;",
    "function routine(program identity u.Program,routine identity u.Function,flags,functions) returns Bool fails m.SemanticError {\n    let profile be identity Profile { flowCalls=0; flowSteps=0; copyWords=0; intersectWords=0; transferCalls=0; instructionVisits=0; };\n    let classes be []; let register be routine.registers;",
    1,
)
s = s.replace("flowAt(flows,cursor.index)", "flowAt(flows,cursor.index,profile)")
s = s.replace("flowAt(flows,0)", "flowAt(flows,0,profile)")
s = s.replace("successors(program,flow,terminal,flows)", "successors(program,flow,terminal,flows,profile)")
s = s.replace("transfer(program,routine,flow,classes,masks,wordCount,flags,functions,true,false)", "transfer(program,routine,flow,classes,masks,wordCount,flags,functions,true,false,profile)")
s = s.replace("transfer(program,routine,current,classes,masks,wordCount,flags,functions,false,false)", "transfer(program,routine,current,classes,masks,wordCount,flags,functions,false,false,profile)")
s = s.replace("propagate(current,current.first,masks,wordCount)", "propagate(current,current.first,masks,wordCount,profile)")
s = s.replace("propagate(current,current.second,masks,wordCount)", "propagate(current,current.second,masks,wordCount,profile)")
s = s.replace("transfer(program,routine,flow,classes,masks,wordCount,flags,functions,true,true)", "transfer(program,routine,flow,classes,masks,wordCount,flags,functions,true,true,profile)")
old_tail = "    flow=flows; while flow != none { if flow.reachable { try transfer(program,routine,flow,classes,masks,wordCount,flags,functions,true,true,profile); } flow=flow.next; } return true;\n}"
new_tail = "    flow=flows; while flow != none { if flow.reachable { try transfer(program,routine,flow,classes,masks,wordCount,flags,functions,true,true,profile); } flow=flow.next; }\n    process.writeError(\"[erist-opt-profile] routine=\"+format.integer(routine.index)+\" registers=\"+format.integer(classes.count)+\" blocks=\"+format.integer(count)+\" iterations=\"+format.integer(iterations)+\" flow_calls=\"+format.integer(profile.flowCalls)+\" flow_steps=\"+format.integer(profile.flowSteps)+\" transfers=\"+format.integer(profile.transferCalls)+\" instruction_visits=\"+format.integer(profile.instructionVisits)+\" copy_words=\"+format.integer(profile.copyWords)+\" intersect_words=\"+format.integer(profile.intersectWords));\n    return true;\n}"
assert old_tail in s
s = s.replace(old_tail, new_tail, 1)

for token in ("profile.flowSteps", "profile.instructionVisits", "[erist-opt-profile]"):
    assert token in s, token
verify_path.write_text(s)

opt_path = Path("src/compiler/universal_optimize.eri")
o = opt_path.read_text()
o = o.replace("import compiler.semantic_model as m;\n", "import compiler.semantic_model as m;\nimport compiler.format;\nimport std.process;\n", 1)
o = o.replace(
    "function visit(routine identity u.Function,block identity u.Block) {\n    if block.live { return; } block.live=true; let terminal be block.terminator;",
    "type OptProfile { blockAtCalls Int; blockAtSteps Int; visitCalls Int; liveBlocks Int; totalBlocks Int; routines Int; }\nfunction blockAt(routine identity u.Function,index Int,profile identity OptProfile) returns maybe identity u.Block { profile.blockAtCalls=profile.blockAtCalls+1; let cursor be routine.blocks; while cursor != none { profile.blockAtSteps=profile.blockAtSteps+1; if cursor.index == index { return cursor; } cursor=cursor.next; } return none; }\nfunction visit(routine identity u.Function,block identity u.Block,profile identity OptProfile) {\n    profile.visitCalls=profile.visitCalls+1; if block.live { return; } block.live=true; profile.liveBlocks=profile.liveBlocks+1; let terminal be block.terminator;",
    1,
)
o = o.replace("u.blockAt(routine,terminal.first)", "blockAt(routine,terminal.first,profile)")
o = o.replace("visit(routine,first)", "visit(routine,first,profile)")
o = o.replace("u.blockAt(routine,terminal.second)", "blockAt(routine,terminal.second,profile)")
o = o.replace("visit(routine,second)", "visit(routine,second,profile)")
o = o.replace(
    "function routine(routine identity u.Function) {\n    let cursor be routine.blocks; while cursor != none { let current be cursor; current.live=false; cursor=current.next; }\n    let first be u.blockAt(routine,0); if first != none { visit(routine,first); }",
    "function routine(routine identity u.Function,profile identity OptProfile) {\n    profile.routines=profile.routines+1; let cursor be routine.blocks; while cursor != none { profile.totalBlocks=profile.totalBlocks+1; let current be cursor; current.live=false; cursor=current.next; }\n    let first be blockAt(routine,0,profile); if first != none { visit(routine,first,profile); }",
    1,
)
o = o.replace(
    "public function optimize(program identity u.Program) returns Bool fails m.SemanticError {\n    try universal_verify.verify(program); routine(program.entry); let cursor be program.functions; while cursor != none { routine(cursor); cursor=cursor.next; } return try universal_verify.verify(program);\n}",
    "public function optimize(program identity u.Program) returns Bool fails m.SemanticError {\n    process.writeError(\"[erist-opt-profile] pass=pre-verify\");\n    try universal_verify.verify(program);\n    process.writeError(\"[erist-opt-profile] pass=reachability\");\n    let profile be identity OptProfile { blockAtCalls=0; blockAtSteps=0; visitCalls=0; liveBlocks=0; totalBlocks=0; routines=0; };\n    routine(program.entry,profile); let cursor be program.functions; while cursor != none { routine(cursor,profile); cursor=cursor.next; }\n    process.writeError(\"[erist-opt-profile] reachability routines=\"+format.integer(profile.routines)+\" blocks=\"+format.integer(profile.totalBlocks)+\" live=\"+format.integer(profile.liveBlocks)+\" block_at_calls=\"+format.integer(profile.blockAtCalls)+\" block_at_steps=\"+format.integer(profile.blockAtSteps)+\" visits=\"+format.integer(profile.visitCalls));\n    process.writeError(\"[erist-opt-profile] pass=post-verify\");\n    return try universal_verify.verify(program);\n}",
    1,
)
for token in ("OptProfile", "reachability routines=", "pass=post-verify"):
    assert token in o, token
opt_path.write_text(o)
