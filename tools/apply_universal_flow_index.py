from pathlib import Path

path = Path('src/compiler/universal_verify.eri')
s = path.read_text()

old = 'type Flow { block identity u.Block; reachable Bool; incoming Int; outgoing Int; first maybe identity Flow; second maybe identity Flow; next maybe identity Flow; }'
new = '''type Flow { block identity u.Block; reachable Bool; incoming Int; outgoing Int; first maybe identity Flow; second maybe identity Flow; next maybe identity Flow; bucketNext maybe identity Flow; }
type FlowBucket { number Int; entries maybe identity Flow; left maybe identity FlowBucket; right maybe identity FlowBucket; touched Bool; touchedNext maybe identity FlowBucket; }
type FlowIndex { root identity FlowBucket; touched maybe identity FlowBucket; }'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old,new,1)

old = 'function flowAt(flows maybe identity Flow,index Int) returns maybe identity Flow { let cursor be flows; while cursor != none { if cursor.block.index == index { return cursor; } cursor=cursor.next; } return none; }'
new = '''function flowBucketTree(first Int,last Int) returns maybe identity FlowBucket {
    if first>last { return none; }
    let middle=first+(last-first)/2;
    return identity FlowBucket { number=middle; entries=none; left=flowBucketTree(first,middle-1); right=flowBucketTree(middle+1,last); touched=false; touchedNext=none; };
}
function flowIndex() returns identity FlowIndex {
    return identity FlowIndex { root=identity FlowBucket { number=128; entries=none; left=flowBucketTree(0,127); right=flowBucketTree(129,256); touched=false; touchedNext=none; }; touched=none; };
}
function clearFlowIndex(indexer identity FlowIndex) {
    let cursor=indexer.touched;
    while cursor != none { let current=cursor; cursor=current.touchedNext; current.entries=none; current.touched=false; current.touchedNext=none; }
    indexer.touched=none;
}
function flowHash(index Int) returns Int { let value=index%257; if value<0 { value=value+257; } return value; }
function flowBucket(indexer identity FlowIndex,number Int) returns identity FlowBucket {
    let cursor maybe identity FlowBucket be indexer.root;
    while cursor != none { let current=cursor; if current.number==number { return current; } if number<current.number { cursor=current.left; } else { cursor=current.right; } }
    return indexer.root;
}
function flowAt(indexer identity FlowIndex,index Int) returns maybe identity Flow {
    let slot=flowBucket(indexer,flowHash(index)); let cursor=slot.entries;
    while cursor != none { if cursor.block.index==index { return cursor; } cursor=cursor.bucketNext; }
    return none;
}
function rememberFlow(indexer identity FlowIndex,value identity Flow) {
    let slot=flowBucket(indexer,flowHash(value.block.index));
    if not slot.touched { slot.touched=true; slot.touchedNext=indexer.touched; indexer.touched=slot; }
    value.bucketNext=slot.entries; slot.entries=value;
}'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old,new,1)

old = '''function successors(program identity u.Program,flow identity Flow,value identity u.Instruction,flows maybe identity Flow) returns Bool fails m.SemanticError {
    if value.op == 6 or value.op == 7 or value.op == 9 { flow.first=flowAt(flows,value.first); try require(program,flow.first != none,"missing first successor"); }
    if value.op == 7 or value.op == 9 { flow.second=flowAt(flows,value.second); try require(program,flow.second != none,"missing second successor"); } return true;
}'''
new = '''function successors(program identity u.Program,flow identity Flow,value identity u.Instruction,indexer identity FlowIndex) returns Bool fails m.SemanticError {
    if value.op == 6 or value.op == 7 or value.op == 9 { flow.first=flowAt(indexer,value.first); try require(program,flow.first != none,"missing first successor"); }
    if value.op == 7 or value.op == 9 { flow.second=flowAt(indexer,value.second); try require(program,flow.second != none,"missing second successor"); } return true;
}'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old,new,1)

old = 'function routine(program identity u.Program,routine identity u.Function,flags,functions) returns Bool fails m.SemanticError {\n    let classes be []; let register be routine.registers;'
new = 'function routine(program identity u.Program,routine identity u.Function,flags,functions,indexer identity FlowIndex) returns Bool fails m.SemanticError {\n    clearFlowIndex(indexer); let classes be []; let register be routine.registers;'
assert s.count(old) == 1, s.count(old)
s = s.replace(old,new,1)

old = '    while cursor != none { try require(program,flowAt(flows,cursor.index) == none and cursor.index>=0,"cyclic/duplicate block table"); let record be identity Flow { block=cursor; reachable=cursor.index == 0; incoming=(2*count+1)*wordCount; outgoing=(2*count+2)*wordCount; first=none; second=none; next=flows; }; flows=record; cursor=cursor.next; count=count+1; }\n    try require(program,flowAt(flows,0) != none,"function has no entry block");'
new = '    while cursor != none { try require(program,flowAt(indexer,cursor.index) == none and cursor.index>=0,"cyclic/duplicate block table"); let record be identity Flow { block=cursor; reachable=cursor.index == 0; incoming=(2*count+1)*wordCount; outgoing=(2*count+2)*wordCount; first=none; second=none; next=flows; bucketNext=none; }; rememberFlow(indexer,record); flows=record; cursor=cursor.next; count=count+1; }\n    try require(program,flowAt(indexer,0) != none,"function has no entry block");'
assert s.count(old) == 1, s.count(old)
s = s.replace(old,new,1)

s = s.replace('try successors(program,flow,terminal,flows);','try successors(program,flow,terminal,indexer);',1)

old = '''public function verify(program identity u.Program) returns Bool fails m.SemanticError {
    try require(program,program.entry.index == -1 and program.entry.parameters == 0,"invalid entry function"); let cursor be program.functions; let count be 0; let functions be [];
    while cursor != none { try require(program,cursor.index == count,"noncontiguous/duplicate function table"); functions.add(cursor); count=count+1; cursor=cursor.next; }
    let flags be powers(); cursor=program.functions; while cursor != none { try routine(program,cursor,flags,functions); cursor=cursor.next; } return try routine(program,program.entry,flags,functions);
}'''
new = '''public function verify(program identity u.Program) returns Bool fails m.SemanticError {
    try require(program,program.entry.index == -1 and program.entry.parameters == 0,"invalid entry function"); let cursor be program.functions; let count be 0; let functions be [];
    while cursor != none { try require(program,cursor.index == count,"noncontiguous/duplicate function table"); functions.add(cursor); count=count+1; cursor=cursor.next; }
    let flags be powers(); let indexer=flowIndex(); cursor=program.functions; while cursor != none { try routine(program,cursor,flags,functions,indexer); cursor=cursor.next; } return try routine(program,program.entry,flags,functions,indexer);
}'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old,new,1)

for required in ('bucketNext', 'clearFlowIndex(indexer)', 'rememberFlow(indexer,record)', 'routine(program,program.entry,flags,functions,indexer)'):
    assert required in s, required
path.write_text(s)
