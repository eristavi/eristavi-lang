from pathlib import Path

path = Path("src/compiler/universal_verify.eri")
s = path.read_text(encoding="utf-8")

old = "type Flow { block identity u.Block; reachable Bool; incoming Int; outgoing Int; first maybe identity Flow; second maybe identity Flow; next maybe identity Flow; }"
new = """type Flow { block identity u.Block; reachable Bool; incoming Int; outgoing Int; first maybe identity Flow; second maybe identity Flow; next maybe identity Flow; indexNext maybe identity Flow; }
type FlowBucket { number Int; generation Int; entries maybe identity Flow; left maybe identity FlowBucket; right maybe identity FlowBucket; }
type FlowIndex { root identity FlowBucket; generation Int; }"""
assert s.count(old) == 1, ("Flow", s.count(old))
s = s.replace(old, new)

old = "function flowAt(flows maybe identity Flow,index Int) returns maybe identity Flow { let cursor be flows; while cursor != none { if cursor.block.index == index { return cursor; } cursor=cursor.next; } return none; }"
new = """function flowBucketTree(first Int,last Int) returns maybe identity FlowBucket {
    if first>last { return none; }
    let middle be first+(last-first)/2;
    return identity FlowBucket { number=middle; generation=-1; entries=none; left=flowBucketTree(first,middle-1); right=flowBucketTree(middle+1,last); };
}
function flowIndex() returns identity FlowIndex {
    return identity FlowIndex { root=identity FlowBucket { number=128; generation=-1; entries=none; left=flowBucketTree(0,127); right=flowBucketTree(129,256); }; generation=-1; };
}
function flowBucket(indexer identity FlowIndex,number Int) returns identity FlowBucket {
    let cursor maybe identity FlowBucket be indexer.root;
    while cursor != none {
        let current be cursor;
        if current.number == number { return current; }
        if number<current.number { cursor=current.left; } else { cursor=current.right; }
    }
    return indexer.root;
}
function flowHash(index Int) returns Int {
    let value be index%257; if value<0 { value=value+257; } return value;
}
function beginRoutine(indexer identity FlowIndex) { indexer.generation=indexer.generation+1; }
function flowAt(indexer identity FlowIndex,index Int) returns maybe identity Flow {
    let slot be flowBucket(indexer,flowHash(index));
    if slot.generation != indexer.generation { return none; }
    let cursor be slot.entries;
    while cursor != none { if cursor.block.index == index { return cursor; } cursor=cursor.indexNext; }
    return none;
}
function rememberFlow(indexer identity FlowIndex,flow identity Flow) {
    let slot be flowBucket(indexer,flowHash(flow.block.index));
    if slot.generation != indexer.generation { slot.generation=indexer.generation; slot.entries=none; }
    flow.indexNext=slot.entries; slot.entries=flow;
}"""
assert s.count(old) == 1, ("flowAt", s.count(old))
s = s.replace(old, new)

old = "function successors(program identity u.Program,flow identity Flow,value identity u.Instruction,flows maybe identity Flow) returns Bool fails m.SemanticError {\n    if value.op == 6 or value.op == 7 or value.op == 9 { flow.first=flowAt(flows,value.first); try require(program,flow.first != none,\"missing first successor\"); }\n    if value.op == 7 or value.op == 9 { flow.second=flowAt(flows,value.second); try require(program,flow.second != none,\"missing second successor\"); } return true;\n}"
new = "function successors(program identity u.Program,indexer identity FlowIndex,flow identity Flow,value identity u.Instruction) returns Bool fails m.SemanticError {\n    if value.op == 6 or value.op == 7 or value.op == 9 { flow.first=flowAt(indexer,value.first); try require(program,flow.first != none,\"missing first successor\"); }\n    if value.op == 7 or value.op == 9 { flow.second=flowAt(indexer,value.second); try require(program,flow.second != none,\"missing second successor\"); } return true;\n}"
assert s.count(old) == 1, ("successors", s.count(old))
s = s.replace(old, new)

old = "function routine(program identity u.Program,routine identity u.Function,flags,functions) returns Bool fails m.SemanticError {\n    let classes be []; let register be routine.registers;"
new = "function routine(program identity u.Program,indexer identity FlowIndex,routine identity u.Function,flags,functions) returns Bool fails m.SemanticError {\n    beginRoutine(indexer); let classes be []; let register be routine.registers;"
assert s.count(old) == 1, ("routine", s.count(old))
s = s.replace(old, new)

old = "while cursor != none { try require(program,flowAt(flows,cursor.index) == none and cursor.index>=0,\"cyclic/duplicate block table\"); let record be identity Flow { block=cursor; reachable=cursor.index == 0; incoming=(2*count+1)*wordCount; outgoing=(2*count+2)*wordCount; first=none; second=none; next=flows; }; flows=record; cursor=cursor.next; count=count+1; }"
new = "while cursor != none { try require(program,flowAt(indexer,cursor.index) == none and cursor.index>=0,\"cyclic/duplicate block table\"); let record be identity Flow { block=cursor; reachable=cursor.index == 0; incoming=(2*count+1)*wordCount; outgoing=(2*count+2)*wordCount; first=none; second=none; next=flows; indexNext=none; }; flows=record; rememberFlow(indexer,record); cursor=cursor.next; count=count+1; }"
assert s.count(old) == 1, ("flow-build", s.count(old))
s = s.replace(old, new)

old = "try require(program,flowAt(flows,0) != none,\"function has no entry block\");"
new = "try require(program,flowAt(indexer,0) != none,\"function has no entry block\");"
assert s.count(old) == 1, ("entry", s.count(old))
s = s.replace(old, new)

old = "if terminal != none { try successors(program,flow,terminal,flows); }"
new = "if terminal != none { try successors(program,indexer,flow,terminal); }"
assert s.count(old) == 1, ("successor-call", s.count(old))
s = s.replace(old, new)

old = "let flags be powers(); cursor=program.functions; while cursor != none { try routine(program,cursor,flags,functions); cursor=cursor.next; } return try routine(program,program.entry,flags,functions);"
new = "let flags be powers(); let indexer be flowIndex(); cursor=program.functions; while cursor != none { try routine(program,indexer,cursor,flags,functions); cursor=cursor.next; } return try routine(program,indexer,program.entry,flags,functions);"
assert s.count(old) == 1, ("verify", s.count(old))
s = s.replace(old, new)

for required in ("FlowIndex", "indexNext", "rememberFlow", "beginRoutine(indexer)", "routine(program,indexer"):
    assert required in s, required
path.write_text(s, encoding="utf-8")

cases = Path("tests/universal_verifier_cases.py")
t = cases.read_text(encoding="utf-8")
anchor = "    add('sparse', 'let b be fresh(); let last be u.block(b); last.index=1000000000000; u.jump(b,last); b.current=last; let value be u.zero(b,\"void\"); u.returnValue(b,value); result(\"sparse\",b,true);')\n"
addition = anchor + "    add('sparse-collision', 'let b be fresh(); let first be u.block(b); first.index=257; let second be u.block(b); second.index=514; u.jump(b,first); b.current=first; u.jump(b,second); b.current=second; let value be u.zero(b,\"void\"); u.returnValue(b,value); result(\"sparse-collision\",b,false);')\n"
assert t.count(anchor) == 1, ("sparse", t.count(anchor))
t = t.replace(anchor, addition)
cases.write_text(t, encoding="utf-8")
