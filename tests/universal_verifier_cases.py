"""Public-verifier probes shared by C/native regressions and paired benchmarks."""

HEADER = '''
import compiler.universal_model as u;
import compiler.universal_verify as verify;
import compiler.universal_optimize as optimize;
import compiler.typed_ir as t;
import compiler.semantic_model as m;
import compiler.format;
function fresh() returns identity u.Builder {
    let location be identity m.Location { path="probe.eri"; line=3; column=7; next=none; ordinal=-1; left=none; right=none; facts=none; };
    let source be identity t.Function { index=-1; name="entry"; result=5; locals=none; body=t.node(0,5,location); failures=none; next=none; };
    let typed be identity t.Program { functions=none; entry=source; types=none; };
    let entry be identity u.Function { index=-1; parameters=0; registers=none; registerTail=none; blocks=none; next=none; };
    let block be identity u.Block { index=0; instructions=none; tail=none; terminator=none; live=false; next=none; }; entry.blocks=block;
    let program be identity u.Program { types=typed; entry=entry; functions=none; };
    return identity u.Builder { program=program; routine=entry; current=block; registerCount=0; blockCount=1; locals=none; };
}
function put(b identity u.Builder,index Int) {
    let value be u.instruction(3); value.result=index; value.valueClass=1; value.text="void"; u.append(b,value);
}
function checked(b identity u.Builder,optimized Bool) returns Bool fails m.SemanticError {
    if optimized { return try optimize.optimize(b.program); } return try verify.verify(b.program);
}
function result(label Text,b identity u.Builder,optimized Bool) {
    let accepted be checked(b,optimized) else error m.SemanticError {
        output(label+":"+error.category+":"+error.message+":"+error.path+":"+format.integer(error.line)+":"+format.integer(error.column)); return;
    }; output(label+":ok");
}
function wide(width Int,chains Int,readIndex Int) returns identity u.Builder {
    let b be fresh(); let test be u.number(b,1); let index be 0;
    while index<width { let value be u.allocate(b,1); if index%3 == 0 { put(b,value); } index=index+1; }
    let first be u.block(b); let second be u.block(b); let done be u.block(b); u.branch(b,test,first,second);
    b.current=first; index=0; while index<width { if index%3 != 0 { put(b,index+1); } index=index+1; } u.jump(b,done);
    b.current=second; index=0; while index<width { if index%3 == 1 { put(b,index+1); } index=index+1; } u.jump(b,done);
    b.current=done; index=0;
    while index<chains { let next be u.block(b); u.jump(b,next); b.current=next; let value be u.call(b,"copy",[1]); index=index+1; }
    u.returnValue(b,readIndex); return b;
}
function loop(definedBefore Bool) returns identity u.Builder {
    let b be fresh(); let test be u.number(b,1); let value be u.allocate(b,1); if definedBefore { put(b,value); }
    let header be u.block(b); let body be u.block(b); let done be u.block(b); u.jump(b,header);
    b.current=header; let used be u.call(b,"copy",[value]); u.branch(b,test,body,done);
    b.current=body; put(b,value); u.jump(b,header); b.current=done; u.returnValue(b,value); return b;
}
function handled(definedBefore Bool) returns identity u.Builder {
    let b be fresh(); let frame be u.zero(b,"frame"); let value be u.allocate(b,1); if definedBefore { put(b,value); }
    let normal be u.block(b); let failed be u.block(b); let done be u.block(b);
    let terminal be u.instruction(9); terminal.arguments=u.operands([frame]); terminal.first=normal.index; terminal.second=failed.index; u.end(b,terminal);
    b.current=normal; put(b,value); u.jump(b,done); b.current=failed; u.jump(b,done); b.current=done; u.returnValue(b,value); return b;
}
function benchmark(width Int,chains Int,rounds Int) {
    let b be wide(width,chains,1); let round be 0;
    while round<rounds { let accepted be verify.verify(b.program) else error m.SemanticError { output(error.message); return; }; round=round+1; } output(round);
}
'''


def regression_program():
    cases = []
    def add(label, body, message=None):
        expected = (label+':ok' if message is None else
                    label+':ir-verify:Universal IR: '+message+':probe.eri:3:7')
        cases.append((f'function case{len(cases)}() {{ {body} }}\n', expected))
    add('empty', 'let b be fresh(); u.end(b,u.instruction(10)); result("empty",b,false);')
    for slot in (1, 2, 3, 61, 62, 63, 123, 124, 125, 185, 186, 187):
        label=f'word-{slot}'
        add(label, f'let b be wide(187,5,{slot}); result("{label}",b,false);',
            'register is not initialized on every incoming path' if (slot-1)%3==2 else None)
    for name, constructor in (('loop','loop'),('handler','handled')):
        for initialized in (True, False):
            label=f'{name}-{initialized}'
            add(label, f'let b be {constructor}({str(initialized).lower()}); result("{label}",b,false);',
                None if initialized else 'register is not initialized on every incoming path')
    add('sparse', 'let b be fresh(); let last be u.block(b); last.index=1000000000000; u.jump(b,last); b.current=last; let value be u.zero(b,"void"); u.returnValue(b,value); result("sparse",b,true);')
    add('bucket-collision', 'let b be fresh(); let last be u.block(b); last.index=257; u.jump(b,last); b.current=last; let value be u.zero(b,"void"); u.returnValue(b,value); result("bucket-collision",b,false);')
    add('duplicate-block', 'let b be fresh(); let last be u.block(b); last.index=0; result("duplicate-block",b,false);', 'cyclic/duplicate block table')
    add('cyclic-block', 'let b be fresh(); b.current.next=b.current; result("cyclic-block",b,false);', 'cyclic/duplicate block table')
    add('cyclic-register', 'let b be fresh(); let value be u.zero(b,"void"); let first be b.routine.registers; if first != none { first.next=first; } result("cyclic-register",b,false);', 'invalid register table')
    add('negative-result', 'let b be fresh(); let value be u.zero(b,"void"); let last be b.current.tail; if last != none { last.result=-7; } u.returnValue(b,value); result("negative-result",b,false);', 'result register class mismatch at -7 (class 1)')
    add('large-result', 'let b be fresh(); let value be u.zero(b,"void"); let last be b.current.tail; if last != none { last.result=99; } u.returnValue(b,value); result("large-result",b,false);', 'result register class mismatch at 99 (class 1)')
    add('negative-operand', 'let b be fresh(); let value be u.call(b,"copy",[-1]); u.returnValue(b,value); result("negative-operand",b,false);', 'unknown register operand')
    add('unreachable-invalid', 'let b be fresh(); u.end(b,u.instruction(10)); let dead be u.block(b); b.current=dead; let value be u.zero(b,"unknown-helper"); u.returnValue(b,value); result("unreachable-invalid",b,true);', 'unknown helper or invalid arity')
    add('known-function', 'let b be fresh(); let called be fresh(); called.routine.index=0; let value be u.zero(called,"void"); u.returnValue(called,value); b.program.functions=called.routine; let used be u.zero(b,"f0"); u.returnValue(b,used); result("known-function",b,false);')
    add('unknown-function', 'let b be fresh(); let value be u.zero(b,"f999"); u.returnValue(b,value); result("unknown-function",b,false);', 'unknown program call target')
    add('function-arity', 'let b be fresh(); let called be fresh(); called.routine.index=0; let value be u.zero(called,"void"); u.returnValue(called,value); b.program.functions=called.routine; let original be u.zero(b,"void"); let used be u.call(b,"f0",[original]); u.returnValue(b,used); result("function-arity",b,false);', 'program call arity mismatch')
    add('changed-before', 'let b be wide(187,0,1); result("changed-before",b,false); let terminal be b.current.terminator; if terminal != none { let changed be terminal; changed.first=999; changed.op=6; changed.arguments=none; } result("changed-after",b,false);')
    # The same public program is checked again after mutation, with fresh caches.
    cases[-1]=(cases[-1][0],cases[-1][1]+'\nchanged-after:ir-verify:Universal IR: missing first successor:probe.eri:3:7')
    ids = [('',-2),('f',-2),('f0',0),('f00',-2),('f01',-2),('f1',1),
           ('f999999999',999999999),('f1000000009',1000000009),('f1000000010',-2),
           ('f10000000000',-2),('f-1',-2),('F1',-2),('f１',-2),('f1λ',-2),('λ1',-2)]
    source=HEADER+''.join(c[0] for c in cases)+''.join(f'case{i}();\n' for i in range(len(cases)))
    source+=''.join(f'output(verify.functionId("{name}"));\n' for name,_ in ids)
    expected='\n'.join(c[1] for c in cases)+'\n'+''.join(f'{value}\n' for _,value in ids)
    return source,expected


def benchmark_program(width=2000, chains=32, rounds=8):
    return HEADER+f'benchmark({width},{chains},{rounds});\n'
