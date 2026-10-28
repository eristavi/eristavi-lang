"""Deterministic typed-IR ownership verifier benchmark (no timed assertion)."""

def benchmark_program(functions=64, locals_per_function=8, rounds=3):
    if min(functions, locals_per_function, rounds) < 1:
        raise ValueError('benchmark dimensions must be positive')
    source = r"""
import compiler.typed_ir as ir;
import compiler.ir_verify;
import compiler.semantic_model as m;
function location() returns identity m.Location { return identity m.Location { path="bench.eri"; line=3; column=7; next=none; ordinal=-1; left=none; right=none; facts=none; }; }
function routine(index Int,width Int) returns identity ir.Function {
 let body be ir.node(0,5,location());
 let result be identity ir.Function { index=index; name="bench"; result=5; locals=none; body=body; failures=none; next=none; };
 let count be width;
 while count > 0 {
  count=count-1;
  result.locals=identity ir.Local { index=count; name="local"; valueType=1; immutable=false; parameter=false; next=result.locals; };
  let declaration be ir.node(10,5,location()); declaration.index=count; declaration.first=ir.node(1,1,location()); declaration.next=body.first; body.first=declaration;
 }
 return result;
}
function run() fails m.SemanticError {
 let program be identity ir.Program { entry=routine(-1,0); functions=none; types=none; };
 let index be {functions};
 while index > 0 { index=index-1; let value be routine(index,{locals_per_function}); value.next=program.functions; program.functions=value; }
 let round be 0;
 while round < {rounds} { try ir_verify.verify(program); round=round+1; }
 output("ok");
}
run() else error m.SemanticError { output(error.message); };
"""
    return (source.replace('{functions}',str(functions))
            .replace('{locals_per_function}',str(locals_per_function))
            .replace('{rounds}',str(rounds)))


def lowering_benchmark_program(width=192):
    """One parameter, many function locals, and locals across entry scopes."""
    if width < 1:
        raise ValueError('benchmark width must be positive')
    declarations=' '.join(f'let x{i} be {i};' for i in range(width))
    return (f'function wide(seed Int) returns Int {{ {declarations} return x{width-1}+seed; }}\n'
            'let first be 1; if true { let nested be 2; } let last be 3; output(wide(7));\n')


def local_regression_program():
    """Exact diagnostics and scope transitions through the public typed verifier."""
    header = r"""
import compiler.typed_ir as ir;
import compiler.ir_verify as verify;
import compiler.semantic_model as m;
import compiler.format;
function location() returns identity m.Location { return identity m.Location { path="locals.eri"; line=3; column=7; next=none; ordinal=-1; left=none; right=none; facts=none; }; }
function node(kind Int,valueType Int) returns identity ir.Node { return ir.node(kind,valueType,location()); }
function fresh(width Int) returns identity ir.Program {
    let entry be identity ir.Function { index=-1; name="entry"; result=5; locals=none; body=node(0,5); failures=none; next=none; };
    let p be identity ir.Program { entry=entry; functions=none; types=none; }; let index be width;
    while index>0 { index=index-1; entry.locals=identity ir.Local { index=index; name="local"; valueType=1; immutable=false; parameter=false; next=entry.locals; }; }
    return p;
}
function declaration(index Int) returns identity ir.Node { let n be node(10,5); n.index=index; n.first=node(1,1); return n; }
function read(index Int) returns identity ir.Node { let n be node(2,1); n.index=index; return n; }
function discard(index Int) returns identity ir.Node { let n be node(12,5); n.first=read(index); return n; }
function branch() returns identity ir.Node { let n be node(13,5); n.first=node(1,3); n.second=node(0,5); n.third=node(0,5); return n; }
function append(body identity ir.Node,value identity ir.Node) {
    let cursor be body.first; if cursor == none { body.first=value; return; }
    let tail be cursor; let next be tail.next; while next != none { tail=next; next=tail.next; } tail.next=value;
}
function result(label Text,p identity ir.Program) {
    let checked be verify.verify(p) else error m.SemanticError {
        output(label+":"+error.category+":"+error.message+":"+error.path+":"+format.integer(error.line)+":"+format.integer(error.column)); return;
    }; output(label+":ok");
}
"""
    cases=[]
    def add(label,body,message=None):
        expected=(label+':ok' if message is None else label+':ir-verify:'+message+':locals.eri:3:7')
        cases.append((f'function case{len(cases)}() {{ {body} result("{label}",p); result("{label}",p); }}\n',expected+'\n'+expected))
    add('empty','let p be fresh(0);')
    add('wide','let p be fresh(129); let index be 0; while index<129 { append(p.entry.body,declaration(index)); index=index+1; } append(p.entry.body,discard(0)); append(p.entry.body,discard(128));')
    add('negative-read','let p be fresh(0); p.entry.body.first=discard(-1);','inactive or unknown local read')
    add('large-read','let p be fresh(0); p.entry.body.first=discard(9223372036854775807);','inactive or unknown local read')
    add('negative-declaration','let p be fresh(1); p.entry.body.first=declaration(-1);','missing or duplicate local declaration')
    add('large-declaration','let p be fresh(1); p.entry.body.first=declaration(9223372036854775807);','missing or duplicate local declaration')
    add('missing-declaration','let p be fresh(1);','local has no declaration')
    add('negative-table','let p be fresh(1); let item be p.entry.locals; if item != none { let current be item; current.index=-1; }','invalid local index or descriptor')
    add('sparse-table','let p be fresh(2); let item be p.entry.locals; if item != none { let next be item.next; if next != none { let current be next; current.index=1000000000000; } }','invalid local index or descriptor')
    add('duplicate-table','let p be fresh(2); let item be p.entry.locals; if item != none { let next be item.next; if next != none { let current be next; current.index=0; } }','invalid local index or descriptor')
    nested='let p be fresh(3); append(p.entry.body,declaration(0)); let b be branch(); let thenBody be b.second; if thenBody != none { append(thenBody,declaration(1)); append(thenBody,discard(0)); append(thenBody,discard(1)); } append(p.entry.body,b); append(p.entry.body,declaration(2)); '
    add('scope-outer',nested+'append(p.entry.body,discard(0)); append(p.entry.body,discard(2));')
    add('scope-inactive',nested+'append(p.entry.body,discard(1));','inactive or unknown local read')
    add('scope-store',nested+'let store be node(11,5); store.index=1; store.first=node(1,1); append(p.entry.body,store);','store into fixed/inactive local')
    add('scope-duplicate','let p be fresh(1); let b be branch(); let a be b.second; let c be b.third; if a != none { let body be a; body.first=declaration(0); } if c != none { let body be c; body.first=declaration(0); } p.entry.body.first=b;','missing or duplicate local declaration')
    add('loop-scope','let p be fresh(1); let loop be node(14,5); loop.first=node(1,3); let body be node(0,5); body.first=declaration(0); loop.second=body; loop.next=discard(0); p.entry.body.first=loop;','inactive or unknown local read')
    parameters='let p be fresh(3); let routine be p.entry; routine.index=0; p.functions=routine; let empty be fresh(0); p.entry=empty.entry; let a be routine.locals; if a != none { let first be a; first.parameter=true; let b be first.next; if b != none { let second be b; second.parameter=true; } } '
    add('parameters',parameters+'append(routine.body,declaration(2)); append(routine.body,discard(0)); append(routine.body,discard(1));')
    add('parameter-declaration',parameters+'append(routine.body,declaration(0));','missing or duplicate local declaration')
    add('invalid-parameter-first',parameters+'let first be routine.locals; if first != none { let current be first; current.immutable=true; let second be current.next; if second != none { let next be second; next.index=-1; } }','invalid parameter')
    add('invalid-table-after-parameter',parameters+'let first be routine.locals; if first != none { let second be first.next; if second != none { let current be second; current.index=-1; } }','invalid local index or descriptor')
    return (header+''.join(s for s,_ in cases)+''.join(f'case{i}();\n' for i in range(len(cases))),
            '\n'.join(expected for _,expected in cases)+'\n')
