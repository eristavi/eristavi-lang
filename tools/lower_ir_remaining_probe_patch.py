from pathlib import Path

path = Path("src/compiler/ir_lower.eri")
s = path.read_text()

old = "type Builder { program identity ir.Program; typeRegistry identity ir_types.Registry; sourceRegistry identity SourceRegistry; sources maybe identity Source; seen maybe identity Seen; count Int; }"
new = "type Builder { program identity ir.Program; typeRegistry identity ir_types.Registry; sourceRegistry identity SourceRegistry; sources maybe identity Source; seen maybe identity Seen; count Int; typeLookups Int; typeSteps Int; typeMisses Int; fieldLookups Int; fieldSteps Int; declarationLookups Int; declarationSteps Int; declarationMisses Int; importLookups Int; importSteps Int; importMisses Int; cloneCalls Int; cloneSteps Int; cloneHits Int; cloneMisses Int; locationLookups Int; locationSteps Int; locationMisses Int; factLookups Int; factSteps Int; factMisses Int; bindingLookups Int; bindingSteps Int; }"
assert s.count(old) == 1, ("Builder", s.count(old))
s = s.replace(old, new)

anchor = "type Context { builder identity Builder; owner identity m.Module; routine identity ir.Function; bindings maybe identity Binding; count Int; map identity m.Clone; tail maybe identity ir.Local; }\n\n"
helpers = r'''type Context { builder identity Builder; owner identity m.Module; routine identity ir.Function; bindings maybe identity Binding; count Int; map identity m.Clone; tail maybe identity ir.Local; }

function profileTypeAt(builder identity Builder, index Int) returns maybe identity ir.Type {
    builder.typeLookups=builder.typeLookups+1;
    let cursor be builder.program.types;
    while cursor != none {
        builder.typeSteps=builder.typeSteps+1;
        if cursor.index == index { return cursor; }
        cursor=cursor.next;
    }
    builder.typeMisses=builder.typeMisses+1; return none;
}
function profileKind(builder identity Builder, index Int) returns Int {
    if index >= 1 and index <= 5 { return index; }
    let value be profileTypeAt(builder,index); if value != none { return value.kind; } return -1;
}
function profileInner(builder identity Builder, index Int) returns Int {
    let value be profileTypeAt(builder,index); if value != none { return value.inner; } return -1;
}
function profileField(builder identity Builder, valueType Int, name Text, location identity m.Location) returns identity ir.Field fails m.SemanticError {
    builder.fieldLookups=builder.fieldLookups+1;
    let target be valueType; if profileKind(builder,target) == 9 { target=profileInner(builder,target); }
    let item be profileTypeAt(builder,target);
    if item != none {
        let cursor be item.fields;
        while cursor != none {
            builder.fieldSteps=builder.fieldSteps+1;
            if cursor.name == name { return cursor; }
            cursor=cursor.next;
        }
    }
    try m.reject(location,"lower","missing nominal field: "+name);
    return identity ir.Field { index=-1; name=name; valueType=5; immutable=false; next=none; };
}
function profileSemanticType(builder identity Builder, index Int) returns identity m.Type {
    let kind be profileKind(builder,index);
    if index >= 1 and index <= 5 { return m.makeType(index,""); }
    let item be profileTypeAt(builder,index);
    if item != none {
        if kind == 7 or kind == 8 or kind == 9 { return m.wrap(kind,profileSemanticType(builder,item.inner)); }
        return m.makeType(kind,item.name);
    }
    return m.makeType(5,"");
}
function profileDeclaration(builder identity Builder, owner identity m.Module, name Text) returns maybe identity m.Declaration {
    builder.declarationLookups=builder.declarationLookups+1;
    let cursor be owner.declarations;
    while cursor != none {
        builder.declarationSteps=builder.declarationSteps+1;
        if cursor.node.text == name { return cursor; }
        cursor=cursor.next;
    }
    builder.declarationMisses=builder.declarationMisses+1; return none;
}
function profileImported(builder identity Builder, owner identity m.Module, alias Text) returns maybe identity m.Import {
    builder.importLookups=builder.importLookups+1;
    let cursor be owner.imports;
    while cursor != none {
        builder.importSteps=builder.importSteps+1;
        if cursor.alias == alias { return cursor; }
        cursor=cursor.next;
    }
    builder.importMisses=builder.importMisses+1; return none;
}
function profileClone(builder identity Builder, value identity m.Type, map identity m.Clone) returns identity m.Type {
    builder.cloneCalls=builder.cloneCalls+1;
    let actual be types.resolve(value);
    if actual.kind == 0 {
        let cursor be map.head;
        while cursor != none {
            builder.cloneSteps=builder.cloneSteps+1;
            if cursor.source == actual { builder.cloneHits=builder.cloneHits+1; return cursor.target; }
            cursor=cursor.next;
        }
        builder.cloneMisses=builder.cloneMisses+1;
        let fresh be m.makeType(0,""); fresh.allowed=actual.allowed; fresh.mustFixed=actual.mustFixed; fresh.mustEqual=actual.mustEqual;
        map.head=identity m.Pair { source=actual; target=fresh; next=map.head; }; return fresh;
    }
    let child be actual.inner;
    if child != none { return m.wrap(actual.kind,profileClone(builder,child,map)); }
    return actual;
}
function profileAt(builder identity Builder, owner identity m.Module, token Int) returns identity m.Location {
    builder.locationLookups=builder.locationLookups+1;
    let cursor be owner.locationIndex;
    while cursor != none {
        builder.locationSteps=builder.locationSteps+1;
        let node be cursor;
        if token == node.ordinal { return node; }
        if token < node.ordinal { cursor=node.left; } else { cursor=node.right; }
    }
    builder.locationMisses=builder.locationMisses+1;
    return identity m.Location { path=owner.path; line=1; column=1; next=none; ordinal=-1; left=none; right=none; facts=none; };
}

'''
assert s.count(anchor) == 1, ("Context", s.count(anchor))
s = s.replace(anchor, helpers)

old_fact = '''function fact(context identity Context, source identity ast.Node) returns identity m.Fact fails m.SemanticError {
    let found be m.expressionFact(context.owner,source);
    if found != none { return found; }
    try reject(context.owner,source,"missing semantic expression fact");
    return identity m.Fact { node=source; value=m.makeType(5,""); failures=none; next=none; tokenNext=none; };
}'''
new_fact = '''function fact(context identity Context, source identity ast.Node) returns identity m.Fact fails m.SemanticError {
    context.builder.factLookups=context.builder.factLookups+1;
    let location be profileAt(context.builder,context.owner,source.token);
    let cursor be location.facts;
    if location.ordinal < 0 { cursor=context.owner.facts; }
    while cursor != none {
        context.builder.factSteps=context.builder.factSteps+1;
        let current be cursor;
        if current.node == source { return current; }
        if location.ordinal < 0 { cursor=current.next; } else { cursor=current.tokenNext; }
    }
    context.builder.factMisses=context.builder.factMisses+1;
    try reject(context.owner,source,"missing semantic expression fact");
    return identity m.Fact { node=source; value=m.makeType(5,""); failures=none; next=none; tokenNext=none; };
}'''
assert s.count(old_fact) == 1, ("fact", s.count(old_fact))
s = s.replace(old_fact, new_fact)

old_binding = '''function binding(context identity Context, source identity ast.Node) returns identity ir.Local fails m.SemanticError {
    let cursor be context.bindings;
    while cursor != none { if cursor.name == source.text { return cursor.local; } cursor=cursor.next; }
    try reject(context.owner,source,"missing lowered local binding"); return local(context,"",1,false,false);
}'''
new_binding = '''function binding(context identity Context, source identity ast.Node) returns identity ir.Local fails m.SemanticError {
    context.builder.bindingLookups=context.builder.bindingLookups+1;
    let cursor be context.bindings;
    while cursor != none { context.builder.bindingSteps=context.builder.bindingSteps+1; if cursor.name == source.text { return cursor.local; } cursor=cursor.next; }
    try reject(context.owner,source,"missing lowered local binding"); return local(context,"",1,false,false);
}'''
assert s.count(old_binding) == 1, ("binding", s.count(old_binding))
s = s.replace(old_binding, new_binding)

replacements = {
    'let result be try ir_types.registerIndexed(builder.typeRegistry,builder.program,owner,value,m.at(owner,source.token));': 'let result be try ir_types.registerIndexed(builder.typeRegistry,builder.program,owner,value,profileAt(builder,owner,source.token));',
    'try types.assign(value,ir_types.semanticType(builder.program,argument.valueType),m.at(owner,source.token));': 'try types.assign(value,profileSemanticType(builder,argument.valueType),profileAt(builder,owner,source.token));',
    'let value be types.clone(parameter.value,map);': 'let value be profileClone(builder,parameter.value,map);',
    'let result be try concrete(builder,owner,source,types.clone(declaration.result,map),true);': 'let result be try concrete(builder,owner,source,profileClone(builder,declaration.result,map),true);',
    'body=ir.node(0,5,m.at(owner,source.token));': 'body=ir.node(0,5,profileAt(builder,owner,source.token));',
    'failures=try ir_types.failuresIndexed(builder.typeRegistry,builder.program,owner,declaration.failures,m.at(owner,source.token));': 'failures=try ir_types.failuresIndexed(builder.typeRegistry,builder.program,owner,declaration.failures,profileAt(builder,owner,source.token));',
    'while parameter != none { let kind be try concrete(builder,owner,source,types.clone(parameter.value,map),false);': 'while parameter != none { let kind be try concrete(builder,owner,source,profileClone(builder,parameter.value,map),false);',
    'let imported be m.imported(owner,base.text);': 'let imported be profileImported(context.builder,owner,base.text);',
    'let declaration be m.declaration(owner,name);': 'let declaration be profileDeclaration(context.builder,owner,name);',
    'let kind be try concrete(context.builder,context.owner,source,types.clone(info.value,context.map),true);': 'let kind be try concrete(context.builder,context.owner,source,profileClone(context.builder,info.value,context.map),true);',
    'imported=m.imported(context.owner,base.text);': 'imported=profileImported(context.builder,context.owner,base.text);',
    'let builder be identity Builder { program=program; typeRegistry=ir_types.registry(program); sourceRegistry=sourceIndex(); sources=none; seen=none; count=0; };': 'let builder be identity Builder { program=program; typeRegistry=ir_types.registry(program); sourceRegistry=sourceIndex(); sources=none; seen=none; count=0; typeLookups=0; typeSteps=0; typeMisses=0; fieldLookups=0; fieldSteps=0; declarationLookups=0; declarationSteps=0; declarationMisses=0; importLookups=0; importSteps=0; importMisses=0; cloneCalls=0; cloneSteps=0; cloneHits=0; cloneMisses=0; locationLookups=0; locationSteps=0; locationMisses=0; factLookups=0; factSteps=0; factMisses=0; bindingLookups=0; bindingSteps=0; };',
}
for old, new in replacements.items():
    assert s.count(old) == 1, (old[:100], s.count(old))
    s = s.replace(old, new)

s = s.replace('ir.kind(context.builder.program,', 'profileKind(context.builder,')
s = s.replace('ir.inner(context.builder.program,', 'profileInner(context.builder,')
s = s.replace('ir_types.field(context.builder.program,', 'profileField(context.builder,')
s = s.replace('m.at(context.owner,', 'profileAt(context.builder,context.owner,')

end_line = 'if source.owner.trace { progress.phase(true,"end","lower-function","f"+format.integer(current.routine.index)+" "+current.routine.name); }'
sample = '''if source.owner.trace {
                    progress.phase(true,"end","lower-function","f"+format.integer(current.routine.index)+" "+current.routine.name);
                    progress.phase(true,"sample","lower-profile","f="+format.integer(current.routine.index)+" functions="+format.integer(builder.count)+" type_lookups="+format.integer(builder.typeLookups)+" type_steps="+format.integer(builder.typeSteps)+" type_misses="+format.integer(builder.typeMisses)+" field_lookups="+format.integer(builder.fieldLookups)+" field_steps="+format.integer(builder.fieldSteps)+" decl_lookups="+format.integer(builder.declarationLookups)+" decl_steps="+format.integer(builder.declarationSteps)+" decl_misses="+format.integer(builder.declarationMisses)+" import_lookups="+format.integer(builder.importLookups)+" import_steps="+format.integer(builder.importSteps)+" import_misses="+format.integer(builder.importMisses)+" clone_calls="+format.integer(builder.cloneCalls)+" clone_steps="+format.integer(builder.cloneSteps)+" clone_hits="+format.integer(builder.cloneHits)+" clone_misses="+format.integer(builder.cloneMisses)+" location_lookups="+format.integer(builder.locationLookups)+" location_steps="+format.integer(builder.locationSteps)+" location_misses="+format.integer(builder.locationMisses)+" fact_lookups="+format.integer(builder.factLookups)+" fact_steps="+format.integer(builder.factSteps)+" fact_misses="+format.integer(builder.factMisses)+" bind_lookups="+format.integer(builder.bindingLookups)+" bind_steps="+format.integer(builder.bindingSteps));
                }'''
assert s.count(end_line) == 1, ("profile-sample", s.count(end_line))
s = s.replace(end_line, sample)

for required in ('profileTypeAt', 'profileSemanticType', 'profileDeclaration', 'profileImported', 'profileClone', 'profileAt', '"lower-profile"'):
    assert required in s, required

path.write_text(s)
