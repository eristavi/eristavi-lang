from pathlib import Path

TYPES = Path("src/compiler/ir_types.eri")
LOWER = Path("src/compiler/ir_lower.eri")

s = TYPES.read_text()

def once(old: str, new: str, label: str) -> None:
    global s
    count = s.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one anchor, found {count}")
    s = s.replace(old, new)

once(
    "public type TypeCacheEntry { kind Int; name Text; inner Int; index Int; next maybe identity TypeCacheEntry; }",
    "public type TypeCacheEntry { kind Int; name Text; inner Int; index Int; value identity ir.Type; next maybe identity TypeCacheEntry; indexNext maybe identity TypeCacheEntry; }",
    "cache entry",
)
once(
    "public type Registry { root identity TypeBucket; nextIndex Int; }",
    "public type Registry { root identity TypeBucket; indexRoot identity TypeBucket; nextIndex Int; }",
    "registry",
)

anchor = '''function typeHash(kind Int, name Text, inner Int) returns Int {
'''
insert = '''function indexBucket(indexer identity Registry, number Int) returns identity TypeBucket {
    let cursor maybe identity TypeBucket be indexer.indexRoot;
    while cursor != none {
        let current be cursor;
        if current.number == number { return current; }
        if number < current.number { cursor=current.left; } else { cursor=current.right; }
    }
    return indexer.indexRoot;
}
function indexHash(index Int) returns Int {
    let value be index%257; if value < 0 { value=value+257; } return value;
}
function cachedIndex(indexer identity Registry, index Int) returns maybe identity ir.Type {
    let slot be indexBucket(indexer,indexHash(index)); let cursor be slot.entries;
    while cursor != none { if cursor.index == index { return cursor.value; } cursor=cursor.indexNext; }
    return none;
}
function typeHash(kind Int, name Text, inner Int) returns Int {
'''
if s.count(anchor) != 1:
    raise SystemExit("index helper anchor mismatch")
s = s.replace(anchor, insert)

once(
'''function remember(indexer identity Registry, kind Int, name Text, inner Int, index Int) {
    let slot be typeBucket(indexer,typeHash(kind,name,inner));
    slot.entries=identity TypeCacheEntry { kind=kind; name=name; inner=inner; index=index; next=slot.entries; };
}''',
'''function remember(indexer identity Registry, kind Int, name Text, inner Int, index Int, value identity ir.Type) {
    let slot be typeBucket(indexer,typeHash(kind,name,inner));
    let entry be identity TypeCacheEntry { kind=kind; name=name; inner=inner; index=index; value=value; next=slot.entries; indexNext=none; };
    slot.entries=entry;
    let byIndex be indexBucket(indexer,indexHash(index)); entry.indexNext=byIndex.entries; byIndex.entries=entry;
}''',
    "remember",
)
once(
    "if value != none { seed(indexer,value.next); remember(indexer,value.kind,value.name,value.inner,value.index); indexer.nextIndex=indexer.nextIndex+1; }",
    "if value != none { seed(indexer,value.next); remember(indexer,value.kind,value.name,value.inner,value.index,value); indexer.nextIndex=indexer.nextIndex+1; }",
    "seed",
)
once(
'''        root=identity TypeBucket { number=128; entries=none; left=bucketTree(0,127); right=bucketTree(129,256); };
        nextIndex=6;''',
'''        root=identity TypeBucket { number=128; entries=none; left=bucketTree(0,127); right=bucketTree(129,256); };
        indexRoot=identity TypeBucket { number=128; entries=none; left=bucketTree(0,127); right=bucketTree(129,256); };
        nextIndex=6;''',
    "registry roots",
)
once(
    "if indexer != none { remember(indexer,kind,actual.name,inner,index); }",
    "if indexer != none { remember(indexer,kind,actual.name,inner,index,item); }",
    "new type cache",
)

anchor = '''public function semanticType(program identity ir.Program, index Int) returns identity m.Type {
'''
helpers = '''public function typeAtIndexed(indexer identity Registry, program identity ir.Program, index Int) returns maybe identity ir.Type {
    let value be cachedIndex(indexer,index); if value != none { return value; } return ir.typeAt(program,index);
}
public function kindIndexed(indexer identity Registry, program identity ir.Program, index Int) returns Int {
    if index >= 1 and index <= 5 { return index; }
    let value be typeAtIndexed(indexer,program,index); if value != none { return value.kind; } return -1;
}
public function innerIndexed(indexer identity Registry, program identity ir.Program, index Int) returns Int {
    let value be typeAtIndexed(indexer,program,index); if value != none { return value.inner; } return -1;
}
public function semanticTypeIndexed(indexer identity Registry, program identity ir.Program, index Int) returns identity m.Type {
    if index >= 1 and index <= 5 { return m.makeType(index,""); }
    let item be typeAtIndexed(indexer,program,index);
    if item != none {
        let kind be item.kind;
        if kind == 7 or kind == 8 or kind == 9 { return m.wrap(kind,semanticTypeIndexed(indexer,program,item.inner)); }
        return m.makeType(kind,item.name);
    }
    return m.makeType(5,"");
}
public function semanticType(program identity ir.Program, index Int) returns identity m.Type {
'''
if s.count(anchor) != 1:
    raise SystemExit("indexed semantic type anchor mismatch")
s = s.replace(anchor, helpers)

field_anchor = '''public function field(program identity ir.Program, valueType Int, name Text, location identity m.Location) returns identity ir.Field fails m.SemanticError {
'''
field_helpers = '''public function fieldIndexed(indexer identity Registry, program identity ir.Program, valueType Int, name Text, location identity m.Location) returns identity ir.Field fails m.SemanticError {
    let target be valueType; if kindIndexed(indexer,program,target) == 9 { target=innerIndexed(indexer,program,target); }
    let item be typeAtIndexed(indexer,program,target);
    if item != none { let cursor be item.fields; while cursor != none { if cursor.name == name { return cursor; } cursor=cursor.next; } }
    try m.reject(location,"lower","missing nominal field: "+name); return identity ir.Field { index=-1; name=name; valueType=5; immutable=false; next=none; };
}
public function field(program identity ir.Program, valueType Int, name Text, location identity m.Location) returns identity ir.Field fails m.SemanticError {
'''
if s.count(field_anchor) != 1:
    raise SystemExit("indexed field anchor mismatch")
s = s.replace(field_anchor, field_helpers)

TYPES.write_text(s)

s = LOWER.read_text()
replacements = {
    "ir_types.semanticType(builder.program,argument.valueType)": "ir_types.semanticTypeIndexed(builder.typeRegistry,builder.program,argument.valueType)",
    "ir.kind(context.builder.program,": "ir_types.kindIndexed(context.builder.typeRegistry,context.builder.program,",
    "ir.inner(context.builder.program,": "ir_types.innerIndexed(context.builder.typeRegistry,context.builder.program,",
    "ir_types.field(context.builder.program,": "ir_types.fieldIndexed(context.builder.typeRegistry,context.builder.program,",
}
for old, new in replacements.items():
    count = s.count(old)
    if count == 0:
        raise SystemExit(f"lowering query anchor missing: {old}")
    s = s.replace(old, new)
    if old in s:
        raise SystemExit(f"lowering query replacement incomplete: {old}")

for required in (
    "semanticTypeIndexed(builder.typeRegistry",
    "kindIndexed(context.builder.typeRegistry",
    "innerIndexed(context.builder.typeRegistry",
    "fieldIndexed(context.builder.typeRegistry",
):
    if required not in s:
        raise SystemExit(f"missing indexed lowering query: {required}")

LOWER.write_text(s)
