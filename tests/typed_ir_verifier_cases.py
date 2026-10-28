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
