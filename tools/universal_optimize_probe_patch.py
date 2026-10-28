from pathlib import Path

verify_path = Path("src/compiler/universal_verify.eri")
s = verify_path.read_text()

s = s.replace("import compiler.format;\n", "import compiler.format;\nimport compiler.progress;\n")

old = "type Flow { block identity u.Block; reachable Bool; incoming Int; outgoing Int; first maybe identity Flow; second maybe identity Flow; next maybe identity Flow; }"
new = "type Flow { block identity u.Block; reachable Bool; incoming Int; outgoing Int; first maybe identity Flow; second maybe identity Flow; next maybe identity Flow; }\ntype Profile { flowLookups Int; flowSteps Int; transferCalls Int; instructionVisits Int; copyCalls Int; copyWords Int; intersectCalls Int; intersectWords Int; intersectBits Int; iterations Int; routines Int; blocks Int; registers Int; }"
assert s.count(old) == 1
s = s.replace(old, new)

old = "function flowAt(flows maybe identity Flow,index Int) returns maybe identity Flow { let cursor be flows; while cursor != none { if cursor.block.index == index { return cursor; } cursor=cursor.next; } return none; }"
new = "function flowAt(profile identity Profile,flows maybe identity Flow,index Int) returns maybe identity Flow { profile.flowLookups=profile.flowLookups+1; let cursor be flows; while cursor != none { profile.flowSteps=profile.flowSteps+1; if cursor.block.index == index { return cursor; } cursor=cursor.next; } return none; }"
assert s.count(old) == 1
s = s.replace(old, new)

old = "function copy(values,target Int,source Int,count Int) returns Bool {\n    let changed be false; let index be 0;"
new = "function copy(profile identity Profile,values,target Int,source Int,count Int) returns Bool {\n    profile.copyCalls=profile.copyCalls+1; profile.copyWords=profile.copyWords+count;\n    let changed be false; let index be 0;"
assert s.count(old) == 1
s = s.replace(old, new)

old = "function intersect(values,target Int,source Int,count Int) returns Bool {\n    let changed be false; let word be 0;"
new = "function intersect(profile identity Profile,values,target Int,source Int,count Int) returns Bool {\n    profile.intersectCalls=profile.intersectCalls+1;\n    let changed be false; let word be 0;"
assert s.count(old) == 1
s = s.replace(old, new)
s = s.replace("    while word<count {\n        let current identity Word", "    while word<count {\n        profile.intersectWords=profile.intersectWords+1;\n        let current identity Word", 1)
s = s.replace("while index<62 { if (current.value/flag)%2", "while index<62 { profile.intersectBits=profile.intersectBits+1; if (current.value/flag)%2", 1)

old = "function successors(program identity u.Program,flow identity Flow,value identity u.Instruction,flows maybe identity Flow) returns Bool fails m.SemanticError {\n    if value.op == 6 or value.op == 7 or value.op == 9 { flow.first=flowAt(flows,value.first);"
new = "function successors(program identity u.Program,profile identity Profile,flow identity Flow,value identity u.Instruction,flows maybe identity Flow) returns Bool fails m.SemanticError {\n    if value.op == 6 or value.op == 7 or value.op == 9 { flow.first=flowAt(profile,flows,value.first);"
assert s.count(old) == 1
s = s.replace(old, new)
s = s.replace("flow.second=flowAt(flows,value.second)", "flow.second=flowAt(profile,flows,value.second)", 1)

old = "function transfer(program identity u.Program,routine identity u.Function,flow identity Flow,classes,masks,wordCount Int,flags,functions,validate Bool,checkDefinitions Bool) returns Bool fails m.SemanticError {\n    copy(masks,0,flow.incoming,wordCount); let cursor be flow.block.instructions; let count be 0;\n    while cursor != none {"
new = "function transfer(program identity u.Program,profile identity Profile,routine identity u.Function,flow identity Flow,classes,masks,wordCount Int,flags,functions,validate Bool,checkDefinitions Bool) returns Bool fails m.SemanticError {\n    profile.transferCalls=profile.transferCalls+1; copy(profile,masks,0,flow.incoming,wordCount); let cursor be flow.block.instructions; let count be 0;\n    while cursor != none { profile.instructionVisits=profile.instructionVisits+1;"
assert s.count(old) == 1
s = s.replace(old, new)
s = s.replace("return copy(masks,flow.outgoing,0,wordCount);", "return copy(profile,masks,flow.outgoing,0,wordCount);", 1)

old = "function propagate(source identity Flow,target maybe identity Flow,masks,wordCount Int) returns Bool {"
new = "function propagate(profile identity Profile,source identity Flow,target maybe identity Flow,masks,wordCount Int) returns Bool {"
assert s.count(old) == 1
s = s.replace(old, new)
s = s.replace("if intersect(masks,current.incoming,source.outgoing,wordCount)", "if intersect(profile,masks,current.incoming,source.outgoing,wordCount)", 1)

old = "function routine(program identity u.Program,routine identity u.Function,flags,functions) returns Bool fails m.SemanticError {\n    let classes be []; let register be routine.registers;\n    while register != none {"
new = "function routine(program identity u.Program,profile identity Profile,routine identity u.Function,flags,functions) returns Bool fails m.SemanticError {\n    profile.routines=profile.routines+1; let classes be []; let register be routine.registers;\n    while register != none { profile.registers=profile.registers+1;"
assert s.count(old) == 1
s = s.replace(old, new)
s = s.replace("while cursor != none { try require(program,flowAt(flows,cursor.index) == none", "while cursor != none { profile.blocks=profile.blocks+1; try require(program,flowAt(profile,flows,cursor.index) == none", 1)
s = s.replace("try require(program,flowAt(flows,0) != none", "try require(program,flowAt(profile,flows,0) != none", 1)
s = s.replace("try successors(program,flow,terminal,flows); } try transfer(program,routine,flow,classes,masks,wordCount,flags,functions,true,false);", "try successors(program,profile,flow,terminal,flows); } try transfer(program,profile,routine,flow,classes,masks,wordCount,flags,functions,true,false);", 1)
s = s.replace("flow=flows; iterations=iterations+1;", "flow=flows; iterations=iterations+1; profile.iterations=profile.iterations+1;", 1)
s = s.replace("if try transfer(program,routine,current,classes,masks,wordCount,flags,functions,false,false)", "if try transfer(program,profile,routine,current,classes,masks,wordCount,flags,functions,false,false)", 1)
s = s.replace("if propagate(current,current.first,masks,wordCount)", "if propagate(profile,current,current.first,masks,wordCount)", 1)
s = s.replace("if propagate(current,current.second,masks,wordCount)", "if propagate(profile,current,current.second,masks,wordCount)", 1)
s = s.replace("if flow.reachable { try transfer(program,routine,flow,classes,masks,wordCount,flags,functions,true,true); }", "if flow.reachable { try transfer(program,profile,routine,flow,classes,masks,wordCount,flags,functions,true,true); }", 1)

old = '''public function verify(program identity u.Program) returns Bool fails m.SemanticError {
    try require(program,program.entry.index == -1 and program.entry.parameters == 0,"invalid entry function"); let cursor be program.functions; let count be 0; let functions be [];
    while cursor != none { try require(program,cursor.index == count,"noncontiguous/duplicate function table"); functions.add(cursor); count=count+1; cursor=cursor.next; }
    let flags be powers(); cursor=program.functions; while cursor != none { try routine(program,cursor,flags,functions); cursor=cursor.next; } return try routine(program,program.entry,flags,functions);
}'''
new = '''function profile() returns identity Profile {
    return identity Profile { flowLookups=0; flowSteps=0; transferCalls=0; instructionVisits=0; copyCalls=0; copyWords=0; intersectCalls=0; intersectWords=0; intersectBits=0; iterations=0; routines=0; blocks=0; registers=0; };
}
function verifyWith(program identity u.Program,stats identity Profile) returns Bool fails m.SemanticError {
    try require(program,program.entry.index == -1 and program.entry.parameters == 0,"invalid entry function"); let cursor be program.functions; let count be 0; let functions be [];
    while cursor != none { try require(program,cursor.index == count,"noncontiguous/duplicate function table"); functions.add(cursor); count=count+1; cursor=cursor.next; }
    let flags be powers(); cursor=program.functions; while cursor != none { try routine(program,stats,cursor,flags,functions); cursor=cursor.next; } return try routine(program,stats,program.entry,flags,functions);
}
public function verify(program identity u.Program) returns Bool fails m.SemanticError {
    return try verifyWith(program,profile());
}
public function verifyProfiled(program identity u.Program,label Text) returns Bool fails m.SemanticError {
    let stats be profile(); let result be try verifyWith(program,stats);
    progress.phase(true,"sample","universal-verify-profile",label+" routines="+format.integer(stats.routines)+" blocks="+format.integer(stats.blocks)+" registers="+format.integer(stats.registers)+" flow_lookups="+format.integer(stats.flowLookups)+" flow_steps="+format.integer(stats.flowSteps)+" transfers="+format.integer(stats.transferCalls)+" instruction_visits="+format.integer(stats.instructionVisits)+" copy_calls="+format.integer(stats.copyCalls)+" copy_words="+format.integer(stats.copyWords)+" intersect_calls="+format.integer(stats.intersectCalls)+" intersect_words="+format.integer(stats.intersectWords)+" intersect_bits="+format.integer(stats.intersectBits)+" iterations="+format.integer(stats.iterations));
    return result;
}'''
assert s.count(old) == 1, s[-1200:]
s = s.replace(old, new)

for required in ("verifyProfiled", "flow_steps", "instruction_visits", "intersect_bits"):
    assert required in s
verify_path.write_text(s)

opt_path = Path("src/compiler/universal_optimize.eri")
o = opt_path.read_text()
o = o.replace("import compiler.semantic_model as m;\n", "import compiler.semantic_model as m;\nimport compiler.progress;\nimport compiler.format;\n")
old = "function visit(routine identity u.Function,block identity u.Block) {"
new = "type OptProfile { blockLookups Int; blockSteps Int; visits Int; routines Int; }\nfunction blockAt(profile identity OptProfile,routine identity u.Function,index Int) returns maybe identity u.Block { profile.blockLookups=profile.blockLookups+1; let cursor be routine.blocks; while cursor != none { profile.blockSteps=profile.blockSteps+1; if cursor.index == index { return cursor; } cursor=cursor.next; } return none; }\nfunction visit(profile identity OptProfile,routine identity u.Function,block identity u.Block) {"
assert o.count(old) == 1
o = o.replace(old, new)
o = o.replace("if block.live { return; } block.live=true;", "if block.live { return; } profile.visits=profile.visits+1; block.live=true;", 1)
o = o.replace("u.blockAt(routine,terminal.first)", "blockAt(profile,routine,terminal.first)")
o = o.replace("visit(routine,first)", "visit(profile,routine,first)")
o = o.replace("u.blockAt(routine,terminal.second)", "blockAt(profile,routine,terminal.second)")
o = o.replace("visit(routine,second)", "visit(profile,routine,second)")
o = o.replace("function routine(routine identity u.Function) {", "function routine(profile identity OptProfile,routine identity u.Function) { profile.routines=profile.routines+1;", 1)
o = o.replace("let first be u.blockAt(routine,0); if first != none { visit(routine,first); }", "let first be blockAt(profile,routine,0); if first != none { visit(profile,routine,first); }", 1)
old = '''public function optimize(program identity u.Program) returns Bool fails m.SemanticError {
    try universal_verify.verify(program); routine(program.entry); let cursor be program.functions; while cursor != none { routine(cursor); cursor=cursor.next; } return try universal_verify.verify(program);
}'''
new = '''public function optimize(program identity u.Program) returns Bool fails m.SemanticError {
    try universal_verify.verifyProfiled(program,"pre");
    let stats be identity OptProfile { blockLookups=0; blockSteps=0; visits=0; routines=0; };
    routine(stats,program.entry); let cursor be program.functions; while cursor != none { routine(stats,cursor); cursor=cursor.next; }
    progress.phase(true,"sample","universal-optimize-profile","routines="+format.integer(stats.routines)+" block_lookups="+format.integer(stats.blockLookups)+" block_steps="+format.integer(stats.blockSteps)+" visits="+format.integer(stats.visits));
    return try universal_verify.verifyProfiled(program,"post");
}'''
assert o.count(old) == 1
o = o.replace(old, new)
for required in ("universal-optimize-profile", "verifyProfiled", "blockSteps"):
    assert required in o
opt_path.write_text(o)
